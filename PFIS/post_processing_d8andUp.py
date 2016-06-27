import os
import sys
import subprocess


def generate_predictions(inputDbFile, outputFolder):
    projectRootDirectory = os.path.dirname(os.getcwd())
    sourceDirectory = os.path.join(projectRootDirectory, "jsparser/src")

    print "Calling PFIS.. "
    subprocess.call(["python","pfis3/src/python/pfis3.py",
                         "-l", "JS",
                         "-s", "je.txt",
                         "-d", inputDbFile,
                         "-p", sourceDirectory,
                         "-o", outputFolder,
                        "-x", "algorithm-config.xml",
                        "-n", os.path.join(outputFolder,"top-predictions")
                     ])

def main():
    sourceFile = sys.argv[1]
    outputFolder = "results"

    print "Generating Predictions ; Running PFIS"
    generate_predictions(sourceFile, outputFolder)


if __name__ == "__main__":
    main()