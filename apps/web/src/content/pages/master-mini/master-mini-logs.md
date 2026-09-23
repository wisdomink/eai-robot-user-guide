# Log Retrieval

> **Terminal export command unavailable:** The source specifies the time format and an example time range, but does not include a log-export command. Use App log upload or request the command from technical support.

When FF Master Mini has issues, follow the steps on this page to retrieve logs and send them to technical support. Logs help locate when the issue occurred, the running state, and related error information.

## Privacy and Purpose

Our company will, without violating any applicable laws and regulations or involving any personal privacy information, collect only data related to the operation of the robots for the purposes of fault detection, problem localization, and statistical analysis.

## Upload Logs via App

1. After connecting to the robot via the App, go to "Settings".

2. Tap "Log Upload".

3. Select the time range to upload, making sure it covers the time when the issue occurred.

4. The upload takes about 5-10 minutes. During this process, keep the robot powered on and connected to the network. Both the App logs and the robot logs will be uploaded together.

5. After the upload is complete, contact customer service to report the issue. Our technical staff will retrieve your uploaded log files through the management console.

## Retrieve Logs via Terminal

Before you start, record the time the issue occurred, the symptoms, and the operation you were performing at the time as accurately as possible. The robot uses the UTC+8 time zone by default; if you are in a different time zone, convert the time before filling in the log time range.

1. Log in to the robot via terminal.

2. Confirm the time the issue occurred and prepare the start and end times for the logs. The time format is YYYYMMDD-HHMMSS.

3. Run the device-specific log export command supplied by technical support; the command is not included in this manual.

4. Select a range that covers the time before and after the issue. For example, if the issue occurred around 20200808-120810, you can export logs about 10 seconds before and after:

5. Send the log package to technical support, along with the symptoms, the time of occurrence, and the reproduction steps.
