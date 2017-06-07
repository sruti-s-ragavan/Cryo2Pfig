import os.path

from PIL import Image, ImageEnhance, ImageFilter
import sys
import cv2
import shutil

import time
import requests
import urllib

import sqlite3


DB_FILE_NAME = "../variants-output.db"
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

	convertedImages = [f for f in os.listdir(correctedImagesFolder) if f.endswith(".png")]

	resultsMap = {}
	for op in convertedImages:
		output = None

		opFilePath = os.path.join(correctedImagesFolder, op)
		response = getImageFeaturesFromMicrosoftVisionAPI(opFilePath)
		output = response['regions']

		if len(output) == 0:
			opFilePath = os.path.join(imagesFolder, op)
			time.sleep(3)
			response = getImageFeaturesFromMicrosoftVisionAPI(opFilePath)
			output = response['regions']

		variantName = op[:-4].replace("/", ":")
		resultsMap[variantName] = response
		time.sleep(3)

	for variant in resultsMap.keys():
		print variant, resultsMap[variant]

def setupDB():
	conn = sqlite3.connect(DB_FILE_NAME)
	if conn is not None:
		c = conn.cursor()
		c.execute("DROP TABLE IF EXISTS variant_output_features")
		c.execute("CREATE TABLE variant_output_features (variant text, output text)")
		conn.commit()

		c.close()
		conn.close()


if __name__ == "__main__":
	# python get_output_features.py /path/to/output/screenshots/folder
	main()
