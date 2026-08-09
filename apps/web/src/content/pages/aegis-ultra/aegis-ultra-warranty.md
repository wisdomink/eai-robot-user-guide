# Safety, Warranty and Compliance

## Important Safety Information

FX Aegis Ultra is a professional-grade quadruped robot equipped with a high-torque drive system, an IP54-rated enclosure, expansion ports, and support for secondary development via SDK and standardized APIs. Aegis Ultra weighs approximately 16 kg, can travel at speeds up to 5 m/s, and can carry combined payloads up to 10 kg. These capabilities make Aegis Ultra significantly more capable — and correspondingly more hazardous when misused — than entry-level products. Always remain attentive during operation to prevent equipment damage, property damage, or personal injury.

### Operating Environment

FX Aegis Ultra is rated **IP54**, providing protection against dust ingress and against splashing water from any direction. IP54 does **not** mean the robot is waterproof or fully weatherproof. Do not operate in the following environments:

- Standing water, streams, pools, or any environment where the robot may be submerged
- Heavy rain, snowstorms, high-pressure water spray, or pressure-washer discharge
- Slippery, oily, icy, or otherwise unstable surfaces
- Tabletops, step edges, stairwells beyond the rated 16 cm step height, ramps steeper than the rated 30°–40° slope capability, or grating with gaps
- Roadways, driveways, or any area with vehicle traffic
- Crowded spaces, confined areas, or areas containing fragile objects
- Near infants, small children, pets, or individuals who cannot move out of the way quickly
- High-temperature, extremely low-temperature, or explosive / flammable atmospheres
- Areas containing corrosive chemicals or sources of strong electromagnetic interference

Maintain a minimum clearance of 3 meters (10 ft) around the robot during locomotion at normal or high speed. Confirm the floor surface can support the robot's weight (16 kg) plus any installed payload or expansion hardware (up to a combined 10 kg).

### Moving Parts Safety

FX Aegis Ultra has 12 powered joints, maximum joint torque of 48 N·m, and a maximum locomotion speed of 5 m/s. Its legs, body, and any user-installed expansion equipment (e.g. robotic arms, LiDAR, depth cameras, external antennas) may present pinching, impact, crush, entanglement, or tip-over hazards.

- Confirm adequate clearance around the robot before powering on.
- Keep fingers, hair, loose clothing, tools, cables, and personal effects clear of joints, feet, and moving parts at all times.
- Do not move, pull, block, straddle, or forcibly reposition the robot while it is executing a motion.
- Before triggering high-dynamic motions — including jumps, backflips, high-speed locomotion, or expansion-arm operations — confirm the area is fully clear of people and obstacles.
- When third-party robotic arms or manipulators are installed, follow the manufacturer's safety instructions for that expansion in addition to the guidance in this manual.
- If the robot exhibits abnormal movement, loses balance, becomes stuck, makes unusual sounds, or overheats, stop operation immediately.

### Professional Operation and Supervision

FX Aegis Ultra is not a toy and is not intended for use by children. It is intended for use by adults 18 years of age and older, and specifically for developers, integrators, researchers, and professional operators who have read and understood this manual.

- Only operators familiar with the safety instructions in this document — and, where applicable, trained on the specific deployment scenario — should control the robot.
- In shared spaces, research labs, workshops, or demonstration environments, designate a responsible operator, cordon off the operating area, and clearly communicate the emergency stop procedure to all attendees.
- Do not allow bystanders — especially children and pets — to be within the robot's motion range during operation.
- Servicing, disassembly, and hardware modifications should be performed only by qualified personnel.

### Emergency Stop and Incident Response

FX Aegis Ultra provides multiple emergency stop paths: the physical emergency stop button on the robot body, the emergency stop control on the pad controller, and the emergency stop function in the App. Before operating the robot, ensure that all operators know the location and function of each emergency stop control.

Stop the robot immediately if any of the following occurs:

- The robot approaches a person, pet, step edge, body of water, or other hazardous area
- The robot moves abnormally, loses balance, or is about to fall
- The robot becomes caught on an object, or its expansion hardware becomes tangled or mechanically restricted
- The pad controller or App becomes unresponsive
- Unusual sounds, odors, or vibrations are detected
- The device overheats, emits smoke, sustains visible damage, or exhibits battery abnormalities
- User-developed code produces unexpected or unsafe behavior

After activating the emergency stop or halting operation, wait for the robot to come to a complete stop and disengage its motors before approaching. Before resuming use, confirm the robot, expansion hardware, surface environment, battery level, and connection status are all normal.

### Battery and Charging Safety

FX Aegis Ultra contains a high-capacity lithium-ion battery pack (216 Wh, nominal 43.2 V). Improper use may result in fire, explosion, or serious injury.

