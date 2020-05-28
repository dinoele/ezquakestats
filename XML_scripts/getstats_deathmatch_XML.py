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

stat_conf.read_config()

sys.path.append("../")

import ezstatslib
from ezstatslib import Team,Player
from ezstatslib import enum,checkNew,htmlLink
from ezstatslib import NEW_GIF_TAG as newGifTag
from ezstatslib import PickMapItemElement,DamageElement,DeathElement

import HTML

import json

from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE, ST_MTIME

import xml.etree.ElementTree as ET
#tree = ET.parse('country_data.xml')
#root = tree.getroot()

ezstatslib.REPORTS_FOLDER = stat_conf.reports_dir
ezstatslib.LOGS_INDEX_FILE_NAME = "index.html"

def fillH2H(who,whom,minute):
    try:
        for elem in headToHead[who]:
            if elem[0] == whom:
                elem[1] += 1
                elem[2][minute] += 1
    except Exception, ex:
        ezstatslib.logError("fillH2H: who=%s, whom=%s, minute=%d, ex=%s\n" % (who, whom, minute, ex))

def fillH2HDamage(who,whom,value,minute):
    try:
        for elem in headToHeadDamage[who]:
            if elem[0] == whom:
                elem[1] += value
                elem[2][minute] += value
    except Exception, ex:
        ezstatslib.logError("fillH2HDamage: who=%s, whom=%s, minute=%d, ex=%s\n" % (who, whom, minute, ex))

def clearZeroPlayer(pl):
    # TODO remove from headToHead
    
    # clear battle progress
    for mpline in matchProgress: # mpline: [[pl1_name,pl1_frags],[pl2_name,pl2_frags],..]
        for mp in mpline:        # mp:     [pl1_name,pl1_frags]
            if pl.name == mp[0]:
                mpline.remove(mp)       # TODO REMOVE
                                        # (n for n in n_list if n !=3)  # ifilter
                                        # https://docs.python.org/2.7/library/stdtypes.html#mutable-sequence-types
        

usageString = "" 
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("-f",   action="store",       dest="inputFile",      type="str",  metavar="LOG_FILE", help="")
parser.add_option("--fxml",   action="store",       dest="inputFileXML",      type="str",  metavar="LOG_FILE_XML", help="")
parser.add_option("--fjson",   action="store",       dest="inputFileJSON",      type="str",  metavar="LOG_FILE_JSON", help="")
parser.add_option("--league", action="store",   dest="leagueName",     type="str",  metavar="LEAGUE",   help="")
parser.add_option("--scripts", action="store_false",   dest="withScripts", default=True,   help="")
parser.add_option("--net-copy", action="store_true",   dest="netCopy", default=False,   help="")

# TODO add -q option: without output at all

(options, restargs) = parser.parse_args()

if not options.leagueName:
    options.leagueName = "";

# check rest arguments
if len(restargs) != 0:
    parser.error("incorrect parameters count(%d)" % (len(restargs)))
    exit(0)

#f = open(options.inputFile, "r")
#f = fileinput.input(options.inputFile)

if options.inputFile:
    f = fileinput.input(options.inputFile)
else:
    f = sys.stdin

matchdate = ""
mapName = ""
matchlog = [[]]
isStart = False
isEnd = False

allplayers = []
disconnectedplayers = []
dropedplayers = []
spectators = []

readLinesNum = 0

newLogFormat = False # if at least one LOG_TIMESTAMP_DELIMITER in logs

xmlPlayersStr = []
xmlPlayers = []

elements = []
damageElements = []
deathElements = []
pickmapitemElements = []

elementsByTime = [] # [timestamp, [elemen1, elemen2, .. , elementN]]
elementsCloseByTime = [] # [[timestamp1,..,timestampN], [elemen1, elemen2, .. , elementN]]  delta(timestamp1,..,timestampN) < 0.2 sec


sourceXML = open(options.inputFileXML)

try:
    tree = ET.parse(sourceXML)
    root = tree.getroot()
except:
    # try to cut XML - find the last "<?xml version="1.0" encoding="ISO-8859-1"?>" and take only text after
    xmlLine = "<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>"
    
    sourceXML = open(options.inputFileXML)
    xmlLines = sourceXML.readlines()
    
    i = len(xmlLines)-1
    isOver = False
    while not isOver:
        if xmlLine in xmlLines[i]:
            isOver = True            
            break
        i -= 1
    
    xmlText = ""
    for j in xrange(i,len(xmlLines)):
        xmlText += xmlLines[j]
    
    root = ET.fromstring(xmlText)

i = 0
j = 0
k = 0
damageCnt = 0
deathCnt  = 0
pickmapitemCnt = 0
currentTS = -1
currentTS2 = -1
for child in root:
    #print child.tag, child.attrib   

    if child.tag == "match_info":
        for ev in child:
            if ev.tag == "map":
                mapName = "[" + ev.text + "]"
            if ev.tag == "timestamp":
                if "Russia" in ev.text:
                    matchdate = ev.text.split(" Russia")[0]
                else:
                    try:
                        matchdate = ev.text.split(" Eur")[0]
                        dt = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S')
                    except:
                        datesplit = ev.text.split(" ")
                        matchdate = datesplit[0] + " " + datesplit[1]

                        print matchdate

                        dt = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S')

                    dtcorrected = dt + timedelta(hours=3)
                    matchdate = dtcorrected.strftime('%Y-%m-%d %H:%M:%S') 
            if ev.tag == "mode":
                gameMode = ev.text
        if gameMode != "":
            mapName = "%s_%s" % (gameMode, mapName)

    if child.tag == "events":
        for ev in child:
#            print ev.tag, ev.attrib
    
            for evtype in ev:
#                print evtype.tag, evtype.attrib

                if evtype.tag == "damage":
                    damageCnt += 1
                    elem = DamageElement(evtype)

