import os.path

from PIL import Image, ImageEnhance, ImageFilter
import sys
import cv2
import shutil

import time
import requests
import urllib

import sqlite3
import imutils
from shapedetector import *


DB_FILE_NAME = "variants-output.db"
_url = 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/ocr'
_key = 'b159b988956a4ff19006b468698d1ac0' #Here you have to paste your primary key


def convertToGrayscaleAndCorrect(outputImageFilePath, correctedImagePath):
	img = Image.open(outputImageFilePath)
	img = img.filter(ImageFilter.SHARPEN)
	enhancer = ImageEnhance.Contrast(img)
	img = enhancer.enhance(10)
	img = img.convert('1')
	img.save('temp.jpg')

	im = cv2.imread('temp.jpg',cv2.COLOR_RGB2GRAY)
	im = cv2.blur(im,(4,4))
	_, im = cv2.threshold(im, 200 , 200, cv2.THRESH_BINARY_INV)
	cv2.imwrite(correctedImagePath, im)

	print str.format("Corrected: {}; written to: {}", outputImageFilePath, correctedImagePath)


def getImageFeaturesFromMicrosoftVisionAPI(imgPath):
	headers = {
		'Ocp-Apim-Subscription-Key':_key,
		'Content-Type': 'application/octet-stream'
	}

	params = urllib.urlencode({
		# Request parameters
		# 'language': 'en',
		# 'detectOrientation ': 'fa',
	})

	with open( imgPath, 'rb' ) as f:
		data = f.read()

	json = None
	print "Sending request for: ", imgPath

	result = processRequest(_url, json, data, headers, params)

	if result is not None:
		return result

def processRequest(url, json, data, headers, params ):
	MAX_NUM_RETRIES = 10
	retries = 0
	result = None

	while True:
		response = requests.request( 'post', url, json = json, data = data, headers = headers, params = params )
		if response.status_code == 429:
			print response.json()
			print( "Message: %s" % ( response.json()['error']['message'] ) )

			if retries <= MAX_NUM_RETRIES:
				time.sleep(1)
				retries += 1
				continue
			else:
				print( 'Error: failed after retrying!' )
				break

		elif response.status_code == 200 or response.status_code == 201:

			if 'content-length' in response.headers and int(response.headers['content-length']) == 0:
				result = None
			elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str):
				if 'application/json' in response.headers['content-type'].lower():
					result = response.json() if response.content else None
				elif 'image' in response.headers['content-type'].lower():
					result = response.content
		else:
			print( "Error code: %d" % ( response.status_code ) )
			print( "Message: %s" % ( response.json()['error']['message'] ) )

		break

	return result

def getLargestHexagonBoundingRect(filepath):
	image = cv2.imread(filepath)

	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	edged = cv2.Canny(gray, 70, 350)
	_,thresh = cv2.threshold(edged, 127, 255, cv2.THRESH_BINARY)

	cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
	cnts = cnts[0] if imutils.is_cv2() else cnts[1]

	sd = ShapeDetector()

	maxArea = -1
	largestHexagonBounds = None

	for c in cnts:
		shape = sd.detect(c)
		if shape=="hexagon":
			c = c.astype("float")
			c = c.astype("int")
			rect = cv2.boundingRect(c) #returns rectangle definition as x,y,w,h
			area = rect[2] * rect[3]
			if area > maxArea:
				largestHexagonBounds = rect
				maxArea = area

	return largestHexagonBounds


def main():
	imagesFolder = sys.argv[1]

	correctedImagesFolder = os.path.join(imagesFolder, "corrected")
	if os.path.exists(correctedImagesFolder):
		shutil.rmtree(correctedImagesFolder)

	os.mkdir(correctedImagesFolder)

	setupDB()

	outputs = [f for f in os.listdir(imagesFolder) if f.endswith(".png")]
	for op in outputs:
		variantName = op
		opFilePath = os.path.join(imagesFolder, variantName)
		correctedImagePath = os.path.join(correctedImagesFolder, variantName)
		convertToGrayscaleAndCorrect(opFilePath, correctedImagePath)


	resultsMap = {}
	for op in outputs:
		regions = getImageFeaturesFromMicrosoftVisionAPI(os.path.join(imagesFolder, op))['regions']
		output_original = getRegions(regions)
		time.sleep(3)

		regions = getImageFeaturesFromMicrosoftVisionAPI(os.path.join(correctedImagesFolder, op))['regions']
		output_corrected = getRegions(regions)
		time.sleep(3)

		textRegions = None
		if len(output_corrected) > len(output_original):
			textRegions = output_corrected
		else:
			textRegions = output_original

		variantName = op[:-4].replace("/", ":")
		largestRectBounds = getLargestHexagonBoundingRect(os.path.join(imagesFolder, op))
		resultsMap[variantName] = (textRegions, largestRectBounds)
		# showFeatureBoundaries(os.path.join(imagesFolder, op), textRegions, largestRectBounds)

	writeToDB(resultsMap)

def showFeatureBoundaries(file, textRegions, hexagon):
	image = cv2.imread(file)

	for c in textRegions.values():
		cv2.rectangle(image, (c[0], c[1]), (c[0]+c[2], c[1]+c[3]),(0,255,0),2)

	if hexagon is not None:
		c = hexagon
		cv2.rectangle(image, (c[0], c[1]), (c[0]+c[2], c[1]+c[3]),(0,255,0),2)

	cv2.imshow("Image", image)
	cv2.waitKey(0)

def getRegions(regions):
	regionMap = {}
	for region in regions:
		lines = region ['lines']
		for line in lines:
			words = line['words']
			for word in words:
				wordText = word['text']
				position = word['boundingBox']
				position = position.split(",")
				bounds = [int(x) for x in position]
				regionMap[wordText] = bounds
	return regionMap

def writeToDB(resultsMap):
	conn = sqlite3.connect(DB_FILE_NAME)
	c = conn.cursor()
	if conn is not None:
		for variantName in resultsMap.keys():
			values = resultsMap[variantName]
			c.execute("INSERT INTO variant_output_features(variant, output, largest_hexagon) VALUES (?, ?, ?)",
			          [variantName, str(values[0]), str(values[1])])
	conn.commit()
	c.close()
	conn.close()


def setupDB():
	conn = sqlite3.connect(DB_FILE_NAME)
	if conn is not None:
		c = conn.cursor()
		c.execute("DROP TABLE IF EXISTS variant_output_features")
		c.execute("CREATE TABLE variant_output_features (variant text, output text, largest_hexagon text)")
		conn.commit()

		c.close()
		conn.close()


if __name__ == "__main__":
	# python get_output_features.py /path/to/output/screenshots/folder
	main()
