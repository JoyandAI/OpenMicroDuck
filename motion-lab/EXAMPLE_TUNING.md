# Example tuning snapshot — not defaults

This records an upstream experiment from **November 6, 2026**. These values
are **not project defaults or recommendations**. They came from per-motion
browser localStorage load modes/presets and server deployment/skill constants.
They are Motion Lab settings, not ONNX weights or robotd.toml.

## Per-motion values

| Motion / ONNX | Loaded source | Action scale | Leg / head low-pass | Timing / special settings |
|---|---|---:|---|---|
| walk / OpenMD_walk.onnx | Custom | 1.20 | 0.70 / 0.50 | vx = 0.16 m/s |
| stand / OpenMD_stand.onnx | Deployment | 1.00 fixed | 0.70 / 0.50 | Hold standing pose |
| sitstand / OpenMD_sitstand.onnx | Deployment | 1.00 fixed | 0.70 / 0.50 | Stand handoff 0.30 s; sit pulse 0.10 s; command[0] = 1 sit / 0 stand |
| ground_pick / OpenMD_ground_pick.onnx | Custom | 1.00 fixed | 0.75 / 0.50 | 0.50 phase units, approximately 2.0 s |
| kick_right / OpenMD_kick_right.onnx | Custom | 1.30 | 0.70 / 0.50, bypassed | 0.50 s; support collision; ball x=0.09, y=−0.042 m |
| roulade / OpenMD_roulade.onnx | Deployment | 1.00 | 0.70 / 0.50, bypassed | Prepare 1.02 s; timeout 3.0 s; typical completion about 1 s |

Custom presets had also been saved for stand, sitstand, and roulade, but their
selected load source was deployment, so those saved values were not active.

## Shared values

| Parameter | Example value |
|---|---|
| Control frequency | 50 Hz |
| Physics substeps | 5 ms × 4 |
| Observation / action | 61 → 14 |
| smooth_skills | false; kick/roll use raw policy output |
| Default walk speed | 0.16 m/s |
| Camera follow | 0.08 per control step |
| Camera distance | 0.82 m, temporarily overridden by manual zoom |
| Resolution | 840 × 472 |
| Render target | 24 FPS |
| JPEG quality | 78 |
| Exposure correction | 256-entry lookup table |
| Fall reset | 1.25 rad tilt, 0.035 m height, 1.3 s grace period |

## Skill physics overrides

These are not exposed as tuning-panel sliders.

| Roll setting | Value |
|---|---|
| Actuator kp | ×4 |
| Torque limit | ×0.8 |
| Command delay | 5 physics steps / 25 ms |
| Collisions | Full model |
| Completion | At least 240° accumulated forward rotation and up > 0.8 |
| 3.0 s duration | Stalled-roll timeout, not nominal execution time |

| Right-kick setting | Value |
|---|---|
| Collisions | Support subset: feet, legs, hips, trunk against floor only |
| Ball offset | x=0.09 m forward, y=−0.042 m right |
| Ball radius | 0.035 m |

## Interpretation

- Action scale is per motion: 1.20 walk, 1.30 kick, 1.00 for the others in this experiment.
- Displayed low-pass values do not affect kick/roll while smooth_skills is false.
- Pickup's 0.50 is in **phase units**, not seconds.
- Roll's 3.0 s is a **timeout**; normal state-based completion is about one second.
- Browser storage holds custom values and selected load sources. Clearing site data or changing browsers restores the applicable recommended/deployment defaults.
