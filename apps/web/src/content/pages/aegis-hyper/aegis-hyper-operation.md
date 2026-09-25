# Operation

![FX Aegis Hyper figure 12](/images/aegis-hyper/aegis-hyper-figure-12.png)

## 2.1 Preparation

### 2.1.1 Environment

- Please ensure that operators and non-operators present have

read the manual carefully and understand the basic operating

instructions and safety precautions.

- Before start FX Aegis Hyper, ensure that all people or objects

present are more than 2 meters away from the robot to avoid

collisions.

- Please use FX Aegis Hyper in an environment of -20℃~55℃.

### 2.1.2 Checking

- Check the battery indicator. It is suggested to use the robot when

the battery is at least 75%.

- Make sure that the emergency stop buttons stay off.

- Make sure there is no visible damage to the exterior of the robot.

- Make sure the joystick used for remote control is fully charged.

If the robot parts are aging or damaged, please do not start the robot

and contact the after-sales staff in time.

## 2.2 Charging

### 2.2.1 Charging the Robot

FX Aegis Hyper is powered by a ternary lithium battery.

You can connect the robot with 220V AC power supply through the charger, and the charging

port is located on the left side.

1. First make sure the robot is turned off. Open the charging port cover and connect the

charger to the charging port and tighten it (charger has an anti-reverse plug-in port), then

connect it to 220V AC power.

2. During charging, the charging indicator on the charger is red.

3. When charging is complete, the charging indicator on the charger turns green.

![FX Aegis Hyper battery replacement procedure](/images/aegis-hyper/aegis-hyper-figure-13.png)

### 2.2.2 Changing Battery

The battery of FX Aegis Hyper is replaceable, so users can take out the battery and replace

it with other batteries, and charge the removed battery separately.

1. Unscrew the two hand-screws, remove the cover plate, and unplug the connector:

Battery Handle

Remove

Charging Port

hand-screw

hand-screw

Battery Connector

2. Straighten the battery handle outward and take out the battery, then connect the charger

for charging:

Straighten the

Remove the battery

handle

and charge it

3. When charging normally, the charging indicator light on the charger is red; when

charging is complete, the charging light on the charger turns green.

- It is recommended to charge in an environment of 0 ℃ to 45℃.

- During charging, please do not power on the robot and always

pay attention to the state of the charger during charging to avoid

accidents. Disconnect the charging power supply in time after

charging.

- When the robot is not charging, the charging port cover must be

closed to prevent water.

![FX Aegis Hyper startup posture](/images/aegis-hyper/aegis-hyper-figure-14.png)

## 2.3 Start

### 2.3.1 Preparation

1. Take the robot from the transport case and place it on a flat surface, as described in the

section "Transport and Storage".

2. Adjust the robot pose as required (as shown in the picture above): knee joints retracted,

hip front swing joints swung back, side swing joints vertical, and the bottom of the body

touching the ground.

### 2.3.2 Power on

Press the power button to turn on the robot. At this time, the power button is always on. At

the same time, it is necessary to ensure that the light of soft emergency stop is off and the

light of hard emergency stop is on. If not, press the hard emergency stop button or rotate

the soft emergency stop button in the direction indicated by the arrow to turn it off. If the

hard emergency stop is triggered, it is necessary to restart the robot after turning off the

hard emergency stop.

### 2.3.3 Connection

Long press the power button to turn on the controller (please ensure that the controller is

fully charged). The robot and controller have been paired and bound. After opening the app,

the controller will automatically connect to the robot it is bound to.

![FX Aegis Hyper remote controller controls](/images/aegis-hyper/aegis-hyper-figure-15.png)

## 2.4 Motion Control

### 2.4.1 Controller Operation

12 13 14

![FX Aegis Hyper figure 16](/images/aegis-hyper/aegis-hyper-figure-16.png)

Flip to the center simultaneously

Cancel Soft Emergency Stop

Button

①Controller Power

Press and hold to power on/off, and press once to wake

Flip up simultaneously

Trigger Soft Emergency Stop

②SW1

