import re
import json
import os
import sqlite3
import uuid
import networkx as nx
from fQNUtils import FQNUtils


DB_FILE_NAME= "variantstofunctions_1.db"

CREATE_VARIANTS_TABLE_QUERY = 'CREATE TABLE VARIANTS(NUM INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50))'
CREATE_PATCHES_TABLE_QUERY = 'CREATE TABLE VARIANTS_TO_FUNCTIONS(METHOD VARCHAR(30), START INTEGER, END INTEGER, BODY TEXT, UUID VARCHAR)'
VARIANT_INSERT_QUERY = 'INSERT INTO VARIANTS(NAME) VALUES (?)'
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
	file = open('fullAST.txt')
	obj = json.loads(file.read())
	file.close()
	return obj[0]

def getMethodFqnRelativeToVariant(function):
	fileNameFromRoot = function['src']
	nestedPathWithinFile = function['filepath']
	functionHeader = function["header"]
	fileNameRelativeToVariant = FQNUtils.getRelativeFilePathWithinVariant(fileNameFromRoot)
	methodFQN = FQNUtils.getFullMethodPath(fileNameRelativeToVariant, nestedPathWithinFile, functionHeader)
	return methodFQN


def insertVariants(sortedVariants):
	conn = sqlite3.connect(DB_FILE_NAME)

	for variant in sortedVariants:
		conn.execute(VARIANT_INSERT_QUERY, [variant])

	conn.commit()
	conn.close()

def createDbAndInitialTables():
	if (os.path.exists(DB_FILE_NAME)):
		os.remove(DB_FILE_NAME)
	conn = sqlite3.connect(DB_FILE_NAME)
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


def main():
	createDbAndInitialTables()

	ast = readASTFile()
	variantsToFunctionsMap, variantsToInvocationsMap = getFunctionsAndInvocationsInVariants(ast)

	variantNames = variantsToFunctionsMap.keys()
	variantNames.sort()
	insertVariants(variantNames)

	conn = sqlite3.connect(DB_FILE_NAME)
	prevVariantGraph = None

	for i in range(0, len(variantNames)):
		variant = variantNames[i]
		graph = buildGraph(variantsToFunctionsMap[variant], variantsToInvocationsMap[variant])
		insertNodesToDb(i, variantNames, variantsToFunctionsMap, graph, prevVariantGraph, conn)
		prevVariantGraph = graph

	conn.close()

main()


'''

{
	u'src': u'/hexcom/2014-05-22-13:38:32/js/entities.js',
	u'end': 4251,
	u'filepath': u'/Clock(sideLength)',
	u'header': u'addBlock()',
	u'length': 474,
	u'start': 3777,
	u'contents': u'this.addBlock = function(block) {\n\t\tblock.settled = 1;\n\t\tblock.tint = .6;\n\t\tvar lane = this.sides - block.lane;//  -this.position;\n\t\tlane += this.position;\n\t\twhile (lane < 0) {\n\t\t\tlane += this.sides;\n\t\t}\n\t\tlane = lane % this.sides;\n\t\tblock.distFromHex = MainClock.sideLength / 2 * Math.sqrt(3) + block.height * this.blocks[lane].length;\n\t\tthis.blocks[lane].push(block);\n\t\tblock.parentArr = this.blocks[lane];\n\t\tconsolidateBlocks(this, lane, this.blocks[lane].length - 1);\n\t};'
  },
'''

