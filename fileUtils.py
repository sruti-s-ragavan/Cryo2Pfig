class fileUtils:

    @staticmethod
    def getOffset(self, document_name, line, column):

        count = 1
        offset = 0
        REPLACE_PATH = '/hexcom/Current/'
        PATH_PREFIX_TO_FILE = "/Users/eecs/VFT/Cryo2Pfig/jsparser/src"

        if('Current 2' in document_name):
            newpath = document_name[17:]
            completeFilePath = PATH_PREFIX_TO_FILE + REPLACE_PATH + newpath
        else:
            completeFilePath = PATH_PREFIX_TO_FILE + document_name

        file = open(completeFilePath, 'r')

        while (count <= line):
            if (count == line):
                offset += column
                break
            count += 1
            lengthofline = len(file.readline()) - 1
            offset += lengthofline

        return offset