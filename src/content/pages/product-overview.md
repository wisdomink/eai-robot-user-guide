# Product Overview

The FF Master series includes three versions: FF Master, FF Master Edu and FF Master Ultra. Each version differs slightly in configuration and functional capability, with a total of 27–31 degrees of freedom (DOF) across the series, enabling precise motion and posture control.

FF Master:
- FF Master is equipped with a total of 27 degrees of freedom (DOF). The head has 2 DOF, each arm has 5 DOF (including shoulder, upper arm, and elbow joints), each leg has 6 DOF (including hip, thigh, knee, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).
- The head is equipped with RGB cameras and interactive hardware, including a microphone, speaker, interactive display, and touch sensors. The computing unit includes a main control board RK3588 and an interactive computing board RK3588s.
- This version does not support any secondary development, and it is NOT compatible with the Locomotion & Manipulation Platform (under development, will release soon).

FF Master Edu:
- FF Master Edu is equipped with a total of 27 degrees of freedom (DOF). The head has 2 DOF, each arm has 5 DOF (including shoulder, upper arm, and elbow joints), each leg has 6 DOF (including hip, thigh, knee, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).
- Building upon the FF MASTER, the FF MASTER Edu equipped with 4G/5G communication modules.
- This version does not support full secondary development, but it is compatible with the Locomotion & Manipulation Platform (under development, will release soon).

FF Master Ultra:
- FF Master Ultra is equipped with a total of 31 degrees of freedom (DOF). The head has 2 DOF, each arm has 7 DOF (including shoulder, upper arm, elbow, wrist, and finger joints), each leg has 6 DOF (including hip, thigh, knees, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).
- Building upon the FF MASTER, the FF MASTER Ultra adds a LiDAR sensor, front-facing dual RGB cameras, an RGB-D camera, and a rear RGB camera. It is equipped with a high-performance Nvidia Orin NX computing unit and comes standard with 4G/5G communication modules. The FF MASTER Ultra also supports optional accessories such as the Omni-Picker, as well as optional teleoperation and charging station modules.
- This model supports full secondary development and is also compatible with the Locomotion & Manipulation Platform (under development, will release soon).

## Product Structure Diagram (Ultra Edition)

Note:
The following diagram illustrates the main components of the FF Master Ultra.

![](/images/docx/product-structure-1.png)

![](/images/docx/product-structure-2.png)

![](/images/docx/product-structure-3.png)

## User Debugging Interface (FF Master Ultra)

No. Interface Interface Interface Type Name Description
1 RK3588 USB Supports USB USB Type-A 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth.
2 RK3588 USB Supports USB USB Type-C 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth.
3 Orin NX USB Supports USB USB Type-A 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth.
4 Orin NX USB Supports USB USB Type-C 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth.
5 SIM card SIM card 5G module SIM slot slot card slot.

![](/images/docx/debugging-interface-1.png)

## Software Development Kit

Interface
No. Interface Interface Interface Type Name Description
1 RJ45 1000 Gigabit Ethernet, Base-T accessible by both Orin NX and RK3588
2 RJ45 1000 Gigabit Ethernet, Base-T accessible by both Orin NX and RK3588
3 XT30UPB 12V 12V/3A Power -F Power Output Port
4 XT30UPB 48V 48V/5A Power -F Power Output Port

![](/images/docx/sdk-interface-1.png)
