# Servo selection, wiring, and configuration

The current build uses **Feetech HD-1910-C001**. This guide translates the
upstream actuator comparison and distinguishes official specifications,
source-derived runtime behavior, planned compatibility, and unresolved details.
See [architecture.md](architecture.md) for those evidence labels.

Actuators determine mechanical fit, feedback timing, and sim-to-real behavior.
A compatible connector or similar torque does not make policies interchangeable.

## 1. Microduck reference actuator

The product specification lists 15 motors. The runtime speaks **Dynamixel XL330**.
Gear ratio, torque, and the BAM M6 training model support **XL330-M288-T** as the
comparison baseline; the exact retail-production SKU was not confirmed by those
sources. The higher-speed M077 has a different 77:1 ratio and roughly one-third
the stall torque. `-T` denotes TTL half-duplex.

### XL330-M288-T specifications

| Property | Value from the cited upstream sources |
|---|---|
| Mass | 18 g |
| Size, W × H × D | 20 × 34 × 26 mm |
| Ratio | 288.4:1 |
| Encoder | 12-bit absolute magnetic, ams AS5601, 4096 counts/revolution |
| Stall torque | 0.42 N·m at 3.7 V / 1.11 A; 0.52 N·m at 5 V / 1.47 A; 0.60 N·m at 6 V / 1.74 A |
| Continuous torque | Not specified |
| No-load speed | 76 / 103 / 123 rpm at 3.7 / 5 / 6 V |
| No-load current | Store lists 0.15 A at 5 V |
| Standby current | Manual 17 mA; store 15 mA |
| Supply | 3.7–6.0 V; recommended 5 V |
| Baud rates | Hardware specification up to 4 Mbps; register table also lists 4.5 Mbps |
| Runtime baud rate | **1 Mbps** |
| Connector | Dual TTL 3P daisy-chain, Robot Cable-X3P; 3.3 V logic, 5 V compatible |
| Pins | 1 GND / 2 VDD / 3 DATA |
| Protocol | Dynamixel Protocol 2.0, half-duplex, 8N1 |
| Current-related modes | Mode 0: current; Mode 5: current-based position |
| Factory mode | Mode 3: position |
| Feedback | Position, speed, current, PWM, trajectory, temperature, voltage, errors |
| Case / gears | Engineering plastic |
| Historical price, September 2026 | Korea $23.90; US $27.49; other cited channels CNY 95–238 |

The historical Korea list price gives roughly $360 for 15 actuators. These are
inherited price references, not current quotes.

### Why feedback and current control matter

The 50 Hz runtime needs encoder position and velocity, with PWM/current available
for diagnostics and actuator characterization. It reads fast registers 124–136;
voltage and temperature are sampled at 1 Hz from 144–146. The standard **61-value
policy observation uses joint position and velocity**, not separate current/PWM
dimensions.

Mode 0 controls current/torque; Mode 5 tracks position with a Goal Current limit.
This supports yielding, contact, mouth gripping, and impact handling.
The runtime's documented startup corrections set return delay, baud, PWM slope,
and shutdown mask; they do **not** establish that production uses Mode 5.

Report temperature per joint, including the hottest joint. Averaging temperatures
can hide a heavily loaded knee. The documented shutdown mask is 52.

## 2. Selection criteria

| Criterion | Requirement |
|---|---|
| Mechanical fit | Check envelope, holes, shaft/horn, and cable exit |
| Actuator type | Magnetic encoder and bus feedback; current control or current-limited position capability |
| Dynamics | Check rated/stall torque, speed, voltage, mass, and inertia |
| Electrical interface | Three-wire TTL with verified connector orientation and pin order |
| Protocol | A new RobotIo driver may be needed; Dynamixel, Feetech, and Unitree protocols are generally different |
| Quality and cost | Traceable batches and lifetime testing matter across 15 actuators |

A supply change affects cell count, HAT rail, MOSFET/current ratings, connectors,
and the IMU adapter power input. The reference NP-F550 is 2S / 7.2 V nominal,
while retail XL330 tops out at 6 V; the original guide marks the production
power arrangement unresolved.

Use the HD-1910 policies in this repository for the HD-1910 build. Other actuators
need their own characterization and policy validation/retraining while preserving
the **61 → 14** interface.

## 3. Candidate comparison

### Source documents

