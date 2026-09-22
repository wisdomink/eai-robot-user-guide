# Network Ports

The following ports are open on the device.

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

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

</div>
