# Instructions for Use

## 3.1 Environment Requirement

- Before powering on, the operator shall thoroughly read this manual to become familiar with all functional states, operational details and precautions.
- During initial operation, avoid the robot moving out of sight and ensure no person or obstacle is within 2 m around it, to prevent collision.
- Temperature: use the robot within an ambient temperature range of -20℃ to 55℃.
- Weather: do not power on and use the robot in severe weather such as heavy fog, thunderstorms, sandstorms or tornadoes.
- Electromagnetic environment: avoid using the robot in environments with strong electromagnetic interference (high-voltage power lines, transmission substations, communication signal towers) to prevent magnetic breakdown.
- Communication environment: do not power on and remotely operate the robot in environments with communication signal interference, to avoid communication disruption and loss of connection.

## 3.2 Unpacking

The robot is packed in a flight case. Place the case on a flat surface with the correct orientation upward, open and remove the lid, then sequentially remove the robot, battery, remote control and charger cradle, and place them on a hard, flat surface.

### Warning

- When moving the robot out, hold the designated lifting points as instructed, and pay attention to the location and content of warning labels to avoid pinching or scratching hands.
- Handle the robot, battery, remote control and charger cradle gently during transport.
- After transport, check that the Aegis Max emergency stop button and battery power button have not been triggered.

![FF Aegis Max figure 8 — description pending review](/images/aegis-max/aegis-max-figure-08.png)

*Source figure — reference only; FF artwork required before publication.*

## 3.3 Pre-start Inspection

### A. Appearance and Mechanical Structure

- Overall exterior integrity: check the body shell for cracking, deformation or detachment, focusing on vulnerable parts such as joint connections and sensor protective covers. Check for obvious stains, liquid residue or foreign matter on the body surface, especially around radiator holes and interfaces.
- Joint and moving parts: check each leg joint and wheel leg to confirm that joint motion is smooth, without sticking, abnormal noise or looseness. For wheel-legs, confirm the anti-slip tread is clear, without cracking or peeling. Confirm that fasteners such as screws and clips at the joints are not missing or loose.

### B. Battery Status

- Battery appearance: check whether the battery pack shell is bulging, leaking or damaged. Bulging may indicate the battery is aged or overcharged — do not use it; replace it immediately to avoid fire or explosion risk.
- Battery connection: check that the interface between the battery and the body is clean and free from oxidation, corrosion or foreign matter. Ensure the latch is fastened securely when inserting, to avoid power interruption due to poor contact.
- Battery level: before power-on, judge the battery level via the indicator — at least one battery should have more than 2 bars of charge. Click the battery power button to display the exact charge level. In a low-battery state, charge first to avoid mid-operation shutdown.

### C. Environmental Perception Sensors

- Optical sensors: check that camera and LiDAR lenses are clean and free from stains, scratches or obstructions.
- Distance / obstacle avoidance sensors: check that the probes of obstacle avoidance components such as ultrasonic sensors are intact and unobstructed.

### D. Remote Control

- Check that the remote control buttons are responsive without sticking, and that the battery has sufficient charge, to ensure normal operation once the robot is powered on.
- Check the display screen, indicator lights and speakers. Confirm the display is undamaged and free of distortion, and that indicators illuminate normally, so that operating status (battery level, fault warning) can be read once powered on.

## 3.4 Pre-start Preparation

### A. Install the Battery

The robot is equipped with dual battery compartments, supporting both single-battery and dual-battery power supply. Align the battery with the compartment interface (which has a foolproof design to prevent incorrect insertion), pull up the battery hand strap, push the battery in until it bottoms out, then release the strap. A click indicates the latch is locked. Once installed, check the battery installation status — the outer surface of the battery should be flush with the surface of the robot body.

### B. Place the Robot

Adopt a horizontal prone posture: abdomen fully flush with the ground, legs naturally positioned on either side of the body, lower legs in a minimally retracted stance, with all four knee joints and wheel feet flat on the ground, and no thigh or lower leg compressed by the torso.

![FF Aegis Max figure 9 — description pending review](/images/aegis-max/aegis-max-figure-09.png)

*Source figure — reference only; FF artwork required before publication.*

## 3.5 Startup and Operation

### A. Power-On Process

Power-on is initiated through the battery. Briefly press the battery button to activate the battery — its indicator will be normally on and display the current charge level. Then press and hold the battery button for 3 s to turn on the battery and boot the robot. A white blinking status indicator signifies startup in progress; a steady white light indicates startup is complete and the robot has entered universal motion mode.

