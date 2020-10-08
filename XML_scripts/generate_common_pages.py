#!/usr/bin/python
import pdb
import time, sys
from datetime import timedelta, date, datetime
import time
import re
import subprocess
from operator import itemgetter, attrgetter, methodcaller

from optparse import OptionParser,OptionValueError

import fileinput
import os.path

import stat_conf
import copy

stat_conf.read_config()

sys.path.append("../")

import ezstatslib
from ezstatslib import Team,Player
from ezstatslib import enum,checkNew,htmlLink
from ezstatslib import NEW_GIF_TAG as newGifTag
from ezstatslib import PickMapItemElement,DamageElement,DeathElement

import HTML

import random

import xml.etree.ElementTree as ET
import json

from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE, ST_MTIME

import xml.etree.ElementTree as ET

from collections import Counter

ezstatslib.REPORTS_FOLDER = stat_conf.reports_dir
ezstatslib.LOGS_INDEX_FILE_NAME = "index.html"

totalsPath = ezstatslib.REPORTS_FOLDER + ezstatslib.TOTALS_FILE_NAME

usageString = "" 
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("--no-links", action="store_true",   dest="noLinks", default=False,   help="")

(options, restargs) = parser.parse_args()

jsonDirPath = ezstatslib.REPORTS_FOLDER + "json/"
entries = (os.path.join(jsonDirPath, fn) for fn in os.listdir(jsonDirPath))
entries = ((os.stat(path), path) for path in entries if ".json" in path)

entries = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))

class JsonPlayerMatch:
    def __init__(self):
        self.dt = 0
        self.mapname = ""
        self.gamemode = ""
        self.reportname = ""
        
        self.frags = 0
        self.deaths = 0
        self.suicides = 0
        self.ra = 0
        self.ya = 0
        self.ga = 0
        self.mh = 0
        
        self.achievements = {}
        self.rlskill = {}
        
        self.resultPlace = 0
        self.isLast = False
        
        self.duels = {}
        
        self.spawnFrags = 0
        self.maxspeed = 0        
        self.avgspeed = 0
        self.givenDamage = 0
        self.takenDamage = 0
        self.selfDamage = 0
        self.playTime = 0
        self.connectionTime = 0
        
        self.rl_dhs_selfdamage = []
        
        self.killStreaks = []
        self.deathStreaks = []
        
        self.killStealsDuels = {}
        
        self.killsByMinutes = []
        self.deathsByMinutes = []
        self.suicidesByMinutes = []



class JsonPlayer:
    def __init__(self):
        self.name = ""
        self.frags = 0
        self.deaths = 0
        self.suicides = 0
        self.ra = 0
        self.ya = 0
        self.ga = 0
        self.mh = 0
        
        self.spawnFrags = 0
        self.givenDamage = 0
        self.takenDamage = 0
        self.selfDamage = 0
        
        self.achievements = {}
        self.rlskill = {}
        
        self.matchesPlayed = 0
        
        self.fragsByMatches = []
        self.fragsByMatchesPairs = []
        
        self.rankByMatches = []
        self.rankByMatchesPairs = []
        
        self.resultPlace = 0
        self.isLast = False
        self.resultPlacesByMatches = {}
        
        self.duels = {}
        self.killStealsDuels = {}
        
        self.rl_dhs_selfdamage = []
        
        
        self.matches = {}
        
    def rank(self):
        return self.frags - self.deaths - self.suicides

jsonPlayers = []
allCDates = set()
    
