# -*- Mode: Python; indent-tabs-mode: nil -*-

# Please adhere to the PEP 8 style guide:
#	  http://www.python.org/dev/peps/pep-0008/

#Version: by navigation, 2 steps per iteration

#detect code based on log - look at beginnning of log to determine this, add if or switch to run java or javascript code
import time
import getopt
import sys
from math import log
import sqlite3
import networkx as nx
import re
import bisect
import datetime
import iso8601
from nltk.stem import PorterStemmer
import cPickle
import copy
import json
JAVA = 0
JAVASCRIPT = 1
#SD: ADD AS NECESSARY

language = 0
stop = {}
sourcefile = ''
activation_root = ''
debug = 0
verbose = 0
verbose2 = 0
topolen = 0
#remember that you have to multiply the number of iterations you want by 2
numIterations = 2
stopwordsFile = ''

def stopwords():
	dp_numStopWords = 0
	f = open(stopwordsFile)
	for line in f:
		stop[line[0:-1]] = 1
		dp_numStopWords += 1
	
	print dp_numStopWords, "stop words added"
		

camelSplitter = re.compile(r'_|\W+|\s+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[a-zA-Z])(?=[0-9]+)|(?<=[0-9])(?=[a-zA-Z]+)')


def camelSplit(string):
	'''Split camel case words. E.g.,

	>>> camelSplit("HelloWorld.java {{RSSOwl_AtomFeedLoader}}")
	['Hello', 'World', 'java', 'RSS', 'Owl', 'Atom', 'Feed', 'Loader']
	'''
	result = []
	last = 0
	for match in camelSplitter.finditer(string):
		if string[last:match.start()] != '':
			result.append(string[last:match.start()])
		last = match.end()
	if string[last:] != '':
		result.append(string[last:])
	return result


def indexCamelWords(string):
	return [('word',
			 PorterStemmer().stem(word).lower()) for word in \
				camelSplit(string) if word.lower() not in stop]


def indexWords(string):
	return [('word',
			 word.lower()) for word in re.split(r'\W+|\s+',string) \
				if word != '' and word.lower() not in stop]


fix_regex = re.compile(r'[\\/]+')


def fix(string):
	return fix_regex.sub('/',string)


normalize_eclipse = re.compile(r"L([^;]+);.*")
normalize_path = re.compile(r".*src\/(.*)\.java")
#SD: this will just cut off the final .js. We can't cut out anything else because cloud9 projects don't have a set structure.
normalize_path_JavaScript = re.compile(r"(.*)\.js")

def normalize(string):
	'''
	Return the class indicated in the string.
	File-name example:
	Raw file name: jEdit/src/org/gjt/sp/jedit/gui/StatusBar.java
	Normalized file name: org/gjt/sp/jedit/gui/StatusBar
	'''
	#print "In normalize string=", string
	global language
	m = normalize_eclipse.match(string)
	if m:
		return m.group(1)
	if(language==JAVASCRIPT):
		return normalize_JavaScript(string)
	if(language==JAVA):
		return normalize_Java(fix(string))
	

def normalize_JavaScript(string):
	n = normalize_path_JavaScript.match(fix(string))
        pos = string.rfind(".js")
        if pos:
                return string[:pos]
	return ''
	
def normalize_Java(string):
	n = normalize_path.match(fix(string))
	if n:
		return n.group(1)
	return ''

#SD: this returns up to the last folder (without file name). I think this is acceptable. Ask David.
package_regex = re.compile(r"(.*)/[a-zA-Z0-9]+")
def package(string):
	'''Return the package.'''
	
	m = package_regex.match(normalize(string))
	if m:
		return m.group(1)
	return ''

#SD: returns the root level folder. each project can have only one root folder in cloud9
project_regex = re.compile(r"\/(.*)\/src/.*")
project_regex_javascript = re.compile(r"(.*?)\/")
def project(string):
	'''Return the project.'''
	if(language==JAVASCRIPT):
		m = project_JavaScript(string)
	if(language==JAVA):
		m =  project_Java(string)
	return m

def project_JavaScript(string):
	m = project_regex_javascript.match(fix(string))
	if m:
		return m.group(1)
	return ''
	

def project_Java(string):
	m = project_regex.match(fix(string))
	if m:
		return m.group(1)
	return ''
	
# Package (type -> package)
# Imports (type -> type)
# Extends (type -> type)
# Implements (type -> type)
# Method declaration (type -> method)
# Constructor invocation (method -> method)
# Method invocation (method -> method)
# Variable declaration (type -> variable)
# Variable type (variable -> type)


# TODO: This function is currently dead code; it may be broken
#def checkTopology(g):
#	 '''For which graphs are there disconnects?'''
#	 for key in g:
#		 if not nx.is_connected(g[key]):
#			 print key