- **HD-1910-C001:** Feetech A/0 specification, September 7, 2026; drawing also uses HD-1910M-C001. Rated operating range 4–8.4 V.
- **Unitree YS-342026-S288:** plastic-case brushless servo; recommended 12.6 V, 288.35:1. J288 is a heavier metal variant with a different voltage range.
- **KPower RD05T:** September 2026 specification; 6 kg·cm dual-axis micro servo. Current feedback is listed; a constant-current operating mode is not explicitly specified.
- **HL-2915-C002 / HL-2909-C001:** the source describes HL-2915 as an earlier name, but the available specification cover says HL-2915-C002. Do not assume a separate HL-2909 electrical specification exists.

Manufacturer PDFs retain their original contents; the key values are translated
below and their filenames are English.

### Specifications

Compare at **6 V** where supplied. Unitree and HL-2915 lack a 6 V operating point;
their 12 V figures are labeled. 1 kg·cm is approximately 0.098 N·m.

| Property | XL330-M288-T | HD-1910-C001 | YS-342026-S288 | KPower RD05T | HL-2915-C002 |
|---|---|---|---|---|---|
| Mass | 18 g | 21 ± 2 g | 19.5 g | 18 g | 22.5 ± 2 g |
| Envelope, mm | 20 × 34 × 26 per manual | 20 × 34 × 23; 20 × 34 × 29 with horn | 20 × 34 × 26 | 26 × 20 × 34 | 34 × 20 × 23 |
| Gear ratio | 288.4:1 | 320:1 | 288.35:1 | Unspecified | 320:1 |
| Comparison voltage | 6 V, maximum | 6 V | 12 V | 6 V | 12 V |
| Stall torque | 0.60 N·m / about 6.1 kg·cm | 12 kg·cm / 1.18 N·m | 0.6 N·m at 12 V | 6 kg·cm / 0.59 N·m | 8.9 kg·cm / 0.87 N·m at 12 V |
| Rated torque | Unspecified | 3 kg·cm / 0.29 N·m | Unspecified | 1.5 kg·cm / 0.15 N·m | 2.9 kg·cm / 0.28 N·m at 12 V |
| No-load speed | 123 rpm | 92 rpm | 157 rpm at 12 V | 125 rpm, 0.08 s/60° | 77 rpm at 12 V |
| Supply range | 3.7–6.0 V | 4–8.4 V | 6.4–12.6 V | 3.6–8.4 V | 9–14 V |
| Standby / no-load / rated / stall current | 17 mA / unspecified at 6 V / — / 1.74 A | 20 / ≤180 / 690 / 1600 mA | 50 / 270 / — / — mA at 12 V | 10 / 280 / — / 1740 mA | 42 / 140 / 200 / 600 mA at 12 V |
| Maximum baud | 4 Mbps specification | 1 Mbps | 6 Mbps | 4 Mbps | 1 Mbps |
| Connector | JST 3P TTL | AMP2.0-3P | TTL multidrop | EH2.54-3P | AMP-3 |
| Pins | 1 GND / 2 VDD / 3 DATA | **1 Signal / 2 Vcc / 3 GND** | Consult vendor | 1 GND / 2 VCC / 3 TTL | 1 GND / 2 Vcc / 3 Signal |
| Protocol | Dynamixel 2.0 | Feetech, half-duplex 8N1 | Unitree-specific | Half-duplex 8N1; frame format not supplied | Feetech, half-duplex 8N1 |
| Force/current control | Modes 0 / 5 | Mode 2 constant current; default mode 4 PD position | Torque + stiffness/damping hybrid | Not explicitly specified | Mode 2 constant current; output register 44 |
| Feedback | Position/speed/current/voltage/temperature/PWM | Position/speed/current/voltage/temperature/load | Rotor torque/angle, output angle, velocity, temperature, voltage | Position/current/speed/voltage/temperature | Load/position/speed/voltage/current/temperature |
| Encoder | 12-bit absolute output | 12-bit magnetic | Dual absolute; rotor 15-bit plus output | Magnetic, 360°, 0.088°/count | 12-bit magnetic |
| Motor / gears | Iron-core / plastic | Coreless / metal | Brushless / plastic | Brushed / POM | Iron-core / metal |
| IDs | 0–252 | 0–253; factory 1 | **0–14** | 0–253 | 0–253; factory 1 |
| Historical price | $23.90–27.49 | CNY 123 presale | $29 official listing | Unresolved | Unresolved |

