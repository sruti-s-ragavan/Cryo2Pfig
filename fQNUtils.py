JS_STD_PREFIX = "JS_Std_lib/"
JS_STD_REFERRER_STRING = 'JavaScript_standard;.'

class FQNUtils:
    @staticmethod
    def addFQNPrefixForEvent(event):
        event['target'] = FQNUtils.getFQN(event['target'])
        event['referrer'] = FQNUtils.getFQN(event['referrer'])

    @staticmethod
    def getFQN(string):
        def isFQN(obj):
            string = str(obj)
            #FQ method names (standard or not) have a ;.
            if ';.' in string:
                return True
            #FQ file names
            if string.startswith("/hexcom") and string.endswith(";"):
                return True
            return False

        if isFQN(string):
            return 'L' + str(string)
        else:
            return string

    @staticmethod
    def getFullClassPath(filepath):
        #TODO: this currently does not handle non-JS files
        return filepath + ";"

    @staticmethod
    def getFullMethodPath(filepath, header):
        return FQNUtils.getFullClassPath(filepath) + "." + header

    @staticmethod
    def correctJSStandardInvocationTargets(event, parentEventReferrer):
        if event['action'].startswith("Method invocation"):
            #Referrer has standard for method invocation
            #ParentEventReferrer has standard for Method invocation offset, length and scent methods.
            if JS_STD_REFERRER_STRING in str(event['referrer'])\
                    or (parentEventReferrer <> None and JS_STD_REFERRER_STRING in parentEventReferrer):
                event['target'] = JS_STD_PREFIX + event['target']
