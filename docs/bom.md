# OpenMicroDuck bill of materials

For the HD-1910 / HL-2909 structural variant. Upstream supplier links and reference
prices in CNY are in the root [README](../README.md#bom); these are sourcing
references, not confirmed US availability.

Build in two stages:

- **Bench setup:** keep the controller and servo adapter outside the robot. Use external power, a monitor if needed, and a PC connection to the servo adapter.
- **Integrated robot:** install the controller, HAT, IMU adapter, battery, and wiring after bench testing.

See [structure.md](structure.md) for printing and mechanical changes.

## Shared components

### Electronics

| Part | Model | Specification | Qty | Notes |
|---|---|---|---|---|
| Servos | Feetech HD-1910-C001 | Coreless, 4–8.4 V, listed stall torque 12 kg·cm | 15 | A different actuator requires policy validation/retraining |
| Controller | Radxa ZERO 3W | RK3566, 2 GB RAM, Wi-Fi, no eMMC, headers fitted | 1 | Boot from microSD |
| Storage | MicroSD / TF | 64 GB, A2 | 1 | Required without eMMC |
| Camera | IMX219 | MIPI FPC / CSI | 1 | Upstream resolution descriptions conflict; see below |
| Microphones | TBD | TBD | TBD | Detailed BOM has not finalized the part |
| Speaker | TBD | TBD | TBD | Detailed BOM has not finalized the part |

### Fasteners and bearings

| Part | Specification | Qty in upstream detailed BOM | Use |
|---|---|---|---|
| M2 self-tapping screws | M2 × 5 mm, Phillips, flat tip, black | 56 | Most structural attachments |
| M2 self-tapping screws | M2 × 6 mm, Phillips, flat tip, black | 14 | Some horns and feet |
| M2 self-tapping screws | M2 × 8 mm, Phillips, flat tip, black | 46 | Servo mounting |
| M2.5 self-tapping screws | M2.5 × 6 mm, Phillips, flat tip, black | 11 | Internal head structure |
| M2 low-profile self-tapping screws | Included with servos | 4 | No separate purchase |
| 6700K bearings | 10 × 15 × 3 mm | 3 | — |
| ET2216 bearings | 16 × 22 × 4 mm | **Unresolved: detailed BOM says 1; README says 11** | Check the selected assembly before buying |

### Printed parts

PLA is recommended; TPU-95 is an option for foot pads.
This is the upstream base list. Alternative battery holders and shells are
described in [structure.md](structure.md).

| Part | Qty | Notes |
|---|---|---|
| ankle_left                | 1    | -    |
| ankle_right               | 1    | -    |
| banana_pcb_locker         | 1    | -    |
| bottom_head_shell         | 1    | -    |
| face_part                 | 1    | -    |
| foot_left                 | 1    | -    |
| foot_right                | 1    | -    |
| hip_l                     | 1    | -    |
| hip_l1                    | 1    | -    |
| jaw                       | 1    | -    |
| jaw_soft                  | 1    | -    |
| left_shell                | 1    | -    |
| leg                       | 1    | -    |
| leg2                      | 1    | -    |
| motor_support             | 1    | -    |
| neck                      | 1    | -    |
| neck1                     | 1    | -    |
| neck_pitch                | 1    | -    |
| noenoeil                  | 1    | -    |
| power_support             | 1    | -    |
| right_shell               | 1    | -    |
| soft_mouth_top            | 1    | -    |
| sole_left                 | 1    | -    |
| sole_right                | 1    | -    |
| top_head_shell            | 1    | -    |
| trunk_base                | 1    | -    |
| upper_leg_left            | 1    | -    |
| upper_leg_right           | 1    | -    |
| upper_leg_rigidity_plate  | 1    | -    |
| upper_leg_rigidity_plate1 | 1    | -    |
| yaw2roll                  | 1    | -    |
| yaw2roll1                 | 1    | -    |
| yaw_roll_motion           | 1    | -    |

## Stage-specific components

### Bench setup

| Part | Model / specification | Qty | Purpose |
|---|---|---|---|
| IMU module | LSM6DSV16X, I²C and SPI | 1 | Read gyro and accelerometer data while the bus adapter is unavailable |
| Servo adapter cable | PH2.0 3P to 5264 3P | 1 | URT-2 uses 5264/AMP-3; HD-1910 uses AMP2.0-3P. Verify actual connector compatibility and pin order |
| Wire | Flexible silicone or PTFE, about 30 cm | As needed | External devices need longer wires than the internal harness |

The URT-2 and external power supplies below are needed for bench testing.
The upstream HAT description uses both PH2.0 and AMP2.0 names; check the actual
board and cables before connecting them.

### Integrated robot

| Part | Model / specification | Qty | Purpose |
|---|---|---|---|
| Zero Robot HAT | ZERO 3W 40-pin header adapter | 1 | Half-duplex direction control, power distribution, I²C / I²S peripherals; replaces the external URT-2 |
| IMU-to-servo board | LSM6DSV16X; planned bus ID 200 | 1 | Collect IMU and servo data through the same bus cycle for the runtime's 50 Hz loop |
| Battery | 7.4 V, 3400 mAh, 2S 18650, 2C, XH2.54 2P male | 1 | Integrated power through the HAT; README lists 3500 mAh instead |

## Development equipment

These tools support configuration and bench testing; they are not all installed
in each completed robot.

| Item | Specification | Qty | Notes |
|---|---|---|---|
| Feetech URT-2 | USB Type-C serial-bus servo adapter | 1 | Connects a PC to the servo bus |
| Servo supply | 7.5 V; DC 5.5 × 2.1 mm | 1 | Detailed BOM says 3 A; README says 6 A. Confirm the load requirement |
| Controller supply | USB-C PD supporting 5 V at 2–3 A | 1 | Separate power for the external controller |
| USB data cable | Type-C to Type-A or Type-C, 0.5–1.5 m | 1 | Flashing, serial console, URT-2 |
| Micro-HDMI cable | Micro-HDMI to HDMI, about 1.5 m | 1 | Optional bench monitor |
| MicroSD reader | USB 2.0 is sufficient | 1 | Unnecessary if already built into the computer |

## Unresolved upstream differences

These inherited discrepancies are recorded explicitly rather than silently
resolved by the English cleanup.

| Item | Root README | Detailed guide | Follow-up |
|---|---|---|---|
| ET2216 quantity | 11 load-bearing locations; mentions 14 for original Pollen geometry | 1 | Reconcile against selected CAD before ordering |
| Servo power supply | 7.5 V / 6 A | 7.5 V / 3 A | Size for the actual simultaneous servo load |
| Camera resolution | IMX219, 8 MP | IMX219 described as 5 MP | Verify the exact module; do not order by the conflicting resolution text |
| Battery capacity | 3500 mAh | 3400 mAh | Verify dimensions, connector, and discharge capability |
| Storage | A1 or better | A2 | Detailed BOM specifies A2 |
| Controller storage | 2 GB / no eMMC build | Controller guide prefers eMMC when available | Select one boot/storage arrangement |
| Microphones / speaker | Two 6050 electret mics; one 3525 speaker | Part numbers not finalized | Confirm HAT connectors and final enclosure |

Use the **M2.5 × 6 mm** specification in the current detailed fastener table;
older planning notes may list 8 mm.
