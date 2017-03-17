from PIL import Image, ImageEnhance, ImageFilter
import sys
import pytesseract
import cv2


# load image
filename = sys.argv[1]

img = Image.open(filename)
img = img.filter(ImageFilter.SHARPEN)
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(10)
img = img.convert('1')
img.save('temp.jpg')

im = cv2.imread('temp.jpg',cv2.COLOR_RGB2GRAY)
# blur image
im = cv2.blur(im,(4,4))
# apply a threshold
im = cv2.threshold(im, 175 , 250, cv2.THRESH_BINARY)
im = im[1]
cv2.imwrite('temp2.jpg', im)

text = pytesseract.image_to_string(Image.open('temp2.jpg'))
print(text)