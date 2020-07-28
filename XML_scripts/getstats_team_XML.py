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

import random

import xml.etree.ElementTree as ET
import json

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
		
def deltaToString(delta):
    deltaStr = ""
    if delta == 0:
        deltaStr = "<sup>0  </sup>"
    else:
        if delta > 0:
            deltaStr = "<sup>+%d%s</sup>" % (delta, " " if delta < 10 else "")
        else:
            deltaStr = "<sup>%d%s</sup>"  % (delta, " " if delta < 10 else "")
    return deltaStr

plPrevFragsDict = {}
    
def getFragsLine(players):
    playersByFrags = sorted(players, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
    s = "[%s]TEAM_DELTA" % (players[0].teamname)

    fragsSum = 0
    for pl in playersByFrags:
        fragsSum += pl.frags()
    s += " {0:3d}: ".format(fragsSum)

    teamFragsDelta = 0
    for pl in playersByFrags:
        if not pl.name in plPrevFragsDict.keys():
            plFragsDelta = pl.frags()
        else:
            plFragsDelta = pl.frags() - plPrevFragsDict[pl.name]
        plPrevFragsDict[pl.name] = pl.frags()

        teamFragsDelta += plFragsDelta
        deltaStr = deltaToString(plFragsDelta)
        s += ( "{0:%ds}" % (20+len(deltaStr)) ).format(pl.name + "(" + str(pl.frags()) + ")" + deltaStr)
    
    s = s.replace("TEAM_DELTA", deltaToString(teamFragsDelta))
    s = s[:-1]

    return s

def fillExtendedBattleProgress():
    s = getFragsLine(players1)
    s += " vs. "
    s += getFragsLine(players2)
    extendedProgressStr.append(s)

usageString = ""
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("-f",        action="store",       dest="inputFile",      type="str",  metavar="LOG_FILE", help="")
parser.add_option("--fxml",   action="store",       dest="inputFileXML",      type="str",  metavar="LOG_FILE_XML", help="")
parser.add_option("--fjson",   action="store",       dest="inputFileJSON",      type="str",  metavar="LOG_FILE_JSON", help="")
parser.add_option("--net-log", action="store_true",  dest="netLog",         default=False,                   help="")
parser.add_option("--scripts", action="store_false",   dest="withScripts", default=True,   help="")
parser.add_option("--net-copy", action="store_true",   dest="netCopy", default=False,   help="")

(options, restargs) = parser.parse_args()

# check rest arguments
if len(restargs) != 0:
    parser.error("incorrect parameters count(%d)" % (len(restargs)))
    exit(0)

    
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

matchdateLog = ""    
    
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
                matchdateLog += "ev.text = " + ev.text + "\n"
            
                if "Russia" in ev.text:
                    matchdate = ev.text.split(" Russia")[0]
                    matchdateLog += "I matchdate = " + matchdate + "\n"
                else:
                    correctionHours = 2
                    try:
                        matchdate = ev.text.split(" Eur")[0]
                        matchdateLog += "II matchdate = " + matchdate + "\n"
                        dt = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S')
                        correctionHours = 3
                    except:
                        datesplit = ev.text.split(" ")
                        matchdate = datesplit[0] + " " + datesplit[1]
                        matchdateLog += "III matchdate = " + matchdate + "\n"
                        dt = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S')
                        if "CEST" in ev.text:
                            correctionHours = 1

                    dtcorrected = dt + timedelta(hours=correctionHours)
                    matchdate = dtcorrected.strftime('%Y-%m-%d %H:%M:%S')
                    matchdateLog += "RESULT: matchdate = " + matchdate + "\n"
                    
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

                    if elem.target == None or elem.attacker == None:
                        continue
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

        # print "%f  %s -> %s  %d \"%d\" splash: %d" % (elem.time, elem.attacker, elem.target, elem.armor, elem.value, elem.splash)

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
    # #print "%f  %s -> %s  \"%s\"  %f" % (elem.time, elem.attacker, elem.target, elem.type, elem.lifetime)
    # #print "%f" % (elem.lifetime)

    if int(elem.time) == minutesPlayedXML*60:
        elem.time = minutesPlayedXML*60 - 1  # correction for events in the match end with timestamp more than minPlayed*60

    for pl in xmlPlayers:
        if pl.name == elem.player:
            if not elem.isArmor and not elem.isMH:
                if "item_" in elem.item:
                    itemName = elem.item.replace("item_", "")
                    if not itemName in pl.pickups_items.keys():
                        pl.pickups_items[itemName] = 1
                    else:
                        pl.pickups_items[itemName] += 1
                elif "weapon_" in elem.item:
                    weaponName = elem.item.replace("weapon_", "")
                    if not weaponName in pl.pickups_weapons.keys():
                        pl.pickups_weapons[weaponName] = 1
                    else:
                        pl.pickups_weapons[weaponName] += 1
                elif "health_15" == elem.item or "health_25" == elem.item:
                    exec("pl.%s_cnt += 1;" % (elem.item))
                    
            # if elem.isArmor:
                # if elem.armorType == ezstatslib.PowerUpType.RA:
                    # pl.raXML += 1
                    # pl.incraXML(int(elem.time))
                # if elem.armorType == ezstatslib.PowerUpType.YA:
                    # pl.yaXML += 1
                    # pl.incyaXML(int(elem.time))
                # if elem.armorType == ezstatslib.PowerUpType.GA:
                    # pl.gaXML += 1
                    # pl.incgaXML(int(elem.time))

            # if elem.isMH:
                # pl.mhXML += 1
                # pl.incmhXML(int(elem.time))

# for pl in xmlPlayers:
    # print "Player \"%s\": kills:  %d, deaths:  %d, suicides:  %d, spawns:  %d, ga: %d, ya: %d, ra: %d, mh: %d" % (pl.name, pl.killsXML, pl.deathsXML, pl.suicidesXML, pl.spawnFragsXML, pl.gaXML, pl.yaXML, pl.raXML, pl.mhXML)
    # print "    ga: %s" % (pl.gaByMinutesXML)
    # print "    ya: %s" % (pl.yaByMinutesXML)
    # print "    ra: %s" % (pl.raByMinutesXML)
    # print "    mh: %s" % (pl.mhByMinutesXML)    

timelimit = -1
duration = -1
isOverTime = False
overtimeMinutes = -1
rlAttacksByPlayers = {}

# open json    
jsonPlayers = []
with open(options.inputFileJSON, 'r') as fjson:
    jsonStrRead = json.load(fjson)
    teamName1 = jsonStrRead["players"][0]["team"]
    team1 = Team(teamName1)
    
    timelimit = int(jsonStrRead["tl"])
    duration = int(jsonStrRead["duration"])
    
    for i in xrange(len(jsonStrRead["players"])):
        if jsonStrRead["players"][i]["team"] != teamName1:
            teamName2 = jsonStrRead["players"][i]["team"]
            team2 = Team(teamName2)
    
        pl = Player( jsonStrRead["players"][i]["team"], jsonStrRead["players"][i]["name"], 0, 0, 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
        pl.initPowerUpsByMinutes(minutesPlayedXML)
        rlAttacksByPlayers[pl.name] = jsonStrRead["players"][i]["weapons"]["rl"]["acc"]["attacks"];
        
        pl.speed_max = jsonStrRead["players"][i]["speed"]["max"];
        pl.speed_avg = jsonStrRead["players"][i]["speed"]["avg"];
        
        jsonPlayers.append(pl)

    isOverTime = minutesPlayedXML != timelimit;
    overtimeMinutes = minutesPlayedXML - timelimit
        
for pl in jsonPlayers:
    print pl.name, " - ", pl.teamname     
  
matchlog = []
isStart = False
isEnd = False

teamNames = []
matchProgressDict = []
matchProgressPlayers1Dict = []
matchProgressPlayers2Dict = []

matchProgressDictEx = []
matchProgressPlayers1DictEx = []
matchProgressPlayers2DictEx = []

matchProgressDictEx2 = []
matchProgressPlayers1DictEx2 = []
matchProgressPlayers2DictEx2 = []

players1 = []
players2 = []
allplayers = []

for pl in jsonPlayers:
    for plXML in xmlPlayers:
        if pl.name == plXML.name:
            pl.tkn = plXML.damageTknArmor + plXML.damageTkn 
            pl.gvn = plXML.damageGvnArmor + plXML.damageGvn 
            pl.spawnfrags = plXML.spawnFragsXML
            pl.initPowerUpsByMinutes(minutesPlayedXML)
            pl.ga = pl.gaXML  #int(line.split("ga:")[1].split(" ")[0])
            pl.ya = pl.yaXML  #int(line.split("ya:")[1].split(" ")[0])
            pl.ra = pl.raXML  #int(line.split("ra:")[1].split(" ")[0])
            pl.mh = pl.mhXML  #int(line.split("mh:")[1].split(" ")[0])
            pl.damageGvn = plXML.damageGvn
            pl.damageTkn = plXML.damageTkn
            pl.damageSelf = plXML.damageSelf
            pl.damageGvnArmor = plXML.damageGvnArmor
            pl.damageTknArmor = plXML.damageTknArmor
            pl.damageSelfArmor = plXML.damageSelfArmor
            # pl.lifetimeXML = plXML.lifetimeXML + (minutesPlayedXML*60 - plXML.lastDeathXML.time)
            pl.lifetimeXML = plXML.lifetimeXML
            pl.lastDeathXML = plXML.lastDeathXML
            pl.firstDeathXML = plXML.firstDeathXML
            pl.connectionTimeXML = plXML.firstDeathXML.time - plXML.firstDeathXML.lifetime
            
            pl.health_15_cnt = plXML.health_15_cnt
            pl.health_25_cnt = plXML.health_25_cnt
            
            pl.pickups_weapons = plXML.pickups_weapons
            pl.pickups_items = plXML.pickups_items
            
            if len(rlAttacksByPlayers) != 0:
                try:
                    pl.rl_attacks = rlAttacksByPlayers[pl.name]
                except:
                    pass

    allplayers.append(pl)
    if pl.teamname == teamName1:
        players1.append(pl)
    if pl.teamname == teamName2:
        players2.append(pl)

# total score
totalScore = []

# head-to-head stats init     
headToHead = {}
for pl1 in allplayers:
    headToHead[pl1.name] = []
    for pl2 in allplayers:
        headToHead[pl1.name].append([pl2.name,0,[0 for i in xrange(minutesPlayedXML+1)]])        
        
# head-to-headDamage stats init
# TODO make separate function
headToHeadDamage = {}
for pl1 in allplayers:
    headToHeadDamage[pl1.name] = []
    for pl2 in allplayers:
        headToHeadDamage[pl1.name].append([pl2.name,0,[0 for i in xrange(minutesPlayedXML+1)]])  
		
def isTeamKill(element):
    if isinstance(element, DeathElement) or isinstance(element, DamageElement):
        attackerTeam = ""
        targetTeam = ""
        for pl in allplayers:
            if element.attacker == pl.name:
                attackerTeam = pl.teamname
            if element.target == pl.name:
                targetTeam = pl.teamname

        if attackerTeam == "" or targetTeam == "":
            ezstatslib.logError("ERROR isTeamKill: attacker: %s, target: %s" % (element.attacker, element.target))
            exit(-1)
        
        return attackerTeam == targetTeam        
        
progressStr = []
extendedProgressStr = []
isProgressLine = False
currentMatchTime = 0
currentMinute = 1
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

        fr1 = 0
        for pl in players1:
            fr1 += pl.frags()
        fr2 = 0
        for pl in players2:
            fr2 += pl.frags()
        
        if fr1 == fr2:
            progressStr.append("tie")
        else:
            progressStr.append("[%s]%s" % (teamName1 if fr1 > fr2 else teamName2, fr1-fr2 if fr1 > fr2 else fr2-fr1))
        fillExtendedBattleProgress()
        
        progressLineDict[team1.name] = fr1;  # team1.frags()
        progressLineDict[team2.name] = fr2; # team2.frags()        
        matchProgressDict.append(progressLineDict)
        matchProgressDictEx.append(progressLineDict)

        players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict1 = {}
        for pl in players1ByFrags:
            playersProgressLineDict1[pl.name] = [pl.frags(), pl.calcDelta()];        
        matchProgressPlayers1Dict.append(playersProgressLineDict1)
        matchProgressPlayers1DictEx.append(playersProgressLineDict1)

        players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict2 = {}
        for pl in players2ByFrags:
            playersProgressLineDict2[pl.name] = [pl.frags(), pl.calcDelta()];
        matchProgressPlayers2Dict.append(playersProgressLineDict2)
        matchProgressPlayers2DictEx.append(playersProgressLineDict2)

        battleProgressExtendedNextPoint += (int)(60 / ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
    
    if len(matchProgressDictEx2) == 0 or matchProgressDictEx2[len(matchProgressDictEx2)-1][team1.name][0] != currentMatchTime:
        progressLineDict = {}
        
        fr1 = 0
        for pl in players1:
            fr1 += pl.frags()
        fr2 = 0
        for pl in players2:
            fr2 += pl.frags()
            
        progressLineDict[team1.name] = [currentMatchTime, fr1]; # team1.frags()
        progressLineDict[team2.name] = [currentMatchTime, fr2]; # team2.frags()
        matchProgressDictEx2.append(progressLineDict)
        
        players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict1 = {}
        for pl in players1ByFrags:
            playersProgressLineDict1[pl.name] = [currentMatchTime, pl.frags(), pl.calcDelta()];                
        matchProgressPlayers1DictEx2.append(playersProgressLineDict1)

        players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict2 = {}
        for pl in players2ByFrags:
            playersProgressLineDict2[pl.name] = [currentMatchTime, pl.frags(), pl.calcDelta()];        
        matchProgressPlayers2DictEx2.append(playersProgressLineDict2)

    # skip Damage and Death elements with target=None (door which is opened by the shot)
    if (isinstance(element, DeathElement) or isinstance(element, DamageElement)) and element.target is None:
        continue
               
    # telefrag
    if isinstance(element, DeathElement) and element.type == "tele1":        
        who = element.attacker
        whom = element.target
        
        isTK = isTeamKill(element)
        if isTK:
            isFoundWho = False
            isFoundWhom = False            
            for pl in allplayers:
                if pl.name == who:
                    pl.incTeamkill(currentMatchTime, who, whom)
                    pl.kill_weapons.add('tele')
                    isFoundWho = True

                if whom != "" and pl.name == whom:
                    pl.incTeamdeath(currentMatchTime, who, whom)
                    pl.death_weapons.add('tele')
                    isFoundWhom = True
       
            if not isFoundWho and not isFoundWhom:
                ezstatslib.logError("ERROR: count telefrag %s-%s\n" % (who, whom))
                exit(0)
        else:        
            for pl in allplayers:
                if who != "" and pl.name == who:
                    pl.incKill(currentMatchTime, who, whom)
                    pl.tele_kills += 1
                    pl.kill_weapons.add('tele')
                    isFoundWho = True
        
                if pl.name == whom:
                    pl.incDeath(currentMatchTime, who, whom)
                    pl.tele_deaths += 1
                    pl.death_weapons.add('tele')
                    isFoundWhom = True
             
            if not isFoundWho or not isFoundWhom:                
                ezstatslib.logError("ERROR: count telefrag %s-%s\n" % (who, whom))
                exit(0)
    
        fillH2H(who,whom,currentMinute)
    
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
                    exec("pl.%s += 1" % (pwr))
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
            elif weap == "stomp" or weap == "lava":
                weap = "other"  # TODO fall on the player  # TODO ULTRA RARE ACH
            else:
                exit(0)
    
        isTK = isTeamKill(element)
              
        if isTK:            
            isFoundWho = False
            isFoundWhom = False
            for pl in allplayers:
                if pl.name == who:
                    pl.incTeamkill(currentMatchTime, who, whom)
                    pl.kill_weapons.add(weap)
                    isFoundWho = True

                if pl.name == whom:
                    pl.incTeamdeath(currentMatchTime, who, whom)
                    pl.death_weapons.add(weap)
                    isFoundWhom = True
       
            if not isFoundWho and not isFoundWhom:
                ezstatslib.logError("ERROR: count common %s-%s\n" % (who, whom))
                exit(0)
        else:   
            isFoundWho = False
            isFoundWhom = False
            for pl in allplayers:
                if pl.name == who:
                    pl.incKill(currentMatchTime, who, whom);
                    exec("pl.%s_kills += 1" % (weap))
                    pl.kill_weapons.add(weap)
                    isFoundWho = True
                    
                if pl.name == whom:
                    pl.incDeath(currentMatchTime, who, whom);
                    exec("pl.%s_deaths += 1" % (weap))
                    pl.death_weapons.add(weap)
                    isFoundWhom = True
                
            if not isFoundWho or not isFoundWhom:
                ezstatslib.logError("ERROR: count common %s-%s\n" % (who, whom))
                
        fillH2H(who,whom,currentMinute)
        
        continue

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
            #print "ERROR: unknown weapon:", weap
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
            isTK = isTeamKill(element)
        
            for pl in allplayers:
                if pl.name == who:
                    exec("pl.%s_damage_gvn += %d" % (weap, value))
                    exec("pl.%s_damage_gvn_cnt += 1" % (weap))
                    if isTK: 
                        pl.tm += value
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
            ezstatslib.logError("ERROR: AAAAA damage calc %s-%s\n" % (who, whom))

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
                    
                attackTeam = ""
                targetTeam = ""
                for pl in allplayers:
                    if pl.name == attackPl:
                        attackTeam = pl.teamname
                    if pl.name == targetPl:
                        targetTeam = pl.teamname
                        
                if attackTeam == targetTeam:
                    # suicide + teamkill
                    ll = "OLOLO: %f suicide + teamkill(%s) by %s [wps: %s + %s]\n" % (tt, target2 if isSuicide1 else target1, attackPl, wp1 if isSuicide1 else wp2, wp2 if isSuicide1 else wp1)
                    ezstatslib.logError(ll)
                    tmpComboStr += ll
                else:
                    # suicide + kill
                    ll = "OLOLO: %f suicide + kill(%s) by %s [wps: %s + %s]\n" % (tt, target2 if isSuicide1 else target1, attackPl, wp1 if isSuicide1 else wp2, wp2 if isSuicide1 else wp1)
                    for pl in allplayers:
                        if pl.name == attackPl:
                            pl.suicide_kills.append([tt,target2 if isSuicide1 else target1,wp2 if isSuicide1 else wp1])
                    
                    ezstatslib.logError(ll)
                    tmpComboStr += ll
            
            else: # non suicide
                attackTeam = ""
                targetTeam1 = ""
                targetTeam2 = ""
                for pl in allplayers:
                    if pl.name == target1:
                        targetTeam1 = pl.teamname
                    if pl.name == target2:
                        targetTeam2 = pl.teamname
                    if pl.name == attacker1:
                        attackTeam = pl.teamname
                
                if attackTeam != targetTeam1 and attackTeam != targetTeam2:
                    # kill + kill
                    for pl in allplayers:
                        if pl.name == attacker1:
                            pl.double_kills.append([target1,target2,wp1])
                    
                    ll = "OLOLO: %f kill(%s) + kill(%s) by %s [wps: %s + %s]\n" % (tt, target1, target2, attacker1, wp1, wp2)
                    ezstatslib.logError(ll)
                    tmpComboStr += ll
                    
                elif attackTeam == targetTeam1 and attackTeam == targetTeam2:
                    # teamkill + teamkill
                    ll = "OLOLO: %f teamkill(%s) + teamkill(%s) by %s [wps: %s + %s]\n" % (tt, target1, target2, attacker1, wp1, wp2)
                    ezstatslib.logError(ll)
                    tmpComboStr += ll
                else:
                    # kill + teamkill
                    ll = "OLOLO: %f kill(%s) + teamkill(%s) by %s [wps: %s + %s]\n" % (tt, target2 if attackTeam != targetTeam2 else target1, target2 if attackTeam == targetTeam2 else target1, attacker1, wp2 if attackTeam != targetTeam2 else wp1, wp2 if attackTeam == targetTeam2 else wp1)
                    ezstatslib.logError(ll)
                    tmpComboStr += ll
            
            
        else:
            # mutual kill
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
                attackerTeam = ""
                targetsTeam = ""
                for pl in allplayers:
                    for targ in targets:
                        if pl.name == attacker:
                            attackTeam = pl.teamname
                    
                        if pl.name == targ:
                            if targetsTeam == "":
                                targetsTeam = pl.teamname
                            else:
                                if targetsTeam != pl.teamname:
                                    targetsTeam = "-1"

                if targetsTeam != "-1" and targetsTeam != "" and targetsTeam != attackTeam:
                    for pl in allplayers:
                        if pl.name == attacker:
                            if attacker != targets[0] and attacker != targets[1] and attacker != targets[2]:
                                pl.triple_kills.append([tt,targets[0],targets[1],targets[2],wps[0]])
                            else:
                                target1 = ""
                                target2 = ""
                                for t in targets:
                                    if t != attacker:
                                        if target1 == "":
                                            target1 = t
                                        else:
                                            target2 = t
                                pl.double_kills.append([target1,target2,wps[0]])
        
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
           
# validate score
fragsSum1 = 0
for pl in players1:
    fragsSum1 += pl.frags()

fragsSum2 = 0
for pl in players2:
    fragsSum2 += pl.frags()

totalScore = []
totalScore.append( [players1[0].teamname, fragsSum1] )
totalScore.append( [players2[0].teamname, fragsSum2] )


# take info from xml
# for death in deathElements:
    # if death.attacker == "world" or death.target == "world":
        # continue
        
    # if death.attacker == death.target:
        # continue

    # attackerTeam = ""
    # targetTeam = ""
    # for pl in allplayers:
        # if death.attacker == pl.name:
            # attackerTeam = pl.teamname
        # if death.target == pl.name:
            # targetTeam = pl.teamname

    # if attackerTeam == "" or targetTeam == "":
        # ezstatslib.logError("ERROR in xml teamkill detection: death.attacker: %s, death.target" % (death.attacker, death.target))
        # exit(-1)
    
    # if attackerTeam == targetTeam:
        # who = death.attacker
        # whom = death.target
    
        # isFoundWho = False
        # isFoundWhom = False
        # for pl in allplayers:
            # if pl.name == who:
                # pl.incTeamkill(currentMatchTime, who, whom)
                # isFoundWho = True

            # if whom != "" and pl.name == whom:
                # pl.incTeamdeath(currentMatchTime, who, whom)
                # isFoundWhom = True

        # if whom != "":
            # fillH2H(who,whom)

        # if not isFoundWho and not isFoundWhom:
            # ezstatslib.logError("count teamkills\n")
            # exit(0)

# power ups
# for element in pickmapitemElements:    
    # if element.isArmor or element.isMH:
        # checkname = element.player
        # if element.isMH:
            # pwr = "mh"
        # if element.isArmor:
            # if element.armorType == ezstatslib.PowerUpType.RA:
                # pwr = "ra"
            # if element.armorType == ezstatslib.PowerUpType.YA:
                # pwr = "ya"
            # if element.armorType == ezstatslib.PowerUpType.GA:
                # pwr = "ga"
                               
        # isFound = False
        # for pl in allplayers:
            # if pl.name == checkname:                    
                # exec("pl.inc%s(%d,%d)" % (pwr, (element.time-2) / 60, element.time))
                # isFound = True
                # break;
        # if not isFound:
            # ezstatslib.logError("ERROR: powerupDetection: no playername %s\n" % (checkname))
            # exit(0)
    
        # continue              
    
    
# fill team kills/deaths/teamkills/suicides/teamdeaths/powerups/weapons
for pl in players1:
    for pwr in ["ga","ya","ra","mh","tkn","gvn","tm"]:
        exec("team1.%s += pl.%s" % (pwr, pwr))
    
    team1.kills += pl.kills
    team1.deaths += pl.deaths
    team1.teamkills += pl.teamkills
    team1.suicides += pl.suicides
    team1.teamdeaths += pl.teamdeaths

    team1.powerUps += pl.powerUps

    if len(team1.gaByMinutes) == 0:
        team1.initPowerUpsByMinutes(len(pl.gaByMinutes))

    for minNum in xrange(len(pl.gaByMinutes)):
        team1.gaByMinutes[minNum] += pl.gaByMinutes[minNum]
        team1.yaByMinutes[minNum] += pl.yaByMinutes[minNum]
        team1.raByMinutes[minNum] += pl.raByMinutes[minNum]
        team1.mhByMinutes[minNum] += pl.mhByMinutes[minNum]

    team1.fillWeaponsKillsDeaths(pl);

for pl in players2:
    for pwr in ["ga","ya","ra","mh","tkn","gvn","tm"]:
        exec("team2.%s += pl.%s" % (pwr, pwr))

    team2.kills += pl.kills
    team2.deaths += pl.deaths
    team2.teamkills += pl.teamkills
    team2.suicides += pl.suicides
    team2.teamdeaths += pl.teamdeaths

    team2.powerUps += pl.powerUps

    if len(team2.gaByMinutes) == 0:
        team2.initPowerUpsByMinutes(len(pl.gaByMinutes))

    for minNum in xrange(len(pl.gaByMinutes)):
        team2.gaByMinutes[minNum] += pl.gaByMinutes[minNum]
        team2.yaByMinutes[minNum] += pl.yaByMinutes[minNum]
        team2.raByMinutes[minNum] += pl.raByMinutes[minNum]
        team2.mhByMinutes[minNum] += pl.mhByMinutes[minNum]

    team2.fillWeaponsKillsDeaths(pl);

# fill final battle progress
progressLineDict = {}
progressLineDict[team1.name] = team1.frags();
progressLineDict[team2.name] = team2.frags();
matchProgressDict.append(progressLineDict)
matchProgressDictEx.append(progressLineDict)


minsCount = len(matchProgressDict)
progressLineDict = {}
progressLineDict[team1.name] = [minsCount*60, team1.frags()];
progressLineDict[team2.name] = [minsCount*60, team2.frags()];

players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
playersProgressLineDict1 = {}
for pl in players1ByFrags:
    playersProgressLineDict1[pl.name] = [pl.frags(), pl.calcDelta()];
matchProgressPlayers1Dict.append(playersProgressLineDict1)
matchProgressPlayers1DictEx.append(playersProgressLineDict1)

playersProgressLineDict1Ex = {}
for pl in players1ByFrags:
    playersProgressLineDict1Ex[pl.name] = [minsCount*60, pl.frags(), pl.calcDelta()];

players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
playersProgressLineDict2 = {}
for pl in players2ByFrags:
    playersProgressLineDict2[pl.name] = [pl.frags(), pl.calcDelta()];
matchProgressPlayers2Dict.append(playersProgressLineDict2)
matchProgressPlayers2DictEx.append(playersProgressLineDict2)

playersProgressLineDict2Ex = {}
for pl in players2ByFrags:
    playersProgressLineDict2Ex[pl.name] = [minsCount*60, pl.frags(), pl.calcDelta()];

# correct final point if necessary
if len(matchProgressDictEx2) != 0 and matchProgressDictEx2[len(matchProgressDictEx2)-1][team1.name][0] == minsCount*60:
    matchProgressDictEx2[len(matchProgressDictEx2)-1] = progressLineDict
    matchProgressPlayers1DictEx2[len(matchProgressPlayers1DictEx2)-1] = playersProgressLineDict1Ex
    matchProgressPlayers2DictEx2[len(matchProgressPlayers2DictEx2)-1] = playersProgressLineDict2Ex
else:
    matchProgressDictEx2.append(progressLineDict)
    matchProgressPlayers1DictEx2.append(playersProgressLineDict1Ex)
    matchProgressPlayers2DictEx2.append(playersProgressLineDict2Ex)

fillExtendedBattleProgress()

# fill final element in calculatedStreaks
for pl in allplayers:
    pl.fillStreaks(currentMatchTime)
    pl.fillDeathStreaks(currentMatchTime)

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
    pl.calculateAchievements([], powerUpsStatus, headToHead, isTeamGame = True)
    #pl.calculateAchievements(matchProgress, powerUpsStatus, headToHead)

ezstatslib.calculateCommonAchievements(allplayers, headToHead, minutesPlayedXML, isTeamGame = True, headToHeadDamage = headToHeadDamage)

# sort by level and type
for pl in allplayers:
    pl.achievements = sorted(pl.achievements, key=lambda x: (x.achlevel, x.achtype), reverse=False)
    
# remove elements with one timestamp - the last one for same time should be left    
for pl in allplayers:
    pl.correctLifetime(minutesPlayedXML)    
    
# generate output string
resultString = ""

resultString += "==================\n"
resultString += "matchdate:" + matchdate + "\n"
resultString += "map:" + mapName + "\n"
resultString += "\n"

resultString += "teams:\n"

def teamPlayersToString(players):
    res = ""
    for pl in players:
        sign = "" if res == "" else ", "
        if res == "":
            res = "[%s]: " % (pl.teamname)
        res += "%s%s" % (sign, pl.name)
    return res

resultString += teamPlayersToString(players1) + "\n"
resultString += teamPlayersToString(players2) + "\n"

# if options.withScripts:
#     resultString += "</pre>MATCH_RESULTS_PLACE\n<pre>"

resultString += "\n"
resultString += "%s[%d] x %s[%d]\n" % (totalScore[0][0], totalScore[0][1], totalScore[1][0], totalScore[1][1])
resultString += "\n"

if options.withScripts:
    resultString += "</pre>TEAM_RESULTS\n<pre>"

s1 = ""
players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
for pl in players1ByFrags:
    if s1 == "":
        s1 = "[%s]:\n" % (pl.teamname)
    s1 +=  "{0:20s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats())
resultString += s1
resultString += "\n"

for pl in players1ByFrags:
    resultString += "{0:20s}  {1:s}\n".format(pl.name, pl.getFormatedPowerUpsStats())
resultString += "\n"

s2 = ""
players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
for pl in players2ByFrags:
    if s2 == "":
        s2 = "[%s]:\n" % (pl.teamname)
    s2 +=  "{0:20s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats())
resultString += s2
resultString += "\n"

for pl in players2ByFrags:
    resultString += "{0:20s}  {1:s}\n".format(pl.name, pl.getFormatedPowerUpsStats())
resultString += "\n"

if options.withScripts:
    resultString += "</pre>PLAYERS_ACHIEVEMENTS_PLACE\n<pre>"

allplayersByFrags = sorted(allplayers, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)

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

# if options.withScripts:
#     resultString += "</pre>TEAM_STATS_DONUTS_PLACE\n<pre>"
#
# resultString += "<hr>"
#
# if options.withScripts:
#     resultString += "</pre>POWER_UPS_DONUTS_PLACE\n<pre>"

if options.withScripts:
    resultString += "</pre>TEAMS_STATS_DONUTS_PLACE\n<pre>"

if options.withScripts:
    resultString += "</pre>POWER_UPS_TIMELINE_VER2_PLACE\n<pre>"

foldingHeaderStr = "</pre>" + ezstatslib.HTML_SCRIPT_FOLDING_SECTION_HEADER
foldingHeaderStr = foldingHeaderStr.replace("H2_CLASS_NAME", "StreaksTable");
foldingHeaderStr = foldingHeaderStr.replace("DIV_ID_NAME", "Streaks table");

resultString += foldingHeaderStr

resultString += str(totalStreaksHtmlTable)

resultString += ezstatslib.HTML_SCRIPT_FOLDING_SECTION_FOOTER + "<pre>"

if options.withScripts:
    resultString += "</pre>STREAK_ALL_TIMELINE_PLACE\n<pre>"

i = 1
resultString += "battle progress:\n"
for p in progressStr:
    resultString += "%d:%s %s%s\n" % (i, "" if i >= 10 else " ", p, " << IT IS OVERTIME!!" if isOverTime and i == timelimit else "")
    i += 1

if totalScore[0][1] > totalScore[1][1]:
    resultString += "%d: [%s]%d\n" % (i, totalScore[0][0], (totalScore[0][1] - totalScore[1][1]))
else:
    resultString += "%d: [%s]%d\n" % (i, totalScore[1][0], (totalScore[1][1] - totalScore[0][1]))

# extended battle progress
i = 1
resultString += "\n"
resultString += "extended battle progress:\n"
for p in extendedProgressStr:
    resultString += "%d:%s %s\n" % (i, "" if i >= 10 else " ",  p)
    i += 1

# if options.withScripts:
    # resultString += "\nHIGHCHART_BATTLE_PROGRESS_PLACE\n"

if options.withScripts:
    resultString += "\nHIGHCHART_EXTENDED_BATTLE_PROGRESS_PLACE\n"

if options.withScripts:
    resultString += "\nHIGHCHART_PLAYERS_BATTLE_PROGRESS_PLACE\n"

if options.withScripts:
    resultString += "\nHIGHCHART_TEAM_BATTLE_PROGRESS_PLACE\n"

if options.withScripts:
    resultString += "\nHIGHCHART_PLAYERS_RANK_PROGRESS_PLACE\n"

sortedByDelta = sorted(allplayers, key=methodcaller("calcDelta"))
# print
# print "next captains: %s(%d) and %s(%d)" % (sortedByDelta[0].name, sortedByDelta[0].calcDelta(), sortedByDelta[1].name, sortedByDelta[1].calcDelta())

# team stats output
resultString += "\n"
resultString += "Team stats:\n"
resultString += "[%s]\n" % (team1.name)
resultString += "GreenArm:   " + "{0:3d}".format(team1.ga) + "  [" +  ezstatslib.sortPlayersBy(players1, "ga") + "]\n"
resultString += "YellowArm:  " + "{0:3d}".format(team1.ya) + "  [" +  ezstatslib.sortPlayersBy(players1, "ya") + "]\n"
resultString += "RedArm:     " + "{0:3d}".format(team1.ra) + "  [" +  ezstatslib.sortPlayersBy(players1, "ra") + "]\n"
resultString += "MegaHealth: " + "{0:3d}".format(team1.mh) + "  [" +  ezstatslib.sortPlayersBy(players1, "mh") + "]\n"
resultString += "\n"
resultString += "TakenDam: " + "{0:5d}".format(team1.tkn) + "  [" +  ezstatslib.sortPlayersBy(players1, "tkn") + "]\n"
resultString += "GivenDam: " + "{0:5d}".format(team1.gvn) + "  [" +  ezstatslib.sortPlayersBy(players1, "gvn") + "]\n"
resultString += "TeamDam:  " + "{0:5d}".format(team1.tm)  + "  [" +  ezstatslib.sortPlayersBy(players1, "tm") + "]\n"
resultString += "DeltaDam: " + "{0:5d}".format(team1.damageDelta()) + "  [" +  ezstatslib.sortPlayersBy(players1,"damageDelta", fieldType="method") + "]\n"
resultString += "\n"
resultString += "Kills:    " + "{0:3d}".format(team1.kills) +   "  [" +  ezstatslib.sortPlayersBy(players1, "kills") + "]\n"
resultString += "Deaths:   " + "{0:3d}".format(team1.deaths) +  "  [" +  ezstatslib.sortPlayersBy(players1, "deaths") + "]\n"
resultString += "Teamkills:" + "{0:3d}".format(team1.teamkills)+"  [" +  ezstatslib.sortPlayersBy(players1, "teamkills") + "]\n"
resultString += "Suicides: " + "{0:3d}".format(team1.suicides) + "  [" +  ezstatslib.sortPlayersBy(players1, "suicides") + "]\n"
resultString += "\n"
# resultString += "Streaks:    " + " [" + ezstatslib.sortPlayersBy(players1,"streaks") + "]\n"
resultString += "SpawnFrags: " + " [" + ezstatslib.sortPlayersBy(players1,"spawnfrags") + "]\n"

resultString += "\n"
resultString += "[%s]\n" % (team2.name)
resultString += "GreenArm:   " + "{0:3d}".format(team2.ga) + "  [" +  ezstatslib.sortPlayersBy(players2, "ga") + "]\n"
resultString += "YellowArm:  " + "{0:3d}".format(team2.ya) + "  [" +  ezstatslib.sortPlayersBy(players2, "ya") + "]\n"
resultString += "RedArm:     " + "{0:3d}".format(team2.ra) + "  [" +  ezstatslib.sortPlayersBy(players2, "ra") + "]\n"
resultString += "MegaHealth: " + "{0:3d}".format(team2.mh) + "  [" +  ezstatslib.sortPlayersBy(players2, "mh") + "]\n"
resultString += "\n"
resultString += "TakenDam: " + "{0:5d}".format(team2.tkn) + "  [" +  ezstatslib.sortPlayersBy(players2, "tkn") + "]\n"
resultString += "GivenDam: " + "{0:5d}".format(team2.gvn) + "  [" +  ezstatslib.sortPlayersBy(players2, "gvn") + "]\n"
resultString += "TeamDam:  " + "{0:5d}".format(team2.tm)  + "  [" +  ezstatslib.sortPlayersBy(players2, "tm") + "]\n"
resultString += "DeltaDam: " + "{0:5d}".format(team2.damageDelta()) + "  [" +  ezstatslib.sortPlayersBy(players2,"damageDelta", fieldType="method") + "]\n"
resultString += "\n"
resultString += "Kills:    " + "{0:3d}".format(team2.kills) +   "  [" +  ezstatslib.sortPlayersBy(players2, "kills") + "]\n"
resultString += "Deaths:   " + "{0:3d}".format(team2.deaths) +  "  [" +  ezstatslib.sortPlayersBy(players2, "deaths") + "]\n"
resultString += "Teamkills:" + "{0:3d}".format(team2.teamkills)+"  [" +  ezstatslib.sortPlayersBy(players2, "teamkills") + "]\n"
resultString += "Suicides: " + "{0:3d}".format(team2.suicides) + "  [" +  ezstatslib.sortPlayersBy(players2, "suicides") + "]\n"
resultString += "\n"
# resultString += "Streaks:    " + " [" + ezstatslib.sortPlayersBy(players2,"streaks") + "]\n"
resultString += "SpawnFrags: " + " [" + ezstatslib.sortPlayersBy(players2,"spawnfrags") + "]\n"

# all players
resultString += "\n"
resultString += "All players:\n"
resultString += "GreenArm:   " + " [" +  ezstatslib.sortPlayersBy(allplayers, "ga") + "]\n"
resultString += "YellowArm:  " + " [" +  ezstatslib.sortPlayersBy(allplayers, "ya") + "]\n"
resultString += "RedArm:     " + " [" +  ezstatslib.sortPlayersBy(allplayers, "ra") + "]\n"
resultString += "MegaHealth: " + " [" +  ezstatslib.sortPlayersBy(allplayers, "mh") + "]\n"
resultString += "\n"
resultString += "TakenDam:   " + " [" +  ezstatslib.sortPlayersBy(allplayers, "tkn") + "]\n"
resultString += "GivenDam:   " + " [" +  ezstatslib.sortPlayersBy(allplayers, "gvn") + "]\n"
resultString += "TeamDam:    " + " [" +  ezstatslib.sortPlayersBy(allplayers, "tm") + "]\n"
resultString += "DeltaDam:   " + " [" +  ezstatslib.sortPlayersBy(allplayers,"damageDelta", fieldType="method") + "]\n"
resultString += "\n"
resultString += "Kills:      " + " [" +  ezstatslib.sortPlayersBy(allplayers, "kills") + "]\n"
resultString += "Deaths:     " + " [" +  ezstatslib.sortPlayersBy(allplayers, "deaths") + "]\n"
resultString += "Teamkills:  " + " [" +  ezstatslib.sortPlayersBy(allplayers, "teamkills") + "]\n"
resultString += "Suicides:   " + " [" +  ezstatslib.sortPlayersBy(allplayers, "suicides") + "]\n"
resultString += "\n"
# resultString += "Streaks:    " + " [" +  ezstatslib.sortPlayersBy(allplayers,"streaks") + "]\n"
resultString += "SpawnFrags: " + " [" +  ezstatslib.sortPlayersBy(allplayers,"spawnfrags") + "]\n"
resultString += "\n"
# resultString += "RL skill DH:" + " [" +  ezstatslib.sortPlayersBy(allplayers, "rlskill_dh") + "]\n"
# resultString += "RL skill AD:" + " [" +  ezstatslib.sortPlayersBy(allplayers, "rlskill_ad") + "]\n"
#resultString += "\n"
# resultString += "Weapons:\n"
# resultString += "RL:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_rl", units="%") + "]\n"
# resultString += "LG:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_lg", units="%") + "]\n"
# resultString += "GL:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_gl", units="%") + "]\n"
# resultString += "SG:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_sg", units="%") + "]\n"
# resultString += "SSG:        " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_ssg", units="%") + "]\n"
# resultString += "\n"

resultString += "Health15:   " + " [" +  ezstatslib.sortPlayersBy(allplayers,"health_15_cnt") + "]\n"
resultString += "Health25:   " + " [" +  ezstatslib.sortPlayersBy(allplayers,"health_25_cnt") + "]\n"
resultString += "\n"

resultString += "Max speed:   " + " [" +  ezstatslib.sortPlayersBy(allplayers,"speed_max") + "]\n"
resultString += "Avg speed:   " + " [" +  ezstatslib.sortPlayersBy(allplayers,"speed_avg") + "]\n"
resultString += "\n"

# TODO
plNameMaxLen = 23;

resultString += "Players weapons:\n"
weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    resultString += "{0:23s} kills  {1:3d} :: {2:100s}\n".format("[%s]%s" % (pl.teamname, pl.name), pl.kills,  pl.getWeaponsKills(pl.kills,   weaponsCheck))
    resultString += "{0:23s} deaths {1:3d} :: {2:100s}\n".format("",                                pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    resultString += "\n"
    resultString += ("{0:%ds} given {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageGvn+pl.damageGvnArmor, pl.getWeaponsDamageGvn(pl.damageGvn+pl.damageGvnArmor, weaponsCheck))
    resultString += ("{0:%ds} taken {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageTkn+pl.damageTknArmor, pl.getWeaponsDamageTkn(pl.damageTkn+pl.damageTknArmor, weaponsCheck))
    resultString += ("{0:%ds} self  {1:4d} :: {2:100s}\n" % (plNameMaxLen)).format("", pl.damageSelf+pl.damageSelfArmor, pl.getWeaponsDamageSelf(pl.damageSelf+pl.damageSelfArmor, weaponsCheck))
    # resultString += ("{0:%ds} avg damage :: {1:100s}\n" % (plNameMaxLen)).format("", pl.getWeaponsAccuracy(weaponsCheck))  TODO
    resultString += ("{0:%ds} rl skill   :: {1:200s}\n" % (plNameMaxLen)).format("", pl.getRLSkill())
    resultString += ("{0:%ds} pickups    :: {1:200s}\n" % (plNameMaxLen)).format("", pl.getWeaponsPickUps())
    resultString += ("{0:%ds} ammo       :: {1:200s}\n" % (plNameMaxLen)).format("", pl.getAmmoPickUps())
    resultString += "\n"
    resultString += "\n"

resultString += "Teams weapons:\n"
resultString += "{0:23s} kills  {1:3d} :: {2:100s}\n".format("[%s]" % (team1.name), team1.kills,  team1.getWeaponsKills(team1.kills,   weaponsCheck))
resultString += "{0:23s} deaths {1:3d} :: {2:100s}\n".format("",                    team1.deaths, team1.getWeaponsDeaths(team1.deaths, weaponsCheck))
resultString += "\n"
resultString += "{0:23s} kills  {1:3d} :: {2:100s}\n".format("[%s]" % (team2.name), team2.kills,  team2.getWeaponsKills(team2.kills,   weaponsCheck))
resultString += "{0:23s} deaths {1:3d} :: {2:100s}\n".format("",                    team2.deaths, team2.getWeaponsDeaths(team2.deaths, weaponsCheck))
resultString += "\n"

if options.withScripts:
    resultString += "RL skill:\n"
    resultString += "\nHIGHCHART_RL_SKILL_PLACE\n"

if options.withScripts:    
    resultString += "\n</pre>HIGHCHART_PLAYER_LIFETIME_PLACE\n<pre>"

# H2H stats
resultString += "\n"
resultString += "Head-to-Head stats (who :: whom)\n"
resultString += "[%s]\n" % (team1.name)
for pl in sorted(players1, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += "{0:20s} {1:3d} :: {2:100s}\n".format(pl.name, pl.kills, resStr)
resultString += "\n"
resultString += "[%s]\n" % (team2.name)
for pl in sorted(players2, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += "{0:20s} {1:3d} :: {2:100s}\n".format(pl.name, pl.kills, resStr)

# H2HDamage stats
resultString += "\n"
resultString += "Head-to-HeadDamage stats (who :: whom)\n"
resultString += "[%s]\n" % (team1.name)
for pl in sorted(players1, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHeadDamage[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += "{0:20s} {1:3d} - {2:3d} :: {3:100s}\n".format(pl.name, pl.gvn, pl.tkn, resStr)
resultString += "\n"
resultString += "[%s]\n" % (team2.name)
for pl in sorted(players2, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHeadDamage[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += "{0:20s} {1:3d} - {2:3d} :: {3:100s}\n".format(pl.name, pl.gvn, pl.tkn, resStr)
	
    
# Players duels table

def createDuelCell(rowPlayer, player, isDamage):
    plName = player.name

    if rowPlayer.name == plName:
        return HTML.TableCell(str(rowPlayer.suicides), bgcolor=ezstatslib.BG_COLOR_GRAY)
    else:
        plKills = 0
        for val in headToHead[rowPlayer.name] if not isDamage else headToHeadDamage[rowPlayer.name]:
            if val[0] == plName:
                plKills = val[1]

        plDeaths = 0
        for val in headToHead[plName] if not isDamage else headToHeadDamage[plName]:
            if val[0] == rowPlayer.name:
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

        return HTML.TableCell(cellVal, bgcolor=cellColor)

def createPlayersDuelTable(team, teamPlayers, enemyPlayers, isDamage):
    if isDamage:
        headerRow=["[" + team.name + "]", 'Frags', 'Given', 'Taken']
    else:
        headerRow=["[" + team.name + "]", 'Frags', 'Kills', 'Deaths']
        
    playersNames = []
    for pl in enemyPlayers:
        headerRow.append(pl.name);
        playersNames.append(pl.name)

    headerRow.append("X");
    headerRow.append("Team kills");
    headerRow.append("Team deaths");
    for pl in teamPlayers:
        headerRow.append(pl.name);

    colAlign=[]
    for i in xrange(len(headerRow)):
        colAlign.append("center")

    htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                           style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

    for pl in teamPlayers:
        tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                        ezstatslib.htmlBold(pl.frags()),
                                        ezstatslib.htmlBold(pl.gvn) if isDamage else ezstatslib.htmlBold(pl.kills),
                                        ezstatslib.htmlBold(pl.tkn) if isDamage else ezstatslib.htmlBold(pl.deaths)])

        for pll in enemyPlayers:
            tableRow.cells.append( createDuelCell(pl, pll, isDamage) )

        tableRow.cells.append( HTML.TableCell("") )
        tableRow.cells.append( HTML.TableCell(ezstatslib.htmlBold(pl.teamkills)) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.htmlBold(pl.teamdeaths)) )

        for pll in teamPlayers:
            tableRow.cells.append( createDuelCell(pl, pll, isDamage) )

        htmlTable.rows.append(tableRow)

    return htmlTable

# Players duels table
resultString += "\n"
resultString += "Players duels:<br>"
	
resultString += str( createPlayersDuelTable(team1, players1ByFrags, players2ByFrags, False) )
resultString += "\n"
resultString += str( createPlayersDuelTable(team2, players2ByFrags, players1ByFrags, False) )


# Players damage duels table
resultString += "\n"
resultString += "Players damage duels:<br>"

resultString += str( createPlayersDuelTable(team1, players1ByFrags, players2ByFrags, True) )
resultString += "\n"
resultString += str( createPlayersDuelTable(team2, players2ByFrags, players1ByFrags, True) )

for pl in allplayersByFrags:
    resultString += "</pre>%s_KILLS_BY_MINUTES_PLACE\n<pre>" % (ezstatslib.escapePlayerName(pl.name))    

# mutual kills 
resultString += "\nMutual kills: \n"
for pl in allplayers:
    if len(pl.mutual_kills) != 0:
        resultString += "%s: " % (pl.name)
        for mk in pl.mutual_kills:
            resultString += "%f: %s(%s,%s)," % (mk[0], mk[1], mk[2], mk[3])
        resultString += "\n"
           
resultString += "\n"

# lifetimeXML
resultString += "\nLifetime: \n"
for pl in allplayers:    
    resultString += "%s: %f; inactive time: %f;  1st death: time(%f), lifetime(%f);   last death: time(%f), lifetime(%f)\n" % (pl.name, pl.lifetimeXML, (minutesPlayedXML*60 - pl.lifetimeXML), pl.firstDeathXML.time, pl.firstDeathXML.lifetime, pl.lastDeathXML.time, pl.lastDeathXML.lifetime)
    resultString += "\tconnectionTime: %f, playTime: %f\n" % (pl.connectionTimeXML, pl.playTimeXML())

resultString += "\n"

# print resultString  RESULTPRINT

def writeHtmlWithScripts(f, teams, resStr):
    sortedTeams = sorted(teams, key=lambda x: (x.frags()), reverse=True)
    teamsStr = ""
    for tt in sortedTeams:
        teamsStr += "%s(%d):_" % (tt.name, tt.frags())
        plys = players1ByFrags if players1ByFrags[0].teamname == tt.name else players2ByFrags
        plysStr = ""
        for pl in plys:
            plysStr += "%s(%d)_" % (pl.name, pl.frags())
        plysStr = plysStr[:-1]
        teamsStr += plysStr + " "
    teamsStr = teamsStr[:-1]
    teamsStr += "\n"
    f.write("<!--\nGAME_TEAMS\n" + teamsStr + "-->\n")
    
    f.write("<!--\nCOMBOS\n" + tmpComboStr + "-->\n")  # TEMP!!
    
    f.write("<!--\nMATCHDATELOG\n" + matchdateLog + "-->\n")  # TEMP!!

    pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
    pageTitle = "%s %s %s" % ("TEAM", mapName, matchdate)  # global values
    pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", pageTitle)
    pageHeaderStr += \
        "google.charts.load('current', {'packages':['corechart', 'bar', 'line', 'timeline']});\n" \
        "google.charts.setOnLoadCallback(drawAllStreakTimelines);\n" \
        "google.charts.setOnLoadCallback(drawTeamResults);\n" \
        "google.charts.setOnLoadCallback(drawPowerUpsTimelineVer2);\n"

    f.write(pageHeaderStr)

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

    isRed = False
    if len(teams) == 2:
        for tt in teams:
            if "red" == tt.name:
                isRed = True
                break

    for tt in teams:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (tt.name)
        # rowLines += "data: [0"

        # add color if one of the two teams is 'red'
        if isRed:
            if tt.name == "red":
                rowLines += "color: 'red',\n"
            else:
                rowLines += "color: 'blue',\n"

        rowLines += "data: [[0,0]"

        # graphGranularity = 1.0
        # for minEl in matchProgressDict:
        #     rowLines += ",[%f,%d]" % (graphGranularity, minEl[tt.name])  # TODO format, now is 0.500000
        #     graphGranularity += 1.0

        # graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
        graphGranularity = 1.0
        for minEl in matchProgressDictEx:
            rowLines += ",[%f,%d]" % (graphGranularity, minEl[tt.name])  # TODO format, now is 0.500000
            # graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
            graphGranularity += 1.0

        rowLines += "]\n"

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)

    # tooltip style
    # highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SIMPLE)
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

    isRed = False
    if len(teams) == 2:
        for tt in teams:
            if "red" == tt.name:
                isRed = True
                break

    for tt in teams:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (tt.name)
        # rowLines += "data: [0"

        # add color if one of the two teams is 'red'
        if isRed:
            if tt.name == "red":
                rowLines += "color: 'red',\n"
            else:
                rowLines += "color: 'blue',\n"

        rowLines += "data: [[0,0]"

        curSec = -1
        curSevVal = -1
        for minEl in matchProgressDictEx2:                        
            if curSec == -1 or curSec != int(minEl[tt.name][0]):
                curSec = int(minEl[tt.name][0])
                curSevVal = minEl[tt.name][1]                
            rowLines += ",[%d,%d]" % (minEl[tt.name][0], curSevVal)            
            
        rowLines += "]\n"

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)

    matchMinutesCnt = len(matchProgressDict)
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
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SIMPLE)

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
                if lt.health == 200 and lt.armor == 200:
                    healthRows += "{x: %f, y: %d, color: \"gold\", marker: { enabled: true, symbol: 'url(ezquakestats/img/quake-icon.png)', height: 55, width: 55 }}," % (lt.time,lt.health)
                    armorRows  += "{x: %f, y: %d, color: \"gold\", marker: { enabled: true, symbol: 'url(ezquakestats/img/quake-icon.png)', height: 55, width: 55 }}," % (lt.time,lt.armor)
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
    
    # highcharts teams battle progress -->
    matchMinutesCnt = len(matchProgressDict)

    minutesStr = ""
    for i in xrange(1,matchMinutesCnt+1):
        minutesStr += "'%d'," % (i)
    minutesStr = minutesStr[:-1]
    
    tickPositions = ""
    for i in xrange(0,matchMinutesCnt+1):
        tickPositions += "%d," % (i)
    tickPositions = tickPositions[:-1]
    
    maxTotalFrags =  (sorted(teams, key=methodcaller("frags"), reverse=True))[0].frags()
    maxPlayerFrags = (sorted(allplayers, key=methodcaller("frags"), reverse=True))[0].frags()

    tn = 1
    for tt in teams:
        highchartsTeamBattleProgressFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_FUNCTION

        rowLines = ""
        for pl in (players1 if tn == 1 else players2):
            plStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_PLAYER_SECTION

            plPoints = ""
            for minEl in matchProgressPlayers1Dict if tn == 1 else matchProgressPlayers2Dict:
                plPoints += "%d," % (minEl[pl.name][0])
            plPoints = plPoints[:-1]

            plStr = plStr.replace("PLAYER_NAME", pl.name)
            plStr = plStr.replace("PLAYER_POINTS", plPoints)

            rowLines += plStr

        teamPointsStr = ""
        for minEl in matchProgressDict:
            teamPointsStr += "%d," % (minEl[tt.name])
        teamPointsStr = teamPointsStr[:-1]

        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("DIV_NAME", "team_progress%d" % (tn))
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("TEAM_NAME", tt.name)
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("MINUTES", minutesStr)
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("TICK_POSITIONS_VALS", tickPositions)
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("ADD_ROWS", rowLines)
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("TEAM_POINTS", teamPointsStr)

        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", str(int(maxPlayerFrags*1.2)))
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("MAX_TOTAL_FRAGS",  str(int(maxTotalFrags*1.2)))

        f.write(highchartsTeamBattleProgressFunctionStr)

        tn = 2
    # <-- highcharts teams battle progress

    # highcharts players battle progress -->
    highchartsBattleProgressFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION).replace("highchart_battle_progress", "highchart_battle_progress_players")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "Players battle progress")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Frags")    

    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \

    maxFrags = -100
    hcDelim = "}, {\n"
    rowLines = ""
    for pl in players1:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (pl.name)
        rowLines += "data: [[0,0]"

        curSec = -1
        curSevVal = -1
        for minEl in matchProgressPlayers1DictEx2:
            maxFrags = max(maxFrags, minEl[pl.name][1])
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSevVal = minEl[pl.name][1]
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSevVal)

        rowLines += "]\n"
        rowLines += ",\ndashStyle: 'ShortDash'"

    for pl in players2:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (pl.name)
        rowLines += "data: [[0,0]"

        curSec = -1
        curSevVal = -1
        for minEl in matchProgressPlayers2DictEx2:
            maxFrags = max(maxFrags, minEl[pl.name][1])
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSevVal = minEl[pl.name][1]
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSevVal)

        rowLines += "]\n"

    matchMinutesCnt = len(matchProgressDict)
    tickPositions = ""
    for k in xrange(matchMinutesCnt*60+1):
        if k % 30 == 0:
            tickPositions += "%d," % (k)

    xAxisLabels = \
        "labels: {\n" \
        "     formatter: function () {\n" \
        "       return (this.value / 60).toFixed(1).toString()\n" \
        "    },\n" \
        "},\n"
    xAxisLabels += "tickPositions: [%s]\n" % (tickPositions)
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", xAxisLabels)        
        
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "      min: -10,")
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "      max: %d," % (int(maxFrags*1.1)))
        
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)

    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)

    f.write(highchartsBattleProgressFunctionStr)
    # <-- highcharts players battle progress

    # all streaks timeline -->
    allStreaksTimelineFunctionStr = ezstatslib.HTML_SCRIPT_ALL_STREAK_TIMELINE_FUNCTION

    rowLines = ""
    currentRowsLines = ""
    # isFirstTeam = False
    # isSecondTeam = False
    for pl in sorted(players1, key=methodcaller("frags"), reverse=True) + sorted(players2, key=methodcaller("frags"), reverse=True):
        strkRes,maxStrk           = pl.getCalculatedStreaksFull(1)
        for strk in strkRes:
            hintStr = "<p>&nbsp&nbsp&nbsp<b>%d: %s</b>&nbsp&nbsp&nbsp</p>" \
                      "<p>&nbsp&nbsp&nbsp<b>Sum: %s</b>&nbsp&nbsp&nbsp</p><hr>" \
                      "&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br>" \
                      "<b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.count, strk.formattedNames(), strk.formattedNamesSum(), (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            rowLines += "[ '%s', '%d', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % ("[%s] %s_kills" % (pl.teamname, pl.name), strk.count, hintStr, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))

        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("[%s] %s_kills" % (pl.teamname, pl.name))
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("[%s] %s_kills" % (pl.teamname, pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt

        deathStrkRes,deathMaxStrk = pl.getDeatchStreaksFull(1)
        for strk in deathStrkRes:
            hintStr = "<p>&nbsp&nbsp&nbsp<b>%d: %s</b>&nbsp&nbsp&nbsp</p>" \
                      "<p>&nbsp&nbsp&nbsp<b>Sum: %s</b>&nbsp&nbsp&nbsp</p><hr>" \
                      "&nbsp&nbsp&nbsp<b>Time:</b>&nbsp%dm %ds - %dm %ds&nbsp<br>" \
                      "<b>&nbsp&nbsp&nbspDuration:</b>&nbsp%d seconds<br>&nbsp" % (strk.count, strk.formattedNames(), strk.formattedNamesSum(), (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60), strk.duration())
            rowLines += "[ '%s', '%d', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % ("[%s] %s_deaths" % (pl.teamname, pl.name), strk.count, hintStr, (strk.start / 60), (strk.start % 60), (strk.end / 60), (strk.end % 60))

        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1), new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("[%s] %s_deaths" % (pl.teamname, pl.name))
        currentRowsLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("[%s] %s_deaths" % (pl.teamname, pl.name), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt

    allStreaksTimelineFunctionStr = allStreaksTimelineFunctionStr.replace("ALL_ROWS", rowLines)
    allStreaksTimelineFunctionStr = allStreaksTimelineFunctionStr.replace("CURRENT_ROWS", currentRowsLines)

    allStreaksTimelineDivStr = ezstatslib.HTML_SCRIPT_ALL_STREAK_TIMELINE_DIV_TAG
    timelineChartHeight = (len(allplayersByFrags) * 2 + 1) * (33 if len(allplayersByFrags) >= 4 else 35)
    allStreaksTimelineDivStr = allStreaksTimelineDivStr.replace("HEIGHT_IN_PX", str(timelineChartHeight))

    # TODO black text color for deaths
    # TODO bold players names
    # TODO folding ??

    f.write(allStreaksTimelineFunctionStr)
    # <-- all streaks timeline

    # highcharts players rank progress -->

    # get min and max values
    minRank = 10000
    maxRank = -10000
    for pl in players1:
        for minEl in matchProgressPlayers1DictEx2:
            minRank = min(minRank, minEl[pl.name][2])
            maxRank = max(maxRank, minEl[pl.name][2])

    for pl in players2:
        for minEl in matchProgressPlayers2DictEx2:
            minRank = min(minRank, minEl[pl.name][2])
            maxRank = max(maxRank, minEl[pl.name][2])
            
    # I -->
    highchartsBattleProgressFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION).replace("highchart_battle_progress", "players_rank1")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "[%s] ranks" % (players1[0].teamname))
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Rank")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "      min: %d," % (minRank))
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "      max: %d," % (maxRank))

    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \

    hcDelim = "}, {\n"
    rowLines = ""
    for pl in players1:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (pl.name)
        # rowLines += "data: [0"
        rowLines += "data: [[0,0]"

        # graphGranularity = 1.0
        # for minEl in matchProgressPlayers1Dict:
        #     rowLines += ",[%f,%d]" % (graphGranularity, minEl[pl.name][1])  # TODO format, now is 0.500000
        #     graphGranularity += 1.0

        # graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
        # for minEl in matchProgressPlayers1DictEx:
        #     rowLines += ",[%f,%d]" % (graphGranularity, minEl[pl.name][1])  # TODO format, now is 0.500000
        #     graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)

        # k = 0
        # while k < len(matchProgressPlayers1DictEx):
            # minEl = matchProgressPlayers1DictEx[k]
            # rowLines += ",[%d,%d]" % (k+1, minEl[pl.name][1])  # TODO format, now is 0.500000
            # k += 1

        curSec = -1
        curSecVal = -1
        for minEl in matchProgressPlayers1DictEx2:                        
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSecVal = minEl[pl.name][2]                
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSecVal)            
            
        rowLines += "]\n"

        # add negative zone
        rowLines += ",zones: [{ value: 0, dashStyle: 'ShortDot' }]"
        
    tickPositions = ""
    for k in xrange(matchMinutesCnt*60+1):
        if k % 60 == 0:
            tickPositions += "%d," % (k)

    xAxisLabels = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_TICK_POSITIONS
    xAxisLabels = xAxisLabels.replace("TICK_POSITIONS_VALS", tickPositions)
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", xAxisLabels)

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)

    f.write(highchartsBattleProgressFunctionStr)
    # <-- I

    # II -->
    highchartsBattleProgressFunctionStr = (ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION).replace("highchart_battle_progress", "players_rank2")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("GRAPH_TITLE", "[%s] ranks" % (players2[0].teamname))
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("Y_AXIS_TITLE", "Rank")

    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MIN_PLAYER_FRAGS", "      min: %d," % (minRank))
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", "      max: %d," % (maxRank))

    # " name: 'rea[rbf]',\n" \
    # " data: [0,7,13,18,22,24,29,36,38,42,48]\n" \

    hcDelim = "}, {\n"
    rowLines = ""
    for pl in players2:
        if rowLines != "":
            rowLines += hcDelim

        rowLines += "name: '%s',\n" % (pl.name)
        # rowLines += "data: [0"
        rowLines += "data: [[0,0]"

        # graphGranularity = 1.0
        # for minEl in matchProgressPlayers2Dict:
        #     rowLines += ",[%f,%d]" % (graphGranularity, minEl[pl.name][1])  # TODO format, now is 0.500000
        #     graphGranularity += 1.0

        # graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
        # for minEl in matchProgressPlayers2DictEx:
        #     rowLines += ",[%f,%d]" % (graphGranularity, minEl[pl.name][1])  # TODO format, now is 0.500000
        #     graphGranularity += 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)

        # k = 0
        # while k < len(matchProgressPlayers2DictEx):
            # minEl = matchProgressPlayers2DictEx[k]
            # rowLines += ",[%d,%d]" % (k+1, minEl[pl.name][1])  # TODO format, now is 0.500000
            # k += 1
            
        curSec = -1
        curSecVal = -1
        for minEl in matchProgressPlayers2DictEx2:                        
            if curSec == -1 or curSec != int(minEl[pl.name][0]):
                curSec = int(minEl[pl.name][0])
                curSecVal = minEl[pl.name][2]                
                rowLines += ",[%d,%d]" % (minEl[pl.name][0], curSecVal)               

        rowLines += "]\n"

        # add negative zone
        rowLines += ",zones: [{ value: 0, dashStyle: 'ShortDot' }]"

    tickPositions = ""
    for k in xrange(matchMinutesCnt*60+1):
        if k % 60 == 0:
            tickPositions += "%d," % (k)

    xAxisLabels = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_X_AXIS_LABELS_TICK_POSITIONS
    xAxisLabels = xAxisLabels.replace("TICK_POSITIONS_VALS", tickPositions)
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("EXTRA_XAXIS_OPTIONS", xAxisLabels)        
        
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SORTED)

    f.write(highchartsBattleProgressFunctionStr)
    # <-- II
    # <-- highcharts players rank progress

    # players achievements -->
    playersAchievementsStr = ezstatslib.HTML_PLAYERS_ACHIEVEMENTS_DIV_TAG
    cellWidth = "20px"
    achievementsHtmlTable = HTML.Table(border="0", cellspacing="0",
                                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

    for pl in allplayersByFrags:
        if len(pl.achievements) != 0:
            tableRow = HTML.TableRow(cells=[ HTML.TableCell(ezstatslib.htmlBold(pl.name), align="center", width=cellWidth) ])  # TODO player name cell width
            achIds = pl.getAchievementsIds()
            i = 0
            while i < len(pl.achievements):
                if achIds.count(pl.achievements[i].achtype) == 1:
                    tableRow.cells.append( HTML.TableCell(pl.achievements[i].generateHtmlEx(), align="center" ) )
                    i += 1
                else:
                    totalExtraInfo = ""
                    for j in xrange(achIds.count(pl.achievements[i].achtype)):
                        totalExtraInfo += "%d) %s\n" % (j+1, pl.achievements[i+j].extra_info)
                    tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(pl.achievements[i], totalExtraInfo, achIds.count(pl.achievements[i].achtype)), align="center" ) ) 
                    i += achIds.count(pl.achievements[i].achtype)

            achievementsHtmlTable.rows.append(tableRow)

    playersAchievementsStr = playersAchievementsStr.replace("PLAYERS_ACHIEVEMENTS_TABLE", str(achievementsHtmlTable) + ezstatslib.Achievement.generateAchievementsLevelLegendTable())
    # <-- players achievements

    # power ups donuts -->
    for pwrup in ["ra","ya","ga","mh"]:
        # data: [ ['Firefox', 45.0], ['IE', 26.8]]
        dataStr = ""
        valSum = 0
        for tt in teams:
            exec("val = tt.%s" % (pwrup))
            valSum += val
            dataStr += "['%s',%d]," % (tt.name, val)

        donutFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_DONUT_FUNCTION_TEMPLATE if valSum != 0 else ezstatslib.HTML_SCRIPT_HIGHCHARTS_EMPTY_DONUT_FUNCTION
        donutFunctionStr = donutFunctionStr.replace("CHART_NAME", "%s_donut" % (pwrup))

        if pwrup == "ra":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Red Armors")
        if pwrup == "ya":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Yellow Armors")
        if pwrup == "ga":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Green Armors")
        if pwrup == "mh":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Mega Healths")

        if valSum != 0:
            donutFunctionStr = donutFunctionStr.replace("ADD_ROWS", dataStr)

        f.write(donutFunctionStr)
    # <-- power ups donuts

    # team stats donuts -->
    for tstat in ["frags","kills","deaths","suicides","teamkills"]:
        # data: [ ['Firefox', 45.0], ['IE', 26.8]]
        dataStr = ""
        for tt in teams:
            exec("val = tt.%s%s" % (tstat, "()" if tstat == "frags" else ""))
            dataStr += "['%s',%d]," % (tt.name, val)

        donutFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_DONUT_FUNCTION_TEMPLATE
        donutFunctionStr = donutFunctionStr.replace("CHART_NAME", "%s_donut" % (tstat))

        if tstat == "frags":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Frags")
        if tstat == "kills":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Kills")
        if tstat == "deaths":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Deaths")
        if tstat == "suicides":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Suicides")
        if tstat == "teamkills":
            donutFunctionStr = donutFunctionStr.replace("CHART_TITLE", "Teamkills")

        donutFunctionStr = donutFunctionStr.replace("ADD_ROWS", dataStr)

        f.write(donutFunctionStr)
    # <-- team stats donuts

    # match results -->
    # matchResultsStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_MATCH_RESULTS_FUNCTION
    # f.write(matchResultsStr)

    matchResultsStr = ezstatslib.HTML_SCRIPT_TEAM_RESULTS_FUNCTION

    matchResultsStr = matchResultsStr.replace("ADD_HEADER_ROW", "['', '%s',{ role: 'annotation'},{ role: 'style'},{ role: 'tooltip'},'%s',{ role: 'annotation'},{role: 'style'},{ role: 'tooltip'}],\n" % (teams[0].name, teams[1].name))

    color1 = ""
    color2 = ""
    if "red" in teams[0].name:
        color1 = "red"
        color2 = "blue"
    elif "red" in teams[1].name:
        color1 = "blue"
        color2 = "red"
    else:
        color1 = "red"
        color2 = "blue"

    matchResultsStr = matchResultsStr.replace("ADD_STATS_ROWS", "['', %d,'%d','color: %s', '%s', %d,'%d','color: %s', '%s'],\n" % \
                                                   (teams[0].frags(), teams[0].frags(), color1, teamPlayersToString(players1), \
                                                    teams[1].frags(), teams[1].frags(), color2, teamPlayersToString(players2)) )

    f.write(matchResultsStr)
    # <-- match results

    # power ups timeline ver2 -->
    powerUpsTimelineVer2FunctionStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_FUNCTION

    rowLines = ""
    # colors = "'gray', "
    colors = []
    for col in ["red","yellow","green","#660066"]:
        colors += [col for i in xrange(len(teams))]
    colStr = ""
    for col in colors:
        colStr += "'%s'," % (col)
    colStr = colStr[:-1]

    for pwrup in ["RA","YA","GA","MH"]:
        for tt in teams:
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,0,0,0,1),  new Date(2016,1,1,0,0,0,0,2)  ],\n" % ("%s_%s" % (tt.name, pwrup))
            rowLines += "[ '%s', '', '', new Date(2016,1,1,0,%d,0,0,1), new Date(2016,1,1,0,%d,0,0,2) ],\n" % ("%s_%s" % (tt.name, pwrup), matchMinutesCnt, matchMinutesCnt)  # global value: matchMinutesCnt

    for tt in teams:
        for pu in tt.powerUps:
            rowLines += "[ '%s', '', '%s', new Date(2016,1,1,0,%d,%d), new Date(2016,1,1,0,%d,%d) ],\n" % \
                        ("%s_%s" % (tt.name, ezstatslib.powerUpTypeToString(pu.type)), \
                         " %s (%d min %d sec) " % (pu.playerName, pu.time / 60, pu.time % 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) / 60), \
                         ( ((pu.time-3) if (pu.time-3) >= 0 else 0) % 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) / 60), \
                         ( ((pu.time+3) if (pu.time+3) <= matchMinutesCnt*60 else matchMinutesCnt*60) % 60) )

    powerUpsTimelineVer2FunctionStr = powerUpsTimelineVer2FunctionStr.replace("ALL_ROWS", rowLines)
    powerUpsTimelineVer2FunctionStr = powerUpsTimelineVer2FunctionStr.replace("COLORS", colStr)

    powerUpsTimelineVer2DivStr = ezstatslib.HTML_SCRIPT_POWER_UPS_TIMELINE_VER2_DIV_TAG
    powerUpsTimelineVer2ChartHeight = (len(teams) * 4 + 1) * (33 if len(teams) >= 4 else 35)
    powerUpsTimelineVer2ChartHeight = (int)(powerUpsTimelineVer2ChartHeight * 1.5)  # TODO intersections
    powerUpsTimelineVer2DivStr = powerUpsTimelineVer2DivStr.replace("HEIGHT_IN_PX", str(powerUpsTimelineVer2ChartHeight))
    powerUpsTimelineVer2DivStr = powerUpsTimelineVer2DivStr.replace("Power Ups timeline ver.2", "Power Ups timeline")

    f.write(powerUpsTimelineVer2FunctionStr)
    # <-- power ups timeline ver2

    # highcharts RL skill -->
    # div
    rlSkillDivStrs = ""
    rowsCount = (len(allplayersByFrags) / 3) + (0 if len(allplayersByFrags) % 3 == 0 else 1)
    
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

        rlSkillFunctionStr = rlSkillFunctionStr.replace("CHART_TITLE", "[%s] %s<br>(%d / %d)" % (pl.teamname, pl.name, cnt, pl.rl_attacks))
        rlSkillFunctionStr = rlSkillFunctionStr.replace("ADD_ROWS", rlSkillRowsStr)
        f.write(rlSkillFunctionStr)
    # <-- highcharts RL skill
    
    # players kills by minutes -->
    allPlayerKillsByMinutesStr = ""
    maxValue = 0
    minValue = 0
    maxTotalValue = 0
    minTotalValue = 0
    for pl in allplayersByFrags:
        plNameEscaped = ezstatslib.escapePlayerName(pl.name)
        
        playerKillsByMinutesStr = ezstatslib.HTML_SCRIPT_PLAYER_KILLS_BY_MINUTES_FUNCTION
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("PLAYER_NAME", "%s_%s" % (pl.teamname, plNameEscaped))
        
        playerH2hElem = headToHead[pl.name]
        
        playerKillsByMinutesHeaderStr = "['Minute'"        
        for el in playerH2hElem:
            tname = ""  
            for pll in allplayersByFrags:
                if pll.name == el[0]:
                    tname = pll.teamname
            if el[0] == pl.name:
                tname = ""
            elif tname == pl.teamname:
                tname = "[MATE]"
            else:
                tname = ""
            playerKillsByMinutesHeaderStr += ",'%s%s'" % (el[0] if el[0] != pl.name else "suicides", tname)
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
                tname = ""  
                for pll in allplayersByFrags:
                    if pll.name == el[0]:
                        tname = pll.teamname
                if el[0] == pl.name:
                    tname = ""
                elif tname == pl.teamname:
                    tname = "[MATE]"
                else:
                    tname = ""
                playerKillsByMinutesRowsStr += ",%d" % (el[2][minut] if el[0] != pl.name and tname != "[MATE]" else -el[2][minut])
                if el[0] != pl.name and tname != "[MATE]":
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
            tname = ""  
            for pll in allplayersByFrags:
                if pll.name == el[0]:
                    tname = pll.teamname
            if el[0] == pl.name:
                tname = ""
            elif tname == pl.teamname:
                tname = "[MATE]"
            else:
                tname = ""
            val = 0
            if el[0] == pl.name:
                val = -pl.suicides
            elif tname == "[MATE]":
                val = -el[1]
            else:
                val = el[1]
        
            playerKillsTotalRowsStr += ",%d" % (val)
        playerKillsTotalRowsStr += "],\n"
        playerKillsByMinutesStr = playerKillsByMinutesStr.replace("ADD_TOTAL_STATS_ROWS", playerKillsTotalRowsStr)
        
        playerKillsByMinutesDivTag = ezstatslib.HTML_PLAYER_KILLS_BY_MINUTES_DIV_TAG
        playerKillsByMinutesDivTag = playerKillsByMinutesDivTag.replace("PLAYER_NAME", "%s_%s" % (pl.teamname, plNameEscaped))
        
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
    
    
    f.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)

    # add divs
    # resStr = resStr.replace("HIGHCHART_BATTLE_PROGRESS_PLACE",      ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG)
    # resStr = resStr.replace("HIGHCHART_BATTLE_PROGRESS_PLACE", "")

    resStr = resStr.replace("HIGHCHART_EXTENDED_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_EXTENDED_BATTLE_PROGRESS_DIV_TAG)

    # resStr = resStr.replace("HIGHCHART_TEAM_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM1 + "\n" + \
    #                                                                 ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM2 )
    resStr = resStr.replace("HIGHCHART_TEAM_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG)
    resStr = resStr.replace("HIGHCHART_PLAYERS_BATTLE_PROGRESS_PLACE", (ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG).replace("highchart_battle_progress", "highchart_battle_progress_players"))
    resStr = resStr.replace("STREAK_ALL_TIMELINE_PLACE", allStreaksTimelineDivStr)
    resStr = resStr.replace("HIGHCHART_PLAYERS_RANK_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_PLAYERS_RANK_PROGRESS_DIV_TAG)
    resStr = resStr.replace("PLAYERS_ACHIEVEMENTS_PLACE", playersAchievementsStr)
    # resStr = resStr.replace("POWER_UPS_DONUTS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_POWER_UPS_DONUTS_DIV_TAG)
    # resStr = resStr.replace("TEAM_STATS_DONUTS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_STATS_DONUTS_DIV_TAG)
    resStr = resStr.replace("TEAMS_STATS_DONUTS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAMS_STATS_DONUTS_DIV_TAG)
    # resStr = resStr.replace("MATCH_RESULTS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_MATCH_RESULTS_DIV_TAG)
    resStr = resStr.replace("TEAM_RESULTS", ezstatslib.HTML_TEAM_RESULTS_FUNCTION_DIV_TAG)
    resStr = resStr.replace("POWER_UPS_TIMELINE_VER2_PLACE", powerUpsTimelineVer2DivStr)
    
    resStr = resStr.replace("HIGHCHART_RL_SKILL_PLACE", rlSkillDivStrs)
    resStr = resStr.replace("HIGHCHART_PLAYER_LIFETIME_PLACE", playersLifetimeDivStrs)

    f.write(resStr)

    f.write(ezstatslib.HTML_PRE_CLOSE_TAG)

    # add script section for folding
    f.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)

    f.write(ezstatslib.HTML_FOOTER_NO_PRE)
  
formatedDateTime = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d_%H_%M_%S')
filePath     = "TEAM_" + mapName + "_" + formatedDateTime + ".html"
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
        writeHtmlWithScripts(tmpf, [team1,team2], resultString)

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
        writeHtmlWithScripts(outf, [team1,team2], resultString)

    outf.close()
    isFileNew = True

# index file
logsIndexPath    = ezstatslib.REPORTS_FOLDER + ezstatslib.TEAM_LOGS_INDEX_FILE_NAME
tmpLogsIndexPath = ezstatslib.REPORTS_FOLDER + ezstatslib.TEAM_LOGS_INDEX_FILE_NAME + ".tmp"

files = os.listdir(ezstatslib.REPORTS_FOLDER)

teamFiles = []

headerRow = HTML.TableRow(cells=[], header=True)
attrs = {} # attribs
attrs['colspan'] = 2
headerRow.cells.append( HTML.TableCell("Date", header=True) )
headerRow.cells.append( HTML.TableCell("Time", header=True) )
headerRow.cells.append( HTML.TableCell("Match", header=True) )
headerRow.cells.append( HTML.TableCell("Result", attribs=attrs, header=True) )

filesTable = HTML.Table(header_row=headerRow, border="1", cellspacing="3", cellpadding="8")

filesMap = {}  # key: dt, value: [[ [PL1,dt],[PL2,dt],..],[ [FD1,dt], [FD2,dt],.. ],[ [SD1,dt], [SD2,dt],.. ]]
zerodt = datetime(1970,1,1)
filesMap[zerodt] = []  # files with problems

for fname in files:
    if "html" in fname and "TEAM" in fname:
        teamFiles.append(fname)

        dateRes = re.search("(?<=]_).*(?=.html)", fname)

        if dateRes:
            try:
                dt = datetime.strptime(dateRes.group(0), "%Y-%m-%d_%H_%M_%S")
                dateStruct = datetime.strptime(dateRes.group(0).split("_")[0], "%Y-%m-%d")

                if not dateStruct in filesMap.keys(): # key exist
                    filesMap[dateStruct] = []

                fnamePair = [fname,dt]

                filesMap[dateStruct].append(fnamePair)

            except Exception, ex:
                filesMap[zerodt].append(fnamePair)
                break;

        else: # date parse failed
            filesMap[zerodt].append(fnamePair)

sorted_filesMap = sorted(filesMap.items(), key=itemgetter(0), reverse=True)

for el in sorted_filesMap:
    formattedDate = el[0]
    if el[0] != zerodt:
        formattedDate = el[0].strftime("%Y-%m-%d")

    pls = el[1] # array, val: [str,dt]


    pls = sorted(pls, key=lambda x: x[1], reverse=True)

    for gg in pls:
        logHeadStr = subprocess.check_output(["head", "%s" % (ezstatslib.REPORTS_FOLDER + gg[0])])
        teamsStr = ""
        if "GAME_TEAMS" in logHeadStr:
            teamsStr = logHeadStr.split("GAME_TEAMS")[1].split("-->")[0]
            teamsStr = teamsStr.replace("\n","")
            teamsStrSplit = teamsStr.split(" ")

            # TODO check for xep vs. red

        formattedTime = gg[1].strftime("%H-%M-%S")

        tableRow = HTML.TableRow(cells=[formattedDate,formattedTime])
        tableRow.cells.append( HTML.TableCell( htmlLink(gg[0], newGifTag if checkNew(isFileNew, filePath, gg[0]) else "") ) )

        if teamsStr == "":
            tableRow.cells.append( HTML.TableCell("") )
            tableRow.cells.append( HTML.TableCell("") )
        else:
            tableRow.cells.append( HTML.TableCell( ezstatslib.htmlBold(teamsStrSplit[0].replace("_","\n")), align="left" ) )
            tableRow.cells.append( HTML.TableCell(teamsStrSplit[1].replace("_","\n"), align="left") )

        filesTable.rows.append(tableRow)


logsf = open(tmpLogsIndexPath, "w")
logsf.write(ezstatslib.HTML_HEADER_STR)

logsf.write("<h1>Team logs</h1>")
# for fileName in teamFiles:
#     logsf.write( htmlLink(fileName) )

logsf.write(str(filesTable))

logsf.write(ezstatslib.HTML_FOOTER_STR)
logsf.close()

if os.path.exists(logsIndexPath):
    os.remove(logsIndexPath)
os.rename(tmpLogsIndexPath, logsIndexPath)

print filePath

print "isOverTime:", isOverTime
print "timelimit:", timelimit
print "duration:", duration
print "minutesPlayedXML:", minutesPlayedXML