#Running this will create two DBs in Cryo2Pfig folder - 1. Text Similarity Only and 2. Text & Topology Similarity.

import re
import json
import os
import sqlite3
import uuid
import shutil
import networkx as nx
from fQNUtils import FQNUtils

DB_FILE_NAME_TEXT= "variations_textSimilarity.db"
DB_FILE_NAME_TEXT_TOPOLOGY= "variations_topologyAndTextSimilarity.db"

CREATE_VARIANTS_TABLE_QUERY = 'CREATE TABLE VARIANTS(NUM INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50), CHANGELOG TEXT)'
CREATE_PATCHES_TABLE_QUERY = 'CREATE TABLE VARIANTS_TO_FUNCTIONS(METHOD VARCHAR(30), START INTEGER, END INTEGER, BODY TEXT, UUID VARCHAR)'
VARIANT_INSERT_QUERY = 'INSERT INTO VARIANTS(NAME, CHANGELOG) VALUES (?,?)'
FUNCTION_INSERT_QUERY = 'INSERT INTO VARIANTS_TO_FUNCTIONS VALUES (?,?,?,?,?)'

UPDATE_QUERY = 'UPDATE VARIANTS_TO_FUNCTIONS SET END = ? WHERE END = ? AND METHOD = ? AND BODY = ?'

def getVariantName(filename):
	regex = re.compile('/hexcom/([^/]*)/.*')
	match = regex.match(filename)
	if match == None:
		raise Exception("No such file: "+ filename)
	return match.groups()[0]

def getFilePath(path):
	regex = re.compile('/[^h0-9]\w.*')
	match = regex.match(path)
	if match == None:
		return ""
	return match.groups()[0]

def readASTFile():
	obj = None
	file = open('../fullAST.txt')
	obj = json.loads(file.read())
	file.close()
	return obj[0]

def isVariant(f1, f2):
	if f1 == None or f2 == None:
		return False
	#TODO: fileName (src value) should exclude variant name from comparison
	# add filename part of f1['src'] == f2['src']
	if getMethodFqnRelativeToVariant(f1) == getMethodFqnRelativeToVariant(f2) \
			and f1['contents'] == f2['contents']:
		return True

	return False

def insertFunctionToDb(index, function, prevVarFunctions, conn):
	methodFQN = getMethodFqnRelativeToVariant(function)
	methodBody = function['contents']

	prevVariantOfFunction = None
	if prevVarFunctions != None:
		for f in prevVarFunctions:
			if isVariant(f, function):
				prevVariantOfFunction = f

	c = conn.cursor()
	if prevVariantOfFunction is None:
		uuidValue = uuid.uuid1()
		c.execute(FUNCTION_INSERT_QUERY, [FQNUtils.normalizer(methodFQN), index, index, FQNUtils.normalizer(methodBody), str(uuidValue)])

	else:
		#Update will break -- update where end = prev var name
		c.execute(UPDATE_QUERY,[index, index-1, FQNUtils.normalizer(methodFQN), FQNUtils.normalizer(methodBody)])

	conn.commit()

def getMethodFqnRelativeToVariant(function):
	fileNameFromRoot = function['src']
	nestedPathWithinFile = function['filepath']
	functionHeader = function["header"]
	fileNameRelativeToVariant = FQNUtils.getRelativeFilePathWithinVariant(fileNameFromRoot)
	methodFQN = FQNUtils.getFullMethodPath(fileNameRelativeToVariant, nestedPathWithinFile, functionHeader)
	return methodFQN

def variantChangelogMap():
	#For creating a map of variant -> changelog.
	root = '../jsparser/src/hexcom'
	variant_changelog_map = {}

	for directory in os.listdir(root):
		message = ''

		if 'Store' in directory or 'c9' in directory:
			continue

		changelog = open(os.path.join(root, directory, 'changes.txt'), 'r')
		linelist = changelog.readlines()

		for line in linelist:
			if re.match('commit|Merge:|Author:|Date:', line) or line == '':
				continue
			else:
				if line in message:
					continue
				else:
					message = message + ' ' + line
		message = message.strip()
		variant_changelog_map[directory] = message

	return  variant_changelog_map