for cdate, size, path in sorted(entries, reverse=False):
    #print time.ctime(cdate), size, os.path.basename(path)    
    #print "AAA", cdate, size, path
    
    dateRes = re.search("(?<=]_).*(?=.html.json)", path)                  
    dt = datetime.strptime(dateRes.group(0), "%Y-%m-%d_%H_%M_%S")
    dateStruct = datetime.strptime(dateRes.group(0).split("_")[0], "%Y-%m-%d")
    
    allCDates.add(dt)    
    
    with open(path, 'r') as f:        
        jsonStrRead = json.load(f)
        #print "JJJ", jsonStrRead
        mapname = ""
        gamemode = ""
        reportname = ""
        for ooo in jsonStrRead:
            #print ooo
            if ooo == "matchdate":
                pass
            
            if ooo == "mapname":
                mapname = jsonStrRead[ooo]

            if ooo == "gamemode":
                gamemode = jsonStrRead[ooo]
                
            if ooo == "reportname":
                reportname = jsonStrRead[ooo]

            if ooo == "players":
                for oo in jsonStrRead[ooo]:
                    currentJsonPlayer = JsonPlayer()
                    
                    currentJsonMatch = JsonPlayerMatch()
                    currentJsonMatch.dt = dt
                    currentJsonMatch.mapname = mapname
                    currentJsonMatch.gamemode = gamemode
                    currentJsonMatch.reportname = reportname
                    
                    currentJsonPlayer.matchesPlayed = 1
                    for o in oo:
                        # print o
                        # exec("currentJsonPlayer.%s = %s" % (o, oo[o]))
                        if o == "name":
                            currentJsonPlayer.name = oo[o]
                        if o == "frags":
                            currentJsonPlayer.frags = oo[o]
                            currentJsonMatch.frags  = oo[o]
                        if o == "suicides":
                            currentJsonPlayer.suicides = oo[o]
                            currentJsonMatch.suicides  = oo[o]
                        if o == "ga":
                            currentJsonPlayer.ga = oo[o]
                            currentJsonMatch.ga  = oo[o]
                        if o == "ya":
                            currentJsonPlayer.ya = oo[o]
                            currentJsonMatch.ya  = oo[o]
                        if o == "ra":
                            currentJsonPlayer.ra = oo[o]
                            currentJsonMatch.ra  = oo[o]
                        if o == "mh":
                            currentJsonPlayer.mh = oo[o]
                            currentJsonMatch.mh  = oo[o]
                        if o == "deaths":
                            currentJsonPlayer.deaths = oo[o]
                            currentJsonMatch.deaths  = oo[o]
                        if o == "achievements":
                            for ach in oo[o]:
                                if isinstance(ach,int):
                                    achID = ach
                                    if not achID in currentJsonPlayer.achievements:
                                        currentJsonPlayer.achievements[achID] = 1
                                        currentJsonMatch.achievements[achID] = 1                                        
                                    else:
                                        currentJsonPlayer.achievements[achID] += 1
                                        currentJsonMatch.achievements[achID] += 1
                                else:
                                    for acho in ach:
                                        if acho == "achID":
                                            achID = ach[acho]
                                            if not achID in currentJsonPlayer.achievements:
                                                currentJsonPlayer.achievements[achID] = 1
                                                currentJsonMatch.achievements[achID] = 1
                                            else:
                                                currentJsonPlayer.achievements[achID] += 1
                                                currentJsonMatch.achievements[achID] += 1
                        if o == "rlskill":
                            currentJsonPlayer.rlskill = oo[o]
                            currentJsonMatch.rlskill = oo[o]
                        if o == "resultPlace":
                            currentJsonPlayer.resultPlace = oo[o]
                            currentJsonMatch.resultPlace = oo[o]
                        if o == "isLast":
                            currentJsonPlayer.isLast = oo[o]
                            currentJsonMatch.isLast = oo[o]
                        if o == "duels":
                            currentJsonPlayer.duels = oo[o]
                            currentJsonMatch.duels = oo[o]
                        if o == "spawnFrags":
                            currentJsonPlayer.spawnFrags = oo[o]
                            currentJsonMatch.spawnFrags = oo[o]
                        if o == "maxspeed":
                            #currentJsonPlayer.maxspeed = oo[o]
                            currentJsonMatch.maxspeed = oo[o]
                        if o == "avgspeed":
                            #currentJsonPlayer.avgspeed = oo[o]
                            currentJsonMatch.avgspeed = oo[o]
                        if o == "givenDamage":
                            currentJsonPlayer.givenDamage = oo[o]
                            currentJsonMatch.givenDamage = oo[o]
                        if o == "takenDamage":
                            currentJsonPlayer.takenDamage = oo[o]
                            currentJsonMatch.takenDamage = oo[o]
                        if o == "selfDamage":
                            currentJsonPlayer.selfDamage = oo[o]
                            currentJsonMatch.selfDamage = oo[o]
                        if o == "playTime":
                            #currentJsonPlayer.playTime = oo[o]
                            currentJsonMatch.playTime = oo[o]
                        if o == "connectionTime":
                            #currentJsonPlayer.connectionTime = oo[o]
                            currentJsonMatch.connectionTime = oo[o]
                        if o == "rl_dhs_selfdamage":
                            currentJsonPlayer.rl_dhs_selfdamage = oo[o]
                            currentJsonMatch.rl_dhs_selfdamage = oo[o]
                        if o == "killStreaks":
                            #currentJsonPlayer.killStreaks = oo[o]
                            currentJsonMatch.killStreaks = oo[o]
                        if o == "deathStreaks":
                            #currentJsonPlayer.deathStreaks = oo[o]
                            currentJsonMatch.deathStreaks = oo[o]
                        if o == "killStealsDuels":
                            currentJsonPlayer.killStealsDuels = oo[o]
                            currentJsonMatch.killStealsDuels = oo[o]
                        if o == "killsByMinutes":
                            currentJsonMatch.killsByMinutes = oo[o]
                        if o == "deathsByMinutes":
                            currentJsonMatch.deathsByMinutes = oo[o]
                        if o == "suicidesByMinutes":
                            currentJsonMatch.suicidesByMinutes = oo[o]                            
                            
                    isFound = False
                    for plJson in jsonPlayers:
                        if plJson.name == currentJsonPlayer.name:
                            isFound = True
                            plJson.frags += currentJsonPlayer.frags
                            plJson.suicides += currentJsonPlayer.suicides
                            plJson.ga += currentJsonPlayer.ga
                            plJson.ra += currentJsonPlayer.ra
                            plJson.ya += currentJsonPlayer.ya
                            plJson.mh += currentJsonPlayer.mh
                            plJson.deaths += currentJsonPlayer.deaths
                            plJson.matchesPlayed += currentJsonPlayer.matchesPlayed
                            plJson.spawnFrags += currentJsonPlayer.spawnFrags
                            plJson.givenDamage += currentJsonPlayer.givenDamage
                            plJson.takenDamage += currentJsonPlayer.takenDamage
                            plJson.selfDamage += currentJsonPlayer.selfDamage
                            plJson.rl_dhs_selfdamage += currentJsonPlayer.rl_dhs_selfdamage
                            
                            plJson.achievements = dict(Counter(plJson.achievements) + Counter(currentJsonPlayer.achievements))
                            plJson.rlskill = dict(Counter(plJson.rlskill) + Counter(currentJsonPlayer.rlskill))
                            
                            plJson.fragsByMatches.append(currentJsonPlayer.frags)
                            plJson.fragsByMatchesPairs.append([dt, currentJsonPlayer.frags])
                            plJson.rankByMatches.append(currentJsonPlayer.frags-currentJsonPlayer.deaths)
                            plJson.rankByMatchesPairs.append([dt, currentJsonPlayer.frags-currentJsonPlayer.deaths])
                            
                            plJson.resultPlacesByMatches[dt] = currentJsonPlayer.resultPlace
                            
                            for currKey in currentJsonPlayer.duels.keys():
                                if not currKey in plJson.duels.keys():
                                    plJson.duels[currKey] = [0,0]
                                    plJson.duels[currKey][0] = currentJsonPlayer.duels[currKey][0]
                                    plJson.duels[currKey][1] = currentJsonPlayer.duels[currKey][1]
                                else:
                                    plJson.duels[currKey][0] += currentJsonPlayer.duels[currKey][0]
                                    plJson.duels[currKey][1] += currentJsonPlayer.duels[currKey][1]
                                    
                            for currKey in currentJsonPlayer.killStealsDuels.keys():
                                if not currKey in plJson.killStealsDuels.keys():
                                    plJson.killStealsDuels[currKey] = currentJsonPlayer.killStealsDuels[currKey]
                                else:
                                    plJson.killStealsDuels[currKey][0] += currentJsonPlayer.killStealsDuels[currKey][0]
                                    plJson.killStealsDuels[currKey][1] += currentJsonPlayer.killStealsDuels[currKey][1]                                    
                                    
                            plJson.matches[dt] = currentJsonMatch
            
                    if not isFound:
                        newJsonPlayer = copy.deepcopy(currentJsonPlayer)
                        
                        newJsonPlayer.fragsByMatches.append(newJsonPlayer.frags)
                        newJsonPlayer.fragsByMatchesPairs.append([dt, newJsonPlayer.frags])
                        newJsonPlayer.rankByMatches.append(newJsonPlayer.frags-newJsonPlayer.deaths)
                        newJsonPlayer.rankByMatchesPairs.append([dt, newJsonPlayer.frags-newJsonPlayer.deaths])
                        
                        newJsonPlayer.resultPlacesByMatches[dt] = newJsonPlayer.resultPlace
                        
                        newJsonPlayer.matches[dt] = currentJsonMatch
                        
                        jsonPlayers.append(newJsonPlayer)

                
                
