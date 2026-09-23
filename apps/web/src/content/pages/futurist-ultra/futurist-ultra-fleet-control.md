# Fleet Projects & Resources

## How to Obtain

Please contact after-sales personnel to obtain the "Fleet Control software package".

## Project Management

Each project is a separate engineering file. After creation, it can be shared among multiple people through export and import.

- Create New Project: Tap the Create New Project button to create a new project.

- Export: Tap the Export button in the top-right corner, select the file to export and name it, to generate a .gcs file.

- Import: Tap [Import Existing Project] and select a .gcs file to quickly open an exported project.

- View Project History: Displays previously edited projects; tap to open a project.

- Delete Project History.

Note: Due to the refactoring of the software interface, projects from historical versions (before v1.2) can no longer be opened.

## Robot Management

- Add Robot: Tap the [Add Robot] button and fill in the relevant information according to the input box prompts. Multiple robots can be added at once, in the format: "All-New Futurist @ Robot Nickname @ IP".

Robot status:

1. Robot nickname (the name given when adding the robot)

2. The robot's current Action

3. The task the robot is currently executing (this task is a multi-robot control task)

4. Robot status (latency with the current computer, manual/automatic state, emergency stop state, Wi-Fi signal, battery information, etc.)

5. The correction effect after time synchronization

6. The reconnect button, etc.

- Function Buttons: The checkbox at the front of the card has two states, selected or unselected; this box affects the scope of functions such as deletion, time synchronization, and resource synchronization. To quickly select only one robot and set all other robots to unselected, double-click that robot's card.

- Time Synchronization: Using this function calculates the time difference interval of the selected robots and caches this data.

Note: When you need to control multiple robots for synchronized operation, be sure to tap Time Synchronization in advance; it can be performed multiple times.

## Menu Bar

Tap the top-left corner to show the menu bar.

- "Execute After": Sets the preparation time before a task is executed (when the network condition is poor, a longer preparation time can be set to ensure that the robots execute commands simultaneously).

- "Close Project": Ends the current project and returns to the home page.

## Audio

Tap [Import Audio].

- Local Audio: Select and upload a file. The program will automatically convert it to a format supported by the robot. The name of the selected audio file is filled in by default during import and can be changed; when files have duplicate names, the new resource will overwrite the existing audio resource.

- Text-to-Speech (TTS): Enter text and call the TTS service (ensure network connectivity) to generate audio; the audio must be named manually.

- Tap [Sync Audio Resources to Robots] to sync all audio resources to the robots, with the robot scope being the robots selected previously.

Note: Synchronization is required each time after adding audio resources.
