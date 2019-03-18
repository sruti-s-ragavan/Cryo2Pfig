import re
import sqlite3
import sys, os


fileName = "variantsAndOutputViewed.txt"
if os.path.exists(fileName):
	os.remove(fileName)
sys.stdout = open(fileName, "a")
SELECT_QUERY = 'SELECT referrer FROM logger_log WHERE action = "Part activated"'


def getVariant(filename):
	regex = re.compile('.*hexcom/([^/]*)/.*')
	match = regex.match(filename)
	if match == None:
		return None
	return match.groups()[0]


def getInfo(dbName):
	checkedOutputArr = []
	variantsArr = []
	checkedReadmeArr = []
	checkedMethodsArr = []

	conn = sqlite3.connect(dbName)
	c = conn.cursor()
	fileList = c.execute(SELECT_QUERY).fetchall()

	for file in fileList:
		variantName = getVariant(file[0])
		if variantName is None:
			continue
		else:
			variantsArr.append(variantName)
			if file[0].startswith("[B]"):
				checkedOutputArr.append(variantName)
			if file[0].endswith(".txt"):
				checkedReadmeArr.append(variantName)
			if file[0].endswith(".js"):
				checkedMethodsArr.append(variantName)


	variantsArr.sort()

	print "The number of unique variants: ", len(set(variantsArr))
	for variant in set(checkedMethodsArr):
		print variant, '\n'
	print "Number of outputs viewed: ", len(set(checkedOutputArr))
	print "Number of readmes viewed: ", len(set(checkedReadmeArr))
	print "Number of variants in which JS files were visited: ", len(set(checkedMethodsArr))

def getDBNames(path):
	dbList = os.listdir(path)
	dbList.sort()

	for file in dbList:
		if ".db" not in file:
			dbList.remove(file)

	return dbList

def main():
	if len(sys.argv) is 1:
		raise Exception("Pass the path to the folder containing the DBs as a parameter")

	dbFolderPath = sys.argv[1]
	dbList = getDBNames(dbFolderPath)

	for db in dbList:
		print "Results for: ", db
		getInfo(os.path.join(dbFolderPath,db))
		print "--------\n"


if __name__=="__main__":
	main()