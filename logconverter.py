import os
import sys
import ast
import time
import pprint
import subprocess
import httplib,urllib
import multiprocessing
import simplejson, json 
from jsonmerge import Merger
from Naked.toolshed.shell import execute_js, muterun_js
# imports for JSON and for communication with PHP site that Charles made

# import methods for communication with JS script


# sql utilities for parsing pfislog, pfislog's output is insert statements which are SQL
import sqlparse
from sqlparse.sql import Parenthesis
from sqlparse.sql import IdentifierList # instead of parsing by hand

# What I was using BEFORE Charles' code existed
# JavaScript code utilities for parsing ASTs out of Cryolog's code snippets
# https://pypi.python.org/pypi/slimit 
#from slimit import ast
#from slimit.parser import Parser

# CREATE TABLE logger_log ( id INTEGER IDENTITY, user VARCHAR(50), timestamp DATETIME, action VARCHAR(50), target VARCHAR, referrer VARCHAR, agent VARCHAR(50));
# what each insert statement in pfig is made up of
PFIS_ID = '1'
PFIS_USER = 'c486980a-74df-40a1-b4eb-07ff1c1dff93'
PFIS_TIMESTAMP = '2014-03-14 09:34:58.231000000'
PFIS_ACTION = 'Variable declaration'
PFIS_TARGET = 'com.blah.blah' # varies depending on the event
PFIS_REFERRER = 'com.blah.blah.blah' # varies depending on the event
PFIS_AGENT = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
DEBUG = True
miv_array = []
opened_doc_list = []
doc_line_list = []
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
    
    print json.dumps(event,sort_keys=True, indent=4, separators=(',',':'))
class Cryolog:
    """Represents a cryolite log file. 
    Each json node in the log file is an event in the events variable.
    """

    def __init__(self, filename):
        """Open the cryolog and create a list of events (json nodes)."""
        f = open(filename)
        self.events = [] # empty list for the event json nodes on each line of the log
        for line in f.readlines():
            # load the json from the line of the file
            node = json.loads(line)
 
            # add it to the list
            self.events.append(node)
        f.close()

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

    PFIS_LOG_FORMAT = "INSERT INTO LOGGER_LOG VALUES({id}, '{user}','{timestamp}', '{action}', '{target}', '{referrer}', '{agent}');\r\n"

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
                    continue # don't care about anything other than insert statements
                result = sqlparse.parse(line) # returns a list
                statement = result[0]

                # what we really care about is what's being inserted, get the values 
                parens = next(token for token in statement.tokens if isinstance(token, Parenthesis))
                identifiers = next(token for token in parens.tokens if isinstance(token, IdentifierList))
                values = [] # each item in the VALUES parenthesis
                for item in identifiers.get_identifiers():
                    values.append(item.value.strip('\'')) # strip because I want values, not strings with quotes

                # create a dict with the values
                event = dict()
                event['id'] = values[0]
                event['user'] = values[1]
                event['timestamp'] = values[2]
                event['action'] = values[3]
                event['target'] = values[4]
                event['referrer'] = values[5]
                event['agent'] = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
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
            agent="-1"
            )
        f.write(line)    
        for event in self.events:
            
            if(isinstance(event, str)):
                pass
            else:
                print event
                line = self.PFIS_LOG_FORMAT.format( 
                    id=event['id'],
                    user=event['user'],
                    timestamp=event['timestamp'],
                    action=event['action'],
                    target=event['target'],
                    referrer=event['referrer'],
                    agent=event['agent']
                )
                f.write(line)
     
        f.close()

