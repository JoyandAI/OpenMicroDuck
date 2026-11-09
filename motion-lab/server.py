#!/usr/bin/env python3
"""OpenMicroDuck Motion Lab.

A local, CPU-only ONNX + MuJoCo playback server.  It loads the MJCF/STL robot
model bundled inside motion-lab and the six OpenMD policies from the repository
root's policies/ directory, steps the physics, and streams a rendered camera
view to a browser UI.

No CUDA, no cloud, no generated meshes.
"""

from __future__ import annotations

import argparse
import collections
import io
import json
import math
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import mujoco
import numpy as np
import onnxruntime as ort
from PIL import Image

APP_DIR = Path(__file__).resolve().parent

ROLES = ("walk", "stand", "sitstand", "ground_pick", "kick_right", "roulade")
MODE_LABELS = {
    "stand": "站立",
    "walk": "行走",
    "sitstand": "坐站",
    "ground_pick": "捡拾",
    "kick_right": "右踢",
    "roulade": "前滚翻",
}
JOINT_NAMES = [
    "left_hip_yaw", "left_hip_roll", "left_hip_pitch", "left_knee", "left_ankle",
    "neck_pitch", "head_pitch", "head_yaw", "head_roll",
    "right_hip_yaw", "right_hip_roll", "right_hip_pitch", "right_knee", "right_ankle",
]
DEFAULT_POSE = np.array([
    0.0, -0.0873, -0.4579, -0.0049, 0.4530,
    0.3491, 0.3491, 0.0, 0.0,
    0.0, 0.0873, 0.4579, 0.0049, -0.4530,
], dtype=np.float32)

# The sitstand policy is bistable from a perfectly static stand: with no
# residual motion it keeps outputting a near-zero standing action.  This short
# crouch pulse gives it the same initial motion the first frame of a rollout
# has.  It lasts 0.10 s; the policy takes over immediately afterwards.
SIT_NUDGE_ACTION = np.array([
    0.02, 0.116, 0.338, 0.288, 0.337,
    0.035, 0.167, 0.07, -0.273,
    0.009, -0.009, -0.032, -0.452, 0.106,
], dtype=np.float32)

# Fraction of the camera-to-robot offset closed per 20 ms control step.
CAMERA_FOLLOW = 0.08

DEFAULT_MODEL = APP_DIR / "assets/microduck/scene.xml"
_POLICIES_ENV = os.environ.get("MOTION_LAB_POLICIES")
DEFAULT_POLICIES = (
    Path(_POLICIES_ENV).expanduser() if _POLICIES_ENV else APP_DIR.parent / "policies"
)

# Deployment action scales used by the OpenMD board config.  The ONNX metadata
# reports the training scale (1.0); the walk/kick slots are deployed at 0.7.
ACTION_SCALES = {
    "walk": 0.7,
    "stand": 1.0,
    "sitstand": 1.0,
    "ground_pick": 1.0,
    "kick_right": 0.7,
    "roulade": 1.0,
}

# Joint-target first-order low-pass, mirroring robotd's deployment smoothing.
# The resolved board config uses legs_lowpass=0.7, head_lowpass=0.5 on the real
# servo targets; the raw sim leaves ctrl == policy output, which is the main
# source of the "jittery / mechanical" look.  Filter is ctrl = lp*raw +
# (1-lp)*prev, per joint; lp=1.0 disables it.  These are live-tunable at
# runtime via /api/tune so the amount can be dialed in by eye.
HEAD_JOINT_IDX = (5, 6, 7, 8)  # neck_pitch, head_pitch, head_yaw, head_roll
DEPLOY_LEGS_LOWPASS = 0.7
DEPLOY_HEAD_LOWPASS = 0.5

# Deployment defaults for every live-tunable knob, so "恢复默认值" can restore
# the whole panel (not just the smoothing sliders) to the board config values.
DEPLOY_WALK_VX = 0.16
DEPLOY_KICK_DURATION = 0.5
DEPLOY_STANDUP_HANDOFF = 0.30     # sitstand -> velstand hand-off window
DEPLOY_SIT_NUDGE = 0.10           # crouch pulse that unsticks the sit policy
DEPLOY_GROUND_PICK_DURATION = 0.7  # ground_pick cycle length (phase units)
DEPLOY_FALL_TILT = 1.25           # |roll|/|pitch| rad before auto-reset arms
DEPLOY_FALL_HEIGHT = 0.035        # trunk height (m) below which it is "down"
DEPLOY_FALL_GRACE = 1.3           # seconds unstable before an auto-reset fires

# The shipped scene's group 2 is the complete visual skin.  These geoms are
# internal bearings, PCBs, batteries, motor mounts and head/neck mechanisms
# that are fully occluded by that skin from the app's camera.  Leaving them
# in the CPU rasterizer roughly doubles draw work without changing the image;
# put them in an unused render group (physics/collision are unaffected).
# Addressed as (body, mesh, nth match) rather than geom id: ids shift whenever a
# geom is added to the MJCF, which silently hides the wrong parts.
OCCLUDED_GEOMS = (
    ("trunk_base", "seeed_bearing__configuration__22x16x4", 0),
    ("trunk_base", "banana_pcb_locker", 0),
    ("trunk_base", "xl330", 1),
    ("trunk_base", "seeed_bearing__configuration__22x16x4", 1),
    ("hip_l", "seeed_bearing__configuration__22x16x4", 0),
    ("upper_leg_left", "seeed_bearing__configuration__22x16x4", 0),
    ("neck_pitch", "seeed_bearing__configuration__22x16x4", 0),
    ("yaw_roll_motion", "yaw_roll_motion", 0),
    ("yaw_roll_motion", "xl330", 0),
    ("yaw_roll_motion", "seeed_bearing__configuration__22x16x4", 0),
    ("yaw_roll_motion", "seeed_bearing__configuration__22x16x4", 1),
    ("jaw_soft", "xl330", 0),
    ("jaw_soft", "jaw_soft", 0),
    ("jaw_soft", "motor_support", 0),
    ("jaw_soft", "xl330", 1),
    ("jaw_soft", "seeed_bearing__configuration_default", 0),
    ("jaw_soft", "elec_rpi_robot_hat_pcb", 0),
    ("jaw_soft", "soft_mouth_top", 0),
    ("jaw_soft", "m12_lens_holder", 0),
    ("jaw_soft", "pcb__raspberry_pi_zero_2_w", 0),
    ("jaw_soft", "speaker", 0),
    ("hip_l_2", "seeed_bearing__configuration__22x16x4", 0),
    ("upper_leg_right", "seeed_bearing__configuration__22x16x4", 0),
    ("ankle_right", "seeed_bearing__configuration_default", 0),
)

# Ball placement for the right-foot kick, copied from the training repo:
# infer_policy.py BALL_OFFSET_X / BALL_OFFSET_ABS_Y and
# microduck_ball_kick_env_cfg reset_ball_in_front_of_foot.
BALL_OFFSET_X = 0.09
BALL_OFFSET_ABS_Y = 0.042
BALL_RADIUS = 0.035
BALL_HIDDEN_POS = (-0.8, 0.0, BALL_RADIUS)

