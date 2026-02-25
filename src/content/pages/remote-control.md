# Remote Control User Guide

## Mode Description

| Concept | Description |
| --- | --- |
| Zero-Torque Mode | The default state after the robot is powered on. All motors stop active motion, and there is no damping sensation when the body is swung. Note: In zero-torque mode the robot will fall over and there is a risk of tipping. Switch to this mode with caution. |
| Damping Mode | The robot is powered on, and the main controller is operating normally. All joints enter a damping state, with a clear damping feel when the body is swung. Changing joint positions is resisted; joints cannot actively change position or hold a position. Note: In damping mode, the robot will slowly collapse and there is a risk of falling. Switch with caution. |
| Standing Preparation (Position-Controlled Standing) Mode | The robot is powered on, and the main controller is operating normally. The robot stands in a position-controlled posture and maintains it; the joints are locked at their current positions. In this mode, body motion cannot be commanded. It is commonly used for hoisting/lowering and is a safe posture. (The robot does not self-balance in this mode.) |
| Sitting Preparation (Position-Controlled Sitting) Mode | The robot is powered on, and the main controller is operating normally. The robot enters a sitting posture and maintains it; the joints are locked at their current positions. In this mode, the robot's body motion cannot be commanded. It is typically used for starting up from a sitting or Supine Position and represents a safe posture. (The robot does not self-balance in this mode.) |
| Stable Standing (Force-Controlled Standing) Mode | The robot is powered on, and the main controller is operating normally. The robot stands and maintains posture. If joint positions are disturbed, there will be strong resistance, and the robot will actively recover to the standing posture. The robot has a certain balancing capability. In this mode, body motions can be commanded; while standing the robot can perform upper-limb actions such as waving or handshaking. It is recommended to perform stable standing on flat, hard surfaces. Avoid standing on soft or uneven surfaces such as carpets or grass. |
| Locomotion Mode | The robot is powered on, and the main controller is operating normally. The robot enters the walking mode and can move forward/backward/left/right and rotate clockwise or counterclockwise as commanded. Speed and gait can be adjusted via the joystick; start with a slow gait and then gradually increase the speed. To maintain balance, preset upper-limb actions are not supported in Locomotion mode. It is recommended to perform road tests on flat, hard surfaces and to avoid stairs, rough/uneven ground, and high-curvature ramps. |
| Emergency-Stop Mode | In this mode, the robot stops safely and may fall softly to the ground. Please pay close attention to the robot's safety during this state. It is recommended to use a protective frame to safeguard the robot when operating in this mode. |
| Off-Road Mode (Beta) | In this mode, the robot enters a fast-running control state with enhanced adaptability to rough terrain. To maintain balance, the robot's upper-limb preset motions are temporarily disabled during Off-Road Mode. |

Remote Control Mode Precautions：
1. It is recommended to operate the robot on flat, hard surfaces. Avoid stairs, steep or uneven roads, and large-curvature slopes to prevent the robot from tipping or falling.
2. Off-Road Mode (Beta):
￮ Operation Limitation: When pushing the remote-control joysticks, avoid pushing them to the maximum extent. It is recommended to gradually adjust the joystick amplitude in sequence.
￮ Environmental Requirement: Operate only in open and unobstructed environments. Avoid stairs higher than 5 cm, slopes steeper than 10°, or rough terrain with elevation changes greater than ±5 cm.
￮ Safety Reminder: During operation, continuously monitor the robot's balance status and adjust control actions in real time.
3. Mode Trigger Limitation: Unless necessary, do not trigger Emergency-Stop Mode (Zero-Torque Mode) or Damping Mode, as these modes may cause joint unloading and could result in the robot falling.
4. Control Priority: The control source priority order is: Remote Controller > App (Under development, will release soon) > Voice Interaction. When operating, pay attention to priority differences to avoid command conflicts.

## Remote Control Instructions

### Remote Control Button Positions

![Remote Control Button Positions](/images/docx/remote-buttons-1.png)

![Remote Control Side View — L1, L2, R1, R2 Buttons](/images/docx/remote-buttons-2.png)

![Remote Control Sticks and Additional Buttons](/images/docx/remote-buttons-3.png)

