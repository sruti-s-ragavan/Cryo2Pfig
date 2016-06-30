import sys
import os
PLOT_FOLDER_NAME = "PlotData"

def main():

	resultsFolder = sys.argv[1]
	navSegmentsFolder = sys.argv[2]

	folders = [folder for folder in os.listdir(resultsFolder) if os.path.isdir(os.path.join(resultsFolder,folder)) and not folder.startswith(".")]
	for participantName in folders:
		processParticipant(participantName, resultsFolder, navSegmentsFolder)


def processParticipant(participantName, resultsFolder, navSegmentsFolder):
	outputFolderName = os.path.join(resultsFolder, participantName, PLOT_FOLDER_NAME)
	if not os.path.exists(outputFolderName):
		os.makedirs(outputFolderName)
	combinedFileName = os.path.join(resultsFolder, participantName, "multi-factors.txt")
	navSegmentsFileName = os.path.join(navSegmentsFolder, participantName) + ".txt"
	headers = getFileHeaders(combinedFileName)
	allAlgorithms = headers[4:]
	graphTypes = set([algorithm.split("__")[-1] for algorithm in allAlgorithms])
	navSegments = getSegments(navSegmentsFileName)
	for graphType in graphTypes:
		outputFileName = os.path.join(outputFolderName, graphType) + ".txt"

		indexList = range(0, 4)
		indexList.extend([headers.index(algorithm) for algorithm in allAlgorithms if graphType in algorithm])

		writeGraphData(graphType, indexList, navSegments, combinedFileName, outputFileName)


def writeGraphData(graphType, indexList, navSegments, combinedFileName, outputFileName):

	combinedFile = open(combinedFileName, 'r')
	outputFile = open(outputFileName, 'w')

	print "Writing to:", outputFileName

	# Append header column
	outputRow = getDataAtIndex(getRowData(combinedFile.readline()), indexList)
	outputRow = [item.replace("__" + graphType, "") for item in outputRow]
	outputRow.append("Segment")
	writeLine(outputFile, outputRow)

	for segment in navSegments:
		outputRow = getDataAtIndex(getRowData(combinedFile.readline()), indexList)
		outputRow.append(segment)
		writeLine(outputFile, outputRow)

	# Append hit rates
	outputRow = getDataAtIndex(getRowData(combinedFile.readline()), indexList)
	outputRow.append("")
	writeLine(outputFile, outputRow)

	combinedFile.close()
	outputFile.close()


def writeLine(outputFile, outputRow):
	outputFile.writelines(["\t".join(outputRow) + "\n"])


def getFileHeaders(combinedFileName):
	combinedFile = open(combinedFileName, 'r')
	headerRow = combinedFile.readline()
	combinedFile.close()
	headers = getRowData(headerRow)
	return headers


def getDataAtIndex(rowData, indexList):
	outputRow = [rowData[index] for index in indexList]
	return outputRow


def getSegments(fileName):
	file = open(fileName, 'r')
	segments = []

	line = file.readline()

	while True:
		line = file.readline()
		if line == '' or line is None:
			break
		data = getRowData(line)
		segments.append(data[-1])

	file.close()
	return segments


def getRowData(row):
	rowCleaned = row.replace('\n', "")
	tokens = rowCleaned.split('\t')
	return tokens


if __name__ == "__main__":
	main()