# Roulade needs a known starting pose: the policy is a one-shot episodic
# skill trained from HOME.  Hold a canonical stand for 1 s, then roll.
ROULADE_PREP = 1.02
# The roll ends on body state, not on a clock (see _roulade_finished); this is
# only the give-up limit for a roll that never lands.
ROULADE_DURATION = 3.0

# The roulade was trained on a BAM model of the servo with a 3-6 physics-step
# command delay.  The MJCF's soft position actuator (kp 0.55) cannot carry the
# robot past the head: it wedges on head + feet with the trunk horizontal.
# These bring the actuator close to the trained one for the roll only, and were
# chosen by a headless sweep with 30 jittered starts (kp 1-6x, force 0.7-1.5x,
# delay 0-6): 29/30 land upright in about 1 s, matching roulade_duration=1 in
# the deployment config.  The authored full collision model stays on throughout:
# the policy pivots on the flat top of the head, as in training.
ROULADE_KP_SCALE = 4.0
ROULADE_FORCE_SCALE = 0.8
ROULADE_DELAY_STEPS = 5

# Roll completion, mirroring the training env's rotation-gated landing: hand
# back to stand once the trunk has rotated this far forward and is upright.
ROULADE_DONE_ROTATION = math.radians(240.0)
ROULADE_DONE_UPRIGHT = 0.8

# Floor-only contact subset used by the kick.
SUPPORT_COLLISION_BODIES = {
    "trunk_base",
    "hip_l", "leg", "ankle_left",
    "hip_l_2", "leg_2", "ankle_right",
}


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def quat_to_rot_inv(q, vec):
    """Rotate a world vector into the body frame (inverse quaternion)."""
    w, x, y, z = [float(v) for v in q]
    return np.array([
        (1 - 2 * (y * y + z * z)) * vec[0] + 2 * (x * y + w * z) * vec[1] + 2 * (x * z - w * y) * vec[2],
        2 * (x * y - w * z) * vec[0] + (1 - 2 * (x * x + z * z)) * vec[1] + 2 * (y * z + w * x) * vec[2],
        2 * (x * z + w * y) * vec[0] + 2 * (y * z - w * x) * vec[1] + (1 - 2 * (x * x + y * y)) * vec[2],
    ], dtype=np.float32)


def euler_from_quat(q):
    w, x, y, z = [float(v) for v in q]
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(clamp(2 * (w * y - z * x), -1.0, 1.0))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


