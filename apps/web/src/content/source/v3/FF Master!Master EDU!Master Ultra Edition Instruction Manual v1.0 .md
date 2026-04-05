# 1. Preliminary Notice&#x20;

### 1.1 Safety Instructions&#x20;

1. Product Knowledge: Before using the robot, please carefully read the user manual to understand the robot's functions, operation methods, and safety precautions.&#x20;

2. Comply with Usage Requirements: Ensure that the robot is operated in a flat environment. Avoid extremely high or low temperatures, humid environments, steep slopes, surfaces with large drops, fragile surfaces, and vibrating areas.&#x20;

3. Operating Space: Ensure that the robot has sufficient operating space. Avoid operating in cramped or crowded environments to reduce the risk of collision and crushing.&#x20;

4. Emergency Stop Function: During operation, users must be familiar with the location and operation of the emergency stop button on the robot remote control so that they can stop the robot in an emergency. When an emergency stop is activated, the robot will lose force from all joints and collapse to the ground. In this case, please pay attention to the robot's safety and always use the protective cage. Do not use the emergency stop function except in emergency situations.&#x20;

5. Power Safety: Before operation, ensure that all cables, plugs, and sockets are intact. Immediately disconnect the power supply if an abnormality (such as a short circuit or overheating) occurs. &#x20;

6. Regular Inspection: Perform regular maintenance and inspections to ensure the proper functioning of robot components, such as joints, sensors, and power supplies, to prevent hazards caused by aging or damage.&#x20;

7. Prevent Misuse: Ensure the robot is not used in any inappropriate, dangerous, or legally prohibited manner.&#x20;

8. This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to radio communications. However, there is no guarantee that interference will not occur in a particular installation. If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:&#x20;

   • Reorient or relocate the receiving antenna.&#x20;

   • Increase the separation between the equipment and receiver.&#x20;

   • Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.&#x20;

   • Consult the dealer or an experienced radio/TV technician for help.&#x20;

   &#x20;

   Note:&#x20;

   This device complies with part 15 of the FCC Rules. Operation is subject to the following two conditions:&#x20;

   (1) This device may not cause harmful interference, and&#x20;

   (2) this device must accept any interference received, including interference that may cause undesired operation.&#x20;

&#x20;

### 1.2 Safety Guidelines&#x20;

1. Pre-Startup Confirmation:&#x20;

   1. Before starting the robot, ensure that its working area is clear of people or other obstacles, especially near its moving parts.&#x20;

   2. Before starting the robot, the operator must confirm that the system is in normal condition and has completed self-tests.&#x20;

2. Safety Distance: Maintain a safe distance (≥ 50 cm) from the robot's working area to avoid accidental collisions. Especially when the robot is performing high-speed movements, avoid standing near the movement path.&#x20;

3. Load and Operation:&#x20;

   1. Strictly adhere to the load limits specified for the robot and avoid overloading.&#x20;

   2. When using the robot's actuators, grippers, or other components, ensure that they are properly aligned with the object being operated to avoid unnecessary pressure and stress.&#x20;

4. Emergency Stop: In the event of an accident or loss of control, use the stop function on the remote control.&#x20;

5. Manual Intervention: Direct intervention in the robot's movements is prohibited during operation. Any adjustments or manual intervention must be performed when the robot is completely stopped and powered off.&#x20;

6. Preventing Mis-operation: Ensure all operators receive training on proper robot operation and emergency response to prevent accidents caused by mis-operation.&#x20;

7. Remote Operation Security:&#x20;

   1. If developing remote operation capabilities for robots, ensure a secure network environment is used to prevent control failures due to network failures or external intrusions.&#x20;

   2. When remotely controlling, operators must have real-time monitoring equipment to ensure a full understanding of the robot and its surroundings.&#x20;

### 1.3 Maintenance and Management Guidelines&#x20;

1. Regular Maintenance: Maintenance and upkeep should be carried out regularly according to the recommendations of FF EAI-Robotics. This ensures that all parts of the robot remain in optimal working condition and helps extend the overall service life of the equipment.&#x20;

2. Fault Handling：&#x20;

   1. If a malfunction occurs during robot operation, immediately stop the operation and promptly notify professional technicians for inspection and repair. Continued operation under fault conditions is strictly prohibited.&#x20;

   2. Do not disassemble, adjust, or repair the equipment while it is powered on or in operation, to avoid further damage or safety hazards.&#x20;

3. Battery and Power Management:&#x20;

   1. If the robot uses batteries, ensure that the batteries are charged in a safe and dry environment.&#x20;

   2. Avoid leaving the robot connected to a power source for extended periods to prevent overcharging or overheating of the battery.&#x20;

   3. In the event of a robot fall, immediately check the condition of the battery. If any damage or deformation is observed, discontinue use and contact the official after-sales service for assistance.&#x20;

4. Software Updates: Regularly check for and update the robot’s operating system and control software to ensure optimal functionality and enhanced system security, preventing potential vulnerabilities and safety risks.&#x20;

# 2. About FF Master&#x20;

### 2.1 Packing List&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-14.png>)

&#x20;

### 2.2 Product Overview&#x20;

The FF Master series includes three versions: FF Master, FF Master Edu and FF Master Ultra. &#x20;

Each version differs slightly in configuration and functional capability, with a total of 27–31 degrees of freedom (DOF) across the series, enabling precise motion and posture control.&#x20;

FF Master: &#x20;

* FF Master is equipped with a total of 25 degrees of freedom (DOF). Each arm has 5 DOF (including shoulder, upper arm, and elbow joints), each leg has 6 DOF (including hip, thigh, knee, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).&#x20;

* The head is equipped with RGB cameras and interactive hardware, including a microphone, speaker, interactive display, and touch sensors. The computing unit includes a main control board RK3588 and an interactive computing board RK3588s.&#x20;

* This version does not support any secondary development, and it is NOT compatible with the Locomotion & Manipulation Platform (under development, will release soon).&#x20;

FF Master Edu:&#x20;

* FF Master Edu is equipped with a total of 25 degrees of freedom (DOF). Each arm has 5 DOF (including shoulder, upper arm, and elbow joints), each leg has 6 DOF (including hip, thigh, knee, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).&#x20;

* Building upon the FF MASTER, the FF MASTER Edu equipped with 4G/5G communication modules.&#x20;

* This version does not support full secondary development, but it is compatible with the Locomotion & Manipulation Platform (under development, will release soon).&#x20;

FF Master Ultra: &#x20;

* FF Master Ultra is equipped with a total of 30 degrees of freedom (DOF). The head has 1 DOF, each arm has 7 DOF (including shoulder, upper arm, elbow, wrist, and finger joints), each leg has 6 DOF (including hip, thigh, knees, and ankle joints), and the waist has 3 DOF (yaw, pitch, and roll).&#x20;

* Building upon the FF MASTER, the FF MASTER Ultra adds a LiDAR sensor, front-facing dual RGB cameras, an RGB-D camera, and a rear RGB camera. It is equipped with a high-performance Nvidia Orin NX computing unit and comes standard with 4G/5G communication modules.&#x20;
  The FF MASTER Ultra also supports optional accessories such as the Omni-Picker, as well as optional teleoperation and charging station modules.&#x20;

* This model supports full secondary development and is also compatible with the Locomotion & Manipulation Platform (under development, will release soon).&#x20;

#### 2.2.1 Product Structure Diagram (Ultra Edition)&#x20;

Note:&#x20;

The following diagram illustrates the main components of the FF Master Ultra.&#x20;

&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename.png>)

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-1.png>)

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-2.png>)

#### 2.2.2 User Debugging Interface (FF Master Ultra)&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-3.png>)

|     |                |                |                                                                                                           |
| --- | -------------- | -------------- | --------------------------------------------------------------------------------------------------------- |
| No. | Interface Type | Interface Name | Interface Description                                                                                     |
| 1   | RK3588 USB     | USB Type-A     | Supports USB 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth.   |
| 2   | RK3588 USB     | USB Type-C     | Supports USB 3.0 host, 5V/1.5A power output; RK3588 USB Type-A and Type-C ports share 5 Gbps bandwidth.   |
| 3   | Orin NX USB    | USB Type-A     | Supports USB 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth. |
| 4   | Orin NX USB    | USB Type-C     | Supports USB 3.0 host, 5V/1.5A power output; Orin NX USB Type-A and Type-C ports share 10 Gbps bandwidth. |
| 5   | SIM card slot  | SIM card slot  | 5G module SIM card slot.                                                                                  |



### 2.3 Computational Unit&#x20;

&#x20;
|   |   |
|---|---|
|Type|On-board computer|
|FF Master / FF Master Edu|One operation and control computing unit（PC1) and one interactive computing unit（PC3)|
|FF Master Ultra|One operation and control computing unit（PC1), one interactive computing unit（PC3) and one development computing unit（PC2)|

|                        |                                                                |
| ---------------------- | -------------------------------------------------------------- |
| Parameter              | Development Computing Unit (PC2)                               |
| Processor              | Jetson Orin NX                                                 |
| AI Performance         | 157Tops                                                        |
| GPU                    | 1,024-core NVIDIA Ampere architecture GPU with 32 Tensor Cores |
| CPU                    | 8-core Arm® Cortex®-A78AE v8.2 64-bit CPU                      |
| Cache                  | 2MB L2 + 4MB L3                                                |
| VRAM (Graphics Memory) | 16G                                                            |
| System Memory (RAM)    | 16G                                                            |
| Storage                | 512GB                                                          |

### 2.4 Battery Indicator Lights&#x20;

Note:&#x20;

