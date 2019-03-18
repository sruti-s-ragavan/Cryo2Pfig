import sys
import re
import os

def getVariantName(loc):
	if loc.startswith('L'):
		loc = loc[1:]
	regex = re.compile('/hexcom/([^/]*)/.*')
	match = regex.match(loc)
	if match == None:
		raise Exception("Incorrect match: "+ loc)
	return match.groups()[0]

def writeToFile(outputFile, variantCount, participant):
	for variant in variantCount.keys():
		line = [participant, str(variant), str(variantCount[variant])]
		lineStr = "\t".join(line) + "\n"
		outputFile.write(lineStr)

def processNavsPerVariant(participantName, filePath, outputFile):

	variantCount = {}
	file = open(filePath, "r")
	line = file.readline()  # Header
	line = file.readline()

	while line != '':
		# Prediction	Timestamp	From loc	To loc	Elapsed_time	Segment_Foraging
		tokens = line.split("\t")
		if len(tokens) > 5:
			toLoc = tokens[3]

			variantName = getVariantName(toLoc)
			if variantName not in variantCount.keys():
				variantCount[variantName] = 0
			variantCount[variantName] += 1

			line = file.readline()


	file.close()
	writeToFile(outputFile, variantCount, participantName)

def processNavsPerSegment(participantName, filePath, outputFile):
	segmentStats = {}
	file = open(filePath, "r")
	line = file.readline()  # Header
	line = file.readline()
	while line != '':
		# Prediction	Timestamp	From loc	To loc	Elapsed_time	Segment_Foraging
		tokens = line.split("\t")
		if len(tokens) > 5:
			toLoc = tokens[3]
			segmentToken = tokens[5].split(",")[0]
			segment = segmentToken.replace("\r\n", "")
			variantName = getVariantName(toLoc)

			if segment not in segmentStats.keys():
				segmentStats[segment] ={}

			if variantName not in segmentStats[segment].keys():
					segmentStats[segment][variantName] = 0

			segmentStats[segment][variantName] += 1

			line = file.readline()
	file.close()

	for segment in segmentStats.keys():
		for variantName in segmentStats[segment]:
			row = [str(participantName), str(segment), str(variantName), str(segmentStats[segment][variantName])]
			outputFile.write("\t".join(row) + "\n")



def main():
	navSegmentsFolder = sys.argv[1]
	variantAggregatesFileName = "VariantAggregates.txt"
	segmentAggregatesFileName = "SegmentAggregates.txt"
	variantAggregatesFilePath = os.path.join(navSegmentsFolder, variantAggregatesFileName)
	segmentAggregatesFilePath = os.path.join(navSegmentsFolder, segmentAggregatesFileName)

	if os.path.exists(variantAggregatesFilePath):
		os.remove(variantAggregatesFilePath)

	if os.path.exists(segmentAggregatesFilePath):
		os.remove(segmentAggregatesFilePath)

	navSegmentsFiles = os.listdir(navSegmentsFolder)
	variantAggregatesOutputFile = open(variantAggregatesFilePath, "w")
	segmentAggregatesOutputFile = open(segmentAggregatesFilePath, "w")

	for fileName in navSegmentsFiles:
		if fileName.endswith(".txt"):
			filePath = os.path.join(navSegmentsFolder, fileName)
			print filePath
			participantName = fileName[:-4]
			processNavsPerVariant(participantName, filePath, variantAggregatesOutputFile)
			processNavsPerSegment(participantName, filePath, segmentAggregatesOutputFile)

	variantAggregatesOutputFile.close()
	segmentAggregatesOutputFile.close()



if __name__=="__main__":
	main()