| Button Position | Name and Meaning |
| --- | --- |
| B: Left Button/Trigger | L1, L2 Buttons (PS5 side view) |
| A: Right Button/Trigger | R1, R2 Buttons (PS5 side view) |
| A: Arrow Button | The left cross key, ↑, ↓, ←, → four direction buttons |
| B: Create Button | Create Button |
| C: Touchpad | Touchpad |
| D: Options Button | Options Button |
| E: Four Action Buttons | △, □, ○ and × Four Action Buttons |
| I & F: Sticks | I: Left Stick (controls forward/backward and left/right). F: Right Stick (controls rotation). |
| "PS" Button | G |

### Remote Controller LED Indicator Guide

| Status Description | LED Color/Behaviour |
| --- | --- |
| Controller power-on / connected | Solid blue |
| Controller waiting to pair | Fast-blinking blue |
| Pairing successful | Solid white |
| Normal startup | Breathing white |
| Battery level ≤10% | Solid amber |
| Charging (0–20%) | Fast blink amber |
| Charging (20–100%) | Slow blink amber |
| Charging complete | Amber off |
| Firmware update | Fast-blinking white |

### Remote Controller Charging Instructions

1. Charging Method: Use a 5V charger plug + Type-C cable for direct charging. Charging via a computer USB port is slower.
2. Charging Time: Typical battery life is about 5 hours of continuous use, and it takes approximately 3–4 hours to fully charge. The actual duration for PS5 controllers may vary depending on usage conditions.
3. Notes: Avoid using fast-charging cables or adapters. It is recommended to use a 5V 1A or 5V 2A charger. The controller may become slightly warm during charging—avoid overcharging to prevent overheating damage.
Remote Controller Usage Precautions
1. When using the remote controller to operate the robot, pay attention to the controller's battery level. Insufficient power may prevent mode switching, which could cause the robot to lose balance or fall unexpectedly.
2. Always use certified safe chargers when charging the remote controller. Using third-party fast chargers that only support 9V/12V (no 5V mode) may result in damage to the controller.

## Mode Switching and Remote Control

### Description of Mode Switching Logic

![Mode Switching Logic](/images/docx/mode-switching-logic-1.jpeg)

Notes on Controller Mode Switching：
1. The robot includes multiple operation modes. Different modes support different state transitions, and switching must follow the logic described above.
2. Upper-limb motion control is only available in Stable Standing (Force- Controlled Standing) Mode and can be triggered by sending upper-limb commands via the controller or app (under development, will release soon).

### Emergency-Stop Mode Switching Instructions

1. When the robot is walking, press 【L1 + R1 + Create】 simultaneously (short press) to trigger an emergency stop. After activation, all robot joints will release torque, and the robot will slowly collapse. Use the protective frame throughout the process to ensure safety.
2. To cancel the emergency stop, press 【L2 + X】 simultaneously to switch the robot back to Sitting Preparation (Position-Controlled Sitting) Mode.
3. Avoid triggering the Emergency-Stop Mode (Zero-Torque Mode) unless necessary.

### Full-Body Mode Switching Button Description