class Policy:
    def __init__(self, role, path):
        self.role = role
        self.path = str(path)
        opts = ort.SessionOptions()
        # CPU only.  Two intra-op threads is enough for these tiny MLPs.
        opts.intra_op_num_threads = 2
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(
            self.path,
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
        inp = self.session.get_inputs()[0]
        out = self.session.get_outputs()[0]
        self.input_name = inp.name
        self.output_name = out.name
        # The simulation feeds exactly the actor layout: 3 angular velocity +
        # 3 gravity + 3x14 joint state/action + 13 command = 61.
        if inp.shape != [1, 61] or out.shape != [1, 14]:
            raise RuntimeError(
                f"{role}: unexpected policy shape {inp.shape} -> {out.shape}; "
                "expected [1, 61] -> [1, 14]"
            )
        meta = self.session.get_modelmeta().custom_metadata_map or {}
        self.run_path = meta.get("run_path", "")
        self.default = DEFAULT_POSE.copy()
        raw_names = meta.get("joint_names")
        if raw_names:
            names = [name.strip() for name in raw_names.split(",")]
            if names != JOINT_NAMES:
                raise RuntimeError(f"{role}: policy joint order does not match MJCF")
        raw = meta.get("default_joint_pos")
        if raw:
            values = [float(v) for v in raw.split(",")]
            if len(values) != 14:
                raise RuntimeError(f"{role}: default_joint_pos is not 14D")
            self.default = np.asarray(values, dtype=np.float32)

    def act(self, obs):
        return self.session.run(
            [self.output_name], {self.input_name: obs.reshape(1, -1).astype(np.float32)}
        )[0][0].astype(np.float32)


class MotionLab:
    def __init__(self, model_path, policies_dir, width=840, height=472,
                 stream_fps=24, jpeg_quality=78):
        self.width = int(width)
        self.height = int(height)
        self.stream_fps = float(stream_fps)
        self.jpeg_quality = int(jpeg_quality)
        # Highlight-safe exposure as a 256-entry LUT: one uint8 gather per frame
        # instead of a full-frame float32 multiply+clip+cast.
        self._exposure_lut = np.clip(
            np.arange(256, dtype=np.float32) * 0.92 + 3.0, 0.0, 255.0
        ).astype(np.uint8)
        self.lock = threading.RLock()
        self.cond = threading.Condition(self.lock)
        self.stop_event = threading.Event()
        self.threads = []

        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        # OpenMD deployment runs the policy at 50 Hz with a 5 ms physics step
        # (4 physics substeps per control step).  The MJCF default is 2 ms;
        # use the deployment cadence so contact and actuator behaviour match.
        self.model.opt.timestep = 0.005
        self.decimation = 4
        self.model.vis.global_.offwidth = max(self.model.vis.global_.offwidth, self.width)
        self.model.vis.global_.offheight = max(self.model.vis.global_.offheight, self.height)
        # Remember the authored full-collision masks so everything but the kick
        # can use them; the kick switches to the support-only subset.
        self._full_contype = self.model.geom_contype.copy()
        self._full_conaffinity = self.model.geom_conaffinity.copy()
        self._style_model()
        self._configure_collisions("full")
        self._hide_occluded_geoms()
        self._actuator_gain = self.model.actuator_gainprm.copy()
        self._actuator_bias = self.model.actuator_biasprm.copy()
        self._actuator_force = self.model.actuator_forcerange.copy()
        self._ctrl_delay = collections.deque()
        self.data = mujoco.MjData(self.model)

        self.stand_key = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "STAND")
        if self.stand_key < 0:
            raise RuntimeError("MJCF has no STAND keyframe")

        self.joint_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)
            for name in JOINT_NAMES
        ]
        if any(jid < 0 for jid in self.joint_ids):
            raise RuntimeError("MJCF joint names do not match the policy joint order")
        self.qpos_adr = [int(self.model.jnt_qposadr[jid]) for jid in self.joint_ids]
        self.qvel_adr = [int(self.model.jnt_dofadr[jid]) for jid in self.joint_ids]
        self.ang_sensor = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SENSOR, "imu_ang_vel"
        )
        if self.ang_sensor < 0:
            raise RuntimeError("MJCF is missing the imu_ang_vel sensor")
        self.ang_adr = int(self.model.sensor_adr[self.ang_sensor])
        self.ang_dim = int(self.model.sensor_dim[self.ang_sensor])

        # Optional kick ball (scene.xml now includes ball.xml).  It is moved
        # out of play for stand/walk/sit/roulade and placed in front of the
        # right foot only when the kick skill starts.
        self.ball_joint = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_free"
        )
        self.ball_geom = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom"
        )
        self.ball_qpos_adr = (
            int(self.model.jnt_qposadr[self.ball_joint]) if self.ball_joint >= 0 else None
        )
        self.ball_qvel_adr = (
            int(self.model.jnt_dofadr[self.ball_joint]) if self.ball_joint >= 0 else None
        )
        self.ball_body = (
            int(self.model.jnt_bodyid[self.ball_joint]) if self.ball_joint >= 0 else -1
        )
        self.ball_visible = False
        self.policies = {}
        for role in ROLES:
            path = Path(policies_dir) / f"OpenMD_{role}.onnx"
            if not path.is_file():
                raise FileNotFoundError(f"missing policy: {path}")
            self.policies[role] = Policy(role, path)
        for policy in self.policies.values():
            if not np.allclose(policy.default, DEFAULT_POSE, atol=1.0e-2):
                raise RuntimeError(
                    f"{policy.role}: ONNX default pose does not match the MJCF STAND pose"
                )

        # Live-tunable, no-retrain motion knobs (see /api/tune).
        #  - legs/head lowpass: deployment-style target smoothing (1.0 = off)
        #  - smooth_skills: also filter kick/roulade (off keeps them crisp)
        #  - kick duration: when the kick hands back to stand; trimming the cut
        #    point is the main lever for a crisper finish
        #  - roulade duration: give-up limit (the roll ends on body state)
        #  - walk_default_vx: forward speed used by the "walk" preset / chat
        self.legs_lowpass = DEPLOY_LEGS_LOWPASS
        self.head_lowpass = DEPLOY_HEAD_LOWPASS
        self.smooth_skills = False
        self.kick_duration = DEPLOY_KICK_DURATION
        self.roulade_duration = ROULADE_DURATION
        self.roulade_prep = ROULADE_PREP
        self.standup_handoff = DEPLOY_STANDUP_HANDOFF
        self.sit_nudge = DEPLOY_SIT_NUDGE
        self.ground_pick_duration = DEPLOY_GROUND_PICK_DURATION
        self.walk_default_vx = DEPLOY_WALK_VX
        # Per-mode action authority (policy output -> joint-target gain).  walk
        # and kick deploy at 0.7.
        self.action_scales = dict(ACTION_SCALES)
        # Auto-reset trip points.
        self.fall_tilt = DEPLOY_FALL_TILT
        self.fall_height = DEPLOY_FALL_HEIGHT
        self.fall_grace = DEPLOY_FALL_GRACE
        self.filtered_ctrl = DEFAULT_POSE.copy()
        self._rebuild_lp()

        self.mode = "stand"
        # The action the user has selected in the UI.  Kept separate from
        # self.mode (the policy physically running): one-shot skills
        # (kick/roulade/pick) return the body to a stand when they finish, but
        # the UI selection and its knob deck stay on the chosen action until the
        # user picks another, so params can keep being tuned.
        self.selected = "stand"
        self.sit = False
        self.paused = False

        # Camera is a free MuJoCo camera.  The UI orbits it with pointer drag;
        # it follows the robot, since a roll or a walk travels out of a fixed view.
        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.azimuth = 130.0
        self.camera.elevation = -15.0
        self.camera.distance = 0.82
        self.camera.lookat[:] = [0.0, 0.0, 0.13]
        self.default_camera = (130.0, -15.0, 0.82)

        self.reset()

        # Commands
        self.cmd_vx = self.walk_default_vx
        self.cmd_vy = 0.0
        self.cmd_wz = 0.0
        self.head_yaw = 0.0
        self.head_pitch = 0.0

        self.jpeg = None
        self.frame_seq = 0
        self.render_fps = 0.0
        self.sim_fps = 0.0
        self._last_frame_time = 0.0
        self._last_sim_time = 0.0

    def _prepare_roulade(self):
        """Return to the canonical reference stand pose, then queue the roll.

        The roulade ONNX is an episodic skill trained from HOME, so use the
        exact STAND keyframe and let the stand policy settle first.
        """
        self.reset()
        self.pending_mode = "roulade"
        self.pending_timer = self.roulade_prep
        self.event = "调整站姿，准备前滚翻"

    def _configure_collisions(self, profile="support"):
        """Apply the authored full collision model or the kick's floor-only subset.

        The subset masks every robot geom to contact the floor only (never each
        other).  Everything else, roulade included, keeps the authored masks.
        """
        if profile == "full":
            self.model.geom_contype[:] = self._full_contype
            self.model.geom_conaffinity[:] = self._full_conaffinity
            self.collision_profile = "full"
            return
        floor_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
        for gid in range(self.model.ngeom):
            self.model.geom_contype[gid] = 0
            self.model.geom_conaffinity[gid] = 0
        if floor_id >= 0:
            # floor bit 1; subset geoms use bit 2 for floor contacts.
            self.model.geom_contype[floor_id] = 1
            self.model.geom_conaffinity[floor_id] = 2
        for gid in range(self.model.ngeom):
            if gid == floor_id:
                continue
            if not (self._full_contype[gid] or self._full_conaffinity[gid]):
                continue
            body = mujoco.mj_id2name(
                self.model, mujoco.mjtObj.mjOBJ_BODY, int(self.model.geom_bodyid[gid])
            ) or ""
            if body in SUPPORT_COLLISION_BODIES:
                # contact the floor but not other robot collision geoms
                self.model.geom_contype[gid] = 2
                self.model.geom_conaffinity[gid] = 1
        self.collision_profile = profile

    def _hide_occluded_geoms(self):
        """Move the fully occluded internal parts to an unrendered group."""
        wanted = set(OCCLUDED_GEOMS)
        seen = collections.Counter()
        for gid in range(self.model.ngeom):
            if self.model.geom_group[gid] != 2 or self.model.geom_dataid[gid] < 0:
                continue
            key = (
                mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, int(self.model.geom_bodyid[gid])),
                mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_MESH, int(self.model.geom_dataid[gid])),
            )
            part = (*key, seen[key])
            seen[key] += 1
            if part in wanted:
                self.model.geom_group[gid] = 4
                wanted.discard(part)
        if wanted:
            raise RuntimeError(f"OCCLUDED_GEOMS not found in the MJCF: {sorted(wanted)}")

    def _set_roulade_actuators(self, active):
        """Switch the actuators and command delay between MJCF and roll settings."""
        self.model.actuator_gainprm[:] = self._actuator_gain
        self.model.actuator_biasprm[:] = self._actuator_bias
        self.model.actuator_forcerange[:] = self._actuator_force
        self._ctrl_delay.clear()
        if active:
            self.model.actuator_gainprm[:, 0] *= ROULADE_KP_SCALE
            self.model.actuator_biasprm[:, 1] *= ROULADE_KP_SCALE
            self.model.actuator_forcerange[:] *= ROULADE_FORCE_SCALE
            self._ctrl_delay.extend(
                self.data.ctrl.copy() for _ in range(ROULADE_DELAY_STEPS)
            )

    def _roulade_finished(self):
        trunk_up = 1.0 - 2.0 * float(np.sum(self.data.qpos[4:6] ** 2))
        return self.roll_rotation >= ROULADE_DONE_ROTATION and trunk_up > ROULADE_DONE_UPRIGHT

    def _style_model(self):
        """Turn the training scene's checkerboard floor into a quiet studio floor."""
        gid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
        if gid < 0:
            return
        mid = int(self.model.geom_matid[gid])
        if mid < 0:
            return
        self.model.mat_texid[mid, :] = -1
        self.model.mat_rgba[mid] = [0.085, 0.105, 0.125, 1.0]
        # The training scene has a strong white directional light plus a
        # specular term.  On the white shell that clipped almost the entire
        # upper body to 255; lower the key light and keep the headlight as fill.
        if self.model.nlight:
            self.model.light_diffuse[:] = [0.35, 0.35, 0.35]
            self.model.light_specular[:] = [0.0, 0.0, 0.0]
        self.model.vis.headlight.ambient[:] = [0.30, 0.30, 0.30]
        self.model.vis.headlight.diffuse[:] = [0.60, 0.60, 0.60]
        self.model.vis.headlight.specular[:] = [0.0, 0.0, 0.0]

    # ------------------------------------------------------------------
    # State reset / policy control
    # ------------------------------------------------------------------
    def reset(self):
        with self.lock:
            self._configure_collisions("full")
            mujoco.mj_resetDataKeyframe(self.model, self.data, self.stand_key)
            mujoco.mj_forward(self.model, self.data)
            self.data.ctrl[:] = DEFAULT_POSE
            self._set_roulade_actuators(False)
            self.roll_angle = 0.0
            self.roll_rotation = 0.0
            self.filtered_ctrl = DEFAULT_POSE.copy()
            self._hide_ball()
            self.camera.lookat[:2] = self.data.qpos[:2]
            self.last_action = np.zeros(14, dtype=np.float32)
            self.command = np.zeros(13, dtype=np.float32)
            self.mode = "stand"
            self.sit = False
            self.paused = False
            self.sim_time = 0.0
            self.mode_time = 0.0
            self.ground_phase = 0.0
            self.behavior_timer = 0.0
            self.sit_nudge_timer = 0.0
            self.pending_mode = None
            self.pending_timer = 0.0
            self.standup_timer = 0.0
            self.fall_timer = 0.0
            self.auto_reset_count = 0
            self.event = "已重置到默认站姿"

    def _activate(self, mode):
        if mode not in ROLES:
            raise ValueError(f"unknown mode: {mode}")
        previous = self.mode
        self.mode = mode
        if previous == "roulade" or mode == "roulade":
            # Leaving the roll: continue the low-pass from what the joints were
            # actually commanded, not the newer target still in the delay line.
            if previous == "roulade":
                self.filtered_ctrl[:] = self.data.ctrl
            self._set_roulade_actuators(mode == "roulade")
        if mode == "kick_right":
            self._configure_collisions("support")
        elif mode in ("walk", "sitstand", "ground_pick", "roulade"):
            self._configure_collisions("full")
        # stand keeps the current profile: the hand-off from the kick stays
        # support-only.
        self.mode_time = 0.0
        self.last_action.fill(0.0)
        self.fall_timer = 0.0
        self.standup_timer = 0.0
        self.sit_nudge_timer = 0.0
        if mode == "ground_pick":
            self.ground_phase = 0.0
            self.behavior_timer = 0.0
        elif mode == "kick_right":
            # OpenMD deployment uses kick_duration=0.5 s (live-tunable).
            self.behavior_timer = self.kick_duration
        elif mode == "roulade":
            self.behavior_timer = self.roulade_duration
            self.roll_angle = 0.0
            self.roll_rotation = 0.0
        else:
            self.behavior_timer = 0.0

        if mode == "kick_right":
            self._place_ball()
        elif mode != "stand" or previous != "kick_right":
            # Keep the kicked ball visible for the stand hand-off, but clear it
            # when starting any other action or an explicit stand request.
            self._hide_ball()

    def _set_ball_visible(self, visible):
        """Toggle the kick ball between the pitch and an unused render group."""
        if self.ball_qpos_adr is None or self.ball_geom < 0:
            return
        if visible:
            x = float(self.data.qpos[0])
            y = float(self.data.qpos[1])
            qw, qx, qy, qz = [float(v) for v in self.data.qpos[3:7]]
            yaw = math.atan2(
                2.0 * (qw * qz + qx * qy),
                1.0 - 2.0 * (qy * qy + qz * qz),
            )
            # Right foot: training uses -BALL_OFFSET_ABS_Y in the yaw frame.
            bx = x + math.cos(yaw) * BALL_OFFSET_X - math.sin(yaw) * (-BALL_OFFSET_ABS_Y)
            by = y + math.sin(yaw) * BALL_OFFSET_X + math.cos(yaw) * (-BALL_OFFSET_ABS_Y)
            self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr + 7] = [
                bx, by, BALL_RADIUS, 1.0, 0.0, 0.0, 0.0,
            ]
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr + 6] = 0.0
            self.model.geom_group[self.ball_geom] = 0
            self.model.geom_contype[self.ball_geom] = 1
            self.model.geom_conaffinity[self.ball_geom] = 1
        else:
            self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr + 7] = [
                BALL_HIDDEN_POS[0], BALL_HIDDEN_POS[1], BALL_HIDDEN_POS[2],
                1.0, 0.0, 0.0, 0.0,
            ]
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr + 6] = 0.0
            self.model.geom_group[self.ball_geom] = 4
            self.model.geom_contype[self.ball_geom] = 0
            self.model.geom_conaffinity[self.ball_geom] = 0
        self.ball_visible = bool(visible)
        mujoco.mj_forward(self.model, self.data)

    def _park_ball(self):
        """Keep the hidden ball at its off-pitch pose instead of free-falling."""
        if self.ball_qpos_adr is None or self.ball_visible:
            return
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr + 7] = [
            BALL_HIDDEN_POS[0], BALL_HIDDEN_POS[1], BALL_HIDDEN_POS[2],
            1.0, 0.0, 0.0, 0.0,
        ]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr + 6] = 0.0

    def _hide_ball(self):
        self._set_ball_visible(False)

    def _place_ball(self):
        self._set_ball_visible(True)

    def _begin_standup(self):
        """Start the sitstand rise, then hand over to the standing policy.

        The sitstand policy reliably sits down, but in this MuJoCo model its
        flag=0 branch stalls while the feet are still tucked.  Letting it make
        the first 0.3 s of the rise and then handing over to the velstand
        policy produces a clean stand without the sideways flop.
        """
        self.sit = False
        self._activate("sitstand")
        self.sit_nudge_timer = 0.0
        self.standup_timer = self.standup_handoff
        self.event = "站起"

    def set_mode(self, mode, sit=None):
        with self.lock:
            if mode not in ROLES:
                return False, f"unknown mode: {mode}"
            # This is a user-initiated selection: remember it for the UI.  The
            # auto-return to stand after a one-shot goes through _activate(),
            # which does NOT touch self.selected, so the selection survives.
            self.selected = mode
            if mode == "sitstand":
                was_sit = self.sit
                self.sit = (not self.sit) if sit is None else bool(sit)
                self.pending_mode = None
                if self.sit:
                    self._activate("sitstand")
                    if not was_sit:
                        self.sit_nudge_timer = self.sit_nudge
                    self.event = "坐下"
                else:
                    self._begin_standup()
                return True, self.event

            # Roulade is a one-shot episodic skill: give it the canonical
            # reference start (settle, then roll) instead of triggering from
            # an arbitrary mid-stand state.
            if mode == "roulade":
                self.pending_mode = None
                self._prepare_roulade()
                return True, self.event

            # A behaviour always starts from a standing pose.  If the robot
            # is currently sitting, rise first, then run the requested mode.
            if self.sit and mode != "sitstand":
                self.pending_mode = mode
                self.pending_timer = 2.0
                self._begin_standup()
                self.event = f"先站起，再进入{MODE_LABELS.get(mode, mode)}"
                return True, self.event

            self.pending_mode = None
            self._activate(mode)
            self.event = f"切换到{MODE_LABELS.get(mode, mode)}"
            return True, self.event

    def toggle_sit(self):
        with self.lock:
            target = not self.sit
            ok, msg = self.set_mode("sitstand", sit=target)
            return ok, msg

    def toggle_pause(self):
        with self.lock:
            self.paused = not self.paused
            self.event = "已暂停" if self.paused else "继续播放"
            return self.paused

    def set_twist(self, vx=None, vy=None, wz=None):
        with self.lock:
            if vx is not None:
                self.cmd_vx = clamp(float(vx), -0.35, 0.35)
            if vy is not None:
                self.cmd_vy = clamp(float(vy), -0.25, 0.25)
            if wz is not None:
                self.cmd_wz = clamp(float(wz), -1.5, 1.5)

    def set_head(self, yaw=None, pitch=None):
        with self.lock:
            if yaw is not None:
                self.head_yaw = clamp(float(yaw), -0.9, 0.9)
            if pitch is not None:
                self.head_pitch = clamp(float(pitch), -0.5, 0.5)

    def set_camera(self, azimuth=None, elevation=None, distance=None):
        with self.lock:
            if azimuth is not None:
                self.camera.azimuth = clamp(float(azimuth), -180.0, 180.0)
            if elevation is not None:
                self.camera.elevation = clamp(float(elevation), -89.0, 89.0)
            if distance is not None:
                self.camera.distance = clamp(float(distance), 0.28, 1.4)

    def reset_camera(self):
        with self.lock:
            az, el, dist = self.default_camera
            self.camera.azimuth = az
            self.camera.elevation = el
            self.camera.distance = dist

    def _rebuild_lp(self):
        """Per-joint low-pass coefficient vector from the leg/head settings."""
        vec = np.full(14, float(self.legs_lowpass), dtype=np.float32)
        for i in HEAD_JOINT_IDX:
            vec[i] = float(self.head_lowpass)
        self._lp_vec = vec

    def set_tune(self, **kw):
        """Live-adjust the no-retrain motion knobs.  All fields optional."""
        with self.lock:
            # Motion smoothing
            if kw.get("legs_lowpass") is not None:
                self.legs_lowpass = clamp(float(kw["legs_lowpass"]), 0.1, 1.0)
            if kw.get("head_lowpass") is not None:
                self.head_lowpass = clamp(float(kw["head_lowpass"]), 0.1, 1.0)
            if kw.get("smooth_skills") is not None:
                self.smooth_skills = bool(kw["smooth_skills"])
            # Action authority (per-mode gain)
            if kw.get("walk_scale") is not None:
                self.action_scales["walk"] = clamp(float(kw["walk_scale"]), 0.3, 1.2)
            if kw.get("kick_scale") is not None:
                self.action_scales["kick_right"] = clamp(float(kw["kick_scale"]), 0.3, 1.3)
            if kw.get("roulade_scale") is not None:
                self.action_scales["roulade"] = clamp(float(kw["roulade_scale"]), 0.5, 1.6)
            # Speed and skill timing
            if kw.get("walk_default_vx") is not None:
                self.walk_default_vx = clamp(float(kw["walk_default_vx"]), 0.0, 0.35)
            if kw.get("kick_duration") is not None:
                self.kick_duration = clamp(float(kw["kick_duration"]), 0.1, 1.5)
            if kw.get("roulade_duration") is not None:
                self.roulade_duration = clamp(float(kw["roulade_duration"]), 0.6, 3.0)
            if kw.get("roulade_prep") is not None:
                self.roulade_prep = clamp(float(kw["roulade_prep"]), 0.3, 2.5)
            if kw.get("standup_handoff") is not None:
                self.standup_handoff = clamp(float(kw["standup_handoff"]), 0.1, 1.2)
            if kw.get("sit_nudge") is not None:
                self.sit_nudge = clamp(float(kw["sit_nudge"]), 0.0, 0.4)
            if kw.get("ground_pick_duration") is not None:
                self.ground_pick_duration = clamp(float(kw["ground_pick_duration"]), 0.3, 1.2)
            # Auto-reset trip points
            if kw.get("fall_tilt") is not None:
                self.fall_tilt = clamp(float(kw["fall_tilt"]), 0.6, 2.2)
            if kw.get("fall_height") is not None:
                self.fall_height = clamp(float(kw["fall_height"]), 0.0, 0.12)
            if kw.get("fall_grace") is not None:
                self.fall_grace = clamp(float(kw["fall_grace"]), 0.3, 4.0)
            # Display (render thread reads these live)
            if kw.get("render_fps") is not None:
                self.stream_fps = clamp(float(kw["render_fps"]), 6.0, 60.0)
            if kw.get("jpeg_quality") is not None:
                self.jpeg_quality = int(clamp(float(kw["jpeg_quality"]), 30, 95))
            self._rebuild_lp()
            return self.tune()

    def tune(self):
        return {
            "legs_lowpass": round(self.legs_lowpass, 3),
            "head_lowpass": round(self.head_lowpass, 3),
            "smooth_skills": bool(self.smooth_skills),
            "walk_scale": round(self.action_scales["walk"], 3),
            "kick_scale": round(self.action_scales["kick_right"], 3),
            "roulade_scale": round(self.action_scales["roulade"], 3),
            "walk_default_vx": round(self.walk_default_vx, 3),
            "kick_duration": round(self.kick_duration, 3),
            "roulade_duration": round(self.roulade_duration, 3),
            "roulade_prep": round(self.roulade_prep, 3),
            "standup_handoff": round(self.standup_handoff, 3),
            "sit_nudge": round(self.sit_nudge, 3),
            "ground_pick_duration": round(self.ground_pick_duration, 3),
            "fall_tilt": round(self.fall_tilt, 3),
            "fall_height": round(self.fall_height, 4),
            "fall_grace": round(self.fall_grace, 3),
            "render_fps": round(self.stream_fps, 1),
            "jpeg_quality": int(self.jpeg_quality),
            "deploy": {
                "legs_lowpass": DEPLOY_LEGS_LOWPASS,
                "head_lowpass": DEPLOY_HEAD_LOWPASS,
                "smooth_skills": False,
                "walk_scale": ACTION_SCALES["walk"],
                "kick_scale": ACTION_SCALES["kick_right"],
                "roulade_scale": ACTION_SCALES["roulade"],
                "walk_default_vx": DEPLOY_WALK_VX,
                "kick_duration": DEPLOY_KICK_DURATION,
                "roulade_duration": ROULADE_DURATION,
                "roulade_prep": ROULADE_PREP,
                "standup_handoff": DEPLOY_STANDUP_HANDOFF,
                "sit_nudge": DEPLOY_SIT_NUDGE,
                "ground_pick_duration": DEPLOY_GROUND_PICK_DURATION,
                "fall_tilt": DEPLOY_FALL_TILT,
                "fall_height": DEPLOY_FALL_HEIGHT,
                "fall_grace": DEPLOY_FALL_GRACE,
                "render_fps": 24.0,
                "jpeg_quality": 78,
            },
        }

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------
    def _observations(self):
        q = self.data.qpos[3:7]
        ang = self.data.sensordata[self.ang_adr:self.ang_adr + self.ang_dim].astype(np.float32)
        gravity = quat_to_rot_inv(q, np.array([0.0, 0.0, -1.0], dtype=np.float32))
        joint_pos = self.data.qpos[self.qpos_adr].astype(np.float32) - DEFAULT_POSE
        joint_vel = self.data.qvel[self.qvel_adr].astype(np.float32)
        return np.concatenate([
            ang, gravity, joint_pos, joint_vel, self.last_action, self.command
        ]).astype(np.float32)

    def _advance(self, dt):
        """Advance one 20 ms control step (4 x 5 ms MuJoCo steps)."""
        if self.paused:
            return

        self.sim_time += dt
        self.mode_time += dt

        # The sitstand rise is only a short hand-off: after it has unbuckled
        # the knees, the velstand policy finishes the motion reliably.
        if self.standup_timer > 0.0:
            self.standup_timer -= dt
            if self.standup_timer <= 0.0:
                self._activate("stand")
                self.event = "站起完成"

        if self.pending_mode is not None and self.mode == "stand":
            self.pending_timer -= dt
            if self.pending_timer <= 0.0:
                pending = self.pending_mode
                self.pending_mode = None
                self._activate(pending)
                if pending == "roulade":
                    self.event = "前滚翻中"

        cmd = np.zeros(13, dtype=np.float32)
        cmd[3] = 0.0
        cmd[4] = 0.0
        cmd[5] = self.head_yaw
        cmd[6] = 0.0

        if self.mode == "walk":
            cmd[0] = self.cmd_vx
            cmd[1] = self.cmd_vy
            cmd[2] = self.cmd_wz
        elif self.mode == "sitstand":
            cmd[0] = 1.0 if self.sit else 0.0
        elif self.mode == "ground_pick":
            self.ground_phase += dt / 4.0
            if self.ground_phase >= self.ground_pick_duration:
                self._activate("stand")
                self.event = "捡拾完成，回到站立"
            else:
                cmd[0] = math.cos(2.0 * math.pi * self.ground_phase)
                cmd[1] = math.sin(2.0 * math.pi * self.ground_phase)
        elif self.mode == "kick_right":
            self.behavior_timer -= dt
            if self.behavior_timer <= 0.0:
                self._activate("stand")
                self.event = "右踢完成，回到站立"
        elif self.mode == "roulade":
            self.behavior_timer -= dt
            if self._roulade_finished() or self.behavior_timer <= 0.0:
                self._activate("stand")
                self.event = "前滚翻完成，回到站立"

        if self.mode in ("kick_right", "roulade"):
            # infer_policy.py: kick/roulade were trained with an all-zero 13D
            # command.  Stale head/body command slots are out-of-distribution.
            cmd[:] = 0.0

        self.command = cmd
        if self.sit_nudge_timer > 0.0:
            action = SIT_NUDGE_ACTION.copy()
            self.sit_nudge_timer = max(0.0, self.sit_nudge_timer - dt)
        else:
            policy = self.policies.get(self.mode) or self.policies["stand"]
            obs = self._observations()
            if not np.all(np.isfinite(obs)):
                self.reset()
                self.event = "观测出现 NaN，已自动复位"
                return
            action = policy.act(obs)
            if not np.all(np.isfinite(action)):
                self.reset()
                self.event = "策略输出出现 NaN，已自动复位"
                return
            action = np.clip(action, -5.0, 5.0)
        self.last_action = action.astype(np.float32)
        raw_target = DEFAULT_POSE + action * self.action_scales.get(self.mode, 1.0)
        # Deployment-style first-order smoothing on the joint targets.  Kick and
        # roulade are fast one-shot skills; filtering them blunts the motion, so
        # they stay raw unless smooth_skills is on.  stand/walk/sit/pick are
        # filtered to remove the jittery target chatter that reads as mechanical.
        if self.mode in ("kick_right", "roulade") and not self.smooth_skills:
            self.filtered_ctrl[:] = raw_target
        else:
            lp = self._lp_vec
            self.filtered_ctrl[:] = lp * raw_target + (1.0 - lp) * self.filtered_ctrl
        self.data.ctrl[:] = self.filtered_ctrl

        for _ in range(self.decimation):
            if self._ctrl_delay:
                self._ctrl_delay.append(self.filtered_ctrl.copy())
                self.data.ctrl[:] = self._ctrl_delay.popleft()
            mujoco.mj_step(self.model, self.data)

        if self.mode == "roulade":
            # Forward rotation so far (freejoint angular velocity is body-frame;
            # +y pitches the trunk forward).  High-water mark, like the training
            # env's accumulator: wobbling back does not undo the roll.
            self.roll_angle += float(self.data.qvel[4]) * dt
            self.roll_rotation = max(self.roll_rotation, self.roll_angle)

        # Auto recover from a fall, but not while intentionally rolling or
        # crouching for a pick.
        roll, pitch, _ = euler_from_quat(self.data.qpos[3:7])
        height = float(self.data.qpos[2])
        unstable = (
            abs(roll) > self.fall_tilt
            or abs(pitch) > self.fall_tilt
            or height < self.fall_height
        )
        if unstable and self.mode not in ("roulade", "ground_pick", "sitstand"):
            self.fall_timer += dt
            if self.fall_timer > self.fall_grace:
                self.auto_reset_count += 1
                self.reset()
                self.event = "检测到失稳，已自动复位"
        else:
            self.fall_timer = 0.0
        self._park_ball()
        self.camera.lookat[:2] += CAMERA_FOLLOW * (self.data.qpos[:2] - self.camera.lookat[:2])

    def state(self):
        with self.lock:
            roll, pitch, yaw = euler_from_quat(self.data.qpos[3:7])
            height = float(self.data.qpos[2])
            return {
                "ok": True,
                "mode": self.mode,
                "mode_label": MODE_LABELS.get(self.mode, self.mode),
                "selected": self.selected,
                "selected_label": MODE_LABELS.get(self.selected, self.selected),
                "sit": bool(self.sit),
                "standup": bool(self.standup_timer > 0.0),
                "paused": bool(self.paused),
                "time": round(self.sim_time, 2),
                "mode_time": round(self.mode_time, 2),
                "height_mm": round(height * 1000.0, 1),
                "x_mm": round(float(self.data.qpos[0]) * 1000.0, 1),
                "y_mm": round(float(self.data.qpos[1]) * 1000.0, 1),
                "roll_deg": round(math.degrees(roll), 1),
                "pitch_deg": round(math.degrees(pitch), 1),
                "yaw_deg": round(math.degrees(yaw), 1),
                "vx": round(float(self.data.qvel[0]), 3),
                "vy": round(float(self.data.qvel[1]), 3),
                "cmd": {
                    "vx": round(self.cmd_vx, 3),
                    "vy": round(self.cmd_vy, 3),
                    "wz": round(self.cmd_wz, 3),
                },
                "head_yaw": round(self.head_yaw, 3),
                "head_pitch": round(self.head_pitch, 3),
                "event": self.event,
                "ball": (
                    {
                        "visible": bool(self.ball_visible),
                        "x_mm": round(float(self.data.qpos[self.ball_qpos_adr]) * 1000.0, 1),
                        "y_mm": round(float(self.data.qpos[self.ball_qpos_adr + 1]) * 1000.0, 1),
                        "z_mm": round(float(self.data.qpos[self.ball_qpos_adr + 2]) * 1000.0, 1),
                    }
                    if self.ball_qpos_adr is not None
                    else None
                ),
                "auto_reset_count": self.auto_reset_count,
                "render_fps": round(self.render_fps, 1),
                "sim_fps": round(self.sim_fps, 1),
                "frame_seq": self.frame_seq,
                "camera": {
                    "azimuth": round(self.camera.azimuth, 1),
                    "elevation": round(self.camera.elevation, 1),
                    "distance": round(self.camera.distance, 3),
                },
                "policies": [
                    {"role": r, "loaded": True, "file": f"OpenMD_{r}.onnx"}
                    for r in ROLES
                ],
                "tune": self.tune(),
            }

    # ------------------------------------------------------------------
    # Chat / command parser (small, deterministic, no cloud model)
    # ------------------------------------------------------------------
    def chat(self, text):
        t = (text or "").strip()
        if not t:
            return {"reply": "说一句话，例如“站起来”“向前走”“捡东西”。", "action": None}

        def result(reply, action=None):
            return {"reply": reply, "action": action}

        if any(k in t for k in ("重置", "复位", "恢复")):
            self.reset()
            return result("已重置到默认站姿，策略回到站立。", "reset")

        if any(k in t for k in ("红球", "球在哪", "球在哪里")):
            return result(
                "场景里有一只 70 mm 的训练用球。平时收在场景外；触发“右踢”时，球会出现在右脚前 9 cm、向右偏 4.2 cm 的位置，踢完留在场上。",
                None,
            )
        if any(k in t for k in ("你是谁", "介绍一下", "你能做什么")):
            return result(
                "我是 OpenMicroDuck 动作实验室的本地回放器：CPU 跑 ONNX，MuJoCo 算物理，浏览器只负责显示。",
                None,
            )
        if any(k in t for k in ("坐下", "坐着", "蹲下")):
            self.set_mode("sitstand", sit=True)
            return result("收到，小鸭正在坐下。", "sit")
        if any(k in t for k in ("站起", "站起来", "起立", "站立")):
            self.set_mode("sitstand", sit=False)
            return result("收到，小鸭正在站起。", "stand_up")
        if any(k in t for k in ("停", "别动", "停住", "刹车")):
            self.set_mode("stand")
            self.set_twist(vx=0.0, vy=0.0, wz=0.0)
            return result("已停止移动，切换到站立保持。", "stop")
        if any(k in t for k in ("捡", "抓", "拾取", "拿东西")):
            self.set_mode("ground_pick")
            return result("开始一次捡拾循环，结束后自动回到站立。", "ground_pick")
        if any(k in t for k in ("踢", "右踢")):
            self.set_mode("kick_right")
            return result("右踢动作已触发，约 0.5 秒后回到站立。", "kick_right")
        if any(k in t for k in ("滚", "翻", "前滚翻")):
            self.set_mode("roulade")
            return result("前滚翻已触发：先调整站姿 1 秒，再翻滚约 1 秒。", "roulade")
        if any(k in t for k in ("走", "前进", "向前", "出发")):
            self.set_mode("walk")
            self.set_twist(vx=self.walk_default_vx, vy=0.0, wz=0.0)
            return result(f"开始向前走，速度指令 {self.walk_default_vx:.2f} m/s。", "walk")
        if any(k in t for k in ("左看", "看左", "向左")):
            self.set_head(yaw=0.65)
            return result("头部向左看。", "head_left")
        if any(k in t for k in ("右看", "看右", "向右")):
            self.set_head(yaw=-0.65)
            return result("头部向右看。", "head_right")
        if any(k in t for k in ("回正", "看前", "向前看", "正视")):
            self.set_head(yaw=0.0, pitch=0.0)
            return result("头部回正。", "head_center")

        return result(
            "我还听不懂这句。可以试：“站起来”“向前走”“停下”“坐下”“捡东西”“右踢”“前滚翻”“重置”。",
            None,
        )

    # ------------------------------------------------------------------
    # Rendering / stream
    # ------------------------------------------------------------------
    def _render_loop(self):
        renderer = mujoco.Renderer(self.model, height=self.height, width=self.width)
        # Group 2 is the complete robot skin; group 3 is the collision-
        # visualization subset (it looks like a disassembled robot if shown
        # alone).  Render floor + complete group 2, with the occluded internal
        # geoms moved to group 4 above.  Do not show every group: that adds
        # duplicate draw work and z-fighting on the white shell.
        renderer._scene_option.geomgroup[:] = [1, 0, 1, 0, 0, 0]
        try:
            next_t = time.perf_counter()
            while not self.stop_event.is_set():
                # Read live so the display-fps knob applies without a restart.
                period = 1.0 / max(1.0, self.stream_fps)
                with self.lock:
                    renderer.update_scene(self.data, camera=self.camera)
                img = renderer.render()
                # Highlight-safe exposure via LUT (see _exposure_lut): keeps the
                # white shell off 255 without a per-frame float pass.
                img = self._exposure_lut[img]
                buf = io.BytesIO()
                Image.fromarray(img).save(
                    buf, format="JPEG", quality=self.jpeg_quality, optimize=False
                )
                now = time.perf_counter()
                with self.cond:
                    self.jpeg = buf.getvalue()
                    self.frame_seq += 1
                    if self._last_frame_time:
                        dt = now - self._last_frame_time
                        if dt > 0:
                            self.render_fps = 0.85 * self.render_fps + 0.15 / dt if self.render_fps else 1.0 / dt
                    self._last_frame_time = now
                    self.cond.notify_all()
                next_t += period
                sleep = next_t - time.perf_counter()
                if sleep > 0:
                    time.sleep(sleep)
                elif sleep < -period:
                    next_t = time.perf_counter()
        finally:
            renderer.close()

    def _sim_loop(self):
        period = 0.02
        next_t = time.perf_counter()
        while not self.stop_event.is_set():
            with self.lock:
                self._advance(period)
            now = time.perf_counter()
            if self._last_sim_time:
                dt = now - self._last_sim_time
                if dt > 0:
                    self.sim_fps = 0.85 * self.sim_fps + 0.15 / dt if self.sim_fps else 1.0 / dt
            self._last_sim_time = now
            next_t += period
            sleep = next_t - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            elif sleep < -0.25:
                next_t = time.perf_counter()

    def start(self):
        for target in (self._sim_loop, self._render_loop):
            th = threading.Thread(target=target, daemon=True)
            th.start()
            self.threads.append(th)

    def stop(self):
        self.stop_event.set()
        with self.cond:
            self.cond.notify_all()
        for th in self.threads:
            th.join(timeout=2.0)