for pl in jsonPlayers:
    correctedFragsByMatches = []
    for cdate in sorted(allCDates):
        isFound = False
        fragsVal = -1
        for fragsPair in pl.fragsByMatchesPairs:
            if fragsPair[0] == cdate:
                fragsVal =  fragsPair[1]
                break        
        correctedFragsByMatches.append(fragsVal)
    pl.fragsByMatches = correctedFragsByMatches
    
    correctedRankByMatches = []
    for cdate in sorted(allCDates):
        isFound = False
        rankVal = -10000
        for rankPair in pl.rankByMatchesPairs:
            if rankPair[0] == cdate:
                rankVal =  rankPair[1]
                break        
        correctedRankByMatches.append(rankVal)
    pl.rankByMatches = correctedRankByMatches
                
totalsStr = "===== TOTALS (%d) =====" % (len(jsonPlayers))
totalsStr += "<hr>\n"
for plJson in jsonPlayers:
    totalsStr += "\t%s: matches:%d, frags:%d, deaths: %d, suicides: %d, ga: %d, ya: %d, ra: %d, mh: %d" % (plJson.name, plJson.matchesPlayed, plJson.frags, plJson.deaths, plJson.suicides, plJson.ga, plJson.ya, plJson.ra, plJson.mh)
    
    totalsStr += "<br>\n"
    
    totalsStr += "\tachievements: "
    for achID in plJson.achievements.keys():
        ach = ezstatslib.Achievement(achID)
        totalsStr += "%s(%d)," % (ach.toString(), plJson.achievements[achID])
    totalsStr = totalsStr[:-1]
    
    totalsStr += "<br>\n"
    
    totalsStr += "\tRLSkill: "
    for rlkey in plJson.rlskill.keys():
        totalsStr += "%s(%d)," % (rlkey, plJson.rlskill[rlkey])
    totalsStr = totalsStr[:-1]
    
    totalsStr += "<br>\n"
    
    totalsStr += "\tavg per match: frags:%f, deaths: %f, suicides: %f, ga: %f, ya: %f, ra: %f, mh: %f" % (float(plJson.frags)/plJson.matchesPlayed, float(plJson.deaths)/plJson.matchesPlayed, float(plJson.suicides)/plJson.matchesPlayed, float(plJson.ga)/plJson.matchesPlayed, float(plJson.ya)/plJson.matchesPlayed, float(plJson.ra)/plJson.matchesPlayed, float(plJson.mh)/plJson.matchesPlayed)
    totalsStr += "<br>\n"
    totalsStr += "frags by matches: %s" % (plJson.fragsByMatches)
    totalsStr += "<hr>\n"
                
logsf = open(totalsPath, "w")
#logsf.write(ezstatslib.HTML_HEADER_STR)


pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
#pageTitle = "%s %s %s" % (options.leagueName, mapName, matchdate)  # global values
pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", "TOTALS")
pageHeaderStr = pageHeaderStr.replace("SLIDER_STYLE", "")
#pageHeaderStr += ezstatslib.HTML_HEADER_SCRIPT_GOOGLE_CHARTS_LOAD
    
logsf.write(pageHeaderStr)

# highcharts totals frags progress -->
highchartsTotalsFragsFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_FRAGS_PROGRESS_FUNCTION
            
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("GRAPH_TITLE", "Totals frags progress")
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("Y_AXIS_TITLE", "Frags")
    
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("MIN_PLAYER_FRAGS", "")
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("MAX_PLAYER_FRAGS", "")
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("EXTRA_XAXIS_OPTIONS", "")
        
# " name: 'rea[rbf]',\n" \
# " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    

hcDelim = "}, {\n"
rowLines = ""        
for plJson in jsonPlayers:
    if rowLines != "":
        rowLines += hcDelim
    
    rowLines += "name: '%s (%d)',\n" % (plJson.name, plJson.matchesPlayed)
    # rowLines += "data: [0"
    rowLines += "data: [[0,0]"
    
    graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_FRAGS_PROGRESS_GRANULARITY)
    for fr in plJson.fragsByMatches:
        # rowLines += ",%d" % (minEl[pl.name])
        if fr != -1:
            rowLines += ",[%f,%d]" % (graphGranularity, fr)  # TODO format, now is 0.500000
        graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_FRAGS_PROGRESS_GRANULARITY)
        
    rowLines += "]\n"        
    
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    
    # tooltip style
highchartsTotalsFragsFunctionStr = highchartsTotalsFragsFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
logsf.write(highchartsTotalsFragsFunctionStr)
# <-- highcharts totals frags progress

# highcharts totals AVG frags progress -->
highchartsTotalsAvgFragsFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_FUNCTION
            
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("GRAPH_TITLE", "Totals AVG frags progress")
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("Y_AXIS_TITLE", "Frags")
    
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("MIN_PLAYER_FRAGS", "")
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("MAX_PLAYER_FRAGS", "")
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("EXTRA_XAXIS_OPTIONS", "")
        
# " name: 'rea[rbf]',\n" \
# " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    

hcDelim = "}, {\n"
rowLines = ""        
for plJson in jsonPlayers:
    if rowLines != "":
        rowLines += hcDelim
    
    rowLines += "name: '%s (%d)',\n" % (plJson.name, plJson.matchesPlayed)
    # rowLines += "data: [0"
    rowLines += "data: [[0,0]"
        
    graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_GRANULARITY)
    avgFragsVal = 0.0
    currentMatchesCnt = 0
    currentFragsSum = 0
    for fr in plJson.fragsByMatches:
        # rowLines += ",%d" % (minEl[pl.name])
        if fr != -1:
            currentMatchesCnt += 1
            currentFragsSum += fr
            avgFragsVal = float(currentFragsSum) / currentMatchesCnt
                
            rowLines += ",[%f,%f]" % (graphGranularity, avgFragsVal)  # TODO format, now is 0.500000
        graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_GRANULARITY)
        
    rowLines += "]\n"        
    
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    
    # tooltip style
highchartsTotalsAvgFragsFunctionStr = highchartsTotalsAvgFragsFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
logsf.write(highchartsTotalsAvgFragsFunctionStr)
# <-- highcharts totals AVG frags progress

# highcharts totals rank progress -->
highchartsTotalsRankFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_RANK_PROGRESS_FUNCTION
            
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("GRAPH_TITLE", "Totals rank progress")
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("Y_AXIS_TITLE", "Rank")
    
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("MIN_PLAYER_FRAGS", "")
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("MAX_PLAYER_FRAGS", "")
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("EXTRA_XAXIS_OPTIONS", "")
        
