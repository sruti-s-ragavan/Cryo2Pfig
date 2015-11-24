import os
import sys
import shutil
import sqlite3
import subprocess
import multiprocessing

conn = ''
c = ''
nav_list = []
id = 0
id_tso = 600000
user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
agent = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
tso_string = "Text selection offset"

def resetGlobals():
    global conn,c,id,user,agent
    conn = ''
    c = ''
    id = 0
    nav_list = []
    user = 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
    agent = '8ea5d9be-d1b5-4319-9def-495bdccb7f51'
#Following code doesn't actually work...
def add_navs_without_tso(source):
    def add_tso(source, timestamp,doc_path):
        global id_tso
        conn = sqlite3.connect(source)
        c = conn.cursor()
        '2015-04-21 23:40:21.118000000'
        
        c.execute("insert into logger_log values(?,?,?,?,?,?,?);", (id, user, timestamp, tso_string, doc_path, 0, agent))
        id_tso +=1
        conn.commit()
    conn = sqlite3.connect(source)
    c = conn.cursor()

    result = c.execute("select * from logger_log order by timestamp").fetchall();
	# |index | user | timestamp | action | target | referrer | agent
    i = 0
    act_list = []
    temp_list = []
    full_list = []
    for row in result:
        if row[3] == "Part activated" and row[4][-2:]=='js' and '[B]' not in row[5]: #what is [B]?
            act_list.append(i)
        i+=1
    i=0
    while (i<len(act_list)):
        for j in range (act_list[i], len(result)):
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
            add_tso(source, set_of_rows[0][2], set_of_rows[0][5])
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
                newJavaFile(cols[0], cols[2], cols[3])
            id+=1
        navData.close()

    def newJavaFile(timestamp, path, fileName):
        global conn,c,agent, id
        path = path+ '/' + fileName +  '.js'
        fakeHeader = path + ';.PFIGFileHeader()V'
        c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);',
            (id, user, timestamp, "Method declaration", path, fakeHeader, agent))
        id += 1
        c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);',
            (id, user, timestamp, "Method declaration offset", fakeHeader, 0, agent))
        id += 1
        c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);',
            (id, user, timestamp, "Method declaration length", fakeHeader, len(fileName), agent))
        id += 1
        c.execute('insert into logger_log values (?, ?, ?, ?, ?, ?, ?);',
            (id, user, timestamp, "Method declaration scent", fakeHeader, fileName, agent))
        conn.commit()

    copyAndOpenDb(sourceFile, outputFile)
    readNewNavsFileIntoDb(navFile)

def db_splitter(source, dest):
    def create_db(dest):
        if(not(os.path.exists(dest))):
            os.makedirs(dest)
        conn2 = sqlite3.connect(dest + '/db')
        c2 = conn2.cursor()
        c2.execute('create table logger_log("index" int(10), user varchar(50), timestamp varchar(50), action varchar(50), target varchar(50), referrer varchar(50), agent varchar(50));')
        c2.close()

    def insert_into_new(timestamp, dest, source, num):
        create_db(dest)
        conn = sqlite3.connect(source+'temp'+ num)
        c = conn.cursor()
        conn2 = sqlite3.connect(dest + '/db')
        c2 = conn2.cursor()
        rows_up_to_timestamp = c.execute('select * from logger_log where timestamp<=? order by timestamp', [timestamp])
        for row in rows_up_to_timestamp:
            c2.execute('insert into logger_log values (?,?,?,?,?,?,?)',[row[0],row[1],row[2],row[3],row[4],row[5],row[6]])
        conn2.commit()
        c2.close()


    def fetch_all_text_selections_or_navs(source_db):
        global conn, c, id, nav_list
        conn = sqlite3.connect(source_db)
        c = conn.cursor()
        all_rows = c.execute("select * from logger_log where action = 'Text selection offset' order by timestamp;")
        i=0
        for row in all_rows:
            i +=1
            nav_list.append(row[2])
            print "Making new DB " + str(i)

    def create_db_until_each_nav(source, dest):
        i=0
        global nav_list
        while(i<len(nav_list)):
            print "multiprocessing "  + str(i);
            p=multiprocessing.Process(target=insert_into_new, args=(nav_list[i], dest + '/nav' + str(i), source,'',))
            p.start()
            if i+1<len(nav_list):
                q=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+1], dest + '/nav' + str(i+1), source,'1',))
                q.start()
            if i+2<len(nav_list):
                r=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+2], dest + '/nav' + str(i+2), source,'2',))
                r.start()
            if i+3<len(nav_list):
                s=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+3], dest + '/nav' + str(i+3), source,'3',))
                s.start()
            if p:
                p.join()
                while (not(p.exitcode == 0)):
                    os.remove(dest + '/nav' + str(i) + '/db')
                    p=multiprocessing.Process(target=insert_into_new, args=(nav_list[i], dest + '/nav' + str(i), source,'',))
                    p.start()
                    p.join()
            if q:
                q.join()
                while (not(q.exitcode == 0)):
                    os.remove(dest + '/nav' + str(i+1) + '/db')
                    q=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+1], dest + '/nav' + str(i+1), source,'1',))
                    q.start()
                    q.join()
            if r:
                r.join()
                while (not(r.exitcode == 0)):
                    os.remove(dest + '/nav' + str(i+2) + '/db')
                    r=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+2], dest + '/nav' + str(i+2), source,'2',))
                    r.start()
                    r.join()
            if s:
                s.join()
                while (not(s.exitcode == 0)):
                    os.remove(dest + '/nav' + str(i+3) + '/db')
                    s=multiprocessing.Process(target=insert_into_new, args=(nav_list[i+3], dest + '/nav' + str(i+3), source,'3',))
                    s.start()
                    s.join()
            i=i+4
    shutil.copyfile(source, source + 'temp')
    shutil.copyfile(source, source + 'temp1')
    shutil.copyfile(source, source + 'temp2')
    shutil.copyfile(source, source + 'temp3')
    fetch_all_text_selections_or_navs(source)
    create_db_until_each_nav(source,dest)
    os.remove(source + 'temp')
    os.remove(source + 'temp1')
    os.remove(source + 'temp2')
    os.remove(source + 'temp3')

