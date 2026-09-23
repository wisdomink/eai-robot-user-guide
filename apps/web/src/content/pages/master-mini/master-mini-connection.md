# App & Terminal Connection

> **Terminal details:** The supplied manual does not include the SSH command, username or login credentials. Obtain the device-specific login details from technical support. The address below is listed under wired network configuration; it is not explicitly identified as the robot’s SSH address.

## Connect via App

1. Download and install App

2. After signing up and signing in, tap "Connect Robot" on the home page.

3. A list of robots on the same network as your phone appears below. If the robot you want to connect is not listed, tap "Discover Devices".

4. In the "Discover Nearby Robots" list, select your robot.

Bluetooth and Location must be enabled, and the app must be granted the required permissions.

Two connection modes are available:

Wi-Fi connection mode: connect the robot to the same Wi-Fi network as your phone, or connect the robot to your phone hotspot. This mode is suitable when network conditions are good.

Direct connection mode: connect your phone to the robot hotspot. This mode is suitable when no network is available and your phone is close to the robot.

![FF Master Mini app connection](/images/master-mini/master-mini-app-connection.jpg)

If you choose Wi-Fi connection mode, select the same network as your phone, or your phone hotspot, from the Wi-Fi list. Enter the password and confirm the connection. If the connection succeeds, the robot control page opens automatically.

If you choose direct connection mode, the robot control page opens automatically after loading.

## Connect via Terminal

### Wired Connection

After connecting to the robot with an Ethernet cable, configure the wired network settings.

address: 192.168.10.10

netmask: 255.255.255.0

gateway: 192.168.10.1

Use an Ethernet cable to connect the development computer and the robot. The robot's Ethernet port is shown in the figure.

![FF Master Mini ethernet port](/images/master-mini/master-mini-ethernet-port.png)

Log in to the robot with SSH.

### Wireless Connection

After connecting to the robot through the app and configuring Wi-Fi for the robot, you can see the robot's IP address.xxx.xxx.xxx.xxx

Log in to the robot with SSH.
