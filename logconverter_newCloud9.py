import os
import sys
import subprocess
import multiprocessing
import json
import shutil
import sqlite3
import datetime
from fileUtils import fileUtils

# sql utilities for parsing pfislog, pfislog's output is insert statements which are SQL
import sqlparse
from sqlparse.sql import Parenthesis
from sqlparse.sql import IdentifierList  # instead of parsing by hand

# other classes
from fQNUtils import FQNUtils

# CREATE TABLE logger_log ( id INTEGER IDENTITY, user VARCHAR(50), timestamp DATETIME, action VARCHAR(50), target VARCHAR, referrer VARCHAR, agent VARCHAR(50));
# what each insert statement in pfig is made up of
PFIS_ID = '1'
PFIS_USER = 'c486980a-74df-40a1-b4eb-07ff1c1dff93'
PFIS_TIMESTAMP = '2014-03-14 09:34:58.231000'
PFIS_ACTION = 'Variable declaration'
PFIS_TARGET = 'com.blah.blah'  # varies depending on the event
PFIS_REFERRER = 'com.blah.blah.blah'  # varies depending on the event
PFIS_AGENT = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'

GET_VARIANT_OUTPUT = 'SELECT output FROM variant_output WHERE variant=?'

# Global Variables
rootdir = './jsparser/src/hexcom'
src_list = [name for name in os.listdir("./jsparser/src/hexcom") if os.path.isdir(os.path.join(
    "./jsparser/src/hexcom", name))]
DEBUG = True
miv_array = []
opened_doc_list = []
doc_line_list = []

variant_output_db = None

def print_list(to_print):
    """Sorts a list and prints it out with an asterisk in front of each one
    """
    organized = list(to_print)
    organized.sort()

    for item in organized:
        print '* ' + item


def print_dict(to_print):
    sorted_keys = list(to_print.keys())
    sorted_keys.sort()
    for item in sorted_keys:
        print '* ' + item + ': ' + str(to_print[item])


'''pretty prints a json dump'''


def jsonprettyprint(event):
    print json.dumps(event, sort_keys=True, indent=4, separators=(',', ':'))