| Battery Status | Power-On Process |
| --- | --- |
| Robot powered off, no battery inserted | Insert only one battery: either insert a battery that is already powered on, or first insert a powered-off battery and then power on the battery to start the robot. |
| Robot powered off, one powered-off battery inserted | Insert another powered-on battery to start the robot. An inserted powered-off battery will start automatically 1 min after insertion. Alternatively, insert another powered-off battery, then power on either battery. |
| Robot powered off, two powered-off batteries inserted | Either battery can be powered on to start the robot as a whole. The other battery will be engaged automatically without manual activation. |

### Warning

- The dual batteries feature mutual wake-up. In dual-battery mode, only both-on or both-off states are supported; one battery on and one off is not supported.
- When Aegis Max is powered on with a single battery, inserting another battery — powered on or off — will automatically activate and connect it.

![FF Aegis Max figure 10 — description pending review](/images/aegis-max/aegis-max-figure-10.png)

*Source figure — reference only; FF artwork required before publication.*

### B. Power On the Remote Control

Press and hold the remote control power button; the screen and power indicator will illuminate. The remote control is paired one-to-one with the robot before delivery and will connect automatically on startup. Once the remote control is on, tap the app icon on the screen to enter the control interface. Once the app health status is confirmed, you can control the robot.

### C. Operation Guide

For remote control operation, refer to the [FF remote controller user manual — title to be assigned].

### D. First Power-On Verification

- Basic motion test: use the app to command the robot to stand, go prone, move forward, backward, left and right, and turn. Confirm joints move freely. In case of jerking, abnormal noise or inability to stand, power off immediately and check for joint jamming or incorrect posture.
- Sensor status test: confirm all vision, laser, ultrasonic and inertial navigation sensors function normally and data displays properly in the app.
- Status feedback: observe the equipment status shown by the LEDs, display and app to confirm normal battery level, connection signal and firmware version. If a fault prompt appears, troubleshoot according to this manual.
- Initial password setup for a new device: (1) after first boot, a mandatory password-change prompt appears on SSH remote login, and debug interface access is denied until the password is changed; (2) the Wi-Fi hotspot password can be changed directly in the app; (3) the app supports a 6-digit numeric lock-screen PIN, verification is required to re-enter the app after a 14-minute timeout, and repeated wrong entries trigger a temporary lockout.

## 3.6 Battery Swapping and Power-Off

### A. Change the Battery

The robot features dual batteries with hot-swap capability. When powered by both batteries, you can unplug one powered-on battery and replace it with a battery in either an on or off state. The robot continues operating normally during battery changing.

![FF Aegis Max figure 11 — description pending review](/images/aegis-max/aegis-max-figure-11.png)

*Source figure — reference only; FF artwork required before publication.*

### B. Power Off

In single-battery or dual-battery mode, turn off any battery. The battery indicator will go out, the robot status indicator will go out, and the robot will power off. To power off the remote control, press and hold its power button.

### Warning

- Whenever possible, first place the robot in a horizontal prone posture before powering off. Avoid powering off directly while the robot is standing.
- When the robot has only one powered-on battery, it is prohibited to shut down by pulling out that battery.

## 3.7 Emergency Stop and Protection

### A. Hard Emergency Stop

- Trigger: when the robot is out of control or malfunctioning, in either autonomous or remote-control mode, press the red hard emergency stop button on the robot's back. The hard emergency stop red light will be normally on, the robot will slowly lie down and remain motionless, and a real-time alert will appear in the app.
- Release: turn the hard emergency stop button clockwise to release it.

### B. Soft Emergency Stop

- Trigger: when the robot is out of control or malfunctioning, press the soft emergency stop button on the remote control. The robot will cease its current action and remain stationary in a standing posture, and a real-time alert will appear in the app.
- Release: once the robot and its surroundings are confirmed safe, release the soft emergency stop via the app, restoring both app and robot to normal status.

### C. Overheat Protection

The robot has comprehensive temperature detection. If a joint, the main control or the battery overheats, the robot enters overheat protection, ceasing all motion, going prone and remaining still. The overheat location and temperature can be viewed in the app. Once the temperature drops to normal, operation can continue.

### D. Low Battery Protection

When the charge level of both batteries falls below 20%, the robot enters a low battery warning state and should be charged immediately. Below 10%, low battery protection triggers: the robot goes prone automatically and no longer responds to remote control commands. Replace the batteries before continuing use.

### E. Fall Protection

