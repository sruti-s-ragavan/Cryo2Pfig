import re
import csv

class NavigationClassifier:
    DESTINATION_VARIANT_NAME = "Current"

    #/hexcom/2014-05-26-10:18:35/js/view.js;.renderText(x"," y"," fontSize"," color"," text)
    METHOD_TARGET_REGEX = re.compile(r'/hexcom/(.*?)/(.*?).js;.(.*?)\((.*?)')

    #/hexcom/Current/js_v9/view,UNKNOWN,0
    UNKNOWN_TARGET_REGEX =  re.compile(r'/hexcom/(.*?)/(.*?),(UNKNOWN),(.*?)')

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

    def updatePredictionAccuracyParams(self, row, nav):

        nav["accurate_variant"] = False
        nav["accurate_file"] = False
        nav["accurate_method"] = False

        if(row[9] == "1"):
            #'[u\\'/hexcom/2014-05-26-09:30:45/js/view.js;.showModal(text"," secondaryText)\\']'
            REGEX = re.compile(r"\[u'(.*?)'\]")
            match = REGEX.match(row[10])
            prediction = match.groups()[0]
            prediction_parts = self.getTargetPathParts(prediction)
            nav["accurate_variant"] = (prediction_parts[0].lower() == nav["variant_name"].lower())
            nav["accurate_file"] = (prediction_parts[1].lower() == nav["file_name"].lower())
            nav["accurate_method"] = (prediction_parts[2].lower() == nav["method_name"].lower())

    def writeBackToCsv(self, fileHandle):
        fileHandle.write(self.headerRow)

        for nav in self.navs:
            row = nav["prediction_row"] + "\t" \
                             + str(nav["is_destination_variant"]) + "\t" \
                             + str(nav["is_between_variant"]) + "\t" \
                            + str(nav["accurate_variant"]) + "\t" \
                            + str(nav["accurate_file"]) + "\t" \
                            + str(nav["accurate_method"]) + "\n"
            fileHandle.write(row)

    def arrayToTabSeparatedString(self, array):
            return '\t'.join([str(x) for x in array])


    def unpackNavs(self, fileHandle):
        reader = csv.reader(fileHandle, delimiter='\t')
        headerRowArray = reader.next() #skips header row
        self.headerRow = self.arrayToTabSeparatedString(headerRowArray) + "\t" + \
                         "Dest Variant?" + "\t" + "Bet variant?" + "\t" + \
                         "Right variant?" + "\t" + "Right file?" + "\t" + "Right method?" + "\n"

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
            "prediction_row" : self.arrayToTabSeparatedString(row)
        }

        self.updatePredictionAccuracyParams(row, nav)
        return nav

    def getTargetPathParts(self, target):

        METHOD_REGEX = re.compile('(.*?)/([a-z|A-Z]+)')
        if target.__contains__("UNKNOWN"):
            regex = NavigationClassifier.UNKNOWN_TARGET_REGEX
        else:
            regex = NavigationClassifier.METHOD_TARGET_REGEX

        match = regex.match(target)
        groups = match.groups()
        variantName = groups[0]
        fullyQualifiedFileName = groups[1]
        methodName = groups[2]

        if fullyQualifiedFileName.__contains__("/"):
            fileName = METHOD_REGEX.match(fullyQualifiedFileName).groups()[1]
        else:
            fileName = fullyQualifiedFileName

        return (variantName, fileName, methodName)

    def updateBetweenVariantNav(self, nav, prevNav):
        if prevNav == None:
            nav["is_between_variant"] = ''
        else:
            nav["is_between_variant"] = (prevNav["variant_name"] <> nav["variant_name"])
