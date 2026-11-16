# OpenMicroDuck Motion Lab

A local CPU simulation and playback interface for the six OpenMD ONNX policies.
The browser shows body telemetry, English text commands, a MuJoCo 3D view,
motion presets, and live tuning controls. MJCF scenes and STL meshes are bundled
under `assets/microduck/`; policies are loaded from the repository's
[`policies/`](../policies/) directory.

## Features and requirements

- CPU ONNX Runtime; no CUDA or GPU needed for policy inference.
- 50 Hz control with one ONNX inference per cycle and four 5 ms physics substeps.
- Walk, stand, sit/stand, ground pickup, right kick, and forward roll.
- Offscreen MuJoCo rendering streamed as MJPEG, with orbit and zoom.
- A 4.2-second scrolling X/Y body-position plot with automatic scaling.
- Local deterministic English command parsing; no cloud language model.
- Local JS/CSS and system fonts; no CDN or external model downloads at runtime.
- Python **3.9+** on macOS/Linux. Windows needs compatible packages and manual startup.
- Installation needs network access. Rendering needs a working OpenGL/offscreen backend.

Optional browser speech recognition may use a browser or system speech service.
Typed commands work without it.

## Quick start

```bash
git clone https://github.com/tnmygrwl/buduck.git
cd buduck/motion-lab
./setup.sh          # Create .venv and install dependencies
./run.sh            # Start and open http://127.0.0.1:18765
```

