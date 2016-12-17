'''
LoLMatchCrawler.py

Recursively crawls the Riot Api searching for recent match data based on a seed player.

Due to rate limiting by Riot, games can only be pulled at a rate of 50 matches per minute.

JSON files respresenting the match data will be written to the data directory.

Run `python LoLMatchCrawler.py' to begin gathering data.

(c) Gary Chen, Ben Drews, Justin Smilan 2016 - CSCI 373 AI, Prof. Jon Park
'''
import urllib2
import json
import time
import Queue
import codecs

DEFAULT_SEED = 25714970

MATCHLIST_REQ_BASE = "https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/"
MATCHLIST_PARAMS = "&beginIndex=0&endIndex=100&rankedQueues=RANKED_SOLO_5x5"

MATCH_REQ_BASE = "https://na.api.pvp.net/api/lol/na/v2.2/match/"
MATCH_TIMELINE = "&includeTimeline=true"

API_KEY = "?api_key=3a871ab5-d3ed-4975-9e03-3b0b1165e171"


#Crawl the riot api for recent match data based on a seed player
def gatherData():
   summonerQueue = Queue.Queue(maxsize=0)
   summonerQueue.put(DEFAULT_SEED)
   while(not summonerQueue.empty()):
      url = MATCHLIST_REQ_BASE + str(summonerQueue.get()) + API_KEY + MATCHLIST_PARAMS
      print(url)

      responseString = "";
      try:
         matchListResponse = urllib2.urlopen(url)
         responseString = matchListResponse.read().decode('utf-8')
         print(responseString)
         
      except urllib2.HTTPError as err:
         if err.code == 429:
            time.sleep(10)
            continue
         else:
            continue

      matchListData = json.loads(responseString)
      
      #This should be multithreaded.
      if(matchListData.has_key('status') and matchListData['status'].has_key('status_code') and matchListData['status']['status_code'] == 429):
         time.sleep(10)
      
      if(matchListData.has_key('matches')):
         matchArray = matchListData['matches']

         #Iterate over all the matches adding their summoners to the queue and writing their data to file.
         for match in matchArray:
            try:
               matchUrl = MATCH_REQ_BASE + str(match['matchId']) + API_KEY + MATCH_TIMELINE
               matchResponse = urllib2.urlopen(matchUrl)
               matchData = json.loads(matchResponse.read().decode('utf-8'))

               with codecs.open('data/match_' + str(match['matchId']) + '.txt', 'w', encoding="utf-8") as outfile:
                  json.dump(matchData, outfile, sort_keys = True, indent = 4, ensure_ascii=False, encoding='utf-8', separators=(',', ':'))

            #Add the summoners ids of the players in the game to the summoner queue
               participantArray = matchData['participantIdentities']
               for participant in participantArray:
                  summonerQueue.put(participant['player']['summonerId'])

            except urllib2.HTTPError as err:
               if err.code == 429:
                  time.sleep(10)
                  continue
               else:
                  continue
if __name__ == "__main__":
   gatherData()
      