When the robot is powered by the battery, please monitor the battery level carefully. If the battery power is low or nearly depleted, the robot may lose power suddenly and collapse. When only one indicator light remains on, charge or replace the battery promptly to ensure stable operation and prevent potential injury or damage caused by the robot falling due to power loss.&#x20;

#### **2.4.1 Battery Indicator Location&#x20;**

&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-4.png>)

&#x20;

&#x20;

#### **2.4.2 Battery Indicator Description&#x20;**

##### **2.4.2.1 Battery Indicator Status (During Discharge)&#x20;**
|                                        |                           |                                              |
| -------------------------------------- | ------------------------- | -------------------------------------------- |
| Battery Indicator Status (Discharging) | Battery Level Description | Status Description                           |
| LEDs 1–4 steady on                     | 75%≤SOC＜100%              | Fully charged                                |
| LEDs 1–3 steady on, remaining off      | 50%≤SOC＜75%               | Battery level sufficient, no action required |
| LEDs 1–2 steady on, remaining off      | 25%≤SOC＜50%               | Normal battery level, no action required     |
| LED 1 steady on, remaining off         | 15%≤SOC＜25%               | Low battery, recharge soon                   |
| LED 1 flashing, remaining off          | SOC＜15%                   | Critically low power, charge immediately     |

##### **2.4.2.2 Battery Indicator Status (During Charging)&#x20;**
|                                              |                           |                                                                                         |
| -------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------- |
| Battery Indicator Status (Charging)          | Battery Level Description | Status Description                                                                      |
| LED1 breathing, LEDs 2–4 off                 | SOC＜25%                   | Initial charging stage, low battery                                                     |
| LED1 steady on, LED2 breathing, LEDs 3–4 off | 25%≤SOC＜50%               | Low battery, not recommended to disconnect power during use                             |
| LEDs 1–2 steady on, LED3 breathing, LED4 off | 50%≤SOC＜75%               | Medium battery level, can be used normally, recommended to continue charging until full |
| LEDs 1–3 steady on, LED4 breathing           | 75%≤SOC＜100%              | Battery nearly full, can be used normally, recommended to continue charging until full  |
| LEDs 1–4 steady on                           | SOC=100%                  | Fully charged, power can be disconnected                                                |

##### 2.4.2.3 Battery Indicator Status (Other Conditions)&#x20;
|     |       |                                  |                         |                         |                         |                                                                |
| --- | ----- | -------------------------------- | ----------------------- | ----------------------- | ----------------------- | -------------------------------------------------------------- |
| No. | Color | LED1                             | LED2                    | LED3                    | LED4                    | Status Description                                             |
| 1   | Green | Displays according to SOC status |                         |                         |                         | Normal                                                         |
| 2   |       | Flashes once per second          | Flashes once per second | Flashes once per second | Flashes once per second | Protection mode (overtemperature, overcurrent, or overvoltage) |
| 3   | Red   | Flashes once per second          |                         |                         |                         | Fault (requires return for repair)                             |
| 4   | -     | All LEDs off                     |                         |                         |                         | Power-off (deep sleep) or very low SOC (< 39V)                 |

### 2.5 Sensor Field of View (Only for Master Ultra)&#x20;
|                           |                                                                                                |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Item                      | Perception Configuration                                                                       | Perception Ability                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| FF MASTER / FF MASTER EDU | Interactive RGB Camera                                                                         | Precision environmental data in real time                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| FF MASTER Ultra           | LiDAR RGB-D Depth Camera Front Stereo RGB Cameras Front Interactive RGB Camera Rear RGB Camera | LiDAR： Captures high-precision environmental data in real time. Rapidly detects and measures surrounding objects. Outputs high-resolution point-cloud data as the core foundation for environmental perception. Additional Camera Suite： RGB-D Depth Camera Provides accurate 3-D spatial information of surroundings. Stereo RGB Cameras Enhances 3-D perception and distance-estimation precision. Rear RGB Camera: Covers rear field eliminating blind spots. Interactive Cameras Enable visual recognition and response during human-robot interaction scenarios. |

&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-5.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Lidar-FOV </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-6.png>)

<span style="color: rgb(143,149,158); background-color: inherit">RGBD-FOV </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-7.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Interactive RGB Camera-FOV-Vertical</span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-8.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Interactive RGB Camera-FOV-Horizontal </span>



### 2.6 Joint Name and Joint Limit&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-9.png>)