③SW4

④Start/Stop Moving

Start or stop moving, that is, to start or stop stepping

Stand up or sit down

⑤A

Switch to Torque Control Mode to unlock each joint

⑥B

Switch to Walk gait

⑦C

Switch to Run gait

⑧D

Switch to Slope gait

⑨E

Switch to Off-Road gait

⑩F

View APP version/Set language/Jueying Lab/User Protocal/Save

⑪Settings

data

⑫Buttons Introduction Show the introduction to physical buttons

⑬Screenshot

Save images for the video streaming

⑭Record

Record a video of the video streaming

Displays the connection status：

connected

/connecting

/

⑮Robot Signal

disconnected

⑯Robot Battery

Real-time display of robot signal strength

⑰Controller Battery

Real-time display of the controller's remaining battery

Soft emergency stop:Forcing the robot to lie down, which is

⑱STOP

generally used when the robot dog is out of control or in an

emergency

Select the elevation map mode, from top to bottom: Solid

⑲Elevation Map Mode

Ground/Grid Ground/Stair without Risers/Multi-Frame

Select body height: Normal/Crawling,and the button displays the

⑳Body height

current status

㉑Stand/Sit

Stand up or sit down and the button displays the current status

㉒Torque Control

Switch to Torque Control Mode to unlock each joint

㉓Control Mode

Select the control mode:Manual Mode/Asist Mode/Nav Mode

![FX Aegis Hyper figure 17](/images/aegis-hyper/aegis-hyper-figure-17.png)

Button

To enable the robot dog to perform autonomous charging, please

㉔Auto Charging

refer to the autonomous charging manual for specific use

Show the real-time video

Flip to the center

from the robot

㉕SW2

Close the real-time video

Flip up or down

from the robot

㉖Gait

Select gait, which can be switched only in the stepping status

㉗Start/Stop Moving

Start or stop moving, that is, to start or stop stepping

㉘2D obstacle point

Open the Jueying Lab to show a top-down 2D obstacle point

clouds

cloud

- After connecting the robot, ⑮will display as connected, at which point you can start

controlling the robot.

- After standing up, each joint of the robot is in a protective locking state, and in this state,

it can switch between lying down and standing by ⑤ or ㉑, or switch to force control

mode by ⑥or ㉒, and the locking state of each joint can be lifted, so that it can move in

steps.

- To make the robot walk, first make the robot stand up, then press ⑥or ㉒ to switch to

torque control mode, and then press ④or ㉗ to make the robot start moving, and the

robot will start stepping. At this time, the left joystick can control the robot to move

forward, backward, left and right, the robot will adjust the movement speed according to

the amplitude of the joystick, and after releasing the joystick, the robot will slow down to

zero and step in place; The right joystick controls the robot to turn left and right. Press

④or ㉗ again to end walking, and if the robot is walking forward, it will take a certain

amount of time to slow down and stop.

- Soft emergency stop on Controller: Triggered by flip ② and ③up simultaneously or

clicking ⑱.

- Through ⑲, the stair gait can be assisted to carry out foothold planning in manual

mode, and the correct elevation map mode needs to be selected according to the type of

staircase ground when used; In the assist mode, it can assist the user to avoid obstacles,

and it is necessary to select the correct elevation map mode according to the ground in

the actual environment to make the obstacle avoidance function work normally.

- Multi-frame mode can only be enabled when the robot is standing still.

![FX Aegis Hyper controller settings](/images/aegis-hyper/aegis-hyper-figure-18.png)

### 2.4.2 Settings

Button

㉙APP Version

View the current APP version

㉚Language

Select language: 中文 /English

㉜User Agreement

Click "View" to view the user agreement

㉝SAVE DATA

Save the data of robot operation

When the robot is abnormal, you can use the ㉝SAVE DATA to record the abnormal data

for troubleshooting. Please ensure that the robot dog is in the state of getting down or

emergency stop before using it.

![FX Aegis Hyper figure 19](/images/aegis-hyper/aegis-hyper-figure-19.png)

## 2.5 Emergency Operation

