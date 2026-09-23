# Body & Battery Indicators

The robot displays its current status through the head screen expressions, the chest light, and the ear lights. The chest light mainly indicates the robot's operating, battery and fault status; the ear lights mainly indicate real-time interaction states such as listening and speaking.

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Category | Status | Description | Light Effect |
| --- | --- | --- | --- |
| Chest Light – Daily Status | Resting | When the robot is lifted up and no other status is triggered | Light off |
|  | Standby | The robot is powered on and waiting for user operation | Solid white |
|  | Charging | The robot is charging and not yet fully charged | Breathing white |
|  | Working | The robot is performing tasks such as navigation, guiding, delivery, dancing, or combat | Solid white |
| Voice Interaction | Listening | The robot is receiving the user's voice | Flowing white |
|  | Speaking | The robot is performing voice interaction tasks such as conversation, guiding, or skill expression.<br>Note: non-voice-interaction scenarios such as dancing, system announcements, and audio announcements triggered from the client do not trigger this light effect | Flowing white |
| Reminders and Faults | Find Robot | The user is locating the robot via the client | Red strobe (300 ms) |
|  | Critical Fault | A critical fault has occurred. Stop using the robot immediately and inspect it according to the system prompts | Solid red |
|  | Device Locked | The robot has entered the locked state |  |
|  | Emergency Stop | Manual intervention for an out-of-control or dangerous situation of the robot |  |
|  | Fault | A fault has occurred and must be handled according to the system prompts | Does not affect the light effect |
|  | Warning | A condition requiring attention has occurred; for example, when one battery is removed, the robot displays the warning light effect |  |
|  | Low Battery | When the combined level of "both batteries" drops to 30% or below, recharge or replace the batteries promptly | Solid white |
|  | Extremely Low Battery | When the combined level of "both batteries" drops to 10% or below, recharge or replace the batteries promptly | Solid red |

</div>

## Battery Indicator

Note: When using battery power, closely monitor the battery level. Low or nearly depleted batteries may cause the robot to topple suddenly due to insufficient output power. Recharge or replace the battery immediately when only one indicator remains, to maintain stable operation and avoid personal injury caused by the robot falling.

### Location of Battery Indicator Lights

![FF All-New Futurist Ultra — Body & Battery Indicators](/images/futurist-ultra/futurist-ultra-ultra-v32-07.png)

### Indicator Status Description (Working)

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Battery Light Status (Working) | Battery Level | Status Description |
| --- | --- | --- |
| All LEDs off | 0% | No power |
| LED1 on, LEDs 2-4 off | 1% ≤ Battery Level &lt; 25% | Critical Low Power (Recharge Immediately) |
| LEDs 1-2 on, LEDs 3-4 off | 25% ≤ Battery Level &lt; 50% | Low Power |
| LEDs 1-3 on, LED4 off | 50% ≤ Battery Level &lt; 75% | Sufficient power |
| LEDs 1-4 on | 75% ≤ Battery Level &lt; 100% | Full power |

</div>

### Indicator Status Description (Charging)

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Battery Light Status (Charging) | Battery Level | Status Description |
| --- | --- | --- |
| LED1 breathing, LEDs 2-4 off | Battery Level &lt; 25% | Critical Low Power |
| LED1 on, LED2 breathing, LEDs 3-4 off | 25% ≤ Battery Level &lt; 50% | Low Power: Do not disconnect |
| LEDs 1-2 on, LED3 breathing, LED4 off | 50% ≤ Battery Level &lt; 75% | Medium Power: Operable; charging to full recommended |
| LEDs 1-3 on, LED4 breathing | 75% ≤ Battery Level &lt; 100% | Sufficient Power: Operable |
| LEDs 1-4 on | Battery Level = 100% | Charging Complete: Power can be disconnected |

</div>
