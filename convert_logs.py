import sys
import os
import subprocess
import sqlite3

def clean_source_dir():
    subprocess.call(['git', 'checkout', './jsparser/src/'])
    subprocess.call(['git', 'clean', '-xdf', './jsparser/src/'])

def convert_log(log_file_name, log_folder, db_folder):
    log_file = os.path.join(log_folder, log_file_name)
    file_name_without_extn = log_file_name[:-3]

    print "Converting: ", log_file
    output_txt_file = os.path.join(db_folder, file_name_without_extn) + "txt"
    args = ['python', 'logconverter.py', 'file', log_file, output_txt_file]
    output_log_name = os.path.join(db_folder, "_"+file_name_without_extn) + "log"
    output_log = open(output_log_name, "w")

    print "Logging to: ", output_log

    subprocess.call(args, stdout=output_log)
    print "Converted logs as Text file in: ", output_txt_file

def updateDbWithManualNavs(db, navs):
    file = open(navs, 'r')
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    for statement in file:
        cursor.execute(statement)

    conn.commit()
    file.close()

def add_manual_navs(db_folder, navs_folder):
    db_files = [f for f in os.listdir(db_folder) if f.endswith(".db")]
    for file_name in db_files:
        nav_file = os.path.join(navs_folder, file_name[:-2]+"sql")
        db_file = os.path.join(db_folder, file_name)
        if os.path.exists(nav_file):
            print "Updating manual navs: ", db_file
            print "Nav file: ", nav_file
            updateDbWithManualNavs(db_file, nav_file)

def main():
    if len(sys.argv)<3:
        raise Exception("Usage: python convert_logs.py <log_files_folder> <output_db_folder> <manual_nav_files_folder>")

    log_folder = sys.argv[1]
    db_folder_name = sys.argv[2]

    if not os.path.exists(log_folder):
        raise Exception("Usage: python convert_logs.py <log_files_folder> <output_db_folder> <manual_nav_files_folder>")

    clean_source_dir()

    db_folder_path = os.path.join(log_folder, db_folder_name)

    convert_logs(log_folder, db_folder_path)

    if len(sys.argv) == 4:
        manual_navs_path = sys.argv[3]
        add_manual_navs(db_folder_path, manual_navs_path)


def convert_logs(log_folder_path, db_folder_path):
    if not os.path.exists(db_folder_path):
        print "Creating folder: ", db_folder_path
        os.makedirs(db_folder_path)

    log_file_names = [f for f in os.listdir(log_folder_path)
                      if not os.path.isdir(os.path.join(log_folder_path, f))
                      and f.endswith(".log")]
    for log_file in log_file_names:
        convert_log(log_file, log_folder_path, db_folder_path)
        clean_source_dir()


if __name__ == '__main__':
    main()