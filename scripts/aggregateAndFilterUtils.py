import os
import sys

def readFile(fileName, neededIndexes):
    f = open(fileName, "r")
    allValues = []

    line = f.readline() #Skip header line

    line = f.readline()
    while (line != None and line.strip() != ''and "hit rates" not in line.lower()):
        line = line.replace("\n", "")
        line = line.replace("\r", "")
        arr = line.split("\t")
        values = [arr[i] for i in neededIndexes]
        allValues.append(values)
        line = f.readline()

    f.close()
    return allValues

def readColsNeeded(fileName, neededColumns):
    def isNeeded(colName):
        cleanedName = getCleanedName(colName)

        # print neededColumns
        if cleanedName in neededColumns:
            return True
        else:
            return False

    f = open(fileName, "r")
    line = f.readline()
    line = line.replace("\r", "").replace('\n', "")

    arr = line.split("\t")
    f.close()

    neededIndexes = [i for i in range(0, len(arr)) if isNeeded(arr[i])]
    colNames = [arr[index] for index in neededIndexes]

    return(colNames, neededIndexes)


def getCleanedName(rawName):
    headerRowCleaned = rawName.replace("-V", "")
    headerRowCleaned = headerRowCleaned.replace("DM1", "").replace("DM2", "").replace("DM3", "").replace("DM4", "")
    headerRowCleaned = headerRowCleaned.replace("__", "")
    return headerRowCleaned

def printAvailableModels():
    filePath = os.path.join(sys.argv[1], "c06", "all-hitRates.txt")
    f = open(filePath, "r")
    headerRow = f.readline().replace("\r", "").replace("\n", "")
    cols = getCleanedName(headerRow).split("\t")[1:]
    models = set([col for col in cols])
    allModels = list(models)
    allModels.sort(key=len)
    print allModels
    f.close()


def main():
    #printAvailableModels()
    outputDir = sys.argv[1]


    groups =[{ "name": "Group-1", "participants": ["d09", "d12"]},
            { "name": "Group-2", "participants": ["c06", "c07", "d08", "d11", "d13"]}]

    colNames = None
    neededCols = ['PFIS with history, spread2', 'Recency', 'Source Topology',
                  'TF-IDF (method)', 'Recency & Source Topology & TF-IDF (method)',
                  'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10']
    for group in groups:
        aggregates = []
        participants_ = group["participants"]
        for participant in participants_:
            allHitRatesFilePath = os.path.join(outputDir, participant, "all-hitRates.txt")
            colNames, neededIndexes = readColsNeeded(allHitRatesFilePath, neededCols)
            if len(neededIndexes) == 0:
                print "No columns selected"
                sys.exit(2)
            hitRateValues = readFile(allHitRatesFilePath, neededIndexes)

            if len(aggregates) == 0:
                for i in range(0, len(hitRateValues)):
                    row = [float(val) for val in hitRateValues[i]]
                    aggregates.append(row)
            else:
                for i in range(0, len(hitRateValues)):
                    for j in range(0, len(hitRateValues[i])):
                        aggregates[i][j] = aggregates[i][j] + float(hitRateValues[i][j])


        for i in range(0, len(aggregates)):
            for j in range(0, len(aggregates[i])):
                aggregates[i][j] = aggregates[i][j] / len(participants_)

        outputFile = os.path.join(outputDir, group["name"]+".txt")
        f = open(outputFile, "w")
        f.write("\t".join(colNames) + "\n")

        for row in aggregates:
            rowStr = [str(i) for i in row]
            rowStr = "\t".join(rowStr) + "\n"
            f.write(rowStr)


        f.close()




if __name__ == "__main__":
    main()
    # printAvailableModels()


