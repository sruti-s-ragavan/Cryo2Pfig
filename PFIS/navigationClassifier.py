import re
import csv

class NavigationClassifier:
    DESTINATION_VARIANT_NAME = "Current"
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

    def writeBackToCsv(self, fileHandle):
        fileHandle.write(self.headerRow)

        for nav in self.navs:
            row = nav["prediction_row"] + "\t" \
                             + str(nav["is_destination_variant"]) + "\t" \
                             + str(nav["is_between_variant"]) + "\n"
            fileHandle.write(row)

    def unpackNavs(self, fileHandle):

        def arrayToTabSeparatedString(array):
            return '\t'.join([str(x) for x in array])

        reader = csv.reader(fileHandle, delimiter='\t')
        headerRowArray = reader.next() #skips header row
        self.headerRow = arrayToTabSeparatedString(headerRowArray) + "\t" + \
                         "Dest Variant?" + "\t" + "Bet variant?" + "\n"

        navs = []
        for row in reader:
            navToLocation = row[6]
            variantName = self.getVariantName(navToLocation)
            isDestinationVariant = variantName == self.DESTINATION_VARIANT_NAME

            nav={
                "prediction_row" : arrayToTabSeparatedString(row),
                "target" : navToLocation,
                "variant_name" : variantName,
                "is_destination_variant": isDestinationVariant
            }
            navs.append(nav)
        return navs

    def getVariantName(self, target):
        VARIANT_NAME_REGEX = re.compile(r'/hexcom/(.*?)/.*')
        variantName = VARIANT_NAME_REGEX.match(target).groups()[0]
        return variantName

    def updateBetweenVariantNav(self, nav, prevNav):
        if prevNav == None:
            nav["is_between_variant"] = ''
        else:
            nav["is_between_variant"] = (prevNav["variant_name"] == nav["variant_name"])







