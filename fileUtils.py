import os
import re
import sqlite3

class fileUtils:

    @staticmethod
    def getOffset(self, rootdir, document_name, line, column):

        #Calculates TSOs for changelogs
        count = 1
        offset = 0

        completeFilePath = rootdir + document_name

        #This is a hack for a participant who copied Current and created Current 2
        completeFilePath = completeFilePath.replace("Current 2", "Current")

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
    def getVariantName(filename):
        regex = re.compile('/hexcom/([^/]*)/.*')
        match = regex.match(filename)
        if match == None:
            raise Exception("No such file: " + filename)
        return match.groups()[0]


    @staticmethod
    def getChangelogFromDb(filePath):

        #Returns the changelog content for a particular variant which is used in logconverter for event_tuple generation for changelogs.
        DB_FILE_NAME = "variations_topologyAndTextSimilarity.db"
        GET_CHANGELOG_QUERY = 'SELECT CHANGELOG FROM VARIANTS WHERE NAME = ?'
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()

        variantName = fileUtils.getVariantName(filePath)
        c.execute(GET_CHANGELOG_QUERY, [variantName])
        changelog =  (c.next()[0]).strip()

        return changelog


    @staticmethod
    def getWeight():

        #This weight calculation logic was just for trial purposes. This calculates what weights get assigned
        #to each changelog based on how many words the changelog has in common with the goalwords.
        DB_FILE_NAME = "variations_topologyAndTextSimilarity.db"
        GET_CHANGELOG_CONTENT_QUERY = 'SELECT CHANGELOG FROM VARIANTS WHERE NAME = ?'

        goalWordsFrequency = {}
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        changelogScoresFile = open('changelogScores.txt','w')

        #Normally, this would be the input from the bug report
        goalWords = ['score',
                     'indicator',
                     'above', 'hexagon',
                     'like', 'used', 'exception', 'text',
                     'color', 'which', 'should', 'changed',  'black',
                     'score', 'calculated', 'differently', 'now', 'than',
                     'used', 'wants', 'stay', 'Users', 'have', 'requested', 'that', 'put',
                     'back', 'bonus', 'multiplier', 'parentheses', 'next',  'score']

        #The variants below were hard-coded on a trial basis. If this weight calculation logic is ever to be used,
        #get these variants from the DB.
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

    @staticmethod
    def readFile():
        #D09 has changelog navs interleaved between sourcecode navs.
        # The following code removes the changelogs navs from the results file
        # and retains navs to sourcecode files only
        # The list in the 'if' condition contains the sourcecode navs.
        reg = re.compile('([^\\t]+)')
        pathToFile = '/Users/eecs/Desktop/temp_withchangelogs_withgoalwords/d09/pfis_history_spread2__DM4.txt'
        fileRead = open(pathToFile, 'r')
        newFileToWrite = open('SourceCodeNavsOnly.txt', 'w+')

        for line in fileRead:
            start = reg.match(line)

            try:
               val = int(start.groups()[0])
            except Exception:
                continue

            if val in [56,57,59,61,62,63,64,65,66,67,79,80,81,82,83,97,98,99,100,101,102,103,104]:
                continue
            newFileToWrite.write(line)


if __name__ == '__main__':
    fileUtils.readFile()