def insertVariants(sortedVariants, variant_changelog_map, connection_tuple):
	for conn in connection_tuple:
	    for variant in sortedVariants:
		    conn.execute(VARIANT_INSERT_QUERY, [variant, variant_changelog_map[variant]])

	    conn.commit()

def createDbAndInitialTables(db_tuple):
	if(os.path.exists(DB_FILE_NAME_TEXT)):
		os.remove(DB_FILE_NAME_TEXT)

	if(os.path.exists(DB_FILE_NAME_TEXT_TOPOLOGY)):
		os.remove(DB_FILE_NAME_TEXT_TOPOLOGY)

	for db in db_tuple:
		conn = sqlite3.connect(db)
		c = conn.cursor()
		c.execute(CREATE_PATCHES_TABLE_QUERY)
		c.execute(CREATE_VARIANTS_TABLE_QUERY)
		c.close()
		conn.commit()

def getFunctionsAndInvocationsInVariants(variant_functions):
	variantsToFuncDefinitionMap = {}
	variantsToFuncCallsMap={}

	for variant in variant_functions:
		functions_list = variant['functions']
		if len(functions_list) > 0:

			file_name = functions_list[0]['src']
			variant_name = getVariantName(file_name)

			if variant_name in variantsToFuncDefinitionMap:
				variantsToFuncDefinitionMap[variant_name].extend(functions_list)
			else:
				variantsToFuncDefinitionMap[variant_name] = functions_list
			variantsToFuncDefinitionMap[variant_name] = sorted(variantsToFuncDefinitionMap[variant_name], key=lambda item:item["start"])

		invocation_list = variant['invocations']
		if len(invocation_list) > 0:

			file_name = invocation_list[0]['src']
			variant_name = getVariantName(file_name)

			if variant_name in variantsToFuncCallsMap:
				variantsToFuncCallsMap[variant_name].extend(invocation_list)
			else:
				variantsToFuncCallsMap[variant_name] = invocation_list

	return (variantsToFuncDefinitionMap, variantsToFuncCallsMap)

def buildGraph(definitions, invocations):
	graph = nx.DiGraph()

	for i in range(0, len(definitions)):
		# print i, " of ", len(definitions)
		fqn = getMethodFqnRelativeToVariant(definitions[i])
		graph.add_node(fqn)

		if i > 0:
			fqn_Prev = getMethodFqnRelativeToVariant(definitions[i-1])
			graph.add_edge(fqn, fqn_Prev, attr_dict={"edge_type":"adjacent"})
			# print "Adj : ", fqn, fqn_Prev

		if i < len(definitions) - 1 :
			fqn_Next = getMethodFqnRelativeToVariant(definitions[i+1])
			graph.add_edge(fqn, fqn_Next, attr_dict={"edge_type":"adjacent"})
			# print "Adj : ", fqn, fqn_Next

	for invocation in invocations:
		invoked_method = FQNUtils.normalizer(invocation["invsrc"])

		if invocation['header'] != None \
				and invocation['header'] != ''\
				and FQNUtils.JS_STD_PREFIX not in invoked_method:

			invoking_method_fqn = getMethodFqnRelativeToVariant(invocation)
			invoked_method_fqn = FQNUtils.getRelativeFilePathWithinVariant(invoked_method)
			graph.add_edge(invoking_method_fqn, invoked_method_fqn, attr_dict={"edge_type":"call"})
			# print "Call: ", invoking_method_fqn, invoked_method_fqn

	return graph

def checkEquivalence(graph, function, prevGraph, prevFunction):
	#Both Node names have to be same!
	funcNodeName = getMethodFqnRelativeToVariant(function)

	funcNeighbors = graph.neighbors(funcNodeName)
	prevNeighbors = prevGraph.neighbors(funcNodeName)

	if getMethodBody(function) != getMethodBody(prevFunction):
		# print "False - method body!!!"
		return False
	if len(funcNeighbors) != len(prevNeighbors):
		# print "False - Neighbor count!!!"
		return False
	for neighbor in funcNeighbors:
		if neighbor not in prevNeighbors:
			# print "False - Missing neighbor!!!"
			return False
		if graph[funcNodeName][neighbor] != prevGraph[funcNodeName][neighbor]:
			# print "Not same neighbors!!!"
			return False

	# print "True!!!"
	return True