# " name: 'rea[rbf]',\n" \
# " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    

hcDelim = "}, {\n"
rowLines = ""        
for plJson in jsonPlayers:
    if rowLines != "":
        rowLines += hcDelim
    
    rowLines += "name: '%s (%d)',\n" % (plJson.name, plJson.matchesPlayed)
    # rowLines += "data: [0"
    rowLines += "data: [[0,0]"
        
    graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_RANK_PROGRESS_GRANULARITY)
    totalRank = 0
    for rank in plJson.rankByMatches:
        # rowLines += ",%d" % (minEl[pl.name])
        if rank != -10000:
            totalRank += rank
            rowLines += ",[%f,%d]" % (graphGranularity, totalRank)  # TODO format, now is 0.500000
        graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_TOTALS_RANK_PROGRESS_GRANULARITY)
        
    rowLines += "]\n"        
    
    # add negative zone
    rowLines += ",zones: [{ value: 0, dashStyle: 'Dash' }]"
    
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    
    # tooltip style
highchartsTotalsRankFunctionStr = highchartsTotalsRankFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
logsf.write(highchartsTotalsRankFunctionStr)
# <-- highcharts totals rank progress

logsf.write(ezstatslib.HTML_SCRIPT_ON_PAGE_LOAD_FUNCTION.replace("FUNCTIONS",""))
logsf.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)

logsf.write(totalsStr)

logsf.write("===== TOTALS (%d) =====" % (len(jsonPlayers)))
logsf.write("<hr>\n")

logsf.write(ezstatslib.HTML_PRE_CLOSE_TAG)
logsf.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_FRAGS_PROGRESS_DIV_TAG)
logsf.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_RANK_PROGRESS_DIV_TAG)
logsf.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_DIV_TAG)



    
# add script section for folding
logsf.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)    
    
logsf.write(ezstatslib.HTML_FOOTER_NO_PRE)

# logsf.write(ezstatslib.HTML_FOOTER_STR)
logsf.close()            



def addTableColumn(htmlTable, columnNum, duels):
    for trow in htmlTable.rows:
        #plName = trow.cells[0].replace("<b>","").replace("</b>","")
        plNameRe = re.search("(?<=<b>).*(?=</b>)", trow.cells[0])
        plName = plNameRe.group(0)
        
        
        if not plName in duels.keys():
            continue
        
        kills  = duels[plName][0]
        deaths = duels[plName][1]
        
        cellVal = "%s / %s" % (ezstatslib.htmlBold(kills)  if kills  > deaths else str(kills),
                               ezstatslib.htmlBold(deaths) if deaths > kills  else str(deaths))
             
        cellColor = ""
        if kills == deaths:
            cellColor = ezstatslib.BG_COLOR_LIGHT_GRAY
        elif kills > deaths:
            cellColor = ezstatslib.BG_COLOR_GREEN
        else:
            cellColor = ezstatslib.BG_COLOR_RED
         
        trow.cells[columnNum].text = cellVal
        trow.cells[columnNum].bgcolor = cellColor
        
