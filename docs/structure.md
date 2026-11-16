# Structure, printing, and assembly

> Structural revision: **v0.1**

The modified parts fit **HD-1910** servos; the upstream guide also lists
**HL-2909** as mechanically compatible. Changes improve printability and rigidity.

## Print and assemble

- Open [`cad/openmicroduck.3mf`](../cad/openmicroduck.3mf) in Bambu Studio for the arranged print project. Check its printer, material, supports, and plate settings for your printer before printing.
- Use [`cad/openmicroduck-assembly-opt.stl`](../cad/openmicroduck-assembly-opt.stl) as the assembly reference.
- Individual files are in [`cad/parts/`](../cad/parts/).
- See the [BOM](bom.md) for electronics, fasteners, and the base structural-parts list.
- PLA is the documented structural material; TPU-95 or silicone pads are options for the soles.
- Print one servo-mounting part and test its fit with an actual HD-1910 before committing to all plates.

There are **38 STL files** in `cad/parts/`, including alternatives. The base BOM
lists **33 parts**, one of each. The additional files are `battery_holder_18650`,
`battery_holder_21700`, `left_shell_battery_opt`, `right_shell_battery_opt`, and
`power_support_battery_opt`. Select variants for your battery and layout; do not
assume all 38 files belong in one assembly.

## Servo geometry

Many original Microduck joints require removing the passive rear servo horn.
After removal, the XL330 has a **recess**, while the HD-1910 has a **protrusion**.
This difference explains most of the structural changes.

![XL330 rear](assets/structure/xl330-288-rear.png)
![HD-1910 rear](assets/structure/1910-rear.png)

## Head

The HD-1910 rear protrusion originally interfered with a screw post.

![Original interference](assets/structure/head-opt.png)

Part of the post was removed to clear the servo while retaining screw attachment.

![Head clearance change](assets/structure/head-opt1.png)
![Modified head](assets/structure/head-opt2.png)

## Jaw

Printing tolerances can make `jaw_soft` rub against `bottom_head_shell`, preventing
the mouth from opening. The modified `jaw_soft` is shorter to provide clearance.

![Jaw clearance](assets/structure/jaw-opt.png)

## Neck

The neck connector was thickened; the original 1 mm wall was difficult to print reliably.

![Thicker neck connector](assets/structure/neck-opt.png)

## Trunk

The original `trunk_base` was thin and held each servo with only two mounting holes.

![Original trunk](assets/structure/trunk-org.png)

The revised structure:

- Thickens `trunk_base`.
- Uses three mounting holes per servo.
- Mounts `power_support` relative to the servo.
- Adjusts IMU mounting holes for an LSM6DSX module.

![Trunk revision](assets/structure/trunk-opt.png)
![Trunk mounting](assets/structure/trunk-opt1.png)
![Trunk detail](assets/structure/trunk-opt2.png)

## Hip

The original yaw mount used two parts, was insufficiently rigid after printing,
and did not fit the HD-1910. Its screw positions also blocked access to the front
servo screws on `trunk_base`.

![Original hip](assets/structure/yaw-org.png)
![Original hip detail](assets/structure/yaw-org1.png)
![Original screw access](assets/structure/yaw-org2.png)

The revised yaw mount is one piece and leaves access for those screws.

![Revised hip](assets/structure/yaw-opt1.png)
![Revised screw access](assets/structure/yaw-opt3.png)

## Legs

- `upper_leg_rigidity_plate` is thicker.
- `upper_leg` fits the HD-1910; two locating posts were removed to improve cable routing and assembly.
- `leg` was also modified for the HD-1910.

![Rigidity plate](assets/structure/upper-leg-rigidity-plate-opt.png)
![Upper-leg revision](assets/structure/upperleg-opt.png)
![Original leg](assets/structure/leg-org.png)
![Revised leg](assets/structure/leg-opt.png)

## Ankle

Originally, the bearing was inserted from inside before fitting the ankle to the
leg. This was difficult with either servo unless the part was very flexible.
The flat internal surface also interfered with the servo and restricted rotation.

![Original ankle](assets/structure/ankle-org.png)

The revised ankle has an arched interior for rotation clearance and a flexible rib:

1. The ankle fits onto the leg module more easily.
2. The bearing clips in from outside.
3. The foot limits clip movement, reducing the chance that the bearing comes loose.

![Revised ankle](assets/structure/ankle-opt.png)
![Ankle bearing retention](assets/structure/ankle-opt2.png)