#                    print "IsSelf: %s" % (elem.isSelfDamage)

                    elements.append(elem)
                    damageElements.append(elem)
                    if elem.target not in xmlPlayersStr:
                        xmlPlayersStr.append(elem.target)                        
                        pl = Player( "", elem.target, 0, 0, 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
                        xmlPlayers.append(pl)

                    if elem.attacker not in xmlPlayersStr:
                        xmlPlayersStr.append(elem.attacker)
                        pl = Player( "", elem.attacker, 0, 0, 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
                        xmlPlayers.append(pl)

                if evtype.tag == "death":
                    deathCnt += 1
                    elem = DeathElement(evtype)
                    elements.append(elem)
                    deathElements.append(elem)

                if evtype.tag == "pick_mapitem":
                    pickmapitemCnt += 1
                    elem = PickMapItemElement(evtype)
                    elements.append(elem)
                    pickmapitemElements.append(elem)
                    
                if evtype.tag == "drop_backpack" or evtype.tag == "pick_backpack":
                    continue

                if currentTS == -1 or currentTS != elem.time:
                    currentTS = elem.time                    
                    elementsByTime.append([currentTS, [elem]])
                else:                  
                    elementsByTime[len(elementsByTime)-1][1].append(elem)
                    
                if evtype.tag == "death":
                    if currentTS2 == -1 or elem.time - currentTS2 >= 0.2:
                        currentTS2 = elem.time                    
                        elementsCloseByTime.append([[currentTS2], [elem]])
                    else:
                        elementsCloseByTime[len(elementsCloseByTime)-1][0].append(elem.time)
                        elementsCloseByTime[len(elementsCloseByTime)-1][1].append(elem)                    

#                for evtags in evtype:
#                    print evtags.tag, evtags.attrib, evtags.text


                k+=1


            j+=1

    
    i+=1

sourceXML.close()

lastTimeStamp = elements[len(elements)-1].time
minutesPlayedXML = int((lastTimeStamp - 2)/60) + 1  # 2 sec is correction for events in the match end with timestamp more than minPlayed*60

for pl in xmlPlayers:
    pl.initPowerUpsByMinutesXML(minutesPlayedXML)

print i
print j 
print k 

print "Elements cnt =", len(elements)
print "Damage cnt =", damageCnt
print "Death cnt =", deathCnt
print "PickMapItems cnt =", pickmapitemCnt
print "XML players:", xmlPlayersStr
print "minutesPlayedXML:", minutesPlayedXML


for elem in damageElements:
    if elem.isSelfDamage:
        for pl in xmlPlayers:
            if pl.name == elem.attacker:
                if elem.armor == 1:
                    pl.damageSelfArmor += elem.value
                else:
                    pl.damageSelf += elem.value
    else:

        print "%f  %s -> %s  %d \"%d\" splash: %d" % (elem.time, elem.attacker, elem.target, elem.armor, elem.value, elem.splash)

        for pl in xmlPlayers:
            if pl.name == elem.attacker and elem.type != "tele1" and elem.type != "trigger":
                if elem.armor == 1:
                    pl.damageGvnArmor += elem.value
                else:
                    pl.damageGvn += elem.value
            if pl.name == elem.target and elem.type != "tele1" and elem.type != "trigger": 
                if elem.armor == 1:
                    pl.damageTknArmor += elem.value
                else:
                    pl.damageTkn += elem.value

for pl in xmlPlayers:
    print "Player \"%s\":   gvn:  %d, tkn:  %d, self:  %d" % (pl.name, pl.damageGvn, pl.damageTkn, pl.damageSelf)
    print "                 gvnA: %d, tknA: %d, selfA: %d" % (pl.damageGvnArmor, pl.damageTknArmor, pl.damageSelfArmor)
    print "                 gvnS: %d, tknS: %d, selfS: %d" % (pl.damageGvn+pl.damageGvnArmor, pl.damageTkn+pl.damageTknArmor, pl.damageSelf+pl.damageSelfArmor)
    print "---------------------------------------------"



for elem in deathElements:
    if elem.isSuicide:
        for pl in xmlPlayers:
            if pl.name == elem.attacker:
                pl.suicidesXML += 1
                pl.lifetimeXML += elem.lifetime
                if pl.firstDeathXML == "":
                    pl.firstDeathXML = elem
                pl.lastDeathXML = elem
    else:

        #print "%f  %s -> %s  \"%s\"  %f" % (elem.time, elem.attacker, elem.target, elem.type, elem.lifetime)
        #print "%f" % (elem.lifetime)

        for pl in xmlPlayers:
            if pl.name == elem.attacker:
                pl.killsXML += 1
                if elem.isSpawnFrag:
                    pl.spawnFragsXML += 1
            if pl.name == elem.target:
                pl.deathsXML += 1
                pl.lifetimeXML += elem.lifetime
                if pl.firstDeathXML == "":
                    pl.firstDeathXML = elem
                pl.lastDeathXML = elem



for elem in pickmapitemElements:
    #print "%f  %s -> %s  \"%s\"  %f" % (elem.time, elem.attacker, elem.target, elem.type, elem.lifetime)
    #print "%f" % (elem.lifetime)

    for pl in xmlPlayers:
        if pl.name == elem.player:
            if elem.isArmor:
                if elem.armorType == ezstatslib.PowerUpType.RA:
                    pl.raXML += 1
                    pl.incraXML(int(elem.time))
                if elem.armorType == ezstatslib.PowerUpType.YA:
                    pl.yaXML += 1
                    pl.incyaXML(int(elem.time))
                if elem.armorType == ezstatslib.PowerUpType.GA:
                    pl.gaXML += 1
                    pl.incgaXML(int(elem.time))

            if elem.isMH:
                pl.mhXML += 1
                pl.incmhXML(int(elem.time))

for pl in xmlPlayers:
    print "Player \"%s\": kills:  %d, deaths:  %d, suicides:  %d, spawns:  %d, ga: %d, ya: %d, ra: %d, mh: %d" % (pl.name, pl.killsXML, pl.deathsXML, pl.suicidesXML, pl.spawnFragsXML, pl.gaXML, pl.yaXML, pl.raXML, pl.mhXML)
    print "    ga: %s" % (pl.gaByMinutesXML)
    print "    ya: %s" % (pl.yaByMinutesXML)
    print "    ra: %s" % (pl.raByMinutesXML)
    print "    mh: %s" % (pl.mhByMinutesXML)


timelimit = -1
duration = -1
isOverTime = False
overtimeMinutes = -1
rlAttacksByPlayers = {}
if not options.inputFileJSON is None and options.inputFileJSON != "":
    with open(options.inputFileJSON, 'r') as fjson:
        jsonStrRead = json.load(fjson)
        timelimit = int(jsonStrRead["tl"])
        duration = int(jsonStrRead["duration"])
        
        for pl in jsonStrRead["players"]:
            rlAttacksByPlayers[pl["name"]] = pl["weapons"]["rl"]["acc"]["attacks"];

    isOverTime = minutesPlayedXML != timelimit;
    overtimeMinutes = minutesPlayedXML - timelimit
    
    
# line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)


# while not ezstatslib.isMatchStart(line):
    # if ".mvd" in line:
        # mapName = line.split("]")[0]
        # mapName += "]"
    
    # if "telefrag" in line and not "teammate" in line: # telefrags before match start
        # matchlog[0].append(line)

    # if "matchdate" in line:
        # if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO TIME
            # matchStartStamp = int( line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[0] )
            # line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
            
        # matchdate = line.split("matchdate: ")[1].split("\n")[0].split(" Russia")[0]

    # line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

# matchMinutesCnt = 1
# line = f.readline()
# readLinesNum += 1
# while not ezstatslib.isMatchEnd(line):
    # if line != "":
        # matchlog[ matchMinutesCnt - 1 ].append(line)
    # line = f.readline()
    # readLinesNum += 1
    # line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)
    
    # if not newLogFormat and ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO TIME
        # newLogFormat = True
    
    # rea[rbf] left the game with 23 frags
    # if "left the game" in line:
        # lineStriped = line
        # lineStamp = -1
        # if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO TIME
            # lineStriped    = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
            # lineStamp = int( line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[0] )
        
        # plname = lineStriped.split(" ")[0];
        # pl = Player( "", plname, 0, 0, 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
        # pl.isDropped = True
        # if lineStamp != -1:
            # pl.disconnectTime = lineStamp - matchStartStamp
        # dropedplayers.append(pl);  # TODO record number of frags for final output

    # Majority votes for mapchange
    # if "Majority votes for mapchange" in line:
        # print "Majority votes for mapchange"
        # ezstatslib.logError("Majority votes for mapchange\n")
        # exit(1)
        
    # Match stopped by majority vote
    # if "Match stopped by majority vote" in line:
        # print "Match stopped by majority vote"
        # ezstatslib.logError("Match stopped by majority vote\n")
        # exit(1)
        
    # if "remaining" in line or "overtime" in line:  # [9] minutes remaining
        # matchMinutesCnt += 1
        # matchlog.append([])

# while not "Player statistics" in line:
   # line = f.readline()
   # readLinesNum += 1
    # line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)
    

# line = f.readline()  # (=================================)
# line = f.readline()  # Frags (rank) . efficiency
# line = f.readline()
# readLinesNum += 3

# while not "top scorers" in line and not "Running" in line:
    # if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO TIME
        # line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
    
    # playerName = line.split(' ')[1].split(':')[0]  # zrkn:

    # if playerName[0] == "_":
        # playerName = playerName[1:]
        # disconnectedplayers.append(playerName)


    # line = f.readline()    # "  45 (2) 51.1%"
    # readLinesNum += 1

    # stats = line.split(' ')

    # pl = Player( "", playerName, int(stats[2]), int( stats[3].split('(')[1].split(')')[0]), 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
    # pl.initPowerUpsByMinutes(matchMinutesCnt)
            
    # line = f.readline() # Wp: rl52.1% sg12.2%
    # readLinesNum += 1

    # pl.parseWeapons(line)

    # line = f.readline() # RL skill: ad:82.2 dh:25
    # readLinesNum += 1
    # pl.rlskill_ad = float(line.split("ad:")[1].split(" ")[0])
    # pl.rlskill_dh = float(line.split("dh:")[1].split(" ")[0])

    # line = f.readline() # Armr&mhs: ga:0 ya:4 ra:1 mh:1
    # readLinesNum += 1
    
    # if not "Armr&mhs" in line:
        # line = f.readline()
        # readLinesNum += 1
    
    # pl.ga = int(line.split("ga:")[1].split(" ")[0])
    # pl.ya = int(line.split("ya:")[1].split(" ")[0])
    # pl.ra = int(line.split("ra:")[1].split(" ")[0])
    # pl.mh = int(line.split("mh:")[1].split(" ")[0])

    # line = f.readline() # Damage: Tkn:4279 Gvn:4217 Tm:284
    # readLinesNum += 1
    # pl.tkn = int(line.split("Tkn:")[1].split(" ")[0])
    # pl.gvn = int(line.split("Gvn:")[1].split(" ")[0])
    # pl.tm  = int(line.split("Tm:")[1].split(" ")[0])

    # line = f.readline() # Streaks: Frags:3 QuadRun:0
    # readLinesNum += 1
    
    # if "Streaks" in line:
        # pl.streaks = int(line.split("Streaks: Frags:")[1].split(" ")[0])

    # line = f.readline() # SpawnFrags: 4
    # readLinesNum += 1
    
    # if "OverTime" in line:
        # line = f.readline()
        # readLinesNum += 1
    
    # line = f.readline() # SpawnFrags: 4
    # readLinesNum += 1

    # pl.spawnfrags = int(line.split("SpawnFrags: ")[1].split(" ")[0])

    # allplayers.append(pl)

    # while not "#" in line:
        # if "top scorers" in line or "Running" in line:
            # break;
        # else:
            # line = f.readline()
            # readLinesNum += 1
            # line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

# check droped players and add them to allplayers collection
# for pl1 in dropedplayers:
    # exist = false
    # for pl2 in allplayers: 
        # if pl1.name == pl2.name:
            # exist = true
    # if not exist:
        # pl1.initpowerupsbyminutes(matchminutescnt)
        # allplayers.append(pl1);



# NEWPLAYERS
for pl in xmlPlayers:
    if pl.name == "world":
        continue
    pl.initPowerUpsByMinutes(minutesPlayedXML)
    #pl.parseWeapons(line)
    #pl.rlskill_ad = float(line.split("ad:")[1].split(" ")[0])
    #pl.rlskill_dh = float(line.split("dh:")[1].split(" ")[0])
    pl.ga = pl.gaXML  #int(line.split("ga:")[1].split(" ")[0])
    pl.ya = pl.yaXML  #int(line.split("ya:")[1].split(" ")[0])
    pl.ra = pl.raXML  #int(line.split("ra:")[1].split(" ")[0])
    pl.mh = pl.mhXML  #int(line.split("mh:")[1].split(" ")[0])
    pl.tkn = pl.damageTknArmor + pl.damageTkn # int(line.split("Tkn:")[1].split(" ")[0])
    pl.gvn = pl.damageGvnArmor + pl.damageGvn # int(line.split("Gvn:")[1].split(" ")[0])
    #pl.tm  = int(line.split("Tm:")[1].split(" ")[0])
    #pl.streaks = int(line.split("Streaks: Frags:")[1].split(" ")[0])
    pl.spawnfrags = pl.spawnFragsXML # int(line.split("SpawnFrags: ")[1].split(" ")[0])
    if len(rlAttacksByPlayers) != 0:
        try:
            pl.rl_attacks = rlAttacksByPlayers[pl.name]
        except:
            pass
    allplayers.append(pl)


# map name
#while not "top scorers" in line:
#    line = f.readline()

# if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO TIME
    # line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]

if mapName == "":
    mapName = line.split(" ")[0]

f.close()

# check that there are more than 1 players
if len(allplayers) == 0:
    #print "No players at all"
    ezstatslib.logError("No players at all\n")
    exit(1)

if len(allplayers) == 1:
    #print "Only one player:", allplayers[0].name
    ezstatslib.logError("Only one player: %s\n" % (allplayers[0].name))
    exit(1)

matchMinutesCnt = minutesPlayedXML

# head-to-head stats init
# TODO make separate function
headToHead = {}
for pl1 in allplayers:
    headToHead[pl1.name] = []
    for pl2 in allplayers:
        headToHead[pl1.name].append([pl2.name,0,[0 for i in xrange(matchMinutesCnt+1)]])

# head-to-headDamage stats init
# TODO make separate function
headToHeadDamage = {}
for pl1 in allplayers:
    headToHeadDamage[pl1.name] = []
    for pl2 in allplayers:
        headToHeadDamage[pl1.name].append([pl2.name,0,[0 for i in xrange(matchMinutesCnt+1)]])

matchProgress = []  # [[[pl1_name,pl1_frags],[pl2_name,pl2_frags],..],[[pl1_name,pl1_frags],[pl2_name,pl2_frags],..]]
matchProgressDict = []
matchProgressDictEx = []
matchProgressDictEx2 = []
currentMinute = 1
currentMatchTime = 0
battleProgressExtendedNextPoint = (int)(60 / ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)

for element in elements:
    
    #if isinstance(element, PickMapItemElement) and (not element.isArmor or not element.isMH):
    #    continue
    
    currentMatchTime = lineStamp = element.time

    if currentMatchTime > currentMinute*60 and currentMinute == minutesPlayedXML:
        currentMatchTime -= 2  # 2 sec is correction for events in the match end with timestamp more than minPlayed*60, used in minutesPlayedXML calculation

    allplayersByFrags = sorted(allplayers, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
    # battle progress    
    if currentMatchTime > currentMinute*60:
        currentMinute += 1                    
        progressLine = []
        progressLineDict = {}
        for pl in allplayersByFrags:
            progressLine.append([pl.name, pl.frags()]);
            progressLineDict[pl.name] = [pl.frags(), pl.calcDelta()];
        matchProgress.append(progressLine)
        matchProgressDict.append(progressLineDict)
        matchProgressDictEx.append(progressLineDict)
        battleProgressExtendedNextPoint += (int)(60 / ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
    else:
        if currentMatchTime > battleProgressExtendedNextPoint:
            battleProgressExtendedNextPoint += (int)(60 / ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
            progressLineDict = {}
            for pl in allplayersByFrags:
                progressLineDict[pl.name] = [pl.frags(), pl.calcDelta()];
            matchProgressDictEx.append(progressLineDict)
        
        
    if len(matchProgressDictEx2) == 0 or matchProgressDictEx2[len(matchProgressDictEx2)-1][allplayers[0].name][0] != currentMatchTime:
        progressLineDict = {}
        for pl in allplayersByFrags:
            progressLineDict[pl.name] = [currentMatchTime, pl.frags(), pl.calcDelta()];
        matchProgressDictEx2.append(progressLineDict)
    
    # overtime check
    if isOverTime and currentMinute == minutesPlayedXML - overtimeMinutes:
        if len(allplayersByFrags) >= 2:
            if allplayersByFrags[0].frags() == allplayersByFrags[1].frags():
                allplayersByFrags[0].overtime_frags = allplayersByFrags[0].frags()
                allplayersByFrags[1].overtime_frags = allplayersByFrags[1].frags()
            else:
                ezstatslib.logError("ERROR: overtime calculation: currentMinute: %d, minutesPlayedXML: %d, allplayersByFrags[0].frags(): %d, allplayersByFrags[1].frags(): %d" % \
                 (currentMinute, minutesPlayedXML, allplayersByFrags[0].frags(), allplayersByFrags[1].frags()))

    # skip Damage and Death elements with target=None (door which is opened by the shot)
    if (isinstance(element, DeathElement) or isinstance(element, DamageElement)) and element.target is None:
        continue
                 
    # telefrag
    if isinstance(element, DeathElement) and element.type == "tele1":
        print "EEE: attacker: %s, target: %s" % (element.attacker, element.target)
        who = element.attacker
        whom = element.target
        for pl in allplayers:
            if who != "" and pl.name == who:
                pl.incKill(currentMatchTime, who, whom)
                pl.tele_kills += 1
                isFoundWho = True
    
            if pl.name == whom:
                pl.incDeath(currentMatchTime, who, whom)
                pl.tele_deaths += 1
                isFoundWhom = True
    
        if who != "":
            fillH2H(who,whom,currentMinute)
    
        if not isFoundWho or not isFoundWhom:
            #print "ERROR: count telefrag", who, "-", whom, ":", logline
            ezstatslib.logError("ERROR: count telefrag %s-%s: %s\n" % (who, whom, logline))
            exit(0)
    
        continue
    
    # suicide    
    if isinstance(element, DeathElement) and (element.isSuicide or element.attacker == "world"):
        if element.attacker == "world":
            checkname = element.target
        else:
            checkname = element.attacker
        isFound = False
        for pl in allplayers:
            if pl.name == checkname:
                pl.incSuicides(currentMatchTime)
                fillH2H(checkname,checkname,currentMinute)
                isFound = True
                break;
        if not isFound:
            #print "ERROR: count suicides"
            ezstatslib.logError("ERROR: count suicides\n")
            exit(0)    
        continue    
        
    # power ups
    if isinstance(element, PickMapItemElement) and (element.isArmor or element.isHealth):
        checkname = element.player
        if element.isMH:
            pwr = "mh"
        if element.isArmor:
            if element.armorType == ezstatslib.PowerUpType.RA:
                pwr = "ra"
            if element.armorType == ezstatslib.PowerUpType.YA:
                pwr = "ya"
            if element.armorType == ezstatslib.PowerUpType.GA:
                pwr = "ga"
                               
        isFound = False
        for pl in allplayers:
            if pl.name == checkname:                    
                if element.isArmor or element.isMH:
                    exec("pl.inc%s(%d,%d)" % (pwr, currentMinute, currentMatchTime))
                isFound = True
                pl.addLifetimeItem(element)
                break;
        if not isFound:
            ezstatslib.logError("ERROR: powerupDetection: no playername %s\n" % (checkname))
            exit(0)
    
        continue            
    
    # commom death
    if isinstance(element, DeathElement):    
        who = element.attacker
        whom = element.target
        weap = element.type
    
        if not weap in ezstatslib.possibleWeapons:
            #print "ERROR: unknown weapon:", weap
            ezstatslib.logError("ERROR: unknown weapon: %s\n" % (weap))
            if weap == "lg_beam" or weap == "lg_dis":
                weap = "lg"
            elif weap == "stomp" or weap == "squish" or weap == "lava":
                weap = "other"  # TODO fall on the player  # TODO ULTRA RARE ACH
            else:
                exit(0)
    
        isFoundWho = False
        isFoundWhom = False
        for pl in allplayers:
            if pl.name == who:
                pl.incKill(currentMatchTime, who, whom);
                exec("pl.%s_kills += 1" % (weap))
                isFoundWho = True
                
            if pl.name == whom:
                pl.incDeath(currentMatchTime, who, whom);
                exec("pl.%s_deaths += 1" % (weap))
                isFoundWhom = True
            
        fillH2H(who,whom,currentMinute)
    
        if not isFoundWho or not isFoundWhom:
            ezstatslib.logError("ERROR: count common %s-%s\n" % (who, whom))


    # damage
    if isinstance(element, DamageElement):
        who = element.attacker
        whom = element.target
        weap = element.type

        if weap == "trigger" or weap == "slime" or weap == "lg_dis":  # TODO
            continue

        if element.type == "tele1":
            value = 0;
            weap = "tele"
        else:
            value = element.value
        
        if not weap in ezstatslib.possibleWeapons:
            print "ERROR: unknown weapon:", weap
            ezstatslib.logError("ERROR: unknown weapon: %s\n" % (weap))
            if weap == "lg_beam":
                weap = "lg"
            elif weap == "fall" or weap == "squish" or weap == "lava":
                who = whom
                weap = "other"  # TODO world -> whom
            elif weap == "stomp":
                weap = "other"  # TODO fall on the player
            else:
                exit(0)

        isFoundWho = False
        isFoundWhom = False
        if who == whom:
            for pl in allplayers:
                if pl.name == who:
                    exec("pl.%s_damage_self += %d" % (weap, value))
                    pl.addLifetimeItem(element)
        else:
            for pl in allplayers:
                if pl.name == who:
                    exec("pl.%s_damage_gvn += %d" % (weap, value))
                    exec("pl.%s_damage_gvn_cnt += 1" % (weap))
                    if weap == "rl":
                        if len(pl.rl_damages_gvn) > 0 and pl.rl_damages_gvn[len(pl.rl_damages_gvn)-1][2] == 1: # armor 
                            if pl.rl_damages_gvn[len(pl.rl_damages_gvn)-1][1] == whom: # the same whom
                                pl.rl_damages_gvn[len(pl.rl_damages_gvn)-1][0] += value
                                pl.rl_damages_gvn[len(pl.rl_damages_gvn)-1][2] = 0
                            else:
                                pl.rl_damages_gvn.append([value,whom,element.armor]);
                        else:
                            pl.rl_damages_gvn.append([value,whom,element.armor]);
                    isFoundWho = True
                
                if pl.name == whom:
                    exec("pl.%s_damage_tkn += %d" % (weap, value))
                    exec("pl.%s_damage_tkn_cnt += 1" % (weap))
                    isFoundWhom = True
                    
                    pl.addLifetimeItem(element)
            
        fillH2HDamage(who,whom,value,currentMinute)
    
        if who != whom and (not isFoundWho or not isFoundWhom):
            ezstatslib.logError("ERROR: damage calc %s-%s\n" % (who, whom))

        continue

# all log lines are processed

tmpComboStr = ""
for i in xrange(len(elementsByTime)):
    deaths = 0
    for j in xrange(len(elementsByTime[i][1])):
        if isinstance(elementsByTime[i][1][j], DeathElement):
            deaths += 1

    tt = elementsByTime[i][0]
    if deaths >= 2 and deaths < 3:       
        attacker1 = ""
        attacker2 = ""
        target1 = ""
        target2 = ""
        wp1 = ""
        wp2 = ""
        for j in xrange(len(elementsByTime[i][1])):
            if isinstance(elementsByTime[i][1][j], DeathElement):
                if attacker1 == "" and target1 == "":
                    attacker1 = elementsByTime[i][1][j].attacker
                    target1 = elementsByTime[i][1][j].target
                    wp1 = elementsByTime[i][1][j].type
                else:
                    attacker2 = elementsByTime[i][1][j].attacker
                    target2 = elementsByTime[i][1][j].target
                    wp2 = elementsByTime[i][1][j].type

        isSuicide1 = attacker1 == target1
        isSuicide2 = attacker2 == target2
        isAttackerTheSame = attacker1 == attacker2

        if isAttackerTheSame:
            if isSuicide1 or isSuicide2:                
                if isSuicide1:
                    attackPl = attacker1
                    targetPl = target2
                else: # isSuicide2
                    attackPl = attacker2
                    targetPl = target1

                # attackTeam = ""
                # targetTeam = ""
                # for pl in allplayers:
                    # if pl.name == attackPl:
                        # attackTeam = pl.teamname
                    # if pl.name == targetPl:
                        # targetTeam = pl.teamname

                # if attackTeam == targetTeam:
                    # # suicide + teamkill
                    # ezstatslib.logError("OLOLO: %f suicide + teamkill(%s) by %s\n" % (tt, target2 if isSuicide1 else target1, attackPl))
                    # tmpComboStr += ("OLOLO: %f suicide + teamkill(%s) by %s\n" % (tt, target2 if isSuicide1 else target1, attackPl))
                # else:
                    # # suicide + kill
                    # ezstatslib.logError("OLOLO: %f suicide + kill(%s) by %s\n" % (tt, target2 if isSuicide1 else target1, attackPl))
                    # tmpComboStr += ("OLOLO: %f suicide + kill(%s) by %s\n" % (tt, target2 if isSuicide1 else target1, attackPl))

                for pl in allplayers:
                    if pl.name == attackPl:
                        pl.suicide_kills.append([tt,target2 if isSuicide1 else target1,wp2 if isSuicide1 else wp1])
                    
                ll = "OLOLO: %f suicide + kill(%s) by %s [wps: %s + %s]\n" % (tt, target2 if isSuicide1 else target1, attackPl, wp1 if isSuicide1 else wp2, wp2 if isSuicide1 else wp1)
                ezstatslib.logError(ll)
                tmpComboStr += ll

            else: # non suicide
                # attackTeam = ""
                # targetTeam1 = ""
                # targetTeam2 = ""
                # for pl in allplayers:
                    # if pl.name == target1:
                        # targetTeam1 = pl.teamname
                    # if pl.name == target2:
                        # targetTeam2 = pl.teamname
                    # if pl.name == attacker1:
                        # attackTeam = pl.teamname

                # if attackTeam != targetTeam1 and attackTeam != targetTeam2:
                    # # kill + kill
                    # ezstatslib.logError("OLOLO: %f kill(%s) + kill(%s) by %s\n" % (tt, target1, target2, attacker1))
                    # tmpComboStr += ("OLOLO: %f kill(%s) + kill(%s) by %s\n" % (tt, target1, target2, attacker1))
                # elif attackTeam == targetTeam1 and attackTeam == targetTeam2:
                    # # teamkill + teamkill
                    # ezstatslib.logError("OLOLO: %f teamkill(%s) + teamkill(%s) by %s\n" % (tt, target1, target2, attacker1))
                    # tmpComboStr += ("OLOLO: %f teamkill(%s) + teamkill(%s) by %s\n" % (tt, target1, target2, attacker1))
                # else:
                    # # kill + teamkill
                    # ezstatslib.logError("OLOLO: %f kill(%s) + teamkill(%s) by %s\n" % (tt, target2 if attackTeam != targetTeam2 else target1, target2 if attackTeam == targetTeam2 else target1, attacker1))
                    # tmpComboStr += ("OLOLO: %f kill(%s) + teamkill(%s) by %s\n" % (tt, target2 if attackTeam != targetTeam2 else target1, target2 if attackTeam == targetTeam2 else target1, attacker1))

                for pl in allplayers:
                    if pl.name == attacker1:
                        pl.double_kills.append([target1,target2,wp1])
                    
                ll = "OLOLO: %f kill(%s) + kill(%s) by %s [wps: %s + %s]\n" % (tt, target1, target2, attacker1, wp1, wp2)
                ezstatslib.logError(ll)
                tmpComboStr += ll

        else:
            # TODO mutual kill
            for pl in allplayers:
                if pl.name == attacker1:
                    pl.mutual_kills.append([tt,target1,wp1,wp2])
                if pl.name == attacker2:
                    pl.mutual_kills.append([tt,target2,wp2,wp1])            
            
            ll = "OLOLO: %f mutual kill: (attacker1(%s), target1(%s), wp1(%s)); (attacker2(%s), target2(%s), wp2(%s)\n" % (tt, attacker1, target1, wp1, attacker2, target2, wp2)
            ezstatslib.logError(ll)
            tmpComboStr += ll

    elif deaths >= 3:
        # TODO
        if deaths == 3:
            attacker = ""            
            isAttackerTheSame = True
            targets = []
            wps = []
            for j in xrange(len(elementsByTime[i][1])):
                if isinstance(elementsByTime[i][1][j], DeathElement):
                    targets.append(elementsByTime[i][1][j].target)
                    wps.append(elementsByTime[i][1][j].type)
                    if attacker == "":
                        attacker = elementsByTime[i][1][j].attacker
                    else:
                        if attacker != elementsByTime[i][1][j].attacker:
                            isAttackerTheSame = False

            if isAttackerTheSame:
                for pl in allplayers:
                    if pl.name == attacker:
                        pl.triple_kills.append([tt,targets[0],targets[1],targets[2],wps[0]])
        
        resStr = ""
        deathNum = 1
        for j in xrange(len(elementsByTime[i][1])):
            if isinstance(elementsByTime[i][1][j], DeathElement):
                resStr += "(attacker%d(%s), target%d(%s), wp%s(%s)); " % (deathNum, elementsByTime[i][1][j].attacker, deathNum, elementsByTime[i][1][j].target, deathNum, elementsByTime[i][1][j].type)
                deathNum += 1

        ezstatslib.logError("OLOLO: %f deaths(%d) >= 3: %s\n" % (tt, deaths, resStr))
        tmpComboStr += ("OLOLO: %f deaths(%d) >= 3: %s\n" % (tt, deaths, resStr))
        
tmpComboStr += "==========================================\n"        

debugLines = ""
linesStr = ""     
for i in xrange(len(elementsCloseByTime)):    
    if len(elementsCloseByTime[i][0]) == 1:
        pass
    elif len(elementsCloseByTime[i][0]) == 2 and elementsCloseByTime[i][0][0] != elementsCloseByTime[i][0][1]:
        debugLines += "DEBUG: time: %s, delta: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s)\n" % \
                ( str(elementsCloseByTime[i][0]), \
                  str(elementsCloseByTime[i][0][1] - elementsCloseByTime[i][0][0]), \
                  elementsCloseByTime[i][1][0].attacker, \
                  elementsCloseByTime[i][1][0].target, \
                  elementsCloseByTime[i][1][0].type, \
                  elementsCloseByTime[i][1][1].attacker, \
                  elementsCloseByTime[i][1][1].target, \
                  elementsCloseByTime[i][1][1].type
                )
                
        if (elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][1].target and elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][1].attacker) or \
           (elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][1].attacker and elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][1].target):
            for pl in allplayers:
                if pl.name == elementsCloseByTime[i][1][0].attacker:
                    pl.mutual_kills.append([(elementsCloseByTime[i][0][1] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][0].target,elementsCloseByTime[i][1][0].type,elementsCloseByTime[i][1][1].type])
                if pl.name == elementsCloseByTime[i][1][1].attacker:
                    pl.mutual_kills.append([(elementsCloseByTime[i][0][1] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][1].target,elementsCloseByTime[i][1][1].type,elementsCloseByTime[i][1][0].type])
           
            linesStr += "Mutual kill: %s(%s) vs. %s(%s), time: %s, delta: %s\n" % \
                ( elementsCloseByTime[i][1][0].attacker, \
                  elementsCloseByTime[i][1][0].type, \
                  elementsCloseByTime[i][1][0].target, \
                  elementsCloseByTime[i][1][1].type, \
                  str(elementsCloseByTime[i][0]), \
                  str(elementsCloseByTime[i][0][1] - elementsCloseByTime[i][0][0]))

    elif len(elementsCloseByTime[i][0]) == 3:
        if elementsCloseByTime[i][0][0] != elementsCloseByTime[i][0][1] and elementsCloseByTime[i][0][0] != elementsCloseByTime[i][0][2] and elementsCloseByTime[i][0][1] != elementsCloseByTime[i][0][2]:
            # all times are different
            debugLines += "DEBUG: all 3 times are different: time: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s) <-> attacker3(%s), target3(%s), wp3(%s)\n" % \
                ( str(elementsCloseByTime[i][0]), \
                  elementsCloseByTime[i][1][0].attacker, \
                  elementsCloseByTime[i][1][0].target, \
                  elementsCloseByTime[i][1][0].type, \
                  elementsCloseByTime[i][1][1].attacker, \
                  elementsCloseByTime[i][1][1].target, \
                  elementsCloseByTime[i][1][1].type, \
                  elementsCloseByTime[i][1][2].attacker, \
                  elementsCloseByTime[i][1][2].target, \
                  elementsCloseByTime[i][1][2].type
                )
            # TODO find potential mutual pair
                
        else:
            debugLines += "DEBUG: len(elementsCloseByTime[i][0]) = 3, time: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s) <-> attacker3(%s), target3(%s), wp3(%s)\n" % \
                ( str(elementsCloseByTime[i][0]), \
                  elementsCloseByTime[i][1][0].attacker, \
                  elementsCloseByTime[i][1][0].target, \
                  elementsCloseByTime[i][1][0].type, \
                  elementsCloseByTime[i][1][1].attacker, \
                  elementsCloseByTime[i][1][1].target, \
                  elementsCloseByTime[i][1][1].type, \
                  elementsCloseByTime[i][1][2].attacker, \
                  elementsCloseByTime[i][1][2].target, \
                  elementsCloseByTime[i][1][2].type
                )
        
            if elementsCloseByTime[i][0][0] != elementsCloseByTime[i][0][1]:
                # debugLines += "DEBUG: time: %s, delta: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s)\n" % \
                    # ( str(elementsCloseByTime[i][0]), \
                      # str(elementsCloseByTime[i][0][1] - elementsCloseByTime[i][0][0]), \
                      # elementsCloseByTime[i][1][0].attacker, \
                      # elementsCloseByTime[i][1][0].target, \
                      # elementsCloseByTime[i][1][0].type, \
                      # elementsCloseByTime[i][1][1].attacker, \
                      # elementsCloseByTime[i][1][1].target, \
                      # elementsCloseByTime[i][1][1].type
                    # )
                
                if (elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][1].target and elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][1].attacker) or \
                   (elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][1].attacker and elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][1].target):
                    for pl in allplayers:
                        if pl.name == elementsCloseByTime[i][1][0].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][1] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][0].target,elementsCloseByTime[i][1][0].type,elementsCloseByTime[i][1][1].type])
                        if pl.name == elementsCloseByTime[i][1][1].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][1] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][1].target,elementsCloseByTime[i][1][1].type,elementsCloseByTime[i][1][0].type])
                                      
                    linesStr += "Mutual kill: %s(%s) vs. %s(%s), time: %s, delta: %s\n" % \
                        ( elementsCloseByTime[i][1][0].attacker, \
                          elementsCloseByTime[i][1][0].type, \
                          elementsCloseByTime[i][1][0].target, \
                          elementsCloseByTime[i][1][1].type, \
                          str(elementsCloseByTime[i][0]), \
                          str(elementsCloseByTime[i][0][1] - elementsCloseByTime[i][0][0]))
    
            elif elementsCloseByTime[i][0][0] != elementsCloseByTime[i][0][2]:
                # debugLines += "DEBUG: time: %s, delta: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s)\n" % \
                    # ( str(elementsCloseByTime[i][0]), \
                      # str(elementsCloseByTime[i][0][2] - elementsCloseByTime[i][0][0]), \
                      # elementsCloseByTime[i][1][0].attacker, \
                      # elementsCloseByTime[i][1][0].target, \
                      # elementsCloseByTime[i][1][0].type, \
                      # elementsCloseByTime[i][1][2].attacker, \
                      # elementsCloseByTime[i][1][2].target, \
                      # elementsCloseByTime[i][1][2].type
                    # )
                
                if (elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][2].target and elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][2].attacker) or \
                   (elementsCloseByTime[i][1][0].target == elementsCloseByTime[i][1][2].attacker and elementsCloseByTime[i][1][0].attacker == elementsCloseByTime[i][1][2].target):
                    for pl in allplayers:
                        if pl.name == elementsCloseByTime[i][1][0].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][2] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][0].target,elementsCloseByTime[i][1][0].type,elementsCloseByTime[i][1][2].type])
                        if pl.name == elementsCloseByTime[i][1][2].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][2] + elementsCloseByTime[i][0][0]) / 2.0,elementsCloseByTime[i][1][2].target,elementsCloseByTime[i][1][2].type,elementsCloseByTime[i][1][0].type])
                   
                    linesStr += "Mutual kill: %s(%s) vs. %s(%s), time: %s, delta: %s\n" % \
                        ( elementsCloseByTime[i][1][0].attacker, \
                          elementsCloseByTime[i][1][0].type, \
                          elementsCloseByTime[i][1][0].target, \
                          elementsCloseByTime[i][1][2].type, \
                          str(elementsCloseByTime[i][0]), \
                          str(elementsCloseByTime[i][0][2] - elementsCloseByTime[i][0][0]))
                          
            else: # elementsCloseByTime[i][0][1] != elementsCloseByTime[i][0][2]:
                # debugLines += "DEBUG: time: %s, delta: %s, attacker1(%s), target1(%s), wp1(%s) <-> attacker2(%s), target2(%s), wp2(%s)\n" % \
                    # ( str(elementsCloseByTime[i][0]), \
                      # str(elementsCloseByTime[i][0][2] - elementsCloseByTime[i][0][1]), \
                      # elementsCloseByTime[i][1][1].attacker, \
                      # elementsCloseByTime[i][1][1].target, \
                      # elementsCloseByTime[i][1][1].type, \
                      # elementsCloseByTime[i][1][2].attacker, \
                      # elementsCloseByTime[i][1][2].target, \
                      # elementsCloseByTime[i][1][2].type
                    # )
                
                if (elementsCloseByTime[i][1][1].attacker == elementsCloseByTime[i][1][2].target and elementsCloseByTime[i][1][1].target == elementsCloseByTime[i][1][2].attacker) or \
                   (elementsCloseByTime[i][1][1].target == elementsCloseByTime[i][1][2].attacker and elementsCloseByTime[i][1][1].attacker == elementsCloseByTime[i][1][2].target):
                    for pl in allplayers:
                        if pl.name == elementsCloseByTime[i][1][1].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][2] + elementsCloseByTime[i][0][1]) / 2.0,elementsCloseByTime[i][1][1].target,elementsCloseByTime[i][1][1].type,elementsCloseByTime[i][1][2].type])
                        if pl.name == elementsCloseByTime[i][1][2].attacker:
                            pl.mutual_kills.append([(elementsCloseByTime[i][0][2] + elementsCloseByTime[i][0][1]) / 2.0,elementsCloseByTime[i][1][2].target,elementsCloseByTime[i][1][2].type,elementsCloseByTime[i][1][1].type])
                   
                    linesStr += "Mutual kill: %s(%s) vs. %s(%s), time: %s, delta: %s\n" % \
                        ( elementsCloseByTime[i][1][1].attacker, \
                          elementsCloseByTime[i][1][1].type, \
                          elementsCloseByTime[i][1][1].target, \
                          elementsCloseByTime[i][1][2].type, \
                          str(elementsCloseByTime[i][0]), \
                          str(elementsCloseByTime[i][0][2] - elementsCloseByTime[i][0][1]))         
    
    elif len(elementsCloseByTime[i][0]) > 3:
        debugLines += "DEBUG: len(elementsCloseByTime[i][0]) = %d\n" % (len(elementsCloseByTime[i][0])) 
                         