currentDatetime = datetime.now()
# PLAYERS PAGES
for plJson in jsonPlayers:
    playerPagePath = ezstatslib.REPORTS_FOLDER + ezstatslib.escapePlayerName(plJson.name) + ".html"

    playerText = ""
    
    playerText += "<table style=\"width: 100%\">"
    playerText += "<tr>"
    playerText += "<td>"
    playerText += "<p style=\"text-align:left;font-size: 4\"> %s </p>" % (htmlLink(ezstatslib.ALLPLAYERS_FILE_NAME, linkText = "<-- All Players page", isBreak=False))
    playerText += "</td>"
    playerText += "<td>"
    playerText += "<i><p style=\"text-align:right;font-size: 4\">Last update: %s</p></i>" % ( str(currentDatetime))
    playerText += "</td>"
    playerText += "</tr>"
    playerText += "</table>"
    
    playerText += "<h1><p style=\"text-align:center;\"> ===== %s =====</p></h1>" % (plJson.name)
    playerText += "\tmatches:%d [%d], frags:%d, deaths: %d, suicides: %d, ga: %d, ya: %d, ra: %d, mh: %d" % (plJson.matchesPlayed, len(plJson.matches), plJson.frags, plJson.deaths, plJson.suicides, plJson.ga, plJson.ya, plJson.ra, plJson.mh)
    
    playerText += "<br>\n"
    
    # playerText += "\tachievements: "
    # for achID in plJson.achievements.keys():
        # ach = ezstatslib.Achievement(achID)
        # playerText += "%s(%d)," % (ach.toString(), plJson.achievements[achID])
    # playerText = playerText[:-1]    
    # playerText += "<br>\n"
    
    playerText += "\tRLSkill: "
    for rlkey in plJson.rlskill.keys():
        playerText += "%s(%d)," % (rlkey, plJson.rlskill[rlkey])
    playerText = playerText[:-1]
    
    playerText += "<br>\n"
    
    playerText += "\tavg per match: frags:%f, deaths: %f, suicides: %f, ga: %f, ya: %f, ra: %f, mh: %f" % (float(plJson.frags)/plJson.matchesPlayed, float(plJson.deaths)/plJson.matchesPlayed, float(plJson.suicides)/plJson.matchesPlayed, float(plJson.ga)/plJson.matchesPlayed, float(plJson.ya)/plJson.matchesPlayed, float(plJson.ra)/plJson.matchesPlayed, float(plJson.mh)/plJson.matchesPlayed)
    playerText += "<br>\n"    
    #playerText += "\tgame positions: %s" % (plJson.resultPlacesByMatches)
    #playerText += "<br>\n"
    
    places = {}
    for match in plJson.matches.values():
        if match.resultPlace in places.keys():
            places[match.resultPlace] += 1
        else:
            places[match.resultPlace] = 1
    playerText += "\tpositions sum: %s" % (places)
    playerText += "<br>\n"
    
    isLastCount = 0
    for match in plJson.matches.values():
        if match.isLast == True:
            isLastCount += 1
    playerText += "\tisLast count: %d\n" % (isLastCount)
    playerText += "<br>\n"
        
    #playerText += "\tfrags by matches: %s" % (plJson.fragsByMatches)
    #playerText += "<br>\n"
    # playerText += "\tduels: %s" % (plJson.duels)
    # playerText += "<br>\n"
        
    headerRow=['Name', 'Last match', 'Last 5 matches', 'Last 10 matches', 'Total']
    colAlign=[]
    for i in xrange(len(headerRow)):
        colAlign.append("center")

    htmlTable = HTML.Table(header_row=headerRow, border="1", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt; border-collapse: collapse; border: 4px solid black")
                       
    totalNum = len(plJson.duels.keys())
    for duelKey in plJson.duels.keys():
        if duelKey == plJson.name:
            continue
    
        tableRow = HTML.TableRow(cells=[ htmlLink(ezstatslib.escapePlayerName(duelKey) + ".html", linkText=ezstatslib.htmlBold(duelKey), isBreak=False) ], style="border:4px solid black")
        #tableRow = HTML.TableRow(cells=[ duelKey ], style="border:4px solid black")
        for i in xrange(len(headerRow)-1):
            tableRow.cells.append( HTML.TableCell("") )
        htmlTable.rows.append(tableRow)        
        
    sortedDTs = sorted(plJson.matches.keys(), reverse=True)
    lastDuels = plJson.matches[ sortedDTs[0] ].duels          
    
    addTableColumn(htmlTable, 1, lastDuels)
    matchNum = 1
    
    while matchNum <= 5 and matchNum < len(sortedDTs):
        for currKey in plJson.matches[ sortedDTs[matchNum] ].duels:
            if not currKey in lastDuels.keys():
                lastDuels[currKey] = plJson.matches[ sortedDTs[matchNum] ].duels[currKey]
            else:
                lastDuels[currKey][0] += plJson.matches[ sortedDTs[matchNum] ].duels[currKey][0]
                lastDuels[currKey][1] += plJson.matches[ sortedDTs[matchNum] ].duels[currKey][1]
        matchNum += 1
                
    addTableColumn(htmlTable, 2, lastDuels)
    
    while matchNum <= 10 and matchNum < len(sortedDTs):
        for currKey in plJson.matches[ sortedDTs[matchNum] ].duels:
            if not currKey in lastDuels.keys():
                lastDuels[currKey] = plJson.matches[ sortedDTs[matchNum] ].duels[currKey]
            else:
                lastDuels[currKey][0] += plJson.matches[ sortedDTs[matchNum] ].duels[currKey][0]
                lastDuels[currKey][1] += plJson.matches[ sortedDTs[matchNum] ].duels[currKey][1]
        matchNum += 1        
    addTableColumn(htmlTable, 3, lastDuels)
    
    addTableColumn(htmlTable, 4, plJson.duels)

    playerText += str(htmlTable)
    
    playerText += "<br>"
    
    playerText += "\tkillStealDuels: %s" % (plJson.killStealsDuels)
    playerText += "<hr>\n"
    
    playerText += "Sorted matches (%d):\n" % (plJson.matchesPlayed)
    for dt in sorted(plJson.matches.keys(), reverse=True):
        playerText += "\tdt: %s, map: %s, place: %d, report: %s\n" %  \
                           ( str(dt), \
                             plJson.matches[dt].mapname, \
                             plJson.matches[dt].resultPlace, \
                             htmlLink(plJson.matches[dt].reportname, isBreak = False) )
    playerText += "<hr>\n"    
    
    playerText += "</pre>PLAYERS_ACHIEVEMENTS_PLACE\n<pre>"
    
    playerText += "</pre>%s\n<pre>" % (ezstatslib.HTML_PLAYER_PAGE_LIFETIME_STATS_BY_MINUTES_DIV_TAG)
    
    # players achievements -->
    playersAchievementsStr = ezstatslib.HTML_PLAYERS_ACHIEVEMENTS_DIV_TAG    
    cellWidth = "20px"
    achievementsHtmlTable = HTML.Table(border="0", cellspacing="0", style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
    if len(plJson.achievements) != 0:
        tableRowBasic     = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold("Basic"), align="center", width=cellWidth) ])
        tableRowAdvanced  = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold("Advanced"), align="center", width=cellWidth) ])
        tableRowRare      = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold("Rare"), align="center", width=cellWidth) ])
        tableRowUltraRare = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold("UltraRare"), align="center", width=cellWidth) ])
        tableRowLegendary = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold("Legendary"), align="center", width=cellWidth) ])
        for achID in plJson.achievements.keys():
            ach = ezstatslib.Achievement(achID)
            # playerText += "%s(%d)," % (ach.toString(), plJson.achievements[achID])
            
            if ach.achlevel == ezstatslib.AchievementLevel.BASIC_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.BASIC_NEGATIVE:
                tableRowBasic.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(ach, "", plJson.achievements[achID]), align="center" ) )
            elif ach.achlevel == ezstatslib.AchievementLevel.ADVANCE_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.ADVANCE_NEGATIVE:
                tableRowAdvanced.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(ach, "", plJson.achievements[achID]), align="center" ) )
            elif ach.achlevel == ezstatslib.AchievementLevel.RARE_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.RARE_NEGATIVE:
                tableRowRare.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(ach, "", plJson.achievements[achID]), align="center" ) )
            elif ach.achlevel == ezstatslib.AchievementLevel.ULTRA_RARE:
                tableRowUltraRare.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(ach, "", plJson.achievements[achID]), align="center" ) )
            # elif ach.achlevel == ezstatslib.AchievementLevel.LEGENDARY:
            #     tableRowLegendary.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(ach, "", plJson.achievements[achID]), align="center" ) )
                
        if len(tableRowBasic.cells) != 1:
            achievementsHtmlTable.rows.append(tableRowBasic)
            
        if len(tableRowAdvanced.cells) != 1:
            achievementsHtmlTable.rows.append(tableRowAdvanced)
            
        if len(tableRowRare.cells) != 1:
            achievementsHtmlTable.rows.append(tableRowRare)
        
        if len(tableRowUltraRare.cells) != 1:        
            achievementsHtmlTable.rows.append(tableRowUltraRare)
        # achievementsHtmlTable.rows.append(tableRowLegendary)
        
    playersAchievementsStr = playersAchievementsStr.replace("PLAYERS_ACHIEVEMENTS_TABLE", str(achievementsHtmlTable)) # + ezstatslib.Achievement.generateAchievementsLevelLegendTable())
    # <-- players achievements
    
    playerText = playerText.replace("PLAYERS_ACHIEVEMENTS_PLACE", playersAchievementsStr)
                
    playerPage = open(playerPagePath, "w")

    
    pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
    pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", "%s stats" % (plJson.name))
    pageHeaderStr = pageHeaderStr.replace("SLIDER_STYLE", "")
    
    pageHeaderStr += \
        "google.charts.load('current', {'packages':['corechart', 'bar', 'line', 'timeline']});\n" \
    
    playerPage.write(pageHeaderStr)
    
    # player page kills by minutes -->       
    playerKillsByMinutesStr = ezstatslib.HTML_SCRIPT_PLAYER_PAGE_LIFETIME_STATS_BY_MINUTES_FUNCTION
    
    maxMinutes = -1
    for match in plJson.matches.values():
        matchMins = len(match.killsByMinutes)
        if matchMins >= maxMinutes:
            maxMinutes = matchMins    
    
    killsByMinutes = [0 for i in xrange(maxMinutes)]
    deathsByMinutes = [0 for i in xrange(maxMinutes)]
    suicidesByMinutes = [0 for i in xrange(maxMinutes)]
    matchesPlayedByMinutes = [0 for i in xrange(maxMinutes)]
        
    for match in plJson.matches.values():
        for k in xrange(1,min( len(match.killsByMinutes), len(killsByMinutes) )):
            killsByMinutes[k] += match.killsByMinutes[k]
            deathsByMinutes[k] += match.deathsByMinutes[k]
            suicidesByMinutes[k] += match.suicidesByMinutes[k]
            matchesPlayedByMinutes[k] += 1
    
    print "%s: matchesPlayedByMinutes: %s" % (plJson.name, str(matchesPlayedByMinutes))
    print "\tkillsByMinutes: %s" % (str(killsByMinutes))
    
    for k in xrange(1,len(killsByMinutes)):
        killsByMinutes[k] = (float(killsByMinutes[k]) / matchesPlayedByMinutes[k]) if matchesPlayedByMinutes[k] != 0 else 0
        deathsByMinutes[k] = (float(deathsByMinutes[k]) / matchesPlayedByMinutes[k]) if matchesPlayedByMinutes[k] != 0 else 0
        suicidesByMinutes[k] = (float(suicidesByMinutes[k]) / matchesPlayedByMinutes[k]) if matchesPlayedByMinutes[k] != 0 else 0
    
    playerKillsByMinutesHeaderStr = "['Minute','Kills','Deaths','Suicides'],\n"

    playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_HEADER_ROW", playerKillsByMinutesHeaderStr)
    
    playerKillsByMinutesRowsStr = ""    
    for k in xrange(1,len(killsByMinutes)):
        playerKillsByMinutesRowsStr += "['%d',%f,%f,%f],\n" % (k, killsByMinutes[k], deathsByMinutes[k], suicidesByMinutes[k])
    playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_STATS_ROWS", playerKillsByMinutesRowsStr)          
    
    playerPage.write(playerKillsByMinutesStr)
    # <-- players kills by minutes

    playerPage.write(ezstatslib.HTML_SCRIPT_ON_PAGE_LOAD_FUNCTION.replace("FUNCTIONS",""))
    
    playerPage.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)

    playerPage.write(playerText)

    playerPage.write(ezstatslib.HTML_PRE_CLOSE_TAG)
    # playerPage.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_FRAGS_PROGRESS_DIV_TAG)
    # playerPage.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_RANK_PROGRESS_DIV_TAG)
    # playerPage.write(ezstatslib.HTML_SCRIPT_HIGHCHARTS_TOTALS_AVG_FRAGS_PROGRESS_DIV_TAG)

    # add script section for folding
    playerPage.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)    
        
    playerPage.write(ezstatslib.HTML_FOOTER_NO_PRE)


    
    
