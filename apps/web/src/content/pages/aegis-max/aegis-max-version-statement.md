# Version Statement

## 1.1 Legal Statement

Before using this product, users must carefully read the user manual and operate the product strictly in accordance with its contents. The company shall not be held liable for any property damage or personal injury resulting from the use of the product in violation of the instructions in this manual. This product consists of multiple components. Please ensure that children cannot access the product to avoid accidents. This product is only for use by persons aged 18 and above. To extend the product's service life, do not use it in high-temperature or high-pressure environments. This manual aims to include functional descriptions and usage instructions for the product as comprehensively as possible. However, due to continuous improvements in functionality and design changes, there may be discrepancies between the actual product and the manual content. If there are differences between the actual product and this manual in terms of colour, appearance, etc., please refer to the actual product.

## 1.2 Precautions

This manual applies to the Aegis Max version (Model: [FF model code to be assigned]).

### A. Application of the Robot

- Terrain: Please try to avoid walking on smooth surfaces such as glass or ice; if walking is necessary, reduce the robot's walking speed to prevent slipping and falling.
- Climate / Weather: Please avoid deploying the robot in severe weather conditions such as heavy fog, thunderstorms, sandstorms or strong winds whenever possible.
- Communication Interference: Do not operate the robot in any environment with severe communication signal interference from sources such as WiFi or RF; if necessary, turn off the interference sources or reduce their interference.
- Electromagnetic Interference: Do not operate the robot in environments with strong electromagnetic interference, such as near high-voltage power lines, high-voltage substations, communication base stations or signal towers. If necessary, consult after-sales service first.
- IP Protection: The robot has a protection rating of IP67, allowing it to walk 1 m underwater for 30 min. Before use, keep the robot in proper condition — exterior undamaged, expansion port cover securely closed, battery and its compartment dry and free of moisture. After completing 30 min of underwater walking, promptly remove the robot from the water, thoroughly wipe and dry its body, and perform any required maintenance before the next underwater operation. Any malfunction caused by prolonged water immersion may void the warranty.
- Maximum Speed: The robot can reach a maximum speed of 6 m/s, with significant impact force. At any high speed, keep the robot away from crowds.
- Mode of Motion: The modes of motion are Stationary Mode, Sport Mode, Navigation Mode and Stair Climbing Mode. Switch between modes according to the environmental scenario.
- Recovery from a Fall: The robot requires space to regain its standing posture after a fall. To avoid collisions, ensure no persons or objects within 2 m around the robot. Do not drag a fallen robot when its hard emergency stop has not been triggered.

### B. Battery Application

- If the battery emits a noticeable odour, shows signs of overheating or exhibits corrosion before initial use, contact the battery supplier.
- Before allowing children to use the equipment, adults must clearly explain how to use the equipment and the battery, and periodically follow up to confirm proper use.
- Do not use or place the battery in an extremely high temperature environment (e.g. over 60℃, such as under intense direct sunlight or inside an extremely hot vehicle). The battery may overheat or catch fire, its performance may degrade and its service life may be shortened.
- Do not use the battery in any environment with electrostatic discharge over 1,000 V, as this may damage the protection circuit and create a safety hazard.
- The battery can only be charged within the temperature range of 0 to 50℃. Charging outside this temperature range may cause the battery to leak liquid, overheat or suffer severe damage, and may degrade its performance and lifespan.
- Do not charge or discharge the battery near anything flammable, as this may create a fire hazard.
- The battery will automatically enter storage mode when a single-cell undervoltage condition is detected. In this mode the battery does not respond to the power switch and the battery indicator remains off. The battery exits storage mode after being charged.
- Once powered off via the battery button, the battery enters sleep mode and can be woken by communication, by pressing the button, or by charging.
- If the battery circuit terminal becomes dirty, wipe it clean with a dry cloth before use; otherwise poor contact may lead to performance failure.
- The battery should be stored at room temperature and charged to 30%–60% of its capacity. To prevent over-discharge, charge the battery to 50% with the standard charging method once every 3 months. If the battery has been stored for over one year, perform one full charge–discharge cycle annually with the standard method to activate the battery.
- A battery left unused for an extended period may become over-discharged through self-discharge, and the cell may even discharge to 0 V. Continued use of such a battery carries risk. Charge the battery regularly to maintain its voltage between 30% and 60% of capacity.
- The plug cord has limited tension resistance and excessive pulling force may damage the battery. Once the battery is installed, do not swing the battery or the plug cord freely.
- Do not use or store the battery near fire or a heater, or in a high-temperature environment (>80℃).
- The use of any unauthorised charger is prohibited. Any damage to the battery caused thereby is not covered under warranty.
- Do not connect the battery with reversed polarity, and do not short-circuit the battery by connecting the positive and negative terminals with wires or any other metal objects.
- Do not incinerate or heat the battery, and do not subject it to excessive mechanical shock such as striking, throwing or stomping. Do not pierce the battery with nails or other sharp objects.
- Do not disassemble the battery — disassembly will void the warranty.

### C. Other Precautions

- If the robot shows signs of water ingress, immediately turn off its power, remove the battery and allow it to dry thoroughly.
- If the robot smokes or catches fire, use a carbon dioxide or dry powder extinguisher. Do not use foam extinguishers.
- If the robot exhibits uncontrolled motion such as leg swinging, first trigger the soft or hard emergency stop and ensure the safety of personnel, then power off and remove the battery before troubleshooting. Report difficult problems to technical support for troubleshooting, repair or replacement.
- Unauthorised disassembly of the robot is prohibited. The warranty will be voided if the robot is disassembled.
- Moving parts — keep body parts away from moving parts.

> **Review note:** Regulatory statements — omitted deliberately<br>The source manual carries FCC, ISED/IC, Thai NBTC and French-language regulatory statements at this point. They are tied to the original certification holder and its FCC ID and are therefore not reproduced.<br>FF's own compliance statements must be inserted here once certification is in place. See the release checklist on the Home page.

### D. Open Network Ports

The following ports are open on the device.

| No. | Port | Open? | Function |
| --- | --- | --- | --- |
| 1 | 21 | Yes | Network log download service, for retrieving system logs remotely. |
| 2 | 22 | Yes | SSH development and debugging entry, for remote access and diagnostics. |
| 3 | 5555 | Yes | ADB debugging entry point. Port remains open; password authentication is enforced. |
| 4 | 7447 | Yes | ROS topic routing entry, for inter-module message passing. |
| 5 | 8081 | Yes | App control port, for the application-layer command and control interface. |
| 6 | 8554 | Yes | RTSP video streaming port, real-time video data transmission (stream 1). |
| 7 | 8555 | Yes | RTSP video streaming port, real-time video data transmission (stream 2). |
| 8 | 5760 | Yes | TCP connection port, remote controller communication link. |
| 9 | 50000 | Yes | Dedicated port for gimbal control and cloud platform integration. |
