# Fleet Task Orchestration

> ❗ Before starting control with Multi-Robot Control, ensure the robots are idle (not walking, performing actions, dancing, etc.).

If abnormal operation occurs, restart the software; data will not be lost.

## Roles

- Roles can be created using the [Add Role] button on the left side of the timeline. Each role generates one task track.

Role card functions:

1. Tap the [Selection Box] to adjust which robots are bound to this role, within the scope of the preceding robot list.

2. Press and hold the card to drag it and adjust the order of the roles up and down.

3. Tap the [Delete] icon to delete a role and all its associated content, without affecting the robot itself.

4. Tap the [Copy] icon to copy this role's tasks to other roles.

5. Tap the [Hide] icon (a special state) to temporarily hide a role; when a task is issued, this role will not participate in execution.

## Task Orchestration

Each role has its own timeline, and each role can run five types of task commands simultaneously:

1. Audio: Audio created in audio management; its duration is fixed to the audio length. Audio tasks can overlap, and the later overlapping audio task interrupts the playback of the previous one, but two audio tasks cannot be created to start at the same time.

2. Expression: A task from the robot's expression list; the expression plays in a loop until the next expression task starts.

3. Action: A task from the robot's action/dance list; the action duration is the action's fixed length. Tasks can overlap, and the later overlapping action task interrupts the playback of the previous one, but two action tasks cannot be created to start at the same time.

4. Movement: Properties such as walking speed, turning, and time of the task can be set.

5. Status: Currently supports Action switching, volume setting, and microphone on/off.

## Create / Edit Tasks

- Right-click a task to show the Edit, Copy, and Delete buttons:

- Edit: Tap to bring up the edit dialog to modify task information.

- Copy: Copies the task information.

- Delete: Deletes the task (after selecting the command, pressing the keyboard Delete key also deletes it).

- Right-click a blank area to show the Create and Paste buttons:

- Create: Tap to bring up the create dialog to quickly create task information.

- Paste: Tap to quickly create a task by pasting the copied task.

## Execute / Cancel Tasks

- Tap [Execute Task] in the top-right corner and confirm.

- The task delivery progress and execution countdown are shown; to cancel a task, tap the [End] button in the top-right corner before the execution countdown ends.

- Stage Preview.
