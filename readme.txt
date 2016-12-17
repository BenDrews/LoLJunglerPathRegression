(c) Gary Chen, Ben Drews, Justin Smilan 2016 - CSCI 373 AI, Prof. Jon Park


LoLPathingCluster.py

Pulls the targeted jungle path data from the match files stored in the data directory, and
then creates fuzzy clusters that represent the common paths taken. Output will be written to
three files in the output directory corresponding to the position data, cluster data, and 
weight data.

Run `python LoLPathingCluster.py' to create clusters.

Parameters can be changed through their respective constants in the source file.


LoLMatchCrawler.py

Recursively crawls the Riot Api searching for recent match data based on a seed player.

Due to rate limiting by Riot, games can only be pulled at a rate of 50 matches per minute.

JSON files respresenting the match data will be written to the data directory.

Run `python LoLMatchCrawler.py' to begin gathering data.


JunglerDataVisualization.py

Uses cluster data (centroids+winrates) and datapoint-cluster-weights matrix to 
visualize effectiveness of jungler paths for various champions.

This script will generate:
	1. For each champion, a map with the paths representing the top 3 and bottom 3 win rate clusters
	2. For each chapmion, a map the paths representing the top 6 weighted clusters over all datapoints
	3. A map with a hand-curated selection of one relatively successful and popular  path/cluster for each champion
	4. A table (output to stdout) with every cluster's winrate and average weight.  Will be in order of chapmion
	   list, and by ascending winrate within each cluster.