- Use only Faraday Future original charging equipment and accessories, or accessories approved in writing by Faraday Future.
- Do not use batteries, cables, chargers, or connectors that are damaged, deformed, overheated, or have been exposed to liquid.
- Do not charge the robot while it is operating.
- Charge the robot in a dry, well-ventilated area between 0 °C and 40 °C (32 °F–104 °F), away from flammable materials and out of reach of children and pets.
- Do not leave the robot charging unattended for extended periods.
- Do not disassemble, puncture, crush, short-circuit, heat, incinerate, or immerse the battery.
- If the battery swells, leaks, emits odors, generates abnormal heat, or fails to charge normally, stop use immediately, isolate the device in a non-flammable location, and contact Faraday Future support.

Air transport of lithium batteries is regulated. Do not ship the robot or its battery, or carry it as luggage, without confirming applicable dangerous goods regulations.

### Secondary Development, Expansion Ports, and Custom Code

FX Aegis Ultra provides expansion ports (Ethernet, USB, Power, SBUS, UART) and supports secondary development via SDK and standardized APIs. These capabilities are powerful, but they shift additional safety responsibility to the developer or system integrator.

- Test all user-developed motion code, control loops, and autonomous behaviors in a controlled environment — with adequate clearance and emergency stop access — before deployment.
- Do not connect expansion hardware that exceeds the electrical, mechanical, or thermal ratings of the expansion ports.
- Do not modify safety-critical firmware, motor controllers, or battery management systems.
- User-installed third-party expansion equipment — including but not limited to 3D LiDAR, depth cameras, RTK modules, 4G modules, robotic arms, and image transmission modules — must comply with local regulations and must not compromise the robot's balance, weight distribution, cooling, or emergency stop function.
- Faraday Future is not responsible for damage, malfunction, or injury caused by user-developed code, unsafe firmware, or third-party expansion hardware.

### Accessories and Payloads

- Do not exceed the rated combined payload of 10 kg.
- Secure all payloads and expansion hardware to the robot before powering on; unsecured items may fall or shift during high-speed motion and cause injury or damage.
- Keep small components such as screws and mounting hardware away from children.

## After-sales Service

Thank you for choosing FX Aegis Ultra. If a non-user-induced quality issue arises during the applicable warranty period, please contact FF after-sales support with your proof of purchase and product serial number. We will assist with remote diagnostics and, based on the assessment results, provide repair or replacement support in accordance with the FF AI Robotics General After-Sales Service Policy.

The following are **not covered** under this warranty:

- Damage caused by accidental drops, impact, liquid exposure beyond the IP54 rating, submersion, or other external physical causes
- Damage caused by operating the robot in environments prohibited by this manual
- Damage caused by misuse, exceeding the rated payload, or use inconsistent with the product's intended purpose
- Damage caused by unauthorized disassembly, modification, or servicing
- Damage caused by use of non-genuine batteries, chargers, or accessories
- Damage caused by connecting incompatible or out-of-spec devices to expansion ports
- Damage or safety incidents caused by third-party expansion hardware, whether officially compatible or not
- Malfunctions resulting from user-developed code, user-installed firmware, modified motor or balance control parameters, or other developer-initiated actions

Use only the original charging equipment provided with the product. If the battery swells, generates abnormal heat, emits smoke, or produces unusual odors, stop use immediately and contact FF after-sales support.

Returns and exchanges are handled through the original point of purchase and in accordance with applicable local consumer protection laws. Complete terms are governed by the FF AI Robotics General After-Sales Service Policy.

After-sales support: [support.ff.com](https://support.ff.com)

After-sales email: [support@ff.com](mailto:support@ff.com)

## Regulatory and Compliance Information

FX Aegis Ultra contains wireless communication modules (Wi-Fi and Bluetooth), an electronic control system, expansion ports, a rechargeable lithium-ion battery pack, and charging accessories. Regulatory information, certification numbers, compliance statements, labeling requirements, and user notices for the United States, Canada, and other applicable regions are provided on the product packaging and on the device rating label.

Unauthorized modification, disassembly, servicing, or replacement of wireless, battery, motor, or power-related components may affect device safety, radio frequency compliance, and void warranty coverage.

**Expansion equipment installed by the user** — including but not limited to 3D LiDAR, depth cameras, RTK modules, 4G or other wireless modules, external antennas, and robotic arms — must be independently certified and compliant with applicable local regulations. Faraday Future's compliance certification does not extend to user-installed third-party hardware, and the user is responsible for ensuring the overall system remains compliant with all applicable regulations after any modification.

For additional regulatory documentation, contact the FF after-sales team at [support@ff.com](mailto:support@ff.com) or visit [support.ff.com](https://support.ff.com).
