import json
import os
import os.path
import random
import sys
import codecs

TIMELINE_CUTOFF = 10

def getPositionMatrix():

    totalMatchCount = len([name for name in os.listdir('data/')])
    matchesProcessed = 0
    positionMatrix = []

    for matchFile in os.listdir('data/'):

        #Find all match files
        if matchFile.startswith('match_'):
            with codecs.open('data/' + matchFile, encoding='utf-8') as openFile:
                matchesProcessed = matchesProcessed + 1
                print('Getting jungler positions from match: ' + matchFile + '(' + str(matchesProcessed) + '/' + str(totalMatchCount) + ')')
                matchData = json.load(openFile)
                
                #If the match has no timeline data skip it
                if not matchData.has_key('timeline'):
                    print('Match has no timeline, skipping...')
                    continue

                #Find the junglers in the game
                participantArray = matchData['participants']
                for participant in participantArray:
                    if participant['timeline']['lane'] == "JUNGLE":
                        frameArray = matchData['timeline']['frames']

                        #Only include matches that last at least through the early game
                        if len(frameArray) < TIMELINE_CUTOFF:
                            print('Jungler has too few frames, skipping...')
                            continue

                        #Populate the jungler position array
                        junglerPositions = []
                        for frame in frameArray:

                            #Only do iterations over the early game
                            if len(junglerPositions) >= TIMELINE_CUTOFF:
                                break

                            junglerFrame = frame['participantFrames'][str(participant['participantId'])]

                            #Check if the jungler was alive, if not, make their position (-1,-1)
                            if junglerFrame.has_key('position'):
                                junglerPositions.append(junglerFrame['position'])
                            else:
                                junglerPositions.append({"x": -1, "y": -1})
                        positionMatrix.append(junglerPositions)
        else:
            continue
    return positionMatrix

def initializeWeights(dataCount, clusterCount):
    weightMatrix = []
    for i in range(0, dataCount):
        weightArray = []
        for j in range(0, clusterCount):
            weightArray.append(random.uniform(0, 1))
        weightMatrix.append(weightArray)
    return weightMatrix

def initializeCentroids(clusterCount):
    centroidMatrix = []
    for i in range(0, clusterCount):
        centroidArray = []
        for j in range(0, TIMELINE_CUTOFF):
            centroidArray.append(0)


def updateWeights(positionMatrix, centroidMatrix):
    
    print('nah fam')

def updateCentroids(positionMatrix, weightMatrix):
    print('nah fam')

def makeClusters(clusterCount):
    positionMatrix = getPositionMatrix()

    weightMatrix = initializeWeights(len(positionMatrix), clusterCount)

    centroidMatrix = initializeCentroids(clusterCount)


if __name__ == "__main__":
    makeClusters(sys.argv[1])
