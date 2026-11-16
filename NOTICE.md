# Attribution and provenance

Buduck is a personal learning and recreation fork of
[JoyandAI/OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck).
OpenMicroDuck is an independent third-party reproduction study of Microduck;
neither project is affiliated with or endorsed by Pollen Robotics.

## Licenses

| Content | License |
|---|---|
| Software | [Apache License 2.0](LICENSE-APACHE-2.0.txt) |
| Hardware and drawings (`assembly-drawings/`, `cad/`) | [CC BY-NC-SA 4.0](LICENSE-CC-BY-NC-SA-4.0.txt) |

SPDX identifiers: `Apache-2.0` and `CC-BY-NC-SA-4.0`.
The complete license texts are retained unchanged.

## Upstream sources

| Source | Author | License |
|---|---|---|
| [OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck) | JoyandAI and contributors | See the repository license and notices |
| [microduck_rl](https://github.com/pollen-robotics/microduck_rl) | Pollen Robotics | Code: Apache-2.0; 3D models: CC-BY-NC-SA-4.0 |
| [microduck](https://github.com/pollen-robotics/microduck) | Pollen Robotics | Apache-2.0 |

The upstream notice describes Microduck as a commercial product whose complete
hardware BOM, editable CAD, PCB schematics, and assembly documentation were not
publicly released. The geometry used here derives from the MJCF simulation models
and STL meshes published in `microduck_rl`.

## Derived content

The following material was generated or adapted from upstream MJCF and STL files
and retains the noncommercial ShareAlike license:

- `assembly-drawings/`: rendered assembly and exploded views, where distributed.
- `cad/`: assembled STL files with world transforms applied, plus structural modifications.
- The upstream simulation meshes bundled in `motion-lab/assets/microduck/` retain their upstream license.

Some CAD parts include topology changes, dimensional adjustments, and assembly
clearance fixes by OpenMicroDuck. Buduck translates documentation and interface
text into English; it does not change the CAD geometry or model weights.

## Non-commercial use

The upstream 3D models and their derivatives may not be used commercially.
This repository is intended for learning, research, and personal recreation.

## Suggested attribution

> Based on Pollen Robotics' Microduck models (CC-BY-NC-SA-4.0),
> https://github.com/pollen-robotics/microduck_rl,
> with adaptations by JoyandAI/OpenMicroDuck and this Buduck fork.