The robot attempts to recover to a standing position after a fall, under the control of a reinforcement learning motion control model. Where the surrounding environment does not permit recovery, the robot maintains a fixed posture and raises an alarm.

### F. Expansion Bay Power Supply Protection

The expansion bay has a separate power button allowing independent control of its power state. When the machine is powered on as a whole and the mounted payload must be replaced, the expansion bay button can power off all interfaces in the bay without powering down the machine. The button is located inside the compartment to avoid accidental external contact powering down the upper assembly.

## 3.8 Payload Expansion

The space on the robot's back is flat, with a load of 30 kg. It is equipped with dual rails on the back to facilitate installation of mounted payload.

![FF Aegis Max figure 12 — description pending review](/images/aegis-max/aegis-max-figure-12.png)

*Source figure — reference only; FF artwork required before publication.*

The back of the robot has an expansion bay entrance. The power and communication cables of the mounted payload enter the expansion bay and connect to the aviation plug, enabling power supply and communication between the robot and the payload.

> **Review note:** Payload figure — unresolved in the source<br>This section states 30 kg while the Core Specification table states an effective payload of 25 kg. Both figures appear as such in the Chinese source and are reproduced unchanged. Confirm the final value before publication.

### Warning

- Once fitted with a payload, the robot supports basic motion modes only. Do not use elevated-platform manoeuvres after adding a payload.
- Adding a payload to the back may affect motion performance. Consult after-sales service staff before installation.
- When using an external power interface to supply a load, the total power provided must not exceed 480 W.
- To ensure the IP67 rating, all interfaces shall use IP67 aviation plugs with protective caps. Cover any unused aviation plug interfaces with caps.
- When installing a top-mounted payload and connecting the power interface, ensure the robot or the expansion bay is powered off.

## 3.9 Charging

### A. Unplug the Battery

- Place the robot in a horizontal prone posture, with the abdomen completely against the ground, legs naturally placed on both sides of the body, lower legs fully retracted, and all four knee joints and wheel-legs flat on the ground. Lift the front and rear legs on the battery side in sequence to leave space for unplugging the battery.
- Alternatively, before turning off the robot, execute the battery swapping posture — the robot automatically assumes a horizontal prone posture and lifts the front and rear legs on the battery side.
- Gently pull the battery hand strap to unlock the battery latch, then pull the battery out.

![FF Aegis Max figure 13 — description pending review](/images/aegis-max/aegis-max-figure-13.png)

*Source figure — reference only; FF artwork required before publication.*

### B. Charging Preparation

- Check the battery exterior for integrity and confirm no bulging, leakage or other damage.
- Place the charger cradle on a hard, flat surface to ensure stable placement and prevent tipping during charging.
- Connect the charger to AC mains. Turn on the charger cradle's rocker switch — a steady red light means the cradle is connected and powered on.
- The charging environment should be dry and cool, away from anything flammable or explosive, with the ambient temperature around the charger cradle between 0 and 50℃.

![FF Aegis Max figure 14 — description pending review](/images/aegis-max/aegis-max-figure-14.png)

*Source figure — reference only; FF artwork required before publication.*

### C. Battery Charging

- Align the battery with the charging interface on the cradle and insert it into the battery holder. Single-battery and dual-battery charging are both supported.
- A steady green indicator on the cradle corresponding to the battery indicates stable charging.
- The battery indicator illuminates in sequence to display charging progress. A steady LED denotes that its corresponding battery segment is fully charged; a rapidly flashing LED denotes the segment currently charging.
- When the battery is fully charged, all four indicators remain on. Promptly disconnect the battery or the cradle power source. Charging time should not exceed 6 hours.
- Once a fully charged battery is removed, promptly turn off the charger cradle to avoid the plug remaining live and posing a risk of electric shock.

It is prohibited to charge the battery using third-party chargers or charger cradles.

![FF Aegis Max figure 15 — description pending review](/images/aegis-max/aegis-max-figure-15.png)

*Source figure — reference only; FF artwork required before publication.*

### D. Remote Control Charging

- Charge the remote control with the original USB charger (AC 100–240 V, USB Type-C).
- During charging, the battery indicator illuminates in sequence to display progress. A steady LED denotes a fully charged segment; a rapidly flashing LED denotes the segment currently charging.
- To maintain the remote control battery in optimal condition, fully charge it once a month.

![FF Aegis Max figure 16 — description pending review](/images/aegis-max/aegis-max-figure-16.png)

*Source figure — reference only; FF artwork required before publication.*

## 3.10 Transporting

Two modes of transport are supported: transporting while powered off, and transporting while powered on.

