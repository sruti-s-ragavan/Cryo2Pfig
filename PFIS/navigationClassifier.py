import re
import csv
import json

class NavigationClassifier:
    DESTINATION_VARIANT_NAME = "Current"

    #/hexcom/2014-05-26-10:18:35/js/view.js;.renderText(x"," y"," fontSize"," color"," text)
    #L/hexcom/Current/js_v9/Hex.js/Hex(sideLength);.rotate() -- nested methods
    METHOD_TARGET_REGEX = re.compile(r'L/hexcom/(.*?)/(.*?).js(.*?);.(.*?)\((.*?)')

    #/hexcom/Current/js_v9/view,UNKNOWN,0
    UNKNOWN_TARGET_REGEX =  re.compile(r'/hexcom/(.*?)/(.*?) at (.*?)')

    def __init__(self, csvPredictionFileName):
        self.fileName = csvPredictionFileName

    def updateNavTypes(self):
        csvFileHandle = open(self.fileName, 'r')
        self.navs = self.unpackNavs(csvFileHandle)
        csvFileHandle.close()

        self.addAdditionalDetails()

        csvFileHandle = open(self.fileName, 'w')
        self.writeBackToCsv(csvFileHandle)
        csvFileHandle.close()

    def addAdditionalDetails(self):
        for i in range(len(self.navs)):
            nav = self.navs[i]
            if i == 0:
                prevNav = None
            else:
                prevNav = self.navs[i - 1]
            self.updateBetweenVariantNav(nav, prevNav)
            self.updatePredictionAccuracyParams(nav)

    def updatePredictionAccuracyParams(self, nav):

        nav["accurate_variant"] = None
        nav["accurate_file"] = None
        nav["accurate_method"] = None

        row = nav["prediction_row_array"]
        if(row[2] != "999999"):
            #'[u\\'/hexcom/2014-05-26-09:30:45/js/view.js;.showModal(text"," secondaryText)\\']'
            predictions = eval(row[7])
            prediction = str(predictions[0])
            prediction_parts = self.getTargetPathParts(prediction)
            nav["accurate_variant"] = (prediction_parts[0].lower() == nav["variant_name"].lower())
            nav["accurate_file"] = (prediction_parts[1].lower() == nav["file_name"].lower())

            methodAccuracy= (prediction_parts[2].lower() == nav["method_name"].lower())

            #This is because a.js;.pfigheader() is not same as b.hs;.pfigheader()
            #But a.js;.render == b.js;.render because functions can be moved around
            if methodAccuracy == True and "pfigheader" in prediction_parts[2].lower():
                methodAccuracy = False

            nav["accurate_method"] = methodAccuracy

        self.__computeNavAccuracy(nav)
        self.__updatePercentageBasedRanking(nav)


    def __computeNavAccuracy(self, nav):
        def accuracy(val, level):
            if val == True:
                return "Right"+ " "+ level
            elif val == False:
                return "Incorrect"+ " " + level
            else:
                return ''

        variant = accuracy(nav["accurate_variant"], "variant")
        file = accuracy(nav["accurate_file"], "file")
        method = accuracy(nav["accurate_method"], "method")

        accuracy_str = 'NA'
        if variant != '' and file != '' and method != '':
            accuracy_str =  variant + " " + file + " " + method
        nav["accuracy"] = accuracy_str

    def __updatePercentageBasedRanking(self,nav):
        row = nav["prediction_row_array"]
        rank = float(row[2])
        out_of = float(row[3])
        if out_of == 0:
            nav["rank_percent"] = None
        else:
            nav["rank_percent"] = (rank / out_of) * 100.0


    def writeBackToCsv(self, fileHandle):
        fileHandle.write(self.headerRow)

        for nav in self.navs:
            rowString = self.arrayToTabSeparatedString(nav["prediction_row_array"])
            row = rowString + "\t" \
                             + str(nav["is_destination_variant"]) + "\t" \
                             + str(nav["is_between_variant"]) + "\t" \
                            + str(nav["accurate_variant"]) + "\t" \
                            + str(nav["accurate_file"]) + "\t" \
                            + str(nav["accurate_method"]) + "\t" \
                            + str(nav["rank_percent"]) + "\t" \
                            + str(nav["accuracy"]) + "\n"
            fileHandle.write(row)

    def arrayToTabSeparatedString(self, array):
            return '\t'.join([str(x) for x in array])


    def unpackNavs(self, fileHandle):
        reader = csv.reader(fileHandle, delimiter='\t')
        headerRowArray = reader.next() #skips header row
        self.headerRow = self.arrayToTabSeparatedString(headerRowArray) + "\t" + \
                         "Dest Variant?" + "\t" + "Bet variant?" + "\t" + \
                         "Right variant?" + "\t" + "Right file?" + "\t" +\
                         "Right method?" + "\t" + "Rank %" + "\t" + " Accuracy Level"+  "\n"

        navs = []
        for row in reader:
            nav = self.unpack(row)
            navs.append(nav)
        return navs

    def unpack(self, row):
        fullyQualifiedLocation = row[6]

        parts = self.getTargetPathParts(fullyQualifiedLocation)

        nav = {
            "variant_name": parts[0],
            "file_name": parts[1],
            "method_name": parts[2],
            "target": fullyQualifiedLocation,
            "is_destination_variant": parts[0] == self.DESTINATION_VARIANT_NAME,
            "prediction_row_array": row
        }

        return nav

    def getTargetPathParts(self, target):

        METHOD_REGEX = re.compile('(.*?)/([a-z|A-Z]+)')

        isNavToUnknownTarget = target.__contains__(" at ")
        if isNavToUnknownTarget:
            regex = NavigationClassifier.UNKNOWN_TARGET_REGEX
        else:
            regex = NavigationClassifier.METHOD_TARGET_REGEX

        match = regex.match(target)
        groups = match.groups()

        variantName = groups[0]

        fullyQualifiedFileName = groups[1]
        if fullyQualifiedFileName.__contains__("/"): #Can be "js_v9/Hex.js" -- get just file name
            fileName = METHOD_REGEX.match(fullyQualifiedFileName).groups()[1]
        else:
            fileName = fullyQualifiedFileName

        if isNavToUnknownTarget:
            methodName = ''
        else:
            methodName = groups[3]

        return (variantName, fileName, methodName)

    def updateBetweenVariantNav(self, nav, prevNav):
        if prevNav == None:
            nav["is_between_variant"] = ''
        else:
            nav["is_between_variant"] = (prevNav["variant_name"] <> nav["variant_name"])