| Name | Details |
| --- | --- |
| Hoisted Start-Up | Process: Power on (hoisted position) → Position-Controlled Standing → Force-Controlled Standing → Remove hoisting ring → Enter Locomotion Mode. Standing Preparation Mode: L2 + X (short press). Stable Standing Mode: R2 + X (short press). "Stick-to-Move": The robot automatically enters Locomotion Mode when the joystick is pushed forward. |
| Start-Up from Supine Position | Process: Power on (ensure the robot's hips are level with the ground and the torso is facing upward) → Supine start-up → Locomotion Mode. Supine Start-Up: Press ↑ + △ simultaneously (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |
| Start-up from Prone Position | Process: Power on (ensure the robot's hips are level with the ground and the torso is facing downward) → Prone start-up → Locomotion Mode. Prone Start-Up: Press ↑ + △ simultaneously (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |
| Start-up from Sitting Position | Process: Power on (sitting standby) → Enter sitting posture → Sit-to-stand → Locomotion Mode. Sitting Preparation Mode: Press ↑ + X (short press). Sitting Start-Up: Press ↑ + □ (short press). "Stick-to-Move": joystick forward to enter Locomotion Mode. |
| Standing Preparation (Position-Controlled Standing) Mode | Press L2 + X simultaneously (short press). This mode can also be switched from Zero-Torque Mode. |
| Sitting Preparation (Position-Controlled Sitting) Mode | Press ↑ + X simultaneously (short press). This mode can also be switched from Zero-Torque Mode. |
| Stable Standing (Force-Controlled Standing) Mode | Press R2 + X simultaneously (short press). |
| Zero-Torque Mode | Press L1 + R1 + Create simultaneously (short press). The robot can enter this mode from any other mode. |
| Damping Mode | Press L2 + R2 + Create simultaneously (short press). The robot can enter this mode from any other mode. |
| Locomotion Mode | In Stable Standing Mode, push joystick to move. Forward/Backward: left joystick up/down. Turn Left/Right: right joystick left/right. Strafe Left/Right: left joystick left/right. |
| Off-Road Mode (Beta) | When in Locomotion Mode, press R2 + ↑ simultaneously (short press) to switch to Off-Road Mode. |
| Sit Down / Stand Up from Sitting | In Stable Standing Mode: Sit Down: Press L2 + ← (short press). Stand Up: Press ↑ + □ (short press). |
| Crouch Down / Stand Up from Crouching | In Stable Standing Mode, press △ + Left Joystick to control crouching depth. Push joystick up to stand, down to crouch. |
| Emergency-Stop Mode | Press L1 + R1 + Create simultaneously (short press). The robot will slowly collapse. To exit, press L2 + X to switch to Standing Preparation Mode. |
| Hoisted Shutdown | Standing Preparation Mode: L2 + X → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Hoist feet off ground → Power off. |
| Assisted Lying-Down Shutdown | Standing Preparation Mode: L2 + X → Manually assist robot to lie down → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Power off. |
| Sitting-Position Shutdown | Sit Down: L2 + ← → Damping Mode: L2 + R2 + Create → Zero-Torque Mode: L1 + R1 + Create → Power off. |

## Interaction Action Library Control

The following robot actions can be performed through the controller, including certain head, upper-limb, and waist movements.
| Action Type | Action Name | Button Instruction |
| --- | --- | --- |
| Head Movements | Clockwise Rotation | L1 + push left joystick right. Release to return to neutral. Hold to fix angle; press again to unlock. |
| | Counterclockwise Rotation | L1 + push left joystick left. Release to return to neutral. Hold to fix; press again to unlock. |
| | Downward Tilt | L1 + push left joystick down. Release to return to neutral. Hold to fix; press again to unlock. |
| | Upward Tilt | L1 + push left joystick up. Release to return to neutral. Hold to fix; press again to unlock. |
| Upper-Limb Movements | Wave (Left) | Create + L1 + tap △ |
| | Wave (Right) | Create + R1 + tap △ |
| | Handshake (Left) | Create + L1 + tap ✕ |
| | Handshake (Right) | Create + R1 + tap ✕ |
| | Flying Kiss (Left) | Create + L1 + tap ○ |
| | Flying Kiss (Right) | Create + R1 + tap ○ |
| | Salute (Left) | Create + L1 + tap □ |
| | Salute (Right) | Create + R1 + tap □ |
| | Fist Strike (Left) | Options + L1 + tap ↓ |
| | Fist Strike (Right) | Options + R1 + tap ↓ |
| | Palm Strike (Left) | Options + L1 + tap → |
| | Palm Strike (Right) | Options + R1 + tap → |
| | Raise Hand (Left) | Options + L1 + tap ↑ |
| | Raise Hand (Right) | Options + R1 + tap ↑ |
| Waist Movements | Clockwise Rotation | L1 + push right joystick right. Release to return to neutral. Hold to fix; press again to unlock. |
| | Counterclockwise Rotation | L1 + push right joystick left. Release to return to neutral. Hold to fix; press again to unlock. |
| | Bend Forward | L1 + push right joystick down. Release to return to neutral. Hold to fix; press again to unlock. |
| | Straighten Waist | L1 + push right joystick up. Release to return to neutral. Hold to fix; press again to unlock. |