# TODO: This function is currently dead code; it may be broken
#def graphDiameters(graphs):
#	 '''What's the radius and diameter of each graph?'''
#	 for key in graphs:
#		 if len(graphs[key]) < 2000:
#			 if len(nx.connected_component_subgraphs(graphs[key])) > 1:
#				 for g in nx.connected_component_subgraphs(graphs[key]):
#					 print key, len(g), nx.radius(g), nx.diameter(g)
#			 continue
#		 print key, len(graphs[key]), nx.radius(graphs[key]), \
#			 nx.diameter(graphs[key])

#SD: CHECK IF WE NEED TO ADD ANYTHING TO ACTIONS. WE SHOULDN'T NEED TO SUBTRACT ANYTHING HERE
def loadScents(graphs={}):
	'''Load just the scent portion of the graphs'''
	dp_numLinks = 0
	dp_numRows = 0
	conn = sqlite3.connect(sourcefile)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Package','Imports','Extends','Implements','Method declaration','Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'Constructor invocation scent', 'Method declaration scent', 'Method invocation scent', 'New package', 'New file header')''')
	for row in c:
		user, action, target, referrer, agent = (row['user'][0:3],
												 row['action'],
												 fix(row['target']),
												 fix(row['referrer']),
												 row['agent'])
		dp_numRows += 1
		if agent not in graphs:
			graphs[agent] = nx.Graph()
		if action in ('Package', 'Imports', 'Extends', 'Implements',
					  'Method declaration', 'Constructor invocation',
					  'Method invocation', 'Variable declaration',
					  'Variable type'):
			
			# Connect class to constituent words
			for word in indexWords(target):
				graphs[agent].add_edge(target, word)
				dp_numLinks += 1
				#if(debug): print "\tAdding edge 1:", target, "<-->", word[1]
			# Connect import to constituent words
			for word in indexWords(referrer):
				graphs[agent].add_edge(referrer, word)
				dp_numLinks += 1
				#if(debug): print "\tAdding edge 2:", referrer, "<-->", word[1]
		elif action in ('New package'):
			for word in indexWords(target):
				graphs[agent].add_edge(target,word)
		elif action in ('Constructor invocation scent',
						'Method declaration scent',
						'Method invocation scent',
						'New file header'):
			for word in indexWords(referrer):
				graphs[agent].add_edge(target,word)
				dp_numLinks += 1
				#if(debug): print "\tAdding edge 3:", target, "<-->", word[1]
			for word in indexCamelWords(referrer):
				graphs[agent].add_edge(target,word)
				dp_numLinks += 1
				#if(debug): print "\tAdding edge 4:", target, "<-->", word[1]
	c.close()
	if(debug): print dp_numLinks, "links added"
	if(debug): print dp_numRows, "rows proccessed"
	
	return graphs


def loadTopology(graphs={}):
	'''Load just the topology portion of the graphs'''
	lastAgent = ''
	dp_rowCount = 0
	conn = sqlite3.connect(sourcefile)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute('''select user,action,target,referrer,agent from logger_log where action in ('Package','Imports','Extends','Implements','Method declaration','Constructor invocation', 'Method invocation', 'Variable declaration', 'Variable type', 'New package', 'Open call hierarchy')''')
        
	for row in c:
                user, action, target, referrer, agent = (row['user'][0:3],
												 row['action'],
												 fix(row['target']),
												 fix(row['referrer']),
												 row['agent'])
		dp_rowCount += 1
		if agent not in graphs:
			graphs[agent] = nx.Graph()
			
		ntarget = normalize(target)
		nreferrer = normalize(referrer)
		pack = package(target)
		proj = project(target)
		
		if action == 'New Package':
			# Link packages node to new packages
			graphs[agent].add_edge('packages', referrer)
		else:
			# Connect topology
			if proj != '':
				graphs[agent].add_edge('packages', proj)
			if pack != '':
				graphs[agent].add_edge('packages', pack)
			if pack != '' and ntarget != '':
				graphs[agent].add_edge(pack, ntarget)
			if pack != '' and proj != '':
				graphs[agent].add_edge(proj, pack)
			graphs[agent].add_edge(target, referrer)
			if ntarget != '':
				graphs[agent].add_edge(ntarget, target)
			if nreferrer != '':
				graphs[agent].add_edge(nreferrer, referrer)
			if ntarget != '' and nreferrer != '':
				graphs[agent].add_edge(ntarget, nreferrer)
		lastAgent = agent
	c.close()
	
	global topolen
	for item in graphs[agent].nodes_iter():
		if item != '' and \
					  not wordNode(item) and \
					  '#' not in item and ';.' in item:
			topolen += 1
	
	print "Topology built using", dp_rowCount, "rows from db"
	print "Topology has", topolen, "method nodes"
	#print graphs[lastAgent].neighbors('Lorg/gjt/sp/jedit/ServiceManager;.getService(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;')
	return graphs

#SD: CHECK WITH DAVID ON THIS ONE
def loadScrolls(graphs={}):
	'''Load the scroll (adjacency) information from the db'''
	offsets = {}

	def sorted_insert(l, item):
		l.insert(bisect.bisect_left(l, item), item)

	def add_offset(agent, timestamp, loc, target, referrer):
		'''Update method declaration offset in offsets data structure'''
		if agent not in offsets:
			offsets[agent] = {}
		if loc not in offsets[agent]:
			offsets[agent][loc] = []
		if agent not in graphs:
			graphs[agent] = nx.Graph()
		# Remove any existing occurrence of given target
		for item in offsets[agent][loc]:
			if item['target'] == target:
				offsets[agent][loc].remove(item)
		# Maintain an ordered list of method declaration offsets that is
		# always current as of this timestamp.
		sorted_insert(offsets[agent][loc],
					  {'referrer': referrer, 'target': target})
		for i in range(len(offsets[agent][loc])):
			if i+1 < len(offsets[agent][loc]):
				graphs[agent].add_edge(offsets[agent][loc][i]['target'],
										offsets[agent][loc][i+1]['target'])

	
	conn = sqlite3.connect(sourcefile)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Method declaration offset') order by timestamp")

	for row in c:
		timestamp, action, agent, target, referrer = \
			(iso8601.parse_date(row['timestamp']),
			 row['action'],
			 row['agent'],
			 row['target'],
			 int(row['referrer']))
		loc = normalize(target)
		if loc:
			add_offset(agent, timestamp, loc, target, referrer)
	c.close()
	if(verbose):print "==========Topology=========="
	if(verbose):print offsets["a23fe51d-196a-45b3-addf-3db4e8423e4f"]
	if(verbose):print "============================"
	return graphs


def loadPaths():
	'''
	Reconstruct the original method-level path through the source code by
	matching text selection offsets to method declaration offsets. Text
	selection offsets occur later in the data than method declaration
	offsets, so we can use this knowledge to speed up the reconstruction
	query. It returns: A timestamped sequence of navigation among methods
	(or classes if no method declaration offsets are available for that
	class)
	'''
	nav = {}
	out = {}
	offsets = {}

	def sorted_insert(l, item):
		l.insert(bisect.bisect_left(l, item), item)
	#SD: DON'T INCREASE TIMESTAMP IF JAVASCRIPT IS ENABLED
	def add_nav(agent, timestamp, loc, referrer):
		'''Add text selection navigation events to a structure'''
		global language
		if(language == JAVA):
			add_nav_Java(agent, timestamp, loc, referrer)
		if(language == JAVASCRIPT):
			add_nav_JavaScript(agent, timestamp, loc, referrer)
		
	def add_nav_Java(agent, timestamp, loc, referrer):
		# Add 20 seconds to each nav to work around a race condition in PFIG
		timestamp += datetime.timedelta(seconds=20)
		if agent not in nav:
			nav[agent] = []
		nav[agent].append({'timestamp': timestamp,
							'referrer': referrer,
							'loc': loc})
		if(verbose2): print "\tAdding", loc, "with offset of", referrer, "at time", str(timestamp)
		if(verbose): print "\tnav now contains:", nav
	
	def add_nav_JavaScript(agent, timestamp, loc, referrer):
		if agent not in nav:
			nav[agent] = []
		nav[agent].append({'timestamp': timestamp,
							'referrer': referrer,
							'loc': loc})
		if(verbose2): print "\tAdding", loc, "with offset of", referrer, "at time", str(timestamp)
		if(verbose): print "\tnav now contains:", nav

	def add_offset(agent, timestamp, loc, target, referrer):
		#global topolen
		'''Update method declaration offset in offsets data structure'''
		global language
		if(language == JAVA):
			add_offset_Java(agent, timestamp, loc, target, referrer)
		if(language == JAVASCRIPT):
			add_offset_JavaScript(agent, timestamp, loc, target, referrer)
	def add_offset_Java(agent, timestamp, loc, target, referrer):
		loc2 = loc.split('$')[0]
		if agent not in offsets:
			offsets[agent] = {}
		if loc2 not in offsets[agent]:
			offsets[agent][loc2] = []
		# Remove any existing occurrence of given target
		for item in offsets[agent][loc2]:
			if item['target'] == target:
				offsets[agent][loc2].remove(item)
		# Maintain an ordered list of method declaration offsets that is
		# always current as of this timestamp.
		sorted_insert(offsets[agent][loc2],
					  {'referrer': referrer, 'target': target})
		#topolen += 1
		if(verbose2): print "\tAdding ", loc2, "with method", target, "and offset of", referrer, "at time", str(timestamp)
	def add_offset_JavaScript(agent, timestamp, loc, target, referrer):
		#split on '/', then check for the js extension. if it's there, join everything after into a string.
                '''		
                loc2 = loc.split('/')
		i = 0
		for L in loc2:
			if('.js' in L):
				break
			i+=i
		temp = ''
		for item in loc2[i:]:
			temp += item
		loc2 = temp
                '''
                loc2 = loc
		if agent not in offsets:
			offsets[agent] = {}
		if loc2 not in offsets[agent]:
			offsets[agent][loc2] = []
		# Remove any existing occurrence of given target
		for item in offsets[agent][loc2]:
			if item['target'] == target:
				offsets[agent][loc2].remove(item)
		# Maintain an ordered list of method declaration offsets that is
		# always current as of this timestamp.
		sorted_insert(offsets[agent][loc2],
					  {'referrer': referrer, 'target': target})
		#topolen += 1
		if(verbose2): print "\tIn add_offset_JavaScript, Adding ", loc2, "with method", target, "and offset of", referrer, "at time", str(timestamp)

	def get_out(agent, timestamp):
		'''Match text selection navigation data to the method declaration
		offset data to determine the method being investigated
		'''

		if agent not in out:
			out[agent] = []
# Original While Loop:			 
#		 while agent in nav and agent in offsets and \
#				 len(nav[agent]) > 0 and \
#				 timestamp >= nav[agent][0]['timestamp']:

# Modified While Loop:
		while agent in nav and agent in offsets and \
				len(nav[agent]) > 0:
			
			referrer = nav[agent][0]['referrer']
			loc = nav[agent][0]['loc']
			print "\tTrying to match", loc, "with offset", referrer
			if(verbose): print "loc is", loc
			curts = nav[agent][0]['timestamp']
			# If method declaration offsets are unavailable, append to out
			# without the method name
			#print "printing offsets" 
                        print json.dumps(offsets[agent])
			print(loc)
			#if(language == JAVASCRIPT):
			#	loc = loc[1:]
                        #print loc
			if loc not in offsets[agent]:
				out[agent].append({'target': "Unknown node in: " + loc,
									'timestamp': curts})
				nav[agent].pop(0)
				print "\t!!!Navigation to unknown class detected."
				continue
			# Otherwise, lookup the method declaration offset for this
			# navigation event
			# TODO: Is the 'zz' supposed to be max string? If so, there must be
			# a better way.
			index = bisect.bisect_left(offsets[agent][loc],
										{'referrer': referrer,
										'target': 'zz'}) - 1
			if index < 0:
				index = 0
			if(verbose2): print "get_out index is", index
			out[agent].append({'target': offsets[agent][loc][index]['target'],
								'timestamp': curts})
			nav[agent].pop(0)

	conn = sqlite3.connect(sourcefile)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	
	#MAJOR CHANGES FROM HERE FORWARDS	 
	c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Method declaration offset') order by timestamp")
	t = None
	for row in c:
		timestamp, action, agent, target, referrer = \
			(iso8601.parse_date(row['timestamp']),
			 row['action'],
			 row['agent'],
			 row['target'],
			 int(row['referrer']))
		loc = normalize(target)
		#print "loc = " +loc + "target = " + target + "referrer = "+ str(referrer)
		if loc:
			add_offset(agent, timestamp, loc, target, referrer)
			t = timestamp
	#c.close() -Commenting this out just to see if it works : CH
	
	c.execute("select timestamp,action,target,referrer,agent from logger_log where action in ('Text selection offset') order by timestamp")
	for row in c:
		print row
		timestamp, action, agent, target, referrer = \
			(iso8601.parse_date(row['timestamp']),
			 row['action'],
			 row['agent'],
			 row['target'],
			 int(row['referrer']))
		loc = normalize(target)
		if loc:
			add_nav(agent, timestamp, loc, referrer)
			get_out(agent, timestamp)
	c.close()
	#MAJOR CHANGES END HERE
	
	for agent in nav:
		if len(nav[agent]) > 0:
			get_out(agent, t)
			for item in nav[agent]:
				out[agent].append({'target': item['loc'], 'timestamp': t})
	#print "==========Path=========="
	#print out
	#print "========================"
	print offsets
	return out


def init():
	global topolen
	topolen = 0
	g = {}
	print 'Loading scent data...'
	loadScents(g)
	print 'Loading topology data...'
	loadTopology(g)
	print 'Loading scroll data...'
	loadScrolls(g)
	print 'Loading paths...'
	nav = loadPaths()
	return nav, g


def between_method(a, b):
	return a != b

def between_class(a, b):
	return normalize(a) != normalize(b)

def between_package(a, b):
	return package(a) != package(b)

def pathsThruGraphs(nav, graph, function, level=between_method,
					data={}, words=[], agents=[]):
	'''Compute information about traversals through graphs.'''
	out = data
	if len(agents) == 0:
		agents = [agent for agent in nav]
	for agent in agents:
		if len(nav[agent]) == 0:
			continue
		if agent not in graph:
			continue
		pprev = None
		prev = nav[agent][0]
		i = 0
		j = 0
		
		for row in nav[agent]:
			j += 1
			if(verbose2): print "\tComparing following nav entries:"
			if(verbose2): print "\tTo:	 ", row['target']
			if(verbose2): print "\tFrom: ", prev['target']
			if level(row['target'], prev['target']):
				if(verbose2): print "\tNAVIGATION DETECTED"
				i += 1
				function(data, agent, graph[agent], pprev, prev, row, i, words)
				pprev = prev
			else:
				if(verbose2): print "\tno navigation"
			prev = row
	return data


def noop(data, agent, graph, pprev, prev, row, i, words):
	pass


def backtracks(data, agent, graph, pprev, prev, row, i, words):
	'''Pass to pathsThruGraphs: record A -> B -> A navigation at some level'''
	if agent not in data:
		data[agent] = 0
	if pprev != None and pprev['target'] == row['target']:
		data[agent] += 1


def shortest_lengths(data, agent, graph, pprev, prev, row, i, words):
	'''Pass to pathsThruGraphs: compute the shortest length of the navigation
	from A->B
	'''
	if agent not in data:
		data[agent] = {'sum': 0,'count': 0}
	if prev['target'] in graph and row['target'] in graph:
		data[agent]['sum'] += \
			len(nx.shortest_path(graph, prev['target'], row['target']))
		data[agent]['count'] += 1


def writeResults(log, output):
	f = open(output, 'w')
	if len(log) > 0:
		log[len(log) - 1]['timestamp'] -= datetime.timedelta(seconds=20)
		f.write("%s,%d,%s,%g,%g,%d,%d,%s,%s,%s,%s\n" % \
					(log[len(log) - 1]['agent'],
					 log[len(log) - 1]['i'],
					 log[len(log) - 1]['timestamp'].time(),
					 log[len(log) - 1]['rank'],
					 log[len(log) - 1]['ties'],
					 log[len(log) - 1]['length'],
					 topolen,
					 log[len(log) - 1]['from'],
					 log[len(log) - 1]['to'],
					 log[len(log) - 1]['class'],
					 log[len(log) - 1]['package'])) 
	f.close()


# If enrich is set to true, it's only valid to run pathsThruGraphs once. You
# must then reset the graph using the loader
enrich = False


def resultsPrev(data, agent, graph, pprev, prev, row, i, words):
	'''Use the previous location to predict the current location.

	>>> nav,g = init()
	>>> r = []
	>>> pathsThruGraphs(nav,g,resultsPrev,data=r)
	>>> writeResults(r,'out.csv')
	'''
	if(verbose2):
		print "checking whether " + prev['target'] + " and " + row['target'] + " are in graph"
	if prev['target'] in graph and row['target'] in graph:
		if pprev and pprev['target'] in graph and enrich:
			graph.add_edge(pprev['target'], prev['target'])
		activation = {prev['target']: 1.0}
		for word in words:
			activation[word]=1.0
		rank, length, ties = getResultRank(graph, activation, row['target'],
									 iterations=numIterations, d=0.85, navnum=i)
		if ties == None:
			ties = 0
		data.append({'agent': agent,
					 'i': i,
					 'rank': rank,
					 'ties': ties,
					 'length': length,
					 'from': prev['target'],
					 'to': row['target'],
					 'class': between_class(prev['target'], row['target']),
					 'package': between_package(prev['target'], row['target']),
					 'timestamp': row['timestamp']})
	else:
		ties = 0
		data.append({'agent': agent,
					 'i': i,
					 'rank': 999999,
					 'ties': ties,
					 'length': topolen,
					 'from': prev['target'],
					 'to': row['target'],
					 'class': between_class(prev['target'], row['target']),
					 'package': between_package(prev['target'], row['target']),
					 'timestamp': row['timestamp']})


def resultsNoop(data, agent, graph, pprev, prev, row, i, words):
	'''Use just the words to make predictions.'''
	if prev['target'] in graph and row['target'] in graph:
		activation = {}
		for word in words:
			activation[word] = 1.0
		rank, length, ties = \
			getResultRank(graph, activation, row['target'], navnum=i)
		data.append({'agent': agent,
					 'i': i,
					 'rank': rank,
					 'ties': ties,
					 'length': length,
					 'from': prev['target'],
					 'to': row['target'],
					 'class': between_class(prev['target'], row['target']),
					 'package': between_package(prev['target'], row['target']),
					 'timestamp': row['timestamp']})
	else:
		data.append({'agent': agent,
					 'i': i,
					 'rank': 999999,
					 'ties': ties,
					 'length': topolen,
					 'from': prev['target'],
					 'to': row['target'],
					 'class': between_class(prev['target'], row['target']),
					 'package': between_packaget(prev['target'], row['target']),
					 'timestamp': row['timestamp']})


def resultsPath(data, agent, graph, pprev, prev, row, i, words):
	'''The most recently encountered item has the highest activation, older
	items have lower activation. No accumulation of activation.

	>>> nav,g = init()
	>>> r = {}
	>>> pathsThruGraphs(nav,g,resultsPath,data=r)
	>>> writeResults(r['log'],'out.csv')
	'''
	if agent not in data:
		data[agent] = []
	if 'log' not in data:
		data['log'] = []
	if prev['target'] in graph and row['target'] in graph:
		if pprev and pprev['target'] in graph and enrich:
			graph.add_edge(pprev['target'], prev['target'])

		if prev['target'] in data[agent]:
			data[agent].remove(prev['target'])
		data[agent].append(prev['target'])

		a = 1.0
		activation = {}
		for word in words:
			activation[word] = 1.0
		for j in reversed(range(len(data[agent]))):
			if(data[agent][j] not in activation or activation[data[agent][j]] < a):
				activation[data[agent][j]] = a
			a *= 0.9
		rank, length, ties = \
			getResultRank(graph, activation, row['target'], navnum=i)
		data['log'].append({'agent': agent,
							'i': i,
							'rank': rank,
							'ties': ties,
							'length': length,
							'from': prev['target'],
							'to': row['target'],
							'class': between_class(prev['target'],
													row['target']),
							'package': between_package(prev['target'],
														row['target']),
							'timestamp': row['timestamp']})
	else:
		data['log'].append({'agent': agent,
							'i': i,
							'rank': 999999,
							'ties': ties,
							'length': topolen,
							'from': prev['target'],
							'to': row['target'],
							'class': between_class(prev['target'],
													row['target']),
							'package': between_package(prev['target'],
														row['target']),
							'timestamp': row['timestamp']})

def sorter (x,y):
	return cmp(y[1],x[1])


def wordNode (n):
	return n[0] == 'word'


def dumpActivation(activation, navnum):
	for (item,val) in activation:
		if wordNode(item):
			activation_root.write("%s|%s|word|%s\n" %( navnum, val, item[1]))
		elif ';.' not in item:
			activation_root.write("%s|%s|class|%s\n" %( navnum, val, item))
		elif '#' in item:
			activation_root.write("%s|%s|localvar|%s\n" %( navnum, val, item))
		else:
			activation_root.write("%s|%s|method|%s\n" %( navnum, val, item))
			
def dumpActivation2(activation, navnum):
	for (item, val) in activation:
		if not(wordNode(item) or ';.' not in item or '#' in item):
			activation_root.write("%s,method,%s,%s\n" %( navnum, val, item))

def getResultRank(graph, start, end, iterations=numIterations, d=0.85, navnum=0):
	#global topolen
	last = sorted(start.items(),sorter)[0][0]
	activation = spreadingActivation(graph, start, iterations, d)
	#dumpActivation(activation, navnum)
	#Here he removes everything but methods from activation
	scores = [val for (item,val) in activation if item != '' and \
					  item != last and not wordNode(item) and \
					  '#' not in item and ';.' in item]
	
	#dumpActivation2(activation, navnum)
	activation = [item for (item,val) in activation if item != '' and \
					  item != last and not wordNode(item) and \
					  '#' not in item and ';.' in item]
	print "\tActivation vector has", len(activation), "nodes"
	rank = 0
	found = 0
	for item in activation:
		rank += 1
		#print rank, item, val
		if item == end:
			found = 1
			break
	#if found:
		#scores = []
	ranks = rankTransform(scores)
	rankTies = mapRankToTieCount(ranks)
	ties = rankTies[ranks[rank - 1]]
	#methods[agent][item] = (len(ranks) - ranks[i]) / (len(ranks) - 1)
	writeScores(navnum, activation, ranks, scores)
	#print "End:", end, "\trank:", rank, "\tranks[rank-1]:", ranks[rank - 1], "\tscores[rank-1]:", scores[rank-1] 
	return (len(ranks) - ranks[rank - 1]), len(activation), ties
	#return (len(ranks) - ranks[rank - 1]) / (len(ranks) - 1), len(activation)
	#else:
	#	 return 999998, len(activation)
	
def mapRankToTieCount(ranks):
# uses methods to create a mapping from the rank to the number of instances
# of that rank in the rank listing
# methods: { agent id --> { method --> rank }
# o: { rank --> number ties }
	
	o = {}
	
	for rank in ranks:		
		if rank not in o:
			o[rank] = 1
		else:
			o[rank] = o[rank] + 1
				
	return o
	
def writeScores(navnum, methods, ranks, scores):
# Writes the contents of methods to the specified file

	for i in range(len(methods)):
		activation_root.write("%d,%s,%s,%s\n" % (navnum, methods[i], (len(ranks) - ranks[i]), scores[i]))
	
#The following were pulled from the stats.py package

	
def rankTransform(inlist):
	#We need to add all the zero entries here
	extendedList = []
	for i in range(topolen):
		if i < len(inlist):
			extendedList.append(inlist[i])
		else:
			extendedList.append(0);
	n = len(extendedList)
	svec, ivec = shellsort(extendedList)
	sumranks = 0
	dupcount = 0
	newlist = [0]*n
	for i in range(n):
		sumranks = sumranks + i
		dupcount = dupcount + 1
		if i==n-1 or svec[i] <> svec[i+1]:
			averank = sumranks / float(dupcount) + 1
			for j in range(i-dupcount+1,i+1):
				newlist[ivec[j]] = averank
			sumranks = 0
			dupcount = 0
	return newlist

def shellsort(inlist):
	n = len(inlist)
	svec = copy.deepcopy(inlist)
	ivec = range(n)
	gap = n/2	# integer division needed
	while gap >0:
		for i in range(gap,n):
			for j in range(i-gap,-1,-gap):
				while j>=0 and svec[j]>svec[j+gap]:
					temp		= svec[j]
					svec[j]		= svec[j+gap]
					svec[j+gap] = temp
					itemp		= ivec[j]
					ivec[j]		= ivec[j+gap]
					ivec[j+gap] = itemp
		gap = gap / 2  # integer division needed
# svec is now sorted inlist, and ivec has the order svec[i] = vec[ivec[i]]
	return svec, ivec


###End stats.py code

def weight(a, b):
	if wordNode(a) or wordNode(b):
		return 0.7
	if normalize(a) == normalize(b):
		return 1
	return 0.7


def spreadingActivation(graph,activation,iterations=numIterations,d=0.85):
	'''Perform spreading activation computation on the graph by activating
	nodes in the activation dictionary. activation = {} where key is node,
	value is initial activation weight
	'''
	
	#i = the current node
	#j = iterated neighbor of i
	#x = iteration counter
	
	# if x is 0,2,4,6,... we want to spread out only to word nodes
	# if x is 1,3,5,7,... we want to spread out only to non-word nodes
	
	for x in range(iterations):
		for i in activation.keys():
			if i not in graph:
				continue
			w = 1.0 / len(graph.neighbors(i))
			for j in graph.neighbors(i):
				if j not in activation:
					activation[j] = 0.0
				if (x % 2 == 0 and wordNode(j)) or (x % 2 != 0 and not wordNode(j)):
					activation[j] = activation[j] + (activation[i] * w * d)
	return sorted(activation.items(), sorter)


def storeGraphs(graphs):
	f = open('graphs.pk1', 'wb')
	cPickle.dump(graphs, f)
	f.close()


def storeNavigation(nav):
	f = open('nav.pk1', 'wb')
	cPickle.dump(nav, f)
	f.close()


def storeTopology(top):
	f = open('topology.pkl', 'wb')
	cPickle.dump(top, f)
	f.close()


def storeScent(scent):
	f = open('scent.pkl', 'wb')
	cPickle.dump(scent, f)
	f.close()


def loadGraphs():
	f = open('graphs.pk1', 'rb')
	graphs = cPickle.load(f)
	f.close()
	return graphs


def loadNav():
	f = open('nav.pk1', 'rb')
	nav = cPickle.load(f)
	f.close()
	return nav


def loadTopologyPickle():
	f = open('topology.pkl', 'rb')
	topology = cPickle.load(f)
	f.close()
	return topology


def loadScentPickle():
	f = open('scent.pkl', 'rb')
	scent = cPickle.load(f)
	f.close()
	return scent

#Words that are specific to the current files.
def ignore(word):
	global language
	if(language == JAVASCRIPT):
		return ignore_javascript(word)
	if(language == JAVA):
		return ignore_java(word)

def ignore_javascript(word):
	return word not in ['var','break','case','catch','continue','debugger','default','delete','do',
						'else','finally','for','function','if','in','instanceof','new',
						'return','switch','this','throw','try','typeof','var','void','while','with']
def ignore_java(word):
	return word not in ['ibm', 'lcom', 'ljava', 'lang', 'string', 'set',
						'tostring', 'instanc']


def generateActivation(nav, g, agent):
	if len(nav[agent]) == 0:
		return
	prev = nav[agent][0]
	data = []
	for item in nav[agent]:
		if prev in g[agent] and item in g[agent]:
			if prev in data:
				data.remove(prev)
			data.append(prev)
			prev = item
	a = 1.0
	activation = {}
	for i in reversed(range(len(data))):
		if(data[i] not in activation or activation[data[i]] < a):
			activation[data[i]] = a
		a *= 0.9
	return [item[1] for (item, activation) in \
				spreadingActivation(g[agent], activation) \
				if wordNode(item) and ignore(item[1])][0:40]

def activate_participant(g, text, participant):
	words = [node for node in g[participant] if wordNode(node) and node[1] in text]
	return words

def make_goal_text(file = '',string = ''):
	#SD: TODO: MAKE SURE FILE ISN'T TOO LONG
	if(file !=''):
		f = open(file, 'r')
		string = f.read()
	wordList = indexCamelWords(string)
	wordList.extend(indexWords(string))
	result = []
	for word in wordList:
		result.append(word[1])
	return result

def do_pfis(participant_id,date, goal_text, history,outputDir):
	global sourcefile, nav, g, activation_root
	file_string = outputDir + participant_id+ "-" + date
	if(history == True and goal_text == None):
		print 'Processing H- (with history, no goal)'
		activation_root = open(file_string + "-ActivationVectors-WithHistNoGoal.csv",'w')
		nav, g = init()
		print 'Analyzing data...'
		r = {}
		pathsThruGraphs(nav, g, resultsPath, data=r)
		writeResults(r['log'],
			file_string+ '-PfisOutput-WithHistNoGoal.csv')
		activation_root.close()
	elif(history == False and goal_text != None):
		print 'Processing -G (no history, with goal)'
		activation_root = open(file_string + "-ActivationVectors-noHistWithGoal.csv",'w')
		o, nav, g = init()
		print 'Analyzing data...'
		r = []
		pathsThruGraphs(nav, g, resultsPrev, data=r, words=activate_participant(participant_id, g, make_goal_text(goal_text)))
		writeResults(r, file_string + '-PfisOutput-NoHistWithGoal.csv')
		activation_root.close()
	elif(history == True and goal_text != None):
		print 'Processing HG (with history, with goal)'
		activation_root = open(file_string + "-ActivationVectors-WithHistWithGoal.csv",'w')
		nav, g = init()
		print 'Analyzing data...'
		r = {}
		pathsThruGraphs(nav, g, resultsPath, data=r, words=activate_participant(participant_id,g, make_goal_text(goal_text)))
		writeResults(r['log'],
				 file_string + '-PfisOutput-WithHistWithGoal.csv')
		activation_root.close()
	elif(history == False and goal_text == None):
		print 'Processing -- (no history, no goal)'
		activation_root = open(file_string + "-ActivationVectors-NoHistNoGoal.csv",'w')
		nav, g = init()
		print 'Analyzing data...'
		r = []
		pathsThruGraphs(nav, g, resultsPrev, data=r)
		writeResults(r, file_string + '-PfisOutput-NoHistNoGoal.csv')
		activation_root.close()
	else:
		print("Unhandled case")
		sys.exit(2)
def check_language(sourcefile):
	conn = sqlite3.connect(sourcefile)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	lang = ''
	c.execute("select action,target from logger_log where action=('Language')")
	for row in c:
		lang = row['target']
	c.close
	return lang
def usage():
	print("Usage is as follows:\n" \
			"python pfis2.py -d <db> -s <stop file> -o <out> -i <pID> -[g <goal file>] -[h]")
	sys.exit(2)
			
#SD: ADD ARGUMENTS GOAL, HISTORY, BOTH, NEITHER, PARTICIPANT_ID.
def main():
	global sourcefile, stopwordsFile, language
	try:
		opts, args = getopt.getopt(sys.argv[1:], "d:s:o:i:f:b:t:h")
	except getopt.GetoptError as err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		print("entering usage from exception")
		usage()
		sys.exit(2)
	goal_text = None
	history = False
	date = time.strftime("%d-%b-%j")
	outputDir = None
	for o, a in opts:
		if o == "-d":
			sourcefile = a
			print sourcefile
		elif o == "-s":
			stopwordsFile = a
		elif o == "-o":
			outputDir = a
			h = True
		elif o == "-i":
			participant_id = a
		elif o == "-g":
			goal_text = a
		elif o == "-h":
			history = True
		elif o == "-t":
			date = a
		else:
			assert False,  o + " is an unhandled option"
			usage()
	lang = check_language(sourcefile)
	language = JAVA
	if(outputDir == None):
		assert False, "output file must be designated by option -o <output>"
	
	if(lang == 'JavaScript'):
		language = JAVASCRIPT
	if(outputDir[-1] != '/'):
		outputDir += '/'
	print "Using database:", sourcefile
	if len(stop) == 0:
		stopwords()
		
	do_pfis(participant_id,date, goal_text, history,outputDir)
	#changed
	sys.exit(0)

if __name__ == "__main__":
	main()
