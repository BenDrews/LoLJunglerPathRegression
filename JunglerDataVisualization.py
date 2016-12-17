'''
JunglerDataVisualization.py

Uses cluster data (centroids+winrates) and datapoint-cluster-weights matrix to 
visualize effectiveness of jungler paths for various champions.

This script will generate:
	1. For each champion, a map with the paths representing the top 3 and bottom 3 win rate clusters
	2. For each chapmion, a map the paths representing the top 6 weighted clusters over all datapoints
	3. A map with a hand-curated selection of one relatively successful and popular  path/cluster for each champion
	4. A table (output to stdout) with every cluster's winrate and average weight.  Will be in order of chapmion
	   list, and by ascending winrate within each cluster.
	
(c) Gary Chen, Ben Drews, Justin Smilan 2016 - CSCI 373 AI, Prof. Jon Park
'''
from PIL import Image, ImageDraw
import json
import codecs
import numpy
import sys

# File suffixes and corresponding champion names
fileIDs = [
	"19_6_5",
	"20_6_5_254",
	"20_6_5_102",
	"20_6_5_120",
	"20_6_5_121"
	]
champs = [
	"LeeSin",
	"Vi",
	"Shyvana",
	"Hecarim",
	"KhaZix"
	]

# Color gradients to use to draw data (indexed by method #)
colors = [[
	# red-yellow-green
	(255, 0, 0),
	(255, 100, 0),
	(255, 200, 0),
	(200, 255, 0),
	(100, 255, 0),
	(0, 255, 0),		
	],[
	# scale of white to  purple
	(255, 255, 255),	
	(255, 205, 255),
	(255, 155, 255),
	(255, 105, 255),
	(255, 55, 255),
	(255, 5, 255),	
	],[
	# different color for each champion (corresponds to scatterplot)
	(72, 133, 237),
	(219, 50, 54),
	(244, 194, 13),
	(60, 186, 84),
	(153, 0, 153)
	]]

# xy scale of player positions
DATA_SCALE = (14820, 14881)
# xy scale of output image
IMG_SCALE = (2430, 2430)
# radius of draw points (px)
PT_RADIUS = 30
# width of draw lines (px)
LINE_WIDTH = 15
# transparency level of drawn elements (0-255)
DRAW_ALPHA = 230
# path to map file to overlay data on
MAP_FILE = "img/util/mapLgGs.png"

# helper fn to scale xy tuple val from src to dst scale
def scale(val, src, dst):
	return ((val[0]*dst[0])/src[0], (val[1]*dst[1])/src[1])

# key fns to use when sorting
def winRateKey(cluster):
	return cluster[1]
def weightKey(cluster):
	return cluster[2]
# list of key fns, indexed by method #
keyFuncs = [winRateKey, weightKey]


# builds list of clusters; each is a 3-tuple with list of 5 image-scaled coordinates, winrate for cluster, and avg weight of cluster
def buildClusters(fileID):
	clusterFile = codecs.open('output/cluster_200_' + fileID, encoding='utf-8')
	weightFile = codecs.open('output/weights_200_' + fileID, encoding='utf-8')
	rawClusters = json.load(clusterFile)
	dataWeights = json.load(weightFile);

	# calculate cumulative average weights of each cluster
	clusterWeights = [0 for x in range(len(rawClusters))];
	for dp in dataWeights:
		# sum all weights
		for i in range(len(clusterWeights)):
			clusterWeights[i] += dp[i]
	for i in range(len(clusterWeights)):
		# divide all sums by num of datapoints
		clusterWeights[i] = clusterWeights[i]/len(dataWeights)

	# build result cluster list
	clusters = []
	for i in range(len(rawClusters)):
		clus = rawClusters[i]
		clusters += [(
			# image-scaled coordinate list
			[scale((pt['x'], pt['y']), DATA_SCALE, IMG_SCALE) for pt in clus[:len(clus)-2]], 
			# cluster winrate
			clus[len(clus)-1], 
			# cluster weight
			clusterWeights[i])]
	


	# sort clusters by appropriate method
	clusters = sorted(clusters, key=keyFuncs[DRAW_METHOD])
	
	#print(len(clusters))
	return clusters

# draws pretty stuff
def drawClusters(clusters, filename, colors):	

	# get base map as output image
	outImage = Image.open(MAP_FILE)

	for i in range(len(clusters)):
		clus = clusters[i]
		
		# draw this cluster's data line on a new bitmap image
		tempImage = Image.new('RGBA', IMG_SCALE, (0, 0, 0, 0))
		tempDraw = ImageDraw.Draw(tempImage)
		color = colors[i] + (DRAW_ALPHA,)
		tempDraw.line(clus[0], color, LINE_WIDTH)
		for pt in clus[0]:
			tempDraw.ellipse([pt[0]-PT_RADIUS, pt[1]-PT_RADIUS, pt[0]+PT_RADIUS, pt[1]+PT_RADIUS], color, color)

		# overlay this cluster's data image on output file
		tempImage = tempImage.transpose(Image.FLIP_TOP_BOTTOM)
		outImage.paste(tempImage,(0, 0),tempImage)
	
	outImage.save(filename)


if __name__ == "__main__":

	# will hold clusters for all champions
	clusters = []

	# for each champion:
	for i in range(len(fileIDs)):
		clusters = clusters + [buildClusters(fileIDs[i])]

		# print data to stick in scatterplot
		for clus in clusters[i]:
			print(str(clus[1]) + " " + str(clus[2]))

		# draw method 0
		top3bot3WR = clusters[i][:3] + clusters[i][len(clusters[i])-3:]
		drawClusters(top3bot3WR, "img/" + champs[i] + "_TopBot3WR.png", colors[0])

		# draw method 1
		top6weight = clusters[i][:6]
		drawClusters(top6weight, "img/" + champs[i] + "_Top6Weight.png", colors[1])

	# draw hand-picked clusters for each champ
	bestClusters = [
	clusters[0][18],
	clusters[1][16],
	clusters[2][17],
	clusters[3][19],
	clusters[4][18]
	]
	drawClusters(bestClusters, "img/Best_Paths_Handpicked.png", colors[2])