&#x20;
|   |   |   |
|---|---|---|
|Joint Name|Joint Limit|   |
|FF Master / FF Master Edu|FF Master Ultra|
|Arm Workspace|J1(Shoulder pitch）: ±146.5°|J1(Shoulder pitch）: ±146.5°|
|J2(Shoulder roll): -3.5~+174.5°|J2(Shoulder roll): -3.5~+174.5°|
|J3(Shoulder yaw): ±146.5°|J3(Shoulder yaw): ±146.5°|
|J4(Elbow): -146.5~0°|J4(Elbow): -146.5~0°|
|J5(Wrist yaw): ±146.5°|J5(Wrist yaw): ±146.5°|
|/|J6(Wrist pitch): ±32°|
|/|J7(Wrist roll): ±88.5°|
|Leg Workspace|J1(Hip pitch): ±146.5°|J1(Hip pitch): ±146.5°|
|J2(Hip roll): -166.5~+13.5°|J2(Hip roll): -166.5~+13.5°|
|J3(Hip yaw): -96.5°~196.5°|J3(Hip yaw): -96.5°~196.5°|
|J4(Knee): 0~121.5°|J4(Knee): 0~121.5°|
|J5(Ankle pitch): -46°~26°|J5(Ankle pitch): -46°~26°|
|J6(Ankle roll): ±15°|J6(Ankle roll): ±15°|
|Head Workspace|J1(Head pitch): ±20°|J1(Head pitch): ±20°|
|J2(Head yaw): ±20°|J2(Head yaw): ±20°|
|Leg Workspace|J1(Waist Yaw) ：-196.5~+136.5°|J1(Waist Yaw) ：-196.5~+136.5°|
|J2(Waist pitch) ：±18°|J2(Waist pitch) ：±18°|
|J3(Waist roll) ：±28°|J3(Waist roll) ：±28°|

### 2.7 Coordinate Systems&#x20;

The coordinate systems for each joint are illustrated in the diagram below, shown when all joints are at their zero-degree position. (Red indicates the X-axis, green the Y-axis, and blue the Z-axis.)&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-10.png>)

&#x20;

### 2.8 Specifications&#x20;
|                                                 |                                                                                                                         |                                                                                                                         |                                                                                                                         |                                                                 |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Item                                            |                                                                                                                         | FF Master                                                                                                               | FF Master Edu                                                                                                           | FF Master Ultra                                                 |
| Overall                                         | Dimensions                                                                                                              | 1310（H）*460（W）*210（L）mm                                                                                                 | 1310（H）*460（W）*210（L）mm                                                                                                 | 1310（H）*460（W）*210（L）mm                                         |
| Height                                          | Approx. 1.31 m                                                                                                          | Approx. 1.31 m                                                                                                          | Approx. 1.31 m                                                                                                          |                                                                 |
| Weight                                          | Approx. 35 kg                                                                                                           | Approx. 35 kg                                                                                                           | Approx. 37 kg                                                                                                           |                                                                 |
| Total actuated DOF                              | 27                                                                                                                      | 27                                                                                                                      | 31                                                                                                                      |                                                                 |
| Neck DOF                                        | 2                                                                                                                       | 2                                                                                                                       | 2                                                                                                                       |                                                                 |
| Single-arm DOF                                  | 5                                                                                                                       | 5                                                                                                                       | 7                                                                                                                       |                                                                 |
| Waist DOF                                       | 3                                                                                                                       | 3                                                                                                                       | 3                                                                                                                       |                                                                 |
| Single-leg DOF                                  | 6                                                                                                                       | 6                                                                                                                       | 6                                                                                                                       |                                                                 |
| Single-arm reach (without end-effector)         | 437mm                                                                                                                   | 437mm                                                                                                                   | 558mm                                                                                                                   |                                                                 |
| Operating temperature                           | -10℃~40℃                                                                                                                | -10℃~40℃                                                                                                                | -10℃~40℃                                                                                                                |                                                                 |
| Perception System                               | RGB camera                                                                                                              | RGB camera                                                                                                              | RGB camera                                                                                                              | Interactive RGB camera; front dual RGB cameras; rear RGB camera |
| Head touch sensor                               | Equipped                                                                                                                | Equipped                                                                                                                | Equipped                                                                                                                |                                                                 |
| RGB-D camera                                    | /                                                                                                                       | /                                                                                                                       | Equipped                                                                                                                |                                                                 |
| 3D LiDAR                                        | /                                                                                                                       | /                                                                                                                       | Equipped                                                                                                                |                                                                 |
| Communication                                   | Interface                                                                                                               | Wi-Fi, Bluetooth                                                                                                        | Wi-Fi, Bluetooth, 4G/5G module                                                                                          | Wi-Fi, Bluetooth, 4G/5G module                                  |
| Interaction Module                              | Voice                                                                                                                   | Microphone array, mini wireless microphone, speaker                                                                     | Microphone array, mini wireless microphone, speaker                                                                     | Microphone array, mini wireless microphone, speaker             |
| Display                                         | Interactive screen; lighting effects                                                                                    | Interactive screen; lighting effects                                                                                    | Interactive screen; lighting effects                                                                                    |                                                                 |
| Performance Parameters                          | Peak joint torque                                                                                                       | 120N·m                                                                                                                  | 120N·m                                                                                                                  | 120N·m                                                          |
| Speed                                           | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use                                                                        | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use                                                                        | Max 1.5 m/s; recommended ≤ 0.8 m/s for daily use                                                                        |                                                                 |
| Payload                                         | Payload (specific posture): Max 3 kg (excluding end-effector) Payload (full workspace): ≤ 1 kg (excluding end-effector) | Payload (specific posture): Max 3 kg (excluding end-effector) Payload (full workspace): ≤ 1 kg (excluding end-effector) | Payload (specific posture): Max 3 kg (excluding end-effector) Payload (full workspace): ≤ 1 kg (excluding end-effector) |                                                                 |
| Obstacle clearance capability                   | ≤50mm                                                                                                                   | ≤50mm                                                                                                                   | ≤50mm                                                                                                                   |                                                                 |
| Climbing capability                             | ≤15°                                                                                                                    | ≤15°                                                                                                                    | ≤15°                                                                                                                    |                                                                 |
| Power System                                    | Battery capacity                                                                                                        | Approx. 500 Wh                                                                                                          | Approx. 500 Wh                                                                                                          | Approx. 500 Wh                                                  |
| Endurance                                       | ~2 h continuous walking at 0.5 m/s                                                                                      | ~2 h continuous walking at 0.5 m/s                                                                                      | ~2 h continuous walking at 0.5 m/s                                                                                      |                                                                 |
| Energy replenishment                            | Supports direct charging and battery swap                                                                               | Supports direct charging and battery swap                                                                               | Supports direct charging and battery swap; optional automatic charging dock                                             |                                                                 |
| Charging time                                   | ≤1.5h                                                                                                                   | ≤1.5h                                                                                                                   | ≤1.5h                                                                                                                   |                                                                 |
| Charger input voltage                           | 100~220V                                                                                                                | 100~220V                                                                                                                | 100~220V                                                                                                                |                                                                 |
| Charger output                                  | 54.6V 10A                                                                                                               | 54.6V 10A                                                                                                               | 54.6V 10A                                                                                                               |                                                                 |
| Control & Compute                               | Base compute board                                                                                                      | RK3588*2                                                                                                                | RK3588*2                                                                                                                | RK3588*2                                                        |
| High-performance compute / secondary dev. board | /                                                                                                                       | /                                                                                                                       | Orin NX 16GB 157 TOPS                                                                                                   |                                                                 |
| Hardware Interfaces                             | USB Host                                                                                                                | USB Type-A*1 USB Type-C*1                                                                                               | USB Type-A*1 USB Type-C*1                                                                                               | USB Type-A*2 USB Type-C*2                                       |
| Ethernet                                        | RJ45*2                                                                                                                  | RJ45*2                                                                                                                  | RJ45*2                                                                                                                  |                                                                 |
| Audio/Video output                              | /                                                                                                                       | /                                                                                                                       | miniDP*1                                                                                                                |                                                                 |
| Power input ports                               | /                                                                                                                       | /                                                                                                                       | 12 V/3A *1 48V/5A*1                                                                                                     |                                                                 |
| Others                                          | Smart OTA upgrade                                                                                                       | NOT Equipped                                                                                                            | Equipped                                                                                                                | Equipped                                                        |
| Handheld remote controller                      | Equipped                                                                                                                | Equipped                                                                                                                | Equipped                                                                                                                |                                                                 |
| Mobile app                                      | Under development, will release soon                                                                                    | Under development, will release soon                                                                                    | Under development, will release soon                                                                                    |                                                                 |
| Secondary development (SDK)                     | /                                                                                                                       | /                                                                                                                       | Equipped                                                                                                                |                                                                 |

# 3. Operation Guide&#x20;

### 3.1 Safety Precautions&#x20;

Note：&#x20;

1. Transportation and Lifting Safety: When transporting or lifting the robot, avoid compression or collision to prevent structural damage or potential safety hazards.&#x20;

2. Ground Environment Requirements: Place the robot on a hard, flat, and non-slippery surface. The ground material should meet a static friction coefficient greater than 0.4 to prevent the robot from unintended movement or tipping.&#x20;

3. Operating Space Reservation: It is recommended to reserve a safety area with a radius of not less than 1 meter around the robot. Personnel are not allowed to stand within this area to ensure operational safety and provide sufficient space for robot movement.&#x20;

4. Robot Battery Management: When powered by the battery, pay close attention to the battery status. Once the battery power is cut off, the robot may lose power and fall. When only one indicator light remains, charge or replace the battery in time to prevent potential injury caused by tipping.&#x20;

5. Remote Controller Power Management: Ensure that the remote controller has sufficient power. Low power may prevent normal mode switching and cause unexpected tipping. If low power is detected, charge the controller in time.&#x20;

6. Mode Usage Restriction: Under non-emergency conditions, do not activate the emergency stop mode (zero-torque mode) or damping mode, as these modes will disable joint torque and may cause the robot to fall.&#x20;

### 3.2 Start-Up Guide&#x20;

#### 3.2.1 Start-Up with Hoisting (Gantry Needed)&#x20;

**Step 1: Hoist the Robot Body&#x20;**

* Open the package as shown in the illustration and slowly lift the robot out.&#x20;

* Use the protective lifting frame to suspend the robot naturally, ensuring that the feet do not touch the ground.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-11.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-1: Unbox </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-12.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-2：Carefully Lift Out the Robot </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-13.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-3：Suspend the robot naturally, ensuring that the feet do not touch the ground. </span>



**Step 2: Install the Battery  &#x20;**

* If the battery is not installed, insert it into the rear battery slot from the outside toward the inside.&#x20;

* Push it down until you hear a *“click”*, indicating it is properly seated.&#x20;

* After installation, press down lightly again to confirm the battery is fully inserted and locked.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-15.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step2: Install Battery </span>
&#x20;

**Step 3: Power On&#x20;**

* Before powering on, make sure the battery level is at least two bars (≥50%).&#x20;

* Short press the power button on the back of the battery to wake the system, then long press for 5 seconds to power on.&#x20;

* After powering on, LEDs 1–4 on the battery will light up sequentially within about 2 seconds, indicating successful startup.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-16.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step3：Press the power button to start the robot. </span>
&#x20;

**Step 4:  Switch to Standing Preparation Mode (Position-Controlled Standing)&#x20;**

Initialization: After powering on, wait for about 1 minute. Do not perform any operations during this period.&#x20;

When all joints enter the zero-torque state, the initialization is complete.&#x20;

Adjust Suspension: After initialization, lower the suspension ropes until both feet of the FF MASTER robot are fully in contact with the ground. The robot will then enter the standing preparation mode (position-controlled standing).&#x20;

Enter Standing Preparation Mode: On the remote controller, press the \[L2 + X] buttons simultaneously to confirm and activate the standing preparation mode (position-controlled standing).&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-17.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step4-1：In zero-torque mode, ensure that the soles of the feet are in contact with the ground. </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-18.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step4-2：Use the remote controller to switch the robot to the standing preparation mode, ensuring both feet are fully in contact with the ground. </span>



**Step 5: Lower the Robot&#x20;**

* Use the electric hoisting device to slowly lower the robot until both feet are fully in contact with the ground.&#x20;

* Ensure the suspension ropes are completely relaxed with some slack remaining.&#x20;

* During the process, make sure the robot remains upright and does not tilt.&#x20;

**Step 6: Enter Stable Standing Mode (Force-Controlled Standing)&#x20;**

Note: Before switching to the stable standing mode (force-controlled standing), make sure the robot has been fully lowered to the ground and both feet are completely in contact with the surface.&#x20;

Enter Stable Standing Mode (Force-Controlled Standing):&#x20;

Press \[R2 + X] on the remote controller simultaneously to activate the stable standing mode (force-controlled standing). Refer to the corresponding diagram for reference.&#x20;

Release the Suspension Hooks:&#x20;

After the FF MASTER robot has reached a stable standing state, the suspension hooks can be fully released.&#x20;

In stable standing mode (force-controlled standing), the robot can maintain balance during slight movement and supports full-body motion control.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-19.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step6: Use the remote controller to switch the robot to Stable Standing Mode (Force-Controlled Standing Mode). </span>
&#x20;

**Step 7: Enter Locomotion Mode&#x20;**

After entering stable standing mode, use the remote controller for “stick-to-move” operation:&#x20;

* Left stick forward/backward: move forward/backward.&#x20;

* Left stick left/right: strafe left/right.&#x20;

* Right stick left/right: rotate in place (turn left/right).&#x20;

#### 3.2.2 Start-Up from Supine Position (No Gantry Needed）&#x20;

**Step 1: Unbox and Position the Robot Correctly&#x20;**

* Open the robot’s packaging box and carefully lift out the robot body (see Step 1-1 and 1-2). During handling, avoid any impact or compression to prevent equipment damage.&#x20;

* Place the robot in its folded posture on a flat and secure surface (see Step 1-3). This position is used for checking the rear battery power status or installing the battery.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-20.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-1: Unbox </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-21.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-2: Carefully Lift Out the Robot </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-22.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-3: Place in Folded Posture </span>



**Step 2: Install the Battery     &#x20;**

* If the battery is not installed, insert it into the rear battery slot from the outside toward the inside.&#x20;

* Push it down until you hear a *“click”*, indicating it is properly seated.&#x20;

* After installation, press down lightly again to confirm the battery is fully inserted and locked.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-23.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step2: Install Battery </span>
&#x20;

**Step 3: Power On&#x20;**

* Before powering on, make sure the battery level is at least two bars (≥50%).&#x20;

* Short press the power button on the back of the battery to wake the system, then long press for 5 seconds to power on.&#x20;

* After powering on, LEDs 1–4 on the battery will light up sequentially within about 2 seconds, indicating successful startup.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-24.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step3：Press the power button to start the robot. </span>
&#x20;

**Step 4: Place the Robot Supine&#x20;**

* Adjust the robot to a supine position with both arms and legs extended naturally and the face facing upward. At this point, the robot is in zero-torque mode.&#x20;

\*Refer to the illustration to ensure the head, legs, arms, chest, waist, and hips are in the correct initial positions. Make sure the legs and hips are aligned with the robot’s forward direction.&#x20;

* Before performing the “supine-to-stand” motion, ensure a safety radius of at least 0.5 meters around the robot is clear of any obstacles or objects.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-25.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step4：Supine position ready for stand-up and keep area clear </span>



**Step 5: Execute Supine-to-Stand Power-On&#x20;**

* Using the remote controller, simultaneously short press \[↑ + △] to trigger the supine-to-stand motion.&#x20;

* Once the motion is complete, the robot enters stable standing mode (force-controlled standing) and can proceed with further operations.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-26.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step5：Supine-to-stand motion illustration </span>
&#x20;

**Step 6: Enter Locomotion Mode&#x20;**

After entering stable standing mode, use the remote controller for “stick-to-move” operation:&#x20;

* Left stick forward/backward: move forward/backward.&#x20;

* Left stick left/right: strafe left/right.&#x20;

* Right stick left/right: rotate in place (turn left/right).&#x20;

  Supine-to-Stand Power-On Notes&#x20;

  * Usage limitation: Supine-to-stand motion is not supported when end-effectors such as dexterous hands or grippers are attached, to prevent damage.&#x20;

  * Posture requirement: Before performing the motion, ensure the robot is face-up and all key parts (head, legs, arms, chest, waist, hips) are in the correct starting position to prevent mechanical stress.&#x20;

  * Surface requirement: The robot must be placed on a flat, hard, and level surface to ensure stability and safety during the motion.&#x20;

#### 3.2.3 Start-up from Prone Position (No Gantry Device Required)&#x20;

**Step 1: Unbox and Position the Robot Correctly&#x20;**

* Follow the diagram to open the packaging box and carefully lift the robot out to avoid collision during handling.&#x20;

* Place the robot flat and stably on a level surface as shown in the diagram, ensuring proper posture. This allows you to check the battery status on the back of the robot or install the battery if necessary.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-27.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-1: Unbox </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-28.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-2：Carefully Lift Out the Robot </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-29.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step1-3：Place the robot flat on a level surface to facilitate battery status inspection. </span>
&#x20;

Notes: &#x20;

During the flat placement process, extend the robot’s legs and arms first, then adjust them so the front side faces downward.&#x20;

Ensure that the head, legs, arms, chest, waist, and thighs are positioned as shown in the diagram, with the front side facing downward.&#x20;

**Step 2: Install the Battery  &#x20;**

* If the battery is not installed, insert it into the rear battery slot from the outside toward the inside.&#x20;

* Push it down until you hear a *“click”*, indicating it is properly seated.&#x20;

* After installation, press down lightly again to confirm the battery is fully inserted and locked.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-30.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step2：Install Battery </span>
&#x20;

**Step 3: Power On&#x20;**

* Before powering on, make sure the battery level is at least two bars (≥50%).&#x20;

* Short press the power button on the back of the battery to wake the system, then long press for 5 seconds to power on.&#x20;

* After powering on, LEDs 1–4 on the battery will light up sequentially within about 2 seconds, indicating successful startup.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-31.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step3：Press the power button to start the robot. </span>
&#x20;

**Step 4:  Start-up from Prone Position&#x20;**

Press【 ↑+△】simultaneously on the remote controller to make the robot rise from the Prone Position to a standing position.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-32.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step4: The robot transitions from flat to standing posture. </span>
&#x20;

Notes：&#x20;

1. Prohibited Scenarios: Flat-position start-up is not supported when the robot’s end effector is equipped with a dexterous hand or claw. Performing this action may cause damage to the hand or claw components.&#x20;

2. Posture Requirements Before Start-Up: Before performing the flat-position start-up, ensure the robot is adjusted to a face-down posture.&#x20;
   Make sure that the head, legs, arms, chest, waist, and thighs are correctly positioned to prevent equipment damage due to improper posture.&#x20;

3. Ground Condition Requirements: Place the robot on a flat and solid surface with no slope before initiating the flat-position start-up. This ensures stability during the process.&#x20;

**Step 5: Enter Locomotion Mode&#x20;**

After entering stable standing mode, use the remote controller for “stick-to-move” operation:&#x20;

* Left stick forward/backward: move forward/backward.&#x20;

* Left stick left/right: strafe left/right.&#x20;

* Right stick left/right: rotate in place (turn left/right).&#x20;

#### 3.2.4 Start-up from Sitting Position (No Gantry Device Required)&#x20;

**Step 1: Unbox and Position the Robot Correctly&#x20;**

* Open the robot’s packaging box and carefully lift out the robot body (see Step 1-1 and 1-2). During handling, avoid any impact or compression to prevent equipment damage.&#x20;

* Place the robot in its folded posture on a flat and secure surface (see Step 1-3). This position is used for checking the rear battery power status or installing the battery.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-33.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-1: Unbox</span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-34.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-2: Carefully Lift Out the Robot </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-35.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1-3: Place in Folded Posture </span>

**Step 2: Install the Battery     &#x20;**

* If the battery is not installed, insert it into the rear battery slot from the outside toward the inside.&#x20;

* Push it down until you hear a *“click”*, indicating it is properly seated.&#x20;

* After installation, press down lightly again to confirm the battery is fully inserted and locked.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-36.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step2: Install Battery </span>
&#x20;

**Step 3: Power On&#x20;**

* Before powering on, make sure the battery level is at least two bars (≥50%).&#x20;

* Short press the power button on the back of the battery to wake the system, then long press for 5 seconds to power on.&#x20;

* After powering on, LEDs 1–4 on the battery will light up sequentially within about 2 seconds, indicating successful startup.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-37.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step3：Press the power button to start the robot. </span>
&#x20;

**Step 4: Place the Robot in Sitting Posture&#x20;**

* Posture adjustment: Adjust the robot to the sitting position as shown.&#x20;

* Key requirements:&#x20;

  * Ensure the head, legs, arms, chest, waist, and hips are in the correct initial positions. The legs and hips must align with the robot’s forward direction.&#x20;

  * Place the robot on a stable platform or bench about 35–40 cm high, ensuring firm support.&#x20;

  * The robot is in zero-torque mode; hold the rear handle to maintain balance and prevent falls.&#x20;

* Mode activation: Use the remote controller and short press \[↑ + X] simultaneously to enter the sitting preparation (position-controlled sitting) mode.&#x20;

* Safety tip: During operation, support the robot’s back from behind to maintain stability.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-38.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Adjust robot to sitting position and switch to sitting preparation mode </span>

**Step 5: Stand-Up Power-On&#x20;**

* Operation: Use the remote controller and short press \[↑ + □] simultaneously to make the robot perform the *sit-to-stand* motion.&#x20;

* Mode: After the motion is completed, the robot will automatically enter stable standing mode (force-controlled standing).&#x20;

* Safety Tip: During operation, support the robot from behind by holding the back handle to help maintain balance and prevent it from falling.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-39.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step5: Robot in Standing Position </span>
&#x20;

**Step 6: Enter Locomotion Mode&#x20;**

After entering stable standing mode, use the remote controller for “stick-to-move” operation:&#x20;

* Left stick forward/backward: move forward/backward.&#x20;

* Left stick left/right: strafe left/right.&#x20;

* Right stick left/right: rotate in place (turn left/right).&#x20;

Sitting-to-Stand Power-On Notes：&#x20;

* Before performing the stand-up motion, ensure the robot is placed securely on a platform or bench 35–40 cm high, and stable support is confirmed.&#x20;

* Foot contact: Confirm both feet are fully in contact with the ground before executing the sitting-to-stand motion to prevent abnormal movement.&#x20;

* Posture: Verify all key parts (head, legs, arms, chest, waist, hips) are aligned forward and in the correct initial position to avoid damage.&#x20;

### 3.3 Shutdown Guide&#x20;

#### 3.3.1 Hoisted Shutdown (Gantry Needed)&#x20;

**Step 1: Install the Hoisting Ring and Perform Initial Hoisting&#x20;**

* Install the hoisting ring on the back of the robot and ensure it is securely attached.&#x20;

* Use the electric gantry hoist to lift the robot to an initial hoisting position, preparing for the subsequent mode switching operation.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-40.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step1：Install the lifting rings </span>
&#x20;

**Step 2: Switch to Standing Preparation Mode (Position-Controlled Standing)&#x20;**

Safety Reminder: Before switching modes, do not lift both feet of the robot completely off the ground to prevent potential equipment damage or personal injury.&#x20;

Operating Steps:&#x20;

1. Keep the robot in the hoisted position and slightly raise the lifting rope to prevent sudden forward tilting.&#x20;

2. Use the remote controller and press \[L2 + X] simultaneously to switch to Standing Preparation Mode (Position-Controlled Standing).&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-41.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step2：Use the remote controller to switch the robot to the standing preparation mode </span>
&#x20;

**Step 3: Enter Zero-Torque Mode&#x20;**

Recommended Safe Procedure:&#x20;

* First switch to Damping Mode: short press \[L2 + R2 + Create].&#x20;

* Then switch to Zero-Torque Mode: short press \[L1 + R1 + Create].&#x20;

Emergency Stop:&#x20;

If an immediate stop is required, you can directly enter Zero-Torque Mode via the remote controller.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-42.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step3：Use the remote controller to switch the robot to the zero-torque mode </span>
&#x20;

**Step 4: Hoist the Robot&#x20;**

After confirming that the robot has entered Zero-Torque Mode, use the electric gantry hoist to slowly lift the robot until both feet are completely off the ground.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-43.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step4：Robot fully hoisted, both feet off the ground </span>
&#x20;

**Step 5: Power Off&#x20;**

* Short press the power button on the back of the battery to wake the device, then long press for about 5 seconds to power off.&#x20;

* During shutdown, LEDs 1–4 on the battery will turn off sequentially, indicating successful power-off.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-44.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step5：Press the power button to turn off the robot </span>
&#x20;

#### 3.3.2 Assisted Lying-Down Shutdown (No Gantry Required)&#x20;

**Step 6: Repack the Robot&#x20;**

* Open the side door of the packaging box and ensure enough space for placement.&#x20;

* Following the illustration, first place the legs into the bottom positioning slots, then fold the upper body into the box.&#x20;

* Confirm the robot is securely positioned before closing and locking the packaging box.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-45.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step6-1: Place the legs into the positioning slots as shown. </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-46.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step6-2: Fold the upper body into the box to complete packing. </span>



**Step 1: Enter Preparation (Position-Controlled Standing) Mode&#x20;**

* Use the remote controller and short press \[L2 + X] simultaneously to switch the robot to standing-preparation (position-controlled standing) mode.&#x20;

* During operation, manually support the robot from behind using the back handle to prevent tipping caused by imbalance.&#x20;

**Step 2: Lay the Robot Down&#x20;**

* Gently lower the robot from the standing-preparation posture to a Prone Position on the ground, ensuring smooth and controlled movement.&#x20;

* It is recommended that one or two operators assist to prevent tipping or abnormal postures during placement.&#x20;

**Step 3: Enter Zero-Torque Mode&#x20;**

* After confirming that the robot is fully lying flat and in contact with the ground, use the remote controller to change modes.&#x20;

* Avoid operating the controller before the robot is stable to prevent accidental falls.&#x20;

Recommended Safe Procedure:&#x20;

* First switch to Damping Mode: short press \[L2 + R2 + Create].&#x20;

* Then switch to Zero-Torque Mode: short press \[L1 + R1 + Create].&#x20;

Emergency Stop:&#x20;

If an immediate stop is required, you can directly enter Zero-Torque Mode via the remote controller.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-47.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step1: Switch to Standing-Preparation Mode (Position-Controlled Standing)  </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-48.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step2：Gently Lay the Robot Flat </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-49.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step3：Switch to Zero-Torque Mode After the Robot is Fully Flat </span>



**Step 4: Power Off&#x20;**

* Short press the power button on the back of the battery to wake the device, then long press for about 5 seconds to power off.&#x20;

* During shutdown, LEDs 1–4 on the battery will turn off sequentially, indicating successful power-off.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-50.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step4：Press the power button to turn off the robot </span>
&#x20;

**Step 5: Repack the Robot&#x20;**

* Open the side door of the packaging box and ensure enough space for placement.&#x20;

* Following the illustration, first place the legs into the bottom positioning slots, then fold the upper body into the box.&#x20;

* Confirm the robot is securely positioned before closing and locking the packaging box.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-51.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step5-1：Place the legs into the positioning slots as shown. </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-52.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step5-2: Fold the upper body into the box to complete packing.</span>



#### 3.3.3 Sitting-Position Shutdown (No Gantry Required)&#x20;

**Step 1: Command the Robot to Sit Down&#x20;**

* Use the remote controller and short press \[L2 + ←] simultaneously to make the robot perform the sitting motion.&#x20;

* Place the robot on a stable platform or bench approximately 35–40 cm high, ensuring firm support.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-53.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Step 1: Use the remote controller to make the robot perform the sitting motion. </span>&#x20;

&#x20;

**Step 2: Enter Zero-Torque Mode&#x20;**

* Once the robot is in a stable sitting posture facing forward, use the remote controller to switch to zero-torque mode to ensure safe shutdown.&#x20;

* During the transition, manually support the robot from behind using the back handle or ensure its back rests firmly against the chair to maintain balance and prevent falling.&#x20;

Recommended Safe Procedure:&#x20;

* First switch to Damping Mode: short press \[L2 + R2 + Create].&#x20;

* Then switch to Zero-Torque Mode: short press \[L1 + R1 + Create].&#x20;

Emergency Stop:&#x20;

If an immediate stop is required, directly enter zero-torque mode using the remote controller.&#x20;

**Step 3: Power Off&#x20;**

* Short press the power button on the back of the battery to wake the device, then long press for about 5 seconds to power off.&#x20;

* During shutdown, LEDs 1–4 on the battery will turn off sequentially, indicating successful power-off.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-54.png>)

