# Safety & Warnings

Whenever the robot moves, stands up, or performs actions, there is a risk of falling, collision, or personal injury. The following items are the most common real-world risk points. Read them before operating the robot for the first time.

## Read Before Operation

- Before entering WALK mode, always enter PREP mode first and make sure the robot is standing securely on the ground.

- Do not lift the robot while it is moving.

- During motion, make sure there are no people or obstacles within the robot's operating range to avoid injury or collision.

- During motion, do not touch any part of the robot with your body except the handle.

## Venue and Actions

Large full-body actions such as full-body dances should be performed on hard surfaces such as rubber, cement, or tile. Carpet has high resistance and can increase the risk of falling. Keep people away from the robot throughout the action. For detailed venue and environment requirements, see "Overview".

## During Upgrade

When installing new software, the robot's motion-control program is stopped and the joints no longer output torque. Before upgrading, make sure the robot is well supported, for example lying flat on the ground, and then switch it to DAMP mode to prevent it from falling during the upgrade.

## Additional Notes for Secondary Development

After entering CUSTOM mode, all joints, including the legs, are controlled by your code, and the robot can easily lose balance and fall. Use a hoist to protect the robot throughout the process, and validate algorithms in Webots / Isaac simulation before running them on the physical robot. Be especially careful with changes involving biped control. CUSTOM mode can only be entered from PREP mode or DAMP mode, and can only switch back to those two modes. For the full mode description, see "Modes".