tmpComboStr += debugLines
tmpComboStr += "\n"
tmpComboStr += linesStr        

# check that there at least one kill
killsSumOrig = 0
killsSum     = 0
for pl in allplayers:
    killsSumOrig += pl.origScore;
    killsSum     += pl.kills;
if killsSumOrig == 0 and killsSum == 0:
    ezstatslib.logError("There are no kills\n")
    exit(1)

# move XML data to common data
# for pl in allplayers:
    # for plXML in xmlPlayers:
        # if pl.name == plXML.name:
            # mmm = 1
            # for mmm in xrange(1,minutesPlayedXML+1):
                # pl.gaByMinutes[mmm] = plXML.gaByMinutesXML[mmm]
                # pl.yaByMinutes[mmm] = plXML.yaByMinutesXML[mmm]
                # pl.raByMinutes[mmm] = plXML.raByMinutesXML[mmm]
                # pl.mhByMinutes[mmm] = plXML.mhByMinutesXML[mmm]

            #for pwrup in plXML.powerUps:
            #    pl.powerUps.append(pwrup)


# clear players with 0 kills and 0 deaths
# TODO change progressSrt structure to be able to clean zero players in battle progress (source data: zero_player_in_stats)
# TODO clear headToHead of zero player
#for pl in allplayers:
#    if pl.kills == 0 and pl.deaths == 0:
#        allplayers.remove(pl);

allplayersByFrags = sorted(allplayers, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)

# fill final battle progress
progressLine = []
progressLineDict = {}
for pl in allplayersByFrags:    
    progressLine.append([pl.name, pl.frags()]);
    progressLineDict[pl.name] = [pl.frags(), pl.calcDelta()];
matchProgress.append(progressLine)
matchProgressDict.append(progressLineDict)
matchProgressDictEx.append(progressLineDict)

minsCount = len(matchProgressDict)
progressLineDict = {}
for pl in allplayersByFrags:
    progressLineDict[pl.name] = [minsCount*60, pl.frags(), pl.calcDelta()];

# correct final point if necessary
if len(matchProgressDictEx2) != 0 and matchProgressDictEx2[len(matchProgressDictEx2)-1][allplayers[0].name][0] == minsCount*60:
    matchProgressDictEx2[len(matchProgressDictEx2)-1] = progressLineDict
else:
    matchProgressDictEx2.append(progressLineDict)
    
# fill final element in calculatedStreaks
for pl in allplayers:
    pl.fillStreaks(currentMatchTime)
    pl.fillDeathStreaks(currentMatchTime)

plNameMaxLen = ezstatslib.DEFAULT_PLAYER_NAME_MAX_LEN
for pl in allplayers:
    plNameMaxLen = max(plNameMaxLen, len(pl.name))

powerUpsStatus = {}
for pwrup in ["ra","ya","ga","mh"]:
    exec("powerUpsStatus[\"%s\"] = False" % (pwrup))

# move power stats for doroped players from power ups by minutes and get power ups status
for pl in allplayers:
    pl.recoverArmorStats()

    for pwrup in ["ra","ya","ga","mh"]:
        exec("if pl.%s != 0:\n    powerUpsStatus[\"%s\"] = True" % (pwrup, pwrup))
    
# achievements
for pl in allplayers:
    pl.calculateAchievements(matchProgress, powerUpsStatus, headToHead, isTeamGame = False)
    
ezstatslib.calculateCommonAchievements(allplayers, headToHead, isTeamGame = False)

# sort by level
for pl in allplayers:
    pl.achievements = sorted(pl.achievements, key=lambda x: (x.achlevel), reverse=False)

# remove elements with one timestamp - the last one for same time should be left    
for pl in allplayers:
    pl.correctLifetime(minutesPlayedXML)
    
# generate output string
resultString = ""

resultString += "\n================== " + options.leagueName + " ==================\n"
resultString += "matchdate: " + matchdate + "\n"
resultString += "map: " + mapName + "\n"
resultString += "\n"

for pl in allplayersByFrags:
    resultString += ("{0:%ds} {1:3d}    ({2:s})\n" % (plNameMaxLen)).format(pl.name, pl.calcDelta(), pl.getFormatedStats_noTeamKills())

# if options.withScripts:
#     resultString += "</pre>MAIN_STATS_PLACE\n<pre>"
    
if options.withScripts:
    resultString += "</pre>MAIN_STATS_BARS_PLACE\n<pre>"
    
if options.withScripts:
    resultString += "</pre>PLAYERS_ACHIEVEMENTS_PLACE\n<pre>"

resultString += "\n"
resultString += "Power ups:\n"
for pl in allplayersByFrags:
    resultString += ("{0:%ds}  {1:s}\n" % (plNameMaxLen)).format(pl.name, pl.getFormatedPowerUpsStats())

