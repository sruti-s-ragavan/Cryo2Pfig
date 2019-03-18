import cv2
import sys
import imutils

def captch_ex(file_name ):
    
    image = cv2.imread(file_name)
    resized = imutils.resize(image, width=300)
    ratio = image.shape[0] / float(resized.shape[0])

    # convert the resized image to grayscale, blur it slightly,
    # and threshold it
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    #gray = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]

    contours = cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) 
    # get contours
    index = 0 

    print len(contours)

    for contour in contours:
        print '\n=============\n'
        print str(contour)
        # get rectangle bounding contour
        [x,y,w,h] = cv2.boundingRect(contour)

        #Don't plot small false positives that aren't text
        if w < 35 and h<35:
            continue

        # draw rectangle around contour on original image
        cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,255),2)

        '''
        #you can crop image and send to OCR  , false detected will return no text :)
        cropped = img_final[y :y +  h , x : x + w]

        s = file_name + '/crop_' + str(index) + '.jpg' 
        cv2.imwrite(s , cropped)
        index = index + 1

        '''
    # write original image with added contours to disk  
    cv2.imshow('captcha_result' , image)
    cv2.waitKey()


file_name=str(sys.argv[1])
captch_ex(file_name)