class Converter:
    """Converts a cryolog to a pfislog. 
    Creates the list of pfislog events and returns a Pfislog object containing them.
    """
    def check_doc_opened(self,event,document_name):
        new_events = []
        global opened_doc_list
        print document_name
        if(document_name in opened_doc_list):
            return
        if(document_name[-2:] !='js'):
            return 
        else:
            opened_doc_list.append(document_name)
            print "going into convert_open_document_event"
            new_events = self.convert_open_document_event(event,document_name)
            return new_events
    def __init__(self):
        self.current_id = 1

        # these variables are necessary for some 'slightly stateful' evaluation of the cryolog events
        # if the ast count has changed between events and the document name is the same, we know that
        # a code change was made that affected the ast so we can mark a pfig event with ast_affected
        # example action: 'Java element changed ast_affected '
        self.current_document_name = ''
        self.current_document_ast_node_count = 0

    def new_event(self, event):
        """Creates an event with a new id and initializes boilerplate variables."""
        new_event = dict()
        new_event['id'] = self.current_id
        new_event['user'] = PFIS_USER

        # crylog time example format = '2014-04-01T20:43:06.803Z'
        # pfis time example format = '2014-03-14 09:34:15.406000000'


        cryolog_time = event['logged-timestamp']

        # remove the 'Z' from the cryolog timestamp
        cryolog_time = cryolog_time.split('Z')[0]

        # see https://docs.python.org/2.7/library/datetime.html#strftime-strptime-behavior
        # for info on these formats
        cryolog_format = '%Y-%m-%dT%X' # NOTE: there is a 'T' hardcoded in the cryolog strings
        generic_time = time.strptime(cryolog_time.split('.')[0], cryolog_format)
        generic_milliseconds = cryolog_time.split('.')[1]

        pfis_format = '%Y-%m-%d %X.'
        pfis_time = time.strftime(pfis_format, generic_time)

        # milliseconds must be handled manually
        # just use the numbers from cryolog and add zeros at the end up to nine digits
        pfis_time += generic_milliseconds.ljust(9, '0')

        new_event['timestamp'] = pfis_time
        new_event['agent'] = PFIS_AGENT

        self.current_id += 1

        return new_event

    """Cryolog Event Converters (1:1 mapping to Cryolog event-types, for the most part)"""
    def convert_change_cursor_event(self, event):
        """The event when someone clicks a different place in the code"""
        new_event = self.new_event(event)
        document_name = event['path']
        position = event['position'] 
        line = position['line'] 
        column = position['column'] 
        
        #We don't have information about the code when converting this event. Needs to be calculated with Charles' code. 
        offset = 0
        document_name = event['path']
        new_events = self.check_doc_opened(event,document_name)
        new_event['referrer'] = offset
        new_event['action'] = 'Text selection offset'
        new_event['target'] = document_name
        sum = self.get_offset_position(document_name, line, column)
        if(sum == -1 or sum == None):
            print("document not found. setting offset to 0")
            exit()
            new_event['referrer'] = 0
        else:
            new_event['referrer'] = sum
        
        if(new_events == None):
            new_events = new_event
        else:
            new_events.append(new_event)
        return new_events

    def convert_change_document_event(self, event):
        """When the user edits code"""
        new_event = self.new_event(event)
        document_name = event['path']
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
        sum = 0    
 
        for item in doc_line_list:
            if(item['file'] == document_name):
                print "get offset position:"
                print item['len']
                for i in range(0, line):
                    if(i == line - 1):
                        sum += column
                    else:
                        sum += item['len'][i]
                return sum
                
    def convert_change_selection_event(self, event):
        jsonprettyprint(event)
        #exit()
        """When the user highlights code"""
        new_event = self.new_event(event)
        document_name = event['path']
        new_events = self.check_doc_opened(event,document_name)
        new_event['action'] = 'Text selection'
        new_event['target'] = document_name

        lines=[]
	f = open(rootdir+ "/"+event['path'], 'r')#Open the file the user is in
        #Read the log of the event to get the start and end line then read the file the user is in through the relevant range 
        if(event['selection'] == []):
            pass
        else: 
            for x in range((event['selection'][0]['start']['line']), (event['selection'][0]['end']['line'])):
                lines.append(f.readline())
        
        f.close()
        new_event['referrer'] = lines
        
        #new_event['referrer'] = 'Cryolog does not capture what text is selected, only lines and columns of start and end positions' #figure out what text is selected
        if(new_events == None):
            new_events = new_event
        else:
            new_events.append(new_event)
        return new_events

    def convert_expand_workspace_tree_node_event(self, event):
        """When the user is clicking through the package tree - don't need to worry about this - TODO: ???"""
        new_event = self.new_event(event)
        path = event['path']
        
        # The slashes in PFIG are the other way for some reason...
        path = path.replace('/', '\\')
            
        new_event['action'] = 'Package Explorer tree expanded'
        new_event['target'] = path 
        new_event['referrer'] = 'There are no packages in javascript'

        return new_event

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

        new_event = self.new_event(event)
        print event
        if('path' in event.keys()):
            document_name = event['path']
        else:
            document_name = event['title']
	
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
        def normalizer(s):
            s = s.replace('\r\n', '\u00a')
            s = s.replace("\n", "\u00a")
            s = s.replace("\r", "\u00a")
            s = s.replace("'", "''")
            s = s.replace(",", "\",\"")
            return s
            
        def event_tuple_generate(new_events,self,item,event,declaration_type,document_name):
            header = normalizer(item["header"])
            filepath = normalizer(item["src"])
            if("invsrc" in item.keys()):
                invsrc = normalizer(item["invsrc"])
            contents = normalizer(item["contents"])
            if(declaration_type == "Method declaration" or declaration_type == "Variable declaration"):
                #declaration
                new_event = self.new_event(event)
                new_event['action'] = declaration_type
                new_event['target'] = filepath
                new_event['referrer'] = filepath + ';.' +header
                new_events.append(new_event)
                
            if(declaration_type == "Method invocation"):
                #invocation
                new_event = self.new_event(event)
                new_event['action'] = declaration_type
                
                new_event['target'] = filepath + ';.'+ header
                new_event['referrer'] = invsrc; 
                new_events.append(new_event)
                
            # create the offset event
            new_event = self.new_event(event)
            new_event['action'] = declaration_type + ' offset'
            new_event['target'] = filepath + ';.' +header
            new_event['referrer'] = item["start"] 
            new_events.append(new_event)

            #create the length event
            new_event = self.new_event(event)
            new_event['action'] = declaration_type + ' length'
            new_event['target'] = filepath + ';.' +header
            new_event['referrer'] = item["length"]
            new_events.append(new_event)
            
            if(declaration_type == "Method declaration" or declaration_type == "Method invocation"):
                new_event = self.new_event(event)
                new_event['action'] = declaration_type + ' scent'
                new_event['target'] =  filepath + ';.' +header
                new_event['referrer'] = contents
                new_events.append(new_event)
                
            return new_events
        
        new_events = []
        function_list = []
        call_list = []
        var_dec_list = []
        x = 0
        for item in miv_array:
             
            if(item['functions'] ==None):
                pass
            else:
                function_list += item['functions']
            if(item['invocations'] ==None):
                pass
            else:
                call_list += item['invocations']
            #if(item['variables'] ==None):
                #pass
            #else:
                #var_dec_list += item['variables']
        declaration_type = 'Method declaration'
        for item in function_list:
            if(item['src']==document_name):
                new_events = event_tuple_generate(new_events,self,item,event,declaration_type,document_name)
            
        declaration_type = 'Method invocation'
        for item in call_list:
            if(item['src']==document_name):
                new_events = event_tuple_generate(new_events,self,item,event,declaration_type,document_name)
            
        declaration_type = 'Variable declaration'
        for item in var_dec_list:
            if(item['src']==document_name):
                new_events = event_tuple_generate(new_events,self,item,event,declaration_type,document_name)
        return new_events


    def convert_select_workspace_tree_nodes_event(self, event):
        """When the user actually selects a node"""
        new_events = []
        paths = event['paths']
        #paths = paths.replace('/', '\\')
        
        for path in paths:
            new_event = self.new_event(event)
            new_event['action'] = 'Package Explorer tree selection'
            new_event['target'] = path    # this needs to be formatted to match pfig, which has a crazy format
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
        
    def check_keys(self,new, new_events):
        if 'target' in new:
            new_events.append(new)
        else:
            new_events.extend(new)
        return new_events
        
    def convert_cryolog_to_pfislog(self, cryolog):
        """Iterates through cryolog events and calls the approprate converter
        functions for each type of event. 
        These map to every type of event that we are converting.
        """
        new_events = []
        queued_cryolog_events = []
        unconverted_events = dict()
        k = 'title'
        for event in cryolog.events:
            print str(event['sequence-id']) + " " + event['event-type']
            if((k in event) and ((event['title'] in ["Immediate","Terminal","Preferences"]) or "[P]" in event['title'])):
                pass
            if(('path' in event) and event['path'][-2:] != 'js'):
                pass
            else:    
                event_type = event['event-type']
                if event_type == 'activate-tab':
                    new_events = self.check_keys(self.convert_tab_event(event, 'Part activated'),new_events)
                elif event_type == 'change-document':
                    if(event['syntax'] in ['text','css', 'html']):
                        pass
                    else:
                        document_name = event['path']
                        action = event['action']
                        text = ""
                        print event['lines']
                        if action == "insert" or action == "remove":
                            for i in range(0,len(event['lines'])-1):
                                text+=event['lines'][i]+'\n'
                            text+=event['lines'][-1]
                        elif action == "insertLines" or action == "removeLines":
                            lines = event['lines']
                            for line in lines:
                                text = text + "\n" + line
                        line = event['start']['line']
                        column = event['start']['column']
                        new_events = self.check_keys(self.convert_change_document_event(event),new_events)
                        print event
                        update_file(document_name, action, text, line, column)
                        array_gen_single_folder(event['path'])
                        '''for doc in doc_line_list:
                            if(doc['file']  == event['path']):
                                print "main Loop:"
                                print doc
                        f = open("./jsparser/src" + event['path'],'r')
                        lines = []
                        for l in f:
                            lines.append(len(l))
                        print lines
                        '''
                elif event_type == 'close-tab':
                    new_events = self.check_keys(self.convert_tab_event(event, 'Part closed'),new_events)
                    #print new_events ###################################################
                    #exit()
                elif event_type == 'create-tab':
                   new_events = self.check_keys(self.convert_tab_event(event, 'Part opened'),new_events)
                    #print new_events ###################################################
                    #exit()
                elif event_type == 'deactivate-tab':
                    new_events = self.check_keys(self.convert_tab_event(event, 'Part deactivated'),new_events)
                    #print new_events
                    #exit()
                elif event_type == 'expand-workspace-tree-node':
                    # commenting out package explorer stuff
                    #new_events = self.check_keys(self.convert_expand_workspace_tree_node_event(event),new_events)
                    pass
                elif event_type == 'change-cursor':
                    new_events = self.check_keys(self.convert_change_cursor_event(event),new_events)
                    #print new_events
                    #exit()
                elif event_type == 'change-selection':#still need to work on line 310
                    new_events = self.check_keys(self.convert_change_selection_event(event),new_events)
                    #print new_events
                    #exit()
                elif event_type == 'select-workspace-tree-nodes':
                    new_events = self.check_keys(self.convert_select_workspace_tree_nodes_event(event),new_events)
                    #print new_events
                    #exit()
                #pass
                elif event_type == 'start-logging':
                    new_events = self.check_keys(self.convert_start_logging_event(event),new_events)
                    #print new_events
                    #exit()
                elif event_type == 'update-workspace-tree':
                    # commenting out package explorer stuff
                    #new_events = self.check_keys(self.convert_update_workspace_tree_event(event),new_events)
                    pass
                # keep track of the events that are not converted and how many instances occur
                if event_type in unconverted_events:
                    unconverted_events[event_type] += 1
                else:
                    unconverted_events[event_type] = 1
        '''
        queued_events = []
        for event in queued_cryolog_events:
            event_type = event['event-type']

            if event_type == 'change-cursor':
                queued_events.extend(self.convert_change_cursor_event(event))
            elif event_type == 'change-selection':
                queued_events.extend(self.convert_change_selection_event(event))
        
        print 'Queued {0} click/selection-related events. Adding to the existing {1} events.'.format(len(queued_events), len(new_events))
        new_events.extend(queued_events)
        '''
        print 'Converted {0} cryolog events to {1} pfislog events.\n'.format(len(cryolog.events), len(new_events))

        print 'There were {0} unique unconverted event types:'.format(len(unconverted_events))
        print_dict(unconverted_events)

        new_pfislog = Pfislog(events=new_events)
        return new_pfislog