Manual setup:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python server.py --open
```

Startup prints the actual scene and policy paths. `MOTION_LAB_POLICIES` or
`--policies` can point to a different policy directory.

### Background operation

```bash
./start.sh
./stop.sh
NO_OPEN=1 ./start.sh
```

The launcher prefers `.venv`, then an installed Python with the required packages.
Override it with `MOTION_LAB_PYTHON=/path/to/python`. It opens the browser with
`open` on macOS or `xdg-open` on Linux. PID and log files are stored locally.
An occupied port is reported rather than killing an unrelated listener.

```bash
PORT=18766 PID_FILE=/tmp/motion-lab.pid LOG_FILE=/tmp/motion-lab.log ./start.sh
PORT=18766 PID_FILE=/tmp/motion-lab.pid ./stop.sh
# Foreground alternative:
./run.sh --port 18766
```

## Controls

| Control | Action |
|---|---|
| 3D viewport | Drag to rotate; scroll to zoom |
| Playback bar | Pause/resume; reset pose; show elapsed mode time |
| Reset view | Restore the default three-quarter camera view |
| Six policy buttons | Select a motion; sit/stand label follows current state |
| Manual controls | Head left/right/center, forward speed, walk, stop |
| Body telemetry | Height, roll/pitch, displacement, command, position history, reset count |
| Text commands | Type a command or use a quick button |
| Space / R | Pause/resume / reset |

Resetting from the UI preserves the selected action; the text **reset** command
returns to the standing policy.

### English commands

```text
stand up
walk forward
stop
sit down
pick up
right kick
forward roll
look left
look right
center head
look forward
where is the ball
reset
help
```

Matching is case-insensitive and accepts surrounding whitespace.
Head commands remain distinct from walking commands.

The training ball is **70 mm diameter / 15 g**. It is normally offstage with
collision disabled. A right kick places it **0.09 m forward and 0.042 m right**
of the right foot, at its radius above the floor. It remains after the kick until
another action clears it. The ball is not part of the 61-dimensional observation.

## Policies and timing

All six files use `obs[1,61]` and `actions[1,14]`.

| Mode | File | Behavior |
|---|---|---|
| walk | `OpenMD_walk.onnx` | Velocity tracking; default command 0.16 m/s |
| stand | `OpenMD_stand.onnx` | Hold standing posture |
| sitstand | `OpenMD_sitstand.onnx` | command[0] = 1 to sit, 0 to stand; 0.10 s sit nudge and 0.30 s standing handoff |
| ground_pick | `OpenMD_ground_pick.onnx` | One phase-encoded pickup cycle |
| kick_right | `OpenMD_kick_right.onnx` | Right kick; default 0.5 s handoff |
| roulade | `OpenMD_roulade.onnx` | Settle for 1.02 s, roll over the head, then stand |

Server deployment defaults scale walk/kick by **0.7** and the other actions by
**1.0**. The UI's recommended presets or saved custom values can override these;
they are separate from server defaults. Stand/sit/standup/pickup policies keep
their existing control logic.

A static standing pose can leave sitstand in a bistable state. The brief crouch
pulse starts sitting; standing hands off from sitstand to stand after 0.30 s.
Kick and roll use a zero 13-dimensional command block to avoid stale head/body
commands outside the training distribution.

### Forward roll

Roll is a one-shot skill starting from the exact `STAND` keyframe, including
default origin and heading. Preparation resets to that pose before settling.

During the roll only:

- Actuator `kp` is multiplied by **4**, torque limit by **0.8** (about 0.77 N·m), and commands delayed **5 physics steps / 25 ms**.
- The original full-collision model remains active, including the flat head surface.
- The skill ends after at least **240°** forward rotation and `up > 0.8`; normally about one second.
- The **3 s** duration knob is a stalled-roll timeout, distinct from the board's 1 s deployment duration.

These actuator changes approximate BAM rather than reproducing it exactly.
The upstream notes report 29 upright landings in 30 perturbed starts; this is a
historical result, not a new measurement by this fork. Reset or return to stand
restores the original dynamics.

## Deployment JSON and simulation

`../policies/OpenMD_policy_settings_20261028.json` is a robotd deployment
configuration and provenance index. **server.py does not parse it directly**;
selected resolved values are represented in code.

| Setting | Simulation treatment |
|---|---|
| Policy filenames | Six matching role files loaded from the policy directory |
| Action scales | ACTION_SCALES: walk/kick 0.7, other modes 1.0; live overrides supported |
| kick_duration | Default 0.5 s |
| roulade_duration | Body-state completion; 3 s fallback timeout instead of blindly using the board's 1 s |
| home_deg | Aligned with MJCF STAND and ONNX default pose; do not copy the 15-value board list into a 14-joint observation |
| head_lowpass / legs_lowpass | Implemented in current server: 0.5 / 0.7 deployment defaults; kick/roll bypass unless smooth_skills is enabled |
| gain | Board-specific; not interchangeable with MuJoCo actuator_gainprm |
| voltage_adapt | Not modeled |
| limp_fall | Replaced by the simulator's instability/reset mechanism |
| stand_on_zero_command | UI selects modes explicitly |
| kick_left | Unavailable |
| models paths / hashes / notes | Provenance; not direct control input |

The prior README said low-pass filtering was unused; that was stale relative to
the current server. This guide reflects the existing implementation, without
changing its gains or physics.

## Files and model assumptions

| Path | Purpose |
|---|---|
| `server.py` | HTTP, MuJoCo, ONNX, rendering and MJPEG |
| `assets/microduck/scene.xml` | Default MJCF scene |
| `assets/microduck/assets/` | STL meshes |
| `../policies/` | Six shared ONNX policies |
| `static/index.html` | Interface markup |
| `static/style.css` | Layout and styling |
| `static/app.js` | Polling, telemetry, controls, commands, camera |
| `tests/` | Headless regression tests |
| `setup.sh`, `run.sh`, `start.sh`, `stop.sh` | Installation and lifecycle |

Startup checks policy dimensions, 14 joint names, and default positions against
the scene and STAND keyframe. There is no joint remapping layer.
Other MJCF variants cannot be assumed to behave identically.

Display changes in the server:

1. Replace the checkerboard with a darker floor.
2. Reduce directional light and specular highlights; retain fill light.
3. Render floor group 0 and complete visual group 2. Group 3 is only a collision visualization subset.
4. Hide 24 fully occluded internal components in group 4, selected by body/mesh/occurrence rather than unstable numeric geom IDs. Missing matches fail at startup.

Kick uses a floor-only support collision subset for feet, legs, hips, and trunk.
Other motions use original full-collision masks. The mesh files and collision
geometry are unchanged.

## API and runtime

| Endpoint | Purpose |
|---|---|
| `GET /`, `/style.css`, `/app.js` | Local interface assets |
| `GET /api/state` | Telemetry polled every 150 ms |
| `GET /stream.mjpg` | Multipart MJPEG stream |
| `GET /frame.jpg` | Single-frame snapshot for startup/debugging |
| `POST /api/mode`, `/api/twist`, `/api/head`, `/api/sit` | Motion commands |
| `POST /api/pause`, `/api/reset` | Playback controls |
| `POST /api/camera`, `/api/camera/reset` | Camera |
| `POST /api/chat`, `/api/tune` | English commands and tuning |

Simulation, rendering, and HTTP run separately. The server uses Python's
`ThreadingHTTPServer`, without Flask or a telemetry WebSocket.
The free camera smoothly follows the body as it walks or rolls.

## Tuning and performance

[EXAMPLE_TUNING.md](EXAMPLE_TUNING.md) records one upstream experiment; it is not
a recommended configuration. Current render defaults are **840×472, 24 FPS,
JPEG quality 78**.

```bash
# Reduce rendering work:
.venv/bin/python server.py --width 720 --height 405 --fps 20
# Increase resolution:
.venv/bin/python server.py --width 960 --height 540 --fps 20
```

The inherited benchmark reported roughly 0.24 ms for one policy inference,
1.3 ms per inference-plus-physics control cycle, and 30–50 ms for one
840×472 render/JPEG. Its older 20 FPS target achieved around 16–20 FPS;
actual results depend on machine and backend.

Rendering is the main cost in that measurement. FP16 may fall back to FP32 on
CPU; INT8 needs calibration and changes closed-loop behavior. Reducing physics
precision can change whether a motion succeeds. Start with render resolution,
FPS, and JPEG quality rather than changing policy weights.

## Troubleshooting and verification

- **Blank or loading UI:** check `http://127.0.0.1:18765/api/state` for JSON, then `/frame.jpg`. Proxies/extensions may interfere with MJPEG.
- **Port occupied:** inspect `lsof -nP -iTCP:18765 -sTCP:LISTEN` or choose `--port 18766`.
- **MuJoCo builds from source on Apple silicon:** check that Python is native arm64 and supported by the available wheels.
- **Headless host:** offscreen rendering still requires a usable OpenGL/OSMesa/EGL backend; confirm `mujoco.Renderer` works.

Run the simulation regressions with:

```bash
.venv/bin/python tests/test_motion_lab.py
```

Upstream reported six-policy rollouts, sit height about 58 mm, stand height about
115 mm, and approximately one-second rolls. It also checked full-width layouts
at 1920×1080, 2560×1440, and 3840×2160, with responsive breakpoints at
1180/860/560 px and a larger-screen mode above 1700 px. Those results predate this
English cleanup; run the tests on your environment to verify current behavior.

## Attribution

The interface/server originate in OpenMicroDuck; robot geometry and policies
retain their upstream provenance. See [NOTICE.md](../NOTICE.md) and
[LICENSE](../LICENSE). English localization does not change asset licenses.