def insertNodesToDb(index, variants, variantsToFunctionsMap, graph, prevGraph, conn):
	c = conn.cursor()

	variant = variants[index]
	# print "---------------------"
	# print index+1, variant
	# print "---------------------"
	functions = variantsToFunctionsMap[variant]

	for function in functions:
		nodeName = getMethodFqnRelativeToVariant(function)
		methodBody = getMethodBody(function)
		# print "Node Name: ", nodeName

		if prevGraph is None or nodeName not in prevGraph.nodes():
			# print "Node insert: ", nodeName
			uuidValue = uuid.uuid1()
			c.execute(FUNCTION_INSERT_QUERY, [FQNUtils.normalizer(nodeName), index+1, index+1, FQNUtils.normalizer(methodBody), str(uuidValue)])

		elif prevGraph[nodeName] is not None:
			prevFunction = None
			isEquivalent = False

			prevVarFunctions = variantsToFunctionsMap[variants[index-1]]
			for func in prevVarFunctions:
				if getMethodFqnRelativeToVariant(func) == nodeName:
					prevFunction = func

			if prevFunction is not None:
				isEquivalent = checkEquivalence(graph, function, prevGraph, prevFunction)

			if isEquivalent:
				# print "Update: ", nodeName
				c.execute(UPDATE_QUERY,[index+1, index, FQNUtils.normalizer(nodeName), FQNUtils.normalizer(methodBody)])

			else:
				# print "Node insert: ", nodeName
				uuidValue = uuid.uuid1()
				c.execute(FUNCTION_INSERT_QUERY, [FQNUtils.normalizer(nodeName), index+1, index+1, FQNUtils.normalizer(methodBody), str(uuidValue)])


	c.close()
	conn.commit()

def getMethodBody(function):
	return FQNUtils.normalizer(function['contents'])

def moveDBToCryo2Pfig():
	shutil.move(DB_FILE_NAME_TEXT, os.path.join('../', DB_FILE_NAME_TEXT))
	shutil.move(DB_FILE_NAME_TEXT_TOPOLOGY, os.path.join('../', DB_FILE_NAME_TEXT_TOPOLOGY))

def main():
	createDbAndInitialTables((DB_FILE_NAME_TEXT, DB_FILE_NAME_TEXT_TOPOLOGY))
	ast = readASTFile()
	variant_changelog_map = variantChangelogMap()
	variantsToFunctionsMap, variantsToInvocationsMap = getFunctionsAndInvocationsInVariants(ast)

	conn_text_only = sqlite3.connect(DB_FILE_NAME_TEXT)
	conn_text_topology = sqlite3.connect(DB_FILE_NAME_TEXT_TOPOLOGY)

	variantNames = variantsToFunctionsMap.keys()
	variantNames.sort()
	insertVariants(variantNames, variant_changelog_map, (conn_text_only, conn_text_topology))
	prevVariantGraph = None

	for i in range(0, len(variantNames)):
		prevVariantFunctions = None
		variant = variantNames[i]
		graph = buildGraph(variantsToFunctionsMap[variant], variantsToInvocationsMap[variant])
		insertNodesToDb(i, variantNames, variantsToFunctionsMap, graph, prevVariantGraph, conn_text_topology)
		prevVariantGraph = graph

		if i > 0:
			prevVariantFunctions = variantsToFunctionsMap[variantNames[i - 1]]

		for function in variantsToFunctionsMap[variant]:
			variantPos = i + 1
			insertFunctionToDb(variantPos, function, prevVariantFunctions, conn_text_only)

	conn_text_only.close()
	conn_text_topology.close()

	moveDBToCryo2Pfig()


if __name__ == '__main__':
    main()