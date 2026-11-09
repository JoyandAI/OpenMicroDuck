#!/usr/bin/env python3
"""Headless regression tests: python tests/test_motion_lab.py"""

import sys
import unittest
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402

# The parts that make up the robot's outer look.  Hiding any of them is what a
# "collapsed" model looks like.
OUTER_SKIN = {
    ("trunk_base", "left_shell"), ("trunk_base", "right_shell"),
    ("jaw_soft", "top_head_shell"), ("jaw_soft", "bottom_head_shell"),
    ("jaw_soft", "face_part"), ("jaw_soft", "lens"), ("jaw_soft", "noenoeil"),
    ("hip_l", "hip_l"), ("hip_l_2", "hip_l"),
    ("ankle_left", "sole_left"), ("ankle_right", "sole_right"),
    ("ankle_left", "foot_left"), ("ankle_right", "foot_right"),
}


class MotionLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = server.MotionLab(server.DEFAULT_MODEL, server.DEFAULT_POLICIES)
        cls.trunk = mujoco.mj_name2id(cls.lab.model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")

    def setUp(self):
        self.lab.roulade_prep = server.ROULADE_PREP
        self.lab.reset()

    def up(self):
        return float(self.lab.data.xmat[self.trunk][8])

    def run_for(self, seconds):
        for _ in range(int(round(seconds / 0.02))):
            self.lab._advance(0.02)

    def roll(self, settle=2.5):
        """Trigger a roulade; return (roll seconds, lowest trunk up, max |lateral gravity|)."""
        lab = self.lab
        lab.set_mode("roulade")
        for _ in range(500):
            lab._advance(0.02)
            if lab.mode == "roulade":
                break
        self.assertEqual(lab.mode, "roulade", "prep never handed over to the roll")
        steps, lowest, lateral = 0, 1.0, 0.0
        while lab.mode == "roulade":
            lowest = min(lowest, self.up())
            gravity = server.quat_to_rot_inv(lab.data.qpos[3:7], np.array([0.0, 0.0, -1.0]))
            lateral = max(lateral, abs(float(gravity[1])))
            lab._advance(0.02)
            steps += 1
            self.assertLess(steps, 400, "roll never handed back to stand")
        self.run_for(settle)
        return steps * 0.02, lowest, lateral

    def test_outer_skin_is_rendered(self):
        model = self.lab.model
        visible = set()
        for gid in range(model.ngeom):
            if model.geom_group[gid] == 2 and model.geom_dataid[gid] >= 0:
                visible.add((
                    mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[gid])),
                    mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, int(model.geom_dataid[gid])),
                ))
        self.assertEqual(OUTER_SKIN - visible, set())

    def test_hidden_parts_are_exactly_the_occluded_list(self):
        hidden = [
            gid for gid in range(self.lab.model.ngeom)
            if self.lab.model.geom_group[gid] == 4 and self.lab.model.geom_dataid[gid] >= 0
        ]
        self.assertEqual(len(hidden), len(server.OCCLUDED_GEOMS))

    def test_mjcf_has_no_extra_collision_hulls(self):
        model = self.lab.model
        names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) for g in range(model.ngeom)]
        self.assertFalse([n for n in names if n and n.startswith("roll_hull")])

    def test_roll_goes_over_the_head_and_lands(self):
        seconds, lowest, lateral = self.roll()
        self.assertLess(lowest, -0.8, "never went inverted")
        self.assertLess(lateral, 0.6, "rolled sideways instead of over the head")
        self.assertLess(seconds, 1.6, "roll should take about one second")
        self.assertGreater(self.up(), 0.97, "did not land upright")
        self.assertGreater(float(self.lab.data.qpos[2]), 0.10, "did not stand back up")
        self.assertEqual(self.lab.auto_reset_count, 0)

    def test_roll_is_repeatable_across_prep_times(self):
        landed = 0
        preps = (0.8, 0.9, 1.0, 1.02, 1.1, 1.2)
        for prep in preps:
            self.lab.roulade_prep = prep
            self.lab.reset()
            _, lowest, _ = self.roll()
            landed += lowest < -0.8 and self.up() > 0.95
        self.assertEqual(landed, len(preps))

    def test_roll_can_be_triggered_twice_in_a_row(self):
        self.roll()
        self.assertGreater(self.up(), 0.97)
        self.roll()
        self.assertGreater(self.up(), 0.97)

    def test_roll_dynamics_do_not_leak_into_other_modes(self):
        lab = self.lab
        before = (lab.model.actuator_gainprm.copy(), lab.model.actuator_biasprm.copy(),
                  lab.model.actuator_forcerange.copy())
        self.roll(settle=0.1)
        self.assertTrue(np.array_equal(before[0], lab.model.actuator_gainprm))
        self.assertTrue(np.array_equal(before[1], lab.model.actuator_biasprm))
        self.assertTrue(np.array_equal(before[2], lab.model.actuator_forcerange))
        # Interrupting mid-roll must restore them as well.
        lab.set_mode("roulade")
        self.run_for(lab.roulade_prep + 0.3)
        self.assertEqual(lab.mode, "roulade")
        lab.reset()
        self.assertTrue(np.array_equal(before[0], lab.model.actuator_gainprm))
        self.assertTrue(np.array_equal(before[2], lab.model.actuator_forcerange))

    def test_camera_keeps_the_rolling_robot_in_view(self):
        lab = self.lab
        lab.set_mode("roulade")
        worst = 0.0
        for _ in range(300):
            lab._advance(0.02)
            worst = max(worst, float(np.linalg.norm(lab.data.qpos[:2] - lab.camera.lookat[:2])))
        self.assertGreater(float(np.linalg.norm(lab.data.qpos[:2])), 0.2, "roll should travel")
        self.assertLess(worst, 0.25, "camera lost the robot")
        lab.reset()
        self.assertTrue(np.allclose(lab.camera.lookat[:2], lab.data.qpos[:2]))

    def test_other_motions_still_work(self):
        lab = self.lab
        self.run_for(2.0)
        self.assertGreater(self.up(), 0.97, "stand")
        lab.set_mode("walk")
        self.run_for(3.0)
        self.assertGreater(self.up(), 0.85, "walk")
        self.assertEqual(lab.auto_reset_count, 0, "walk")
        lab.reset()
        lab.set_mode("kick_right")
        self.run_for(3.0)
        self.assertGreater(self.up(), 0.85, "kick")
        self.assertEqual(lab.auto_reset_count, 0, "kick")
        lab.reset()
        lab.set_mode("sitstand", sit=True)
        self.run_for(2.0)
        self.assertLess(float(lab.data.qpos[2]), 0.08, "sit")
        lab.set_mode("sitstand", sit=False)
        self.run_for(3.0)
        self.assertGreater(float(lab.data.qpos[2]), 0.10, "stand up")


if __name__ == "__main__":
    unittest.main(verbosity=2)
