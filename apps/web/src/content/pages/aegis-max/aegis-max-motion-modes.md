# Motion Modes

The robot comes standard with a reinforcement learning locomotion model, featuring Stationary Mode, Sport Mode, Navigation Mode and Stair Climbing Mode.

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Mode | Description |
| --- | --- |
| Stationary Mode | The robot remains stationary while its torso performs various actions including rotation, pitch and height adjustment. |
| Sport Mode | The robot automatically adapts to flat ground, slopes, stairs and complex terrain such as mountains, forests and rubble. It supports forward and backward movement and in-place rotation, and can perform standing, crawling, prone and locked postures, as well as advanced manoeuvres such as climbing elevated platforms and twisting motions. |
| Navigation Mode | Maps can be created in this mode. Once the map is generated, the fixed-point cruise function can be enabled based on the map to achieve automated inspection and fixed-point operations. |
| Stair Climbing Mode | The robot autonomously plans its gait to traverse multi-level staircases with stability, suitable for multi-storey operations. |

</div>

**Warning:**

- When performing high-platform climbing manoeuvres, ensure the robot has ≥ 2 battery bars and is unloaded, keep it in sight, and maintain a safety distance of ≥ 2 m from bystanders.

- When navigating stairs, slopes or similar surfaces, ensure no one is directly above, below or within the robot's path.

- In Sport Mode the robot has standard low, medium and high speed settings. To ensure safe task execution, lateral movement and in-place rotation are restricted at medium and high speeds.
