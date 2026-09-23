# Voice Interaction

## Introduction

### Hi Chat Agent

For v1.3.1.1 and above, the Master Mini robot is equipped with AI realtime voice dialogue. This feature can be enabled or disabled via the “Hi Chat” Agent in the mobile app.

#### Usage Instructions

Open the “Hi Chat” entry in the mobile app, tap and select a persona. When you hear a voice prompt similar to “Hello, I am the Master Mini robot. How can I assist you?”, the realtime voice dialogue function is activated, and you can start talking to the robot.

Once realtime voice dialogue is enabled, the robot will automatically turn its head to face the nearest person in front of it.

AI voice interaction requires an internet connection.

#### Voice Commands

Note: When using a custom persona, conflicting system prompts may cause voice commands to fail.

Master Mini robots currently support voice commands that make the robot perform corresponding actions. The large model may also autonomously trigger the following actions based on the current conversation context. The action set includes:

<div class="overflow-x-auto" role="region" aria-label="Scrollable table" tabindex="0">

| Action Category | Command Name | Trigger Condition |
| --- | --- | --- |
| Basic Movement | Turn Left | Triggered when explicit commands such as "turn left" or "turn to the left" are received. |
| Basic Movement | Turn Right | Triggered when explicit commands such as "turn right" or "turn to the right" are received. |
| Basic Movement | Turn Left One Full Circle | Triggered when commands such as "turn left one full circle" or "turn counterclockwise one full circle" are received. |
| Basic Movement | Turn Right One Full Circle | Triggered when commands such as "turn right one full circle" or "turn clockwise one full circle" are received. |
| Basic Movement | Walk Forward | Triggered when commands such as "walk forward" or "go forward" are received. |
| Basic Movement | Walk Backward | Triggered when commands such as "walk backward" or "move back" are received. |
| Basic Movement | Move Left | Triggered when commands such as "move left" or "move to the left" are received. |
| Basic Movement | Move Right | Triggered when commands such as "move right" or "move to the right" are received. |
| Interaction Actions | Wave | Triggered when commands such as "wave" or "wave your hand" are received, or when expressing goodbye. |
| Interaction Actions | Handshake | Triggered when explicit social commands such as "shake hands" or "let's shake hands" are received. |
| Interaction Actions | Greet | Triggered only when the user explicitly greets the robot, such as "hello" or "Hi FF Master Mini"; the reply should include a greeting. |
| Interaction Actions | Nod | Triggered when the robot needs to express agreement or approval, such as responding to "the weather is nice today" or "did I do it right?"; the reply may use an affirmative tone. |
| Interaction Actions | Shake Head | Triggered when the user asks about unknown content, such as "what does this word mean?"; execute this action if the knowledge base has no answer. |

</div>
