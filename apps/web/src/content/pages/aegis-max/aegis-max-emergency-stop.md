# Emergency Stop & Protection

## Hard Emergency Stop

- Trigger: when the robot is out of control or malfunctioning, in either autonomous or remote-control mode, press the red hard emergency stop button on the robot's back. The hard emergency stop red light will be normally on, the robot will slowly lie down and remain motionless, and a real-time alert will appear in the app.

- Release: turn the hard emergency stop button clockwise to release it.

## Soft Emergency Stop

- Trigger: when the robot is out of control or malfunctioning, press the soft emergency stop button on the remote control. The robot will cease its current action and remain stationary in a standing posture, and a real-time alert will appear in the app.

- Release: once the robot and its surroundings are confirmed safe, release the soft emergency stop via the app, restoring both app and robot to normal status.

## Overheat Protection

The robot has comprehensive temperature detection. If a joint, the main control or the battery overheats, the robot enters overheat protection, ceasing all motion, going prone and remaining still. The overheat location and temperature can be viewed in the app. Once the temperature drops to normal, operation can continue.

## Low Battery Protection

When the charge level of both batteries falls below 20%, the robot enters a low battery warning state and should be charged immediately. Below 10%, low battery protection triggers: the robot goes prone automatically and no longer responds to remote control commands. Replace the batteries before continuing use.

## Fall Protection

The robot attempts to recover to a standing position after a fall, under the control of a reinforcement learning motion control model. Where the surrounding environment does not permit recovery, the robot maintains a fixed posture and raises an alarm.

## Expansion Bay Power Supply Protection

The expansion bay has a separate power button allowing independent control of its power state. When the machine is powered on as a whole and the mounted payload must be replaced, the expansion bay button can power off all interfaces in the bay without powering down the machine. The button is located inside the compartment to avoid accidental external contact powering down the upper assembly.
