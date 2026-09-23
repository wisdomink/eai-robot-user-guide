# Autonomous Charging

## Functional Overview

> 🦄 • Autonomous charging is a prerequisite for the robot to achieve 7 x 24-hour autonomous operation.
> • When the robot needs recharging, it autonomously navigates to the charging point and completes actions such as identifying and plugging in the charging gun to start charging; after charging is complete, it autonomously performs the wrap-up actions — unplugging, holstering the gun, and retracting the arm — and ends charging on its own.

![FF All-New Futurist Ultra — Autonomous Charging](/images/futurist-ultra/futurist-ultra-ultra-v32-52.png)

![FF All-New Futurist Ultra — Autonomous Charging](/images/futurist-ultra/futurist-ultra-ultra-v32-53.png)

## Preparation

> Prerequisites: Complete mapping first, and make sure the robot is in motion mode and has been localized on the current map. This section covers the autonomous charging function only; for mapping, navigation, and relocalization, refer to the corresponding user manuals.

### Deploying the Charging Point

1. Fix the charging gun base to the edge of a light-colored table with the fixing clip (deployment on dark-colored tables is not supported in this release); table height: 75–95 cm. Connect the other end to a power supply.

2. Attach the charging point marker board in the orientation shown: align its bottom edge with the table edge and press its right edge tightly against the charging gun base; peel off the protective film on the back and stick it to the desktop.

3. Remote-control the robot to the table where the charging gun is fixed.

#### Secure the charging connector to the edge of the table

![Secure the charging connector to the edge of the table](/images/futurist-ultra/futurist-ultra-ultra-v32-54.png)

#### Attach the charging-point marker

![Attach the charging-point marker](/images/futurist-ultra/futurist-ultra-ultra-v32-55.png)

#### Use the remote controller to move the robot next to the table.

![Use the remote controller to move the robot next to the table.](/images/futurist-ultra/futurist-ultra-ultra-v32-56.png)

4. Open the App map page and select Edit Map.

5. Select Point → Record → Charging Point in turn. The live feed from the robot's chest camera appears in the upper-left corner, and the dashed box in the lower-right corner indicates the best deployment position for the charging gun.

6. Fine-tune the robot's position with the controller or by dragging until the charging gun is inside the dashed box; the dashed box turns green once the charging gun is detected.

7. Tap Charging Point → Mark, name the charging point, and tap Save to finish creating it.

- Note: The charging point can be given a custom name; this does not affect how the function is triggered.

8. Only one charging point can be created per map. To change the charging point location, delete the current charging point first and then create a new one.

### Enabling Autonomous Charging

1. Autonomous charging can be enabled on the Settings → Map page.

2. Two trigger methods are available: voice trigger and low-battery trigger.

- With voice trigger enabled, autonomous charging can be triggered by the voice command.

- For the low-battery trigger, you can choose a threshold of 20%, 30%, 40%, or 50%; autonomous charging is triggered when the battery level falls below the selected threshold.

![FF All-New Futurist Ultra — Autonomous Charging](/images/futurist-ultra/futurist-ultra-ultra-v32-57.png)

## Charging Operation

### Starting Autonomous Charging

> Preconditions for normal triggering: The robot is not executing any task other than Lively Standby; a charging point exists on the current map; the robot's localization is normal and the robot is in a movable state.

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Trigger Method | User Operation |
| --- | --- |
| Voice trigger | Say "[Wake Word], go charge" or "[Wake Word], go to the charging point" |
| Automatic low-battery trigger | Triggered automatically when the battery level falls below the configured threshold |

</div>

### Ending Autonomous Charging

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Exit Method | User Operation |
| --- | --- |
| Voice exit | Say "[Wake Word], end charging" or "[Wake Word], stop charging" |
| Manual exit from the client | Tap End Charging Task in the client |
| Full-battery exit | No operation needed; triggered automatically when the battery level exceeds 95% |

</div>

### Interrupting Autonomous Charging

> Condition for ending autonomous charging: Both batteries are correctly installed and the battery level is ≥ 15%. Otherwise, the robot cannot exit charging autonomously.

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Phase | Can Be Interrupted | How to Interrupt |
| --- | --- | --- |
| Navigation | Yes | Voice command; terminate the task in the client |
| Plugging in the gun | No | Not supported |
| Charging | Yes | Voice command; terminate the task in the client |
| Unplugging the gun | No | Not supported |

</div>

## Troubleshooting Quick Reference

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Symptom | Possible Cause | Solution |
| --- | --- | --- |
| Autonomous charging cannot be triggered | Trigger method not enabled; no charging point set (or wrong charging point name); localization abnormal; robot not movable; or another task in progress | Check the settings, map localization, and robot status; trigger again after other tasks finish |
| Cannot reach the charging point | Path blocked by people, objects, or temporary obstacles | Clear the path, exit the current task in the client, and trigger autonomous charging again |
| Charging gun not recognized | Charging gun in the wrong position, outside the dashed box, occluded, or abnormal lighting | Adjust the charging gun position; make sure it is unobstructed and lighting is normal |
| Plugging, unplugging, or holstering the gun fails | Charging gun position offset; QR code position offset; arm path blocked; cable under tension | Do not forcibly pull the arm or cables; wait until the robot's arms return to its sides, then manually help the robot plug in, unplug, or holster the gun |

</div>

## Precautions

> ⚠️ Precautions
> 1. Before triggering autonomous charging, make sure both batteries are correctly installed and the battery level is at least 5%. Otherwise, insufficient power may prevent the robot from completing the charging process or cause it to fall.
> 2. If the robot is in an abnormal state, emergency-stop state, or abnormal posture, restore the robot to a normal state before triggering autonomous charging.
> 3. Do not move the deployed charging table, charging gun, or charging base at will. If their positions change, check and update the charging point again.
> 4. During autonomous charging, do not cover the QR code on the table, as this affects recognition and plug/unplug success rate.
> 5. During autonomous charging, do not cover the robot's cameras, the charging gun, or the charging base, as this affects recognition and plug/unplug success rate.
> 6. Do not reach in while the robot is plugging in / unplugging the gun. If the operation fails, wait until the robot's arms return to its sides before attempting to recover.
> 7. If the robot fails to plug in the gun autonomously, manual assistance is required. After manually assisting the plug-in, the robot cannot exit this charging task autonomously.
> 8. After each charging task, make sure the charging gun is correctly returned to the base. If the robot fails to holster it, return it manually; otherwise the next autonomous charging task cannot start.
> 9. The entire autonomous charging process cannot be interrupted by other tasks. Do not launch other tasks while autonomous charging is running.
