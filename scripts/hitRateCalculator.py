import os

def readFile(fileName, neededIndexes):
    f = open(fileName, "r")
    allValues = []

    line = f.readline() #Skip header line

    line = f.readline()
    while (line != None and "Hit rates" not in line):
        line = line.replace("\n", "")
        line = line.replace("\r", "")
        arr = line.split("\t")
        values = [arr[i] for i in neededIndexes]
        allValues.append(values)
        line = f.readline()

    f.close()
    return allValues

def readColsNeeded(fileName):
    f = open(fileName, "r")
    line = f.readline()
    line = line.replace('\n', "")

    arr = line.split("\t")
    print arr

    f.close()

    neededColumns = ["Adjacency",
                     #"Frequency",
                     #"PFIS with history, spread2",
                     "Recency",
                     'Adjacency & Recency',
                     #"TF-IDF (method)",
                     #"Working Set, delta 10",
                     "Source Topology",
                     "Undirected Call Graph",
                    'Recency & Source Topology',
                    #'Recency & TF-IDF (method)',
                    # "Recency & Source Topology & TF-IDF (method)",
                    'Adjacency & Recency & Source Topology',
                    'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method)',
                     "Adjacency & Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10",
                     "Segment"]

    neededIndexes = [i for i in range(0, len(arr)) if arr[i] in neededColumns]
    colNames = [arr[index] for index in neededIndexes]
    return(colNames, neededIndexes)

def getHitRates(participant, values, segment):
    thresholds = [5,10,20,30,40,50,60,70,80,90,100]
    navCount = len(values)
    nModels = len(values[0])-1

    allHitRates = []
    allUnknownRates = []

    for threshold in thresholds:
        hitCounts = [0] * nModels
        unknownCounts = [0] * nModels
        for i in range(0,navCount):
            row = values[i]
            if row[len(row)-1] == None: #segment
                continue
            else:
                for j in range(0, nModels):
                    if float(row[j]) <= threshold:
                        hitCounts[j] = hitCounts[j] + 1
                    if float(row[j]) == 999999:
                        unknownCounts[j] = unknownCounts[j] + 1

        hitRates = [float(hitCount) / float(navCount) for hitCount in hitCounts ]
        allHitRates.append(hitRates)

        unknownRates = [float(unknownCount) / float(navCount) for unknownCount in unknownCounts ]
        allUnknownRates.append(unknownRates)

    return (allHitRates, allUnknownRates)

def getAverages(hitRates):
    thresholds = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    nParticipants = len(hitRates)
    nRows = len(thresholds)
    nCols = len(hitRates[0][1])
    averages = [[0.0]*nCols]*nRows


    for rowIndex in range(0,nRows):
        for colIndex in range(0, nCols):
            sum = 0
            for i in range(0, nParticipants):
                sum = sum + hitRates[i][rowIndex][colIndex]
            average = float(sum) / nParticipants
            averages[rowIndex][colIndex] = average
        rowStr = [str(i) for i in averages[rowIndex]]
        print "\t".join(rowStr)

    return averages

def main():
    group1 = ["d09", "d12"]
    group2 = ["c07", "d08", "d11", "d13", "c06"]
    combined = ["d09", "d12","c07", "d08", "d11", "d13", "c06"]

    fileNames = ['NoCollapse.txt', 'PureEquivalenceCollapse.txt', 'TextEquivalenceCollapse.txt', 'VariantUnaware.txt']

    (colNames, neededIndexes) = readColsNeeded("/Users/eecs/VFT/Cryo2Pfig/PFIS/results/db/d09/PlotData/NoCollapse.txt")

    segment = "-"
    for fileName in fileNames:
        print fileName
        hitRates = []
        unknownRates = []
        for participant in combined:
            folderName = "/Users/eecs/Dropbox/analysis-jul5/db/" + participant + "/PlotData"
            values = readFile(os.path.join(folderName, fileName), neededIndexes)
            hitRateData, unknownRateData = getHitRates(participant, values, segment)
            hitRates.append(hitRateData)
            unknownRates.append(unknownRateData)

        print "\t".join(colNames)
        print "=========== hit rates ============"
        averageHitRate = getAverages(hitRates)
        print "=========== unknown rates ============"
        averageUnknownRates = getAverages(unknownRates)
        print "======================="

if __name__ == "__main__":
    main()

