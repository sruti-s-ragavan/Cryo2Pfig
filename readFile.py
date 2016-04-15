import re
import json
import os, sys
import sqlite3
import uuid
from fQNUtils import FQNUtils


def getVariantName(filename):
	regex = re.compile('/hexcom/([^/]*)/.*')
#r'/hexcom/([^/]*)/.*'            ([0-9].*[0-9])
	match = regex.match(filename)
	if match == None:
		raise "No such file"
	return match.groups()[0]

def getFilePath(path):
	regex = re.compile('/[^h0-9]\w.*')
	match = regex.match(path)
	if match == None:
		return ""
	return match.groups()[0]

def main():
	variantstoFunctionsMap = {}
	file = open('fullAST.txt')
	obj = json.loads(file.read())
	variant_functions = obj[0]

	for variant in variant_functions:
		functions_list = variant['functions']

		if len(functions_list)>0:
			file_name = functions_list[0]['src']
			variant_name = getVariantName(file_name)

			if variant_name in variantstoFunctionsMap:
				variantstoFunctionsMap[variant_name].extend(functions_list)
			else:
				variantstoFunctionsMap[variant_name] = functions_list
	file.close()
	
	db_name= "variantstofunctions.db"
	if(os.path.exists(db_name)):
		os.remove(db_name)
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('create table variantstofunctions(method varchar(30), start varchar(20), end varchar(20), body TEXT)')
	conn.commit()

	variant_keys = variantstoFunctionsMap.keys()
	variant_keys.sort()
	index = 0
	print variantstoFunctionsMap['2014-05-17-07:18:41']
	for variant in variant_keys:
		for functions in variantstoFunctionsMap[variant]:
			if index == 0:
				methodFQN = FQNUtils.getFullMethodPath(functions['filepath'],functions['header'])
				c.execute('insert into variantstofunctions values (?,?,?,?)', [methodFQN, getVariantName(functions['src']), getVariantName(functions['src']), functions['contents']])
			else:
				method_body = functions['contents']
				function_name = functions['header']
				file_name = functions['filepath']
				current_variant_name = getVariantName(functions['src'])
				var = variantstoFunctionsMap[variant_keys[index-1]]
				for each in var:
					if each['header'] == function_name: #and each['filepath'] == file_name:
							if each['contents'] == method_body:
							#	print "Here methods are same!"
								methodFQN = FQNUtils.getFullMethodPath(each['filepath'],each['header'])
								c.execute('update variantstofunctions set end = ? where method = ? and body = ?',(current_variant_name, methodFQN, method_body))
							else:
							#	print "None same"
								methodFQN = FQNUtils.getFullMethodPath(functions['filepath'],functions['header'])
								c.execute('insert into variantstofunctions values (?,?,?,?)', [methodFQN, getVariantName(functions['src']), getVariantName(functions['src']), functions['contents']])
		index += 1
	conn.commit()
	c.close()

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