def getRankTableRow(parameterName, parameterDescription, players):
    valPairs = []
    
    for pl in players:
        if pl.matchesPlayed >= 5:
            exec("valPairs.append([pl.name, float(pl.%s)/pl.matchesPlayed])" % (parameterName))
            
    valRow = ezstatslib.HTML_SCRIPT_ALL_PLAYERS_RATING_TABLE_ROW.replace("PARAMETERNAME", parameterName)
    valRow = valRow.replace("PARAMETERDESCRIPTION", parameterDescription)

    valPairsSorted = sorted(valPairs, key=lambda x: x[1], reverse=True)

    valRow = valRow.replace("GOLD_PLAYER_NAME",   htmlLink(ezstatslib.escapePlayerName(valPairsSorted[0][0]) + ".html", \
                                                          linkText=ezstatslib.htmlBold("%s (%.2f)" % (valPairsSorted[0][0], valPairsSorted[0][1])), isBreak=False))
    valRow = valRow.replace("SILVER_PLAYER_NAME", htmlLink(ezstatslib.escapePlayerName(valPairsSorted[1][0]) + ".html", \
                                                           linkText=ezstatslib.htmlBold("%s (%.2f)" % (valPairsSorted[1][0], valPairsSorted[1][1])), isBreak=False))
    valRow = valRow.replace("BRONZE_PLAYER_NAME", htmlLink(ezstatslib.escapePlayerName(valPairsSorted[2][0]) + ".html", \
                                                           linkText=ezstatslib.htmlBold("%s (%.2f)" % (valPairsSorted[2][0], valPairsSorted[2][1])), isBreak=False))

    return valRow
    
# all players page
allPlayersPagePath = ezstatslib.REPORTS_FOLDER + ezstatslib.ALLPLAYERS_FILE_NAME
allPlayersPageText = ""

allPlayersPageText += "<div align=\"center\"><h1> == ALL PLAYERS == </h1></div>\n"

jsonPlayersByRank = sorted(jsonPlayers, key=lambda x: (x.rank()), reverse=True)

allPlayersDuelsHeaderRow=['', 'Matches', 'Rank', 'Frags', 'Deaths']
for pl in jsonPlayersByRank:
    allPlayersDuelsHeaderRow.append(pl.name);    