class TimeFormatConverter:
    PFIS3_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
    CRYOLOG_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'  # NOTE: there is a 'T' hardcoded in the cryolog strings

    def __init__(self, start_time):
        self.start_time = start_time

    def convert_cryolog_to_pfis_time_fmt(self, cryolog_fmt_time_string, increment_timestamp):
        # crylog time example format = '2014-04-01T20:43:06.803Z'
        generic_time = TimeFormatConverter.get_time_obj_from_cryo_fmt(cryolog_fmt_time_string)

        # PFIS3 format : 2010-01-25 00:00:00.000
        if increment_timestamp:
            generic_time = generic_time + datetime.timedelta(milliseconds=1)

        pfis3_time = generic_time.strftime(TimeFormatConverter.PFIS3_FORMAT)
        elapsed_time = generic_time - self.start_time

        return [pfis3_time, elapsed_time]

    def get_time_obj_from_pfis_fmt(self, pfis_fmt_timestamp):
        print "pfis time format", pfis_fmt_timestamp
        return datetime.datetime.strptime(pfis_fmt_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def get_time_obj_from_cryo_fmt(cryo_fmt_timestamp):
        # crylog time example format = '2014-04-01T20:43:06.803Z'
        # remove the 'Z' from the cryolog timestamp
        time_str = cryo_fmt_timestamp.split('Z')[0]
        generic_time = datetime.datetime.strptime(time_str, TimeFormatConverter.CRYOLOG_FORMAT)

        return generic_time


class Cryolog:
    """Represents a cryolite log file.
    Each json node in the log file is an event in the events variable.
    """

    def __init__(self, filename):
        """Open the cryolog and create a list of events (json nodes)."""
        f = open(filename)
        self.events = []  # empty list for the event json nodes on each line of the log
        for line in f.readlines():
            # load the json from the line of the file
            node = json.loads(line)

            # add it to the list
            self.events.append(node)
        f.close()
        self.start_time = TimeFormatConverter.get_time_obj_from_cryo_fmt(self.events[0]['logged-timestamp']);

    def get_event_types(self):
        # create a set which will keep event_types unique
        event_types = set()
        for event in events:
            event_types.add(event['event-type'])
        return event_types


class Pfislog:
    """Represents a pfis log file.
    Each insert statement is converted to a dictionary of values and added to the events variable.
    """

    PFIS_LOG_FORMAT = "INSERT INTO LOGGER_LOG VALUES({id}, '{user}','{timestamp}', '{action}', '{target}', '{referrer}', '{agent}', '{elapsed_time}');\r\n"

    def __init__(self, filename=None, events=None):
        """Open the Pfislog and create a list of insert statements, or take a list of events."""
        self.current_id = 1

        if events:
            self.events = events
        elif filename:
            self.events = []

            f = open(filename)
            for line in f.readlines():
                if 'INSERT' not in line:
                    continue  # don't care about anything other than insert statements
                result = sqlparse.parse(line)  # returns a list
                statement = result[0]

                # what we really care about is what's being inserted, get the values
                parens = next(token for token in statement.tokens if isinstance(token, Parenthesis))
                identifiers = next(token for token in parens.tokens if isinstance(token, IdentifierList))
                values = []  # each item in the VALUES parenthesis
                for item in identifiers.get_identifiers():
                    values.append(item.value.strip('\''))  # strip because I want values, not strings with quotes

                # create a dict with the values
                event = dict()
                event['id'] = values[0]
                event['user'] = values[1]
                event['timestamp'] = values[2]
                event['action'] = values[3]
                event['target'] = values[4]
                event['referrer'] = values[5]
                event['agent'] = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
                event['elapsed_time'] = values[6]
                self.events.append(event)

    def export_to_file(self, filename):
        """Write a series of insert statements created from the events variable to a file.
        Uses the PFIS_LOG_FORMAT variable to generate the insert statements.
        """
        f = open(filename, 'w')
        line = self.PFIS_LOG_FORMAT.format(
            id="-1",
            user="-1",
            timestamp="-1",
            action="Language",
            target="JavaScript",
            referrer="-1",
            agent="-1",
            elapsed_time="-1"
        )
        f.write(line)
        for event in self.events:

            if (isinstance(event, str)):
                pass
            elif event == None:
                pass
            else:
                # print event
                line = self.PFIS_LOG_FORMAT.format(
                    id=event['id'],
                    user=event['user'],
                    timestamp=event['timestamp'],
                    action=event['action'],
                    target=event['target'],
                    referrer=event['referrer'],
                    agent=event['agent'],
                    elapsed_time=event['elapsed_time']
                )
                f.write(line)

        f.close()


class Converter:
    """Converts a cryolog to a pfislog.
    Creates the list of pfislog events and returns a Pfislog object containing them.
    """

    def __init__(self, timeConverter):
        self.current_id = 1
        self.time_converter = timeConverter

        # these variables are necessary for some 'slightly stateful' evaluation of the cryolog events
        # if the ast count has changed between events and the document name is the same, we know that
        # a code change was made that affected the ast so we can mark a pfig event with ast_affected
        # example action: 'Java element changed ast_affected '
        self.current_document_name = ''
        self.current_document_ast_node_count = 0

    def get_declaration_events_if_applicable(self, event):
        global opened_doc_list

        document_name = self.get_document_name_for_event(event)

        if (document_name in opened_doc_list):
            return None
        if (document_name[-2:] != 'js' and document_name[-3:] != 'txt' and
                    '[B]' not in document_name and '.output' not in document_name):
            return None
        else:
            opened_doc_list.append(document_name)
            method_declaration_events = self.convert_open_document_event(event, document_name)
            return method_declaration_events

    def get_document_name_for_event(self, event):
        document_name = None
        if 'path' in event.keys():
            document_name = event['path']
        elif 'title' in event.keys():
            document_name = event['title']
        else:
            raise Exception("Invalid event document name: ", event)

        #Normalize output patch name
        if document_name.endswith('.html') and ('[B]' in document_name or '[P]' in document_name):
            document_name = document_name.replace('[B]', '')
            document_name = document_name.replace('[P]', '')
            document_name = document_name.replace('index.html', 'index.html.output')
            document_name = document_name.strip()

        if '/hexcom' in document_name:
            # This is to normalize paths when participant opened file in browser,
            # and path has the server name in the URL.
            position = document_name.index('/hexcom')
            document_name = document_name[position:]

        return document_name


    def new_event(self, event, increment_timestamp=False):
        """Creates an event with a new id and initializes boilerplate variables."""
        new_event = dict()
        new_event['id'] = self.current_id
        new_event['user'] = PFIS_USER

        if ('action-timestamp' in event):
            cryolog_time = event['action-timestamp']
        elif ('logged-timestamp' in event):
            cryolog_time = event['logged-timestamp']

        pfis_time = self.time_converter.convert_cryolog_to_pfis_time_fmt(cryolog_time, increment_timestamp)
        new_event['timestamp'] = pfis_time[0]
        new_event['elapsed_time'] = pfis_time[1]
        new_event['agent'] = PFIS_AGENT

        self.current_id += 1
        return new_event

    """Cryolog Event Converters (1:1 mapping to Cryolog event-types, for the most part)"""

    def convert_change_cursor_event(self, event, setToBeginning = False):
        """The event when someone clicks a different place in the code"""
        document_name = self.get_document_name_for_event(event)

        if 'hexcom' not in document_name:
            return None

        new_events = []
        change_cursor_event = self.new_event(event)

        if setToBeginning:
            line=0
            column=0
        else:
            line = event['position']['line']
            column = event['position']['column']

        offset = 0

        doc_prev_len = len(opened_doc_list)
        method_declartion_events = self.get_declaration_events_if_applicable(event)

        doc_curr_len = len(opened_doc_list)
        # add one millisecond from time if this is the first time a document has been opened.
        # This is because there is no initial text selection event upon opening a file, so this navigation occurs AFTER the particpant sees the methods, etc.
        if (doc_curr_len > doc_prev_len):
            change_cursor_event['timestamp'] = str(
                datetime.datetime.strptime(change_cursor_event['timestamp'], "%Y-%m-%d %H:%M:%S.%f") +
                datetime.timedelta(microseconds=50))
        change_cursor_event['referrer'] = offset
        change_cursor_event['action'] = 'Text selection offset'
        change_cursor_event['target'] = document_name
        sum = self.get_offset_position(document_name, line, column)

        if (sum is not None):
            change_cursor_event['referrer'] = sum
            new_events.append(change_cursor_event)

            if (method_declartion_events is not None):
                new_events.extend(method_declartion_events)

        return new_events

    def convert_change_document_event(self, event):
        """When the user edits code"""
        document_name = self.get_document_name_for_event(event)

        if 'hexcom' not in document_name:
            return None

        new_event = self.new_event(event)
        code_summary = event['code-summary']
        ast_node_count = code_summary['ast-node-count']

        action = 'Java element changed'
        if self.current_document_name != document_name:
            self.current_document_name = document_name
            self.current_document_ast_node_count = ast_node_count
        else:
            # mark the element changed event with ast_affected if the node count of the ast has changed
            if self.current_document_ast_node_count != ast_node_count:
                action += ' ast_affected'
                self.current_document_ast_node_count = ast_node_count

        new_event['action'] = action
        new_event['target'] = document_name
        new_event['referrer'] = os.path.basename(document_name)

        return new_event

    def get_offset_position(self, document_name, line, column):

        if "changes.txt" in document_name:
            sum = fileUtils.getOffset(self, rootdir, document_name, line, column)
            return sum

        elif '.output' in document_name:
            return 0

        elif (".js" in document_name):
            sum = 0
            for item in doc_line_list:
                if (item['file'] == document_name):
                    for i in range(0, line):
                        if (i == line - 1):
                            sum += column
                        else:
                            sum += item['len'][i]
                    return sum

    def convert_change_selection_event(self, event):
        """When the user highlights code"""
        document_name = self.get_document_name_for_event(event)
        if 'hexcom' not in document_name:
            return None

        new_event = self.new_event(event)
        doc_prev_len = len(opened_doc_list)
        new_events = self.get_declaration_events_if_applicable(event)
        doc_curr_len = len(opened_doc_list)
        # add one millisecond from time if this is the first time a document has been opened.
        # This is because there is no initial text selection event upon opening a file, so this navigation occurs AFTER the particpant sees the methods, etc.
        if (doc_curr_len > doc_prev_len):
            new_event['timestamp'] = str(
                datetime.datetime.strptime(new_event['timestamp'], "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(
                    milliseconds=+1))
        new_event['action'] = 'Text selection'
        new_event['target'] = document_name

        lines = []
        f = open(rootdir + "/" + document_name, 'r')  # Open the file the user is in
        # Read the log of the event to get the start and end line then read the file the user is in through the relevant range
        if (event['selection'] == []):
            pass
        else:
            for x in range((event['selection'][0]['start']['line']), (event['selection'][0]['end']['line'])):
                lines.append(FQNUtils.normalizer(f.readline()))
        referrer = ''
        for line in lines:
            referrer += line
        f.close()
        new_event['referrer'] = referrer

        # new_event['referrer'] = 'Cryolog does not capture what text is selected, only lines and columns of start and end positions' #figure out what text is selected
        if (new_events == None):
            new_events = new_event
        else:
            new_events.append(new_event)
        return new_events

    def convert_start_logging_event(self, event):
        """This is when the logger starts logging"""
        new_event = self.new_event(event)

        new_event['action'] = 'Begin'
        new_event['target'] = ''
        new_event['referrer'] = ''

        return new_event

    def convert_tab_event(self, event, action):
        """Converts a tab event (create/activate/deactivate/close) to the pfislog action
        passed in (Part opened/activated/deactivated/closed).
        """
        document_name = self.get_document_name_for_event(event)

        if 'hexcom' not in document_name:
            return None

        new_event = self.new_event(event)
        new_event['action'] = action
        new_event['target'] = os.path.basename(document_name)
        new_event['referrer'] = document_name
        return new_event

    def convert_open_document_event(self, event, document_name):
        """Parses the code in an open-document event into a JavaScript AST and
        recurses through every node creating pfislog events for variable and function
        nodes. Queues the click events and adds them after other events have been
        generated because PFIS can't handle the natural order of events.
        """

        def getOutputContent(outputFileName):
            variant_name = FQNUtils.getVariantName(outputFileName)

            conn = sqlite3.connect(variant_output_db)
            if conn is None:
                raise Exception("No output DB file in project directory: ", variant_output_db)

            c = conn.cursor()
            c.execute(GET_VARIANT_OUTPUT, [variant_name])
            content = None
            for row in c:
                content = row[0]
            c.close()
            conn.close()
            return content

        def normalizer(s):
            if s != None:
                s = FQNUtils.normalizer(s)
            else:
                s = ''
            return s

        def get_events_on_newly_opened_document(event_type, target, referrer):
            new_event = self.new_event(event, increment_timestamp=True)
            new_event['action'] = event_type
            new_event['referrer'] = referrer
            new_event['target'] = target
            return new_event

        def event_tuple_generate(new_events, self, item, event, declaration_type, document_name):

            if (declaration_type == 'Changelog declaration'):
                declaration_file = normalizer(item["src"])
                nesting_path = normalizer(item["filepath"])
                header = normalizer(item["header"])

                methodFQN = FQNUtils.getFullMethodPath(declaration_file, nesting_path, header)
                contents = normalizer(item["contents"])

                new_event = get_events_on_newly_opened_document(declaration_type, FQNUtils.getFullClassPath(declaration_file), methodFQN)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                scent_event_type = declaration_type + ' scent'
                new_event = get_events_on_newly_opened_document(scent_event_type, methodFQN, contents)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                return new_events

            if (declaration_type == "Method declaration" or declaration_type == "Variable declaration"):
                declaration_file = normalizer(item["src"])
                nesting_path = normalizer(item["filepath"])
                header = normalizer(item["header"])

                methodFQN = FQNUtils.getFullMethodPath(declaration_file, nesting_path, header)
                contents = normalizer(item["contents"])

                new_event = get_events_on_newly_opened_document(declaration_type,
                                                                FQNUtils.getFullClassPath(declaration_file), methodFQN)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                offset_event_type = declaration_type + ' offset'
                new_event = get_events_on_newly_opened_document(offset_event_type, methodFQN, item["start"])
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                length_event_type = declaration_type + ' length'
                new_event = get_events_on_newly_opened_document(length_event_type, methodFQN, item["length"])
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                scent_event_type = declaration_type + ' scent'
                new_event = get_events_on_newly_opened_document(scent_event_type, methodFQN, contents)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                return new_events

            if (declaration_type == "Method invocation"):
                invoking_file = normalizer(item["src"])
                invocation_path_within_file = normalizer(item["filepath"])
                header = normalizer(item["header"])

                contents = normalizer(item["contents"])
                invoked_method_fqn = normalizer(item["invsrc"])

                invoking_method_fqn = FQNUtils.getFullMethodPath(invoking_file, invocation_path_within_file, header)

                new_event = get_events_on_newly_opened_document(declaration_type, invoking_method_fqn,
                                                                invoked_method_fqn)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                offset_event_type = declaration_type + ' offset'
                new_event = get_events_on_newly_opened_document(offset_event_type, invoked_method_fqn, item["start"])
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                length_event_type = declaration_type + ' length'
                new_event = get_events_on_newly_opened_document(length_event_type, invoked_method_fqn, item["length"])
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                scent_event_type = declaration_type + ' scent'
                new_event = get_events_on_newly_opened_document(scent_event_type, invoked_method_fqn, contents)
                FQNUtils.addFQNPrefixForEvent(new_event)
                new_events.append(new_event)

                return new_events

        new_events = []
        function_list = []
        call_list = []
        var_dec_list = []

        if 'hexcom' not in document_name:
            return None

        if 'changes.txt' in document_name:
            declaration_type = 'Changelog declaration'
            changelogMessage = fileUtils.getChangelogFromDb(document_name)

            item = dict()
            item['src'] = document_name
            item['start'] = 0
            item['end'] = len(changelogMessage)
            item['length'] = len(changelogMessage)
            item['filepath'] = 'u\''
            item['header'] = ''
            item['contents'] = changelogMessage

            return event_tuple_generate(new_events, self, item, event, declaration_type, document_name)

        elif '.output' in document_name:

            declaration_type = 'Output declaration'
            declarationEvent = get_events_on_newly_opened_document(declaration_type, document_name, document_name)
            FQNUtils.addFQNPrefixForEvent(declarationEvent)

            declaration_type = 'Output declaration scent'
            output_content = getOutputContent(document_name)
            scentEvent = get_events_on_newly_opened_document(declaration_type, document_name, output_content)
            FQNUtils.addFQNPrefixForEvent(scentEvent)

            return self.append_event([declarationEvent, scentEvent], new_events)

        else:
            # Add declarations after nav to first location, only after nav can a person see what's in there.
            # This is a PFIS assumption
            for item in miv_array:

                if (item['functions'] == None):
                    pass
                else:
                    function_list += item['functions']
                if (item['invocations'] == None):
                    pass
                else:
                    call_list += item['invocations']

                    # if(item['variables'] ==None):
                    # pass
                    # else:
                    # var_dec_list += item['variables']
            declaration_type = 'Method declaration'
            for item in function_list:
                if (item['src'] == document_name):
                    new_events = event_tuple_generate(new_events, self, item, event, declaration_type, document_name)

            declaration_type = 'Method invocation'
            for item in call_list:
                if (item['src'] == document_name):
                    new_events = event_tuple_generate(new_events, self, item, event, declaration_type, document_name)

            declaration_type = 'Variable declaration'
            for item in var_dec_list:
                if (item['src'] == document_name):
                    new_events = event_tuple_generate(new_events, self, item, event, declaration_type, document_name)

            return new_events

    def convert_select_workspace_tree_nodes_event(self, event):

        def getPaths(evt):
            selections = event['selection']
            paths = [s["path"] for s in selections]
            return paths

        """When the user actually selects a node"""
        new_events = []
        paths = getPaths(event)
        # paths = paths.replace('/', '\\')

        for path in paths:
            new_event = self.new_event(event)
            new_event['action'] = 'Package Explorer tree selection'
            new_event['target'] = path  # this needs to be formatted to match pfig, which has a crazy format
            new_event['referrer'] = ''

            new_events.append(new_event)

        return new_events

    def convert_update_workspace_tree_event(self, event):
        """update-workspace-tree has a 1:M mapping to pfislog events because
        of the tree structure being represented in one clean JSON node.
        """
        new_events = []
        workspace_tree_configuration = event['workspace-tree-configuration']
        path = workspace_tree_configuration['path']
        children = workspace_tree_configuration['children']
        for child in children:
            # each child is a node in the tree, which in pfig is a separate event
            new_event = self.new_event(event)
            new_event['action'] = 'Package Explorer tree'
            new_event['target'] = child['label']  # label in a child node in cryolog appears to be the filename
            new_event['referrer'] = path  # this is the root path in the workspace tree event

            new_events.append(new_event)
        return new_events

    def append_event(self, new, new_events):
        if new == None:
            return new_events
        elif 'target' in new:
            new_events.append(new)
        else:
            new_events.extend(new)
        return new_events

    def convert_cryolog_to_pfislog(self, cryolog):
        """Iterates through cryolog events and calls the appropriate converter
        functions for each type of event.
        These map to every type of event that we are converting.
        """
        new_events = []
        queued_cryolog_events = []
        unconverted_events = dict()

        for event in cryolog.events:
            print str(event['sequence-id']) + " " + event['event-type'] + " " + event['logged-timestamp']

            if (('title' in event.keys()) and (event['title'] in ["Immediate", "Terminal", "Preferences"])):
                pass
            if (('path' in event) and ('searchresults' in event['path'])):
                pass
            else:
                event_type = event['event-type']
                if event_type == 'activate-tab':
                    new_events = self.append_event(self.convert_tab_event(event, 'Part activated'), new_events)
                    new_events = self.append_event(self.convert_change_cursor_event(event, setToBeginning=True), new_events)

                elif event_type == 'change-document':
                    # TODO: Now: SS, BP: Revisit and add js check if things break
                    if (event['syntax'] in ['text', 'css', 'html']):
                        pass
                    else:
                        document_name = event['path']
                        action = event['action']
                        text = ""
                        if action == "insert" or action == "remove":
                            for i in range(0, len(event['lines']) - 1):
                                text += event['lines'][i] + '\n'
                            text += event['lines'][-1]
                        elif action == "insertLines" or action == "removeLines":
                            lines = event['lines']
                            for line in lines:
                                text = text + "\n" + line
                        line = event['start']['line']
                        column = event['start']['column']
                        new_events = self.append_event(self.convert_change_document_event(event), new_events)
                        update_file(document_name, action, text, line, column)
                        array_gen_single_folder(document_name)
                        new_events = self.append_event(self.convert_open_document_event(event, document_name), new_events)

                elif event_type == 'close-tab':
                    new_events = self.append_event(self.convert_tab_event(event, 'Part closed'), new_events)
                elif event_type == 'create-tab':
                    if 'path' in event:
                        new_events = self.append_event(self.convert_tab_event(event, 'Part opened'), new_events)
                elif event_type == 'deactivate-tab':
                    new_events = self.append_event(self.convert_tab_event(event, 'Part deactivated'), new_events)
                elif event_type == 'change-cursor':
                    new_events = self.append_event(self.convert_change_cursor_event(event), new_events)
                elif event_type == 'change-selection':
                    new_events = self.append_event(self.convert_change_selection_event(event), new_events)
                elif event_type == 'start-logging':
                    new_events = self.append_event(self.convert_start_logging_event(event), new_events)
                elif event_type == 'copy-workspace-directory':
                    copy_dir(event['paths'][0], event['paths'][1])
                    add_dir_to_miv(event['paths'][1])
                elif event_type == 'select-workspace-tree-nodes':
                    new_events = self.append_event(self.convert_select_workspace_tree_nodes_event(event), new_events)
                elif event_type == 'update-workspace-tree':
                    # new_events = self.check_keys(self.convert_update_workspace_tree_event(event),new_events)
                    pass
                # keep track of the events that are not converted and how many instances occur
                if event_type in unconverted_events:
                    unconverted_events[event_type] += 1
                else:
                    unconverted_events[event_type] = 1

        print 'Converted {0} cryolog events to {1} pfislog events.\n'.format(len(cryolog.events), len(new_events))
        print 'There were {0} unique unconverted event types:'.format(len(unconverted_events))

        print_dict(unconverted_events)
        new_pfislog = Pfislog(events=new_events)
        return new_pfislog


def copy_dir(old, new):
    old = rootdir + old
    new = rootdir + new
    if (not (os.path.isdir(new)) and os.path.isdir(old)):
        shutil.copytree(old, new)


def update_file(file_path, actionType, text, line_number, column):
    # open file and read in string
    if file_path.startswith("/"):
        f1 = file_path[1:]
    else:
        f1 = file_path

    file = open(rootdir + "/" + f1, "r")
    i = 0
    sum = 0
    for line in file:
        if i == line_number - 1:
            sum += column
            break
        sum += len(line)
        i += 1
    file.seek(0)
    contents = file.read()
    file.close()

    # calculate position
    cur_line = 1
    cur_index = 0
    while (cur_index < len(contents)):
        if (contents[cur_index] == "\n"):
            cur_line = cur_line + 1
        if (cur_line == line_number):
            break
        cur_index = cur_index + 1
        # column numbers in log not zero indexed
    index = cur_index + column - 1
    # print "Index: %d" % index
    # print "Contents before index: %s" % contents[:index]
    # print "text - " +text
    # print "Contents after index: %s" % contents[index:]
    # print actionType
    # print contents
    # print "updated contents"
    if actionType == "insert" or actionType == "insertLines":
        # insert text into string
        updated_contents = contents[:sum - 1] + text + contents[sum - 1:]
        # print updated_contents[sum-20:sum+20]
    else:
        # skip over deleted text while copying string
        updated_contents = contents[:sum - 1] + contents[(sum - 1 + len(text)):]
        # print updated_contents

    # write updated string to file
    file = open(rootdir + "/" + file_path, "w")
    file.write(updated_contents)
    file.close()


def get_array(dir, out_file):
    if dir not in ['.c9', '.cryolite']:
        f = ''
        if (out_file):
            f = open(out_file, 'a')
        dir_to_run = "./jsparser/src/hexcom/" + dir
        out = subprocess.check_output(["php", "./jsparser/fileIterator.php", dir_to_run])

        if (out_file):
            f.write(out)
            f.close()
        else:
            return out

            # call(["php", "fileIterator.php", dir_to_run]);


def add_dir_to_miv(fn):
    # print "adding " + fn + " to miv"
    k = fn.rfind('/')
    # print k
    global miv_array
    global doc_line_list
    # print "sending " + fn[k:] + " as an arg to get_array"
    new_data = json.loads(get_array(fn[k:], None))
    # print "got new data"
    lengths = new_data[-1]
    new_data.pop()
    for item in lengths['lengths']:
        doc_line_list.append(item)
    for item in new_data:
        miv_array.append(item)


def array_gen_single_folder(fn):
    k = fn.rfind('/')
    global miv_array
    global doc_line_list
    new_data = json.loads(get_array(fn[len('/hexcom/'):k], None))
    lengths = new_data[-1]
    new_data.pop()
    for item in lengths['lengths']:
        i = 0
        for doc in doc_line_list:
            if (doc['file'] == item['file']):
                doc_line_list[i] = item
                break
            i = i + 1
    for item in new_data:
        i = 0
        for doc in miv_array:
            if ((doc['functions'] != [] and item['functions'] != []) and (
                item['functions'][0]['src'] == doc['functions'][0]['src'])):
                for j in range(0, len(item['functions'])):
                    item['functions'][j]['start'] += 1
                    item['functions'][j]['end'] += 1
                miv_array[i] = item

            i = i + 1


def array_gen(fn):
    i = 0
    if (os.path.isfile("fullAST.txt") == False):

        while (i <= len(src_list) - 4):
            # print str(i) + src_list[i]
            p = multiprocessing.Process(target=get_array, args=(src_list[i], fn + '1.txt',))
            p.start()
            q = multiprocessing.Process(target=get_array, args=(src_list[i + 1], fn + '2.txt',))
            q.start()
            r = multiprocessing.Process(target=get_array, args=(src_list[i + 2], fn + '3.txt',))
            r.start()
            s = multiprocessing.Process(target=get_array, args=(src_list[i + 3], fn + '4.txt',))
            s.start()
            p.join()
            if (i + 1 < len(src_list)):
                q.join()
            if (i + 2 < len(src_list)):
                r.join()
            if (i + 3 < len(src_list)):
                s.join()
            i = i + 4
        results = []
        f = open(fn + '1.txt', 'r')
        for line in f:
            results.append(json.loads(line))

        f = open(fn + '2.txt', 'r')
        for line in f:
            results.append(json.loads(line))

        f = open(fn + '3.txt', 'r')
        for line in f:
            results.append(json.loads(line))

        f = open(fn + '4.txt', 'r')
        for line in f:
            results.append(json.loads(line))

        lengths = []
        folder_arrays = []
        for singleFolderArray in results:
            lengths.append(singleFolderArray[-1])
            singleFolderArray.pop()
            folder_arrays.append(singleFolderArray)

        compressedLengths = []
        for x in lengths:
            if x:
                compressedLengths.extend(x["lengths"])
        lengths = {}
        lengths["lengths"] = compressedLengths
        master = [[]]
        for x in folder_arrays:
            master[0].extend(x)
        master.append(lengths)
        global miv_array
        miv_array = master
        f = open("fullAST.txt", 'a+')
        f.write(json.dumps(miv_array))
    else:
        f = open("fullAST.txt", 'r')
        miv_array = json.loads(f.read())
    global doc_line_list

    doc_line_list = miv_array.pop()
    doc_line_list = doc_line_list["lengths"]
    miv_array = miv_array[0]  # collapse the array


def create_db(pfislog_name):
    f = open(pfislog_name, 'r')
    db_name = pfislog_name[:-4] + '.db'
    if (os.path.exists(db_name)):
        os.remove(db_name)
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute(
        'create table logger_log("index" int(10), user varchar(50), timestamp varchar(50), action varchar(50), target varchar(50), referrer varchar(50), agent varchar(50), elapsed_time varchar(50));')
    conn.commit()
    for line in f:
        c.execute(line)
    conn.commit()
    c.close()


if __name__ == '__main__':
    variant_output_db = 'variants-output.db'
    cryolog = Cryolog(sys.argv[2])
    timeConverter = TimeFormatConverter(cryolog.start_time)
    converter = Converter(timeConverter)
    array_gen(sys.argv[1])
    pfislog = converter.convert_cryolog_to_pfislog(cryolog)
    pfislog.export_to_file(sys.argv[3])
    create_db(sys.argv[3])