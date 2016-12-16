'''
JunglerDataVisualization.py

Uses cluster data (centroids+winrates) and datapoint-cluster-weights matrix to 
visualize effectiveness of jungler paths for various champions.

Run `python JunglerDataVisualization.py 0` to generate bottom3/top3 cluster maps for each champion
Run `python JunglerDataVisualization.py 1` to generate top6 avg weighted cluster maps for each champion
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

# Color values to use to draw data
colors = [[
	(255, 0, 0),
	(255, 100, 0),
	(255, 200, 0),
	(200, 255, 0),
	(100, 255, 0),
	(0, 255, 0),		
	],[
	(255, 255, 255),	
	(255, 205, 255),
	(255, 155, 255),
	(255, 105, 255),
	(255, 55, 255),
	(255, 5, 255),	
	]]

# xy scale of player positions
DATA_SCALE = (14820, 14881)
# xy scale of output image
IMG_SCALE = (2430, 2430)
# radius of draw points (px)
PT_RADIUS = 30
# width of draw lines (px)
LINE_WIDTH = 15
# transparency level (0-255)
DRAW_ALPHA = 230
# path to map file to overlay data on
MAP_FILE = "img/util/mapLg.png"

# Default draw method
# 0 = top3/bottom3 winrate clusters; 1 = top6 weighted clusters
DRAW_METHOD = 0


def scale(val, src, dst):
	return ((val[0]*dst[0])/src[0], (val[1]*dst[1])/src[1])

def winRateKey(cluster):
	return cluster[1]
def weightKey(cluster):
	return cluster[2]
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
		# divide all sums by num of clusters
		clusterWeights[i] = clusterWeights[i]/len(clusterWeights)

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

def drawClusters(clusters, champ, colors):	
	# get base map as output image
	outName = "img/" + champ + "_Method"+str(DRAW_METHOD)+".png"
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
	
	outImage.save(outName)


if __name__ == "__main__":

	# override default draw method if one specified in args
	if (len(sys.argv) > 1):
		DRAW_METHOD = int(sys.argv[1])

	for i in range(len(fileIDs)):
		clusters = buildClusters(fileIDs[i])
		if DRAW_METHOD == 0:
			clusters = clusters[:3] + clusters[len(clusters)-3:]
		elif DRAW_METHOD == 1:
			clusters = clusters[:6]
		drawClusters(clusters, champs[i], colors[DRAW_METHOD])