colAlign=[]
for i in xrange(len(allPlayersDuelsHeaderRow)):
    colAlign.append("center")

    htmlTable = HTML.Table(header_row=allPlayersDuelsHeaderRow, border="1", cellspacing="3", col_align=colAlign, id="duels_table",
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt; border-collapse: collapse; border: 4px solid black")

maxPlayedMatchesCount = 0
for pl in jsonPlayersByRank:
    if pl.matchesPlayed >= maxPlayedMatchesCount:
        maxPlayedMatchesCount = pl.matchesPlayed

    tableRow = HTML.TableRow(cells=[htmlLink(ezstatslib.escapePlayerName(pl.name) + ".html", linkText="%s" % (ezstatslib.htmlBold(pl.name))),
                                    ezstatslib.htmlBold(pl.matchesPlayed),
                                    HTML.TableCell(ezstatslib.htmlBold(pl.rank()), bgcolor=ezstatslib.BG_COLOR_GREEN if pl.rank() >= 0 else ezstatslib.BG_COLOR_RED),
                                    ezstatslib.htmlBold(pl.frags),
                                    ezstatslib.htmlBold(pl.deaths)])
        
    for i in xrange(5,len(allPlayersDuelsHeaderRow)):
        if allPlayersDuelsHeaderRow[i] in pl.duels.keys():
            if allPlayersDuelsHeaderRow[i] == pl.name:
                tableRow.cells.append( HTML.TableCell(str(pl.suicides), bgcolor=ezstatslib.BG_COLOR_GRAY, id=allPlayersDuelsHeaderRow[i]) )
            else:
                kills  = pl.duels[allPlayersDuelsHeaderRow[i]][0]
                deaths = pl.duels[allPlayersDuelsHeaderRow[i]][1]
        
                cellVal = "%s / %s" % (ezstatslib.htmlBold(kills)  if kills  > deaths else str(kills),
                                       ezstatslib.htmlBold(deaths) if deaths > kills  else str(deaths))
             
                cellColor = ""
                if kills == deaths:
                    cellColor = ezstatslib.BG_COLOR_LIGHT_GRAY
                elif kills > deaths:
                    cellColor = ezstatslib.BG_COLOR_GREEN
                else:
                    cellColor = ezstatslib.BG_COLOR_RED
                 
                tableRow.cells.append( HTML.TableCell(cellVal, bgcolor=cellColor, id=allPlayersDuelsHeaderRow[i]) )
                
        else:
            tableRow.cells.append( HTML.TableCell("", id=allPlayersDuelsHeaderRow[i]) )
                 
    htmlTable.rows.append(tableRow)  

allPlayersPageText += ezstatslib.HTML_SCRIPT_ALL_PLAYERS_DUELS_TABLE_DIV_TAG.replace("DUELS_TABLE", str(htmlTable))

allPlayersPageText += "</pre>\n"

allPlayersPageText += "<table>\n"
allPlayersPageText += getRankTableRow("frags", "Avg. Frags", jsonPlayers)
allPlayersPageText += getRankTableRow("ra", "Avg. Red Armors", jsonPlayers)
allPlayersPageText += getRankTableRow("ya", "Avg. Yellow Armors", jsonPlayers)
allPlayersPageText += getRankTableRow("ga", "Avg. Green Armors", jsonPlayers)
allPlayersPageText += getRankTableRow("mh", "Avg. Mega Health", jsonPlayers)
allPlayersPageText += "</table>\n"
    
        
allPlayersPage = open(allPlayersPagePath, "w")
allPlayersPageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
allPlayersPageHeaderStr = allPlayersPageHeaderStr.replace("PAGE_TITLE", "All players stats")
allPlayersPageHeaderStr = allPlayersPageHeaderStr.replace("SLIDER_STYLE", ezstatslib.HTML_SLIDER_STYLE_HORIZONTAL)
allPlayersPage.write(allPlayersPageHeaderStr)
allPlayersPage.write(ezstatslib.HTML_SCRIPT_ALLPLAYERS_DUELS_TABLE_FUNCTION)
allPlayersPage.write(ezstatslib.HTML_SCRIPT_ON_PAGE_LOAD_FUNCTION.replace("FUNCTIONS", "drawDuelsTable(3);\n"))
allPlayersPage.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)
allPlayersPage.write(allPlayersPageText)
allPlayersPage.write(ezstatslib.HTML_PRE_CLOSE_TAG)   
# add script section for folding
allPlayersPage.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)
allPlayersPage.write(ezstatslib.GET_ALLPLAYERS_DUELS_TABLE_SLIDER_SCRIPT(maxPlayedMatchesCount))
allPlayersPage.write(ezstatslib.HTML_FOOTER_NO_PRE)    
    
    
    
# all achievements page    
allAchievementsPagePath = ezstatslib.REPORTS_FOLDER + ezstatslib.ALLACHIEVEMENTS_FILE_NAME

allachievements = []
for key in ezstatslib.AchievementType.__dict__.keys():
    if key != "__dict__" and key != "__doc__" and key != "__module__"and key != "__weakref__":
        exec("allachievements.append(  ezstatslib.Achievement(ezstatslib.AchievementType.%s, \"\" ) )" % (key))

# sort by id
allachievements = sorted(allachievements, key=lambda x: (x.achtype), reverse=False)        

playersAchs = []
playersAchs.append([])

basicAchs = []
advanceAchs = []
rareAchs = []
ultrarareAchs = []
for ach in allachievements:
    playersAchs.append([])
    if ach.isImplemented():
        if ach.achlevel == ezstatslib.AchievementLevel.BASIC_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.BASIC_NEGATIVE:
            basicAchs.append(ach)
        if ach.achlevel == ezstatslib.AchievementLevel.ADVANCE_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.ADVANCE_NEGATIVE:
            advanceAchs.append(ach)
        if ach.achlevel == ezstatslib.AchievementLevel.RARE_POSITIVE or ach.achlevel == ezstatslib.AchievementLevel.RARE_NEGATIVE:
            rareAchs.append(ach)
        if ach.achlevel == ezstatslib.AchievementLevel.ULTRA_RARE:
            ultrarareAchs.append(ach)

for plJson in jsonPlayers:
    for achID in plJson.achievements.keys():
        playersAchs[achID].append([plJson, plJson.achievements[achID]])
        
# for i in xrange(len(playersAchs)):

    # sortedPlAchs = sorted(playersAchs[i], key=lambda x: (x[1], x[0].rank()), reverse=True)

    # sss = ""
    # for achPair in sortedPlAchs:
        # sss += "%s: %d, " % (achPair[0].name, achPair[1])
    # sss = sss[:-1]
    # print "id: %d, %s\n" % (i, sss)
    
allAchievementsPageText = ""

allAchievementsPageLinksText = ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_LINKS
allAchievementsPageLinksText = allAchievementsPageLinksText.replace("TOTALS_LINK", ezstatslib.TOTALS_FILE_NAME)
allAchievementsPageLinksText = allAchievementsPageLinksText.replace("ALLPLAYERS_LINK", ezstatslib.ALLPLAYERS_FILE_NAME)
allAchievementsPageLinksText = allAchievementsPageLinksText.replace("INDEX_LINK", ezstatslib.LOGS_INDEX_FILE_NAME)
allAchievementsPageText += allAchievementsPageLinksText

allAchievementsPageText += ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_HEADER
allAchievementsPageText += ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_WRAPPER_HEADER

