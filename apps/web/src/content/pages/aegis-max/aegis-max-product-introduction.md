# Product Introduction

## 2.1 Product Overview

Aegis Max is a wheel-legged quadruped robot featuring lightweight design, high load capacity, long endurance, strong protection, and flexible, stable movement. Each leg is equipped with three joint motors and one hub motor, forming a wheeled leg. It is equipped with sensors including LiDAR, optical cameras, ultrasonic radar, IMU, fill lights and RTK modules. Internally it incorporates a high-performance main platform for motion control, autonomous navigation and positioning, and environmental detection, and it provides a rich set of power supply and communication interfaces supporting the expansion of multiple categories of mission payload.

![FF Aegis Max figure 1 — description pending review](/images/aegis-max/aegis-max-figure-01.png)

*Source figure — reference only; FF artwork required before publication.*

## 2.2 Component Name

![FF Aegis Max figure 2 — description pending review](/images/aegis-max/aegis-max-figure-02.png)

*Source figure — reference only; FF artwork required before publication.*

![FF Aegis Max figure 3 — description pending review](/images/aegis-max/aegis-max-figure-03.png)

*Source figure — reference only; FF artwork required before publication.*

Callouts: Ultrasonic Mounting Rail · Hard Emergency Stop · Upper Bumper · Lower Bumper · RF Antenna · Thigh · Battery · Lower Leg · Wheel-Leg · Rearward Indicator Light · Forward Indicator Light · Ambient Light Sensor · Fill Light · Expansion Bay Entrance · Optical Camera · Expansion Bay · LiDAR · RTK Interface · Contact Charging Assembly.

## 2.3 Core Specification

| Category | Specification | Description |
| --- | --- | --- |
| Basic Information | Product Model | [FF model code to be assigned] |
|  | Material | Aluminium alloy + high-strength engineering plastic |
|  | Size (standing) | 930 mm × 480 mm × 585 mm |
|  | Size (lying prone) | 930 mm × 630 mm × 200 mm |
|  | Machine weight (with battery) | 41 kg |
|  | Battery weight | 3.3 kg per unit |
|  | Wheel size | 8 inches |
|  | Ingress protection | IP67 |
|  | Operating temperature | -20℃ ~ 55℃ |
| Motion Performance | Degrees of freedom | 12+4 DOF |
|  | Max speed | 6 m/s |
|  | Effective payload | 25 kg (pending FF confirmation) |
|  | Max climb angle | 45° |
|  | Continuous climbable step height | 25 cm |
|  | Vertical obstacle crossing height | 80 cm |
|  | Load-bearing span | 50 cm |
|  | Minimum turning radius | Supports turning around in place and switching between forward and reverse directions |
|  | Crawling height | 34 ± 0.5 cm |
| Battery Parameters | Battery capacity | 504.9 Wh × 2; dual batteries supporting quick replacement with hot-swap capability |
|  | No-load runtime | 5 ± 0.5 h |
|  | Full-load runtime | 3.5 ± 0.5 h |
|  | No-load range | 29 ± 1 km |
|  | Full-load range | 18 ± 1 km |
|  | Charging dock input voltage | AC 100–240 V |
|  | Charging dock output voltage / current | DC 63 V, max charging current 10 A |
|  | Charging time |  |

### Notes:

(1) For instructions on using the functional expansion interface, refer to the expansion manual.

(2) For detailed warranty terms, refer to the product warranty manual.

(3) The above parameters are laboratory test data. Actual performance may vary due to usage environment, operation methods and other factors. Refer to actual product performance.

## 2.4 Description of Light Effect

Status Indicator

| Colour | Effect | Robot Status |
| --- | --- | --- |
| White | Slow flash | Startup in progress |
| White | Normally on | Manual control / working state |
| White | Breathing | Standby |
| Green | Slow flash | Locating / auto return in progress |
| Green | Normally on | Auto task execution in progress |
| Yellow | Quick flash | Alarm state |
| Yellow | Normally on | Low battery |
| Red | Quick flash | Fault state |
| Red | Normally on | Soft emergency stop |
| Blue | Normally on | Upgrading |
| — | Breathing | Charging (optional charging pile) |