&#x20;

<span style="color: rgb(143,149,158); background-color: inherit">Step 3：Press the power button to turn off the robot </span>
&#x20;

**Step 4: Repack the Robot&#x20;**

* Open the side door of the packaging box and ensure enough space for placement.&#x20;

* Following the illustration, first place the legs into the bottom positioning slots, then fold the upper body into the box.&#x20;

* Confirm the robot is securely positioned before closing and locking the packaging box.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-55.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step4-1：Place the legs into the positioning slots as shown. </span>

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-56.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Step4-2: Fold the upper body into the box to complete packing. </span>

&#x20;

Sitting-Position Shutdown Notes:&#x20;

* During the sitting motion, ensure the robot is placed stably on a 35–40 cm high bench or platform with a backrest for support.&#x20;

* When switching from sitting posture to zero-torque mode, manually support the back handle or keep the robot leaning against the backrest to maintain balance and prevent tipping.&#x20;

### 3.4 Charging Procedure&#x20;

#### 3.4.1 Charging&#x20;

1. Charging Method Selection&#x20;

* Method 1: After powering off the robot, directly connect the charger plug to the device’s charging port to charge.&#x20;

* Method 2: After powering off the robot, remove the battery first, then insert the charger plug into the battery’s charging port to charge.&#x20;

