import json
import os
import os.path
import random
import sys
import math
import codecs

TIMELINE_CUTOFF = 10
FUZZY_INDEX = 2
EPSILON = 1
TEAM = 100
DATA_CUTOFF = 10000

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
                    if participant['timeline']['lane'] == "JUNGLE" and participant['teamId'] == TEAM:
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
                        junglerPositions.append(participant['stats']['winner'])
                        positionMatrix.append(junglerPositions)
                        if len(positionMatrix) >= DATA_CUTOFF:
                            return positionMatrix
        else:
            continue
    return positionMatrix

def distance(l1, l2):
    sqrdDist = 0
    for item1 in l1:
        for item2 in l2:
            sqrdDist += math.pow(pointDistance(item1, item2), 2)

    return math.sqrt(sqrdDist)

def pointDistance(p1, p2):
    sqrdDist = math.pow(p1['x'] - p2['x'], 2) + math.pow(p1['y'] - p2['y'], 2)
    return math.sqrt(sqrdDist)
            

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
            centroidArray.append({'x':0.0, 'y':0.0})
        centroidMatrix.append(centroidArray)
    return centroidMatrix

def updateWeights(positionMatrix, centroidMatrix, clusterCount):
    weightMatrix = []
    for i in range(0, len(positionMatrix)):
        print('Updating weights (' + str(i) + '/' + str(len(positionMatrix)) + ')')
        weightArray = []
        posData = positionMatrix[i]
        for j in range(0, clusterCount):
            invWeight = 0
            distFromCurrent = distance(posData, centroidMatrix[j])
            for k in range(0, clusterCount):
                invWeight += math.pow(distFromCurrent / distance(posData, centroidMatrix[k]), 2/(FUZZY_INDEX - 1))
            weightArray.append(1/invWeight)
        weightMatrix.append(weightArray)
    return weightMatrix

def updateCentroids(positionMatrix, weightMatrix, clusterCount):
    centroidMatrix = []
    for j in range(0, clusterCount):
        print('Updating cluster (' + str(j) + '/' + str(clusterCount) + ')')
        centroidArray = []
        for k in range(0, TIMELINE_CUTOFF):
            centroidNum = {'x':0.0, 'y':0.0}
            centroidDenom = 0.0
            for i in range(0, len(positionMatrix)):
                centroidWeight = pow(weightMatrix[i][j], FUZZY_INDEX)
                centroidNum['x'] += centroidWeight * positionMatrix[i][k]['x']
                centroidNum['y'] += centroidWeight * positionMatrix[i][k]['y']
                centroidDenom += centroidWeight

            centroidArray.append({'x':centroidNum['x'] / centroidDenom, 'y':centroidNum['y'] / centroidDenom })
        centroidMatrix.append(centroidArray)
    return centroidMatrix

def objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount):
    objective = 0
    for i in range(0, len(positionMatrix)):
        for j in range(0, clusterCount):
            objective += pow(weightMatrix[i][j], FUZZY_INDEX) * pow(distance(positionMatrix[i], centroidMatrix[j]), 2)
    print('Objective is currently:' + str(objective))
    return objective

def makeClusters(clusterCount):
    positionMatrix = getPositionMatrix()

    weightMatrix = initializeWeights(len(positionMatrix), clusterCount)

    centroidMatrix = initializeCentroids(clusterCount)

    newEval = -2.0 * EPSILON
    oldEval = 0.0
    while(math.fabs(newEval - oldEval) > EPSILON):
        oldEval = newEval
        centroidMatrix = updateCentroids(positionMatrix, weightMatrix, clusterCount)
        weightMatrix = updateWeights(positionMatrix, centroidMatrix, clusterCount)
        newEval = objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount)

    with open('clusters_' + str(len(positionMatrix)) + '_' + str(clusterCount), 'wb') as outfile:
        json.dump(centroidMatrix, outfile)

    with open('weights_' + str(len(positionMatrix)) + '_' + str(clusterCount), 'wb') as outfile:
        json.dump(weightMatrix, outfile)

    with open('positions_' + str(len(positionMatrix)) + '_' + str(clusterCount), 'wb') as outfile:
        json.dump(positionMatrix, outfile)
    

if __name__ == "__main__":
    makeClusters(int(sys.argv[1]))