- Hard emergency stop: the red status indicator is normally on and the red light of the hard emergency stop button is normally on.
- Forward / reverse direction switch: when the robot switches between forward and reverse directions, the status light on the corresponding direction illuminates, followed by the lighting effect above.
- Except when switching between forward and reverse main direction states, where the front and rear lights differ, the lights are consistent in all other situations.

![FF Aegis Max figure 4 — description pending review](/images/aegis-max/aegis-max-figure-04.png)

*Source figure — reference only; FF artwork required before publication.*

Battery Indicator

![FF Aegis Max figure 5 — description pending review](/images/aegis-max/aegis-max-figure-05.png)

*Source figure — reference only; FF artwork required before publication.*

| Indicator Effect | Battery Level |
| --- | --- |
| 4 LEDs normally on | 75%–100% |
| First 3 LEDs normally on | 50%–75% |
| First 2 LEDs normally on | 25%–50% |
| First LED normally on | 0%–25% |
| First LED flashing | 0% |
| 4 LEDs illuminated in sequence | Charging; all 4 stay lit when fully charged |

Emergency Stop Indicator

![FF Aegis Max figure 6 — description pending review](/images/aegis-max/aegis-max-figure-06.png)

*Source figure — reference only; FF artwork required before publication.*

| Indicator | State |
| --- | --- |
| Off | Hard emergency stop not triggered |
| Red, normally on | Hard emergency stop triggered |

## 2.5 Expansion Interface

![FF Aegis Max figure 7 — description pending review](/images/aegis-max/aegis-max-figure-07.png)

*Source figure — reference only; FF artwork required before publication.*

| No. | Interface |
| --- | --- |
| ① | 48 V (10 A) × 1 |
| ② | 24 V (20 A) × 1 |
| ③ | 24 V (3 A) + 1 × Ethernet port |
| ④ | 12 V (5 A) + 1 × Ethernet port |
| ⑤ | Serial port (RS232 × 1, RS485 × 1, SBUS × 2, PPS × 1) |
| ⑥, ⑦ | 2 × USB 3.0 (5 V, 1 A) |
| ⑧ | RTK interface |
| ⑨ | Expansion bay button |

### Warning

- When installing additional equipment on the back of the robot, consult after-sales service staff regarding the planning and design of centre of gravity, position, interface and wiring before formal installation.
- The total power supplied by all power interfaces is ≤ 480 W.
- If an aviation plug is used, a protective cap shall be fitted to ensure the IP67 rating. The protective cap shall be secured when the aviation plug is not in use.
- The expansion bay button controls the power supply to the expansion interface. When connecting assemblies, power off the expansion bay first.

## 2.6 Mode of Motion

The robot comes standard with a reinforcement learning locomotion model, featuring Stationary Mode, Sport Mode, Navigation Mode and Stair Climbing Mode.

| Mode | Description |
| --- | --- |
| Stationary Mode | The robot remains stationary while its torso performs various actions including rotation, pitch and height adjustment. |
| Sport Mode | The robot automatically adapts to flat ground, slopes, stairs and complex terrain such as mountains, forests and rubble. It supports forward and backward movement and in-place rotation, and can perform standing, crawling, prone and locked postures, as well as advanced manoeuvres such as climbing elevated platforms and twisting motions. |
| Navigation Mode | Maps can be created in this mode. Once the map is generated, the fixed-point cruise function can be enabled based on the map to achieve automated inspection and fixed-point operations. |
| Stair Climbing Mode | The robot autonomously plans its gait to traverse multi-level staircases with stability, suitable for multi-storey operations. |

### Warning

- When performing high-platform climbing manoeuvres, ensure the robot has ≥ 2 battery bars and is unloaded, keep it in sight, and maintain a safety distance of ≥ 2 m from bystanders.
- When navigating stairs, slopes or similar surfaces, ensure no one is directly above, below or within the robot's path.
- In Sport Mode the robot has standard low, medium and high speed settings. To ensure safe task execution, lateral movement and in-place rotation are restricted at medium and high speeds.
