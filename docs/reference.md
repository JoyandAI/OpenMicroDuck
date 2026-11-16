# Microduck reference projects

This index translates the links collected by OpenMicroDuck. Buduck is a fork of
[JoyandAI/OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck), inspired by
Pollen Robotics / Hugging Face Microduck, and is not affiliated with these projects.

Descriptions reflect the imported snapshot. Transient star counts and likes
have been removed. Check each project's current license, maintenance status,
hardware assumptions, and availability.


## Official repositories

| Resource | Purpose |
|---|---|
| [microduck](https://github.com/pollen-robotics/microduck) | Onboard robotd control, mediad camera/WebRTC, gamepad input, updates and board integration. |
| [microduck_rl](https://github.com/pollen-robotics/microduck_rl) | mjlab / MuJoCo Warp PPO training, BAM actuators, backlash, randomization, MJCF and STL. Code and meshes have different licenses. |
| [elec_RPI_Robot_HAT](https://github.com/pollen-robotics/elec_RPI_Robot_HAT) | KiCad 9 schematic, PCB, Gerber, BOM, placement and STEP files; four-layer production files. |
| [lib_KiCAD](https://github.com/pollen-robotics/lib_KiCAD) | Symbols, footprints and 3D libraries required for the HAT project. |
| [rustypot](https://github.com/pollen-robotics/rustypot) | Dynamixel communication and the XL330 register map. |
| [microduck-gst-plugins](https://github.com/pollen-robotics/microduck-gst-plugins) | aarch64 GStreamer builds for Rockchip MPP and WebRTC. |

### Official sites and documentation

| Resource | Purpose |
|---|---|
| [Product page](https://pollen-robotics.com/microduck) | Product specifications and release information. |
| [Store](https://store.pollen-robotics.com/products/microduck) | Official store; check current price and availability. |
| [Press kit](https://pollen-robotics.com/microduck/press-kit/) | Specifications, photos and media downloads. |
| [Meet Microduck](https://pollen-robotics.com/microduck/blog/introducing-microduck/) | Launch article. |
| [Documentation index](https://github.com/pollen-robotics/microduck/blob/main/docs/README.md) | Upstream runtime documentation index. |
| [Architecture](https://github.com/pollen-robotics/microduck/blob/main/docs/design/architecture.md) | Daemons, control loop, policies and updater. |
| [Policy-channel design (historical branch)](https://github.com/pollen-robotics/microduck/blob/policy-hub-design/docs/design/policy-channel-design.md) | Hub package layout, manifest contract and robotctl commands; historical branch link. |
| [Roadmap](https://github.com/pollen-robotics/microduck/blob/main/docs/project/roadmap.md) | Upstream milestones and planned features. |

## Hugging Face


### Simulators and visualization

| Resource | Purpose |
|---|---|
| [pollen-robotics/microduck-simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator) | MuJoCo WASM / onnxruntime-web sandbox, 50 Hz playback, gamepad and skating variants. |
| [mishig/microduck-anatomy](https://huggingface.co/spaces/mishig/microduck-anatomy) | Interactive part inspection and exploded assembly visualization. |
| [multimodalart/microduck-ar](https://huggingface.co/spaces/multimodalart/microduck-ar) | WebXR adaptation with floor placement and ground pickup. |
| [ysharma/gr-workflow-microduck-lab](https://huggingface.co/spaces/ysharma/gr-workflow-microduck-lab) | Natural-language routines composed into skill sequences. |
| [osolmaz/microquack](https://huggingface.co/spaces/osolmaz/microquack) | Procedural robot voice synthesis; Rust core compiled to WASM. |

### Policy models

| Resource | Purpose |
|---|---|
| [pollen-robotics/microduck-policies](https://huggingface.co/pollen-robotics/microduck-policies) | Official ONNX models, separate from this fork's HD-1910 policies. |
| [RemiFabre/microduck-flamingo-cycle](https://huggingface.co/RemiFabre/microduck-flamingo-cycle) | Single-leg stance with left/right switching. |
| [joanfox/microduck-happy-hop](https://huggingface.co/joanfox/microduck-happy-hop) | Hopping policy. |
| [q2p/microduck-beak-throw](https://huggingface.co/q2p/microduck-beak-throw) | Throw an object with the beak. |
| [fffiloni/microduck-polite-bow-b1d864](https://huggingface.co/fffiloni/microduck-polite-bow-b1d864) | Bowing policy. |
| [fffiloni/microduck-moonwalk-backward-55e6af](https://huggingface.co/fffiloni/microduck-moonwalk-backward-55e6af) | Backward moonwalk. |
| [RemiFabre/microduck-rough-walk-g](https://huggingface.co/RemiFabre/microduck-rough-walk-g) | Rough-terrain walking. |
| [HannesVonEssen/microduck-running](https://huggingface.co/HannesVonEssen/microduck-running) | Running policy. |
| [Nupr-Haokun/microduck-step-up-head-brake](https://huggingface.co/Nupr-Haokun/microduck-step-up-head-brake) | Use the head as a brake to cross a 25 mm step, then return upright. |

### Datasets

| Resource | Purpose |
|---|---|
| [craigm26/microduck-stairs-challenge](https://huggingface.co/datasets/craigm26/microduck-stairs-challenge) | Simulation-only stair benchmark with physics models pinned by hash. |

## Community projects


### Tools and applications

| Resource | Purpose |
|---|---|
| [rokbenko/quackd](https://github.com/rokbenko/quackd) | Task-planning daemon, simulator, .duck routines, safety rules and MCP; later versions support other small robots. |
| [jonathanhawkins/microduck-lab](https://github.com/jonathanhawkins/microduck-lab) | Mac training without CUDA, MJCF / 61-to-14 contract, and live browser inspection. |
| [joeynyc/awesome-microduck](https://github.com/joeynyc/awesome-microduck) | Curated software, simulators, policies, agent tools and coverage. |
| [craigm26/duckkit](https://github.com/craigm26/duckkit) | Swift ONNX implementation, 61 observations at 50 Hz, kinematics, protocol types and Linux tests. |
| [aj-dev-smith/microduck-mcp](https://github.com/aj-dev-smith/microduck-mcp) | MCP for CPU MuJoCo simulation, rendered results and an agent debugging page. |
| [joeynyc/microduck-mcp](https://github.com/joeynyc/microduck-mcp) | MCP over mock, MuJoCo, Unix socket and SSH transports; hardware transport was unverified in the source snapshot. |
| [jvpflum/microduck-lab](https://github.com/jvpflum/microduck-lab) | DGX Spark training workspace with pinned upstream submodules. |
| [carpentry-liu/rl-physics-overlay](https://github.com/carpentry-liu/rl-physics-overlay) | Browser telemetry overlay for forces, torque, contacts and learning signals. |
| [kgediya/specs-microduck](https://github.com/kgediya/specs-microduck) | Snap Spectacles gesture teleoperation and telemetry for simulation. |
| [ngxson/wicroduck](https://github.com/ngxson/wicroduck) | Browser WASM MJCF simulation encoded in a URL; browser training was a future goal. |

### Training and simulation

| Resource | Purpose |
|---|---|
| [Vottivott/microduck-playground](https://github.com/Vottivott/microduck-playground) | Independent training playground, reproducible experiments, demos and printable add-ons. |
| [AlexBodner/microduck-tracking](https://github.com/AlexBodner/microduck-tracking) | Multi-object tracking with roboflow/trackers to retrieve a ball among distractors. |
| [metahubaifeel/microduck-rl-on-thor](https://github.com/metahubaifeel/microduck-rl-on-thor) | aarch64 CUDA training support for Thor / DGX Spark / Jetson. |
| [kabilankb/isaaclab-microduck](https://github.com/kabilankb/isaaclab-microduck) | Isaac Lab / Newton MJWarp locomotion, running, kicking and two-robot tasks compared with mjlab. |
| [Macmachi/microduck-rl-genesis](https://github.com/Macmachi/microduck-rl-genesis) | Genesis walking port targeting AMD/ROCm, retaining the upstream actuator model. |
| [osrbot/microduck-ros2-isaac](https://github.com/osrbot/microduck-ros2-isaac) | ROS 2 Jazzy / Isaac Sim tutorials, RViz joint control and official walking policies in USD. |
| [Lulzx/microduck-backflip](https://github.com/Lulzx/microduck-backflip) | Simulation-only backflip task with evaluations, logs and safety criteria. |
| [selinayfilizp/microduck-courier](https://github.com/selinayfilizp/microduck-courier) | Simulation-only pickup, transport and placement in an apartment. |
| [yangyihai/Microduck_RL_Ball_Follow](https://github.com/yangyihai/Microduck_RL_Ball_Follow) | MuJoCo Warp ball following, command-contract layer and ball-dragging demo. |
| [Liyucheng1997/318_lab-microduck-simulator](https://github.com/Liyucheng1997/318_lab-microduck-simulator) | Official sandbox fork with a custom vertical-jump policy. [Demo](https://duck.liyucheng.me). |

### Reproduction and hardware

| Resource | Purpose |
|---|---|
| [JoyandAI/OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck) | Upstream of Buduck: alternative actuators, modified prints, BOM, documentation and software. |
| [fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica) | Assembly/CAD/fastener/electronics reconstruction; not hardware-verified in the source snapshot. |
| [IronSpiderMan/MicroDuckModels](https://github.com/IronSpiderMan/MicroDuckModels) | Three.js / R3F simulator using MuJoCo WASM and local ONNX. |
| [ScrapMeta/microduck-diy](https://github.com/ScrapMeta/microduck-diy) | Personal build log, simulation meshes, printed parts and staged parts lists. |
| [SaberOnGo/open-microduck](https://github.com/SaberOnGo/open-microduck) | Hardware/software documentation; no PCB files in the source snapshot. |
| [boris721/microduck-3d](https://github.com/boris721/microduck-3d) | STL and MJCF extracted from the official simulator. |
| [lingzolabs/microduck-hardware-replica](https://github.com/lingzolabs/microduck-hardware-replica) | FreeCAD multipart assembly, printable meshes and planned BOM; unverified and unaffiliated. |
| [Shiyao-Huang/ChinaMicroDuck](https://github.com/Shiyao-Huang/ChinaMicroDuck) | Manufacturing-route comparisons, asset-license audit, environment reports and reproduction references. |
| [Rhoban/microban](https://github.com/Rhoban/microban) | A different robot using the same HAT: 19 XL330s and Pi Zero 2 W, with BOM and assembly guide. |

### Lineage and history

| Resource | Purpose |
|---|---|
| [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini) | Open-hardware predecessor, BOM, CAD and early mjlab training. |
| [apirrone/Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) | Raspberry Pi runtime for Open Duck Mini. |
| [TommyZihao/microduck_runtime](https://github.com/TommyZihao/microduck_runtime) | Historical prototype runtime mirror using I2C BNO055, superseded by pollen-robotics/microduck. |
| [apirrone/microduck_maploc_rs](https://github.com/apirrone/microduck_maploc_rs) | Prototype ToF submap SLAM, relocalization and navigation code in Rust. |

## Additional resources

- [MicroduckHub](https://microduckhub.com): community policy browser.
- [uDuck Registry](https://uduck-registry.pages.dev): policy descriptor directory.
- [OpenCastor integration](https://docs.opencastor.com/robots/microduck/).
- [Strands Robots provider](https://strands-labs.github.io/robots/policies/microduck/).
- [Microquack web demo](https://osolmaz.github.io/microquack/).
- [Search policy models](https://huggingface.co/models?search=microduck).

The upstream training tool's `uv run publish` publishes an ONNX plus
`manifest.json` with dimensions, API version and robot compatibility.
The official `duck_detector` training repository was inaccessible in the source
snapshot; detector claims are discussed in [the controller guide](main_controller.md).

Microduck grew out of Antoine Pirrone's Open Duck Mini. The projects share
actuator modeling and sim-to-real experience. Prototype runtime and IMU
architectures differ from the current robotd stack.

For this build, begin with [printing](structure.md), the [BOM](bom.md),
[servo wiring](servo.md), and [Motion Lab](../motion-lab/README.md).
