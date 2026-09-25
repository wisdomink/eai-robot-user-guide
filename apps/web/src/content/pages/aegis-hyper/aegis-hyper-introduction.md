# Introduction

![FX Aegis Hyper dimensions and package contents](/images/aegis-hyper/aegis-hyper-figure-04.png)

## 1.1 Overview

FX Aegis Hyper is an intelligent quadruped robot designed to meet core industry needs,

with a total of 12 degrees of freedom (DOF), capable of walking, going up and down the

stairs. The robot is equipped with a wide-angle camera, four laser radars, and two internal

hosts respectively for motion control and environmental perception calculation. An

additional host inside Intelligent Controller is used for navigation and inspections.

470mm

1130mm

285mm

470mm

1000mm

715mm

## 1.2 Product List

Intelligent Controller ×1

Controller ×1

Charger ×1

Repalceable Battery ×1

Aviation Plug ×8

Antistatic Cloth ×1

Robot ×1

(without battery)

Certificate ×1

User Manual ×1

Warranty Card ×1

![FX Aegis Hyper components](/images/aegis-hyper/aegis-hyper-figure-05.png)

## 1.3 Main Specifications

1 Wide Angle Camera

2 Laser Radar

3 Mounting Rails

4 Intelligent Controller Power Button

5 Upper Leg

6 Power Button

7 Charging Port Cover

8 Lower Leg

9 Antislip Foot

10 Controller's Antenna

11 WiFi Antenna

12 Cooling Fan

13 Soft Emergency STOP

14 Hard Emergency STOP

15 Debugging Ethernet Port

16 Laser Radar

![FX Aegis Hyper figure 6](/images/aegis-hyper/aegis-hyper-figure-06.png)

### Robot dimensions

| Item | Specification |
| --- | --- |
| Sitting size (L × W × H) | 1130 mm × 470 mm × 285 mm |
| Standing size (L × W × H) | 1000 mm × 470 mm × 715 mm |
| Weight | 59 kg |

### Electrical parameters

| Item | Specification |
| --- | --- |
| Battery capacity | 22.4 Ah (ideal data at 25℃) |
| Nominal battery voltage | 72 V |
| Charger input voltage | 200–240 V AC |
| Charger output | 84 V / 8 A |
| Charging time | 2.5–3 hours |
| Power supply | 12 V; 24 V; 5 V USB |
| Communication interfaces | Ethernet; Wi-Fi; USB 2.0; USB 3.0 |
| Autonomous charging | Supported |

### Locomotion parameters

| Item | Specification |
| --- | --- |
| Maximum speed | 4.95 m/s (extreme-test data) |
| Maximum walking speed | 1.2 m/s |
| Maximum running speed | 2.5 m/s |
| Maximum slope | ±30° |
| Maximum step height | 20 cm |
| Maximum staircase slope | ±45° |
| No-load runtime | 4 hours |
| Payload runtime | 2.5 hours |
| Payload | 20 kg, including the intelligent controller |
| Maximum load | 85 kg (extreme-test data) |

![FX Aegis Hyper power and emergency stop controls](/images/aegis-hyper/aegis-hyper-figure-07.png)

### Sensors and environment

| Item | Specification |
| --- | --- |
| Laser radar | 4 |
| Wide-angle camera | 1 |
| Optional module | Bi-spectrum PTZ camera |
| Ingress protection | IP67 |
| Operating temperature | -20℃ to 55℃ |

※Data above is measured under ideal conditions, and the actual results may be biased.

## 1.4 Power and STOP

Power Button

of Intelligent

Controller

Power LED

Power Button of

Robot

Charging Port

Cover

Soft Emergency

STOP Button

Hard Emergency

STOP Button

Light OFF

Power OFF

Power LED

Light ON

Percentage & Voltage

Power ON

Light ON

Light OFF

Hard Emergency Stop OFF

Soft Emergency Stop OFF

Light ON

Light OFF

Soft Emergency Stop Triggered

Hard Emergency Stop Triggered

![FX Aegis Hyper intelligent controller](/images/aegis-hyper/aegis-hyper-figure-08.png)

Power LED

4 lights are always on

75%

1 light is off, 3 lights are always on

50%

2 light are off, 2 lights are always on

25%

3 lights are off, 1 light is flashing

5%

4 lights are off

Current Battery Level ≤ 5%

4 lights cycle on

Charging: Current Battery Level ≤ 25%