class Handler(BaseHTTPRequestHandler):
    lab = None
    static_dir = APP_DIR / "static"
    server_version = "OpenMDMotionLab/0.1"

    def log_message(self, fmt, *args):
        # Keep the terminal clean; the UI shows status instead.
        return

    def _json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path, content_type):
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._file(self.static_dir / "index.html", "text/html; charset=utf-8")
        elif path == "/app.js":
            self._file(self.static_dir / "app.js", "application/javascript; charset=utf-8")
        elif path == "/style.css":
            self._file(self.static_dir / "style.css", "text/css; charset=utf-8")
        elif path == "/api/state":
            self._json(self.lab.state())
        elif path == "/stream.mjpg":
            self._stream()
        elif path == "/frame.jpg":
            self._frame()
        else:
            self.send_error(404)

    def _frame(self):
        with self.lab.cond:
            frame = self.lab.jpeg
        if frame is None:
            self.send_error(503)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(frame)

    def _stream(self):
        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        last_seq = -1
        try:
            while True:
                with self.lab.cond:
                    self.lab.cond.wait(timeout=1.0)
                    frame = self.lab.jpeg
                    seq = self.lab.frame_seq
                if frame is None or seq == last_seq:
                    continue
                last_seq = seq
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except Exception:
            self._json({"ok": False, "error": "invalid JSON"}, 400)
            return

        lab = self.lab
        try:
            if path == "/api/mode":
                mode = payload.get("mode")
                sit = payload.get("sit")
                ok, msg = lab.set_mode(mode, sit=sit)
                self._json({"ok": ok, "event": msg, "state": lab.state()})
            elif path == "/api/twist":
                lab.set_twist(payload.get("vx"), payload.get("vy"), payload.get("wz"))
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/head":
                lab.set_head(payload.get("yaw"), payload.get("pitch"))
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/sit":
                lab.set_mode("sitstand", sit=payload.get("sit"))
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/pause":
                if "paused" in payload:
                    with lab.lock:
                        lab.paused = bool(payload["paused"])
                        lab.event = "已暂停" if lab.paused else "继续播放"
                else:
                    lab.toggle_pause()
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/reset":
                # Default now keeps the current action: reset only clears the
                # pose/physics (recover from a fall), then re-enters whatever
                # mode was running.  Pass keep_mode=false to force a stand.
                keep = payload.get("keep_mode", True)
                prev_mode = lab.mode
                prev_selected = lab.selected
                prev_sit = lab.sit
                prev_vx, prev_vy, prev_wz = lab.cmd_vx, lab.cmd_vy, lab.cmd_wz
                lab.reset()
                if keep and prev_mode != "stand":
                    if prev_mode == "sitstand":
                        lab.set_mode("sitstand", sit=prev_sit)
                    else:
                        lab.set_mode(prev_mode)
                        if prev_mode == "walk":
                            lab.set_twist(vx=prev_vx, vy=prev_vy, wz=prev_wz)
                else:
                    lab.set_twist(vx=0.0, vy=0.0, wz=0.0)
                # reset() clears the running policy to stand, but the UI
                # selection should survive a keep reset (e.g. reset while
                # "前滚翻" is selected stays on 前滚翻).  A forced stand clears it.
                lab.selected = prev_selected if keep else "stand"
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/camera":
                lab.set_camera(payload.get("azimuth"), payload.get("elevation"), payload.get("distance"))
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/camera/reset":
                lab.reset_camera()
                self._json({"ok": True, "state": lab.state()})
            elif path == "/api/tune":
                tune = lab.set_tune(**payload)
                self._json({"ok": True, "tune": tune, "state": lab.state()})
            elif path == "/api/chat":
                result = lab.chat(payload.get("text", ""))
                result["ok"] = True
                result["state"] = lab.state()
                self._json(result)
            else:
                self._json({"ok": False, "error": "not found"}, 404)
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, 500)


