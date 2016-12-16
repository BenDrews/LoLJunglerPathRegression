import json
import os
import os.path
import random
import sys
import math
import codecs

TIMELINE_CUTOFF = 5
FUZZY_INDEX = 1.5
EPSILON = 1
TEAM = 100
DATA_CUTOFF = 1000
FOUNTAIN_POSITION = {'x':0, 'y':0}
CHAMPION = 64

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
                    if participant['timeline']['lane'] == "JUNGLE" and participant['teamId'] == TEAM and participant['championId'] == CHAMPION:
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
                                junglerPositions.append(FOUNTAIN_POSITION)
                        junglerPositions.append(participant['stats']['winner'])
                        positionMatrix.append(junglerPositions)
                        if len(positionMatrix) >= DATA_CUTOFF:
                            return positionMatrix
        else:
            continue
    return positionMatrix

def distance(l1, l2):
    sqrdDist = 0
    for i in range(0, len(l1) - 1):
        sqrdDist += math.pow(pointDistance(l1[i], l2[i]), 2)

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

def initializeCentroids(positionMatrix, clusterCount):
    centroidMatrix = []
    for i in range(0, clusterCount):
        centroidMatrix.append(positionMatrix[random.randint(0, len(positionMatrix) - 1)])
    return centroidMatrix

def updateWeights(positionMatrix, centroidMatrix, clusterCount):
    weightMatrix = []
    for i in range(0, len(positionMatrix) - 1):
        print('Updating weights (' + str(i) + '/' + str(len(positionMatrix) - 1) + ')')
        weightArray = []
        posData = positionMatrix[i]
        for j in range(0, clusterCount):
            invWeight = 0
            distFromCurrent = distance(posData, centroidMatrix[j])
            for k in range(0, clusterCount):
                if(distance(posData, centroidMatrix[k]) < EPSILON):
                    invWeight += math.pow(distFromCurrent / EPSILON, 2/(FUZZY_INDEX - 1))
                else:
                    invWeight += math.pow(distFromCurrent / distance(posData, centroidMatrix[k]), 2/(FUZZY_INDEX - 1))
            if(invWeight < EPSILON):
                invWeight = EPSILON
            weightArray.append(1.0/invWeight)
        weightMatrix.append(weightArray)
    return weightMatrix

def updateCentroids(positionMatrix, weightMatrix, clusterCount):
    centroidMatrix = []
    for j in range(0, clusterCount):
        print('Updating cluster (' + str(j) + '/' + str(clusterCount) + ')')
        centroidArray = []
        centroidNum = [{'x':0.0, 'y':0.0} for x in range(0, TIMELINE_CUTOFF)]
        centroidDenom = 0.0
        winRateNum = 0.0

        for i in range(0, len(positionMatrix) - 1):
            centroidWeight = pow(weightMatrix[i][j], FUZZY_INDEX)
            centroidDenom += centroidWeight
            winRateNum += positionMatrix[i][TIMELINE_CUTOFF] * centroidWeight

            for k in range(0, TIMELINE_CUTOFF):
                centroidNum[k]['x'] += centroidWeight * positionMatrix[i][k]['x']
                centroidNum[k]['y'] += centroidWeight * positionMatrix[i][k]['y']
        
        for k in range(0, TIMELINE_CUTOFF):
            centroidArray.append({'x':centroidNum[k]['x'] / centroidDenom, 'y':centroidNum[k]['y'] / centroidDenom })

        centroidArray.append(winRateNum / centroidDenom)
        centroidMatrix.append(centroidArray)

    return centroidMatrix

def cullClusters(weightMatrix, centroidMatrix, clusterCount):
    j = 0
    while j < clusterCount:
        k = j + 1
        while k < clusterCount:
            if distance(centroidMatrix[j], centroidMatrix[k]) < EPSILON:
                print 'CULLING CLUSTER'
                clusterCount -= 1
                centroidMatrix.pop(k)
                for i in range(0, len(weightMatrix)):
                    weightMatrix[i].pop(k)
                k -= 1
            k += 1
        j += 1
    return clusterCount

def objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount):
    objective = 0
    for i in range(0, len(positionMatrix) - 1):
        for j in range(0, clusterCount):
            objective += pow(weightMatrix[i][j], FUZZY_INDEX) * pow(distance(positionMatrix[i], centroidMatrix[j]), 2)
    print('Objective is currently:' + str(objective))
    return objective

def makeClusters(clusterCount):
    positionMatrix = getPositionMatrix()

    centroidMatrix = initializeCentroids(positionMatrix, clusterCount)
                                 
    newEval = -2.0 * EPSILON
    oldEval = 0.0
    while(math.fabs(newEval - oldEval) > EPSILON):
        oldEval = newEval

        weightMatrix = updateWeights(positionMatrix, centroidMatrix, clusterCount)
        centroidMatrix = updateCentroids(positionMatrix, weightMatrix, clusterCount)

        clusterCount = cullClusters(weightMatrix, centroidMatrix, clusterCount)

        newEval = objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount)

    with open('output/cluster', 'wb') as outfile:
        json.dump(centroidMatrix, outfile, indent = 4, separators=(',', ':'))

    with open('output/weights', 'wb') as outfile:
        json.dump(weightMatrix, outfile, indent = 4, separators=(',', ':'))

    with open('output/positions', 'wb') as outfile:
        json.dump(positionMatrix, outfile, indent = 4, separators=(',', ':'))
    

if __name__ == "__main__":
    makeClusters(int(sys.argv[1]))
