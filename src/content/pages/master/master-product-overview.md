# 2.2 Product Overview

The FF Master series includes three versions: `FF Master`, `FF Master Edu`, and `FF Master Ultra`.

Each version differs slightly in configuration and functional capability, with a total of 27 to 31 degrees of freedom across the series, enabling precise motion and posture control.

## FF Master

- Equipped with a total of 25 degrees of freedom.
- Each arm has 5 DOF and each leg has 6 DOF; the waist has 3 DOF.
- The head is equipped with RGB cameras and interactive hardware including a microphone, speaker, interactive display, and touch sensors.
- The computing unit includes a main control board RK3588 and an interactive computing board RK3588s.
- This version does not support secondary development and is not compatible with the Locomotion & Manipulation Platform.

## FF Master Edu

- Equipped with a total of 25 degrees of freedom.
- Adds 4G/5G communication modules on top of FF Master.
- This version does not support full secondary development, but it is compatible with the Locomotion & Manipulation Platform.

## FF Master Ultra

- Equipped with a total of 30 degrees of freedom.
- Adds a LiDAR sensor, front dual RGB cameras, an RGB-D camera, and a rear RGB camera.
- Equipped with an Nvidia Orin NX computing unit and comes standard with 4G/5G communication modules.
- Supports optional accessories such as the Omni-Picker, teleoperation, and charging station modules.
- Supports full secondary development and is compatible with the Locomotion & Manipulation Platform.

## 2.2.1 Product Structure Diagram (Ultra Edition)

The following diagrams illustrate the main components of the FF Master Ultra.

![Product structure 1](/images/master/master-product-overview-1.png)

![Product structure 2](/images/master/master-product-overview-2.png)

![Product structure 3](/images/master/master-product-overview-3.png)

## 2.2.2 User Debugging Interface (FF Master Ultra)

![User debugging interface](/images/master/master-product-overview-4.png)

| No. | Interface Type | Interface Name | Interface Description |
| --- | --- | --- | --- |
| 1 | RK3588 USB | USB Type-A | Supports USB 3.0 host, 5V/1.5A power output |
| 2 | RK3588 USB | USB Type-C | Supports USB 3.0 host, 5V/1.5A power output |
| 3 | Orin NX USB | USB Type-A | Supports USB 3.0 host, 5V/1.5A power output |
| 4 | Orin NX USB | USB Type-C | Supports USB 3.0 host, 5V/1.5A power output |
| 5 | SIM card slot | SIM card slot | 5G module SIM card slot |