# all players
resultString += "\n"
resultString += "All players:\n"
resultString += "GreenArm:   " + " [ " + ezstatslib.sortPlayersBy(allplayers, "ga") + " ]\n"
resultString += "YellowArm:  " + " [ " + ezstatslib.sortPlayersBy(allplayers, "ya") + " ]\n"
resultString += "RedArm:     " + " [ " + ezstatslib.sortPlayersBy(allplayers, "ra") + " ]\n"
resultString += "MegaHealth: " + " [ " + ezstatslib.sortPlayersBy(allplayers, "mh") + " ]\n"
resultString += "\n"
resultString += "TakenDam:   " + " [ " + ezstatslib.sortPlayersBy(allplayers, "tkn") + " ]\n"
resultString += "GivenDam:   " + " [ " + ezstatslib.sortPlayersBy(allplayers, "gvn") + " ]\n"
resultString += "DeltaDam:   " + " [ " + ezstatslib.sortPlayersBy(allplayers,"damageDelta", fieldType="method") + " ]\n"
resultString += "\n"
resultString += "Kills:      " + " [ " + ezstatslib.sortPlayersBy(allplayers, "kills") + " ]\n"
resultString += "Deaths:     " + " [ " + ezstatslib.sortPlayersBy(allplayers, "deaths") + " ]\n"
resultString += "Suicides:   " + " [ " + ezstatslib.sortPlayersBy(allplayers, "suicides") + " ]\n"
resultString += "\n"
# resultString += "Streaks:    " + " [ " + ezstatslib.sortPlayersBy(allplayers,"streaks") + " ]\n"
resultString += "SpawnFrags: " + " [ " + ezstatslib.sortPlayersBy(allplayers,"spawnfrags") + " ]\n"
resultString += "\n"
# resultString += "RL skill DH:" + " [ " + ezstatslib.sortPlayersBy(allplayers, "rlskill_dh") + " ]\n"
# resultString += "RL skill AD:" + " [ " + ezstatslib.sortPlayersBy(allplayers, "rlskill_ad") + " ]\n"
resultString += "\n"
# resultString += "Weapons:\n"
# resultString += "RL:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_rl", units="%") + " ]\n"
# resultString += "LG:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_lg", units="%") + " ]\n"
# resultString += "GL:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_gl", units="%") + " ]\n"
# resultString += "SG:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_sg", units="%") + " ]\n"
# resultString += "SSG:        " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_ssg", units="%") + " ]\n"
resultString += "\n"