### 2.5.1 Soft Emergency Stop

If the robot's legs swing or shake violently and other abnormal phenomena occur during

use, please start the soft emergency stop function on Controller (flip ②and ③up at the

same time or click the button ⑱) or push the soft emergency stop button at the tail of

the robot to make the robot lie down and enter the self-locking protection state. If the

soft emergency stop is triggered by ②and ③ , please flip them back to release the soft

emergency stop. If the rear soft emergency stop button is pressed, you need to rotate

the button in the direction of the arrow on the button to release it. After releasing the

soft emergency stop, please release the force in time (press ⑤or ㉑) to release the self-

locking protection. After troubleshooting, press the stand button again to operate the robot

normally.

### 2.5.2 Hard Emergency Stop

Hard emergency stop, that is, hardware emergency shutdown, press the hard emergency

stop button at the tail of the robot, and the indicator light is off to indicate that the hard

emergency stop has been triggered, which can ensure that the robot joints are locked in

the boot state and avoid the robot from getting out of control. At this time, press the hard

emergency stop button again, and the indicator light will be on to indicate that the hard

emergency stop has been lifted, and the robot needs to be restarted to restore the normal

use state after the hard emergency stop is lifted.

Once the hard emergency stop is triggered, it will cause the robot to lose

all kinetic energy and thus fall to the ground. There is a risk of damaging

the ground or the robot, so it is strictly forbidden to press the hard stop

emergency button during normal movement!

### 2.5.3 Overtemperature

The system comes with temperature sensing. Once the robot runs for a long time causing

the motor or drive to overheat, it will automatically start the overtemperature protection

and the robot will automatically stop moving and get down in place.

![FX Aegis Hyper figure 20](/images/aegis-hyper/aegis-hyper-figure-20.png)

### 2.5.4 Falling Down

If the robot falls down suddenly, the joints will be automatically locked. Please try to click

[Stand] button in the app after making sure there is no obstacle around. If the robot still

can't get up, press the emergency stop button at the rear of robot, then click [Save Data] at

the Settings page of the APP and power off the robot.

### 2.5.5 Low Battery

When the robot's battery is below 10%, it will enter a low battery warning state, and it

should be charged immediately. When the battery level drops below 3%, the robot will

trigger a low battery protection mode, where it will automatically lie down and will no

longer respond to commands from the remote controller.

### 2.5.6 Other Circumstances

- If the joints are not locked or are still swinging after the robot falls down suddenly, wait

30 seconds after the robot joints have completely stopped moving before pressing the

hard emergency stop button at the rear of the body.

- In case of a fire, do not use water to extinguish it. Please use foam fire extinguisher, dry

powder fire extinguisher or carbon dioxide fire extinguisher nearby.

- If the soft emergency stop button fails or smoke from or water in robot or other

unexpected situations, please immediately power off the robot and wait until it's

safe to identify the problem. Then please contact FF EAI Robotics, and we will help to

troubleshoot the problem and repair or change your robot. Pay attention to safety in use!

- If the robot falls, do not drag, push or flip it before triggering the hard emergency stop.

## 2.6 Power Off

Make sure that the robot is sitting before the following operations.

Press the power button to power off the robot.

After powering off, please cover the robot with the antistatic cloth to

avoid dust contamination of laser radar and other devices.

![FX Aegis Hyper figure 21](/images/aegis-hyper/aegis-hyper-figure-21.png)

## 2.7 Payload and Development

Users can attach payloads to the back of the robot or develop new functions based

on software interfaces. To learn more about payload development, usage of software

interfaces and packages, refer to Application Manual and API Documentation.

- After attaching payloads to the back of the robot, please modify

the parameters of payload. To learn more about how to modify the

parameters, refer to the chapter "2.2 Paramters Configuration" in

Application Manual, or contact after-sales staff.

- The maximum power supplied by the robot to the payload is 600W.

For details about the maximum power provided by each power port,

read the chapter "5.2 Hardware interface and wiring definition" in

Application Manual.

- Please cover the aviation plug with its cover.