2. Magnetic Charging Port Operation Notes&#x20;

* The charging port adopts a magnetic design. Simply bring the charger plug close to the charging port, and it will automatically align and start charging.&#x20;

* During charging, make sure the magnetic charging port is fully aligned to avoid poor contact that could affect charging efficiency or damage the port.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-57.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">Magnetic Charging Port Location </span>
&#x20;

Note：&#x20;

Do not charge the robot while it is powered on. During charging, do not use the remote controller or operate the robot by any other means.&#x20;

#### 3.4.2 Battery Replacement&#x20;

* Power Off: Refer to the shutdown procedure described earlier.&#x20;

* Remove the Battery: Use two fingers to pull out the battery handle fixed on the front of the battery pack. Then insert your fingers into the handle loop and pull the handle strap outward to easily remove the battery.&#x20;

* Install the Battery: Follow the installation procedure described in the startup section.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-58.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Pull the battery handle and extract the battery backward. </span>

### 3.5 Remote Control User Guide&#x20;

#### 3.5.1 Mode Description&#x20;

|   |   |
|---|---|
|Concept|Description|
|Zero-Torque Mode|The default state after the robot is powered on. All motors stop active motion, and there is no damping sensation when the body is swung. Note: In zero-torque mode the robot will fall over and there is a risk of tipping. Switch to this mode with caution.|
|Damping Mode|The robot is powered on, and the main controller is operating normally. All joints enter a damping state, with a clear damping feel when the body is swung. Changing joint positions is resisted; joints cannot actively change position or hold a position. Note: In damping mode, the robot will slowly collapse and there is a risk of falling. Switch with caution.|
|Standing Preparation (Position-Controlled Standing) Mode|The robot is powered on, and the main controller is operating normally. The robot stands in a position-controlled posture and maintains it; the joints are locked at their current positions. In this mode, body motion cannot be commanded. It is commonly used for hoisting/lowering and is a safe posture. (The robot does not self-balance in this mode.)|
|Sitting Preparation (Position-Controlled Sitting) Mode|The robot is powered on, and the main controller is operating normally. The robot enters a sitting posture and maintains it; the joints are locked at their current positions. In this mode, the robot’s body motion cannot be commanded. It is typically used for starting up from a sitting or Supine Position and represents a safe posture. (The robot does not self-balance in this mode.)|
|Stable Standing (Force-Controlled Standing) Mode|The robot is powered on, and the main controller is operating normally. The robot stands and maintains posture. If joint positions are disturbed, there will be strong resistance, and the robot will actively recover to the standing posture. The robot has a certain balancing capability. In this mode, body motions can be commanded, while standing the robot can perform upper-limb actions such as waving or handshaking. It is recommended to perform stable standing on flat, hard surfaces. Avoid standing on soft or uneven surfaces such as carpets or grass.|
|Locomotion Mode|The robot is powered on, and the main controller is operating normally. The robot enters the walking mode and can move forward/backward/left/right and rotate clockwise or counterclockwise as commanded. At this time, the robot has stronger disturbance rejection and will actively maintain balance when subjected to moderate external forces. Speed and gait can be adjusted via the joystick; start with a slow gait and then gradually increase the speed. To maintain balance, preset upper-limb actions are not supported in Locomotion mode. It is recommended to perform road tests on flat, hard surfaces and to avoid stairs, rough/uneven ground, and high-curvature ramps.|
|Emergency-Stop Mode|In this mode, the robot stops safely and may fall softly to the ground. Please pay close attention to the robot’s safety during this state. It is recommended to use a protective frame to safeguard the robot when operating in this mode.|
|Off-Road Mode (Beta)|In this mode, the robot enters a fast-running control state with enhanced adaptability to rough terrain. To maintain balance, the robot’s upper-limb preset motions are temporarily disabled during Off-Road Mode.|