resultString += "Players weapons:\n"
# weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
weaponsCheck = ezstatslib.WeaponsCheckRes(True)
for pl in allplayersByFrags:
    resultString += ("{0:%ds} kills  {1:3d}  :: {2:100s}\n" % (plNameMaxLen)).format(pl.name, pl.kills, pl.getWeaponsKills(pl.kills, weaponsCheck))
    resultString += ("{0:%ds} deaths {1:3d}  :: {2:100s}\n" % (plNameMaxLen)).format("",      pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    resultString += "\n"
    resultString += ("{0:%ds} given {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageGvn+pl.damageGvnArmor, pl.getWeaponsDamageGvn(pl.damageGvn+pl.damageGvnArmor, weaponsCheck))
    resultString += ("{0:%ds} taken {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageTkn+pl.damageTknArmor, pl.getWeaponsDamageTkn(pl.damageTkn+pl.damageTknArmor, weaponsCheck))
    resultString += ("{0:%ds} self  {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageSelf+pl.damageSelfArmor, pl.getWeaponsDamageSelf(pl.damageSelf+pl.damageSelfArmor, weaponsCheck))
    # resultString += ("{0:%ds} avg damage :: {1:100s}\n" % (plNameMaxLen)).format("", pl.getWeaponsAccuracy(weaponsCheck))  TODO
    resultString += ("{0:%ds} rl skill   :: {1:200s}\n" % (plNameMaxLen)).format("", pl.getRLSkill())
    resultString += "\n"
    resultString += "\n"

if options.withScripts:
    resultString += "RL skill:\n"
    resultString += "\nHIGHCHART_RL_SKILL_PLACE\n"

if options.withScripts:    
    resultString += "\n</pre>HIGHCHART_PLAYER_LIFETIME_PLACE\n<pre>"
# ============================================================================================================

# # calculated streaks
# resultString += "\n"
# resultString += "Players streaks (%d+):\n" % (ezstatslib.KILL_STREAK_MIN_VALUE)
# resultString += str( ezstatslib.createStreaksHtmlTable(allplayers, ezstatslib.StreakType.KILL_STREAK) )
# resultString += "\n"
# 
# # death streaks
# resultString += "\n"
# resultString += "Players death streaks (%d+):\n" % (ezstatslib.DEATH_STREAK_MIN_VALUE)
# resultString += str( ezstatslib.createStreaksHtmlTable(allplayers, ezstatslib.StreakType.DEATH_STREAK) )
# resultString += "\n"

totalStreaksHtmlTable = \
    HTML.Table(header_row=["Kill streaks (%d+)\n" % (ezstatslib.KILL_STREAK_MIN_VALUE), "Death streaks (%d+)\n" % (ezstatslib.DEATH_STREAK_MIN_VALUE)],
               rows=[ \
                   HTML.TableRow(cells=[ \
                                     HTML.TableCell( str( ezstatslib.createStreaksHtmlTable(allplayersByFrags, ezstatslib.StreakType.KILL_STREAK)) ),
                                     HTML.TableCell( str( ezstatslib.createStreaksHtmlTable(allplayersByFrags, ezstatslib.StreakType.DEATH_STREAK)) ) \
                                       ] \
                                ) \
                    ],               
               border="1", 
               style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

resultString += "\n"
resultString += "Players streaks:\n"
resultString += str(totalStreaksHtmlTable)
resultString += "\n"


fullTotalStreaksHtmlTable = \
    HTML.Table(header_row=["Kill streaks (%d+)\n" % (ezstatslib.KILL_STREAK_MIN_VALUE), "Death streaks (%d+)\n" % (ezstatslib.DEATH_STREAK_MIN_VALUE)],
               rows=[ \
                   HTML.TableRow(cells=[ \
                                     HTML.TableCell( str( ezstatslib.createFullStreaksHtmlTable(allplayersByFrags, ezstatslib.StreakType.KILL_STREAK)) ),
                                     HTML.TableCell( str( ezstatslib.createFullStreaksHtmlTable(allplayersByFrags, ezstatslib.StreakType.DEATH_STREAK)) ) \
                                       ] \
                                ) \
                    ],               
               border="1", 
               style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

# POINT: Players full streaks
# resultString += "\n"
# resultString += "Players full streaks:\n"
# resultString += str(fullTotalStreaksHtmlTable)
# resultString += "\n"

# POINT: streaks timelines place
# if options.withScripts:
#     resultString += "</pre>STREAK_TIMELINE_PLACE\n<pre>"
#     
if options.withScripts:
    resultString += "</pre>STREAK_ALL_TIMELINE_PLACE\n<pre>"

# ============================================================================================================

# H2H stats
resultString += "\n"
resultString += "Head-to-Head stats (who :: whom)\n"
for pl in allplayersByFrags:
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += ("{0:%ds} {1:3d} :: {2:100s}\n" % (plNameMaxLen)).format(pl.name, pl.kills, resStr)
resultString += "\n"

# H2HDamage stats
resultString += "\n"
resultString += "Head-to-HeadDamage stats (who :: whom)\n"
for pl in allplayersByFrags:
    resStr = ""
    for el in sorted(headToHeadDamage[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += ("{0:%ds} {1:3d} - {2:3d} :: {3:100s}\n" % (plNameMaxLen)).format(pl.name, pl.gvn, pl.tkn, resStr)
resultString += "\n"

# ============================================================================================================

# Players duels table
resultString += "\n"
resultString += "Players duels:<br>"
headerRow=['', 'Frags', 'Kills', 'Deaths']
playersNames = []
for pl in allplayersByFrags:
    headerRow.append(pl.name);
    playersNames.append(pl.name)

colAlign=[]
for i in xrange(len(headerRow)):
    colAlign.append("center")

htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

for pl in allplayersByFrags:
    tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                    ezstatslib.htmlBold(pl.frags()),
                                    ezstatslib.htmlBold(pl.kills),
                                    ezstatslib.htmlBold(pl.deaths)])
        
    for plName in playersNames:
        if pl.name == plName:
            tableRow.cells.append( HTML.TableCell(str(pl.suicides), bgcolor=ezstatslib.BG_COLOR_GRAY) )
        else:            
            plKills = 0
            for val in headToHead[pl.name]:
                if val[0] == plName:
                    plKills = val[1]
            
            plDeaths = 0
            for val in headToHead[plName]:
                if val[0] == pl.name:
                    plDeaths = val[1]
            
            cellVal = "%s / %s" % (ezstatslib.htmlBold(plKills)  if plKills  > plDeaths else str(plKills),
                                   ezstatslib.htmlBold(plDeaths) if plDeaths > plKills  else str(plDeaths))
            
            cellColor = ""
            if plKills == plDeaths:
                cellColor = ezstatslib.BG_COLOR_LIGHT_GRAY
            elif plKills > plDeaths:
                cellColor = ezstatslib.BG_COLOR_GREEN
            else:
                cellColor = ezstatslib.BG_COLOR_RED
            
            tableRow.cells.append( HTML.TableCell(cellVal, bgcolor=cellColor) )
            
    htmlTable.rows.append(tableRow)  

resultString += str(htmlTable)
    


# Players damage duels table
resultString += "\n"
resultString += "Players damage duels:<br>"
headerRow=['', 'Frags', 'Given', 'Taken']
playersNames = []
for pl in allplayersByFrags:
    headerRow.append(pl.name);
    playersNames.append(pl.name)

colAlign=[]
for i in xrange(len(headerRow)):
    colAlign.append("center")

htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

for pl in allplayersByFrags:
    tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                    ezstatslib.htmlBold(pl.frags()),
                                    ezstatslib.htmlBold(pl.gvn),
                                    ezstatslib.htmlBold(pl.tkn)])
        
    for plName in playersNames:
        if pl.name == plName:
            tableRow.cells.append( HTML.TableCell(str(pl.damageSelf+pl.damageSelfArmor), bgcolor=ezstatslib.BG_COLOR_GRAY) )
        else:            
            plDamageGvn = 0
            for val in headToHeadDamage[pl.name]:
                if val[0] == plName:
                    plDamageGvn = val[1]
            
            plDamageTkn = 0
            for val in headToHeadDamage[plName]:
                if val[0] == pl.name:
                    plDamageTkn = val[1]
            
            cellVal = "%s / %s" % (ezstatslib.htmlBold(plDamageGvn)  if plDamageGvn  > plDamageTkn else str(plDamageGvn),
                                   ezstatslib.htmlBold(plDamageTkn) if plDamageTkn > plDamageGvn  else str(plDamageTkn))
            
            cellColor = ""
            if plDamageGvn == plDamageTkn:
                cellColor = ezstatslib.BG_COLOR_LIGHT_GRAY
            elif plDamageGvn > plDamageTkn:
                cellColor = ezstatslib.BG_COLOR_GREEN
            else:
                cellColor = ezstatslib.BG_COLOR_RED
            
            tableRow.cells.append( HTML.TableCell(cellVal, bgcolor=cellColor) )
            
    htmlTable.rows.append(tableRow)  

resultString += str(htmlTable)



i = 1
resultString += "\n\n"
resultString += "battle progress:\n"
plPrevFragsDict = {}

isFirstLine = True
for mpline in matchProgress: # mpline: [[pl1_name,pl1_frags],[pl2_name,pl2_frags],..]       
    s = ""
    for mp in mpline:        # mp:     [pl1_name,pl1_frags]
        if isFirstLine:
            plFragsDelta = mp[1]
        else:
            plFragsDelta = mp[1] - plPrevFragsDict[mp[0]]
        
        plPrevFragsDict[mp[0]] = mp[1]

        if plFragsDelta == 0:
            deltaStr = "<sup>0  </sup>"
        else:
            if plFragsDelta > 0:
                deltaStr = "<sup>+%d%s</sup>" % (plFragsDelta, " " if plFragsDelta < 10 else "")
            else:
                deltaStr = "<sup>%d%s</sup>"  % (plFragsDelta, " " if plFragsDelta < 10 else "")
        
        s += ("{0:%ds}" % (plNameMaxLen+9+11)).format( "%s(%d)%s" % (mp[0], mp[1], deltaStr) )
    
    if isFirstLine: isFirstLine = False    

    resultString += "%d:%s %s\n" % (i, "" if i >= 10 else " ",  s)
        
    if isOverTime and i == timelimit:
        resultString += "\t\t>> IT IS OVERTIME!! <<\n"
    
    i += 1
    
# POINT battle progress
# if options.withScripts:
#     resultString += "\nBP_PLACE\n"
    
if options.withScripts:
    resultString += "\nHIGHCHART_BATTLE_PROGRESS_PLACE\n"
    
if options.withScripts:
    resultString += "\nHIGHCHART_EXTENDED_BATTLE_PROGRESS_PLACE\n"
    
if options.withScripts:
    resultString += "\nHIGHCHART_PLAYERS_RANK_PROGRESS_PLACE\n"
    
if options.withScripts:
    resultString += ezstatslib.HTML_EXPAND_CHECKBOX_TAG
    for pl in allplayersByFrags:
        resultString += "</pre>%s_KILLS_BY_MINUTES_PLACE\n<pre>" % (ezstatslib.escapePlayerName(pl.name))    

if options.withScripts:
    resultString += "<hr>\n"
    resultString += ezstatslib.HTML_EXPAND_POWER_UPS_CHECKBOX_TAG
    resultString += "</pre> POWER_UPS_BARS_PLACE\n"
    resultString += "\nHIGHCHART_POWER_UPS_PLACE\n<pre>"
    # resultString += "</pre>ra_BY_MINUTES_PLACE\n<pre>"
    # resultString += "</pre>ya_BY_MINUTES_PLACE\n<pre>"
    # resultString += "</pre>ga_BY_MINUTES_PLACE\n<pre>"
    # resultString += "</pre>mh_BY_MINUTES_PLACE\n<pre>"
    for pl in allplayersByFrags:
        resultString += "</pre>%s_POWER_UPS_BY_MINUTES_PLACE\n<pre>" % (ezstatslib.escapePlayerName(pl.name))    

if options.withScripts:
    resultString += "</pre>POWER_UPS_TIMELINE_PLACE\n<pre>"
    
if options.withScripts:
    resultString += "</pre>POWER_UPS_TIMELINE_VER2_PLACE\n<pre>"

if len(dropedplayers) != 0:
    dropedStr = ""
    for pl in dropedplayers:
        dropedStr += "%s(drop time: %d)," % (pl.name, pl.disconnectTime)

    dropedStr = dropedStr[:-1]
    resultString += "Droped players: " + dropedStr + "\n"

if len(spectators) != 0:
    resultString += "Spectators: " + str(spectators) + "\n"

if len(disconnectedplayers) != 0:
    resultString += "\n"
    resultString += "Disconnected players: " + str(disconnectedplayers) + "\n"
    resultString += "\n"
    
connectedPlayersStr = ""
for pl in allplayersByFrags:
    if pl.connectTime != 0:
        connectedPlayersStr += "%s(connect time: %d), " % (pl.name, pl.connectTime)
    
if connectedPlayersStr != "":
    connectedPlayersStr = connectedPlayersStr[:-1]
    resultString += "\n"
    resultString += "Connected players: " + connectedPlayersStr[:-1] + "\n"
    resultString += "\n"

print "currentMinute:", currentMinute
print "matchMinutesCnt:", matchMinutesCnt
for pl in allplayersByFrags:
    for el in headToHead[pl.name]:
        print pl.name, ":", el[0], " - ", el[1], " - ", el[2]
        
    print "%s: ra[%d] %s" % (pl.name, pl.ra, str(pl.raByMinutes))
    print "%s: ya[%d] %s" % (pl.name, pl.ya, str(pl.yaByMinutes))
    print "%s: ga[%d] %s" % (pl.name, pl.ga, str(pl.gaByMinutes))
    print "%s: mh[%d] %s" % (pl.name, pl.mh, str(pl.mhByMinutes))
    
    puStr = ""
    for pu in pl.powerUps:
        puStr += "%s, " % (str(pu))
    print "%s: powerUps: %s" % (pl.name, puStr)
    
    # streaks
    strkStr = ""
    for strk in pl.calculatedStreaks:
        strkStr += "%s [%s], " % (strk.toString(), str(strk.names))
        
    print "%s: streaks: %s" % (pl.name, strkStr)

# mutual kills 
resultString += "\nMutual kills: \n"
for pl in allplayers:
    if len(pl.mutual_kills) != 0:
        resultString += "%s(%d): " % (pl.name, len(pl.mutual_kills))
        for mk in pl.mutual_kills:
            resultString += "%f: %s(%s,%s), " % (mk[0], mk[1], mk[2], mk[3])
        resultString += "\n"
           
resultString += "\n"    

# lifetimeXML
resultString += "\nLifetime: \n"
for pl in allplayers:    
    resultString += "%s: %f, inactive time: %f,  1st death: time(%f), lifetime(%f)\n" % (pl.name, pl.lifetimeXML, (minutesPlayedXML*60 - pl.lifetimeXML), pl.firstDeathXML.time, pl.firstDeathXML.lifetime)

resultString += "\n"
    
# print resultString  RESULTPRINT

# ============================================================================================================

def writeHtmlWithScripts(f, sortedPlayers, resStr):
    plStr = ""
    for pl in sortedPlayers:
        plStr += "%s(%d) " % (pl.name, pl.frags())
    plStr = plStr[:-1]
    plStr += "\n"        
    f.write("<!--\nGAME_PLAYERS\n" + plStr + "-->\n")
    
    f.write("<!--\nCOMBOS\n" + tmpComboStr + "-->\n")  # TEMP!!
    
    pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
    pageTitle = "%s %s %s" % (options.leagueName, mapName, matchdate)  # global values
    pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", pageTitle)
    pageHeaderStr += ezstatslib.HTML_HEADER_SCRIPT_GOOGLE_CHARTS_LOAD
    
    f.write(pageHeaderStr)
        
    # battle progress -->
    bpFunctionStr = ezstatslib.HTML_SCRIPT_BATTLE_PROGRESS_FUNCTION
    
    columnLines = ""        
    for pl in sortedPlayers:
        columnLines += ezstatslib.HTML_SCRIPT_BATTLE_PROGRESS_ADD_COLUMN_LINE.replace("PLAYER_NAME", pl.name)
    bpFunctionStr = bpFunctionStr.replace("ADD_COLUMN_LINES", columnLines)
    
    rowLines = "[0"
    for k in xrange(len(sortedPlayers)):
        rowLines += ",0"        
    rowLines += "],\n"
    
    minuteNum = 1
    for minEl in matchProgressDict:
        rowLines += "[%d" % (minuteNum)
        for pl in sortedPlayers:
            rowLines += ",%d" % (minEl[pl.name][0])
        rowLines += "],\n"
        minuteNum += 1
        
    rowLines = rowLines[:-1]
     
    bpFunctionStr = bpFunctionStr.replace("ADD_ROWS_LINES", rowLines)       

    # POINT battle progress
    # f.write(bpFunctionStr)
    # <-- battle progress
    
    # main stats -->
    # mainStatsStr = ezstatslib.HTML_SCRIPT_MAIN_STATS_FUNCTION
    # fragsLines    = ""
    # killsLines    = ""
    # deathsLines   = ""    
    # suicidesLines = ""
    # for pl in sortedPlayers:
    #     fragsLines    += "['%s',%d],\n" % (pl.name, pl.frags())
    #     killsLines    += "['%s',%d],\n" % (pl.name, pl.kills)
    #     deathsLines   += "['%s',%d],\n" % (pl.name, pl.deaths)
    #     suicidesLines += "['%s',%d],\n" % (pl.name, pl.suicides)
    # 
    # mainStatsStr = mainStatsStr.replace("ADD_FRAGS_ROWS",    fragsLines)
    # mainStatsStr = mainStatsStr.replace("ADD_KILLS_ROWS",    killsLines)
    # mainStatsStr = mainStatsStr.replace("ADD_DEATHS_ROWS",   deathsLines)
    # mainStatsStr = mainStatsStr.replace("ADD_SUICIDES_ROWS", suicidesLines)
    # 
    # f.write(mainStatsStr)
    # <-- main stats
    
    # main stats bars-->
    isAnnotations = True
    
    mainStatsBarsStr = ezstatslib.HTML_SCRIPT_MAIN_STATS_BARS_FUNCTION
    
    namesLine    = "['Name'"
    fragsLine    = "['Frags'"
    killsLine    = "['Kills'"
    deathsLine   = "['Deaths'"    
    suicidesLine = "['Suicides'"
    
    for pl in sortedPlayers:
        namesLine    += ", '%s'" % (pl.name)
        fragsLine    += ", %d" % (pl.frags())
        killsLine    += ", %d" % (pl.kills)
        deathsLine   += ", %d" % (pl.deaths)
        suicidesLine += ", %d" % (pl.suicides)
        
        if isAnnotations:
            namesLine += ", {type: 'string', role: 'annotation'}"
            fragsLine    += ", '%d'" % (pl.frags())
            killsLine    += ", '%d'" % (pl.kills)
            deathsLine   += ", '%d'" % (pl.deaths)
            suicidesLine += ", '%d'" % (pl.suicides)
                    
    namesLine    += "],\n"
    fragsLine    += "],\n"
    killsLine    += "],\n"
    deathsLine   += "],\n"
    suicidesLine += "]\n"
    
    mainStatsBarsStr = mainStatsBarsStr.replace("ADD_HEADER_ROW", namesLine)
    mainStatsBarsStr = mainStatsBarsStr.replace("ADD_STATS_ROWS", fragsLine + killsLine + deathsLine + suicidesLine)    

    f.write(mainStatsBarsStr)
    # <-- main stats bars
    
    # power ups bars-->            
    isAnnotations = True
    
    powerUpsBarsStr = ezstatslib.HTML_SCRIPT_POWER_UPS_BARS_FUNCTION
    
    namesLine = "['Name'"
    raLine    = "['Red Armor'"
    yaLine    = "['Yellow Armor'"
    gaLine    = "['Green Armor'"    
    mhLine    = "['Mega Health'"
    
    for pl in sortedPlayers:
        namesLine += ", '%s'" % (pl.name)
        raLine    += ", %d" % (pl.ra)
        yaLine    += ", %d" % (pl.ya)
        gaLine    += ", %d" % (pl.ga)
        mhLine    += ", %d" % (pl.mh)
        
        if isAnnotations:
            namesLine += ", {type: 'string', role: 'annotation'}"
            raLine    += ", '%d'" % (pl.ra)
            yaLine    += ", '%d'" % (pl.ya)
            gaLine    += ", '%d'" % (pl.ga)
            mhLine    += ", '%d'" % (pl.mh)
                    
    namesLine += "],\n"
    raLine    += "],\n"
    yaLine    += "],\n"
    gaLine    += "],\n"
    mhLine    += "]\n"
    
    powerUpsBarsStr = powerUpsBarsStr.replace("ADD_HEADER_ROW", namesLine)
    powerUpsBarsStr = powerUpsBarsStr.replace("ADD_STATS_ROWS", raLine + yaLine + gaLine + mhLine)    

    f.write(powerUpsBarsStr)
    # <-- power ups bars
    
    # power ups by minutes -->
    
    # TODO ezstatslib.logError("WARNING: ...") check power ups sum and given value
    
    powerUpsByMinutesStr = ""
    maxValue = 0
    minValue = 0
    maxTotalValue = 0
    minTotalValue = 0
    
    for powerUpName in ["RedArmor","YellowArmor","GreenArmor","MegaHealth"]:
        
        shortName = ""
        if powerUpName == "RedArmor":
            shortName = "ra"
        elif powerUpName == "YellowArmor":
            shortName = "ya"
        elif powerUpName == "GreenArmor":
            shortName = "ga"
        elif powerUpName == "MegaHealth":
            shortName = "mh"
        
        raByMinutesStr = ezstatslib.HTML_SCRIPT_POWER_UPS_BY_MINUTES_FUNCTION
        raByMinutesStr = raByMinutesStr.replace("POWER_UP_NAME", powerUpName)
        
        powerUpByMinutesHeaderStr = "['Minute'"
        for pl in allplayersByFrags:
            powerUpByMinutesHeaderStr += ",'%s'" % (pl.name)
        powerUpByMinutesHeaderStr += "],\n"

        raByMinutesStr = raByMinutesStr.replace("ADD_HEADER_ROW", powerUpByMinutesHeaderStr)
        raByMinutesStr = raByMinutesStr.replace("ADD_TOTAL_HEADER_ROW", powerUpByMinutesHeaderStr)
        
        raByMinutesRowsStr = ""
        minut = 1
        #plMaxValue = 0
        #plMinValue = 0
        while minut <= currentMinute:
            raByMinutesRowsStr += "['%d'" % (minut)
            
            for pl in sortedPlayers:
                exec("val = pl.%sByMinutes[minut]" % (shortName))
                raByMinutesRowsStr += ",%d" % (val)
            raByMinutesRowsStr += "],\n"
            
            #plMaxValue = max(plMaxValue, stackSum)
            #plMinValue = min(plMinValue, stackNegVal)
            minut += 1
            
        raByMinutesStr = raByMinutesStr.replace("ADD_STATS_ROWS", raByMinutesRowsStr)
        
        raTotalRowsStr = "[''"
        for pl in sortedPlayers:
            exec("val = pl.%s" % (shortName))
            raTotalRowsStr += ",%d" % (val)
        raTotalRowsStr += "],\n"
            
        raByMinutesStr = raByMinutesStr.replace("ADD_TOTAL_STATS_ROWS", raTotalRowsStr)
    
        powerUpsByMinutesDivTag = ezstatslib.HTML_POWER_UPS_BY_MINUTES_DIV_TAG
        powerUpsByMinutesDivTag = powerUpsByMinutesDivTag.replace("POWER_UP_NAME", powerUpName)
        
        powerUpsByMinutesStr += raByMinutesStr
        
        # powerUpsByMinutesStr = powerUpsByMinutesStr.replace("MIN_VALUE", str(minValue))
        # powerUpsByMinutesStr = powerUpsByMinutesStr.replace("MAX_VALUE", str(maxValue))
        # powerUpsByMinutesStr = powerUpsByMinutesStr.replace("TOTAL_MIN__VALUE", str(minTotalValue))
        # powerUpsByMinutesStr = powerUpsByMinutesStr.replace("TOTAL_MAX__VALUE", str(maxTotalValue))
        powerUpsByMinutesStr = powerUpsByMinutesStr.replace("MIN_VALUE", "0")
        powerUpsByMinutesStr = powerUpsByMinutesStr.replace("MAX_VALUE", "10")
        powerUpsByMinutesStr = powerUpsByMinutesStr.replace("TOTAL_MIN__VALUE", "0")
        powerUpsByMinutesStr = powerUpsByMinutesStr.replace("TOTAL_MAX__VALUE", "10")
        
        # add div
        # resStr = resStr.replace("%s_BY_MINUTES_PLACE" % (shortName), powerUpsByMinutesDivTag)                
    
    # f.write(powerUpsByMinutesStr)
    # <-- power ups by minutes
    
    # highcharts power ups -->
    highchartsPowerUpsFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_POWER_UPS_FUNCTIONS
            
    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    
    
    hcDelim = "}, {\n"
    
    for powerUpName in ["ra","ya","ga","mh"]:    
        rowLines = ""        
        for pl in sortedPlayers:
            if rowLines != "":
                rowLines += hcDelim
            
            rowLines += "name: '%s',\n" % (pl.name)
            rowLines += "data: [0"                
            cnt = 0
            for minNum in xrange(1,matchMinutesCnt+1):  # global matchMinutesCnt
                exec("cnt += pl.%sByMinutes[minNum]" % (powerUpName))
                rowLines += ",%d" % (cnt)
            
            rowLines += "]\n"        
        
        highchartsPowerUpsFunctionStr = highchartsPowerUpsFunctionStr.replace("ADD_STAT_ROWS_%s" % (powerUpName), rowLines)
                
    f.write(highchartsPowerUpsFunctionStr)
    # <-- highcharts power ups
    
    # players power ups by minutes by players -->
    allPlayersPowerUpsByMinutesStr = ""
    maxValue = 0    
    maxTotalValue = 0    
    for pl in allplayersByFrags:
        plNameEscaped = ezstatslib.escapePlayerName(pl.name)
        
        playerPowerUpsByMinutesStr = ezstatslib.HTML_SCRIPT_PLAYER_POWER_UPS_BY_MINUTES_BY_PLAYERS_FUNCTION
        playerPowerUpsByMinutesStr = playerPowerUpsByMinutesStr.replace("PLAYER_NAME", plNameEscaped)
        
        playerPowerUpsByMinutesRowsStr = ""
        minut = 1
        plMaxValue = 0        
        while minut <= currentMinute:
            playerPowerUpsByMinutesRowsStr += "['%d',%d,%d,%d,%d],\n" % (minut, pl.mhByMinutes[minut], pl.gaByMinutes[minut], pl.yaByMinutes[minut], pl.raByMinutes[minut])
            stackSum = pl.raByMinutes[minut] + pl.yaByMinutes[minut] + pl.gaByMinutes[minut] + pl.mhByMinutes[minut]
            plMaxValue = max(plMaxValue, stackSum)
            minut += 1            

        playerPowerUpsByMinutesStr = playerPowerUpsByMinutesStr.replace("ADD_STATS_ROWS", playerPowerUpsByMinutesRowsStr)
        
        playerPowerUpsTotalRowsStr = "['',%d,%d,%d,%d],\n" % (pl.mh, pl.ga, pl.ya, pl.ra)
        playerPowerUpsByMinutesStr = playerPowerUpsByMinutesStr.replace("ADD_TOTAL_STATS_ROWS", playerPowerUpsTotalRowsStr)
        
        playerPowerUpsByMinutesDivTag = ezstatslib.HTML_PLAYER_POWER_UPS_BY_MINUTES_BY_PLAYERS_DIV_TAG
        playerPowerUpsByMinutesDivTag = playerPowerUpsByMinutesDivTag.replace("PLAYER_NAME", plNameEscaped)
        
        allPlayersPowerUpsByMinutesStr += playerPowerUpsByMinutesStr
        
        # add div
        resStr = resStr.replace("%s_POWER_UPS_BY_MINUTES_PLACE" % (plNameEscaped), playerPowerUpsByMinutesDivTag)
        
        # max & min
        maxValue = max(maxValue, plMaxValue)
        
        # maxTotalValue = max(maxTotalValue, pl.kills)
        #maxTotalValue = max(maxTotalValue, sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True)[0][1])
        maxTotalValue = max(maxTotalValue, pl.mh, pl.ga, pl.ya, pl.ra)
            
    allPlayersPowerUpsByMinutesStr = allPlayersPowerUpsByMinutesStr.replace("MAX_VALUE", str(maxValue))    
    allPlayersPowerUpsByMinutesStr = allPlayersPowerUpsByMinutesStr.replace("TOTAL_MAX__VALUE", str(maxTotalValue))
    
    f.write(allPlayersPowerUpsByMinutesStr)
    # <-- players power ups by minutes by players
    
    # players kills by minutes -->
    allPlayerKillsByMinutesStr = ""
    maxValue = 0
    minValue = 0
    maxTotalValue = 0
    minTotalValue = 0
    for pl in allplayersByFrags:
        plNameEscaped = ezstatslib.escapePlayerName(pl.name)
        
        playerKillsByMinutesStr = ezstatslib.HTML_SCRIPT_PLAYER_KILLS_BY_MINUTES_FUNCTION
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("PLAYER_NAME", plNameEscaped)
        
        playerH2hElem = headToHead[pl.name]
        
        playerKillsByMinutesHeaderStr = "['Minute'"
        for el in playerH2hElem:
            playerKillsByMinutesHeaderStr += ",'%s'" % (el[0] if el[0] != pl.name else "suicides")
        playerKillsByMinutesHeaderStr += "],\n"
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_HEADER_ROW", playerKillsByMinutesHeaderStr)
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_TOTAL_HEADER_ROW", playerKillsByMinutesHeaderStr)
        
        playerKillsByMinutesRowsStr = ""
        minut = 1
        plMaxValue = 0
        plMinValue = 0
        while minut <= currentMinute:
            playerKillsByMinutesRowsStr += "['%d'" % (minut)
            stackSum = 0
            stackNegVal = 0
            for el in playerH2hElem:
                playerKillsByMinutesRowsStr += ",%d" % (el[2][minut] if el[0] != pl.name else -el[2][minut])
                if el[0] != pl.name:
                    stackSum += el[2][minut]
                else:
                    stackNegVal = min(stackNegVal, -el[2][minut])
            playerKillsByMinutesRowsStr += "],\n"
            plMaxValue = max(plMaxValue, stackSum)
            plMinValue = min(plMinValue, stackNegVal)
            minut += 1
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_STATS_ROWS", playerKillsByMinutesRowsStr)
        
        playerKillsTotalRowsStr = "[''"
        for el in playerH2hElem:
            playerKillsTotalRowsStr += ",%d" % (el[1] if el[0] != pl.name else -pl.suicides)
        playerKillsTotalRowsStr += "],\n"
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_TOTAL_STATS_ROWS", playerKillsTotalRowsStr)
        
        playerKillsByMinutesDivTag = ezstatslib.HTML_PLAYER_KILLS_BY_MINUTES_DIV_TAG
        playerKillsByMinutesDivTag = playerKillsByMinutesDivTag.replace("PLAYER_NAME", plNameEscaped)
        
        allPlayerKillsByMinutesStr += playerKillsByMinutesStr
        
        # add div
        resStr = resStr.replace("%s_KILLS_BY_MINUTES_PLACE" % (plNameEscaped), playerKillsByMinutesDivTag)
        
        # max & min
        maxValue = max(maxValue, plMaxValue)
        minValue = min(minValue, plMinValue)
        
        # maxTotalValue = max(maxTotalValue, pl.kills)
        maxTotalValue = max(maxTotalValue, sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True)[0][1])
        minTotalValue = min(minTotalValue, -pl.suicides)
        
    allPlayerKillsByMinutesStr = allPlayerKillsByMinutesStr.replace("MIN_VALUE", str(minValue))
    allPlayerKillsByMinutesStr = allPlayerKillsByMinutesStr.replace("MAX_VALUE", str(maxValue))
    allPlayerKillsByMinutesStr = allPlayerKillsByMinutesStr.replace("TOTAL_MIN__VALUE", str(minTotalValue))
    allPlayerKillsByMinutesStr = allPlayerKillsByMinutesStr.replace("TOTAL_MAX__VALUE", str(maxTotalValue))
    
    f.write(allPlayerKillsByMinutesStr)
    # <-- players kills by minutes
    
    # streaks timeline -->
    streaksTimelineFunctionStr = ezstatslib.HTML_SCRIPT_STREAK_TIMELINE_FUNCTION
    
    rowLines = ""
    for pl in allplayersByFrags:
        strkRes,maxStrk = pl.getCalculatedStreaksFull()
        for strk in strkRes:
            rowLines += "[ '%s', '%d', new Date(0,0,0,0,%d,%d), new Date(0,0,0,0,%d,%d) ],\n" % (pl.name, strk.count, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))
            
        if len(strkRes) == 0:
            rowLines += "[ '%s', '', new Date(0,0,0,0,0,0), new Date(0,0,0,0,0,0) ],\n" % (pl.name)  # empty element in order to add player            
        
        # rowLines += "[ '%s', '', new Date(0,0,0,0,10,0), new Date(0,0,0,0,10,0) ],\n" % (pl.name) # TODO change options - need length        
        
    deathRowLines = ""
    for pl in allplayersByFrags:
        strkRes,maxStrk = pl.getDeatchStreaksFull()
        for strk in strkRes:
            deathRowLines += "[ '%s', '%d', new Date(0,0,0,0,%d,%d), new Date(0,0,0,0,%d,%d) ],\n" % (pl.name, strk.count, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))            
            
        if len(strkRes) == 0:
            deathRowLines += "[ '%s', '', new Date(0,0,0,0,0,0), new Date(0,0,0,0,0,0) ],\n" % (pl.name)  # empty element in order to add player            
        
        # deathRowLines += "[ '%s', '', new Date(0,0,0,0,10,0), new Date(0,0,0,0,10,0) ],\n" % (pl.name) # TODO change options - need length
    
    streaksTimelineFunctionStr = streaksTimelineFunctionStr.replace("ADD_STATS_ROWS", rowLines)
    streaksTimelineFunctionStr = streaksTimelineFunctionStr.replace("ADD_DEATH_STATS_ROWS", deathRowLines)       
                
    # TODO calculate height using players count
    # TODO black text color for deaths
    # TODO hints ??
    # TODO correct last events end time (10:01 or 10:02)
    # TODO check on 15 and 20 minutes
    # TODO add finish event or events, the timeline should be full
    # TODO bold players names
    # TODO folding ??
                
    # POINT: streaksTimelineFunctionStr
    # f.write(streaksTimelineFunctionStr)
    # <-- streaks timeline
    
    # all streaks timeline -->
    allStreaksTimelineFunctionStr = ezstatslib.HTML_SCRIPT_ALL_STREAK_TIMELINE_FUNCTION
    
    rowLines = ""
    currentRowsLines = ""
    for pl in sortedPlayers:
        strkRes,maxStrk           = pl.getCalculatedStreaksFull(1)
        for strk in strkRes:
            hintStr = "<p>&nbsp&nbsp&nbsp<b>%d: %s</b>&nbsp&nbsp&nbsp</p>" \
                      "<p>&nbsp&nbsp&nbsp<b>Sum: %s</b>&nbsp&nbsp&nbsp</p><hr>" \
                      "&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br>" \
                      "<b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.count, strk.formattedNames(), strk.formattedNamesSum(), (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            #hintStr = "<p>&nbsp&nbsp&nbsp<b>%s</b>&nbsp&nbsp&nbsp</p><hr>&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br><b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.names, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            rowLines += "[ '%s', '%d', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % ("%s_kills" % (pl.name), strk.count, hintStr, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))
            
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_kills" % (pl.name))
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_kills" % (pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt    
        
        deathStrkRes,deathMaxStrk = pl.getDeatchStreaksFull(1)
        for strk in deathStrkRes:
            hintStr = "<p>&nbsp&nbsp&nbsp<b>%d: %s</b>&nbsp&nbsp&nbsp</p>" \
                      "<p>&nbsp&nbsp&nbsp<b>Sum: %s</b>&nbsp&nbsp&nbsp</p><hr>" \
                      "&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br>" \
                      "<b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.count, strk.formattedNames(), strk.formattedNamesSum(), (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            #hintStr = "<p>&nbsp&nbsp&nbsp<b>%s</b>&nbsp&nbsp&nbsp</p><hr>&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br><b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.names, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            rowLines += "[ '%s', '%d', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % ("%s_deaths" % (pl.name), strk.count, hintStr, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))
            
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_deaths" % (pl.name))  
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_deaths" % (pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt        
    
    allStreaksTimelineFunctionStr = allStreaksTimelineFunctionStr.replace("ALL_ROWS", rowLines)
    allStreaksTimelineFunctionStr = allStreaksTimelineFunctionStr.replace("CURRENT_ROWS", currentRowsLines)
    
    allStreaksTimelineDivStr = ezstatslib.HTML_SCRIPT_ALL_STREAK_TIMELINE_DIV_TAG
    timelineChartHeight = (len(allplayersByFrags) * 2 + 1) * (33 if len(allplayersByFrags) >= 4 else 35)
    allStreaksTimelineDivStr = allStreaksTimelineDivStr.replace("HEIGHT_IN_PX", str(timelineChartHeight))
    
    # TODO black text color for deaths
    # TODO hints ??    
    # TODO bold players names
    # TODO folding ??
                    
    f.write(allStreaksTimelineFunctionStr)
    # <-- all streaks timeline
    
    # highcharts battle progress -->
    highchartsBattleProgressFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION
            
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "Battle progress")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Frags")
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", "")
        
    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    
    
    hcDelim = "}, {\n"
    rowLines = ""        
    for pl in sortedPlayers:
        if rowLines != "":
            rowLines += hcDelim
        
        rowLines += "name: '%s',\n" % (pl.name)
        # rowLines += "data: [0"
        rowLines += "data: [[0,0]"
        
        graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
        for minEl in matchProgressDictEx:
            # rowLines += ",%d" % (minEl[pl.name])
            rowLines += ",[%f,%d]" % (graphGranularity, minEl[pl.name][0])  # TODO format, now is 0.500000
            graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
            
        rowLines += "]\n"        
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
    f.write(highchartsBattleProgressFunctionStr)
    # <-- highcharts battle progress
    
    # highcharts battle extended progress -->
    highchartsBattleProgressFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("highchart_battle_progress", "highchart_battle_progress_extended")
            
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "Battle progress")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Frags")
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "")    
        
    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \    
    
    hcDelim = "}, {\n"
    rowLines = ""        
    for pl in sortedPlayers:
        if rowLines != "":
            rowLines += hcDelim
        
        rowLines += "name: '%s',\n" % (pl.name)
        # rowLines += "data: [0"
        rowLines += "data: [[0,0]"
                
        # for minEl in matchProgressDictEx2:            
            # rowLines += ",[%d,%d]" % (minEl[pl.name][0], minEl[pl.name][1])  # TODO format, now is 0.500000

        curSec = -1
        curSecVal = -1
        for minEl in matchProgressDictEx2:                        
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSecVal = minEl[pl.name][1]                
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSecVal)

            
        rowLines += "]\n"        
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)
        
    tickPositions = ""
    for k in xrange(matchMinutesCnt*60+1):
        if k % 30 == 0:
            tickPositions += "%d," % (k)
            
    # xAxisLabels = \
        # "labels: {\n" \
        # "     formatter: function () {\n" \
        # "       return (this.value / 60).toFixed(1).toString()\n" \
        # "    },\n" \
        # "},\n"
    # xAxisLabels += "tickPositions: [%s]\n" % (tickPositions)
    
    xAxisLabels = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_TICK_POSITIONS
    xAxisLabels = xAxisLabels.replace("TICK_POSITIONS_VALS", tickPositions)
    
    if isOverTime:
        xAxisLabels += ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_VERTICAL_LINE
        xAxisLabels = xAxisLabels.replace("VERTICAL_LINE_POS", str((minutesPlayedXML-overtimeMinutes)*60))
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", xAxisLabels)
    
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
    f.write(highchartsBattleProgressFunctionStr)
    # <-- highcharts battle extended progress
    
    # highcharts players lifetime -->
    playersLifetimeDivStrs = ""
    for pl in allplayersByFrags:
        playersLifetimeDivStrs += ezstatslib.HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_DIV_TAG.replace("PLAYERNAME", ezstatslib.escapePlayerName(pl.name))
        # playersLifetimeDivStrs += "<br>\n"
    
    highchartsPlayerLifetimeFunctionStrs = ""
    for pl in allplayersByFrags:
        highchartsPlayerLifetimeFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_FUNCTION).replace("PLAYERNAME", ezstatslib.escapePlayerName(pl.name))    
        
        highchartsPlayerLifetimeFunctionStr = highchartsPlayerLifetimeFunctionStr.replace("CHART_TITLE", "%s Lifetime" % (ezstatslib.escapePlayerName(pl.name)))
    
        tickPositions = ""
        for k in xrange(matchMinutesCnt*60+1):
            if k % 30 == 0:
                tickPositions += "%d," % (k)
                    
        xAxisLabels = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_TICK_POSITIONS
        xAxisLabels = xAxisLabels.replace("TICK_POSITIONS_VALS", tickPositions)
        
        highchartsPlayerLifetimeFunctionStr = highchartsPlayerLifetimeFunctionStr.replace("EXTRA_XAXIS_OPTIONS", xAxisLabels)
    
        healthRows = ""
        armorRows = ""
        deathLines = ""
        for lt in pl.lifetime:
            if lt.deathType != ezstatslib.PlayerLifetimeDeathType.NONE:
                deathLine = ezstatslib.HTML_SCRIPT_HIGHCHARTS_PLAYER_LIFETIME_DEATH_LINE_TEMPLATE.replace("LINE_VALUE", str(lt.time))
                
                lineColor = ""
                if lt.deathType == ezstatslib.PlayerLifetimeDeathType.COMMON:
                    lineColor = "red"
                elif lt.deathType == ezstatslib.PlayerLifetimeDeathType.SUICIDE:
                    lineColor = "green"
                elif lt.deathType == ezstatslib.PlayerLifetimeDeathType.TEAM_KILL:
                    lineColor = "purple"
                else:
                    lineColor = "gray"
                    
                deathLine = deathLine.replace("LINE_COLOR", lineColor)
                deathLine = deathLine.replace("LABEL_COLOR", lineColor)
                deathLine = deathLine.replace("LINE_LABEL", lt.killer)
                deathLines += deathLine
                
            else:
                healthRows += "[%f,%d]," % (lt.time,lt.health)
                armorRows  += "[%f,%d]," % (lt.time,lt.armor)
            
        highchartsPlayerLifetimeFunctionStr = highchartsPlayerLifetimeFunctionStr.replace("HEALTH_ROWS", healthRows)
        highchartsPlayerLifetimeFunctionStr = highchartsPlayerLifetimeFunctionStr.replace("ARMOR_ROWS", armorRows)
        highchartsPlayerLifetimeFunctionStr = highchartsPlayerLifetimeFunctionStr.replace("DEATH_LINES", deathLines)
    
        highchartsPlayerLifetimeFunctionStrs += highchartsPlayerLifetimeFunctionStr

    # # tooltip style
    # highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
                
    f.write(highchartsPlayerLifetimeFunctionStrs)
    # <-- highcharts highcharts players lifetime 
    
    # power ups timeline -->
    powerUpsTimelineFunctionStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_FUNCTION
    
    rowLines = ""
    colors = "'gray', "
    for pl in sortedPlayers:
        
        # rowLines += "[ '----> %s <----', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s" % (pl.name))
        rowLines += "[ '----> %s <----', '', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s" % (pl.name))
        
        for pwrup in ["RA","YA","GA","MH"]:
            # rowLines += "[ '%s', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (pl.name, pwrup))
            # rowLines += "[ '%s', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (pl.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (pl.name, pwrup))
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (pl.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt            


        #ezstatslib.logError("pl: %s, powerUpsCnt: %d\n" % (pl.name, len(pl.powerUps)))

        for pu in pl.powerUps:
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d),  new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s_%s" % (pl.name, ezstatslib.powerUpTypeToString(pu.type)), "", ((pu.time-1) / 60), ((pu.time-1) % 60), ((pu.time+1) / 60), ((pu.time+1) % 60))
            
            # TODO check that previous entry is not intersected with the new one: need to store and check lastFinishDate (source data: power_ups_intersection_in_stats)
            
            rowLines += "[ '%s', '', '%s', new Date(2016,1,1,0,%d,%d),  new Date(2016,1,1,0,%d,%d) ],\n" % \
                         ("%s_%s" % (pl.name, ezstatslib.powerUpTypeToString(pu.type)), \
                         " %d min %d sec " % (pu.time / 60, pu.time % 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) / 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) % 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) / 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) % 60) )
            
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s" % (pl.name), ezstatslib.powerUpTypeToString(pu.type), ((pu.time-1) / 60), ((pu.time-1) % 60), ((pu.time+1) / 60), ((pu.time+1) % 60))
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d),  new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s" % (pl.name), ezstatslib.powerUpTypeToString(pu.type), ((pu.time) / 60), ((pu.time) % 60), ((pu.time) / 60), ((pu.time) % 60))
            
            # if pu.type == ezstatslib.PowerUpType.RA: colors += "'%s', " % ("red")
            # if pu.type == ezstatslib.PowerUpType.YA: colors += "'%s', " % ("yellow")
            # if pu.type == ezstatslib.PowerUpType.GA: colors += "'%s', " % ("green")
            # if pu.type == ezstatslib.PowerUpType.MH: colors += "'%s', " % ("#660066")
                        
        # rowLines += "[ '%s', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s" % (pl.name))
        # rowLines += "[ '%s', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s" % (pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt
        
        # colors += "'gray'"
    
    powerUpsTimelineFunctionStr = powerUpsTimelineFunctionStr.replace("ALL_ROWS", rowLines)
    # powerUpsTimelineFunctionStr = powerUpsTimelineFunctionStr.replace("COLORS", colors)    
    
    powerUpsTimelineDivStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_DIV_TAG
    powerUpsTimelineChartHeight = (len(sortedPlayers) * 5 + 1) * (33 if len(sortedPlayers) >= 4 else 35)    
    powerUpsTimelineDivStr = powerUpsTimelineDivStr.replace("HEIGHT_IN_PX", str(powerUpsTimelineChartHeight))        
                    
    f.write(powerUpsTimelineFunctionStr)
    # <-- power ups timeline
    
    # power ups timeline ver2 -->
    powerUpsTimelineVer2FunctionStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_FUNCTION
    
    rowLines = ""
    # colors = "'gray', "
    colors = []
    for col in ["red","yellow","green","#660066"]:
        colors += [col for i in xrange(len(sortedPlayers))]
    colStr = ""
    for col in colors:
        colStr += "'%s'," % (col)
    colStr = colStr[:-1]
    
    for pwrup in ["RA","YA","GA","MH"]:
        for pl in sortedPlayers:
            # rowLines += "[ '%s', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (pl.name, pwrup))
            # rowLines += "[ '%s', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (pl.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (pl.name, pwrup))
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (pl.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt
    
    for pl in sortedPlayers:
        # for pwrup in ["RA","YA","GA","MH"]:
        #     rowLines += "[ '%s', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (pl.name, pwrup))
        #     rowLines += "[ '%s', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (pl.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt

        for pu in pl.powerUps:
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s_%s" % (pl.name, ezstatslib.powerUpTypeToString(pu.type)), "", ((pu.time-1) / 60), ((pu.time-1) % 60), ((pu.time+2) / 60), ((pu.time+2) % 60))
            rowLines += "[ '%s', '', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % \
                        ("%s_%s" % (pl.name, ezstatslib.powerUpTypeToString(pu.type)), \
                         " %d min %d sec " % (pu.time / 60, pu.time % 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) / 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) % 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) / 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) % 60) )
            
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s" % (pl.name), ezstatslib.powerUpTypeToString(pu.type), ((pu.time-1) / 60), ((pu.time-1) % 60), ((pu.time+1) / 60), ((pu.time+1) % 60))
            # rowLines += "[ '%s', '%s', new Date(2016,1,1,0,%d,%d),  new Date(2016,1,1,0,%d,%d) ],\n" % \
            #             ("%s" % (pl.name), ezstatslib.powerUpTypeToString(pu.type), ((pu.time) / 60), ((pu.time) % 60), ((pu.time) / 60), ((pu.time) % 60))
            
            # if pu.type == ezstatslib.PowerUpType.RA: colors += "'%s', " % ("red")
            # if pu.type == ezstatslib.PowerUpType.YA: colors += "'%s', " % ("yellow")
            # if pu.type == ezstatslib.PowerUpType.GA: colors += "'%s', " % ("green")
            # if pu.type == ezstatslib.PowerUpType.MH: colors += "'%s', " % ("#660066")
                        
        # rowLines += "[ '%s', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s" % (pl.name))
        # rowLines += "[ '%s', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s" % (pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt
        
        # colors += "'gray'"
    
    powerUpsTimelineVer2FunctionStr = powerUpsTimelineVer2FunctionStr.replace("ALL_ROWS", rowLines)
    powerUpsTimelineVer2FunctionStr = powerUpsTimelineVer2FunctionStr.replace("COLORS", colStr)    
    
    powerUpsTimelineVer2DivStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_DIV_TAG
    powerUpsTimelineVer2ChartHeight = (len(sortedPlayers) * 4 + 1) * (33 if len(sortedPlayers) >= 4 else 35)    
    powerUpsTimelineVer2DivStr = powerUpsTimelineVer2DivStr.replace("HEIGHT_IN_PX", str(powerUpsTimelineVer2ChartHeight))        
                    
    f.write(powerUpsTimelineVer2FunctionStr)
    # <-- power ups timeline ver2
    
    # players achievements -->
    playersAchievementsStr = ezstatslib.HTML_PLAYERS_ACHIEVEMENTS_DIV_TAG    
    cellWidth = "20px"
    achievementsHtmlTable = HTML.Table(border="0", cellspacing="0",
                                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
    
    for pl in sortedPlayers:
        if len(pl.achievements) != 0:
            tableRow = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold(pl.name), align="center", width=cellWidth) ])  # TODO player name cell width
            for ach in pl.achievements:
                tableRow.cells.append( HTML.TableCell(ach.generateHtmlEx(), align="center" ) )
            
            achievementsHtmlTable.rows.append(tableRow)
        
    playersAchievementsStr = playersAchievementsStr.replace("PLAYERS_ACHIEVEMENTS_TABLE", str(achievementsHtmlTable) + ezstatslib.Achievement.generateAchievementsLevelLegendTable())
    # <-- players achievements
    
    # highcharts players rank progress -->
    highchartsBattleProgressFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION).replace("highchart_battle_progress", "players_rank")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "Players ranks")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Rank")
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", "")
            
    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \        
    
    minRank = 10000
    maxRank = -10000
    hcDelim = "}, {\n"
    rowLines = ""
    for pl in allplayersByFrags:
        if rowLines != "":
            rowLines += hcDelim
        
        rowLines += "name: '%s',\n" % (pl.name)        
        rowLines += "data: [[0,0]"

        curSec = -1
        curSecVal = -1
        for minEl in matchProgressDictEx2:
            minRank = min(minRank, minEl[pl.name][2])
            maxRank = max(maxRank, minEl[pl.name][2])
        
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSecVal = minEl[pl.name][2]
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSecVal)
        
        rowLines += "]\n"

        # add negative zone
        rowLines += ",zones: [{ value: 0, dashStyle: 'ShortDot' }]"
        
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "      min: %d," % (minRank))
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "      max: %d," % (maxRank))        
  
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)    
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)
    
    f.write(highchartsBattleProgressFunctionStr)
    # <-- highcharts players rank progress
    
    # highcharts RL skill -->
    # rlSkillDivStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_RL_SKILL_DIV_TAG
    # rlSkillDivStr = rlSkillDivStr.replace("PLAYERNAME", "dinoel")
    # rlSkillFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_RL_SKILL_FUNCTION_TEMPLATE).replace("PLAYERNAME", "dinoel")    
    
    # rlSkillRowsStr = ""
    # for pl in allplayersByFrags:
        # if pl.name == "dinoel":
          # cnt = len(pl.rl_damages_gvn)
          # val110 = sum(1 for val in pl.rl_damages_gvn if val[0] == 110)
          # val100 = sum(1 for val in pl.rl_damages_gvn if val[0] < 110 and val[0] >= 100)
          # val90  = sum(1 for val in pl.rl_damages_gvn if val[0] < 100 and val[0] >= 90)
          # val75  = sum(1 for val in pl.rl_damages_gvn if val[0] < 90 and val[0] >= 75)
          # val55  = sum(1 for val in pl.rl_damages_gvn if val[0] < 75 and val[0] >= 55)
          # val0   = sum(1 for val in pl.rl_damages_gvn if val[0] < 55 and val[0] >= 0)
          
          # rlSkillRowsStr = "['DirectHit110', %d],\n ['(110,100])', %d],\n ['(100,90]', %d], ['(90,75]', %d], ['(75,55]', %d], ['(55,0]', %d]" % (val110, val100, val90, val75, val55, val0)

    # rlSkillFunctionStr = rlSkillFunctionStr.replace("CHART_TITLE", "dinoel<br>(%d)" % (cnt))
  
    # rlSkillFunctionStr = rlSkillFunctionStr.replace("ADD_ROWS", rlSkillRowsStr)
    # f.write(rlSkillFunctionStr)
    # <-- highcharts RL skill

    # <-- highcharts players rank progress
    
    # highcharts RL skill -->
    # div
    rlSkillDivStrs = ""
    rowsCount = (len(allplayersByFrags) / 3) + (0 if len(allplayersByFrags) % 3 == 0 else 1)
    
    print "rowsCount", rowsCount
    
    for rowNum in xrange(rowsCount):
        rlSkillDivStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_RL_SKILL_DIV_AND_TABLE_TAG
        tableRowsStr = ""
        currentRowCount = 3 if rowNum < (rowsCount-1) or len(allplayersByFrags) % 3 == 0 else len(allplayersByFrags) % 3
        percentsVal = 100 / currentRowCount
        for j in xrange(currentRowCount):
           tRowStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_RL_SKILL_TABLE_ROW
           tRowStr = tRowStr.replace("PLAYERNAME", ezstatslib.escapePlayerName(allplayersByFrags[j+rowNum*3].name))
           tRowStr = tRowStr.replace("TD_WIDTH", "%d" % (percentsVal))
           tableRowsStr += tRowStr
           
        rlSkillDivStr = rlSkillDivStr.replace("TABLE_ROWS", tableRowsStr)
        rlSkillDivStrs += rlSkillDivStr
    
    for pl in allplayersByFrags:
        rlSkillFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_RL_SKILL_FUNCTION_TEMPLATE).replace("PLAYERNAME", ezstatslib.escapePlayerName(pl.name))    
       
        cnt = len(pl.rl_damages_gvn)
        val110 = sum(1 for val in pl.rl_damages_gvn if val[0] == 110)
        val100 = sum(1 for val in pl.rl_damages_gvn if val[0] < 110 and val[0] >= 100)
        val90  = sum(1 for val in pl.rl_damages_gvn if val[0] < 100 and val[0] >= 90)
        val75  = sum(1 for val in pl.rl_damages_gvn if val[0] < 90 and val[0] >= 75)
        val55  = sum(1 for val in pl.rl_damages_gvn if val[0] < 75 and val[0] >= 55)
        val0   = sum(1 for val in pl.rl_damages_gvn if val[0] < 55 and val[0] >= 0)
        
        rlSkillRowsStr = "['DirectHit110', %d],\n ['(110,100])', %d],\n ['(100,90]', %d], ['(90,75]', %d], ['(75,55]', %d], ['(55,0]', %d]" % (val110, val100, val90, val75, val55, val0)

      # ['DirectHit110', 26.79],
      # ['(110,100])', 0],
      # ['(100,90]', 9.92],
      # ['(90,75]', 26.78],
      # ['(75,55]', 26.78],
      # ['(55,0]', 10.71],

        rlSkillFunctionStr = rlSkillFunctionStr.replace("CHART_TITLE", "%s<br>(%d / %d)" % (pl.name, cnt, pl.rl_attacks))
        rlSkillFunctionStr = rlSkillFunctionStr.replace("ADD_ROWS", rlSkillRowsStr)
        f.write(rlSkillFunctionStr)
    # <-- highcharts RL skill
    


    # write expand/collapse function
    f.write(ezstatslib.HTML_EXPAND_CHECKBOX_FUNCTION)
    f.write(ezstatslib.HTML_EXPAND_POWER_UPS_CHECKBOX_FUNCTION)
    
    f.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)
    
    # add divs
    resStr = resStr.replace("BP_PLACE", ezstatslib.HTML_BATTLE_PROGRESS_DIV_TAG)
    #resStr = resStr.replace("MAIN_STATS_PLACE", ezstatslib.HTML_MAIN_STATS_DIAGRAMM_DIV_TAG)
    resStr = resStr.replace("MAIN_STATS_BARS_PLACE", ezstatslib.HTML_MAIN_STATS_BARS_DIV_TAG)    
    resStr = resStr.replace("PLAYERS_ACHIEVEMENTS_PLACE", playersAchievementsStr)
    resStr = resStr.replace("POWER_UPS_BARS_PLACE", ezstatslib.HTML_POWER_UPS_BARS_DIV_TAG)
    resStr = resStr.replace("STREAK_TIMELINE_PLACE", ezstatslib.HTML_SCRIPT_STREAK_TIMELINE_DIV_TAG)
    resStr = resStr.replace("STREAK_ALL_TIMELINE_PLACE", allStreaksTimelineDivStr)
    # resStr = resStr.replace("HIGHCHART_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG)
    resStr = resStr.replace("HIGHCHART_BATTLE_PROGRESS_PLACE", "")
    resStr = resStr.replace("HIGHCHART_EXTENDED_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_EXTENDED_BATTLE_PROGRESS_DIV_TAG)
    resStr = resStr.replace("HIGHCHART_POWER_UPS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_POWER_UPS_DIVS_TAG)
    resStr = resStr.replace("POWER_UPS_TIMELINE_PLACE", powerUpsTimelineDivStr)
    resStr = resStr.replace("POWER_UPS_TIMELINE_VER2_PLACE", powerUpsTimelineVer2DivStr)
    resStr = resStr.replace("HIGHCHART_PLAYERS_RANK_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_DEATHMATCH_PLAYERS_RANK_PROGRESS_DIV_TAG)    
    resStr = resStr.replace("HIGHCHART_RL_SKILL_PLACE", rlSkillDivStrs)
    resStr = resStr.replace("HIGHCHART_PLAYER_LIFETIME_PLACE", playersLifetimeDivStrs)
    
    f.write(resStr)
    
    f.write(ezstatslib.HTML_PRE_CLOSE_TAG)
    
    # add script section for folding
    f.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)    
    
    f.write(ezstatslib.HTML_FOOTER_NO_PRE)

# check and write output file
leaguePrefix = ""
if "Premier" in options.leagueName:
    leaguePrefix = "PL_"
if "First" in options.leagueName:
    leaguePrefix = "FD_"
if "Second" in options.leagueName:
    leaguePrefix = "SD_"
if "Number" in options.leagueName:    
    leaguePrefix = "N%s_" % (options.leagueName.split(" ")[1])

formatedDateTime = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d_%H_%M_%S')
filePath     = leaguePrefix + mapName + "_" + formatedDateTime + ".html"
filePathFull = ezstatslib.REPORTS_FOLDER + filePath

isFileNew = False
if os.path.exists(filePathFull):
    # temp file 
    tmpFilePathFull = "../" + filePath + ".tmp"
    if os.path.exists(tmpFilePathFull):        
        os.remove(tmpFilePathFull)
    
    tmpf = open(tmpFilePathFull, "w")
    
    if not options.withScripts:
        tmpf.write(ezstatslib.HTML_HEADER_STR)
        tmpf.write(resultString)
        tmpf.write(ezstatslib.HTML_FOOTER_STR)
    else:
        writeHtmlWithScripts(tmpf, allplayersByFrags, resultString)  
    
    tmpf.close()
    
    tmpinfo = os.stat(tmpFilePathFull)
    finfo   = os.stat(filePathFull)
    
    isSizesEqual = tmpinfo.st_size == finfo.st_size
    
    if isSizesEqual:
        os.remove(tmpFilePathFull)
    else:
        os.remove(filePathFull)
        os.rename(tmpFilePathFull, filePathFull)

else:  # not os.path.exists(filePathFull):
    outf = open(filePathFull, "w")
    
    if not options.withScripts:
        outf.write(ezstatslib.HTML_HEADER_STR)
        outf.write(resultString)
        outf.write(ezstatslib.HTML_FOOTER_STR)
    else:    
        writeHtmlWithScripts(outf, allplayersByFrags, resultString)
    
    outf.close()
    isFileNew = True
    
# update contents file
logsIndexPath    = ezstatslib.REPORTS_FOLDER + ezstatslib.LOGS_INDEX_FILE_NAME
logsByMapPath    = ezstatslib.REPORTS_FOLDER + ezstatslib.LOGS_BY_MAP_FILE_NAME
tmpLogsIndexPath = ezstatslib.REPORTS_FOLDER + ezstatslib.LOGS_INDEX_FILE_NAME + ".tmp"
totalsPath       = ezstatslib.REPORTS_FOLDER + ezstatslib.TOTALS_FILE_NAME

files = os.listdir(ezstatslib.REPORTS_FOLDER)

#headerRow = HTML.TableRow(["Date", "Time", "Premier League", "First Division", "Second Division"], header=True)

headerRow = HTML.TableRow(cells=[], header=True)
attrs = {} # attribs    
attrs['colspan'] = 2
headerRow.cells.append( HTML.TableCell("Date", header=True) )
headerRow.cells.append( HTML.TableCell("Time", header=True) )
headerRow.cells.append( HTML.TableCell("Premier League", attribs=attrs, header=True) )
headerRow.cells.append( HTML.TableCell("First Division", attribs=attrs, header=True) )
headerRow.cells.append( HTML.TableCell("Second Division", attribs=attrs, header=True) )

filesTable = HTML.Table(header_row=headerRow, border="1", cellspacing="3", cellpadding="8")

filesMap = {}  # key: dt, value: [[ [PL1,dt],[PL2,dt],..],[ [FD1,dt], [FD2,dt],.. ],[ [SD1,dt], [SD2,dt],.. ]]

zerodt = datetime(1970,1,1)
filesMap[zerodt] = [[],[],[]]  # files with problems

otherFiles = []

for fname in files:
    if "html" in fname and len(fname) != 0 and fname[0] == "N":
        logHeadStr = subprocess.check_output(["head.exe", "%s" % (ezstatslib.REPORTS_FOLDER + fname)])  # TODO check for win vs. linux
        if "GAME_PLAYERS" in logHeadStr:
            playsStr = logHeadStr.split("GAME_PLAYERS")[1].split("-->")[0]
                
        plays = []
        if playsStr != "":
            playsStr = playsStr.replace("\n","")
            plays = playsStr.split(" ")
        
        otherFiles.append([fname, plays])
        
    
    elif "html" in fname and ("PL" in fname or "FD" in fname or "SD" in fname):
                
        #"PL_[dad2]_2016-05-23_18_45_16.html"
        #nameSplit = fname.split("_")  # ['PL', '[dad2]', '2016-05-23', '18', '45', '16.html']
        #dateSplit = nameSplit[2].split("-")        
        
        dateRes = re.search("(?<=]_).*(?=.html)", fname)
                
        if dateRes:
            try:
                dt = datetime.strptime(dateRes.group(0), "%Y-%m-%d_%H_%M_%S")
                dateStruct = datetime.strptime(dateRes.group(0).split("_")[0], "%Y-%m-%d")
            
                if not dateStruct in filesMap.keys(): # key exist
                    filesMap[dateStruct] = [[],[],[]]
                    
                fnamePair = [fname,dt]
                    
                if "PL" in fname:
                    filesMap[dateStruct][0].append(fnamePair)
                elif "FD" in fname:
                    filesMap[dateStruct][1].append(fnamePair)
                else: # SD
                    filesMap[dateStruct][2].append(fnamePair)
            except Exception, ex:
                if "PL" in fname:
                    filesMap[zerodt][0].append(fnamePair)
                elif "FD" in fname:
                    filesMap[zerodt][1].append(fnamePair)
                else: # SD
                    filesMap[zerodt][2].append(fnamePair)
                break;
                
        else: # date parse failed
            if "PL" in fname:
                filesMap[zerodt][0].append(fnamePair)
            if "FD" in fname:
                filesMap[zerodt][1].append(fnamePair)
            else: # SD
                filesMap[zerodt][2].append(fnamePair)
        
        
        # if isFileNew and filePath == fname:
        #     tableRow = HTML.TableRow(cells=[ HTML.TableCell("<a href=\"" + fname + "\">" + fname + "</a>" + newGifTag + "<br>\n") ])
        # else:
        #     tableRow = HTML.TableRow(cells=[ HTML.TableCell("<a href=\"" + fname + "\">" + fname + "</a>" + "<br>\n") ])
        # filesTable.rows.append(tableRow)
        # modTime = os.stat("../" + fname).st_mtime # TODO newGifTag <-> modTime

# IDEA: http://codepen.io/codyhouse/pen/FdkEf
# IDEA: http://codepen.io/jenniferperrin/pen/xfwab

def generateHtmlList(playersNames):
    if len(playersNames) == 0:
        return ""
    
    fontSize = 8
    styleHeightStr = ""
    # workaround for web kit bug with select tag size - size less than 4 is ignored
    if len(playersNames) < 4:
        styleHeightStr = "; height:%dpt" % (fontSize*len(playersNames) + 6)    
    
    htmlList = "<select style=\"font-family: Helvetica; font-size: %dpt%s\" name=\"select\" size=\"%d\" multiple=\"multiple\" title=\"OLOLOLO\">\n" % (fontSize, styleHeightStr, len(playersNames))
    i = 0
    for pl in playersNames:
        htmlList += "<option>%s</option>\n" % (pl)
        #htmlList += "<option%s>%s</option>\n" % (" selected" if i < 2 else "", pl)
        i += 1
        
    htmlList += "</select>\n"
    return htmlList

sorted_filesMap = sorted(filesMap.items(), key=itemgetter(0), reverse=True)

filesByMapDict = {} # key: mapname, value: [ [legue, date, players], ..]

for el in sorted_filesMap: # el: (datetime.datetime(2016, 5, 5, 0, 0), [[], [ ['FD_[spinev2]_2016-05-05_16_12_52.html',dt1], ['FD_[skull]_2016-05-05_13_38_11.html',dt2]]])
    formattedDate = el[0]
    if el[0] != zerodt:
        formattedDate = el[0].strftime("%Y-%m-%d")
    
    pls = el[1][0] # array, val: [str,dt]
    fds = el[1][1] # array, val: [str,dt]
    sds = el[1][2] # array, val: [str,dt]
    
    pls = sorted(pls, key=lambda x: x[1], reverse=True)
    fds = sorted(fds, key=lambda x: x[1], reverse=True)
    sds = sorted(sds, key=lambda x: x[1], reverse=True)
    
    alllist = pls + fds + sds
    alllist = sorted(alllist, key=lambda x: x[1], reverse=True)
    
    #maxcnt = max(len(fds), len(pls), len(sds))
    sumcnt = len(fds) + len(pls) + len(sds)
    
    tableRow = HTML.TableRow(cells=[ HTML.TableCell(formattedDate) ])
    fullTimeRowIndex = len(filesTable.rows)
        
    # TODO checkbox for hiding textareas with players
    # TODO baloons instead of textareas
    # TODO may be textareas are sensible only for several recent matches
    
    i = 0
    TIME_DELTA = 15*60
    isNewRow = True
    rowspanVal = 0
    rowMask = [0,0,0]
    for i in xrange(sumcnt):
        formattedTime = alllist[i][1].strftime("%H-%M-%S")
        formattedTimeNoSec = alllist[i][1].strftime("%H-%M")
        currentMapName = alllist[i][0].split("_")[1]        
        
        if isNewRow:
            rowMask = [0,0,0]
            minTime = alllist[i][1]
            maxTime = alllist[i][1]
                            
            if i != 0:        
                tableRow = HTML.TableRow(cells=[formattedTime])
            else:
                tableRow.cells.append( HTML.TableCell(formattedTime) )
        
            for j in xrange(3):
                tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
                tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        
        minTime = min(minTime, alllist[i][1])
        maxTime = max(maxTime, alllist[i][1])
        
        isP = alllist[i][0][0] == "P"
        isF = alllist[i][0][0] == "F"
        isS = alllist[i][0][0] == "S"
        
        # get log players        
        playsStr = ""
        # logf = open("../" + alllist[i][0], "r")
        # linesCnt = 0        
        
        logHeadStr = subprocess.check_output(["head.exe", "%s" % (ezstatslib.REPORTS_FOLDER + alllist[i][0])])  # TODO check for win vs. linux
        if "GAME_PLAYERS" in logHeadStr:
            playsStr = logHeadStr.split("GAME_PLAYERS")[1].split("-->")[0]
                
        plays = []
        if playsStr != "":
            playsStr = playsStr.replace("\n","")
            plays = playsStr.split(" ")
        
        if not filesByMapDict.has_key(currentMapName):
            filesByMapDict[currentMapName] = []
            
        filesByMapDict[currentMapName].append([alllist[i][0][0], str(alllist[i][1]), plays, playsStr, alllist[i][0]] )
                
        if isP: insertIndex = len(tableRow.cells) - 6
        if isF: insertIndex = len(tableRow.cells) - 4
        if isS: insertIndex = len(tableRow.cells) - 2
        
        if isP: rowMask[0] = 1
        if isF: rowMask[1] = 1
        if isS: rowMask[2] = 1
        
        tableRow.cells[insertIndex] = HTML.TableCell( htmlLink(alllist[i][0],
                                                     newGifTag if checkNew(isFileNew, filePath, alllist[i][0]) else ""),
                                                     style="border-right-width:0")
        tableRow.cells[insertIndex+1] = HTML.TableCell( generateHtmlList(plays), style="border-left-width:0" )
                        
        # check next
        if i+1 < sumcnt:
            formattedTimeNoSecNext = alllist[i+1][1].strftime("%H-%M")
            currentMapNameNext = alllist[i+1][0].split("_")[1]
            
            if currentMapNameNext == currentMapName \
               and ( int(time.mktime(alllist[i][1].timetuple())) - int(time.mktime(alllist[i+1][1].timetuple())) ) < TIME_DELTA:
                isNewRow = False
            else:
                isNewRow = True
            
            isPNext = alllist[i+1][0][0] == "P"
            isFNext = alllist[i+1][0][0] == "F"
            isSNext = alllist[i+1][0][0] == "S"
                
            if isPNext and rowMask[0] == 1: isNewRow = True
            if isFNext and rowMask[1] == 1: isNewRow = True
            if isSNext and rowMask[2] == 1: isNewRow = True
        else:
            isNewRow = True
        
        if isNewRow:
            # correct time cell
            if minTime != maxTime:
                tableRow.cells[len(tableRow.cells)-7] = "%s\n    - \n%s" % (minTime.strftime("%H-%M-%S"), maxTime.strftime("%H-%M-%S"))
            
            filesTable.rows.append(tableRow)
            rowspanVal += 1
            
        i += 1          
    
    # set rowspan attribute of full time cell
    if rowspanVal != 0:
        attrs = {} # attribs
        attrs['rowspan'] = rowspanVal
        filesTable.rows[fullTimeRowIndex].cells[0].attribs = attrs
        
            
        # if isP:
        #     tableRow.cells.append( HTML.TableCell( htmlLink(alllist[i][0],
        #                                            newGifTag if checkNew(isFileNew, filePath, alllist[i][0]) else ""),
        #                                            style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell( generateHtmlList(plays), style="border-left-width:0" ) )
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        #     
        # if isF:
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        #     tableRow.cells.append( HTML.TableCell( htmlLink(alllist[i][0],
        #                                            newGifTag if checkNew(isFileNew, filePath, alllist[i][0]) else ""),
        #                                            style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell( generateHtmlList(plays), style="border-left-width:0" ) )
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        # 
        # if isS:
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell("", style="border-left-width:0") )
        #     tableRow.cells.append( HTML.TableCell( htmlLink(alllist[i][0],
        #                                            newGifTag if checkNew(isFileNew, filePath, alllist[i][0]) else ""),
        #                                            style="border-right-width:0") )
        #     tableRow.cells.append( HTML.TableCell( generateHtmlList(plays), style="border-left-width:0" ) )
        #     
        # filesTable.rows.append(tableRow)
        # i += 1
    
    # i = 0
    # for i in xrange(maxcnt):
    #     if i != 0:
    #         tableRow = HTML.TableRow(cells=[])
    #     
    #     if i < len(pls): # PLs
    #         tableRow.cells.append( HTML.TableCell( htmlLink(pls[i][0],
    #                                                newGifTag if checkNew(isFileNew, filePath, pls[i][0]) else "") ) )
    #     else: # no PLs
    #         tableRow.cells.append( HTML.TableCell("") )
    #         
    #     if i < len(fds): # FDs
    #         tableRow.cells.append( HTML.TableCell( htmlLink(fds[i][0],
    #                                                newGifTag if checkNew(isFileNew, filePath, fds[i][0]) else "") ) )            
    #     else: # no FDs
    #         tableRow.cells.append( HTML.TableCell("") )
    #         
    #     if i < len(sds): # SDs
    #         tableRow.cells.append( HTML.TableCell( htmlLink(sds[i][0],
    #                                                newGifTag if checkNew(isFileNew, filePath, sds[i][0]) else "") ) )            
    #     else: # no SDs
    #         tableRow.cells.append( HTML.TableCell("") )
    #         
    #     filesTable.rows.append(tableRow)
    #     i += 1

filesByMapTable = HTML.Table(border="1", cellspacing="1", style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 8pt;")

for filemap in filesByMapDict.keys():
    maxCnt = 0
    
    tableRow = HTML.TableRow(cells=[])
        
    tableRow.cells.append( HTML.TableCell("%s(%d)" % (filemap, len(filesByMapDict[filemap])), align="center") )
        
    for el in filesByMapDict[filemap]:
        maxCnt = max(maxCnt, len(el[2]))    
        tableRow.cells.append( HTML.TableCell("<a href=\"%s\">%s %s</a>" % (el[4], ezstatslib.htmlBold(el[0]), el[1]), align="center") )
    
    filesByMapTable.rows.append( tableRow )
        
    for cnt in xrange(maxCnt):
        tRow = HTML.TableRow(cells=[""])
                
        for el in filesByMapDict[filemap]:
            tRow.cells.append( HTML.TableCell("%s" % (el[2][cnt] if len(el[2]) > cnt else ""), align="center") )
        
        filesByMapTable.rows.append( tRow )

logsf = open(logsByMapPath, "w")
logsf.write(ezstatslib.HTML_HEADER_STR)
logsf.write(str(filesByMapTable))
logsf.write(ezstatslib.HTML_FOOTER_STR)
logsf.close()


logsf = open(tmpLogsIndexPath, "w")
logsf.write(ezstatslib.HTML_HEADER_STR)
# logsf.write(htmlLink(ezstatslib.TOURNAMENT_TABLE_FILE_NAME, linkText = "AdRiver Quake tournament 2016"))
# logsf.write("<hr>")
logsf.write(htmlLink(ezstatslib.LOGS_BY_MAP_FILE_NAME, linkText = "Match results by maps"))
logsf.write("<hr>")
logsf.write(htmlLink(ezstatslib.TEAM_LOGS_INDEX_FILE_NAME, linkText = "Team matches logs"))
logsf.write("<hr>")
logsf.write(htmlLink(ezstatslib.TOTALS_FILE_NAME, linkText = "Totals"))
logsf.write("<hr>")
logsf.write(str(filesTable))

logsf.write("<hr>")
logsf.write("<h1>Duels</h1>")
for fileName in otherFiles:
    logsf.write( htmlLink(fileName[0], isBreak = False) )
    logsf.write( generateHtmlList(fileName[1]) )
logsf.write("<hr>")

logsf.write(ezstatslib.HTML_FOOTER_STR)
logsf.close()

if os.path.exists(logsIndexPath):
    os.remove(logsIndexPath)
os.rename(tmpLogsIndexPath, logsIndexPath)

# save to json
def encode_Player(pl):
    # if isinstance(z, complex):
        # return (z.real, z.imag)
    # else:
        # type_name = z.__class__.__name__
        # raise TypeError(f"Object of type '{type_name}' is not JSON serializable")
	# return (pl.name, pl.frags, pl.ga, pl.suicides)
	if isinstance(pl, Player):
		return {"name":pl.name, "frags":pl.frags(), "ga":pl.ga, "suicides":pl.suicides, "deaths":pl.deaths, "ya":pl.ya, "ra":pl.ra, "mh":pl.mh}
		# return (pl.name, pl.frags(), pl.ga, pl.suicides)

str = "["
# json.dump(allplayersByFrags, write_file, default=encode_Player)
for pl in allplayersByFrags:
	if str != "[":
		str += ','
	str += json.dumps(pl, default=encode_Player, indent=4)	
str += "]"

# with open("data_file.json", "w") as write_file:    
	# for pl in allplayersByFrags:
		# json.dump(pl, write_file, default=encode_Player, indent=4)	

# print str

jsonPath =  filePathFull.replace(ezstatslib.REPORTS_FOLDER, ezstatslib.REPORTS_FOLDER + "json/")
jsonPath += ".json"
jsonf = open(jsonPath, "w")  # TODO check and create folder if needed
jsonf.write(str)
jsonf.close()
	
ooo = json.loads(str)

print ooo
for oo in ooo:
	print oo
	for o in oo:
		print o, ":", oo[o]
	
print filePath    

jsonDirPath = ezstatslib.REPORTS_FOLDER + "json/"
entries = (os.path.join(jsonDirPath, fn) for fn in os.listdir(jsonDirPath))
entries = ((os.stat(path), path) for path in entries if ".json" in path)

entries = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))

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
		
		self.matchesPlayed = 0
		
		self.fragsByMatches = []
		self.fragsByMatchesPairs = []
		
		self.rankByMatches = []
		self.rankByMatchesPairs = []

