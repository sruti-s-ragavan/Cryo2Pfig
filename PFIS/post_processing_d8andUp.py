import os
import sys
import shutil
import sqlite3
import subprocess
import multiprocessing
from navigationClassifier import *

conn = ''
c = ''
nav_list = []
id = 0
id_tso = 600000
user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
agent = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
tso_string = "Text selection offset"

INSERT_QUERY = "insert into logger_log values(?,?,?,?,?,?,?,?);"
FIX_OFFSETS_TO_START_FROM_0_QUERY = "UPDATE logger_log SET referrer = referrer - 1 WHERE action like '%offset' AND referrer > 0"

def add_navs_without_tso(source):
    def add_tso(source, timestamp,doc_path, time_elapsed):
        global id_tso
        conn = sqlite3.connect(source)
        c = conn.cursor()

        c.execute(INSERT_QUERY, (id, user, timestamp, tso_string, doc_path, 0, agent, time_elapsed))
        id_tso +=1
        conn.commit()

    print "Adding manual TSO..."
    conn = sqlite3.connect(source)
    c = conn.cursor()

    result = c.execute("select * from logger_log order by timestamp").fetchall();
	# |index | user | timestamp | action | target | referrer | agent | elapsed_time

    i = 0
    open_tabs_list = []
    temp_list = []
    full_list = []

    for row in result:
        if row[3] == "Part activated" and row[4][-2:]=='js' and '[B]' not in row[5]:
            open_tabs_list.append(i)
        i+=1

    i=0
    while (i<len(open_tabs_list)):
        for j in range (open_tabs_list[i], len(result)):
            temp_list.append(result[j])
            if result[j][3] == "Part deactivated":
                break
        full_list.append(temp_list)
        temp_list = []
        i+=1
    for set_of_rows in full_list:
        has_tso = False
        for row in set_of_rows:
            if(row[3] == "Text selection offset"):
                has_tso = True
                break
        if(not(has_tso)):
            add_tso(source, set_of_rows[0][2], set_of_rows[0][5], set_of_rows[0][7])
        elif(has_tso):
            continue

def manualNavs(sourceFile, outputFile, navFile):
    def copyAndOpenDb(source, dest):
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


def fix_offsets_to_0_beginning(dbfile):
    conn = sqlite3.connect(dbfile)
    conn.execute(FIX_OFFSETS_TO_START_FROM_0_QUERY);
    conn.commit()
    conn.close()



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
                        "-x", "algorithm-config.xml"])

def main():
    sourceFile = sys.argv[1]
    outputFolder = "results"

    #optional nav file argument for manual navigations
    if (len(sys.argv) > 2): #manual navs for expand tree folders
        navFile = sys.argv[2];
        newDbFile = sourceFile + "_new_"
        print "Inserting Manual Navigations"
        manualNavs(sourceFile,newDbFile, navFile)
        sourceFile = newDbFile

    print "Fixing offsets"
    fix_offsets_to_0_beginning(sourceFile)

    print "Inserting manual TSO"
    add_navs_without_tso(sourceFile)

    print "Generating Predictions ; Running PFIS"
    generate_predictions(sourceFile, outputFolder)

    # print "Updating navigation types for analysis..."
    # pfisHistoryPath = os.path.join(outputFolder, "pfis_history.txt")
    # navClassifier = NavigationClassifier(pfisHistoryPath)
    # navClassifier.updateNavTypes()

if __name__ == "__main__":
    main()