Remote Control Mode Precautions：&#x20;

1. It is recommended to operate the robot on flat, hard surfaces. Avoid stairs, steep or uneven roads, and large-curvature slopes to prevent the robot from tipping or falling.&#x20;

2. Off-Road Mode (Beta):&#x20;

   * Operation Limitation: When pushing the remote-control joysticks, avoid pushing them to the maximum extent. It is recommended to gradually adjust the joystick amplitude in sequence.&#x20;

   * Environmental Requirement: Operate only in open and unobstructed environments. Avoid stairs higher than 5 cm, slopes steeper than 10°, or rough terrain with elevation changes greater than ±5 cm.&#x20;

   * Safety Reminder: During operation, continuously monitor the robot’s balance status and adjust control actions in real time.&#x20;

3) Mode Trigger Limitation: Unless necessary, do not trigger Emergency-Stop Mode (Zero-Torque Mode) or Damping Mode, as these modes may cause joint unloading and could result in the robot falling.&#x20;

4) Control Priority: The control source priority order is: Remote Controller > App (Under development, will release soon) > Voice Interaction. When operating, pay attention to priority differences to avoid command conflicts.&#x20;

#### 3.5.2 Remote Control Instructions&#x20;

##### 3.5.2.1 Remote Control Button Positions&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-59.png>)

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-60.png>)

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-61.png>)

&#x20;
|   |   |
|---|---|
|Button position|FF MASTER remote control button names and meanings|
|B: Left Button/Trigger|L1, L2 Buttons (PS5 side view)|
|A: Right Button/Trigger|R1, R2 buttons (PS5 side view)|
|A: Arrow Button|The left cross key, ↑, ↓, ←, → four direction button|
|B: Create Button|Create Button|
|C: Touchpad|Touchpad|
|D: Options Button|Options Button|
|E: Four Action Buttons|△、□、○ and × Four Action Buttons|
|I&F: Sticks|I: Left Stick (controls forward/backward and left/right). F: Right Stick (controls rotation).|
|“PS” Button|G|
##### 3.5.2.2 Remote Controller LED Indicator Guide&#x20;
|                                                 |                     |
| ----------------------------------------------- | ------------------- |
| Status Description                              | LED Color/Behaviour |
| Controller power-on / connected                 | Solid blue          |
| Controller waiting to pair                      | Fast-blinking blue  |
| Pairing successful                              | Solid white         |
| Normal startup                                  | Breathing white     |
| Battery level ≤10 %                             | Solid amber         |
| Charging: 0–20 %：Fast blink 20–100 %：Slow blink | Breathing amber     |
| Charging complete                               | Amber off           |
| Firmware update                                 | Fast-blinking white |
##### 3.5.2.3 Remote Controller Charging Instructions&#x20;

1. Charging Method: Use a 5V charger plug + Type-C cable for direct charging. Charging via a computer USB port is slower.&#x20;

2. Charging Time: Typical battery life is about 5 hours of continuous use, and it takes approximately 3–4 hours to fully charge. The actual duration for PS5 controllers may vary depending on usage conditions.&#x20;

3. Notes: Avoid using fast-charging cables or adapters. It is recommended to use a 5V 1A or 5V 2A charger. The controller may become slightly warm during charging—avoid overcharging to prevent overheating damage.&#x20;

Remote Controller Usage Precautions&#x20;

1. When using the remote controller to operate the robot, pay attention to the controller’s battery level. Insufficient power may prevent mode switching, which could cause the robot to lose balance or fall unexpectedly.&#x20;

2. Always use certified safe chargers when charging the remote controller. Using third-party fast chargers that only support 9V/12V (no 5V mode) may result in damage to the controller.&#x20;

#### 3.5.3 Mode Switching and Remote Control&#x20;

##### 3.5.3.1 Description of Mode Switching Logic&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-62.png>)

&#x20;

Notes on Controller Mode Switching：&#x20;

1. The robot includes multiple operation modes. Different modes support different state transitions, and switching must follow the logic described above.&#x20;

2. Upper-limb motion control is only available in Stable Standing (Force-Controlled Standing) Mode and can be triggered by sending upper-limb commands via the controller or app (under development, will release soon).&#x20;

##### 3.5.3.2 Emergency-Stop Mode Switching Instructions&#x20;

1. When the robot is walking, press 【L1 + R1 + Create】 simultaneously (short press) to trigger an emergency stop. After activation, all robot joints will release torque, and the robot will slowly collapse. Use the protective frame throughout the process to ensure safety.&#x20;

2. To cancel the emergency stop, press 【L2 + X】 simultaneously to switch the robot back to Sitting Preparation (Position-Controlled Sitting) Mode.&#x20;

3. Avoid triggering the Emergency-Stop Mode (Zero-Torque Mode) unless necessary.&#x20;

##### 3.5.3.3 Full-Body Mode Switching Button Description&#x20;
|                                                          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Name                                                     | Details                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Hoisted Start-Up                                         | Process Description: Power on (hoisted position) → Position-Controlled Standing → Force-Controlled Standing → Remove hoisting ring → Enter Locomotion Mode → Demonstration process. Standing Preparation (Position-Controlled Standing) Mode: L2 + X, short press simultaneously.  <br>Stable Standing (Force-Controlled Standing) Mode: R2 + X, short press simultaneously.  <br>“Stick-to-Move”: The robot automatically enters Locomotion Mode when the joystick is pushed forward.                                                                                                                                                                                                                                                                                                  |
| Start-Up from Supine Position                            | Process Description: Power on (ensure the robot’s hips are level with the ground and the torso is facing upward) → Start-up from supine position → Enter Locomotion Mode → Demonstration process.  <br>Supine Start-Up: Press ↑ + △ simultaneously (short press).  <br>“Stick-to-Move”: The robot automatically enters Locomotion Mode when the joystick is pushed forward.                                                                                                                                                                                                                                                                                                                                                                                                             |
| Start-up from Prone Position                             | Process Description: Power on (ensure the robot’s hips are level with the ground and the torso is facing downward) → Start-up from prone position → Enter Locomotion Mode → Demonstration process.  <br>Prone Start-Up: Press ↑ + △ simultaneously (short press).  <br>“Stick-to-Move”: The robot automatically enters Locomotion Mode when the joystick is pushed forward.                                                                                                                                                                                                                                                                                                                                                                                                             |
| Start-up from Sitting Position                           | Process Description: Power on (sitting standby) → Enter sitting posture → Sit-to-stand → Enter Locomotion Mode → Demonstration process.  <br>Before starting, ensure that the robot’s limbs are placed in the standard sitting posture. Sitting Preparation (Position-Controlled Sitting) Mode: Press ↑ + X simultaneously (short press). The robot’s back must be supported by a stable chair or assisted by personnel.  <br>Siting Start-Up: Press ↑ + □ simultaneously (short press).  <br>“Stick-to-Move”: The robot automatically enters Locomotion Mode when the joystick is pushed forward.                                                                                                                                                                                      |
| Standing Preparation (Position-Controlled Standing) Mode | Press L2 + X simultaneously (short press) to switch to Standing Preparation (Position-Controlled Standing) Mode.  <br>This mode can also be switched from Zero-Torque Mode.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Sitting Preparation (Position-Controlled Sitting) Mode.  | Press ↑ + X simultaneously (short press) to switch to Position-Controlled Sitting Mode.  <br>This mode can also be switched from Zero-Torque Mode.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Stable Standing (Force-Controlled Standing) Mode         | Press R2 + X simultaneously (short press) to switch to Stable Standing (Force-Controlled Standing) Mode.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Zero-Torque Mode                                         | Press L1 + R1 + Create simultaneously (short press) to switch to Zero-Torque Mode.  <br>The robot can enter this mode from any other mode using the same button combination.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Damping Mode                                             | Press L2 + R2 + Create simultaneously (short press) to switch to Damping Mode.  <br>The robot can enter this mode from any other mode using the same button combination.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Locomotion Mode                                          | In Stable Standing (Force-Controlled Standing) Mode, the robot moves when the joystick is pushed. Forward: Push the left joystick upward. Backward: Push the left joystick downward. Turn Left: Push the right joystick to the left. Turn Right: Push the right joystick to the right. Strafe Left: Push the left joystick to the left. Strafe Right: Push the left joystick to the right.                                                                                                                                                                                                                                                                                                                                                                                              |
| Off-Road Mode (Beta)                                     | When in Locomotion Mode, the robot can switch to Off-Road Mode.  <br>Press R2 + ↑ simultaneously (short press) to switch to Off-Road Mode.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Sit Down / Stand Up from Sitting                         | When in Stable Standing (Force-Controlled Standing) Mode, the robot can switch to Sitting Motion. Sit Down: Press L2 + ← simultaneously (short press). Stand Up from Sitting: Press ↑ + □ simultaneously (short press).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Crouch Down / Stand Up from Crouching                    | When the robot is in Stable Standing (Force-Controlled Standing) Mode, it can enter the Crouch/Stand Transition Motion. Press ▲ + Left Joystick simultaneously to control the robot’s crouching depth and standing height via the joystick. Push the left joystick upward to stand up from crouching. Push the left joystick downward to crouch down from standing. During the crouching process, please monitor the robot’s balance closely. Assistance may be required to help maintain stability.                                                                                                                                                                                                                                                                                    |
| Emergency-Stop Mode                                      | Emergency-Stop Mode is equivalent to the Zero-Torque Mode, and the key combinations are the same. Press L1 + R1 + Create simultaneously (short press) to switch to Emergency-Stop Mode. At this time, the robot will slowly collapse and fall to the ground. Please ensure the surrounding area is safe during this process. To exit Emergency-Stop Mode, press L2 + X simultaneously to switch the robot to the Standing Preparation (Position-Controlled Standing) Mode.                                                                                                                                                                                                                                                                                                              |
| Hoisted Shutdown                                         | Process Description: Demonstration Mode → Complete demonstration → Switch to Standing Preparation (Position-Controlled Standing) Mode → Switch to Damping Mode → Switch to Zero-Torque Mode → The robot’s legs gradually lift off the ground → Power off. Standing Preparation (Position-Controlled Standing) Mode: Press L2 + X simultaneously to switch to this mode. Damping Mode: Press L2 + R2 + Create simultaneously (short press) to switch to Damping Mode. The robot will soften its joints and collapse slowly. Please ensure safety during this process. Zero-Torque Mode: Press L1 + R1 + Create simultaneously (short press) to switch to Zero-Torque Mode. When the robot is fully suspended with both feet off the ground, turn off the power to complete the shutdown. |
| Assisted Lying-Down Shutdown                             | Process Description: Demonstration Mode → Standing Preparation (Position-Controlled Standing) Mode → Manually assist the robot to lie down → Robot lies flat → Damping Mode → Zero-Torque Mode → Power off. During the transition from Standing Preparation (Position-Controlled Standing) Mode to the robot lying flat, an operator must assist in supporting the robot. Standing Preparation (Position-Controlled Standing) Mode: Press L2 + X simultaneously (short press). Damping Mode: Press L2 + R2 + Create simultaneously (short press) to switch to Damping Mode.  <br>At this time, the robot will switch to the Damping Mode and slowly collapse. Please ensure safety during this process. Zero-Torque Mode: Press L1 + R1 + Create simultaneously (short press).          |
| Sitting-Position Shutdown                                | Process Description: Demonstration Mode → Sit-Down Action → Damping Mode → Zero-Torque Mode → Power off. Sit-Down Action: Press L2 + ← simultaneously (short press). Damping Mode: Press L2 + R2 + Create simultaneously (short press) to switch to Damping Mode.  <br>At this time, the robot will switch to Damping Mode and slowly collapse. Please ensure safety during this process. Zero-Torque Mode: Press L1 + R1 + Create simultaneously (short press) to switch to Zero-Torque Mode from sitting position.  <br>The robot’s back should be supported by a chair or assisted manually for balance.                                                                                                                                                                             |
#### 3.5.4 Interaction Action Library Control&#x20;

