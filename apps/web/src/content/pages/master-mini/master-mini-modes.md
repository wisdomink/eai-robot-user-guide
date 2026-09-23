# Operating Modes

> **Mode transition clarification:** The source broadly states that WALK can switch to any other mode, but explicitly restricts CUSTOM entry to PREP or DAMP. Follow the specific CUSTOM restrictions; a direct WALK-to-CUSTOM transition is not documented.

The robot has multiple mode

Different mode determines which action are available

Different mode can switch between one another, but with certain constraints. For example, DAMP mode cannot switch directly to WALK mode; it must first enter PREP mode

## State map

![FF Master Mini mode transitions](/images/master-mini/master-mini-mode-transitions.png)

## DAMP Mode (DAMP)

The robot is powered on and the main controller is running normally.

All joints enter a damped state. That is, when their positions are changed, there is resistance; the joints do not actively change position and do not try to hold position.

In DAMP mode, the robot cannot stand and needs effective support.

DAMP mode is a safe mode and is less likely to cause accidental injury.

DAMP mode can switch to PREP mode , but cannot switch directly to WALK mode

## PREP Mode (PREP)

The robot is powered on and the main controller is running normally.

The robot enters and maintains a standing posture. That is, the robot assumes and holds a standing pose. If you try to change a joint position at this time, there is very strong resistance , and after displacement the joint will actively recover to return to the standing posture.

In PREP mode, the robot can stand steadily and remain balanced on the ground. However, it cannot withstand large disturbances in this state because it only holds its posture and does not try to recover balance.

PREP mode can switch to any other mode, including DAMP Mode、WALK mode

## WALK Mode

The robot is powered on and the main controller is running normally.

The joints can execute corresponding preset action , including omnidirectional walking, turning, stepping, standing still, and head turning.

Compared with PREP mode, WALK mode has stronger disturbance resistance and actively tries to recover balance after external forces within a certain range.

WALK mode can switch to any other mode, including DAMP mode and PREP mode

Before entering this mode, make sure the robot is already in PREP mode and standing on flat ground.

## CUSTOM Mode

The robot is powered on and the main controller is running normally.

At this time, all robot joint control is fully handed over to user-defined joint commands, including both legs. Use caution in this mode to prevent the robot from losing balance and falling.

CUSTOM mode can only be entered from PREP mode or DAMP mode.

CUSTOM mode can only switch to DAMP mode or PREP mode.

💡During secondary development, especially in CUSTOM mode, it is recommended to use a hoist to protect the robot throughout the process.

## PROTECT Mode

The robot automatically enters PROTECT mode when runtime issues occur, such as exceeding limits or falling.

In PROTECT mode, the joint state is the same as DAMP Mode the same.

PROTECT mode is a safe mode and is less likely to cause accidental injury.