jsonPlayers = []
allCDates = set()
	
for cdate, size, path in sorted(entries, reverse=False):
    #print time.ctime(cdate), size, os.path.basename(path)	
	print "AAA", cdate, size, path
	
	dateRes = re.search("(?<=]_).*(?=.html.json)", path)                  
	dt = datetime.strptime(dateRes.group(0), "%Y-%m-%d_%H_%M_%S")
	dateStruct = datetime.strptime(dateRes.group(0).split("_")[0], "%Y-%m-%d")
	
	allCDates.add(dt)	
	
	with open(path, 'r') as f:
		jsonStrRead = json.load(f)
		print "JJJ", jsonStrRead
		for oo in jsonStrRead:
			currentJsonPlayer = JsonPlayer()
			currentJsonPlayer.matchesPlayed = 1
			for o in oo:
				print o, ":", oo[o]
				# exec("currentJsonPlayer.%s = %s" % (o, oo[o]))
				if o == "name":
					currentJsonPlayer.name = oo[o]
				if o == "frags":
					currentJsonPlayer.frags = oo[o]
				if o == "suicides":
					currentJsonPlayer.suicides = oo[o]
				if o == "ga":
					currentJsonPlayer.ga = oo[o]
				if o == "ya":
					currentJsonPlayer.ya = oo[o]
				if o == "ra":
					currentJsonPlayer.ra = oo[o]
				if o == "mh":
					currentJsonPlayer.mh = oo[o]
				if o == "deaths":
					currentJsonPlayer.deaths = oo[o]

				
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
					plJson.fragsByMatches.append(currentJsonPlayer.frags)
					plJson.fragsByMatchesPairs.append([dt, currentJsonPlayer.frags])
					plJson.rankByMatches.append(currentJsonPlayer.frags-currentJsonPlayer.deaths)
					plJson.rankByMatchesPairs.append([dt, currentJsonPlayer.frags-currentJsonPlayer.deaths])
	
			if not isFound:
				currentJsonPlayer.fragsByMatches.append(currentJsonPlayer.frags)
				currentJsonPlayer.fragsByMatchesPairs.append([dt, currentJsonPlayer.frags])
				currentJsonPlayer.rankByMatches.append(currentJsonPlayer.frags-currentJsonPlayer.deaths)
				currentJsonPlayer.rankByMatchesPairs.append([dt, currentJsonPlayer.frags-currentJsonPlayer.deaths])
				jsonPlayers.append(currentJsonPlayer)

				
				
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
	totalsStr += "\tavg per match: frags:%f, deaths: %f, suicides: %f, ga: %f, ya: %f, ra: %f, mh: %f" % (float(plJson.frags)/plJson.matchesPlayed, float(plJson.deaths)/plJson.matchesPlayed, float(plJson.suicides)/plJson.matchesPlayed, float(plJson.ga)/plJson.matchesPlayed, float(plJson.ya)/plJson.matchesPlayed, float(plJson.ra)/plJson.matchesPlayed, float(plJson.mh)/plJson.matchesPlayed)
	totalsStr += "<br>\n"
	totalsStr += "frags by matches: %s" % (plJson.fragsByMatches)
	totalsStr += "<hr>\n"
				
logsf = open(totalsPath, "w")
#logsf.write(ezstatslib.HTML_HEADER_STR)


pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
#pageTitle = "%s %s %s" % (options.leagueName, mapName, matchdate)  # global values
pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", "TOTALS")
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

print "allCDates.size =", len(allCDates)

for pl in jsonPlayers:
	print "count:", len(pl.fragsByMatches)
	
print allCDates
print sorted(allCDates)

print "isOverTime:", isOverTime
print "timelimit:", timelimit
print "duration:", duration
print "minutesPlayedXML:", minutesPlayedXML
        
