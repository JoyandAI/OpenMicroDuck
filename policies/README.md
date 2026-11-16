# OpenMD policies for HD-1910 / robotd

This directory contains **six deployable ONNX models** and a deployment-settings
JSON whose relative model paths refer to this directory.

- Index and parameters: `OpenMD_policy_settings_20261028.json`.
- Naming: `OpenMD_<role>.onnx`, retaining the role keys in the original JSON.
- Policy normalization is embedded in each ONNX graph.

## Files

| Role | ONNX | Bytes | SHA-256 prefix |
|---|---|---:|---|
| walk | `OpenMD_walk.onnx` | 793890 | `24267be20b81` |
| stand | `OpenMD_stand.onnx` | 793842 | `783951c98a74` |
| ground_pick | `OpenMD_ground_pick.onnx` | 804473 | `c3eff49abe24` |
| kick_right | `OpenMD_kick_right.onnx` | 793722 | `31ce29f29a76` |
| roulade | `OpenMD_roulade.onnx` | 793717 | `3c54f3b3111c` |
| sitstand | `OpenMD_sitstand.onnx` | 793794 | `7356e318a7ee` |

The upstream release records matching full hashes in `models.*.onnx_sha256`.
The English cleanup leaves the ONNX files and deployment JSON unchanged.

## Walk and stand slots

The **walk** slot uses `OpenMD_walk.onnx` (`openmd_velocity`, model_9999).
The **stand** slot uses `OpenMD_stand.onnx` (`openmd_velstand` r3 walkpt orig,
model_17500). With `stand_on_zero_command=true`, zero twist selects standing
and nonzero twist selects walking.

This differs from upstream arrangements that use a stand-up model in the stand
slot or run velstand alone in the walk slot. The split was chosen because
velstand's walking behavior still needed improvement. If a later velstand model
covers walking adequately, it can occupy walk with stand set to none.

## Sit / stand

Added November 3, 2026. Both `policy.sitstand` and `models.sitstand` point to
`OpenMD_sitstand.onnx`.

In **robotd 0.13.3**, sitstand action scale is hard-coded to **1.0**;
`standing_action_scale` does not affect it. Button mapping lives in the `padd`
binary rather than an editable configuration in this directory.

The upstream hardware notes report that a forward center of mass can leave the
robot at the initial tilted-head pose without sitting; slight backward motion
helped in that experiment. This is an observation, not a calibrated setup procedure.

## Resolved deployment values, robotd 0.13.3

| Parameter | Value | Meaning |
|---|---|---|
| `action_scale` | 0.7 | Walking / default network scale |
| `standing_action_scale` | 1.0 | Stand network, not the walk slot |
| `stand_on_zero_command` | true | Zero twist → stand; nonzero → walk |
| `head_lowpass` / `legs_lowpass` | 0.5 / 0.7 | Original null values resolve to runtime defaults |
| `gain` | 6 | Runtime default for null |
| `voltage_adapt` | false | Runtime default for null |
| `ground_pick_action_scale` | 1.0 | Default when absent |
| `roulade_action_scale` | 1.0 | Roll scaling |
| `roulade_duration` | 1.0 s | Board deployment value |
| `kick_duration` | 0.5 s | Default when absent |
| `limp_fall` | false | Automatic fall response disabled |
| `sitstand` | `OpenMD_sitstand.onnx` | Fixed scale 1.0 |
| `kick_left` | none | Only right kick is supplied |

`policy.home_deg` contains 15 values including mouth:
neck_pitch/head_pitch 20°; hip_roll −5/+5°; hip_pitch −26.2/+26.2°;
ankle +26/−26°; knee 0°. Preserve the supplied list rather than truncating it to
the 14-dimensional policy action.

## Usage

Paths use `base_dir: "policies"`. Copy the entire directory together.
Original absolute board paths remain in each model's `board_path` for provenance.

Run on a configured robot:

```bash
sudo robotctl policy add walk tnmygrwl/buduck@policies/OpenMD_walk.onnx
sudo robotctl policy add sitstand tnmygrwl/buduck@policies/OpenMD_sitstand.onnx
# Alternatively, copy models to /opt/robot/policies/trials/<name>/ and edit robotd.toml.
```

For local playback, use [Motion Lab](../motion-lab/README.md).
The upstream `uv run scripts/infer_policy.py --walking ... --standing ...`
command belongs to the training checkout; that script is not part of Buduck.

All models have shape **[1,61] → [1,14]**. Do not overwrite them with a direct
checkpoint-to-ONNX conversion that omits normalization.

## Verify model loading

Run from the repository root with ONNX Runtime and NumPy installed:

```bash
python - <<'PY'
import glob
import numpy as np
import onnxruntime as ort

for path in sorted(glob.glob("policies/*.onnx")):
    session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    output = session.run(None, {"obs": np.zeros((1, 61), np.float32)})[0]
    print(path, session.get_inputs()[0].shape, "->", output.shape,
          "finite:", np.isfinite(output).all())
PY
```