def generate_predictions(dbFile):
    global nav_list
    # for i in range (0, len(nav_list)):
    #     if not os.path.exists(splitDir+'/nav'+str(i)+'/output'):
    #         os.makedirs(splitDir+'/nav'+str(i)+'/output')

    def call_pfis(dbFile):
        subprocess.call(["python","pfis3/src/python/pfis3.py", "-l", "JS", "-s", "je.txt", "-d", dbFile, "-p", "Cryo2Pfig/jsparser/src/hexcom"])

    def predict_all_navs():
        i=0
        while (i< len(nav_list)):
            print "Running PFIS on dir " + str(i)
            p=multiprocessing.Process(target=call_pfis, args=(i,))
            p.start()
            if i+1<len(nav_list):
                q=multiprocessing.Process(target=call_pfis, args=(i+1,))
                q.start()
            if i+2<len(nav_list):
                r=multiprocessing.Process(target=call_pfis, args=(i+2,))
                r.start()
            if i+3<len(nav_list):
                s=multiprocessing.Process(target=call_pfis, args=(i+3,))
                s.start()
            if p:
                p.join()
            if q:
                q.join()
            if r:
                r.join()
            if s:
                s.join()
            i=i+4

    print "Calling PFIS"
    #predict_all_navs()

    call_pfis(dbFile) #use this to run PFIS for a particular folder


def log_cat(splitDir,source):
    global nav_list
    line = ''
    cat_file = open(source+"_pfis_predictions.csv", 'a')
    for i in range(0, len(nav_list)):
        if os.path.exists(splitDir+'/nav'+str(i)+'/output/-PfisOutput-WithHistNoGoal.csv'):
            prediction_file = open(splitDir+'/nav'+str(i)+'/output/-PfisOutput-WithHistNoGoal.csv', 'r')
        else:
            continue
        cur_line = prediction_file.readline()
        prediction_file.close()
        if(cur_line == line):
            continue
        elif(cur_line != line):
            line = cur_line
            cat_file.write(cur_line)
    cat_file.close()
    cat_file = open(source+"_pfis_predictions.csv", 'r')
    prev_line = ''
    all_lines = ''
    for line in cat_file:
        t_line = line
        t_line = t_line.split(',')
        p_line = prev_line.split(',')
#        print line
#       print t_line
        if(len(t_line)>0 and len(p_line)>1 and (t_line[1] == p_line[1])):
            continue
        else:
            all_lines = all_lines + line
        prev_line = line
    cat_file = open(source+"_pfis_predictions_corr.csv", 'a')
#    print(all_lines[1])
    cat_file.write(all_lines)

sourceFile = sys.argv[1]
splitDir = sys.argv[2]
navFile = None
newDbFile = None

if (len(sys.argv) > 3): #manual navs for expand tree folders
    navFile = sys.argv[3];
    newDbFile = sourceFile + "_new_"
    print "Inserting Manual Navigations"
    manualNavs(sourceFile,newDbFile, navFile)
    sourceFile = newDbFile

print "Inserting manual TSO"
add_navs_without_tso(sourceFile)
# print "Splitting Databases"
# db_splitter(sourceFile, splitDir)
print "Generating Predictions ; Running PFIS"
generate_predictions(sourceFile)
print "Concatenating logs"
log_cat(splitDir, sourceFile)
