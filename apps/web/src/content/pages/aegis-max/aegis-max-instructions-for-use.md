# Preparation & Startup

## Environment Requirement

- Before powering on, the operator shall thoroughly read this manual to become familiar with all functional states, operational details and precautions.

- During initial operation, avoid the robot moving out of sight and ensure no person or obstacle is within 2 m around it, to prevent collision.

- Temperature: use the robot within an ambient temperature range of -20°C to 55°C.

- Weather: do not power on and use the robot in severe weather such as heavy fog, thunderstorms, sandstorms or tornadoes.

- Electromagnetic environment: avoid using the robot in environments with strong electromagnetic interference (high-voltage power lines, transmission substations, communication signal towers) to prevent magnetic breakdown.

- Communication environment: do not power on and remotely operate the robot in environments with communication signal interference, to avoid communication disruption and loss of connection.

## Unpacking

1. Place the flight case on a flat surface with the correct orientation upward.
2. Open and remove the lid.
3. Remove the robot, battery, remote control and charger cradle in sequence, and place them on a hard, flat surface.

**Warning:**

- When moving the robot out, hold the designated lifting points as instructed, and pay attention to the location and content of warning labels to avoid pinching or scratching hands.

- Handle the robot, battery, remote control and charger cradle gently during transport.

- After transport, check that the FX Aegis Max emergency stop button and battery power button have not been triggered.

![Unpacking the flight case](/images/aegis-max/aegis-mega-a-d1-09.png)

## Pre-start Inspection

### Appearance and Mechanical Structure

- Overall exterior integrity: check the body shell for cracking, deformation or detachment, focusing on vulnerable parts such as joint connections and sensor protective covers. Check for obvious stains, liquid residue or foreign matter on the body surface, especially around radiator holes and interfaces.

- Joint and moving parts: check each leg joint and wheel leg to confirm that joint motion is smooth, without sticking, abnormal noise or looseness. For wheel-legs, confirm the anti-slip tread is clear, without cracking or peeling. Confirm that fasteners such as screws and clips at the joints are not missing or loose.

### Battery Status

- Battery appearance: check whether the battery pack shell is bulging, leaking or damaged. Bulging may indicate the battery is aged or overcharged — do not use it; replace it immediately to avoid fire or explosion risk.

- Battery connection: check that the interface between the battery and the body is clean and free from oxidation, corrosion or foreign matter. Ensure the latch is fastened securely when inserting, to avoid power interruption due to poor contact.

- Battery level: before power-on, judge the battery level via the indicator — at least one battery should have more than 2 bars of charge. Click the battery power button to display the exact charge level. In a low-battery state, charge first to avoid mid-operation shutdown.

### Environmental Perception Sensors

- Optical sensors: check that camera and LiDAR lenses are clean and free from stains, scratches or obstructions.

- Distance / obstacle avoidance sensors: check that the probes of obstacle avoidance components such as ultrasonic sensors are intact and unobstructed.

### Remote Control

- Check that the remote control buttons are responsive without sticking, and that the battery has sufficient charge, to ensure normal operation once the robot is powered on.

- Check the display screen, indicator lights and speakers. Confirm the display is undamaged and free of distortion, and that indicators illuminate normally, so that operating status (battery level, fault warning) can be read once powered on.

## Pre-start Preparation

### Install the Battery

The robot supports single-battery and dual-battery power supply.

1. Align the battery with the compartment interface. Its keyed design prevents incorrect insertion.
2. Pull up the battery hand strap and push the battery in until it bottoms out.
3. Release the strap. A click indicates that the latch is locked.
4. Check that the outer surface of the battery is flush with the robot body.


### Place the Robot

Adopt a horizontal prone posture: abdomen fully flush with the ground, legs naturally positioned on either side of the body, lower legs in a minimally retracted stance, with all four knee joints and wheel feet flat on the ground, and no thigh or lower leg compressed by the torso.

![Prone posture before startup](/images/aegis-max/aegis-mega-a-d1-10.png)

## Startup and Operation

### Power-On Process

1. Briefly press the battery button to activate it. The indicator stays on and shows the current charge level.
2. Press and hold the battery button for 3 seconds to power on the battery and boot the robot.

A flashing white status indicator means startup is in progress. A steady white light indicates startup is complete and the robot has entered universal motion mode.


<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Battery Status | Power-On Process |
| --- | --- |
| Robot powered off, no battery inserted | Insert only one battery: either insert a battery that is already powered on, or first insert a powered-off battery and then power on the battery to start the robot. |
| Robot powered off, one powered-off battery inserted | Insert another powered-on battery to start the robot. An inserted powered-off battery will start automatically 1 min after insertion. Alternatively, insert another powered-off battery, then power on either battery. |
| Robot powered off, two powered-off batteries inserted | Either battery can be powered on to start the robot as a whole. The other battery will be engaged automatically without manual activation. |

</div>

**Warning:**

- The dual batteries feature mutual wake-up. In dual-battery mode, only both-on or both-off states are supported; one battery on and one off is not supported.

- When FX Aegis Max is powered on with a single battery, inserting another battery — powered on or off — will automatically activate and connect it.

### Power On the Remote Control

![Remote controller and power button](/images/aegis-max/aegis-mega-a-d1-11.png)

1. Press and hold the remote control power button. The screen and power indicator illuminate.

   The controller is paired one-to-one with the robot before delivery and connects automatically on startup.

2. Tap the app icon to enter the control interface.
3. Confirm the app health status before controlling the robot.


For button mappings and app controls, see [Remote Control](/aegis-max/remote-control). The separate remote controller manual title is not yet assigned.

### First Power-On Verification

- Basic motion test: use the app to command the robot to stand, go prone, move forward, backward, left and right, and turn. Confirm joints move freely. In case of jerking, abnormal noise or inability to stand, power off immediately and check for joint jamming or incorrect posture.

- Sensor status test: confirm all vision, laser, ultrasonic and inertial navigation sensors function normally and data displays properly in the app.

- Status feedback: observe the equipment status shown by the LEDs, display and app to confirm normal battery level, connection signal and firmware version. If a fault prompt appears, troubleshoot according to this manual.

### Initial Security Setup

- On the first SSH login after boot, a mandatory password-change prompt appears. Debug interface access is denied until the password is changed.
- Change the Wi-Fi hotspot password directly in the app.
- The app supports a 6-digit numeric lock-screen PIN. Verification is required after a 14-minute timeout; repeated incorrect entries trigger a temporary lockout.
