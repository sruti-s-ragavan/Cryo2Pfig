import re
import json
import os, sys
import sqlite3
import uuid
from fQNUtils import FQNUtils

DB_FILE_NAME= "variantstofunctions.db"

CREATE_VARIANTS_TABLE_QUERY = 'CREATE TABLE VARIANTS(NUM INTEGER PRIMARY KEY AUTOINCREMENT, NAME VARCHAR(50))'
CREATE_PATCHES_TABLE_QUERY = 'CREATE TABLE VARIANTS_TO_FUNCTIONS(METHOD VARCHAR(30), START INTEGER, END INTEGER, BODY TEXT)'
VARIANT_INSERT_QUERY = 'INSERT INTO VARIANTS(NAME) VALUES (?)'
FUNCTION_INSERT_QUERY = 'INSERT INTO VARIANTS_TO_FUNCTIONS VALUES (?,?,?,?)'

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

def isVariant(f1, f2):
	if f1 == None or f2 == None:
		return False
	#TODO: fileName (src value) should exclude variant name from comparison
	# add filename part of f1['src'] == f2['src']
	if f1['header'] == f2['header']\
			and f1['filepath'] == f2['filepath'] \
			and f1['contents'] == f2['contents']:
		return True

	return False

def insertFunctionToDb(index, function, prevVarFunctions, conn):
	fileNameFromRoot = function['src']

	nestedPathWithinFile = function['filepath']
	functionHeader = function["header"]
	methodBody = function['contents']
	variantName = getVariantName(fileNameFromRoot)
	fileNameRelativeToVariant = FQNUtils.getRelativeFilePathWithinVariant(fileNameFromRoot)

	prevVariantOfFunction = None
	if prevVarFunctions != None:
		for f in prevVarFunctions:
			if isVariant(f, function):
				prevVariantOfFunction = f

	if prevVariantOfFunction == None:
		methodFQN = FQNUtils.getFullMethodPath(fileNameRelativeToVariant, nestedPathWithinFile, functionHeader)
		conn.execute(FUNCTION_INSERT_QUERY, [methodFQN, index, index, methodBody])
	else:
		#Update will break -- update where end = prev var name
		methodFQN = FQNUtils.getFullMethodPath(fileNameRelativeToVariant, nestedPathWithinFile, functionHeader)
		conn.execute(UPDATE_QUERY,[index, index-1, methodFQN, methodBody])
	conn.commit()

def insertVariants(sortedVariants):
	conn = sqlite3.connect(DB_FILE_NAME)
	for variant in sortedVariants:
		conn.execute(VARIANT_INSERT_QUERY, [variant])

	conn.commit()
	conn.close()

def main():

	ast = readASTFile()
	variantsToFunctionsMap = getFunctionsInVariants(ast)

	createDbAndInitialTables()

	variantNames = variantsToFunctionsMap.keys()
	variantNames.sort()
	insertVariants(variantNames)

	conn = sqlite3.connect(DB_FILE_NAME)
	for index in range(0, len(variantNames)):
		variant = variantNames[index]
		prevVariantFunctions = None

		if index > 0:
				prevVariantFunctions = variantsToFunctionsMap[variantNames[index-1]]

		for function in variantsToFunctionsMap[variant]:
			insertFunctionToDb(index, function, prevVariantFunctions, conn)

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


def getFunctionsInVariants(variant_functions):
	variantsToFunctionsMap = {}

	for variant in variant_functions:
		functions_list = variant['functions']
		if len(functions_list) > 0:

			file_name = functions_list[0]['src']
			variant_name = getVariantName(file_name)

			if variant_name in variantsToFunctionsMap:
				variantsToFunctionsMap[variant_name].extend(functions_list)
			else:
				variantsToFunctionsMap[variant_name] = functions_list

	return variantsToFunctionsMap


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





#print functions_list
#print variantstoFunctionsMap.keys()
#print variantstoFunctionsMap['2014-05-22-13:38:32']
#print len(variantstoFunctionsMap.keys())
#for i in range(0,5):
#	xyz = variantstoFunctionsMap.keys()[i]
#	print xyz
#	print variantstoFunctionsMap[xyz]
#src': u'/hexcom/2014-05-17-07:18:31/server.js',
	#u'end': 342,
	#u'filepath': u'',
	#u'header': u'handler (req, res)',
   # u'length': 253,
	#u'start': 89,
  #  u'contents'
'''
current= variantstoFunctionsMap['Current']
for functions in current:
	print functions['src']
'''
