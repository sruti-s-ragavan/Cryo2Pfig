import sqlite3
import sys
conn = sqlite3.connect(sys.argv[1])
c = conn.cursor()
array = []

for row in c.execute('''select * from logger_log WHERE action like "Text selection%"'''):
	array.append(row)
i=0 
while array[i] != None:
	if array[i][3] == "Text selection":
		if array[i+1] == None:
			break
		elif array[i+1][3] == "Text selection offset":
			insertThis = int(array[i+1][5]) - len(array[i][5])
			c.execute("UPDATE logger_log SET referrer=? WHERE 'index'=?", [str(insertThis), array[i][0]])
			i+=2
		else:
			i+=1
	else:
		if array[i+1] == None:
			break
		else:
			i+=1
conn.commit()