The upstream comparison table gave conflicting XL330 dimensions (23 / 29 mm
alongside the manual's 26 mm). Use the actual drawing and mounting surfaces
rather than treating those envelopes as interchangeable.
The root README also gives a different historical HD-1910 price and an
unspecified-voltage speed figure.

### HD-1910 voltage points

| Voltage | No-load speed | Stall torque | Rated torque | Stall current |
|---|---|---|---|---|
| 4.8 V | 73 rpm | 9 kg·cm | 2.2 kg·cm | 1.2 A |
| 6 V | 92 rpm | 12 kg·cm | 3 kg·cm | 1.6 A |
| 7.4 V | 113 rpm | 15 kg·cm | 3.7 kg·cm | 2 A |

Specified torque constant: **7.5 kg·cm/A**.

RD05T at 6 / 5 V: no-load 125 / 100 rpm (0.08 / 0.10 s per 60°);
stall 6 / 5.2 kg·cm; rated 1.5 / 1.2 kg·cm; stall current 1740 / 1470 mA.

### Practical implications

- HD-1910's **pin 1 / pin 3 order is reversed** relative to the listed Dynamixel, RD05T, and HL-2915 connectors. Do not plug in an XL330-style cable without checking orientation and polarity.
- Unitree's ID range 0–14 cannot directly represent the joint map below or IMU ID 200.
- RD05T covers the ID range but needs a verified protocol implementation; its rated torque is half the HD-1910's at 6 V.
- Similar size does not establish matching hole spacing or passive-horn clearance.
- A 12 V actuator requires a different power design. HD-1910 and RD05T can be considered for a 2S design, subject to protection and actual component ratings.
- The HD-1910 specification lists a 10 V overvoltage threshold; this is **not** its normal maximum operating voltage, which remains 8.4 V.
- Size wiring and supply for measured simultaneous loads and transients; a single-servo current figure is not a complete robot power budget.

## 4. Bus rate and IDs

The documented reference bus is `/dev/ttyS2`, **1,000,000 bps**, Dynamixel
Protocol 2.0, shared by 15 servos and IMU ID 200.
A Feetech driver must use the appropriate vendor protocol and register map.

| Group | IDs and joints |
|---|---|
| Right leg | 10 hip_yaw; 11 hip_roll; 12 hip_pitch; 13 knee; 14 ankle |
| Left leg | 20 hip_yaw; 21 hip_roll; 22 hip_pitch; 23 knee; 24 ankle |
| Head/neck/mouth | 30 neck_pitch; 31 head_pitch; 32 head_yaw; 33 head_roll; 34 mouth |
| Body IMU | 200 |

Configure and label **one unmounted servo at a time** before connecting the full
chain, so factory ID collisions do not make configuration ambiguous.
Use the datasheet for that servo's baud register; the XL330 values below are
not Feetech configuration values.

### XL330 startup settings

The reference `check_and_fix_config` enforces:
`return_delay_time=0`, `baud_rate=3`, `pwm_slope=255`, `shutdown=52`.

| XL330 Baud Rate(8) value | bps |
|---|---:|
| 0 | 9,600 |
| 1, factory default | 57,600 |
| 2 | 115,200 |
| 3 | 1,000,000 |
| 4 | 2,000,000 |
| 5 | 3,000,000 |
| 6 | 4,000,000 |
| 7 | 4,500,000 |

An unconfigured XL330 at 57,600 bps will not answer a 1 Mbps scan.
The factory return delay of 250 corresponds to 500 µs per device; across 16
devices that is about 8 ms of a 20 ms control period. Reducing delay is separate
from setting baud rate.

The 50 Hz design budgets two bus transactions per tick plus slow telemetry.
Validate the alternative protocol's packet lengths and timing; do not run the
15-servo chain at a low factory baud and assume the same timing contract.

## 5. Sources

- [XL330-M288 manual](https://docs.robotis.com/docs/dxl/model_reference/x_series/xl_series/xl330-m288/)
- [ROBOTIS Korea](https://en.robotis.com/shop_en/item.php?it_id=902-0163-000), [US](https://www.robotis.us/dynamixel-xl330-m288-t/)
- [robotd control loop](https://github.com/pollen-robotics/microduck/blob/main/docs/design/robotd-design.md), [rustypot](https://github.com/pollen-robotics/rustypot)
- [Unitree digital servo](https://www.unitree.com/cn/DigitalServo), [store](https://shop.unitree.com/products/brushless-digital-servo)
- [HD-1910 specification, A/0, 2026-09-07](../hardware_spec/servo/HD-1910-C001-spec-20260907.pdf)
- [HD-1910 drawing](../hardware_spec/servo/HD-1910M-C001-drawing-20260902.pdf)
- [HL-2915 / HL-2909 specification, A/0, 2026-02-27](../hardware_spec/servo/HL-2915-C002_HL-2909-C001-spec-20260227.pdf)
- [KPower RD05T specification](../hardware_spec/servo/KPower-RD05T-spec-2026-09.pdf)
- [BAM / training](https://github.com/pollen-robotics/microduck_rl)

