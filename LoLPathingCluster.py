import json
import os
import os.path
import random
import sys
import math
import codecs

#Champion id constants
LEE_SIN = 64
VI = 254
SHYVANA = 102
HECARIM = 120
KHA_ZIX = 121

#Contant parameters
CLUSTER_COUNT = 20
TIMELINE_CUTOFF = 6
FUZZY_INDEX = 1.5
EPSILON = 1
TEAM = 100
DATA_CUTOFF = 200
FOUNTAIN_POSITION = {'x':0, 'y':0}
VALIDATION_COUNT = 5
CHAMPION = LEE_SIN

#Parse the targeted data from the match repository
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

#Calculate the distance between two jungle paths
def distance(l1, l2):
    sqrdDist = 0

    #Ignore the last element since it is a label
    for i in range(0, len(l1) - 1):
        sqrdDist += math.pow(pointDistance(l1[i], l2[i]), 2)

    return math.sqrt(sqrdDist)

#Euclidean distance between two points
def pointDistance(p1, p2):
    sqrdDist = math.pow(p1['x'] - p2['x'], 2) + math.pow(p1['y'] - p2['y'], 2)
    return math.sqrt(sqrdDist)
            
#Pick random data points to be the initial centroids
def initializeCentroids(positionMatrix):
    centroidMatrix = []
    for i in range(0, CLUSTER_COUNT):
        centroidMatrix.append(positionMatrix[random.randint(0, len(positionMatrix) - 1)])
    return centroidMatrix

#Update how much each data point is a part of each cluster
def updateWeights(positionMatrix, centroidMatrix, clusterCount):
    weightMatrix = []
    for i in range(0, len(positionMatrix)):
        print('Updating weights (' + str(i + 1) + '/' + str(len(positionMatrix)) + ')')
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

            #Prevent division by zero. Does introduce error.
            if(invWeight < EPSILON):
                invWeight = EPSILON

            weightArray.append(1.0/invWeight)
        weightMatrix.append(weightArray)
    return weightMatrix

#Update the centroid for each cluster
def updateCentroids(positionMatrix, weightMatrix, clusterCount):
    centroidMatrix = []
    for j in range(0, clusterCount):
        print('Updating cluster (' + str(j + 1) + '/' + str(clusterCount) + ')')
        centroidArray = []
        centroidNum = [{'x':0.0, 'y':0.0} for x in range(0, TIMELINE_CUTOFF)]
        centroidDenom = 0.0
        winRateNum = 0.0

        #Calculate a list of weight numerators along with the normalizing denominator
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

#If any set of clusters converges, delete all but one
def cullClusters(weightMatrix, centroidMatrix, clusterCount):
    j = 0
    while j < clusterCount:
        k = j + 1
        while k < clusterCount:
            if distance(centroidMatrix[j], centroidMatrix[k]) < EPSILON:
                print 'Culling cluster: ' + str(k + 1)
                clusterCount -= 1
                centroidMatrix.pop(k)
                for i in range(0, len(weightMatrix)):
                    weightMatrix[i].pop(k)
                k -= 1
            k += 1
        j += 1
    return clusterCount

#Calculate the objective function for Fuzzy C-Means
def objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount):
    objective = 0
    for i in range(0, len(positionMatrix) - 1):
        for j in range(0, clusterCount):
            objective += pow(weightMatrix[i][j], FUZZY_INDEX) * pow(distance(positionMatrix[i], centroidMatrix[j]), 2)
    print('Objective is currently:' + str(objective))
    return objective

#Main clustering function
def makeClusters(positionMatrix, clusterCount):

    centroidMatrix = initializeCentroids(positionMatrix)
                                 
    #Initial values choosen so the loop doesn't terminate immediately
    newEval = -2.0 * EPSILON
    oldEval = 0.0

    #Loop until the objective function converges
    while(math.fabs(newEval - oldEval) > EPSILON):
        oldEval = newEval

        weightMatrix = updateWeights(positionMatrix, centroidMatrix, clusterCount)
        centroidMatrix = updateCentroids(positionMatrix, weightMatrix, clusterCount)

        clusterCount = cullClusters(weightMatrix, centroidMatrix, clusterCount)
        newEval = objectiveFunction(positionMatrix, weightMatrix, centroidMatrix, clusterCount)

    with open('output/cluster_' + str(DATA_CUTOFF) + '_' + str(CLUSTER_COUNT) + '_' + str(TIMELINE_CUTOFF) + '_' + str(VALIDATION_COUNT) + '_' + str(CHAMPION), 'wb') as outfile:
        json.dump(centroidMatrix, outfile, indent = 4, separators=(',', ':'))

    with open('output/weights_' + str(DATA_CUTOFF) + '_' + str(CLUSTER_COUNT) + '_' + str(TIMELINE_CUTOFF) + '_' + str(VALIDATION_COUNT) + '_' + str(CHAMPION), 'wb') as outfile:
        json.dump(weightMatrix, outfile, indent = 4, separators=(',', ':'))

    with open('output/positions_' + str(DATA_CUTOFF) + '_' + str(CLUSTER_COUNT) + '_' + str(TIMELINE_CUTOFF) + '_' + str(VALIDATION_COUNT) + '_' + str(CHAMPION), 'wb') as outfile:
        json.dump(positionMatrix, outfile, indent = 4, separators=(',', ':'))
    
    return centroidMatrix

#Find the performance for the given clusters on a set of test data
def validateData(clusters, testSet):
    
    correctPoints = 0.0

    for testPoint in testSet:
        weightArray = []

        #Find the Fuzzy C-Means weights for the given test point
        for cluster in clusters:
            invWeight = 0
            distFromCurrent = distance(testPoint, cluster)

            for otherCluster in clusters:
                if(distance(testPoint, otherCluster) < EPSILON):
                    invWeight += math.pow(distFromCurrent / EPSILON, 2/(FUZZY_INDEX - 1))
                else:
                    invWeight += math.pow(distFromCurrent / distance(testPoint, otherCluster), 2/(FUZZY_INDEX - 1))

            if(invWeight < EPSILON):
                invWeight = EPSILON

            weightArray.append(1.0/invWeight)

        predictedWinRate = 0

        #Find the weighted average winrate
        for i in range(0, len(weightArray)):
            predictedWinRate += cluster[len(clusters[i]) - 1] * weightArray[i]
        
        #Predict game outcome
        if (predictedWinRate > 0.5) == testPoint[len(testPoint) - 1]:
            correctPoints += 1.0

    return correctPoints / len(testSet)


if __name__ == "__main__":
    
    positionMatrix = getPositionMatrix()
    if not (len(positionMatrix) % VALIDATION_COUNT == 0):
        print 'Data cannot be neatly partitioned into ' + str(VALIDATION_COUNT) + ' sets'

    avgPerformanceNum = 0

    #K-fold cross validation
    for i in range(0, VALIDATION_COUNT):
        trainingSet = positionMatrix[0 : i * len(positionMatrix) / VALIDATION_COUNT]
        trainingSet += positionMatrix[(i + 1) * len(positionMatrix) / VALIDATION_COUNT : len(positionMatrix)]
        testSet = positionMatrix[i * len(positionMatrix) / VALIDATION_COUNT : (i + 1) * len(positionMatrix) / VALIDATION_COUNT]
        clusters = makeClusters(trainingSet, CLUSTER_COUNT)
        avgPerformanceNum += validateData(clusters, testSet)

    print('Performance: ' + str(avgPerformanceNum / VALIDATION_COUNT))