def update_file(file_path, actionType, text, line_number, column):
    print line_number
    print column
    # open file and read in string
    file = open(rootdir+ "/" + file_path, "r")
    i = 0
    sum = 0
    for line in file:
        if i == line_number-1:
            sum+=column
            break
        sum+=len(line)
        i+=1
    file.seek(0)
    contents = file.read()
    file.close()
       
    #calculate position
    cur_line = 1
    cur_index = 0
    while(cur_index<len(contents)):
        if(contents[cur_index] == "\n"):
            cur_line = cur_line + 1
        if(cur_line ==line_number):
            break
        cur_index = cur_index + 1 
    # column numbers in log not zero indexed
    index = cur_index + column - 1
    #print "Index: %d" % index
    #print "Contents before index: %s" % contents[:index]
    print "text - " +text
    #print "Contents after index: %s" % contents[index:]
    #print actionType
    #print contents
    #print "updated contents"
    if actionType == "insert" or actionType == "insertLines":
        #insert text into string
        updated_contents = contents[:sum-1] + text + contents[sum-1:]
        print updated_contents[sum-20:sum+20]
    else:
        #skip over deleted text while copying string
        updated_contents = contents[:sum-1] + contents[(sum-1 + len(text)):]
        #print updated_contents
       
    # write updated string to file
    file = open(rootdir+ "/" + file_path, "w")
    file.write(updated_contents)
    file.close()