1 light is always on, 3 lights cycle on

Charging: 25%

2 lights are always on, 2 lights cycle on

Charging: 50%

3 lights are always on, 1 light flashes

Charging: 75%

## 1.5 Intelligent Controller

Indicator light

Intelligent Controller's

Power Button

Light OFF

Intelligent Controller OFF

Light ON

Intelligent Controller ON

Intelligent Controller Indicator Light

Intelligent Controller is working normally.

Always on and green light

Green flashing light

Robot is charging.

Yellow flashing light

Robot is avoiding obstances when in navigation.

Red flashing light

Robot battery is not enough.

Light off

Intelligent Controller is not powered on.

![FX Aegis Hyper intelligent controller interfaces](/images/aegis-hyper/aegis-hyper-figure-09.png)

⑤USB2.0×2

Interface

①LAN1+12V

⑥ LAN3+12V

②LAN2

⑦ LAN4+12V

③24V

⑧ LAN5+24V

④USB3.0x2

⑨ LAN6+24V

※When the USB 3.0 interface is not in use, the intelligent controller maintains an IP67 protection rating.

If the dust- and water-proof cap is removed to use the USB 3.0 intelligent, additional protective measures

are required to preserve dust and water resistance.

## 1.6 Mode and Gait

Control Mode

Manual

Robot is completely controlled by the user through the controller

The perception host will monitor the surrounding environment and

Assist

assist the user in controlling the robot

Navigation

Robot moves autonomously and can not be controlled with the controller

Body Height

Normal

Robot stands normally

Crawling

Suitable for passing through the terrain with smaller longitudinal height

![FX Aegis Hyper figure 10](/images/aegis-hyper/aegis-hyper-figure-10.png)

Gait

Walking

Suitable for flat surfaces such as concrete (limited max speed: 1.2m/s)

Running

Suitable for flat surfaces such as concrete (limited max speed: 2.5m/s)

Slope

Suitable for slopes less than 30° or other gentle irregular terrain

Suitable for complex terrain through irregular obstacles such as stone

Off-Road

piles and ruins

It can perceive the shape of the staircase and calculate the foothold on

Stair

its own, which is suitable for stairs with a slope under 45°

It can perceive the shape of the staircase and calculate the foothold

45° Stairs

on its own, which is suitable for stairs with a slope of 45°, and is only

supported in multi-frame mode

Utilizes AI algorithms, suitable for surfaces with slight undulations

L-Walk

under normal conditions

Utilizes AI algorithms, suitable for complex terrain with height

Mountain

differences, slopes and stairs

Utilizes AI algorithms, suitable for scenarios requiring reduced robotic

Silent

motion noise.

※L-Walk is suitable for surfaces with little undulations, including but not limited to flat surfaces, muddy

surfaces, flooded surfaces, undulating surfaces with small differences in height, stairs with a single step of

15cm, slopes of 18° , etc.

※Mountain is suitable for surfaces with large undulations under normal conditions, including but not

limited to rubble surfaces, bumpy surfaces with large differences in elevation, stairs with a single step of

25cm, and slopes of 30° .

※Silent is suitable for noise cancellation demand scenarios, the gait noise when standing still

≤ 50dB,

walking noise ≤ 60dB, does not support walking up and down stairs, walking on slopes.

- When the robot passes through stairs or slopes, do not stand on the

stairways, platforms or slopes below the robot, to avoid possible

personal injury if the robot falls.

- The robot can only climb stairs when its front faces the upward

direction of the staircase.

Using mountain gait generates a lot of heat, and the continuous use

of this gait to cross obstacles within a short period of time will easily

cause the robot to overheat, so it is recommended not to use this gait to

climb stairs for more than 8 minutes continuously.

![FX Aegis Hyper figure 11](/images/aegis-hyper/aegis-hyper-figure-11.png)

Elevation Map Mode

Suitable for scenarios where the robot's landing plane

Solid ground mode

is solid, such as a normal solid concrete flat floor or

concrete stairs.

Suitable for scenarios where the robot's landing plane

is a grid-like pattern with gaps in between, such as an

Grid ground mode

industrial platform or staircase made of steel grating

panels.

A special condition of solid ground, which refers to a

Stair without risers mode

staircase where the robot places its feet on a solid surface

without risers.

Suitable for scenarios including multiple types of ground

Multi-frame mode

surfaces or 45° stairs. For example, if the robot moves

from solid ground to grid ground.