The following robot actions can be performed through the controller, including certain head, upper-limb, and waist movements.&#x20;
|   |   |   |
|---|---|---|
|Action Type|Action Name|Button Instruction|
|Head Movements|Clockwise Rotation|L1 + push the left joystick to the right: The head rotates clockwise. When the joystick is released, the head will automatically return to its neutral position. To fix the head at a specific angle, hold the joystick; to unlock, press the joystick again.|
||Counterclockwise Rotation|L1 + push the left joystick to the left: The head rotates counterclockwise. When the joystick is released, the head will return to neutral. Hold to fix at a specific angle; press again to unlock.|
||Downward Tilt|L1 + push the left joystick downward: The head tilts downward. When the joystick is released, the head automatically returns to neutral. Hold to fix; press again to unlock.|
||Upward Tilt|L1 + push the left joystick upward: The head tilts upward. When the joystick is released, the head automatically returns to neutral. Hold to fix; press again to unlock.|
|Upper-Limb Movements|Wave|Wave (Left Arm): Simultaneously press PS5 Create (Left) + L1 + tap △ Wave (Right Arm): Simultaneously press PS5 Create (Left) + R1 + tap △|
||Handshake|Handshake (Left Hand): Simultaneously press PS5 Create (Left) + L1 + tap ✕ Handshake (Right Hand): Simultaneously press PS5 Create (Left) + R1 + tap ✕|
||Flying Kiss|Flying Kiss (Left Hand): Simultaneously press PS5 Create (Left) + L1 + tap ○ Flying Kiss (Right Hand): Simultaneously press PS5 Create (Left) + R1 + tap ○|
||Salute|Salute (Left Arm): Simultaneously press PS5 Create (Left) + L1 + tap ☐ Salute (Right Arm): Simultaneously press PS5 Create (Left) + R1 + tap ☐|
||Fist Strike|Fist Strike (Left Arm): Simultaneously press PS5 Options (Right) + L1 + tap↓ Fist Strike (Right Arm): Simultaneously press PS5 Options (Right) + R1 + tap↓|
||Palm Strike|Palm Strike (Left Arm): Simultaneously press PS5 Options (Right) + L1 + tap → Palm Strike (Right Arm): Simultaneously press PS5 Options (Right) + R1 + tap →|
||Raise Hand|Raise Hand (Left Arm): Simultaneously press PS5 Options (Right) + L1 + tap ↑ Raise Hand (Right Arm): Simultaneously press PS5 Options (Right) + R1 + tap ↑|
|Waist Movements|Clockwise Rotation|L1 + push the right joystick to the right: The waist rotates clockwise. When the joystick is released, the waist will automatically return to its neutral position. To fix the waist at a specific angle, hold the joystick; press again to unlock.|
||Counterclockwise Rotation|L1 + push the right joystick to the left: The waist rotates counterclockwise. When the joystick is released, the waist will automatically return to its neutral position. To fix the waist at a specific angle, hold the joystick; press again to unlock.|
||Bend Forward|L1 + push the right joystick downward: The waist bends forward. When the joystick is released, the waist will automatically return to its neutral position. To fix the waist at a specific angle, hold the joystick; press again to unlock.|
||Straighten Waist|L1 + push the right joystick upward: The waist straightens up. When the joystick is released, the waist will automatically return to its neutral position. To fix the waist at a specific angle, hold the joystick; press again to unlock.|
### 3.6 Robot Interaction Procedures Guide&#x20;

#### 3.6.1 Robot Interaction Precautions&#x20;

1. During voice-controlled walking or upper-limb motion commands, it is recommended to maintain a clear space with at least a 1-meter radius around the robot. This ensures a safe operating area and allows the robot to move freely within its active range.&#x20;

2. During voice-controlled walking or motion execution, please pay close attention to the robot’s safety to avoid any risk of falling.&#x20;

3. It is recommended to perform motion commands on hard flooring. Avoid using voice control on soft surfaces such as grass or carpets, as this may affect stability.&#x20;

4. For customized speech corpus configuration, please contact FF EAI Robotic technical support. In later versions, this feature will be available for self-configuration via the Intellectual & Interactive Platform (Under development, will release soon).&#x20;

&#x20;

#### 3.6.2 Current Version (External Microphone)&#x20;

* Interaction Support: Only external microphone interaction is supported. You must use the external microphone provided in the package for connection.&#x20;

* Operation Steps: Connect and pair the microphone properly. After ensuring that the robot is connected to the network, turn on the microphone to activate the voice interaction function.&#x20;

* Interaction Method: No wake-up word is required — you can communicate with the robot directly through the external microphone.&#x20;

#### 3.6.3 Upcoming Version (Built-in Microphone, OTA Update)&#x20;

* The built-in microphone interaction feature will be introduced through a future OTA update. Please pay attention to version upgrade notifications in the FF Robotic app (Under development, will release soon) for detailed update instructions.&#x20;

* Function Switching: After the update, users can manually switch between the built-in and external microphones within the app (Under development, will release soon).&#x20;

* Built-in Microphone Interaction: When using the built-in microphone, the robot must be activated with a wake word before interaction.&#x20;

* English wake word: “Hey, Master”&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-63.png>)

&#x20;

##### 3.6.3.1 Voice Chat&#x20;

1. Chat Content Scope&#x20;

* Everyday Topics: Users can engage in casual voice conversations with the robot on general subjects such as current news, weather conditions, or information about the surrounding environment.&#x20;

* FF Master Topics: Users can ask questions related to FF Master, including its personality, preferences, or its details.&#x20;

* Knowledge Base Topics: Users can inquire about content related to the custom knowledge base, depending on the system configuration.&#x20;

2. Language Interaction Support&#x20;

* The system currently supports interaction in multi-languages including English, Chinese, Spanish, French, Italian, etc. Users can speak directly to the robot in any language, and the robot will automatically detect the language and respond accordingly in the language used.&#x20;

* In future updates, additional languages can be customized and switched via the Intellectual & Interactive Platform (Under development, will release soon), enabling flexible adaptation to various use scenarios.&#x20;

3. Voice Skill Commands&#x20;

* Singing Skill：&#x20;

1. Supported songs include *Bingo*, *Happy Birthday*, *Little Star*, *London Bridge*, *Row Row Row Your Boat*, *The Wheels on the Bus*, *Jingle Bells, etc*.&#x20;

2. Example commands: “Sing me a song.” / “Can you sing?”&#x20;

* Rap Singing Skill：&#x20;

1. Example commands: “Sing me a rap.” / “Can you do a rap?”&#x20;

##### 3.6.3.2 Multimodal Interaction&#x20;

1. Environment and Object Q\&A&#x20;

* Users can initiate multimodal question–answering with the robot — for example, asking about the surrounding environment or inquiring about the number, Color, or type of objects on a table.&#x20;

2. Interactive Object Attribute Query&#x20;

* The robot can answer questions about specific targets in the scene, such as detecting the number of people, or recognizing their clothing, facial expressions, or gender.&#x20;

3. Customized Guest Greeting &#x20;