def get_array(dir, out_file):
    if dir not in ['.c9', '.cryolite']:
        f = ''
        if(out_file):
            f = open(out_file,'a')
        dir_to_run = "./jsparser/src/hexcom/" + dir
        out = subprocess.check_output(["php", "./jsparser/fileIterator.php", dir_to_run])
        if(out_file):
            f.write(out)
            f.close()
        else:
            return out
        #call(["php", "fileIterator.php", dir_to_run]);	
def array_gen_single_folder(fn):
    k = fn.rfind('/')
    global miv_array
    global doc_line_list
    new_data = json.loads(get_array(fn[len('/hexcom/'):k], None))
    lengths = new_data[-1]
    new_data.pop()
    for item in lengths['lengths']:
    	i=0
        for doc in doc_line_list:
            if(doc['file']  == item['file']):
                doc_line_list[i] = item
                break
            i=i+1    
    for item in new_data:
        i=0
        for doc in miv_array:
            if((doc['functions'] != [] and item['functions'] != []) and (item['functions'][0]['src'] == doc['functions'][0]['src'])):
                miv_array[i] = doc
            i=i+1
def array_gen(fn):
    
    i=0
    if(os.path.isfile("fullAST.txt")==False):   
        
        while(i<len(src_list)-4):
            print str(i) + src_list[i]
            p=multiprocessing.Process(target=get_array, args=(src_list[i], fn+'1.txt',))
            p.start()
            q=multiprocessing.Process(target=get_array, args=(src_list[i+1],fn+'2.txt',))
            q.start()
            r=multiprocessing.Process(target=get_array, args=(src_list[i+2],fn+'3.txt',))
            r.start()
            s=multiprocessing.Process(target=get_array, args=(src_list[i+3],fn+'4.txt',))
            s.start()
            p.join()
            q.join()
            r.join()
            s.join()
            i=i+4
        results = []
        f = open(fn+'1.txt', 'r')
        for line in f:
            results.append(json.loads(line))
        

        f = open(fn+'2.txt', 'r')
        for line in f:
            results.append(json.loads(line))
        

        f = open(fn+'3.txt', 'r')
        for line in f:
            results.append(json.loads(line))
        

        f = open(fn+'4.txt', 'r')
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

    doc_line_list =miv_array.pop()
    doc_line_list = doc_line_list["lengths"]
    miv_array = miv_array[0] #collapse the array

rootdir = './jsparser/src'
src_list = [name for name in os.listdir("./jsparser/src/hexcom") if os.path.isdir(os.path.join(
"./jsparser/src/hexcom", name))]
array_gen(sys.argv[1])
cryolog = Cryolog('cryolite.log')
pfislog = Pfislog('pfis.log') # here as an example. The new_pfislog is what gets exported.
converter = Converter()
new_pfislog = converter.convert_cryolog_to_pfislog(cryolog)
if __name__ == '__main__':
    new_pfislog.export_to_file('output.txt')
