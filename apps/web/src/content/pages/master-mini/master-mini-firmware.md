# Firmware & Upgrades

> **Source limitations:** The terminal command for checking the firmware version is missing from the supplied manual. The troubleshooting command below uses `v1.1.1.0-release-aarch64.run` as the source’s example package name; use the package that matches your device. The source’s general upgrade guidance requires DAMP mode or stopped motion control with physical support; its App section also mentions ready mode. Confirm the applicable procedure before upgrading.

## Check Version

### Check via App

After connecting to the robot, tap "Settings - About" to view the robot's current version.

### Check via Terminal

The supplied manual refers to a terminal version-check command but does not include it. Use the App method above or request the command from technical support.

## Version Upgrade

### Before Upgrading

1. ❗ When installing a new version of software, the robot's motion control program will be stopped, and the robot's joints will not exert force. Before upgrading, ensure the robot is in damping mode or motion control is stopped and has good support (e.g., placing it flat on the ground or using a stand to support the robot). Do not cut off power or interrupt the process during the upgrade.

2. Make sure the installation package matches the current FF Master Mini model and the target version.

3. Make sure the robot's battery level, network, and terminal connection are stable.

4. If you have modified any configuration files, back up important configurations and logs first.

### Upgrade via App

In the robot settings, tap "Firmware Update".

Before installing the firmware, make sure the robot has entered damping or ready mode, and the battery level is above 50%.

### FAQ

#### Slow pip Downloads

The perception process depends on some Python libraries installed via pip. If downloads are slow, you can switch the pip download source and run the upgrade again.

```bash
sudo su
pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple
./v1.1.1.0-release-aarch64.run
```

#### apt update Fails

If the upgrade log indicates that apt update failed, you can use the fishros tool to switch sources and try the upgrade again.

```bash
# Recommended: use fishros and select in order:
# [5] One-click source change
# [1] Change system source only
# [1] Add ROS/ROS2 source
wget http://fishros.com/install -O fishros && . fishros
```
