import os, sys
import MySQLdb
import sqlite3
import mysql

path = "/home/bhargav/Cryo2Pfig/jsparser/src/hexcom"
dirs = os.listdir(path)
dirs.sort()
 
db_name= "variants.db"
var = 0
if(os.path.exists(db_name)):
        os.remove(db_name)
conn = sqlite3.connect('variants.db')
c = conn.cursor()
c.execute('create table variants(index_num int(10), variant_name varchar(20))')
conn.commit()


for file in dirs:
        c.execute('insert into variants values (?,?)', [var,file])
        var = var+1
c.execute('delete from variants where variant_name =".c9" ')
conn.commit()
c.close()


