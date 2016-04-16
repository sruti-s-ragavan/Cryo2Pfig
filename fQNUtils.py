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
    def getFullMethodPath(filepath, nested_path_within_file, header):
        fullClassPath = FQNUtils.getFullClassPath(filepath)
        if header == '': #This happens when a call site is not another method body -- JS specific!
            return fullClassPath

        else:
            return fullClassPath[:-1] + nested_path_within_file + ";." + header

    @staticmethod
    def correctJSStandardInvocationTargets(event, parentEventReferrer):
        if event['action'].startswith("Method invocation"):
            #Referrer has standard for method invocation
            #ParentEventReferrer has standard for Method invocation offset, length and scent methods.
            if JS_STD_REFERRER_STRING in str(event['referrer'])\
                    or (parentEventReferrer <> None and JS_STD_REFERRER_STRING in parentEventReferrer):
                event['target'] = JS_STD_PREFIX + event['target']
