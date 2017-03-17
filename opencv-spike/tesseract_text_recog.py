from PIL import Image
import sys
import pytesseract

filename = sys.argv[1]
print "----: ", sys.argv[1]
print(pytesseract.image_to_string(Image.open(filename)))
#print image_to_string(Image.open('test-english.jpg'), lang='eng')