#['Recency', 'Adjacency', 'Frequency', 'Source Topology', 'TF-IDF (method)', 'Working Set, delta 10', 'Undirected Call Graph', 'PFIS with history, spread2',
#
# 'Frequency & Recency', 'Adjacency & Recency',  'Adjacency & Frequency',
# 'Recency & Source Topology', 'Recency & TF-IDF (method)', 'Frequency & Source Topology',
# 'Adjacency & TF-IDF (method)', 'Frequency & TF-IDF (method)', 'Adjacency & Source Topology', 'Recency & Working Set, delta 10',
# 'Recency & Undirected Call Graph', 'Adjacency & Frequency & Recency', 'Adjacency & Working Set, delta 10', 'Adjacency & Undirected Call Graph',
# 'Frequency & Undirected Call Graph', 'Frequency & Working Set, delta 10', 'Source Topology & TF-IDF (method)',
#
# 'Frequency & Recency & Source Topology', 'Adjacency & Recency & TF-IDF (method)', 'Frequency & Recency & TF-IDF (method)',
# 'Adjacency & Recency & Source Topology', 'Adjacency & Frequency & Source Topology', 'TF-IDF (method) & Undirected Call Graph',
# 'Source Topology & Undirected Call Graph', 'Adjacency & Frequency & TF-IDF (method)', 'Source Topology & Working Set, delta 10',
# 'TF-IDF (method) & Working Set, delta 10', 'Frequency & Recency & Working Set, delta 10', 'Recency & Source Topology & TF-IDF (method)',
# 'Adjacency & Recency & Working Set, delta 10', 'Adjacency & Recency & Undirected Call Graph', 'Frequency & Recency & Undirected Call Graph',
# 'Undirected Call Graph & Working Set, delta 10', 'Adjacency & Source Topology & TF-IDF (method)', 'Adjacency & Frequency & Working Set, delta 10',
# 'Frequency & Source Topology & TF-IDF (method)', 'Adjacency & Frequency & Undirected Call Graph', 'Recency & Source Topology & Undirected Call Graph',
#  'Recency & Source Topology & Working Set, delta 10', 'Adjacency & Frequency & Recency & TF-IDF (method)', 'Recency & TF-IDF (method) & Undirected Call Graph',
#
# 'Adjacency & Frequency & Recency & Source Topology', 'Recency & TF-IDF (method) & Working Set, delta 10',
# 'Adjacency & Source Topology & Working Set, delta 10', 'Frequency & Source Topology & Working Set, delta 10',
# 'Adjacency & Source Topology & Undirected Call Graph', 'Frequency & TF-IDF (method) & Undirected Call Graph',
# 'Frequency & Source Topology & Undirected Call Graph', 'Adjacency & TF-IDF (method) & Working Set, delta 10',
# 'Frequency & TF-IDF (method) & Working Set, delta 10', 'Adjacency & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Recency & Source Topology & TF-IDF (method)',
# 'Recency & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & Working Set, delta 10',
# 'Frequency & Recency & Source Topology & TF-IDF (method)', 'Adjacency & Frequency & Recency & Undirected Call Graph', 'Source Topology & TF-IDF (method) & Working Set, delta 10', 'Adjacency & Undirected Call Graph & Working Set, delta 10', 'Frequency & Undirected Call Graph & Working Set, delta 10', 'Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Frequency & Source Topology & TF-IDF (method)', 'Adjacency & Recency & TF-IDF (method) & Undirected Call Graph', 'Frequency & Recency & TF-IDF (method) & Working Set, delta 10', 'Frequency & Recency & Source Topology & Working Set, delta 10', 'Frequency & Recency & Source Topology & Undirected Call Graph', 'Adjacency & Recency & Source Topology & Working Set, delta 10', 'Adjacency & Recency & Source Topology & Undirected Call Graph', 'Frequency & Recency & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Recency & TF-IDF (method) & Working Set, delta 10', 'Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Source Topology & Undirected Call Graph', 'TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & TF-IDF (method) & Working Set, delta 10', 'Adjacency & Frequency & Source Topology & Working Set, delta 10', 'Adjacency & Frequency & TF-IDF (method) & Undirected Call Graph', 'Frequency & Recency & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method)', 'Recency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Recency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Recency & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Frequency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Frequency & Undirected Call Graph & Working Set, delta 10', 'Frequency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Adjacency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Frequency & Recency & Source Topology & Working Set, delta 10', 'Adjacency & Frequency & Recency & Source Topology & Undirected Call Graph', 'Recency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Recency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Frequency & Recency & TF-IDF (method) & Working Set, delta 10', 'Frequency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Frequency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Frequency & Recency & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Recency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Frequency & Recency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Adjacency & Frequency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Frequency & Recency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Frequency & Recency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Recency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Recency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method) & Working Set, delta 10', 'Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph', 'Adjacency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Frequency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & Source Topology & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Frequency & Recency & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Adjacency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10', 'Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10',
# 'Adjacency & Frequency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10',
#  'Adjacency & Frequency & Recency & Source Topology & TF-IDF (method) & Undirected Call Graph & Working Set, delta 10']
