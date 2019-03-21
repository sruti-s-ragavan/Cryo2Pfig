Cryolite
========

**C**loud9 **R**ecorder of **Y**our **O**perations by **L**istening to **I**nteractions in **T**he **E**ditor

**Version:** 0.4.0-beta3-dev

## Contact

<pre>
Andrew Faulring, faulring@cs.cmu.edu
Brad Myers, bam@cs.cmu.edu
Human-Computer Interaction Institute
School of Computer Science
Carnegie Mellon University
</pre>

## License

Copyright 2013–2015 Carnegie Mellon University

This file is part of Cryolite.

Cryolite is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Cryolite is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Cryolite. If not, see <http://www.gnu.org/licenses/>.

## Overview

Cryolite, a [Cloud9 IDE (version 3)](https://c9.io/) plugin, logs user actions.

Cryolite logs the following user actions:

* Opening, closing, and moving of documents, tabs, and panes (“tab groups”)
* Editing and scrolling in code editors
* Invoking commands via menus or keyboard shortcuts
* Interaction with the Workspace tree (“Project Explorer”)
* Most cut, copy, and paste actions: see [Cut, Copy, and Paste and the Native Clipboard](#clipboard).

Cryolite does not log all user actions, such as:

* Commands that do not use the central command manager, such as theme switching
* Most dialog boxes, including Find/Replace and Find in Files
* Interactions in the Navigate, Commands, Outline, and Debugger panels

Since Cryolite does not log the above information, the log files are not re-playable.

## Requirements

### Cloud9 IDE and SDK

Cryolite requires Cloud9 IDE version 3.0.941 (released 2015-02-21) or later. We recommend using the latest available Cloud9 IDE release.

The Cloud9 SDK’s README.md includes instructions for downloading, installing, and running the Cloud9 SDK. Unix-based operating systems, including Ubuntu, are recommended. Windows and MacOS X are not officially supported. Verify that the Cloud9 SDK works before installing Cryolite.

### Browser Support

The Cloud9 IDE runs in recent versions of Google Chrome, Mozilla Firefox, and Apple Safari. We recommend using the most recent version of each web browser. Microsoft Internet Explorer is not supported. Cryolite was primarily developed and tested using Google Chrome on both Ubuntu and Microsoft Windows. Cryolite has also been minimally tested using Mozilla Firefox and Apple Safari.

## Installation

Cryolite runs in “[Debug Mode](https://cloud9-sdk.readme.io/docs/package-development-workflow#section-cloud9-debug-mode)” on both the [c9.io](https://c9.io/) servers and a Cloud9 SDK server.

To install, create the `~/.c9/plugins/cryolite/` directory. Copy the `package.json` and `cryolite.js` files into that directory. When you run the Cloud9 IDE in Debug Mode, Cryolite will load and start logging events.

To verify that Cryolite is running: “Open Preferences” (`Ctrl-,`), select “PLUGIN MANAGER”, and check that “cryolite” is listed under “Installed Plugins”. Also check that Cryolite has written events to a log file located in the `<workspace>/.cryolite/` directory (see [Log Files](#log-files)).

Cryolite also runs in normal mode on a Cloud9 SDK server. Open a command prompt in the `~/.c9/plugins/cryolite/` directory that you created earlier. Copy the `README.md` file into that directory. Run the `c9 build` command, which creates `__installed__.js`. Ignore the error message about the missing tests. Check that the `__installed__.js` was created. Now (re)start the Cloud9 IDE in normal mode; you do not need to restart Cloud9 SDK server. Verify that Cryolite is running by using the same checks described in the previous paragraph.

Cryolite has not yet been published on the Cloud9 website, so it will not run in normal mode on the c9.io servers.

## Network Issues

The Cloud9 IDE uses a client-server architecture. The client provides the user interface for code editors, a project explorer, a Unix-style terminal, and other development tools. The client runs in a web browser using HTML, CSS, and JavaScript. The server hosts a file system containing the project workspace and provides a Unix shell.

Cryolite runs as a plugin to the client (in the web browser) and uses the Cloud9 IDE APIs to write events to a log file stored on the server. Cryolite has been written to handle common network issues.

Cryolite buffers events to reduce network traffic, which is particularly useful when a single user action generates multiple small events. Once per second Cryolite writes the buffered event(s) to the server via a single file system API call. The buffering and network latencies cause a small delay between when an event occurs and when that event is appended to the log file on the server.

When network errors occur, Cryolite re-sends the events to the server until successful.

While the network is disconnected, Cryolite will continue logging user actions and buffering the events. After a network connection is re-established, Cryolite will write all the events from the buffer to the log file on the server. If the browser window containing the Cloud9 IDE is closed while the network is disconnected, any events not yet written to the server log will be lost.

When the user closes the Cloud9 IDE window, Cryolite immediately attempts to write all remaining events to the server. When closing a window, web browsers deallocate resources for the window including network connections. Hence, the network connection may close before Cryolite can write all remaining events to the log file. We recommend waiting several seconds after the last user action before closing the Cloud9 IDE window to avoid losing any events.

Cryolite writes two events, `c9-ide-closing` and `stop-logging`, when the user reloads or closes the Cloud9 IDE window. Our experience is that when the client and server are running on the same machine these events are usually written to the log, and when the client and server are on separate machines these events are usually not written to the log.

## <a id="log-files"></a>Log Files

Cryolite writes events to a log file in the `<workspace>/.cryolite/` directory.

The log file name format is `cryolite-YYYY-MM-DD.log`. Cryolite sets `YYYY-MM-DD` to the date, in UTC, when Cryolite was loaded. When Cryolite is left running past UTC midnight, it will continue writing to the previous day’s log file until Cryolite reloads.

Cryolite only appends to the log file. Cryolite never deletes or overwrites any part of the log file. If the user reloads the Cloud9 IDE, Cryolite will continue writing to the same log file unless the reload happens after midnight UTC as discussed above.

Cryolite encodes the log files in UTF-8 without a BOM (byte order mark). Cryolite formats events in JSON with one event per line.

## Log Format

Cryolite creates one JavaScript object for each event and then serializes that object to the JSON format. Each event contains a set of properties. Each property has a value with one of the following types: Boolean, number, string, object, or array. Note that JSON encodes JavaScript Date objects as a string in ISO format: see [Date.prototype.toISOString()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toISOString).

Common properties of all events:

* `event-type`: See [Event Types](#event-types).
* `sequence-id`: Cryolite assigns each event a numeric id in the _order in which the event is logged_. Events are not necessarily logged in the order in which the user actions occurred. Do not use the `sequence-id` to order events by user action. See [Timestamps](#timestamps). The `sequence-id` starts at 1 and increments by 1 for each event. Each time Cryolite is loaded, including when reloaded, the initial sequence id is reset to 1.
* `logged-timestamp`: The time at which the event was logged. See [Timestamps](#timestamps).

Most events also include the following property:

* `action-timestamp` or `action-timestamps`: The time(s) at which the user action that triggered this event happened. See [Timestamps](#timestamps).

Events also include event-specific properties.

### <a id="timestamps"></a>Timestamps

Cryolite cannot log some events immediately after the user action that triggered them. Many user actions initiate update and rendering processes in the Cloud9 IDE user interface. Cryolite must wait for these processes to complete before logging the event; otherwise the logs might contain incorrect data. The wait varies from a few milliseconds to 100s of milliseconds or even longer. Most events have two timestamps to account for the delay between when the user action occurs and when the event is logged.

The `action-timestamp` or `action-timestamps` property records the time when the user action happened. User actions include a key press, a mouse click, a mouse movement, and so forth. For most events, the `action-timestamp` property’s value is a single timestamp.

In a few cases multiple user actions, for example continuous scrolling, only generate a single event. This behavior is necessary because the Cloud9 IDE rendering process never finishes between each individual scroll action. There is very little valid information that Cryolite can log for each scrolling event. Instead, Cryolite coalesces the individual user actions into a single event. That event contains an `action-timestamps` property (note the plural `timestamps`) with its value being an array of timestamps, one for each user action. Cryolite coalesces the timestamps for the `change-scroll-position` and `resize-tab` events.

The `logged-timestamp` property records when an event was logged. An event cannot be logged (and `logged-timestamp` set) until after the update and rendering process completes. Cryolite uses a combination of event listeners and timeouts to wait for the update and rendering processes to complete. Cryolite uses a conservative timeout value and hence waits longer than is minimally necessary.

Events in the log files are ordered by increasing values of both the `sequence-id` and `logged-timestamp` properties. Events are _not_ ordered by the `action-timestamp(s)` property; the log file can contain `event1` before `event2` even though `event2`’s `action-timestamp(s)` property value is earlier than `event1`’s.

Several events, in general those not triggered by a user action, do not contain an `action-timestamp(s)` property. These events are: `start-logging`, `stop-logging`, `load-panels`, `load-tabs`, `load-documents`, `load-workspace-tree`, `c9-ide-ready`, `c9-ide-closing`, `post-execute-command`, and `update-settings`.

## <a id="event-types"></a>Event Types

### Startup Events

* `start-logging`
* `c9-ide-ready`
* `load-panels`
* `load-documents`
* `load-tabs`
* `load-workspace-tree:` If the Workspace tree (Project Explorer) is not initially open, this event is not logged at startup. When the user opens the Workspace tree, this event is logged.

### Shutdown Events

* `c9-ide-closing`
* `stop-logging`

### Tab and Pane Events

* `create-tab`
* `close-tab`
* `activate-tab`
* `deactivate-tab`
* `blur-tab`
* `focus-tab`
* `reorder-tab`
* `reparent-tab`
* `reload-tab`
* `resize-tab`
* `create-pane`
* `destroy-pane`

### Document Events

* `open-document`
* `save-document`
* `close-document`
* `change-document`
* `change-cursor`
* `change-selection`
* `change-scroll-position`
* `change-fold`: Logged when the user adds or removes a fold.
  + The `fold` property describes the newly added or removed fold. The `folds` property lists all the folds in the document. A fold can contain other folds, which are called `children` folds. The coordinates of a child fold are absolute document coordinates, not parent-fold relative coordinates.
  + When the user creates a new fold that contains an existing fold, the log contains a less than ideal event sequence of two `change-fold` events.
    - The first event records the removal of the existing fold, which will become a child fold. The `document-view` property of the first event will be invalid (see discussion in the [document-view property](#document-view) section). Since the second event will contain a valid `document-view` property, this should not be a problem in practice.
    - The second event records the addition of the new parent fold. The log does _not_ contain an event recording the addition of the child fold because the Cloud9 IDE does not report its creation to Cryolite. The second event will list the new child fold in the `children` property of the newly created fold.
* `change-wrap-limit`
* `change-wrap-mode`

### Clipboard Events

* `cut-clipboard`
* `copy-clipboard`
* `paste-clipboard`

### Panel Events

* `hide-panel`
* `show-panel`

### Console Events

* `resize-console`

### Workspace Tree Events

* `select-workspace-tree-nodes`
* `rename-workspace-tree-node`
* `delete-workspace-tree-nodes`
* `expand-workspace-tree-node`
* `collapse-workspace-tree-node`
* `open-workspace-tree-context-menu`
* `close-workspace-tree-context-menu`
* `scroll-workspace-tree`
* `refresh-workspace-tree`
* `update-workspace-tree`
* `resize-workspace-tree`

### Command Events

* `post-execute-command`
* `pre-execute-command`

### Settings Events

* `update-settings`

### <a id="document-view"></a>document-view Property

Several events contain the `document-view` property, which describes the state of a document’s view including `folds`, `editor`, `viewport`, and `visible-text`.

In a few cases, a single user action can generate multiple events, such as for the `change-fold` event. Some of the `document-view` state is only valid after the update and rendering process completes (see discussion in the [Timestamps](#timestamps) section). Cryolite must wait for the update and rendering process to complete before logging any of the events. Hence, Cryolite cannot log the `document-view` property as it existed for earlier events. In such cases, Cryolite adds an `invalid: true` property to the `document-view` property for the earlier events but still logs the complete `document-view` property since it may contain some valid data.

## Multiple Event Sequences

A single user action can generate multiple events. The following examples list a user action and the logged multiple event sequences. These examples are illustrative of multiple event sequences but are not a complete list; many other user actions generate similar multiple event sequences.

### Pasting Text

The user types the `Ctrl-P` keyboard shortcut to paste text from the clipboard to the cursor position of the focused document. Cryolite logs three events:

* `paste-clipboard`
* `change-document`
* `change-cursor`

The third event records that the cursor position moved to the end of the pasted text.

### <a id="command"></a>Command

The user types the `Ctrl-/` keyboard shortcut to execute the “Toggle Comment” command. Cryolite logs three events:

* `pre-execute-command`
* `change-document`
* `post-execute-command`

The first and last events wrap the event(s) generated by the command’s execution. The second event records the addition or removal of comment characters in the document’s text. Additionally, the `command-name` property of `*-execute-command` events will be `togglecomment`.

### Open Document

The user double clicks on a file (document) in the Workspace tree to open that file in a newly created tab.

If the to-be-opened file is not already selected in the Workspace tree, then Cryolite logs a `select-workspace-tree-nodes` event.

In either case, Cryolite logs four events:

* `focus-tab`
* `create-tab`
* `open-document`
* `activate-tab`

The Cloud9 IDE emits the `focus-tab` event before the `create-tab` event. This illogical ordering is due to flaws in the Cloud9 IDE tab management code. We considered implementing an event reordering feature in Cryolite but decided that reordering in Cryolite was risker than doing so in log analysis tools.

Each pane (tab group) contains zero or more tabs, only one of which is visible at a time. That visible tab is called the *active* tab. When multiple panes are open then multiple *active* tabs can exist concurrently (at most one per pane). In the above event sequence, the `activate-tab` event records that the new tab is now the *active* tab within its pane.

Amongst all the open tabs in all the panes, only one can be the *focused* tab, which receives keyboard input. In the above event sequence, the `focus-tab` event records that the new tab is now the *focused* tab.

### Resizing Tab

The user resizes a tab, which has wrapping enabled. Cryolite logs up to three events:

* `change-scroll-position`
* `change-wrap-limit`
* `resize-tab`

Horizontally resizing a tab that contains a wrapped file can cause the scroll position to shift as the text is reflowed to fit into the new width. When the scroll position shifts, Cryolite logs a `change-scroll-position` event.

The `change-wrap-limit` event records the new horizontal wrap limit for the resized tab. Not all tab resizing actions change the wrap limit. For example, changing a tab’s height does not change the wrap limit. Changing the width less than the width of a single character will not necessarily change the wrap limit either.

The `resize-tab` event records the new dimensions for the resized tab.

## Cursor and Selection

The cursor and selection are separate, although inherently related states. Cryolite records changes to the cursor and selection with the `change-cursor` and `change-selection` events. A single user action can generate either or both events.

The Cloud9 IDE text editor includes a multiple cursor and selection feature (see the [Cloud9 IDE documentation on multiple cursors](https://docs.c9.io/v1.0/docs/multiple-cursors)). The first three subsections explain how Cryolite logs the cursor and selection when in the “single-cursor-selection” mode. The final subsection, [Multiple Cursors and Selections](#multiple-cursors-and-selections), describes how Cryolite logs the cursor and selection when in the “multi-cursor-selection” mode.

### <a id="coordinates"></a>Coordinates

Cryolite records cursor and selection coordinates using an object with `line` and `column` properties. The values for both properties are 1-based, as is typically displayed by a text editor including the Cloud9 IDE. Since the cursor is positioned between to character columns, the `column` property value represents the column to the immediate _right_ of the cursor. For example, when the cursor is at the start of a line, the `column` property value will be 1. A cursor positioned after the fourth character on the second line is represented as:

    {
        "line": 2,
        "column": 5
    }

### Cursor

Cryolite records cursor movement with the `change-cursor` event.

Various user actions move the cursor, including arrow keys, mouse clicks, and text editing. Note that a single text-editing user action may generate both a `change-document` and `change-cursor` event. The Cloud9 IDE executes some user actions using commands: pressing the arrow or backspace keys, selecting navigation commands from the “Goto” menu, and so forth. As mentioned elsewhere, [commands generate multiple event sequences](#command). For example, pressing the “Up” arrow key generates the following three event sequence:

* `pre-execute-command ... command-name: golineup ...`
* `change-cursor`
* `post-execute-command ... command-name: golineup ...`

The `cursor` property of `change-cursor` event records the cursor’s coordinates. In “single-cursor-selection” mode, the value of the `cursor` property is a single object with `line` and `column` properties (see [Coordinates](#coordinates)).

### Selection

Cryolite records selection changes with the `change-selection` event. The `selection` property represents the selection as described next.

An empty selection is represented with the `null` value in _both_ “single-cursor-selection” and “multi-cursor-selection” modes. An empty selection does not move; moving the cursor with an empty selection will not generate any `change-selection` events since the selection remains `null`.

In “single-cursor-selection” mode, a non-empty selection is represented by an object with three properties: `start`, `end`, and `isBackwards`. The value for the `start` and `end` properties is a single object with `line` and `column` properties (see [Coordinates](#coordinates)). The `start` coordinate is _always before_ the `end` coordinate. The cursor is positioned at either the start or end of the selection. When the cursor is positioned at the start of the selection, then the `isBackwards` property is `true`. Otherwise when the cursor is positioned at the end of the selection, then the `isBackwards` property is `false`.

As with cursor movement, various user actions change the selection. A single user action can generate both a `change-cursor` and `change-selection` event.

If a non-empty selection exists and a user action removes that selection, Cryolite records a `change-selection` event with the `selection` property having a `null` value.

As an example, if the user selects a range of text in the first line by dragging the mouse from left to right, the new selection in the `change-selection` event might be represented as:

    "selection": {
        "start": {
            "line": 1,
            "column": 29
        },
        "end": {
            "line": 1,
            "column": 40
        },
        "isBackwards": false
    }

### <a name="multiple-cursors-and-selections"></a>Multiple Cursors and Selections

The Cloud9 IDE text editor includes a multiple cursor and selection feature (see the [Cloud9 IDE documentation on multiple cursors](https://docs.c9.io/v1.0/docs/multiple-cursors)). This feature allows the user to simultaneously edit multiple text positions. The user activates the “multi-cursor-selection” mode by selecting commands from the “Edit > Selection > Multiple Selections” submenu or by pressing their keyboard shortcuts.

TODO: incomplete

## Preferences and Settings

Cryolite supports the following preferences, which can be set using the Cloud9 IDE preference editor. Open the preference editor using the `Ctrl-,` keyboard shortcut, open the “Settings” section, and scroll down to the “Cryolite” section.

* “Generate Second Log in Pretty Print Format”: When enabled Cryolite writes a second log file with the file name format `cryolite-YYYY-MM-DD-pretty-print.log`. Cryolite writes events to this file in an expanded “pretty print” JSON format to enhance readability. In this format one event can span multiple lines. Default is disabled.
* “Event Types to Ignore”: A comma-separated list of event types that should not be written to the log file. Default is an empty string.
* “Code Summary Logging”: **This feature is currently disabled.** Cryolite can analyze JavaScript files to report abstract syntax tree (AST) complexity and line counts by type, such as comments or code. The code summary analysis takes approximately 100ms for a moderate-sized file (for example, 80KB and 2K lines), which can slow down the editor. Since the code summary analysis may not be needed, this preference controls when the analysis is performed and logged (`code-summary` property). The preference can have one of the following values:
  + “Never”: The code summary analysis is not performed. This is the default value.
  + “Open, Save, and Close Document”: The code summary analysis is performed at startup (the `load-documents` event) and when a document is opened, saved, and closed (the `open-document`, `save-document`, and `close-document`,  events).
  + “Open, Save, Close, and Change Document”: The code summary analysis is performed for `change-document` events, along with the events enabled by the “Open, Save, and Close Document” setting.

Cryolite’s preferences are stored in `~/.c9/user.settings` (when running the Cloud9 SDK) or in the user database (when hosted by Cloud9), along with the other Cloud9 IDE "Settings" section preferences. These preferences are shared across all of the user’s workspaces.

## <a id="clipboard"></a>Cut, Copy, and Paste and the Native Clipboard

Cryolite logs Cut, Copy, and Paste commands when invoked on the text editor (ACE) via keyboard shortcuts, `Ctrl-X`, `Ctrl-C`, or `Ctrl-P`, respectively. When these commands cause document, cursor, and selection changes, Cryolite will also log those events: `change-document`, `change-cursor`, and `change-selection`. Due to implementation constraints, the ordering of events is as follows:

* Cut: The `cut-clipboard` event follows the `change-*` events. Log analysis tools can use the `dom-event-timestamp` event property to determine the order of the `Ctrl-X` user action with respect to the `change-*` events.
* Copy: Copying text does not change the document, and so Cryolite only logs a `copy-clipboard` event.
* Paste: The `paste-clipboard` event _precedes_ the `change-*` events.

### Limitations

When the user selects one of the Cut, Copy, and Paste menu items, the Cloud9 IDE displays the “Native Clipboard Unavailable” dialog box. For the Cut and Copy commands, the dialog contains the selected text and instructs the user to manually copy that text to the native clipboard using the `Ctrl-C` keyboard shortcut. However when the user presses `Ctrl-C` (or `Ctrl-X`), Cryolite receives the event with an empty clipboard causing Cryolite to log a `*-clipboard` event with an empty `data` property.