def parse_args():
    p = argparse.ArgumentParser(description="OpenMicroDuck local CPU motion lab")
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--policies", type=Path, default=DEFAULT_POLICIES)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--width", type=int, default=840)
    p.add_argument("--height", type=int, default=472)
    p.add_argument("--fps", type=float, default=24.0, help="MJPEG render frames per second")
    p.add_argument("--quality", type=int, default=78, help="MJPEG JPEG quality 1-95")
    p.add_argument("--open", action="store_true", help="open the UI in the default browser")
    return p.parse_args()


def main():
    args = parse_args()
    if not args.model.is_file():
        sys.exit(f"model not found: {args.model}")
    if not args.policies.is_dir():
        sys.exit(f"policies directory not found: {args.policies}")

    lab = MotionLab(
        args.model, args.policies, width=args.width, height=args.height,
        stream_fps=args.fps, jpeg_quality=args.quality,
    )
    Handler.lab = lab
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    lab.start()

    url = f"http://{args.host}:{args.port}"
    print(f"OpenMicroDuck Motion Lab  {url}")
    print(f"model:    {args.model}")
    print(f"policies: {args.policies}  (CPUExecutionProvider)")
    print("Ctrl+C to stop.")
    if args.open:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        lab.stop()
        server.server_close()


if __name__ == "__main__":
    main()