sortedAchs = [basicAchs, advanceAchs, rareAchs, ultrarareAchs]
achsLevelsNames = ["Basic", "Advanced", "Rare", "UltraRare"]

allAchievementsPageFoldingScriptsStr = ""

for i in xrange(len(sortedAchs)):
    achsHeaderStr = ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_SECTION_HEADER
    achsHeaderStr = achsHeaderStr.replace("ACH_LEVEL_NAME", achsLevelsNames[i])
    achsHeaderStr = achsHeaderStr.replace("ACHS_COUNT", "%d" % (len(sortedAchs[i])))
    achsHeaderStr = achsHeaderStr.replace("ACH_DIV_ID", achsLevelsNames[i].lower())
    allAchievementsPageText += achsHeaderStr

    achFoldingScriptStr = ezstatslib.HTML_SCRIPT_ALLACHIEVEMENTS_PAGE_FOLDING
    achFoldingScriptStr = achFoldingScriptStr.replace("ACH_LEVEL_NAME", achsLevelsNames[i])
    achFoldingScriptStr = achFoldingScriptStr.replace("ACH_DIV_ID", achsLevelsNames[i].lower())
    allAchievementsPageFoldingScriptsStr += achFoldingScriptStr    
    
    for ach in sortedAchs[i]:
        sortedPlAchs = sorted(playersAchs[ach.achtype], key=lambda x: (x[1], x[0].rank()), reverse=True)
    
        if options.noLinks:
            achCardText = ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_CARD_BEGIN + "<br><br><br><br>" + ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_CARD_END
        else:
            achCardText = ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_CARD_BEGIN + ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_CARD_TABLE + ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_CARD_END
        achCardText = achCardText.replace("CARD_IMAGE", ezstatslib.Achievement.generateHtmlEx(ach, extraStyleParams = "margin-left: 14px;margin-top: 14px;"))
        
        shortNameStr = ach.shortName()
        shortNameWords = ach.shortName().split(" ")
        endBRCount = 2 - len(shortNameWords)
        if len(shortNameWords) <= 3:
            shortNameStr = ""
            for i in xrange(len(shortNameWords)):
                shortNameStr += shortNameWords[i]
                if len(shortNameWords[i]) > 3:
                    shortNameStr += "<br>"
                else:
                    shortNameStr += " "
                    endBRCount += 1

        for i in xrange(endBRCount):
            shortNameStr += "<br>"
                    
        achCardText = achCardText.replace("CARD_MAIN_TEXT", shortNameStr)
        
        achCardText = achCardText.replace("CARD_TEXT_COLOR", ezstatslib.Achievement.getBorderColor(ach.achlevel))
        
        if not options.noLinks:
            if len(sortedPlAchs) > 0:
                achCardText = achCardText.replace("GOLD_PLAYER_NAME", "%s [%d]" % (sortedPlAchs[0][0].name, sortedPlAchs[0][1]))
                achCardText = achCardText.replace("GOLD_PLAYER_VISIBILITY", "show")
                
                if len(sortedPlAchs) > 1:
                    achCardText = achCardText.replace("SILVER_PLAYER_NAME", "%s [%d]" % (sortedPlAchs[1][0].name, sortedPlAchs[1][1]))
                    achCardText = achCardText.replace("SILVER_PLAYER_VISIBILITY", "show")
                    
                    if len(sortedPlAchs) > 2:
                        achCardText = achCardText.replace("BRONZE_PLAYER_NAME", "%s [%d]" % (sortedPlAchs[2][0].name, sortedPlAchs[2][1]))
                        achCardText = achCardText.replace("BRONZE_PLAYER_VISIBILITY", "show")
                    else:
                        achCardText = achCardText.replace("BRONZE_PLAYER_VISIBILITY", "hidden")
                    
                else:
                    achCardText = achCardText.replace("SILVER_PLAYER_VISIBILITY", "hidden")
                    achCardText = achCardText.replace("BRONZE_PLAYER_VISIBILITY", "hidden")
            else:
                achCardText = achCardText.replace("GOLD_PLAYER_VISIBILITY", "hidden")
                achCardText = achCardText.replace("SILVER_PLAYER_VISIBILITY", "hidden")
                achCardText = achCardText.replace("BRONZE_PLAYER_VISIBILITY", "hidden")
            
        achCardText = achCardText.replace("CARD_DESCRIPTION", str(ach.description()) + "<hr>" + ach.conditionsDescription())
        achCardText = achCardText.replace("POSITIVE_VISIBLE", "none" if not ach.isPositive() else "")
        achCardText = achCardText.replace("NEGATIVE_VISIBLE", "none" if ach.isPositive() else "")
        
        if ach.gameType() == ezstatslib.AchievementGameType.BOTH:
            achCardText = achCardText.replace("SECTION_SPECIFIC_VISIBLE", "none")
        else:
            achCardText = achCardText.replace("SECTION_SPECIFIC_VISIBLE", "")
            achCardText = achCardText.replace("TEAM_SPECIFIC_VISIBLE", "none" if not ach.gameType() == ezstatslib.AchievementGameType.TEAM_SPECIFIC else "")
            achCardText = achCardText.replace("DM_SPECIFIC_VISIBLE", "none" if not ach.gameType() == ezstatslib.AchievementGameType.DEATHMATCH_SPECIFIC else "")
        
        allAchievementsPageText += achCardText
    
    allAchievementsPageText += ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_DIV_FOOTER
    allAchievementsPageText += "<br>\n"
    
allAchievementsPagePath = open(allAchievementsPagePath, "w")
allAchievemensPageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
allAchievemensPageHeaderStr += allAchievementsPageFoldingScriptsStr
allAchievemensPageHeaderStr += ezstatslib.HTML_SCRIPT_ALLACHIEVEMENTS_INIT_PAGE
allAchievemensPageHeaderStr += "</script>\n"
allAchievemensPageHeaderStr = allAchievemensPageHeaderStr.replace("PAGE_TITLE", "All achievements")
allAchievemensPageHeaderStr = allAchievemensPageHeaderStr.replace("SLIDER_STYLE", "")
allAchievementsPagePath.write(allAchievemensPageHeaderStr)
allAchievementsPagePath.write(ezstatslib.HTML_ALLACHIEVEMENTS_PAGE_STYLE)
allAchievementsPagePath.write("</head>\n<body onload=\"initPage();\">\n")

allAchievementsPagePath.write(allAchievementsPageText)

# add script section for folding
allAchievementsPagePath.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)
allAchievementsPagePath.write(ezstatslib.HTML_FOOTER_NO_PRE)        