* Supports face enrolment via the Intellectual & Interactive platform (under development, will release soon). Once a face is registered, the robot can recognize the guest and greet them accordingly.&#x20;

* Both single-person and multi-person recognition scenarios are supported.&#x20;

* Future updates will allow self-service customization via the Intellectual & Interactive Platform (under development, will release soon), following platform update releases.&#x20;

* A new Face Recognition Switch has been added — users can enable or disable the feature directly in the FF Robotic app (under development, will release soon).&#x20;

##### 3.6.3.3 Voice Command Actions and Expressions&#x20;

You can converse with the robot using voice commands to trigger physical actions or facial expressions：&#x20;
|   |   |   |
|---|---|---|
|Category|Supported Range|Example Voice Command|
|Upper Limb + Prosthetic Hand Actions|Left/Right wave, Left/Right chest-front wave, Cross arms, Left/Right raise hand, Left/Right salute, Left/Right handshake, Double-hand heart, Left/Right single-hand heart, Dynamic energy beam, Hug, High five, Cheering, Double-hand lift, Left/Right single-hand lift, Left/Right fist bump, Left/Right thumbs up, Left/Right “V” gesture|“Perform an XXX action.”|
|Upper Limb + Dexterous Hand Actions|Left/Right dexterous hand thumbs up, Peace gesture, Fist bump, Cheering motion; also includes: Left/Right wave, Left/Right chest-front wave, Cross arms, Left/Right raise hand, Left/Right salute, Left/Right handshake, Double-hand heart, Left/Right single-hand heart, Dynamic energy beam, Hug, High five, Double/Single-hand lift|“Perform an XXX action.”|
|Head Movements|Look left, look right, Nod, Shake head|“Look left / Look right / Nod / Shake head.”|
|Walking Actions|Move forward, backward, left, or right|“Walk two steps forward/backward/left/right.”|
|Waist Movements|Turn waist left and return, Turn waist right and return|“Turn your waist left/right.”|
|Expressive Actions|Head scratching, Butt scratching|“Do a head-scratch/butt-scratch action.”|
|Facial Screen Expressions|Blinking, Laughing, Sad/Crying, Bored, Thinking, Sleepy, Confused/Surprised, Angry, Adoring, Coquettish, Sympathetic expressions|“Show a XXX expression.”|
##### 3.6.3.4 Head Pat Interaction&#x20;

You can gently touch the head touch sensor of FF Master. The robot will respond by nodding pleasantly and saying: “Friendly touch signal detected — energy +100%!”&#x20;

##### 3.6.3.5 Robot Interaction Customization (under development, will release soon. Not available for Master edition)&#x20;

You may contact the sales representative to submit your knowledge base customization request and ask for your business solution.&#x20;

In future updates, you will be able to configure and customize your interactive knowledge base, character profile, wake words, and voice tone selection directly through the FF EAI Robotic Robotics Intellectual & Interactive Platform (under development, will release soon).&#x20;
|   |   |   |
|---|---|---|
|Type|Required Content|Description|
|Character Customization|- Character profile (optional), default: FF EAI Robotic humanoid robot — FF Master. - Desired company-related knowledge (optional). - Desired business-related knowledge (optional). - Limit: within 300 characters. - Currently supported via sales representative submission; future support through the Intellectual & Interactive Platform (under development, will release soon).|Customize a corporate-specific persona, enabling the robot to understand core company knowledge.|
|Q&A Customization|- Question: User utterances, up to 20 characters each, with 2–5 high-frequency variations (no special symbols).- Answer: Robot response, up to 50 characters (recommended 50).- Currently supported via sales representative submission; future support through the Intellectual & Interactive Platform (under development, will release soon).|Designed for high-frequency Q&A scenarios — allows the robot to accurately answer company-specific questions and provide effective responses to user inquiries.|
|Facial Registration|Supports facial data entry and customization of greeting dialogues for specific individuals. Future customization will be available on the Intellectual & Interactive Platform (under development, will release soon).|Enables personalized greetings and welcome messages for registered faces.|
|Voice Tone Selection|Future customization available through the Intellectual & Interactive Platform (under development, will release soon).|Allows customization or replication of the robot’s voice tone.|
|Wake Word Customization|Future customization available through the Intellectual & Interactive Platform (under development, will release soon).|Enables defining personalized wake words for robot activation.|
#### 3.6.4 External Microphone Pairing and Connection&#x20;

1. Press the power button on the microphone to turn it on and ensure the device is active.&#x20;

2. The external microphone receiver is integrated into the robot’s head, and the microphone will automatically pair with the robot. A solid green light indicates a successful connection.&#x20;

   1. If the green light is flashing, it means the microphone is still attempting to pair. In this case, restart the robot to automatically complete the pairing process.&#x20;

   2. If pairing still fails after restarting, insert a toothpick or thin tool into the round hole on the back of the robot’s head and press gently while holding the microphone’s pairing button to manually complete the pairing.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-64.png>)

&#x20;<span style="color: rgb(143,149,158); background-color: inherit">External Microphone Transmitter Indicator Light Meanings </span>
&#x20;

### 3.7 FF Robotic APP Manual (Under development, will release soon)&#x20;

FF Robotic APP is the official companion control application for the FF Master robot.&#x20;

Through FF Robotic APP, users can perform full lifecycle management of the robot, including but not limited to the following features:&#x20;

* Network configuration and connection&#x20;

* Motion control and posture management&#x20;

* OTA firmware updates and version upgrades&#x20;

* Exhibition and showroom navigation modes&#x20;

FF Robotic provides users with an all-in-one intelligent management and control experience, making robot operation more intuitive, efficient, and convenient.&#x20;

#### 3.7.1 APP Download (Under development, will release soon)&#x20;

The latest version of the APP corresponds to the latest firmware version of the robot. Please make sure to download and use the correct version.&#x20;

&#x20;

#### 3.7.2 Remote Controller operations&#x20;

1. Remote Controller operations: such as checking the controller status, re-pairing the controller, and deleting historical pairing records.&#x20;



**Re-pair the Controller *(Note: The remote controller is pre-configured and paired at the factory. No manual re-pairing is required — simply press the center button to activate the controller when needed.)*&#x20;**

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-65.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Default Pairing</span>

If you need to re-pair or connect another controller, follow these steps:&#x20;

**Enter pairing mode:&#x20;**

Press and hold both buttons inside the red box at the bottom of the controller until the blue indicator light starts flashing, indicating that the controller has entered pairing mode.&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-66.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Repairing</span>



**Delete Pairing History**

After the connection is disconnected, the controller will automatically power off.&#x20;

If the historical connection record has not been deleted, simply press the button shown in the red box the next time you power on to automatically reconnect.&#x20;

If the history has been deleted, you will need to go through the pairing process again.&#x20;

**&#x20;**

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-67.png>)

<span style="color: rgb(143,149,158); background-color: inherit">Automatic Pairing</span>



&#x20;

Controller Connection Notes:&#x20;

1. Basic Connection Operation&#x20;

   * The FF MASTER remote controller comes pre-configured and paired at the factory — no re-pairing is required.&#x20;

   * To use, simply press the center button on the controller to quickly establish a connection.&#x20;

2. How to Distinguish Multiple Controllers&#x20;

   * Each controller has a unique MAC address. If multiple controllers share the same name, follow these steps:&#x20;

     * Try connecting several times to identify and remember your controller’s MAC address.&#x20;

     * In the APP (under development, will release soon) Bluetooth scan interface, the MAC address is displayed beneath the device name — use it to select and connect to the correct controller. &#x20;

3) Troubleshooting Connection Issues&#x20;

   * If the historical connection record has not been deleted, but the controller fails to reconnect automatically after startup:&#x20;
     Wait a few moments. If the issue persists, enter pairing mode and reconnect.&#x20;

   * If the historical connection record has been deleted, you must manually enter pairing mode again to reconnect the controller to the device.&#x20;

#### 3.7.3 Action Control Commands&#x20;

##### 3.7.3.1 Safety Notes&#x20;

1. When the robot switches to full-body motion control mode, please pay close attention to its movements. It is strongly recommended to provide manual support or other protective measures in advance to prevent falls that may cause mechanical damage.&#x20;

2. Avoid triggering passive (zero-torque) mode, emergency stop mode, or damping mode unless necessary, as these modes may cause the robot to lose balance and fall, resulting in potential equipment damage.&#x20;

##### 3.7.3.2 App Action Command Operation (under development, will release soon)&#x20;

### 3.8 Others&#x20;

1. This manual is based on the FF MASTER Ultra version.&#x20;

2. For any other matters not mentioned in this user manual, please visit the FF EAI Robotic official website or contact FF EAI Robotic customer service for more information.&#x20;

# 4. Locomotion & Manipulation Platform Manual (under development, will release soon, not for Master edition)&#x20;

The FF Master supports the use of the Locomotion & Manipulation Platform (under development, will release soon), developed by FF EAI-Robotics. Locomotion & Manipulation (under development, will release soon) is a content creation and performance platform designed for general creators, enabling users to easily produce and publish robotic performances without requiring professional backgrounds in programming, control, or motion design. The platform aims to lower the barrier to robot content creation, empowering anyone to bring creative ideas to life through intuitive tools and interfaces.&#x20;

# 5. Contact Information&#x20;

1. Official Website: [<u>https://robotics.ff.com/us/</u>](https://robotics.ff.com/us/)&#x20;

2. Hotline: &#x20;

3. Email: ServiceSupport@ff.com&#x20;

![](<images/FF Master!Master EDU!Master Ultra Edition Instruction Manual v1.0 -filename-68.png>)

&#x20;
