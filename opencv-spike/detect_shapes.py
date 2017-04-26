# import the necessary packages
from shapedetector import ShapeDetector
import argparse
import imutils
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to the input image")
args = vars(ap.parse_args())

image = cv2.imread(args["image"])
# resized = imutils.resize(image, width=300)
# ratio = image.shape[0] / float(resized.shape[0])

# convert the resized image to grayscale, blur it slightly,
# and threshold it
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# filtered = cv2.bilateralFilter(gray, 11, 17, 17)
edged = cv2.Canny(gray, 70, 350)
# blurred = cv2.GaussianBlur(edged, (5, 5), 0)
_,thresh = cv2.threshold(edged, 127, 255, cv2.THRESH_BINARY)

cv2.imshow("Image", thresh)
cv2.waitKey(0)
cv2.destroyAllWindows()

# find contours in the thresholded image and initialize the
# shape detector
# cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
	# cv2.CHAIN_APPROX_SIMPLE)
cnts = cv2.findContours(thresh.copy(), cv2.RETR_TREE,
	cv2.CHAIN_APPROX_NONE)

cnts = cnts[0] if imutils.is_cv2() else cnts[1]
sd = ShapeDetector()

# loop over the contours
for c in cnts:
	# compute the center of the contour, then detect the name of the
	# shape using only the contour
	M = cv2.moments(c)
	cX = int((M["m10"] / M["m00"]))
	cY = int((M["m01"] / M["m00"]))
	shape = sd.detect(c)
	if shape=="hexagon":

		# multiply the contour (x, y)-coordinates by the resize ratio,
		# then draw the contours and the name of the shape on the image
		c = c.astype("float")
		# c *= ratio
		c = c.astype("int")
		cv2.drawContours(image, [c], -1, (0, 0, 0), 2)

		cv2.putText(image, shape, (cX, cY+200), cv2.FONT_HERSHEY_SIMPLEX,
			0.5, (255, 0, 0), 2)

		# show the output image
		cv2.imshow("Image", image)
		cv2.waitKey(0)
