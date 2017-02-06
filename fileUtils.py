import os
import re
import sqlite3

class fileUtils:

    @staticmethod
    def getOffset(self, rootdir, document_name, line, column):

        count = 1
        offset = 0

        completeFilePath = rootdir + document_name

        #This is a hack for a participant who copied Current and created Current 2
        completeFilePath.replace("Current 2", "Current")

        file = open(completeFilePath, 'r')

        while (count <= line):
            if (count == line):
                offset += column
                break
            count += 1
            lengthofline = len(file.readline()) - 1
            offset += lengthofline

        return offset

    @staticmethod
    def readChangelogs():

        DB_FILE_NAME = "variations_topologyAndTextSimilarity.db"
        CHANGELOG_INSERT_QUERY = 'UPDATE VARIANTS SET CHANGELOG = ? WHERE NAME = ?'
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        root = './jsparser/src/hexcom'

        for folder in os.listdir(root):

            message = ''

            if 'Store' in folder:
                continue

            changelog = open(os.path.join(root, folder, 'changes.txt'), 'r')
            linelist = changelog.readlines()

            for line in linelist:
                if re.match('commit|Merge|Author|Date', line) or line == '':
                    continue
                else:
                    if line in message:
                        continue
                    else:
                        message = message + ' ' + line

            message.strip()
            c.execute(CHANGELOG_INSERT_QUERY, [message, folder])
            # message = folder + ': ' + message + '\n'
            # with open("test1.txt", "a") as myfile:
            #     myfile.write(message)

        c.close()
        conn.commit()



    @staticmethod
    def getWeight():

        DB_FILE_NAME = "variations_topologyAndTextSimilarity.db"
        GET_CHANGELOG_CONTENT_QUERY = 'SELECT CHANGELOG FROM VARIANTS WHERE NAME = ?'

        goalWordsFrequency = {}
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        changelogScoresFile = open('changelogScores.txt',pfis3'w')

        goalWords = ['score',
                     'indicator',
                     'above', 'hexagon',
                     'like', 'used', 'exception', 'text',
                     'color', 'which', 'should', 'changed',  'black',
                     'score', 'calculated', 'differently', 'now', 'than',
                     'used', 'wants', 'stay', 'Users', 'have', 'requested', 'that', 'put',
                     'back', 'bonus', 'multiplier', 'parentheses', 'next',  'score']

        variantsVisited = ['2014-05-17-16:17:28',
                     '2014-05-17-15:22:12', '2014-05-17-15:22:12',
                     'Current', '2014-07-20-18:47:08', '2014-07-20-18:47:08',
                     '2014-05-17-16:17:28', '2014-05-17-15:22:12', '2014-05-17-14:19:23', '2014-05-17-14:28:15',
                     '2014-05-17-14:37:52', '2014-05-17-14:38:11', '2014-05-17-15:22:12', '2014-05-17-15:22:12', '2014-05-18-08:43:49',
                     '2014-05-17-16:29:51', '2014-05-17-16:26:31', '2014-05-17-16:23:59', '2014-05-17-16:21:22', '2014-05-17-16:21:19', '2014-05-18-08:49:27', '2014-05-18-11:12:33']

        for word in goalWords:
            if word in goalWordsFrequency:
                goalWordsFrequency[word] += 1

            else:
                goalWordsFrequency[word] = 1


        for variant in set(variantsVisited):
            changelogScore = 0

            c.execute(GET_CHANGELOG_CONTENT_QUERY, [variant])
            changelogWordsArray = c.fetchone()[0].split()

            for unicodeWord in changelogWordsArray:
                word = str.lower(str(unicodeWord))
                if word in goalWordsFrequency:
                    changelogScore += goalWordsFrequency[word]

                else:
                    continue

            changelogScoresFile.write(variant + ': ' + str(changelogScore) + '\n')

        c.close()


if __name__ == '__main__':
    fileUtils.getWeight()
