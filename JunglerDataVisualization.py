from PIL import Image, ImageDraw
import json
import codecs
import numpy
import sys

DATA_SCALE = (14820, 14881)
IMG_SCALE = (2430, 2430)
PT_RADIUS = 40
LINE_WIDTH = 15

def scale(val, src, dst):
	return ((val[0]*dst[0])/src[0], (val[1]*dst[1])/src[1])
def winRateKey(cluster):
	return cluster[1]

def buildClusters():
	clusterFile = codecs.open('output/cluster_200_20_6_5_254', encoding='utf-8')
	weightFile = codecs.open('output/weights_200_20_6_5_254', encoding='utf-8')

	rawClusters = json.load(clusterFile)
	dataWeights = json.load(weightFile);

	clusterWeights = [0 for x in range(len(rawClusters))];
	for dp in dataWeights:
		for i in range(len(clusterWeights)):
			clusterWeights[i] += dp[i]
	for i in range(len(clusterWeights)):
		clusterWeights[i] = clusterWeights[i]/len(clusterWeights)

	clusters = []
	for i in range(len(rawClusters)):
		clus = rawClusters[i]
		clusters += [(([scale((pt['x'], pt['y']), DATA_SCALE, IMG_SCALE) for pt in clus[:len(clus)-2]], clus[len(clus)-1], clusterWeights[i]))]
	clusters = sorted(clusters, key=winRateKey)

	print(len(clusters))
	return clusters

def drawClusters(clusters, outName):	

	outImage = Image.new('RGBA', IMG_SCALE, (0, 0, 0, 0))
	draw = ImageDraw.Draw(outImage)

	redness = 0;
	for clus in clusters[:3] + clusters[len(clusters)-3:]:
		print("lol");
		tempImage = Image.new('RGBA', IMG_SCALE, (0, 0, 0, 0))
		tempDraw = ImageDraw.Draw(tempImage)

		color = (255, 255-redness, 255-redness, 230)
		ptColor = (color[0], color[1], color[2], 230)
		tempDraw.line(clus[0], color, LINE_WIDTH)
		for pt in clus[0]:
			tempDraw.ellipse([pt[0]-PT_RADIUS, pt[1]-PT_RADIUS, pt[0]+PT_RADIUS, pt[1]+PT_RADIUS], ptColor, ptColor)

		outImage.paste(tempImage,(0, 0),tempImage)
		redness = redness + int((1/6)*255)
	

	outImage = outImage.transpose(Image.FLIP_TOP_BOTTOM)
	outImage.save(outName)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		raise Exception("Specify output file name in args")
	clusters = buildClusters()
	drawClusters(clusters, sys.argv[1])

