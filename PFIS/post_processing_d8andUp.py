import os
import sys
import shutil
import sqlite3
import subprocess
from navigationClassifier import NavigationClassifier

conn = ''
c = ''
nav_list = []
id = 0
id_tso = 600000
user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
agent = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
tso_string = "Text selection offset"

INSERT_QUERY = "insert into logger_log values(?,?,?,?,?,?,?,?);"


def manualNavs(sourceFile, outputFile, navFile):
    def copyAndOpenDb(source, dest):
        #TODO: Duplicate copy, eliminate this
        global conn,c, id
        shutil.copyfile(source, dest)
        conn = sqlite3.connect(dest)
        c = conn.cursor()
        c.execute('select "index" from logger_log order by "index" desc;')
        id = c.next()[0] + 1


    def readNewNavsFileIntoDb(path):
        global id
        navData = open(path)
        for line in navData:
            cols = line.rstrip('\r\n').split('\t')
            if cols[1] == 'New java file':
                newJavaFile(cols[0], cols[2], cols[3], '-1') #incorrect time_elapsed. Won't fix unless necessary
            id+=1
        navData.close()

    def newJavaFile(timestamp, path, fileName, elapsed_time):
        global conn,c,agent, id
        path = path+ '/' + fileName + '.js'

        print "Adding Header: ", path

        fakeHeader = path + ';.PFIGFileHeader()V'
        c.execute(INSERT_QUERY,
            (id, user, timestamp, "Method declaration", path, fakeHeader, agent, elapsed_time))
        id += 1
        c.execute(INSERT_QUERY,
            (id, user, timestamp, "Method declaration offset", fakeHeader, 0, agent, elapsed_time))
        id += 1
        c.execute(INSERT_QUERY,
            (id, user, timestamp, "Method declaration length", fakeHeader, len(fileName), agent, elapsed_time))
        id += 1
        c.execute(INSERT_QUERY,
            (id, user, timestamp, "Method declaration scent", fakeHeader, fileName, agent, elapsed_time))
        conn.commit()

    copyAndOpenDb(sourceFile, outputFile)
    readNewNavsFileIntoDb(navFile)



def generate_predictions(inputDbFile, outputFolder):
    projectRootDirectory = os.path.dirname(os.getcwd())
    sourceDirectory = os.path.join(projectRootDirectory, "jsparser/src")

    print "Calling PFIS.. "
    subprocess.call(["python","pfis3/src/python/pfis3.py",
                         "-l", "JS",
                         "-s", "je.txt",
                         "-d", inputDbFile,
                         "-p", sourceDirectory,
                         "-o", outputFolder,
                        "-x", "algorithm-config.xml",
                        "-n", os.path.join(outputFolder,"top-predictions")
                     ])

def copyDatabase(dbpath, newdbpath):
    print "Making a working copy of the database..."
    shutil.copyfile(dbpath, newdbpath)
    print "Done."

def main():
    sourceFile = sys.argv[1]
    outputFolder = "results"

    print "Generating Predictions ; Running PFIS"
    generate_predictions(sourceFile, outputFolder)

    # print "Updating navigation types for analysis..."
    #
    # all_files = os.listdir(outputFolder)
    # prediction_files = [f for f in all_files if f.endswith(".txt")]
    #
    # for prediction_file in prediction_files:
    #     print "Adding extra details to: ", prediction_file
    #     pfisHistoryPath = os.path.join(outputFolder, prediction_file)
    #     navClassifier = NavigationClassifier(pfisHistoryPath)
    #     navClassifier.updateNavTypes()

if __name__ == "__main__":
    main()