### A. Powered-Off Transport

- Place the robot in a horizontal prone posture, abdomen completely flush against the ground, legs naturally placed on either side of the body, lower legs fully retracted, and four knee joints and wheel-legs flat on the ground.
- Two persons shall stand at the head and tail of the robot respectively and use both hands to hold the designated lifting points (the position of the lower leg near the knee joint), lifting the thigh and lower leg upward to the joint limit to prevent the legs from swinging.
- Once at the destination, place the robot on the ground, still in a horizontal prone posture.

![FF Aegis Max figure 17 — description pending review](/images/aegis-max/aegis-max-figure-17.png)

*Source figure — reference only; FF artwork required before publication.*

### B. Powered-On Transport

The robot features a locked posture. While powered on, its limbs can be locked, allowing a single worker to carry the robot by gripping the bumper with both hands.

![FF Aegis Max figure 18 — description pending review](/images/aegis-max/aegis-max-figure-18.png)

*Source figure — reference only; FF artwork required before publication.*

### Warning

- Pay close attention to the warning labels on the robot during transport, to avoid pinching hands with the legs.
- When transporting the robot while powered on, or immediately after powering off, grasp it as far from the joints and battery as possible to avoid burns from heat generated by the battery or joints.

## 3.11 Storage

### A. Preparation before Storage

- Environment: the storage environment shall be at a temperature of -20℃ to 60℃, kept dry and ventilated, and away from strong magnetic fields (high-power transformers, electromagnets) and strong vibration sources (generators, crushers).
- Cleaning: remove dust, stains and other impurities from the surfaces of the robot body, remote control, battery and charger cradle. Avoid liquids entering interfaces and radiator holes, to prevent moisture damage to internal components.
- Status check: check the robot, remote control, battery and charger cradle to ensure no physical damage and good functional condition.
- Battery charge regulation: charge the battery to 50%–60%. This range prevents damage from excessive discharge while avoiding capacity degradation from long-term storage at full charge.

### B. Storage Method for Each Component

- Robot: power off a cleaned robot, remove its batteries and place it stably inside the dedicated packing case.
- Battery: place the two removed batteries in the packing case, each stored separately to avoid mutual compression or collision. Prevent the positive and negative poles from contacting metal objects, to avoid short circuits.
- Remote control: power it off, place it in the dedicated protective sheath and store both in the packing case. Avoid severe impact or compression that could crack the shell, damage buttons or break the display.
- Charger: place the charger in the dedicated storage bag or the charger storage space inside the packing case. Keep it isolated from other metal components to prevent wear or damage to the charger interface. Check that the plug is intact; if damage or rust is found, replace it before storage.
- Packing case: fold the case neatly and place it in a dry, ventilated environment. Avoid moisture, mould, or deformation from heavy objects. If the case is damaged or its load-bearing capacity is reduced, replace it with a new dedicated case.

### C. Maintenance and Inspection during Storage

Short-term storage (1–3 months)

- Conduct a monthly visual inspection of the robot, batteries, remote control and charger to confirm no damage, deformation, rust or other defects.
- Check the battery charge level once; if below 40%, charge to 50%–60% before continuing storage.
- Check whether the temperature and humidity of the storage environment are satisfactory, and promptly replace any desiccant that has become ineffective.

Long-term storage (over 3 months)

- Conduct a power-on test once every 2 months: connect the robot to a power source or install batteries, power it on and run it for 5–10 min, checking that all functions are normal and joints move freely.
- Perform charge–discharge maintenance on the batteries once a month (discharge to 30%, then recharge to 60%) to prevent memory effect and preserve capacity.
- Perform a functional check on the remote control and charger once every 3 months, testing button sensitivity and charging function. If abnormalities are found, contact after-sales service for repair.

### D. Precautions for Storage

- Do not store the robot or its accessories upside down or tilted. Upside-down storage may cause internal components to shift or become damaged.
- During storage, do not place heavy objects on the equipment or its packing case, to prevent deformation or component damage.
- If the equipment is taken out of storage for use, first let it rest at room temperature for 1–2 hours where there is a significant temperature difference between storage and usage environments. Wait until the device temperature matches ambient temperature before starting up, to prevent internal condensation and damage to electronic components.
- Do not let any non-professional disassemble the robot, battery, remote control or charger during storage. If malfunctions or abnormalities are detected, contact after-sales service for professional inspection and repair.
- Keep detailed storage records (time of storage, inspection dates, maintenance status) to facilitate subsequent tracing and timely identification of potential problems.
