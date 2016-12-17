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

Run `python JunglerDataVisualization.py 0` to generate bottom3/top3 winrate cluster maps for each champion
Run `python JunglerDataVisualization.py 1` to generate top6 avg weighted cluster maps for each champion
Both will print a table of winrate to avg weight for each cluster for each champion



