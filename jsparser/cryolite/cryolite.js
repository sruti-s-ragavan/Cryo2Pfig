/**
 * Cryolite: Cloud9 Recorder of Your Operations by Listening to Interactions in The Editor
 *
 * @class cryolite
 * @extends Plugin
 * @singleton
 * @copyright Copyright 2013-2015 Carnegie Mellon University
 * @license GPLv3 <http://www.gnu.org/licenses/gpl.txt>
 *
 * This file is part of Cryolite.
 *
 * Cryolite is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Cryolite is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cryolite. If not, see <http://www.gnu.org/licenses/>.
 */

define(function cryolite(require, exports, module) {
    "use strict";

    main.consumes = ["Plugin", "c9", "settings", "preferences", "fs", "fs.cache", "commands", "panels", "tree", "tree.favorites", "tabManager", "console", "dialog.alert"];
    main.provides = ["cryolite"];

    var modelist = require("ace/ext/modelist");

    var treehuggerTree;
    var treehuggerTraverse;
    var treehuggerParse;
    var treehuggerAcornLoose;

    // treehuggerTree = require("treehugger/tree");
    // treehuggerTraverse = require("treehugger/traverse");
    // treehuggerParse = require("treehugger/js/parse");
    // treehuggerAcornLoose = require("acorn/dist/acorn_loose");

    return main;

    function main(options, imports, register) {
        var Plugin = imports.Plugin;
        var c9 = imports.c9;
        var settings = imports.settings;
        var preferences = imports.preferences;
        var fs = imports.fs;
        var fsCache = imports["fs.cache"];
        var commands = imports.commands;
        var panels = imports.panels;
        var tree = imports.tree;
        var treeFavorites = imports["tree.favorites"];
        var tabManager = imports.tabManager;
        var c9Console = imports.console;
        var alert = imports["dialog.alert"];

        var plugin = new Plugin("Human-Computer Interaction Institute, Carnegie Mellon University", main.consumes);

        var PLUGIN_VERSION = "0.4.0-beta3-dev";
        var LOG_FORMAT_VERSION = "0.4.0-beta3-dev";

        var SETTINGS_PATH = "user/cryolite";
        var DEBUG_SETTING_NAME = "debug";
        var DEBUG_SETTING_PATH = SETTINGS_PATH + "/@" + DEBUG_SETTING_NAME;
        var GENERATE_PRETTY_PRINT_LOG_SETTING_NAME = "generate-pretty-print-log";
        var GENERATE_PRETTY_PRINT_LOG_SETTING_PATH = SETTINGS_PATH + "/@" + GENERATE_PRETTY_PRINT_LOG_SETTING_NAME;
        var EVENT_TYPES_TO_IGNORE_SETTING_NAME = "event-types-to-ignore";
        var EVENT_TYPES_TO_IGNORE_SETTING_PATH = SETTINGS_PATH + "/@" + EVENT_TYPES_TO_IGNORE_SETTING_NAME;
        var CODE_SUMMARY_LOGGING_SETTING_NAME = "code-summary-logging";
        var CODE_SUMMARY_LOGGING_SETTING_PATH = SETTINGS_PATH + "/@" + CODE_SUMMARY_LOGGING_SETTING_NAME;

        var CODE_SUMMARY_LOGGING_NEVER = "never";
        var CODE_SUMMARY_LOGGING_OPEN_SAVE_CLOSE = "open-save-close";
        var CODE_SUMMARY_LOGGING_OPEN_SAVE_CLOSE_CHANGE = "open-save-close-change";

        var LOG_FILE_DIRECTORY = "/.cryolite";
        var LOG_FILE_DATE = new Date().toISOString().substring(0, 10);
        var LOG_FILE_NAME_PREFIX = "cryolite-" + LOG_FILE_DATE;
        var LOG_FILE_PATH = LOG_FILE_DIRECTORY + "/" + LOG_FILE_NAME_PREFIX + ".log";
        var LOG_FILE_PRETTY_PRINT_PATH = LOG_FILE_DIRECTORY + "/" + LOG_FILE_NAME_PREFIX + "-pretty-print.log";

        var WRITE_TO_EVENTS_LOG_INTERVAL = 1000;

        var CONSOLE_INFO_CSS = "background: #ACFFA3";
        var CONSOLE_WARN_CSS = "background: orange";
        var CONSOLE_ERROR_CSS = "color: white; background: red";

        var loaded = false;

        var logReady = false;
        var loggingActive = false;

        var userSettings = {};

        var openDocuments = {};

        function clamp(min, val, max) {
            return Math.min(Math.max(min, val), max);
        }

        function appendEventProperties(event, properties) {
            for (var key in properties) {
                if (event.hasOwnProperty(key)) {
                    console.warn("appendEventProperties(): overwriting key", key, event[key], properties[key]);
                }

                event[key] = properties[key];
            }

            return event;
        }

        function areObjectsEqual(object1, object2) {
            var object1JSON = JSON.stringify(object1);
            var object2JSON = JSON.stringify(object2);
            return object1JSON === object2JSON;
        }

        function isDebug() {
            return userSettings[DEBUG_SETTING_NAME];
        }

        function load() {
            if (loaded) {
                return;
            }

            loaded = true;

            initializePreferences();

            function createLogFileDirectory(callback) {
                fs.exists(LOG_FILE_DIRECTORY, function afterCheckIfLogFileDirectoryExists(exists) {
                    if (!exists) {
                        fs.mkdir(LOG_FILE_DIRECTORY, function afterMakeDirectoryForLogFile(err) {
                            if (err) {
                                console.error("error creating log directory", LOG_FILE_DIRECTORY, err);
                                var alertTitle = "Cryolite Fatal Error";
                                var alertHeader = "Failed to create log directory: &ldquo;" + LOG_FILE_DIRECTORY + "&rdquo;";
                                var alertMessage = "The log file will NOT be written.\n" + err.message + "";
                                alert.show(alertTitle, alertHeader, alertMessage);
                            }
                            else {
                                callback();
                            }
                        });
                    }
                    else {
                        callback();
                    }
                });
            }

            createLogFileDirectory(function afterLogFileDirectoryCreated() {
                logReady = true;
                initializeSettings();
                startLogging();
            });
        }

        function initializePreferences() {
            var preferenceDefinitions = {
                "position": 100,
                "Debug": {
                    "type": "checkbox",
                    "path": DEBUG_SETTING_PATH,
                    "position": 100
                },
                "Generate Second Log in Pretty Print Format": {
                    "type": "checkbox",
                    "path": GENERATE_PRETTY_PRINT_LOG_SETTING_PATH,
                    "position": 200
                },
                "Event Types to Ignore": {
                    "type": "textbox",
                    "width": 500,
                    "path": EVENT_TYPES_TO_IGNORE_SETTING_PATH,
                    "position": 300
                }
            };

            if (isTreehuggerLoaded()) {
                preferenceDefinitions["Code Summary Logging"] = {
                    "type": "dropdown",
                    "width": 250,
                    "path": CODE_SUMMARY_LOGGING_SETTING_PATH,
                    "items": [{
                        "caption": "Never",
                        "value": CODE_SUMMARY_LOGGING_NEVER
                    }, {
                        "caption": "Open, Save, and Close Document",
                        "value": CODE_SUMMARY_LOGGING_OPEN_SAVE_CLOSE
                    }, {
                        "caption": "Open, Save, Close, and Change Document",
                        "value": CODE_SUMMARY_LOGGING_OPEN_SAVE_CLOSE_CHANGE
                    }],
                    "position": 400
                };
            }

            preferences.add({
                "Logging": {
                    "position": 900,
                    "Cryolite": preferenceDefinitions
                }
            }, plugin);
        }

        function initializeSettings() {
            function updateSettings(e) {
                var originalUserSettingsAsJSON = JSON.stringify(userSettings);

                userSettings[DEBUG_SETTING_NAME] = settings.getBool(DEBUG_SETTING_PATH);
                userSettings[GENERATE_PRETTY_PRINT_LOG_SETTING_NAME] = settings.getBool(GENERATE_PRETTY_PRINT_LOG_SETTING_PATH);
                userSettings[EVENT_TYPES_TO_IGNORE_SETTING_NAME] = [];
                userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME] = settings.get(CODE_SUMMARY_LOGGING_SETTING_PATH);

                var eventTypesToIgnoreString = settings.get(EVENT_TYPES_TO_IGNORE_SETTING_PATH).trim();
                if (eventTypesToIgnoreString !== "") {
                    var eventTypesToIgnore = eventTypesToIgnoreString.split(",");

                    eventTypesToIgnore = eventTypesToIgnore.map(function trimEventType(eventType) {
                        return eventType.trim();
                    });

                    eventTypesToIgnore = eventTypesToIgnore.filter(function isEventTypeEmpty(eventType) {
                        return eventType !== "";
                    });

                    userSettings[EVENT_TYPES_TO_IGNORE_SETTING_NAME] = eventTypesToIgnore;
                }

                if (loggingActive && (originalUserSettingsAsJSON !== JSON.stringify(userSettings))) {
                    var updateSettingsEventProperties = {
                        "settings": userSettings
                    };

                    logEvent("update-settings", null, updateSettingsEventProperties);
                }
            }

            settings.on("read", function onReadSettings() {
                settings.setDefaults(SETTINGS_PATH, [
                    [DEBUG_SETTING_NAME, false],
                    [GENERATE_PRETTY_PRINT_LOG_SETTING_NAME, false],
                    [EVENT_TYPES_TO_IGNORE_SETTING_NAME, ""],
                    [CODE_SUMMARY_LOGGING_SETTING_NAME, CODE_SUMMARY_LOGGING_NEVER]
                ]);

                updateSettings();
            }, plugin);

            settings.on("write", updateSettings, plugin);

            settings.on(DEBUG_SETTING_PATH, updateSettings, plugin);
            settings.on(GENERATE_PRETTY_PRINT_LOG_SETTING_PATH, updateSettings, plugin);
            settings.on(EVENT_TYPES_TO_IGNORE_SETTING_PATH, updateSettings, plugin);
            settings.on(CODE_SUMMARY_LOGGING_SETTING_PATH, updateSettings, plugin);
        }

        var eventsToWrite = [];
        var eventsWritingTask = null;
        var nextEventSequenceID = 1;
        var lastEventTimestamp = 0;

        function logEvent(eventType, actionTimestamp, properties) {
            console.log("%clogEvent():", "background: #AADBFF", eventType);

            if (!(logReady && loggingActive)) {
                console.warn("logEvent(): not in logging state", logReady, loggingActive, eventType);
                console.trace();
                return null;
            }

            if (!eventType) {
                console.warn("logEvent(): missing eventType", eventType);
            }

            if (typeof eventType !== "string") {
                console.warn("logEvent(): eventType is not a string", typeof eventType, eventType);
            }

            if (actionTimestamp) {
                if (!Array.isArray(actionTimestamp)) {
                    if (!actionTimestamp instanceof Date) {
                        console.warn("logEvent(): actionTimestamp is not a date", eventType, actionTimestamp);
                    }
                }
                else {
                    var allActionTimestampsAreDates = actionTimestamp.every(function isDate(timestamp) {
                        return timestamp instanceof Date;
                    });

                    if (!allActionTimestampsAreDates) {
                        console.warn("logEvent(): actionTimestamp array contains non-date element(s)", eventType, actionTimestamp);
                    }
                }
            }

            if ((properties !== undefined) && (typeof properties !== "object")) {
                console.warn("logEvent(): actionTimestamp is not an object", eventType, typeof properties, properties);
            }

            var eventTypesToIgnore = userSettings[EVENT_TYPES_TO_IGNORE_SETTING_NAME];
            if (eventTypesToIgnore.indexOf(eventType) >= 0) {
                console.log("logEvent(): ignoring event", eventType);
                return null;
            }

            var event = {
                "event-type": eventType,
                "sequence-id": nextEventSequenceID++
            };

            event["logged-timestamp"] = new Date();

            if (actionTimestamp) {
                var actionTimestampPropertyName = Array.isArray(actionTimestamp) ? "action-timestamps" : "action-timestamp";
                event[actionTimestampPropertyName] = actionTimestamp;
            }

            var eventSummary = {};

            for (var key in event) {
                eventSummary[key] = event[key];
            }

            if (properties) {
                for (var key in properties) {
                    if (key in event) {
                        console.warn("logEvent(): overwriting event property", key, event[key], properties[key]);
                    }

                    event[key] = properties[key];
                }
            }

            try {
                eventSummary["json"] = JSON.stringify(event);
                eventsToWrite.push(eventSummary);
            }

            catch (ex) {
                var errorMessage = "JSON.stringify(event) failed";
                console.error(errorMessage, ex, eventSummary);

                try {
                    eventSummary["error-message"] = errorMessage;
                    eventSummary["exception"] = ex.toString();
                    eventSummary["json"] = JSON.stringify(eventSummary);
                    eventsToWrite.push(eventSummary);
                }

                catch (ex) {
                    console.error(ex, eventSummary);
                }
            }

            return event;
        }

        function writeEventsToLog() {
            var STATUS_READY = "ready";
            var STATUS_WRITING = "writing";
            var STATUS_DONE = "done";

            function setupWritingTask() {
                var generatePrettyPrint = userSettings[GENERATE_PRETTY_PRINT_LOG_SETTING_NAME];

                eventsWritingTask = {
                    "name": eventsToWrite[0]["sequence-id"] + "-" + eventsToWrite[eventsToWrite.length - 1]["sequence-id"] + ":" + eventsToWrite.length,
                    "events": eventsToWrite,
                    "singleLineStatus": STATUS_READY,
                    "singleLineJSON": "",
                    "prettyPrintStatus": generatePrettyPrint ? STATUS_READY : STATUS_DONE,
                    "prettyPrintJSON": ""
                };

                // var setupTimerLabel = eventsWritingTask.name + "-setup";
                // console.time(setupTimerLabel);

                eventsToWrite.forEach(function addEventJSONToWritingTask(eventSummary) {
                    var currentEventTimestamp = new Date(eventSummary["logged-timestamp"]);
                    var timestampDelta = currentEventTimestamp - lastEventTimestamp;
                    lastEventTimestamp = currentEventTimestamp;

                    if (isDebug() && (timestampDelta > 1000)) {
                        eventsWritingTask.singleLineJSON += "\n";
                    }

                    eventsWritingTask.singleLineJSON += eventSummary["json"] + "\n";

                    if (generatePrettyPrint) {
                        eventsWritingTask.prettyPrintJSON += JSON.stringify(JSON.parse(eventSummary["json"]), null, "\t") + "\n";
                    }
                });

                // console.timeEnd(setupTimerLabel);

                eventsToWrite = [];
            }

            function checkIfWritingTaskIsDone() {
                if ((eventsWritingTask.singleLineStatus === STATUS_DONE) && (eventsWritingTask.prettyPrintStatus === STATUS_DONE)) {
                    eventsWritingTask = null;
                }
            }

            function writeToLogFiles() {
                if (!c9.connected) {
                    return;
                }

                if (eventsWritingTask.singleLineStatus === STATUS_READY) {
                    // var slfTimerLabel = eventsWritingTask.name + "-slf-" + eventsWritingTask.singleLineJSON.length;
                    // console.time(slfTimerLabel);

                    eventsWritingTask.singleLineStatus = STATUS_WRITING;
                    fs.appendFile(LOG_FILE_PATH, eventsWritingTask.singleLineJSON, function afterAppendingEventsToLogFile(err) {
                        if (err) {
                            console.error("writeToLogFiles(): error writing event to log file (single-line format)", LOG_FILE_PATH, err, eventsWritingTask.name);
                            eventsWritingTask.singleLineStatus = STATUS_READY;
                            return;
                        }

                        eventsWritingTask.singleLineStatus = STATUS_DONE;
                        checkIfWritingTaskIsDone();
                        // console.timeEnd(slfTimerLabel);
                    });
                }

                if (eventsWritingTask.prettyPrintStatus === STATUS_READY) {
                    // var ppfTimerLabel = eventsWritingTask.name + "-ppf-" + eventsWritingTask.prettyPrintJSON.length;
                    // console.time(ppfTimerLabel);

                    eventsWritingTask.prettyPrintStatus = STATUS_WRITING;
                    fs.appendFile(LOG_FILE_PRETTY_PRINT_PATH, eventsWritingTask.prettyPrintJSON, function afterAppendingEventsToPrettyPrintLogFile(err) {
                        if (err) {
                            console.error("writeToLogFiles(): error writing event to log file (pretty-print format)", LOG_FILE_PRETTY_PRINT_PATH, err, eventsWritingTask.name);
                            eventsWritingTask.prettyPrintStatus = STATUS_READY;
                            return;
                        }

                        eventsWritingTask.prettyPrintStatus = STATUS_DONE;
                        checkIfWritingTaskIsDone();
                        // console.timeEnd(ppfTimerLabel);
                    });
                }
            }

            if (eventsWritingTask !== null) {
                if ((eventsWritingTask.singleLineStatus === STATUS_READY) || (eventsWritingTask.prettyPrintStatus === STATUS_READY)) {
                    writeToLogFiles();
                }

                return false;
            }

            if (eventsToWrite.length === 0) {
                return true;
            }

            setupWritingTask();
            writeToLogFiles();

            return false;
        }

        function getTabRenderer(tab) {
            var c9Document = tab.document;
            if (!c9Document) {
                console.warn("getTabRenderer(): invalid document", tab.title);
                return null;
            }

            var editor = c9Document.editor;
            if (!editor) {
                console.warn("getTabRenderer(): invalid editor", tab.title);
                return null;
            }

            var ace = editor.ace;
            if (!ace) {
                console.warn("getTabRenderer(): invalid ace", tab.title);
                return null;
            }

            var renderer = ace.renderer;
            if (!renderer) {
                console.warn("getTabRenderer(): invalid renderer", tab.title);
                return null;
            }

            return renderer;
        }

        function waitUntilTabRendered(tab, callback, id, afterRenderCallback) {
            var renderer = getTabRenderer(tab);
            // console.log("%cwaitUntilTabRendered():", CONSOLE_INFO_CSS, id, !!renderer);
            if (renderer) {
                waitUntilRendered(renderer, isAceRendererDirty, callback, id, afterRenderCallback);
            }

            return !!renderer;
        }

        function waitUntilRendered(renderer, isRendererDirty, callback, id, afterRenderCallback) {
            console.log("waitUntilRendered():", id);

            if (typeof callback !== "function") {
                console.warn("waitUntilRendered(): callback not a function", typeof callback, callback);
            }

            var afterRenderCount = 0;
            var startTime = Date.now();

            var MAX_TIMEOUT_INTERVAL = 300;
            var timeoutID;

            if (isRendererDirty && !isRendererDirty(renderer)) {
                console.log("waitUntilRendered(): renderer not dirty", id);

                if (typeof callback === "function") {
                    callback();
                }

                return;
            }

            renderer.on("afterRender", onAfterRender);

            function onAfterRender() {
                console.log("onAfterRender():", id, ++afterRenderCount, Date.now() - startTime, renderer.$changes);

                clearTimeout(timeoutID);

                if (typeof afterRenderCallback === "function") {
                    var done = afterRenderCallback();
                    if (done) {
                        report();
                        return;
                    }
                }

                timeoutID = setTimeout(report, MAX_TIMEOUT_INTERVAL);
            }

            function report() {
                console.log("report()", id, afterRenderCount, Date.now() - startTime);

                if (isRendererDirty && isRendererDirty(renderer)) {
                    console.log("waitUntilRendered() / report(): renderer is dirty", id);
                    return;
                }

                if (typeof callback === "function") {
                    callback();
                }

                renderer.off("afterRender", onAfterRender);
            }
        }

        function logStartLogging() {
            var startLoggingEventProperties = {
                "version": PLUGIN_VERSION,
                "log-format": LOG_FORMAT_VERSION,
                "user-agent": window.navigator.userAgent,
                "timezone-offset": new Date().getTimezoneOffset(),
                "settings": userSettings
            };

            logEvent("start-logging", null, startLoggingEventProperties);
        }

        function logStopLogging() {
            logEvent("stop-logging");
        }

        function convertLocationToOneBasedIndex(location) {
            if (location === undefined) {
                return undefined;
            }

            var convertedLocation = {};

            if (typeof location.row === "number") {
                convertedLocation.line = location.row + 1;
            }

            if (typeof location.line === "number") {
                convertedLocation.line = location.line + 1;
            }

            if (typeof location.column === "number") {
                convertedLocation.column = location.column + 1;
            }

            return convertedLocation;
        }

        function normalizeCursor(selection) {
            if (!Array.isArray(selection)) {
                return extractCursorFromRange(selection);
            }

            return selection.map(extractCursorFromRange);

            function extractCursorFromRange(range) {
                var cursor = range.isBackwards ? range.start : range.end;
                return convertLocationToOneBasedIndex(cursor);
            }
        }

        function normalizeSelection(selection) {
            if (!Array.isArray(selection)) {
                return isRangeNonEmpty(selection) ? convertRangeToOneBasedIndex(selection) : null;
            }

            var nonEmptyRanges = selection.filter(isRangeNonEmpty);
            var convertedRanges = nonEmptyRanges.map(convertRangeToOneBasedIndex);
            return (convertedRanges.length > 0) ? convertedRanges : null;

            function isRangeNonEmpty(range) {
                return !((range.start.row === range.end.row) && (range.start.column === range.end.column));
            }

            function convertRangeToOneBasedIndex(range) {
                return {
                    "start": convertLocationToOneBasedIndex(range.start),
                    "end": convertLocationToOneBasedIndex(range.end),
                    "isBackwards": range.isBackwards
                };
            }
        }

        function convertRowColumnToLineColumn(rowColumn) {
            return {
                "line": rowColumn.row,
                "column": rowColumn.column
            };
        }

        function convertFoldsToOneBasedIndex(folds) {
            function convertLocationToAbsolute(location, baseLocation) {
                var resultLocation = {
                    "row": baseLocation.row + location.row,
                    "column": location.column
                };

                if (location.row === 0) {
                    resultLocation.column += baseLocation.column;
                }

                return resultLocation;
            }

            function convertFold(fold) {
                var parentFoldLocation = (this !== window) ? this : undefined;

                var start = fold.start;
                var end = fold.end;

                if (parentFoldLocation) {
                    start = convertLocationToAbsolute(start, parentFoldLocation.start);
                    end = convertLocationToAbsolute(end, parentFoldLocation.start);
                }

                var subFolds;
                if ((fold.subFolds !== undefined) && (fold.subFolds.length > 0)) {
                    var foldLocation = {
                        "start": start,
                        "end": end
                    };

                    subFolds = fold.subFolds.map(convertFold, foldLocation);
                }

                return {
                    "start": convertLocationToOneBasedIndex(start),
                    "end": convertLocationToOneBasedIndex(end),
                    "children": subFolds
                };
            }

            return folds.map(convertFold);
        }

        function isTreehuggerLoaded() {
            return (treehuggerTree !== undefined) && (treehuggerTraverse !== undefined) && (treehuggerParse !== undefined) && (treehuggerAcornLoose !== undefined);
        }

        function summarizeCode(contents) {
            if (!isTreehuggerLoaded()) {
                console.error("summarizeCode(): treehugger not loaded", treehuggerTree, treehuggerTraverse, treehuggerParse, treehuggerAcornLoose);
                return undefined;
            }

            try {
                var lines = contents.split(/\r\n|\r|\n/);
                var linesType = [];

                var blankLineRegExp = new RegExp("^\\s*$");
                var singleLineCommentRegExp = new RegExp("^\\s*//.*$");

                for (var lineNum = 0; lineNum < lines.length; lineNum++) {
                    var line = lines[lineNum];
                    if ((line.length === 0) || blankLineRegExp.test(line)) {
                        linesType[lineNum] = "blank-lines";
                    }
                    else if (singleLineCommentRegExp.test(line)) {
                        linesType[lineNum] = "single-line-comment-lines";
                    }
                }

                var ast = treehuggerAcornLoose.parse_dammit(contents, {
                    "locations": true,
                    "onComment": function onComment(block, text, startPos, endPos, startLoc, endLoc) {
                        if (block) {
                            for (var lineNum = startLoc.line; lineNum <= endLoc.line; lineNum++) {
                                linesType[lineNum] = "block-comment-lines";
                            }
                        }
                    }
                });

                ast = treehuggerParse.transform(ast);

                var astNodeCount = 0;

                ast.traverseTopDown("node", function visitASTNode(bindings) {
                    if ((bindings.node instanceof treehuggerTree.StringNode) || (bindings.node instanceof treehuggerTree.ConsNode)) {
                        astNodeCount++;
                        var pos = bindings.node.getPos();
                        if (pos && (pos.sl < lines.length)) {
                            if ((bindings.node.cons === "Try") || (bindings.node.cons === "Switch")) {
                                for (var lineNum = pos.sl; lineNum <= pos.el; lineNum++) {
                                    if (linesType[lineNum] === undefined) {
                                        linesType[lineNum] = "active-lines";
                                    }
                                }
                            }
                            else {
                                linesType[pos.sl] = "active-lines";
                                linesType[pos.el] = "active-lines";
                            }
                        }
                    }

                    return false;
                });

                var codeSummary = {
                    "ast-node-count": astNodeCount,
                    "active-lines": 0,
                    "blank-lines": 0,
                    "single-line-comment-lines": 0,
                    "block-comment-lines": 0,
                    "unclassified-lines": 0,
                    "total-lines": lines.length
                };

                for (var lineNum = 0; lineNum < lines.length; lineNum++) {
                    var lineType = linesType[lineNum];
                    if (lineType !== undefined) {
                        codeSummary[lineType]++;
                    }
                    else {
                        codeSummary["unclassified-lines"]++;
                    }
                }

                return codeSummary;
            }
            catch (ex) {
                return {
                    "parse-exception": {
                        "message": ex.message,
                        "location": convertLocationToOneBasedIndex(ex.loc),
                        "position": ex.pos
                    }
                };
            }
        }

        function logPanelConfiguration(callback) {
            var thePanels = panels.panels || {};
            var activePanels = panels.activePanels || [];
            var panelConfigurations = [];

            Object.keys(thePanels).forEach(function getPanelConfiguration(name) {
                var panel = thePanels[name];

                panelConfigurations.push({
                    "name": name,
                    "caption": panel.button ? panel.button.caption : null,
                    "enabled": panel.enabled,
                    "active": activePanels.indexOf(name) >= 0,
                    "where": panel.where,
                    "area": panel.area ? panel.area.name : null
                });
            });

            var loadPanelsEventProperties = {
                "configuration": panelConfigurations
            };

            logEvent("load-panels", null, loadPanelsEventProperties);
            callback();
        }

        function getTabsState() {
            var tabsState = [];

            var editorState = tabManager.getState(null, true);

            if (editorState === undefined) {
                return undefined;
            }

            tabsState.push({
                "name": "editor",
                "type": "container",
                "dimensions": {
                    "width": tabManager.container.getWidth(),
                    "height": tabManager.container.getHeight()
                },
                "nodes": [editorState]
            });

            var c9ConsoleValid = c9Console.container !== undefined;

            tabsState.push({
                "name": "console",
                "type": "container",
                "dimensions": c9ConsoleValid ? {
                    "width": c9Console.container.getWidth(),
                    "height": c9Console.container.getHeight()
                } : null,
                "opened": settings.getBool("state/console/@expanded"),
                "maximized": settings.getBool("state/console/@maximized"),
                "normal-height": settings.getNumber("state/console/@height"),
                "nodes": c9ConsoleValid ? [c9Console.getState(true)] : undefined
            });

            return tabsState;
        }

        function getTabsConfiguration(tabsState) {
            if (tabsState === undefined) {
                tabsState = getTabsState();
            }

            var focusedTab = tabManager.focussedTab;
            var focusedTabName = focusedTab && focusedTab.name;

            function convertSourceNode(sourceNode) {
                var node = {
                    "type": sourceNode.type,
                    "name": sourceNode.name,
                    "dimensions": sourceNode.dimensions,
                    "opened": sourceNode.opened,
                    "maximized": sourceNode.maximized,
                    "normal-height": sourceNode["normal-height"]
                };

                var type = sourceNode.type;

                if ((type === "container") || (type === "hsplitbox") || (type === "vsplitbox") || (type === "pane")) {
                    node["width"] = sourceNode.width;
                    node["height"] = sourceNode.height;

                    if (sourceNode.nodes && Array.isArray(sourceNode.nodes) && (sourceNode.nodes.length > 0)) {
                        node["children"] = sourceNode.nodes.map(convertSourceNode);
                        node["children"] = node["children"].filter(isValueNonNull);

                        if (node["children"].length === 0) {
                            delete node["children"];
                        }
                    }
                }
                else if (type === "tab") {
                    var tab = tabManager.findTab(sourceNode.name) || tabManager.findTab(sourceNode.path);

                    if (tab === undefined) {
                        console.warn("getTabsConfiguration(): invalid tab in tabsState", sourceNode.name, sourceNode.path, JSON.stringify(tabsState, null, 1));
                        return null;
                    }

                    node["title"] = sourceNode.document.title;
                    node["path"] = sourceNode.path;
                    node["document-name"] = tab.document.name;
                    node["cloned"] = !!sourceNode.document.meta.cloned;
                    node["focused"] = sourceNode.name === focusedTabName;
                    node["active"] = sourceNode.active;
                    node["editor-type"] = sourceNode.editorType;
                    node["width"] = sourceNode.width;
                    node["height"] = sourceNode.height;
                }
                else {
                    console.warn("getTabsConfiguration(): unknown node type", type);
                }

                return node;
            }

            function isValueNonNull(value) {
                return value !== null;
            }

            return tabsState.map(convertSourceNode);
        }

        function logTabsConfiguration(callback) {
            function attemptToLogTabsConfiguration() {
                var tabsState = getTabsState();
                if (tabsState === undefined) {
                    return false;
                }

                // console.log("attemptToLogTabsConfiguration(): tab count", tabManager.getTabs().length);

                var areAllTabsReadyToLog = tabManager.getTabs().every(function isTabReadyToLog(tab) {
                    // console.log("%cisTabReadyToLog()", CONSOLE_INFO_CSS, tab.title, tab.path, tab.active);
                    return !isAceTab(tab) || !tab.active || isDocumentViewValid(tab.document);
                });

                console.log("areAllTabsReadyToLog", areAllTabsReadyToLog);

                if (!areAllTabsReadyToLog) {
                    // console.log("%careAllTabsReadyToLog is false; wait and try again", CONSOLE_WARN_CSS);
                    return false;
                }

                if (intervalID !== undefined) {
                    clearInterval(intervalID);
                }

                // console.log("focusedTab:", tabManager.focussedTab, tabManager.focussedTab.name);

                var loadTabsEventProperties = {
                    "configuration": getTabsConfiguration(tabsState),
                    "active-tabs": getActiveTabsInfo()
                };

                logEvent("load-tabs", null, loadTabsEventProperties);
                callback();

                return true;
            }

            if (attemptToLogTabsConfiguration()) {
                return;
            }

            var intervalID = setInterval(attemptToLogTabsConfiguration, 10);
        }

        function isDocumentLoaded(c9Document) {
            if (!c9Document.ready || !c9Document.hasValue()) {
                return false;
            }

            if (!isAceTab(c9Document.tab)) {
                return true;
            }

            var state = c9Document.getState();
            var isAceStateLoaded = ("ace" in state) && ("selection" in state.ace) && ("scrolltop" in state.ace) && ("scrollleft" in state.ace) && ("folds" in state.ace) && ("options" in state.ace);

            if (!isAceStateLoaded) {
                console.warn("isDocumentLoaded(): ACE state not loaded", JSON.stringify(state.ace, null, 1));
            }

            return isAceStateLoaded;
        }

        function getDocumentInfo(c9Document, logCodeSummary) {
            var state = c9Document.getState();

            // console.log("%cgetDocumentInfo():", CONSOLE_INFO_CSS, c9Document.tab.path, JSON.stringify(state, null, 1));

            var documentInfo = {
                "name": c9Document.name,
                "title": c9Document.tab.title,
                "path": c9Document.tab.path,
                "cloned": !!c9Document.meta.cloned
            };

            if (state.ace !== undefined) {
                var syntax = modelist.getModeForPath(c9Document.tab.path).name;
                var value = c9Document.value;

                if (!documentInfo["cloned"]) {
                    documentInfo["syntax"] = syntax;
                    documentInfo["length"] = value.length;
                    documentInfo["changed"] = c9Document.changed;
                    documentInfo["contents"] = value;
                    documentInfo["code-summary"] = (logCodeSummary && (syntax === "javascript")) ? summarizeCode(value) : undefined;
                }

                documentInfo["cursor"] = (state.ace.selection !== undefined) ? normalizeCursor(state.ace.selection) : undefined;
                documentInfo["selection"] = (state.ace.selection !== undefined) ? normalizeSelection(state.ace.selection) : undefined;
                documentInfo["scroll-position"] = ((state.ace.scrolltop !== undefined) && (state.ace.scrollleft !== undefined)) ? {
                    "top": state.ace.scrolltop,
                    "left": state.ace.scrollleft
                } : undefined;
                documentInfo["folds"] = (state.ace.folds !== undefined) ? convertFoldsToOneBasedIndex(state.ace.folds) : undefined;
                documentInfo["ace-options"] = (state.ace.options !== undefined) ? state.ace.options : undefined;
            }

            return documentInfo;
        }

        function logDocuments(callback) {
            var logCodeSummary = userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME].indexOf("open") >= 0;

            var initiallyOpenDocuments = {};

            var tabs = tabManager.getTabs();
            // console.log("%clogDocuments tab count", CONSOLE_INFO_CSS, tabs.length);
            tabs.forEach(function getDocumentFromTab(tab) {
                // console.log("%cinitially opened tab", CONSOLE_INFO_CSS, tab.name, tab.path, tab.title, !!tab.editor, !!tab.document);
                if (tab.path !== undefined) {
                    // console.log(tab.path, tab.document.name, tab.document.meta.cloned);
                    initiallyOpenDocuments[tab.document.name] = {
                        "c9Document": tab.document,
                        "loaded": false
                    };
                }
            });

            // console.log("initiallyOpenDocuments", Object.keys(initiallyOpenDocuments).toString());

            if (Object.keys(initiallyOpenDocuments).length === 0) {
                logLoadDocuments([]);
                callback();
                return;
            }

            tabManager.on("tabDestroy", initialTabDestroyed, plugin);

            for (var documentName in initiallyOpenDocuments) {
                var c9Document = initiallyOpenDocuments[documentName].c9Document;
                c9Document.once("ready", documentReady, plugin);
            }

            function documentReady(e) {
                var c9Document = e.doc;

                if (!isDocumentLoaded(c9Document)) {
                    console.warn("documentReady(): document is not loaded", c9Document.name, c9Document.tab.path);
                }

                initiallyOpenDocuments[c9Document.name].loaded = true;

                checkIfAllDocumentsAreLoaded();
            }

            function initialTabDestroyed(e) {
                delete initiallyOpenDocuments[e.tab.document.name];
                checkIfAllDocumentsAreLoaded();
            }

            function checkIfAllDocumentsAreLoaded() {
                for (var documentName in initiallyOpenDocuments) {
                    if (!initiallyOpenDocuments[documentName].loaded) {
                        return;
                    }
                }

                tabManager.off("tabDestroy", initialTabDestroyed);

                var documentInfos = [];

                for (var documentName in initiallyOpenDocuments) {
                    var documentStatus = initiallyOpenDocuments[documentName];
                    var documentInfo = getDocumentInfo(documentStatus.c9Document, logCodeSummary);
                    documentInfos.push(documentInfo);
                    openDocuments[documentName] = initiallyOpenDocuments[documentName].c9Document;
                }

                logLoadDocuments(documentInfos);
                callback();
            }

            function logLoadDocuments(documentInfos) {
                var loadDocumentsEventProperties = {
                    "documents": documentInfos
                };

                logEvent("load-documents", null, loadDocumentsEventProperties);
            }
        }

        function getWrapType(aceSession) {
            var wrapType = aceSession.getOption("wrap");

            if (wrapType === "free") {
                wrapType = "viewport";
            }
            else if (wrapType === "printMargin") {
                wrapType = "print-margin";
            }

            return wrapType;
        }

        function getWrapLimit(aceSession) {
            var wrapType = getWrapType(aceSession);
            var wrapLimit = aceSession.getWrapLimit();

            if (wrapType === "off") {
                wrapLimit = undefined;
            }

            return wrapLimit;
        }

        function isAceRendererDirty(renderer) {
            console.log("isAceRendererDirty", renderer.$changes, renderer.$loop.changes, renderer.$loop.pending, renderer.$size.$dirty);

            if (!renderer.$loop.changes) {
                // if (renderer.$loop.pending) {
                //     console.warn("ACE: PENDING without changes", renderer.$loop.pending, renderer.$loop.changes);
                // }

                if (renderer.$size.$dirty) {
                    console.warn("ACE: SIZE DIRTY without changes", renderer.$size.$dirty, renderer.$loop.changes);
                }
            }

            return !!(renderer.$changes || renderer.$loop.changes); // || renderer.$size.$dirty);
        }

        function isAceTreeRendererDirty(renderer) {
            // console.log("isAceTreeRendererDirty", renderer.$changes, renderer.$loop.changes, renderer.$loop.pending);

            if (!renderer.$loop.changes) {
                // if (renderer.$loop.pending) {
                //     console.warn("ACE TREE: PENDING without changes", renderer.$loop.pending, renderer.$loop.changes);
                // }

                if (renderer.$size.$dirty) {
                    console.warn("ACE TREE: SIZE DIRTY without changes", renderer.$size.$dirty, renderer.$loop.changes);
                }
            }

            return !!(renderer.$changes || renderer.$loop.changes || renderer.$loop.pending);
        }

        function isAceTab(tab) {
            // console.log("isAceTab", tab.path, tab.editorType, tab.active, " => ", (tab.path !== undefined) && (tab.editorType === "ace"));
            return (tab.path !== undefined) && (tab.editorType === "ace");
        }

        function isDocumentViewValid(c9Document) {
            var tabTitle = c9Document.tab.title;
            var tabName = c9Document.tab.name;

            var c9Session = c9Document.getSession();
            if (!c9Session) {
                return false;
            }

            var aceSession = c9Session.session;
            if (!aceSession) {
                return false;
            }

            if (aceSession.getLength() <= 0) {
                console.warn("isDocumentViewValid(): document is empty", tabTitle, tabName, aceSession.getLength());
            }

            var editor = c9Document.editor;

            if (!editor || (editor.type !== "ace") || !editor.ace || !editor.ace.renderer) {
                return false;
            }

            if (aceSession !== editor.ace.session) {
                console.warn("isDocumentViewValid(): mismatching sessions", tabTitle, tabName);
            }

            var renderer = editor.ace.renderer;

            if (c9Document !== renderer.session.c9doc) {
                console.warn("isDocumentViewValid(): mismatching documents", tabTitle, tabName, c9Document && c9Document.name, renderer.session.c9doc && renderer.session.c9doc.name);
            }

            if (isAceRendererDirty(renderer)) {
                // console.error("%cace renderer dirty", CONSOLE_WARN_CSS, tabTitle, tabName, renderer.$changes, renderer.$loop.changes, renderer.$loop.pending, renderer.$size.$dirty);
                return false;
            }

            return true;
        }

        function getDocumentView(c9Document) {
            console.log("%cgetDocumentView()", CONSOLE_INFO_CSS, c9Document.name, c9Document.tab.name, c9Document.tab.path);

            if (c9Document.tab.path === undefined) {
                return undefined;
            }

            if (c9Document.tab.editorType !== "ace") {
                return undefined;
            }

            var documentViewInvalid;

            if (!isDocumentViewValid(c9Document)) {
                console.warn("getDocumentView(): document view invalid", c9Document.name, c9Document.tab.name, c9Document.tab.path);
                // console.trace();
                documentViewInvalid = true;
            }

            var c9Session = c9Document.getSession();
            var aceSession = c9Session.session;
            var editor = c9Document.editor;
            var renderer = editor.ace.renderer;

            if (aceSession !== editor.ace.session) {
                console.error("getDocumentView(): mismatching sessions", c9Document.name, c9Document.tab.name, c9Document.tab.path);
                return {
                    "invalid": true
                };
            }

            var lineHeight = renderer.lineHeight;
            var characterWidth = renderer.characterWidth;
            var screenLength = aceSession.getScreenLength();
            var screenWidth = aceSession.getScreenWidth();

            var scrollerHeight = renderer.$size.scrollerHeight;
            var scrollerWidth = renderer.$size.scrollerWidth;

            var topScreenRow = renderer.scrollTop / lineHeight;
            var bottomScreenRow = Math.min((renderer.scrollTop + scrollerHeight) / lineHeight, screenLength);

            var wrapLines = aceSession.getUseWrapMode();
            var wrapType = getWrapType(aceSession);
            var wrapLimit = getWrapLimit(aceSession);

            var lineCount = aceSession.getLength();
            var horizontalPadding = renderer.$padding;
            var columnsWidth = (wrapType === "viewport") ? (scrollerWidth - 2 * horizontalPadding) : scrollerWidth;
            var columnsVisible = columnsWidth / characterWidth;

            if (wrapType === "print-margin") {
                columnsVisible = Math.min(columnsVisible, wrapLimit);
            }

            if (wrapType === "viewport") {
                columnsVisible = wrapLimit;
            }

            function formatFloat(val) {
                return parseFloat(val.toFixed(3));
            }

            var documentView = {
                "invalid": documentViewInvalid,
                "line-count": lineCount,
                "folds": convertFoldsToOneBasedIndex(aceSession.getAllFolds()),
                "editor": {
                    "character-width": characterWidth,
                    "line-height": lineHeight,
                    "screen-width": screenWidth,
                    "screen-length": screenLength,
                    "wrap-type": wrapType,
                    "wrap-limit": wrapLimit,
                    "show-invisibles": editor.getOption("showInvisibles")
                },
                "viewport": {
                    "top": renderer.scrollTop,
                    "left": renderer.scrollLeft,
                    "width": scrollerWidth,
                    "height": scrollerHeight,
                    "horizontal-padding": horizontalPadding,
                    "lines-visible": formatFloat(bottomScreenRow - topScreenRow),
                    "columns-visible": formatFloat(columnsVisible),
                    "vertical-scrollbar-visible": renderer.$vScroll,
                    "horizontal-scrollbar-visible": renderer.$horizScroll
                }
            };

            var visibleText = documentView["visible-text"] = {};

            var partiallyVisibleText = {
                "top-line": formatFloat(Math.ceil(topScreenRow) - topScreenRow),
                "bottom-line": formatFloat(bottomScreenRow - Math.floor(bottomScreenRow))
            };

            if (!wrapLines) {
                var topDocumentLine = aceSession.screenToDocumentRow(Math.ceil(topScreenRow), 0);
                var bottomDocumentLine = aceSession.screenToDocumentRow(Math.floor(bottomScreenRow) - 1, 0);

                visibleText["first-visible-line"] = clamp(1, topDocumentLine + 1, lineCount);
                visibleText["last-visible-line"] = clamp(1, bottomDocumentLine + 1, lineCount);

                var leftColumn = (renderer.scrollLeft - renderer.$padding) / characterWidth;
                var rightColumn = leftColumn + columnsVisible;

                visibleText["first-visible-column"] = clamp(1, Math.ceil(leftColumn) + 1, screenWidth);
                visibleText["last-visible-column"] = clamp(1, Math.floor(rightColumn) - 1 + 1, screenWidth);

                leftColumn = clamp(0, leftColumn, screenWidth);
                rightColumn = clamp(0, rightColumn, screenWidth);

                partiallyVisibleText["left-column"] = formatFloat(Math.ceil(leftColumn) - leftColumn);
                partiallyVisibleText["right-column"] = formatFloat(rightColumn - Math.floor(rightColumn));
            }
            else {
                var firstVisibleCharacterPosition = convertRowColumnToLineColumn(aceSession.screenToDocumentPosition(Math.ceil(topScreenRow), 0));
                var firstVisibleLine = aceSession.getLine(firstVisibleCharacterPosition.line);
                firstVisibleCharacterPosition.column = Math.min(firstVisibleCharacterPosition.column, firstVisibleLine.length - 1);
                visibleText["first-visible-character"] = convertLocationToOneBasedIndex(firstVisibleCharacterPosition);

                var lastVisibleCharacterPosition = convertRowColumnToLineColumn(aceSession.screenToDocumentPosition(Math.floor(bottomScreenRow - 1), Number.MAX_VALUE));
                var lastVisibleLine = aceSession.getLine(lastVisibleCharacterPosition.line);
                lastVisibleCharacterPosition.column = Math.min(lastVisibleCharacterPosition.column, lastVisibleLine.length - 1);
                visibleText["last-visible-character"] = convertLocationToOneBasedIndex(lastVisibleCharacterPosition);
            }

            visibleText["partially-visible-text"] = partiallyVisibleText;

            return documentView;
        }

        function getWorkspaceTreeSettings() {
            var workspaceTreeSettings = {
                "show-open-files": settings.getBool("user/openfiles/@show"),
                "show-workspace-files": !settings.getBool("state/openfiles/@hidetree"),
                "show-file-system": settings.getBool("state/projecttree/@showfs"),
                "show-hidden-files": settings.getBool("user/projecttree/@showhidden")
            };

            return workspaceTreeSettings;
        }

        function getWorkspaceTreeConfiguration(waitForRender, callback) {
            // console.log("getWorkspaceTreeConfiguration()", waitForRender);
            isAceTreeRendererDirty(tree.tree.renderer);
            // console.trace();
            // console.log("getWorkspaceTreeConfiguration()", tree.tree.renderer.$changes, tree.tree.renderer.$loop, tree.tree.renderer.$loop.changes);

            function NodeStatusError(node, message) {
                this.node = node;
                this.message = message;
                this.stack = Error().stack;
            }

            NodeStatusError.prototype = Object.create(Error.prototype);
            NodeStatusError.prototype.name = "NodeStatusError";

            function getTreeConfiguration() {
                // console.log("getTreeConfiguration()", intervalID);
                var aceTree = tree.tree;

                if (aceTree === undefined) {
                    return "error: workspace tree is hidden";
                }

                var cursorNode = tree.selectedNode;
                var expandedPaths = tree.getAllExpanded();

                function isExpandedPath(path) {
                    return expandedPaths.indexOf(path) >= 0;
                }

                function getNodeConfiguration(node) {
                    if (node.status === "loading") {
                        throw new NodeStatusError(node, "'" + node.label + "' is loading");
                    }

                    if ((node.status === "pending") && isExpandedPath(node.path)) {
                        throw new NodeStatusError(node, "expanded node '" + node.label + "' is pending");
                    }

                    var row = aceTree.provider.getIndexForNode(node);
                    var path = node.path;
                    var fsNode = node.isFavorite ? fsCache.findNode(path) : node;

                    if (fsNode === undefined) {
                        // console.warn("getTreeConfiguration(): no fsNode for ", path);
                        // fsCache.findNode(path);
                        fsNode = {};
                    }

                    // console.log(row, node.label, node.path, node.status, aceTree.isNodeVisible(node, 0), aceTree.isNodeVisible(node, 0.5));

                    var nodeConfiguration = {
                        "row": row,
                        "path": path,
                        "label": fsNode.label,
                        "content-type": fsNode.contenttype,
                        // "size": !fsNode.isFolder ? fsNode.size : undefined,
                        // "last-modified": fsNode.mtime,
                        "link": fsNode.link,
                        "folder": node.isFolder === true,
                        "open": node.isFolder ? (node.isOpen === true) : undefined,
                        "selected": node.isSelected === true,
                        "cursor": node === cursorNode ? true : undefined,
                        "partially-visible": aceTree.isNodeVisible(node, 0.5),
                        "fully-visible": aceTree.isNodeVisible(node, 0),
                        "favorite": node.isFavorite,
                        "favorite-path": !node.isFavorite && treeFavorites.isFavoritePath(path) ? true : undefined,
                        "status": node.status
                    };

                    if (nodeConfiguration["open"] && nodeConfiguration["favorite-path"]) {
                        nodeConfiguration["open"] = false;
                    }

                    if (node.isOpen && aceTree.provider.hasChildren(node)) {
                        var children = aceTree.provider.getChildren(node);
                        nodeConfiguration.children = children.map(getNodeConfiguration);
                    }

                    return nodeConfiguration;
                }

                try {
                    var rootNodeChildren = aceTree.provider.getChildren(aceTree.provider.root);
                    return rootNodeChildren.map(getNodeConfiguration);
                }
                catch (ex) {
                    if (ex instanceof NodeStatusError) {
                        return false;
                    }

                    throw ex;
                }
            }

            var intervalID;

            function tryToGetTreeConfiguration() {
                // console.trace("tryToGetTreeConfiguration()", intervalID);
                var workspaceTreeConfiguration = getTreeConfiguration();

                if (workspaceTreeConfiguration === false) {
                    if (!intervalID) {
                        intervalID = setInterval(tryToGetTreeConfiguration, 10);
                    }

                    return;
                }

                if (intervalID) {
                    clearInterval(intervalID);
                    intervalID = undefined;
                }

                callback(workspaceTreeConfiguration);
            }

            if (waitForRender) {
                waitUntilRendered(tree.tree.renderer, isAceTreeRendererDirty, tryToGetTreeConfiguration, "getWorkspaceTreeConfiguration");
            }
            else {
                tryToGetTreeConfiguration();
            }
        }

        function logWorkspaceTreeConfiguration(callback) {
            getWorkspaceTreeConfiguration(true, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                var loadWorkspaceTreeEventProperties = {
                    "settings": getWorkspaceTreeSettings(),
                    "configuration": workspaceTreeConfiguration
                };

                logEvent("load-workspace-tree", null, loadWorkspaceTreeEventProperties);
                callback(workspaceTreeConfiguration);
            });
        }

        function getActiveTabsInfo() {
            var tabs = tabManager.getTabs();
            var activeTabsInfo = [];

            tabs.forEach(function getTabInfo(tab) {
                if (!tab.active) {
                    return;
                }

                var activeTabInfo = {
                    "name": tab.name,
                    "title": tab.title,
                    "path": tab.path,
                    "focused": tab === tabManager.focussedTab,
                    "document-name": tab.document.name,
                    "document-view": getDocumentView(tab.document)
                };

                activeTabsInfo.push(activeTabInfo);
            });

            return activeTabsInfo;
        }

        var writeEventsToLogIntervalID;

        function startLogging() {
            writeEventsToLogIntervalID = setInterval(writeEventsToLog, WRITE_TO_EVENTS_LOG_INTERVAL);

            loggingActive = true;

            logStartLogging();

            var initializationChecks = {
                "c9-ide-ready": false,
                "panels-loaded": false,
                "workspace-tree-loaded": false,
                "tab-manager-ready": false,
                "tabs-loaded": false,
                "documents-loaded": false
            };

            c9.once("ready", function onC9Ready() {
                initializationChecks["c9-ide-ready"] = true;

                var c9IDEReadyEventProperties = {
                    "start-date": c9.startdate,
                    "c9-ide-version": c9.version,
                    "project-name": c9.projectName
                };

                logEvent("c9-ide-ready", null, c9IDEReadyEventProperties);
            });

            c9.on("connect", function onC9Connect() {
                writeEventsToLog();
            }, plugin);

            c9.on("quit", function onC9Quit() {
                var c9IDEClosingEventProperties = {
                    "tab-configuration": getTabsConfiguration(),
                    "active-tabs": getActiveTabsInfo()
                };

                logEvent("c9-ide-closing", null, c9IDEClosingEventProperties);

                stopLogging();
            }, plugin);

            logPanelConfiguration(function afterPanelConfigurationLogged() {
                initializationChecks["panels-loaded"] = true;
            });

            tabManager.once("ready", function onTabManagerReady() {
                // console.log("%ctabManager ready", CONSOLE_INFO_CSS, tabManager.getTabs().length);
                initializationChecks["tab-manager-ready"] = true;
                logDocuments(function afterDocumentsLogged() {
                    initializationChecks["documents-loaded"] = true;
                });
            });

            var initialWorkspaceTreeConfiguration;

            if (panels.isActive("tree")) {
                logWorkspaceTreeConfiguration(function afterLoadWorkspaceTreeLogged(workspaceTreeConfiguration) {
                    initializationChecks["workspace-tree-loaded"] = true;
                    initialWorkspaceTreeConfiguration = workspaceTreeConfiguration;
                });
            }
            else {
                delete initializationChecks["workspace-tree-loaded"];
            }

            var monitorInitializationIntervalID;
            var logTabConfigurationInvoked = false;

            function monitorInitialization() {
                console.log("monitorInitialization", tabManager.getTabs().length, JSON.stringify(initializationChecks));

                if (initializationChecks["tab-manager-ready"] && initializationChecks["documents-loaded"]) {
                    if (!logTabConfigurationInvoked) {
                        logTabConfigurationInvoked = true;

                        logTabsConfiguration(function afterTabsConfigurationLogged() {
                            initializationChecks["tabs-loaded"] = true;
                        });
                    }
                }

                for (var property in initializationChecks) {
                    if (initializationChecks[property] === false) {
                        return;
                    }
                }

                clearInterval(monitorInitializationIntervalID);
                writeEventsToLog();

                console.log("%cInitialization Done. Setting up events logging.", CONSOLE_INFO_CSS);
                setupEventLogging(initialWorkspaceTreeConfiguration);
            }

            monitorInitializationIntervalID = setInterval(monitorInitialization, 10);
        }

        function stopLogging() {
            logStopLogging();
            loggingActive = false;

            function writeEventsToLogWhileStopping() {
                if (writeEventsToLog()) {
                    clearInterval(writeEventsToLogIntervalID);
                }
            }

            clearInterval(writeEventsToLogIntervalID);
            writeEventsToLog();
            writeEventsToLogIntervalID = setInterval(writeEventsToLogWhileStopping, 0);
        }

        function setupEventLogging(workspaceTreeConfiguration) {
            function setupCommandLogging() {
                commands.on("beforeExec", function onBeforeExecCommand(e) {
                    var preExecuteCommandEventProperties = {
                        "command-name": e.command.name,
                        "command-sequence-id": e.sequenceID,
                        "arguments": e.args
                    };

                    logEvent("pre-execute-command", new Date(), preExecuteCommandEventProperties);
                }, plugin);

                commands.on("afterExec", function onAfterExecCommand(e) {
                    var postExecuteCommandEventProperties = {
                        "command-name": e.command.name,
                        "command-sequence-id": e.sequenceID,
                        "arguments": e.args,
                        "return-value": e.returnValue
                    };

                    logEvent("post-execute-command", null, postExecuteCommandEventProperties);

                    if (e.command.name === "save") {
                        logSaveDocument();
                    }
                }, plugin);
            }

            function logSaveDocument() {
                var actionTimestamp = new Date();
                var tab = tabManager.focussedTab;

                if ((tab !== undefined) && isAceTab(tab)) {
                    var saveDocumentEventProperties = {
                        "tab-name": tab.name
                    };

                    var logCodeSummary = userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME].indexOf("save") >= 0;
                    appendEventProperties(saveDocumentEventProperties, getDocumentInfo(tab.document, logCodeSummary));
                    logEvent("save-document", actionTimestamp, saveDocumentEventProperties);
                }
            }

            function setupClipboardLogging() {
                function nativeClipboardEventListener(e) {
                    var actionTimestamp = new Date();

                    var clipboardEventProperties = {
                        "dom-event-timestamp": new Date(e.timeStamp),
                        "clipboard": "native"
                    };

                    if (e.clipboardData) {
                        var types = e.clipboardData.types;

                        if (!Array.isArray(types)) {
                            types = [];
                            for (var i = 0; i < e.clipboardData.types.length; i++) {
                                types[i] = e.clipboardData.types.item(i);
                            }
                        }

                        clipboardEventProperties["data"] = types.map(function getClipboardTypeAndValue(type) {
                            return {
                                "value": e.clipboardData.getData(type),
                                "type": type
                            };
                        });
                    }
                    else if (window.clipboardData) {
                        clipboardEventProperties["data"] = [{
                            "value": window.clipboardData.getData("Text"),
                            "type": "text/plain"
                        }];
                    }

                    logEvent(e.type + "-clipboard", actionTimestamp, clipboardEventProperties);
                }

                apf.addListener(document, "cut", nativeClipboardEventListener, false);
                apf.addListener(document, "copy", nativeClipboardEventListener, false);
                apf.addListener(document, "paste", nativeClipboardEventListener, true);
            }

            function setupPanelLogging() {
                var allPanels = panels.panels;
                Object.keys(allPanels).forEach(function addPanelListeners(name) {
                    var panel = allPanels[name];

                    panel.on("show", function onShowPanel() {
                        var showPanelEventProperties = {
                            "name": name,
                            "caption": panel.button ? panel.button.caption : null
                        };

                        logEvent("show-panel", new Date(), showPanelEventProperties);
                    }, plugin);

                    panel.on("hide", function onHidePanel() {
                        var hidePanelEventProperties = {
                            "name": name,
                            "caption": panel.button ? panel.button.caption : null
                        };

                        logEvent("hide-panel", new Date(), hidePanelEventProperties);
                    }, plugin);
                });
            }

            function setupWorkspaceTreeLogging(workspaceTreeConfiguration) {
                var aceTree = tree.tree;

                var lastState = {
                    "selection": undefined,
                    "expandedPaths": undefined,
                    "workspaceTreeConfigurationJSON": undefined
                };

                function nodeReplacerForStringify(key, value) {
                    if (key === "parent") {
                        return "[" + typeof value + "] ... " + value.path;
                    }

                    if (key === "map" || key === "children") {
                        return "[" + typeof value + "] ...";
                    }

                    return value;
                }

                function getSectionForNode(node) {
                    if (node.path === "!favorites") {
                        return "favorites";
                    }

                    if (node.path === "!fsroot" || node.path === "/") {
                        return "file system";
                    }

                    if (node.parent) {
                        return getSectionForNode(node.parent);
                    }

                    console.warn("getSectionForNode(): unknown section for node", node.path);

                    return "unknown";
                }

                function extractNodeInfo(node) {
                    return {
                        "section": getSectionForNode(node),
                        "path": node.path,
                        "row": aceTree.provider.getIndexForNode(node)
                    };
                }

                function compareNodeInfos(nodeInfo1, nodeInfo2) {
                    return nodeInfo1.row - nodeInfo2.row;
                }

                function extractNodeInfos(nodes) {
                    return nodes.map(extractNodeInfo).sort(compareNodeInfos);
                }

                function isNodeInfoValid(nodeInfo) {
                    var invalid = nodeInfo.row < 0;

                    if (invalid) {
                        console.warn("isNodeInfoValid(): workspace node has invalid row", nodeInfo);
                    }

                    return !nodeInfo.invalid;
                }

                function normalizeSelection(selectedNodes) {
                    var cursorRow = aceTree.provider.getIndexForNode(tree.selectedNode);

                    function addCursorToNodeInfo(nodeInfo) {
                        if (cursorRow === nodeInfo.row) {
                            nodeInfo["cursor"] = true;
                        }
                    }

                    var selectedNodeInfos = extractNodeInfos(selectedNodes);
                    selectedNodeInfos = selectedNodeInfos.filter(isNodeInfoValid);
                    selectedNodeInfos.forEach(addCursorToNodeInfo);
                    return selectedNodeInfos;
                }

                function areSelectionsEqual(selection1, selection2) {
                    if (selection1.length !== selection2.length) {
                        return false;
                    }

                    for (var i = 0; i < selection1.length; i++) {
                        if (selection1[i].section !== selection2[i].section ||
                            selection1[i].path !== selection2[i].path ||
                            selection1[i].cursor !== selection2[i].cursor) {
                            return false;
                        }
                    }

                    return true;
                }

                function updateLastState(workspaceTreeConfiguration) {
                    // console.log("updateLastState()");
                    lastState.selection = normalizeSelection(tree.selectedNodes);
                    lastState.expandedPaths = tree.getAllExpanded().sort();
                    lastState.workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);
                }

                updateLastState(workspaceTreeConfiguration);

                tree.on("rename", function onRenameWorkspaceTreeNode(e) {
                    var actionTimestamp = new Date();

                    // console.log("%cRENAME", CONSOLE_INFO_CSS, e);

                    var renameWorkspaceTreeNodeEventProperties = {
                        "new-path": e.path,
                        "old-path": e.oldpath
                    };

                    logEvent("rename-workspace-tree-node", actionTimestamp, renameWorkspaceTreeNodeEventProperties);
                }, plugin);

                tree.on("delete", function onDeleteWorkspaceTreeNode(e) {
                    var actionTimestamp = new Date();

                    // FIXME: use nodes, not paths
                    var paths = e.selection.map(function extractPathFromNode(node) {
                        return node.path;
                    });

                    var deleteWorkspaceTreeNodesEventProperties = {
                        "paths": paths
                    };

                    logEvent("delete-workspace-tree-nodes", actionTimestamp, deleteWorkspaceTreeNodesEventProperties);
                }, plugin);

                tree.on("select", function onSelectWorkspaceTreeNode(e) {
                    var actionTimestamp = new Date();

                    var selection = normalizeSelection(e.nodes);

                    // console.log("%cSELECT", CONSOLE_INFO_CSS, e.nodes, e.paths, areSelectionsEqual(lastState.selection, selection), JSON.stringify(selection, null, 1));
                    // console.log(JSON.stringify(e.nodes, nodeReplacerForStringify, 1));

                    if (areSelectionsEqual(lastState.selection, selection)) {
                        return;
                    }

                    lastState.selection = selection;

                    var selectWorkspaceTreeNodesEventProperties = {
                        "selection": selection
                    };

                    logEvent("select-workspace-tree-nodes", actionTimestamp, selectWorkspaceTreeNodesEventProperties);
                }, plugin);

                tree.on("expand", function onExpandWorkspaceTreeNode(e) {
                    var actionTimestamp = new Date();

                    var allExpandedPaths = tree.getAllExpanded().sort();
                    if (areObjectsEqual(lastState.expandedPaths, allExpandedPaths)) {
                        return;
                    }

                    lastState.expandedPaths = tree.getAllExpanded().sort();

                    getWorkspaceTreeConfiguration(true, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var expandWorkspaceTreeNodeEventProperties = {
                            "path": e.path,
                            "settings": getWorkspaceTreeSettings(),
                            "configuration": workspaceTreeConfiguration
                        };

                        logEvent("expand-workspace-tree-node", actionTimestamp, expandWorkspaceTreeNodeEventProperties);

                        lastState.workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);
                    });
                }, plugin);

                tree.on("collapse", function onCollapseWorkspaceTreeNode(e) {
                    var actionTimestamp = new Date();

                    var allExpandedPaths = tree.getAllExpanded().sort();
                    if (areObjectsEqual(lastState.expandedPaths, allExpandedPaths)) {
                        return;
                    }

                    lastState.expandedPaths = tree.getAllExpanded().sort();

                    getWorkspaceTreeConfiguration(false, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var collapseWorkspaceTreeNodeEventProperties = {
                            "path": e.path,
                            "settings": getWorkspaceTreeSettings(),
                            "configuration": workspaceTreeConfiguration
                        };

                        logEvent("collapse-workspace-tree-node", actionTimestamp, collapseWorkspaceTreeNodeEventProperties);

                        lastState.workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);
                    });
                }, plugin);

                tree.on("refreshComplete", function onRefreshWorkspaceTree() {
                    var actionTimestamp = new Date();

                    getWorkspaceTreeConfiguration(false, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var refreshWorkspaceTreeEventProperties = {
                            "settings": getWorkspaceTreeSettings(),
                            "configuration": workspaceTreeConfiguration
                        };

                        logEvent("refresh-workspace-tree", actionTimestamp, refreshWorkspaceTreeEventProperties);

                        updateLastState(workspaceTreeConfiguration);
                    });
                }, plugin);

                // var changeCounter = 0;
                var changedNodes = [];

                tree.tree.provider.on("change", function onChangeWorkspaceTreeNode(node) {
                    var actionTimestamp = new Date();

                    if ((node !== undefined) && (changedNodes.indexOf(node) < 0)) {
                        changedNodes.push(node);
                    }

                    // var changeCount = ++changeCounter;

                    // console.log("%cCHANGE", CONSOLE_INFO_CSS, changeCount, changedNodes.length, JSON.stringify(node, nodeReplacerForStringify, 1), node ? node.path : "");

                    getWorkspaceTreeConfiguration(true, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);

                        // console.log("afterWorkspaceTreeConfigurationAvailable", changeCount, changedNodes.length, node !== undefined ? node.path : null);

                        if (workspaceTreeConfigurationJSON !== lastState.workspaceTreeConfigurationJSON) {
                            // console.log("afterWorkspaceTreeConfigurationAvailable !==", changeCount, changedNodes.length);

                            var updateWorkspaceTreeEventProperties = {
                                "updated-nodes": extractNodeInfos(changedNodes),
                                "settings": getWorkspaceTreeSettings(),
                                "configuration": workspaceTreeConfiguration
                            };

                            logEvent("update-workspace-tree", actionTimestamp, updateWorkspaceTreeEventProperties);

                            changedNodes = [];
                            updateLastState(workspaceTreeConfiguration);
                        }
                    });
                });

                tree.tree.provider.on("changeScrollTop", function onScrollWorkspaceTree() {
                    var actionTimestamp = new Date();

                    getWorkspaceTreeConfiguration(false, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var scrollWorkspaceTreeEventProperties = {
                            "settings": getWorkspaceTreeSettings(),
                            "configuration": workspaceTreeConfiguration
                        };

                        logEvent("scroll-workspace-tree", actionTimestamp, scrollWorkspaceTreeEventProperties);

                        lastState.workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);
                    });
                });

                tree.tree.renderer.on("resize", function onResizeWorkspaceTree() {
                    var actionTimestamp = new Date();

                    getWorkspaceTreeConfiguration(false, function afterWorkspaceTreeConfigurationAvailable(workspaceTreeConfiguration) {
                        var resizeWorkspaceTreeEventProperties = {
                            "settings": getWorkspaceTreeSettings(),
                            "configuration": workspaceTreeConfiguration
                        };

                        logEvent("resize-workspace-tree", actionTimestamp, resizeWorkspaceTreeEventProperties);

                        lastState.workspaceTreeConfigurationJSON = JSON.stringify(workspaceTreeConfiguration);
                    });
                });

                var mnuCtxTree = tree.getElement("mnuCtxTree");
                mnuCtxTree.addEventListener("onprop.visible", function onOpenOrCloseWorkspaceTreeContextMenu(e) {
                    var openOrCloseWorkspaceTreeContentMenuEventProperties = {
                        "selection-paths": tree.selection.sort()
                    };

                    var eventType = (e.value ? "open" : "close") + "-workspace-tree-context-menu";
                    logEvent(eventType, new Date(), openOrCloseWorkspaceTreeContentMenuEventProperties);
                });
            }

            function setupTabsLogging() {
                function checkIfTabConfigurationChanged(event) {
                    if (!event) {
                        return;
                    }

                    setTimeout(function warnIfTabConfigurationChanged() {
                        var eventTabConfiguration = event["configuration"];
                        var currentTabConfiguration = getTabsConfiguration();

                        if (!areObjectsEqual(eventTabConfiguration, currentTabConfiguration)) {
                            console.log("checkIfTabConfigurationChanged(): tab configuration changed, event:", event["event-type"], event);
                            // console.log(JSON.stringify(eventTabConfiguration, null, 1));
                            // console.log(JSON.stringify(currentTabConfiguration, null, 1));
                        }
                    }, 0);
                }

                var openTabs = {};

                function setupTabLogging(tab, activateEvent) {
                    // console.log("setupTabLogging()", tab.title, tab.path, activateEvent);

                    var activeTabInfo = null;

                    function tabAfterActivateListener(e) {
                        // console.log("%ctabAfterActivateListener()", CONSOLE_INFO_CSS, e.tab.title, tab.title);

                        // this listener is registered for every tab, so ignore events caused by other tabs
                        if (e.tab !== tab) {
                            return;
                        }

                        console.log("%ctabAfterActivateListener()", CONSOLE_INFO_CSS, e.tab.title, tab.title);

                        var actionTimestamp = new Date();

                        if (tab.document.ready) {
                            documentReady();
                        }
                        else {
                            tab.document.once("ready", documentReady, plugin);
                        }

                        function documentReady() {
                            console.log("documentReady()", tab.title, tab.editorType, tab.editor, tab.editor.ace);

                            if (!isAceTab(tab)) {
                                console.log("%cdocumentReady() / isAceTab() => false", CONSOLE_INFO_CSS);
                                logActivateTabEvent();
                                return;
                            }

                            waitUntilTabRendered(tab, logActivateTabEvent, tab.title + "-activate", setLastDocumentView);

                            function isTabActiveInEditor() {
                                var ace = tab.editor.ace;

                                if (!ace) {
                                    return false;
                                }

                                if (tab.document !== ace.session.c9doc) {
                                    console.warn("isTabActiveInEditor(): ACE document is different");
                                    return false;
                                }

                                return true;
                            }

                            var lastDocumentView;

                            function setLastDocumentView() {
                                var activeInEditor = isTabActiveInEditor();
                                console.log("setLastDocumentView()", tab.title, activeInEditor, tab.active);

                                if (!activeInEditor) {
                                    return true;
                                }

                                var latestDocumentView = getDocumentView(tab.document);
                                var didDocumentViewChange = !areObjectsEqual(lastDocumentView, latestDocumentView);
                                console.log("setLastDocumentView() / changed?", tab.title, didDocumentViewChange); //, didDocumentViewChange ? JSON.stringify(latestDocumentView, null, 1) : "");
                                lastDocumentView = latestDocumentView;
                            }

                            function logActivateTabEvent() {
                                var activeInEditor = isTabActiveInEditor();
                                // console.log("logActivateTabEvent", tab.title, activeInEditor);

                                var activateTabEventProperties = {
                                    "name": tab.name,
                                    "title": tab.title,
                                    "path": tab.path,
                                    "document-name": tab.document.name,
                                    "document-view": activeInEditor ? getDocumentView(tab.document) : lastDocumentView
                                };

                                logEvent("activate-tab", actionTimestamp, activateTabEventProperties);

                                if (tab.active) {
                                    startLoggingActiveTab();
                                }
                            }
                        }
                    }

                    function startLoggingActiveTab() {
                        console.log("startLoggingActiveTab()", tab.title, tab.path, tab.active);

                        if (!tab.active) {
                            console.error("startLoggingActiveTab(): called when tab is not active", tab.title, tab.path, tab.name, tab.active);
                            return;
                        }

                        if (tab.path === undefined) {
                            activeTabInfo = null;
                            return;
                        }

                        activeTabInfo = {};

                        activeTabInfo.editor = tab.document.editor;

                        if (activeTabInfo.editor) {
                            activeTabInfo.editor.on("resize", resizeEditorListener, plugin);

                            activeTabInfo.lastClientDimensions = getClientDimensions();

                            activeTabInfo.ace = activeTabInfo.editor.ace;
                        }

                        if (activeTabInfo.ace) {
                            activeTabInfo.ace.on("beforeEndOperation", beforeEndOperationListener);

                            var selection = activeTabInfo.ace.getSelection().toJSON();
                            activeTabInfo.lastCursorJSON = JSON.stringify(normalizeCursor(selection));
                            activeTabInfo.lastSelectionJSON = JSON.stringify(normalizeSelection(selection));

                            activeTabInfo.aceSession = activeTabInfo.ace.session;
                        }

                        if (activeTabInfo.aceSession) {
                            activeTabInfo.aceSession.on("changeScrollTop", changeScrollPositionListener);
                            activeTabInfo.aceSession.on("changeScrollLeft", changeScrollPositionListener);
                        }

                        // console.log("activate / lastCursorJSON", activeTabInfo.lastCursorJSON);
                    }

                    function stopLoggingActiveTab() {
                        // console.log("stopLoggingActiveTab()", tab.title, tab.path, tab.active);

                        if (tab.path === undefined) {
                            return;
                        }

                        if (activeTabInfo === null) {
                            console.warn("stopLoggingActiveTab(): activeTabInfo is null");
                            return;
                        }

                        if (activeTabInfo.editor) {
                            activeTabInfo.editor.off("resize", resizeEditorListener);
                        }

                        if (activeTabInfo.ace) {
                            activeTabInfo.ace.off("beforeEndOperation", beforeEndOperationListener);
                        }

                        if (activeTabInfo.aceSession) {
                            activeTabInfo.aceSession.off("changeScrollTop", changeScrollPositionListener);
                            activeTabInfo.aceSession.off("changeScrollLeft", changeScrollPositionListener);
                        }

                        activeTabInfo = null;
                    }

                    function getClientDimensions() {
                        var htmlNode = tab.aml.$pHtmlNode;
                        return {
                            "width": htmlNode.clientWidth,
                            "height": htmlNode.clientHeight
                        };
                    }

                    var resizeEditorActionTimestamps = [];
                    var resizeEditorClientDimensions = [];

                    function resizeEditorListener() {
                        var clientDimensions = getClientDimensions();
                        // console.log("resizeEditorListener", tab.title, resizeEditorActionTimestamps.length, activeTabInfo.lastClientDimensions, clientDimensions, areObjectsEqual(activeTabInfo.lastClientDimensions, clientDimensions));
                        // console.log("resizeEditorListener", tab.document.editor, activeTabInfo.editor === tab.editor, activeTabInfo.editor === tab.document.editor);

                        if (areObjectsEqual(activeTabInfo.lastClientDimensions, clientDimensions)) {
                            return;
                        }

                        activeTabInfo.lastClientDimensions = clientDimensions;

                        resizeEditorActionTimestamps.push(new Date());
                        resizeEditorClientDimensions.push(clientDimensions);

                        if (resizeEditorActionTimestamps.length > 1) {
                            return;
                        }

                        if (!isAceTab(tab)) {
                            logResizeTab();
                            return;
                        }

                        waitUntilTabRendered(tab, logResizeTab, tab.title + "-resize");

                        function logResizeTab() {
                            // console.log("logResizeTab()", tab.title);

                            var resizeTabEventProperties = {
                                "dimensions": resizeEditorClientDimensions.slice(),
                                "name": tab.name,
                                "title": tab.title,
                                "path": tab.path,
                                "document-name": tab.document.name,
                                "document-view": getDocumentView(tab.document),
                                "configuration": getTabsConfiguration()
                            };

                            var resizeTabEvent = logEvent("resize-tab", resizeEditorActionTimestamps.slice(), resizeTabEventProperties);
                            checkIfTabConfigurationChanged(resizeTabEvent);

                            resizeEditorActionTimestamps = [];
                            resizeEditorClientDimensions = [];
                        }
                    }

                    function beforeEndOperationListener() {
                        var ace = activeTabInfo.ace;
                        if (ace.curOp && ace.curOp.selectionChanged) {
                            // var selection = ace.getSelection();
                            // var json = selection.toJSON();
                            // console.log("beforeEndOperation()", normalizeCursor(json));
                            // console.log(JSON.stringify(json, null, 1));
                            logChangeCursor();
                            logChangeSelection();
                        }
                    }

                    function logChangeCursor() {
                        var currentCursor = normalizeCursor(activeTabInfo.ace.getSelection().toJSON());
                        var currentCursorJSON = JSON.stringify(currentCursor);

                        // console.log("logChangeCursor():", currentCursorJSON, activeTabInfo.lastCursorJSON);

                        if (currentCursorJSON === activeTabInfo.lastCursorJSON) {
                            return;
                        }

                        activeTabInfo.lastCursorJSON = currentCursorJSON;

                        var changeCursorEventProperties = {
                            "cursor": currentCursor,
                            "tab-name": tab.name,
                            "path": tab.path,
                            "document-name": tab.document.name
                        };

                        // console.log("%cchange-cursor", "background: #FFF899", currentCursorJSON);
                        logEvent("change-cursor", new Date(), changeCursorEventProperties);
                    }

                    function logChangeSelection() {
                        var currentSelection = normalizeSelection(activeTabInfo.ace.getSelection().toJSON());
                        var currentSelectionJSON = JSON.stringify(currentSelection);

                        // console.log("logChangeSelection():", currentSelectionJSON, activeTabInfo.lastSelectionJSON);

                        if (currentSelectionJSON === activeTabInfo.lastSelectionJSON) {
                            return;
                        }

                        activeTabInfo.lastSelectionJSON = currentSelectionJSON;

                        var changeSelectionEventProperties = {
                            "selection": currentSelection,
                            "document-name": tab.document.name,
                            "tab-name": tab.name,
                            "path": tab.path
                        };

                        // console.log("%cchange-selection", "background: #FFF899", currentSelectionJSON);
                        logEvent("change-selection", new Date(), changeSelectionEventProperties);
                    }

                    var changeScrollPositionActionTimestamps = [];
                    var changeScrollPositionScrollPositions = [];

                    function changeScrollPositionListener() {
                        // console.log("changeScrollPositionListener", tab.path, changeScrollPositionActionTimestamps.length);

                        if (openDocuments[tab.document.name] === undefined) {
                            console.warn("changeScrollPositionListener(): unopened document", tab.document.name, tab.path, Object.keys(openDocuments).toString());
                            return;
                        }

                        var aceSession = activeTabInfo.aceSession;

                        changeScrollPositionActionTimestamps.push(new Date());
                        changeScrollPositionScrollPositions.push({
                            "top": aceSession.getScrollTop(),
                            "left": aceSession.getScrollLeft()
                        });

                        if (changeScrollPositionActionTimestamps.length > 1) {
                            return;
                        }

                        var waiting = waitUntilTabRendered(tab, logChangeScrollPosition, tab.title + "-scroll");
                        if (!waiting) {
                            changeScrollPositionActionTimestamps = [];
                        }

                        function logChangeScrollPosition() {
                            var changeScrollPositionEventProperties = {
                                "scroll-positions": changeScrollPositionScrollPositions.slice(),
                                "tab-name": tab.name,
                                "path": tab.path,
                                "document-name": tab.document.name,
                                "document-view": getDocumentView(tab.document)
                            };

                            logEvent("change-scroll-position", changeScrollPositionActionTimestamps.slice(), changeScrollPositionEventProperties);

                            changeScrollPositionActionTimestamps = [];
                            changeScrollPositionScrollPositions = [];
                        }
                    }

                    function deactivateTabListener() {
                        // console.log("%cdeactivateTabListener() / deactivate-tab", CONSOLE_INFO_CSS, tab.title, tab.active);
                        var actionTimestamp = new Date();

                        var deactivateTabEventProperties = {
                            "name": tab.name,
                            "title": tab.title,
                            "path": tab.path,
                            "document-name": tab.document.name,
                            "document-view": getDocumentView(tab.document)
                        };

                        logEvent("deactivate-tab", actionTimestamp, deactivateTabEventProperties);

                        stopLoggingActiveTab();
                    }

                    if (activateEvent) {
                        tabAfterActivateListener(activateEvent);
                    }
                    else if (tab.active) {
                        startLoggingActiveTab();
                    }

                    tabManager.on("tabAfterActivateSync", tabAfterActivateListener, plugin);
                    tab.on("deactivate", deactivateTabListener, plugin);

                    openTabs[tab.name] = {
                        "tabAfterActivateListener": tabAfterActivateListener,
                        "deactivateTabListener": deactivateTabListener
                    };
                }

                function cleanupTabLogging(tab) {
                    // console.log("cleanupTabLogging()", tab.title);

                    var tabListeners = openTabs[tab.name];

                    if (!tabListeners) {
                        console.warn("cleanupTabLogging(): no tabListeners to unregister", tab.path, tab.title);
                        return;
                    }

                    tabManager.off("tabAfterActivateSync", tabListeners.tabAfterActivateListener);
                    tab.off("deactivate", tabListeners.deactivateTabListener);

                    delete openTabs[tab.name];
                }

                var initialTabs = tabManager.getTabs();
                // console.log("setupTabLogging initial tabs count", initialTabs.length);
                initialTabs.forEach(function setupTab(tab) {
                    setupTabLogging(tab);
                });

                var focusedTabInfo = null;

                function startLoggingFocusedTab(tab) {
                    // console.log("%cstartLoggingFocusedTab()", CONSOLE_INFO_CSS, tab.title, tab.document.name);

                    if (tab.path === undefined) {
                        console.error("startLoggingFocusedTab(): tab.path is undefined", tab.document.name, tab.name);
                        return;
                    }

                    if (openDocuments[tab.document.name] === undefined) {
                        console.warn("startLoggingFocusedTab(): unopened document", tab.document.name, tab.path, Object.keys(openDocuments).toString());
                        return;
                    }

                    var ace = tab.document.editor.ace;
                    if (!ace) {
                        console.warn("startLoggingFocusedTab(): invalid ace", tab.document.name, tab.path, Object.keys(openDocuments).toString());
                        return;
                    }

                    function changeDocumentListener(delta) {
                        // console.log("changeDocumentListener()");

                        var actionTimestamp = new Date();

                        var value = tab.document.value;

                        var syntax = modelist.getModeForPath(tab.path).name;
                        var logCodeSummary = userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME].indexOf("change") >= 0;

                        var changeDocumentEventProperties = {
                            "name": tab.document.name,
                            "path": tab.path,
                            "syntax": syntax,
                            "length": value.length,
                            "code-summary": (logCodeSummary && (syntax === "javascript")) ? summarizeCode(value) : undefined,
                            "action": delta.action,
                            "start": convertLocationToOneBasedIndex(delta.start),
                            "end": convertLocationToOneBasedIndex(delta.end),
                            "lines": delta.lines
                        };

                        logEvent("change-document", actionTimestamp, changeDocumentEventProperties);
                    }

                    function changeFoldListener(e) {
                        var actionTimestamp = new Date();

                        var fold = {
                            "start": convertLocationToOneBasedIndex(e.data.start),
                            "end": convertLocationToOneBasedIndex(e.data.end)
                        };

                        var folds = convertFoldsToOneBasedIndex(ace.getSession().getAllFolds());

                        waitUntilTabRendered(tab, logChangeFold, tab.title + "-change-fold");

                        function logChangeFold() {
                            var documentView = getDocumentView(tab.document);
                            if (documentView && !areObjectsEqual(folds, documentView["folds"])) {
                                documentView["invalid"] = true;
                            }

                            var changeFoldEventProperties = {
                                "action": e.action,
                                "fold": fold,
                                "folds": folds,
                                "tab-name": tab.name,
                                "path": tab.path,
                                "document-name": tab.document.name,
                                "document-view": documentView
                            };

                            logEvent("change-fold", actionTimestamp, changeFoldEventProperties);
                        }
                    }

                    function changeWrapModeListener() {
                        // console.log("%cchangeWrapModeListener", CONSOLE_INFO_CSS, tab.title); //, aceSession.getOption("wrap"), getWrapType(aceSession), aceSession.getWrapLimit());
                        var actionTimestamp = new Date();

                        waitUntilTabRendered(tab, logChangeWrapMode, tab.title + "-change-wrap-mode-" + Date.now());

                        function logChangeWrapMode() {
                            var aceSession = ace.getSession();
                            // console.log("logChangeWrapMode", aceSession.getOption("wrap"), getWrapType(aceSession), aceSession.getWrapLimit());

                            // isDocumentViewValid(tab.document);

                            var changeWrapModeEventProperties = {
                                "wrap-type": getWrapType(aceSession),
                                "wrap-limit": getWrapLimit(aceSession),
                                "tab-name": tab.name,
                                "path": tab.path,
                                "document-name": tab.document.name,
                                "document-view": getDocumentView(tab.document)
                            };

                            logEvent("change-wrap-mode", actionTimestamp, changeWrapModeEventProperties);
                        }
                    }

                    function changeWrapLimitListener() {
                        // console.log("%cchangeWrapLimitListener", CONSOLE_INFO_CSS, tab.title); //, aceSession.getOption("wrap"), getWrapType(aceSession), aceSession.getWrapLimit());
                        var actionTimestamp = new Date();

                        waitUntilTabRendered(tab, logChangeWrapLimit, tab.title + "-change-wrap-limit");

                        function logChangeWrapLimit() {
                            var aceSession = ace.getSession();
                            // console.log("logChangeWrapLimit", tab.title, aceSession.getOption("wrap"), getWrapType(aceSession), aceSession.getWrapLimit());

                            // isDocumentViewValid(tab.document);

                            var changeWrapLimitEventProperties = {
                                "wrap-type": getWrapType(aceSession),
                                "wrap-limit": getWrapLimit(aceSession),
                                "tab-name": tab.name,
                                "path": tab.path,
                                "document-name": tab.document.name,
                                "document-view": getDocumentView(tab.document)
                            };

                            logEvent("change-wrap-limit", actionTimestamp, changeWrapLimitEventProperties);
                        }
                    }

                    focusedTabInfo = {
                        "tab": tab,
                        "aceSession": ace.getSession(),
                        "aceSessionListeners": {
                            "change": changeDocumentListener,
                            "changeFold": changeFoldListener,
                            "changeWrapMode": changeWrapModeListener,
                            "changeWrapLimit": changeWrapLimitListener
                        }
                    };

                    for (var key in focusedTabInfo.aceSessionListeners) {
                        focusedTabInfo.aceSession.on(key, focusedTabInfo.aceSessionListeners[key]);
                    }
                }

                function stopLoggingFocusedTab() {
                    // console.log("%cstopLoggingFocusedTab()", CONSOLE_INFO_CSS, focusedTabInfo ? focusedTabInfo.tab.title : null);

                    if (focusedTabInfo === null) {
                        console.warn("stopLoggingFocusedTab(): focusedTabInfo is null");
                        return;
                    }

                    for (var key in focusedTabInfo.aceSessionListeners) {
                        focusedTabInfo.aceSession.off(key, focusedTabInfo.aceSessionListeners[key]);
                    }

                    focusedTabInfo = null;
                }

                var focusedTab = tabManager.focussedTab;
                if (focusedTab && isAceTab(focusedTab)) {
                    startLoggingFocusedTab(focusedTab);
                }

                tabManager.on("tabCreate", function onTabCreate(e) {
                    var actionTimestamp = new Date();
                    // console.log("%ctabCreate", CONSOLE_INFO_CSS, e.tab.title, e.tab.name);

                    if (initialTabs.indexOf(e.tab) >= 0) {
                        return;
                    }

                    var createTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path,
                        "configuration": getTabsConfiguration()
                    };

                    var createTabEvent = logEvent("create-tab", actionTimestamp, createTabEventProperties);
                    checkIfTabConfigurationChanged(createTabEvent);

                    if (openTabs[e.tab.name] === undefined) {
                        setupTabLogging(e.tab);
                    }
                }, plugin);

                tabManager.on("open", function onTabOpen(e) {
                    console.log("%copen", CONSOLE_INFO_CSS, e.tab.title);
                    var actionTimestamp = new Date();

                    if (e.tab.path === undefined) {
                        return;
                    }

                    // var openDocumentTimerLabel = "open-document-" + e.tab.title;
                    // console.time(openDocumentTimerLabel);

                    var c9Document = e.tab.document;
                    openDocuments[c9Document.name] = c9Document;

                    var openDocumentEventProperties = {
                        "tab-name": e.tab.name
                    };

                    var logCodeSummary = userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME].indexOf("open") >= 0;
                    appendEventProperties(openDocumentEventProperties, getDocumentInfo(c9Document, logCodeSummary));
                    logEvent("open-document", actionTimestamp, openDocumentEventProperties);

                    // console.timeEnd(openDocumentTimerLabel);

                    if (!focusedTabInfo || (focusedTabInfo.tab !== e.tab)) {
                        if (isAceTab(e.tab)) {
                            startLoggingFocusedTab(e.tab);
                        }
                    }
                }, plugin);

                tabManager.on("tabAfterActivateSync", function onTabAfterActivate(e) {
                    // console.log("%ctabAfterActivateSync", CONSOLE_INFO_CSS, e.tab.title);
                    if (openTabs[e.tab.name] === undefined) {
                        // The tabManager emits the "tabAfterActivateSync" event before the "tabCreate" event.
                        // Until that bug is fixed:
                        //  * call setupTabLogging() with the event ("e") as the second argument,
                        //      which will log the tab-activate event
                        //  * the following warning message is unnecessary
                        // console.warn("onTabAfterActivate(): tabAfterActivateSync event for unopened tab:", e.tab.name);
                        setupTabLogging(e.tab, e);
                    }
                }, plugin);

                function onTabAfterClose(e) {
                    // console.time("close-document");

                    console.log("%ctabAfterClose / close-document", CONSOLE_INFO_CSS, e.tab.title);

                    var actionTimestamp = new Date();

                    if (e.tab.path === undefined) {
                        return;
                    }

                    delete openDocuments[e.tab.document.name];

                    var closeDocumentEventProperties = {
                        "tab-name": e.tab.name
                    };

                    var logCodeSummary = userSettings[CODE_SUMMARY_LOGGING_SETTING_NAME].indexOf("close") >= 0;
                    appendEventProperties(closeDocumentEventProperties, getDocumentInfo(e.tab.document, logCodeSummary));
                    logEvent("close-document", actionTimestamp, closeDocumentEventProperties);
                    // console.timeEnd("close-document");
                }

                tabManager.on("tabAfterClose", onTabAfterClose, plugin);

                tabManager.on("tabDestroy", function onTabDestroy(e) {
                    // console.log("%ctabDestroy / close-tab", CONSOLE_INFO_CSS, e.tab.title, openDocuments, openTabs, e.tab.active, openTabs[e.tab.name].deactivateTabListener);

                    if (e.tab.active) {
                        console.error("%conTabDestroy(): tabDestroy event received for an active tab", CONSOLE_ERROR_CSS, e.tab.document.name, e.tab.path, e.tab.active);
                        // The tab has not been deactivated. Deactivate it now to generate log event and unregister listeners.
                        openTabs[e.tab.name].deactivateTabListener();
                    }

                    if (openDocuments[e.tab.document.name] !== undefined) {
                        console.error("%conTabDestroy(): tabDestroy event received for an open document", CONSOLE_ERROR_CSS, e.tab.document.name, e.tab.path);
                        // The tab's document was not closed. Close it now to generate log event.
                        onTabAfterClose(e);
                    }

                    var actionTimestamp = new Date();

                    var closeTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path,
                        "configuration": getTabsConfiguration()
                    };

                    // var closeTabEvent = logEvent("close-tab", actionTimestamp, closeTabEventProperties);
                    // checkIfTabConfigurationChanged(closeTabEvent);

                    cleanupTabLogging(e.tab);
                }, plugin);

                tabManager.on("focusSync", function onTabFocus(e) {
                    // console.log("%cfocusSync", CONSOLE_INFO_CSS, e.tab.title);

                    var focusTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path
                    };

                    logEvent("focus-tab", new Date(), focusTabEventProperties);

                    // The Cloud9 IDE tabManager emits the "focusSync" event before the "open" event.
                    // Until that bug is fixed do not call startLoggingFocusedTab() when the document is not yet open.
                    // The "open" event listener will call startLoggingFocusedTab() instead.
                    if (openDocuments[e.tab.document.name] !== undefined) {
                        if (isAceTab(e.tab)) {
                            startLoggingFocusedTab(e.tab);
                        }
                    }
                }, plugin);

                tabManager.on("blur", function onTabBlur(e) {
                    // console.log("%conTabBlur / blur-tab", CONSOLE_INFO_CSS, e.tab.title);

                    var blurTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path
                    };

                    logEvent("blur-tab", new Date(), blurTabEventProperties);

                    if (isAceTab(e.tab)) {
                        stopLoggingFocusedTab();
                    }
                }, plugin);

                tabManager.on("tabOrder", function onTabOrder(e) {
                    var actionTimestamp = new Date();

                    var reorderTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path,
                        "next-tab": e.next ? {
                            "name": e.next ? e.next.name : null,
                            "title": e.next ? e.next.title : null,
                            "path": (e.next && (e.next.path !== undefined)) ? e.next.path : null
                        } : null,
                        "configuration": getTabsConfiguration()
                    };

                    var reorderTabEvent = logEvent("reorder-tab", actionTimestamp, reorderTabEventProperties);
                    checkIfTabConfigurationChanged(reorderTabEvent);
                }, plugin);

                tabManager.on("tabAfterReparent", function onTabAfterReparent(e) {
                    var actionTimestamp = new Date();

                    if (e.pane.name === e.lastPane.name) {
                        return;
                    }

                    var reparentTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path,
                        "new-parent-pane-name": e.pane.name,
                        "old-parent-pane-name": e.lastPane.name,
                        "configuration": getTabsConfiguration()
                    };

                    var reparentTabEvent = logEvent("reparent-tab", actionTimestamp, reparentTabEventProperties);
                    checkIfTabConfigurationChanged(reparentTabEvent);
                }, plugin);

                var initialPanes = tabManager.getPanes();

                tabManager.on("paneCreate", function onPaneCreate(e) {
                    // console.log("%cpaneCreate", CONSOLE_INFO_CSS, e.pane.name);
                    var actionTimestamp = new Date();

                    if (initialPanes.indexOf(e.pane) >= 0) {
                        return;
                    }

                    var createPaneEventProperties = {
                        "name": e.pane.name,
                        "configuration": getTabsConfiguration()
                    };

                    var createPaneEvent = logEvent("create-pane", actionTimestamp, createPaneEventProperties);
                    checkIfTabConfigurationChanged(createPaneEvent);
                }, plugin);

                tabManager.on("paneDestroy", function onPaneDestroy(e) {
                    var actionTimestamp = new Date();

                    var destroyPaneEventProperties = {
                        "name": e.pane.name,
                        "configuration": getTabsConfiguration()
                    };

                    var destroyPaneEvent = logEvent("destroy-pane", actionTimestamp, destroyPaneEventProperties);
                    checkIfTabConfigurationChanged(destroyPaneEvent);
                }, plugin);

                tabManager.on("reload", function onTabReload(e) {
                    var reloadTabEventProperties = {
                        "name": e.tab.name,
                        "title": e.tab.title,
                        "path": e.tab.path
                    };

                    logEvent("reload-tab", new Date(), reloadTabEventProperties);
                }, plugin);

                c9Console.on("resize", function onConsoleResize() {
                    var actionTimestamp = new Date();

                    setTimeout(function logResizeConsole() {
                        var resizeConsoleEventProperties = {
                            "dimensions": {
                                "width": c9Console.container.getWidth(),
                                "height": c9Console.container.getHeight()
                            },
                            "opened": settings.getBool("state/console/@expanded"),
                            "maximized": settings.getBool("state/console/@maximized"),
                            "normal-height": settings.getNumber("state/console/@height")
                        };

                        logEvent("resize-console", actionTimestamp, resizeConsoleEventProperties);
                    });
                }, plugin);
            }

            setupCommandLogging();
            setupClipboardLogging();
            setupPanelLogging();

            if (workspaceTreeConfiguration === undefined) {
                tree.once("ready", function onWorkspaceTreeReady() {
                    // console.log("workspace tree ready");
                    logWorkspaceTreeConfiguration(function afterLoadWorkspaceTreeLogged(workspaceTreeConfiguration) {
                        setupWorkspaceTreeLogging(workspaceTreeConfiguration);
                    });
                });
            }
            else {
                setupWorkspaceTreeLogging(workspaceTreeConfiguration);
            }

            setupTabsLogging();
        }

        plugin.on("load", load);

        plugin.on("unload", function unload() {
            stopLogging();
            loaded = false;
        });

        plugin.freezePublicAPI({
            "logEvent": logEvent
        });

        register(null, {
            "cryolite": plugin
        });
    }
});
