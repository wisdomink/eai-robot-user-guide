# Quick Start Guide

*Before performing the following operations, first complete robot unboxing according to the unboxing document.*

## I. Power On

### Step 1: Open the AimMaster Client

Turn on the official FF-EAI Robotics controller. The controller power button is located at the top. Press and hold the power button until the white light next to the power indicator turns on. After the controller starts up, AimMaster opens automatically and enters the robot startup wizard. The controller charging port is located at the bottom of the remote.

![](/images/futurist/futurist-quick-start-guide-1.png)

On the robot type selection screen, choose "FF Futurist", then enter the FF Futurist startup wizard and follow the prompts step by step to complete power-on.

### Step 2: Hoist the Robot

Before powering on the robot, the robot must first be hoisted. Connect the robot to the hook at the top of the electric lift using the shoulder lifting ring and sling, then manually operate the electric lift until the robot is in the position shown and both feet are completely off the ground.

*Note: While moving or hoisting the robot, take care not to squeeze or strike the dexterous hands.*

![](/images/futurist/futurist-quick-start-guide-2.png)

After the robot is hoisted, click "Next" in the AimMaster interface.

### Step 3: Install the Battery and Power On

The battery is installed on the back of the robot. Confirm that the battery has sufficient charge, then slide it down from top to bottom into the battery slot on the robot's back. When the battery reaches the bottom, you will hear a "click," indicating that it is fully locked in place.

Press and hold the power button in the maintenance compartment at the rear side of the robot's waist to power on the robot. When power is connected, the LED inside the power button lights up.

Power button operation: press and hold to power on; to power off, short-press once and then immediately press and hold.

![](/images/futurist/futurist-quick-start-guide-3.png)

After startup is complete, click "Next" in AimMaster.

### Step 4: Wireless Emergency Stop

The emergency-stop remote is simple to use and is paired before shipment, so it works out of the box. In the default released state, the motors are powered normally. In an emergency, press the button to cut power to the motors. After the issue has been resolved, rotate the button to release it and re-energize the motors. A green indicator means normal operation; red indicates an abnormal state. When fully charged, the remote displays four battery indicator LEDs.

![](/images/futurist/futurist-quick-start-guide-4.png)

During the robot joint self-check, the neck will move slightly for self-inspection. After the joint self-check is complete, click "Next" in AimMaster.

### Step 5: Connect the Robot

After the emergency stop has been released, AimMaster shows the robot connection screen. Click the connection button to connect or manually enter the IP address to connect.

![](/images/futurist/futurist-quick-start-guide-5.png)

**Connection method and safety verification:**

* Recommended before first use: For safety, after using the remote for the first time, set a robot authorization password first to prevent unauthorized devices from connecting.
* Robot IP connection:
  * Click the prompt text at the bottom of the page to open the input box, then manually enter the robot IP address.
  * A password input box appears. Enter the correct password to connect.
  * If the password is incorrect, the system displays: "Connection exception, please re-enter password."
  * A password must be entered for each IP connection; the password is stored on the device.
  * The robot IP can be viewed under `[Settings] - [Wireless LAN]`.

![](/images/futurist/futurist-quick-start-guide-6.png)

* View / change password:
  * Go to `[Settings] - [Authorization Password]` to view or modify the password.
  * Enter a new password (at least 8 characters), then click "Confirm."

After the robot is successfully connected, AimMaster displays "Connection successful." Click "Next."

### Step 6: Switch to the Standing Preparation Pose

Before the robot stands up, first switch it to the standing preparation pose while it is still suspended. In the "Switch Standing Pose" screen in AimMaster, click the "Switch Pose" button. The robot automatically adjusts the positions of the head, arms, and legs to the preparation pose.

In the preparation pose, both arms are slightly bent, the wrists are parallel to the forearms, both legs are slightly bent, and the soles are approximately parallel to the floor.

*Note: The joints will move during the pose-switching process. Stay away from the robot and make sure there is sufficient space around it.*

After the standing preparation pose has been completed, click "Next."

### Step 7: Lower the Robot

Instructions for the electric lift: Place the electric lift behind the robot and ensure that the robot stands between the two legs of the lift. After confirming safety, press the lower button on the lift and observe the lowering process. Continue until both feet are fully in contact with the ground and the suspension sling is completely slack with a little extra slack.

![](/images/futurist/futurist-quick-start-guide-7.png)

After the lowering operation is complete, click "Next" in AimMaster.

### Step 8: Switch to Standing Mode

On the "Switch Standing Mode" screen in AimMaster, click the "Enable Standing Mode" button. The robot enters standing mode. When the message "Standing Successful!" appears, the standing process is complete. At this point, the shoulder sling may be removed, and the robot will maintain autonomous balanced standing.

![](/images/futurist/futurist-quick-start-guide-8.png)

*Note: Before switching to standing mode, make sure the robot has already been lowered to the ground and both feet are fully contacting the floor.*

Click "Finish" to exit the legged startup wizard; AimMaster will enter the workbench page.

## II. Power Off

### Step 1: Install the Lifting Ring

Raise the lifting arm of the standby frame until the robot's feet are completely off the ground.

### Step 2: Hoist the Robot

Install the lifting rings at the robot's shoulders and use the electric lift to hoist the robot until both feet are completely off the ground.

### Step 3: Power Off

Press the power button once inside the maintenance compartment at the rear side of the robot's waist to cut power and shut down the robot.

## III. Motion Control

### 3.1 Walking Preparation

Before using the remote to walk the FF Futurist robot, first ensure that the robot has completed the standing procedure (refer to the standing process in the power-on section). After the robot is standing, click the Toolbox panel on the left side of the AimMaster main screen to view the mode-switching function bar.

Double-click to switch to "Walking, Natural Arm Swing" mode. Following the flow shown in the interface, click to execute the relevant actions and the robot will begin stepping in place. Switch to "Motion" and the robot can perform interaction actions.

### 3.2 Remote Walking

Click the "Control" button on the software sidebar to enter the "Remote Walking" page.

### 3.3 Interactive Actions

Click "Interaction" in the sidebar to switch to the interaction page. Click "Action List" at the top of the screen to enter the action list page. Swipe up and down to view the preset robot actions stored on the robot. Click the play button in the upper-left corner of a card to play the selected action, and the robot will begin performing it.

Click "Custom Broadcast" at the top of the screen to enter the custom broadcast list page, which allows users to create new broadcast content. Swipe to browse the broadcast list; double-click an item to play it.

![](/images/futurist/futurist-quick-start-guide-9.png)
