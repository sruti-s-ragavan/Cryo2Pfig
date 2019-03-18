import time
import requests
import operator
import numpy as np
import urllib

# Display images within Jupyter


# Variables
_url = 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/recognizeText'
    # 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/textOperations' #analyze

_key = 'b159b988956a4ff19006b468698d1ac0' #Here you have to paste your primary key
_maxNumRetries = 10


params = {'handwriting':'false'}
#{ 'visualFeatures' : 'Color,Categories,Description,ImageType,Tags'}
headers = {
    'Ocp-Apim-Subscription-Key':_key,
    'Content-Type': 'application/octet-stream'
}


def processRequest( json, data, headers, params ):

    """
    Helper function to process the request to Project Oxford

    Parameters:
    json: Used when processing images from its URL. See API Documentation
    data: Used when processing image read from disk. See API Documentation
    headers: Used to pass the key information and the data type request
    """

    retries = 0
    result = None

    while True:

        response = requests.request( 'post', _url, json = json, data = data, headers = headers, params = params )
        if response.status_code == 429:

            print( "Message: %s" % ( response.json()['error']['message'] ) )

            if retries <= _maxNumRetries:
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

def urlAnalysis():
    urlImage = 'https://upload.wikimedia.org/wikipedia/commons/2/2a/AMS_Euler_sample_text.svg'

    # Computer Vision parameters

    json = None #{ 'url': urlImage }
    data = None

    f = urllib.urlopen(urlImage)
    data = f.read()

    result = processRequest( json, data, headers, params )

    if result is not None:
        return result

def diskAnalysis():
    # Load raw image file into memory
    pathToFileInDisk = r'SoutisVariant.png'
    with open( pathToFileInDisk, 'rb' ) as f:
        data = f.read()

    json = None

    result = processRequest( json, data, headers, params )

    if result is not None:
        return result


result = diskAnalysis()
print result
