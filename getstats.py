#!/usr/bin/python
import pdb
import time, sys
from datetime import timedelta, date, datetime
import time
import re
from operator import itemgetter, attrgetter, methodcaller

from optparse import OptionParser,OptionValueError

import fileinput
import os.path

import ezstatslib
from ezstatslib import Team,Player

import HTML

import random

# TODO use ezstatslib.readLineWithCheck
# TODO error log
# TODO skip lines separate log
# TODO remove all prints
# TODO write htmls
# TODO make index file

COMMAND_LOG_LOCAL_SMALL_DELIM = "__________";
COMMAND_LOG_LOCAL_BIG_DELIM   = "___________________________________";

COMMAND_LOG_NET_SMALL_DELIM   = "(========)";
COMMAND_LOG_NET_BIG_DELIM     = "(=================================)";

teammateTelefrags = [] # array of names who was telegragged by teammates

def fillH2H(who,whom):
    try:
        for elem in headToHead[who]:
            if elem[0] == whom:
                elem[1] += 1
    except Exception, ex:
        ezstatslib.logError("fillH2H: who=%s, whom=%s, ex=%s\n" % (who, whom, ex))

def fillExtendedBattleProgress():
    players1ByFrags = sorted(players1, key=methodcaller("frags"), reverse=True)
    s = "[%s]" % (players1[0].teamname)
    
    fragsSum = 0
    for pl in players1ByFrags:
        fragsSum += pl.frags()
    s += " {0:3d}: ".format(fragsSum)

    for pl in players1ByFrags:
        s += "{0:20s}".format(pl.name + "(" + str(pl.frags()) + ")")
    s = s[:-1]
    
    players2ByFrags = sorted(players2, key=methodcaller("frags"), reverse=True)
    
    fragsSum = 0
    for pl in players2ByFrags:
        fragsSum += pl.frags()

    s += " vs. [%s]" % (players2[0].teamname)
    s += " {0:3d}: ".format(fragsSum)
    for pl in players2ByFrags:
        s += "{0:20s}".format(pl.name + "(" + str(pl.frags()) + ")")
    s = s[:-1]

    extendedProgressStr.append(s)

usageString = "" 
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("-f",        action="store",       dest="inputFile",      type="str",  metavar="LOG_FILE", help="")
parser.add_option("--net-log", action="store_true",  dest="netLog",         default=False,                   help="")
parser.add_option("--scripts", action="store_false",   dest="withScripts", default=True,   help="")

(options, restargs) = parser.parse_args()

# check rest arguments
if len(restargs) != 0:
    parser.error("incorrect parameters count(%d)" % (len(restargs)))
    exit(0)

if options.inputFile:
    f = fileinput.input(options.inputFile)
else:
    f = sys.stdin

matchdate = ""
matchlog = []
isStart = False
isEnd = False

teamNames = []
matchProgressDict = []
matchProgressPlayers1Dict = []
matchProgressPlayers2Dict = []

players1 = []
players2 = []
allplayers = []
disconnectedplayers = []

smallDelimiter = COMMAND_LOG_NET_SMALL_DELIM if options.netLog else COMMAND_LOG_LOCAL_SMALL_DELIM;
bigDelimiter   = COMMAND_LOG_NET_BIG_DELIM   if options.netLog else COMMAND_LOG_LOCAL_BIG_DELIM;

line = f.readline() 
#while not "matchdate" in line:
#    line = f.readline()
#matchdate = line.split("matchdate: ")[1].split("\n")[0]

while not ezstatslib.isMatchStart(line):
    if "telefrag" in line and not "teammate" in line: # telefrags before match start
        matchlog.append(line)
        
    if "matchdate" in line:
        if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
            matchStartStamp = int( line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[0] )
            line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
            
        matchdate = line.split("matchdate: ")[1].split("\n")[0]            

    line = f.readline()

line = f.readline()
while not ezstatslib.isMatchEnd(line):
    matchlog.append(line)
    line = f.readline()
    
# team 1
while not "Team [" in line:
    line = f.readline()
teamName1 = line.split('[')[1].split(']')[0]


line = f.readline()
while not "Team [" in line:
    while not smallDelimiter in line:
        line = f.readline()

        if "Team [" in line:
            break

    if "Team [" in line:
        break

    line = f.readline()
    
    if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
        line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
    
    playerName = line.split(' ')[1].split(':')[0]
    
    if playerName[0] == "_" or playerName[0] == "#":
        playerName = playerName[1:]
        disconnectedplayers.append(playerName)

    line = f.readline()
    if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
        line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]

    #"  24 (-25) 10 32.9%"
    stats = line.split(' ')
    pl = Player( teamName1, playerName, int(stats[2]), int( stats[3].split('(')[1].split(')')[0]), int(stats[4]) )
    
    line = f.readline() # Wp: rl52.1% sg12.2%
    pl.parseWeapons(line)

    line = f.readline() # RL skill: ad:82.2 dh:25
    pl.rlskill_ad = float(line.split("ad:")[1].split(" ")[0])
    pl.rlskill_dh = float(line.split("dh:")[1].split(" ")[0])

    line = f.readline() # Armr&mhs: ga:0 ya:4 ra:1 mh:1
    pl.ga = int(line.split("ga:")[1].split(" ")[0])
    pl.ya = int(line.split("ya:")[1].split(" ")[0])
    pl.ra = int(line.split("ra:")[1].split(" ")[0])
    pl.mh = int(line.split("mh:")[1].split(" ")[0])

    line = f.readline() # Powerups: Q:0 P:0 R:0
    line = f.readline() # RL: Took:30 Killed:15 Dropped:28

    line = f.readline() # Damage: Tkn:4279 Gvn:4217 Tm:284
    pl.tkn = int(line.split("Tkn:")[1].split(" ")[0])
    pl.gvn = int(line.split("Gvn:")[1].split(" ")[0])
    pl.tm  = int(line.split("Tm:")[1].split(" ")[0])

    line = f.readline() # Streaks: Frags:3 QuadRun:0
    pl.streaks = int(line.split("Streaks: Frags:")[1].split(" ")[0])

    line = f.readline() # SpawnFrags: 4
    pl.spawnfrags = int(line.split("SpawnFrags: ")[1].split(" ")[0])

    players1.append(pl)
    allplayers.append(pl)

    line = f.readline()


# team 2
#while not "Team [" in line:
#    line = f.readline()
teamName2 = line.split('[')[1].split(']')[0]


line = f.readline()
while not bigDelimiter in line:
    while not smallDelimiter in line:
        line = f.readline()

        if bigDelimiter in line:
            break

    if bigDelimiter in line:
        break

    line = f.readline()
    if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
        line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
    
    playerName = line.split(' ')[1].split(':')[0]

    if playerName[0] == "_":
        playerName = playerName[1:]
        disconnectedplayers.append(playerName)

    line = f.readline()
    if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
        line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]

    #"  24 (-25) 10 32.9%"
    stats = line.split(' ')
    pl = Player( teamName2, playerName, int(stats[2]), int( stats[3].split('(')[1].split(')')[0]), int(stats[4]) )
    
    line = f.readline() # Wp: rl52.1% sg12.2%
    pl.parseWeapons(line)

    line = f.readline() # RL skill: ad:82.2 dh:25
    pl.rlskill_ad = float(line.split("ad:")[1].split(" ")[0])
    pl.rlskill_dh = float(line.split("dh:")[1].split(" ")[0])

    line = f.readline() # Armr&mhs: ga:0 ya:4 ra:1 mh:1
    pl.ga = int(line.split("ga:")[1].split(" ")[0])
    pl.ya = int(line.split("ya:")[1].split(" ")[0])
    pl.ra = int(line.split("ra:")[1].split(" ")[0])
    pl.mh = int(line.split("mh:")[1].split(" ")[0])

    line = f.readline() # Powerups: Q:0 P:0 R:0
    line = f.readline() # RL: Took:30 Killed:15 Dropped:28

    line = f.readline() # Damage: Tkn:4279 Gvn:4217 Tm:284
    pl.tkn = int(line.split("Tkn:")[1].split(" ")[0])
    pl.gvn = int(line.split("Gvn:")[1].split(" ")[0])
    pl.tm  = int(line.split("Tm:")[1].split(" ")[0])

    line = f.readline() # Streaks: Frags:3 QuadRun:0
    pl.streaks = int(line.split("Streaks: Frags:")[1].split(" ")[0])

    line = f.readline() # SpawnFrags: 4
    pl.spawnfrags = int(line.split("SpawnFrags: ")[1].split(" ")[0])

    players2.append(pl)
    allplayers.append(pl)

    line = f.readline()

# teams stats parse
while not "weapons, powerups, armors&mhs, damage" in line:
    line = f.readline()
line = f.readline()
line = f.readline() # [xep]: Wp: rl41 gl5 sg14% ssg14%
teamName = line.split("]")[0].split("[")[1]

team1 = Team(teamName)
line = f.readline() # Powerups: Q:0 P:0 R:0

line = f.readline() # Armr&mhs: ga:0 ya:24 ra:13 mh:13
team1.ga = int(line.split("ga:")[1].split(" ")[0])
team1.ya = int(line.split("ya:")[1].split(" ")[0])
team1.ra = int(line.split("ra:")[1].split(" ")[0])
team1.mh = int(line.split("mh:")[1].split(" ")[0])

line = f.readline() # RL: Took:93 Killed:66 Dropped:88

line = f.readline() # Damage: Tkn:15750 Gvn:15831 Tm:1916
team1.tkn = int(line.split("Tkn:")[1].split(" ")[0])
team1.gvn = int(line.split("Gvn:")[1].split(" ")[0])
team1.tm  = int(line.split("Tm:")[1].split(" ")[0])

line = f.readline() # [xep]: Wp: rl41 gl5 sg14% ssg14%
teamName = line.split("]")[0].split("[")[1]
team2 = Team(teamName)
line = f.readline() # Powerups: Q:0 P:0 R:0

line = f.readline() # Armr&mhs: ga:0 ya:24 ra:13 mh:13
team2.ga = int(line.split("ga:")[1].split(" ")[0])
team2.ya = int(line.split("ya:")[1].split(" ")[0])
team2.ra = int(line.split("ra:")[1].split(" ")[0])
team2.mh = int(line.split("mh:")[1].split(" ")[0])

line = f.readline() # RL: Took:93 Killed:66 Dropped:88

line = f.readline() # Damage: Tkn:15750 Gvn:15831 Tm:1916
team2.tkn = int(line.split("Tkn:")[1].split(" ")[0])
team2.gvn = int(line.split("Gvn:")[1].split(" ")[0])
team2.tm  = int(line.split("Tm:")[1].split(" ")[0])

mapName = ""
# map name
while not "top scorers" in line:
    line = f.readline()
    
if ezstatslib.LOG_TIMESTAMP_DELIMITER in line:
    line = line.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]
    
mapName = line.split(" ")[0]


# total score
totalScore = []
while not "Team scores" in line:
    line = f.readline()
line = f.readline()
line = f.readline()

if not ezstatslib.LOG_TIMESTAMP_DELIMITER in line:  # TODO incorrect dates in netlog 
    if "+" in line and "=" in line:
        totalScore.append( [line.split(":")[0].split("[")[1].split("]")[0], int(line.split("= ")[1].split(" ")[0])] )
    else:
        totalScore.append( [line.split(":")[0].split("[")[1].split("]")[0], int(line.split(" ")[1])] )
    
    line = f.readline()
    
    if "+" in line and "=" in line:
        totalScore.append( [line.split(":")[0].split("[")[1].split("]")[0], int(line.split("= ")[1].split(" ")[0])] )
    else:
        totalScore.append( [line.split(":")[0].split("[")[1].split("]")[0], int(line.split(" ")[1])] )

f.close()

# head-to-head stats init
headToHead = {}
for pl1 in allplayers:
    headToHead[pl1.name] = []
    for pl2 in allplayers:
        if pl1.name != pl2.name and pl1.teamname != pl2.teamname:
            headToHead[pl1.name].append([pl2.name,0])

progressStr = []
extendedProgressStr = []
isProgressLine = False
for logline in matchlog:
    if logline == "":
        continue

    if ezstatslib.LOG_TIMESTAMP_DELIMITER in logline:
        logline = logline.split(ezstatslib.LOG_TIMESTAMP_DELIMITER)[1]

    # battle progress
    if "remaining" in logline:  # [9] minutes remaining
        isProgressLine = True
        continue

    if isProgressLine or "time over, the game is a draw" in logline: # Team [red] leads by 4 frags || tie || time over, the game is a draw
        isProgressLine = False
        
        # TODO replace with frags when teams stats are updated on each increment
        progressLineDict = {}
        
        fr1 = 0
        for pl in players1:
            fr1 += pl.frags()
        fr2 = 0
        for pl in players2:
            fr2 += pl.frags()        
        
        progressLineDict[team1.name] = fr1;  # team1.frags()
        progressLineDict[team2.name] = fr2; # team2.frags()
        matchProgressDict.append(progressLineDict)
        
        players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict1 = {}
        for pl in players1ByFrags:
            playersProgressLineDict1[pl.name] = pl.frags();
        matchProgressPlayers1Dict.append(playersProgressLineDict1)
        
        players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
        playersProgressLineDict2 = {}
        for pl in players2ByFrags:
            playersProgressLineDict2[pl.name] = pl.frags();
        matchProgressPlayers2Dict.append(playersProgressLineDict2)        
        
        
        if "time over, the game is a draw" in logline:
            progressStr.append("tie (overtime)")
            fillExtendedBattleProgress()
            continue
        elif "tie" in logline:
            progressStr.append("tie")
            fillExtendedBattleProgress()
            continue
        else:
            if not "leads" in logline:
                # print "ERROR: progress"
                exit(0)                
            sp = logline.split(" ")
            progressStr.append("%s%s" % (sp[1], sp[4]))
            fillExtendedBattleProgress()
            continue
    
    checkres,checkname = ezstatslib.teamkillDetection(logline)
    if checkres:
        isFound = False
        for pl in allplayers:
            if pl.name == checkname:
                pl.teamkills += 1
                isFound = True
                break;
        if not isFound:
            # print "ERROR: count teamkills"
            exit(0)

        continue

    # telefrag
    checkres,who,whom = ezstatslib.talefragDetection(logline, teammateTelefrags)
    if checkres:
        isFoundWho = False if who != "" else True
        isFoundWhom = False
        for pl in allplayers:
            if who != "" and pl.name == who:
                pl.kills += 1
                pl.tele_kills += 1
                isFoundWho = True
            
            if pl.name == whom:
                pl.deaths += 1
                pl.tele_deaths += 1
                isFoundWhom = True
                
        if who != "":
            fillH2H(who,whom)

        if not isFoundWho or not isFoundWhom:
            # print "ERROR: count telefrag", who, "-", whom, ":", logline
            exit(0)

        continue

    checkres,checkname = ezstatslib.suicideDetection(logline)
    if checkres:
        isFound = False
        for pl in allplayers:
            if pl.name == checkname:
                pl.suicides += 1
                isFound = True
                break;
        if not isFound:
            # print "ERROR: count suicides"
            exit(0)

        continue

    cres,who,whom,weap = ezstatslib.commonDetection(logline)
    if cres:
        if not weap in ezstatslib.possibleWeapons:
            # print "ERROR: unknown weapon:", weap
            exit(0)

        isFoundWho = False
        isFoundWhom = False
        for pl in allplayers:
            if pl.name == who:
                pl.kills += 1
                exec("pl.%s_kills += 1" % (weap))
                isFoundWho = True
            
            if pl.name == whom:
                pl.deaths += 1
                exec("pl.%s_deaths += 1" % (weap))
                isFoundWhom = True
                
        fillH2H(who,whom)
        
        if not isFoundWho or not isFoundWhom:
            ezstatslib.logError("ERROR: count common %s-%s: %s\n" % (who, whom, logline))
        
        continue
    

# validate score
fragsSum1 = 0
for pl in players1:
    fragsSum1 += pl.frags()

fragsSum2 = 0
for pl in players2:
    fragsSum2 += pl.frags()

if len(totalScore) != 0:
    if players1[0].teamname == totalScore[0][0]:
       if fragsSum1 != totalScore[0][1]:
            # print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum1, players1[0].teamname, totalScore[0][1])
            pass
       if fragsSum2 != totalScore[1][1]:
            # print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum2, players2[0].teamname, totalScore[1][1])
            pass
    else:
       if fragsSum2 != totalScore[0][1]:
            # print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum2, players1[0].teamname, totalScore[0][1])
            pass
       if fragsSum1 != totalScore[1][1]:
            # print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum1, players2[0].teamname, totalScore[1][1])
            pass
else:
    totalScore.append( [players1[0].teamname, fragsSum1] )
    totalScore.append( [players2[0].teamname, fragsSum2] )
    

# fill team kills/deaths/teamkills/suicides
for pl in players1:
    team1.kills += pl.kills
    team1.deaths += pl.deaths
    team1.teamkills += pl.teamkills
    team1.suicides += pl.suicides

for pl in players2:
    team2.kills += pl.kills
    team2.deaths += pl.deaths
    team2.teamkills += pl.teamkills
    team2.suicides += pl.suicides

# TODO add teammateTelefrags to team score
# print "teammateTelefrags:", teammateTelefrags

# generate output string
resultString = ""

resultString += "==================\n"
resultString += "matchdate:" + matchdate + "\n"
resultString += "map:" + mapName + "\n"
resultString += "\n"

resultString += "teams:\n"

s1 = ""
for pl in players1:
    sign = "" if s1 == "" else ", "
    if s1 == "":
        s1 = "[%s]: " % (pl.teamname)
    s1 += "%s%s" % (sign, pl.name)
resultString += s1 + "\n"

s2 = ""
for pl in players2:
    sign = "" if s2 == "" else ", "
    if s2 == "":
        s2 = "[%s]: " % (pl.teamname)
    s2 += "%s%s" % (sign, pl.name)
resultString += s2 + "\n"

resultString += "\n"
resultString += "%s[%d] x %s[%d]\n" % (totalScore[0][0], totalScore[0][1], totalScore[1][0], totalScore[1][1])
resultString += "\n"

s1 = ""
players1ByFrags = sorted(players1, key=methodcaller("frags"), reverse=True)
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
players2ByFrags = sorted(players2, key=methodcaller("frags"), reverse=True)
for pl in players2ByFrags:
    if s2 == "":
        s2 = "[%s]:\n" % (pl.teamname)
    s2 +=  "{0:20s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats())
resultString += s2
resultString += "\n"

for pl in players2ByFrags:
    resultString += "{0:20s}  {1:s}\n".format(pl.name, pl.getFormatedPowerUpsStats())
resultString += "\n"

i = 1
resultString += "battle progress:\n"
for p in progressStr:
    resultString += "%d:%s %s\n" % (i, "" if i >= 10 else " ",  p)
    i += 1

if totalScore[0][1] > totalScore[1][1]:
    resultString += "%d: [%s]%d\n" % (i, totalScore[0][0], (totalScore[0][1] - totalScore[1][1]))
else:
    resultString += "%d: [%s]%d\n" % (i, totalScore[1][0], (totalScore[1][1] - totalScore[0][1]))

progressLineDict = {}
progressLineDict[team1.name] = team1.frags();
progressLineDict[team2.name] = team2.frags();
matchProgressDict.append(progressLineDict)

players1ByFrags = sorted(players1, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
playersProgressLineDict1 = {}
for pl in players1ByFrags:
    playersProgressLineDict1[pl.name] = pl.frags();
matchProgressPlayers1Dict.append(playersProgressLineDict1)

players2ByFrags = sorted(players2, key=lambda x: (x.frags(), x.kills, x.calcDelta()), reverse=True)
playersProgressLineDict2 = {}
for pl in players2ByFrags:
    playersProgressLineDict2[pl.name] = pl.frags();
matchProgressPlayers2Dict.append(playersProgressLineDict2)        

fillExtendedBattleProgress()
# extended battle progress
i = 1
resultString += "\n"
resultString += "extended battle progress:\n"
for p in extendedProgressStr:
    resultString += "%d:%s %s\n" % (i, "" if i >= 10 else " ",  p)
    i += 1

if options.withScripts:
    resultString += "\nHIGHCHART_BATTLE_PROGRESS_PLACE\n"
    
if options.withScripts:
    resultString += "\nHIGHCHART_TEAM_BATTLE_PROGRESS_PLACE\n"

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
resultString += "Streaks:    " + " [" + ezstatslib.sortPlayersBy(players1,"streaks") + "]\n"
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
resultString += "Streaks:    " + " [" + ezstatslib.sortPlayersBy(players2,"streaks") + "]\n"
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
resultString += "Streaks:    " + " [" +  ezstatslib.sortPlayersBy(allplayers,"streaks") + "]\n"
resultString += "SpawnFrags: " + " [" +  ezstatslib.sortPlayersBy(allplayers,"spawnfrags") + "]\n"
resultString += "\n"
resultString += "RL skill DH:" + " [" +  ezstatslib.sortPlayersBy(allplayers, "rlskill_dh") + "]\n"
resultString += "RL skill AD:" + " [" +  ezstatslib.sortPlayersBy(allplayers, "rlskill_ad") + "]\n"
resultString += "\n"
resultString += "Weapons:\n"
resultString += "RL:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_rl", units="%") + "]\n"
resultString += "LG:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_lg", units="%") + "]\n"
resultString += "GL:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_gl", units="%") + "]\n"
resultString += "SG:         " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_sg", units="%") + "]\n"
resultString += "SSG:        " + " [" +  ezstatslib.sortPlayersBy(allplayers, "w_ssg", units="%") + "]\n"
resultString += "\n"

resultString += "Players weapons:\n"
weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    resultString += "{0:23s} kills  {1:3d} :: {2:100s}\n".format("[%s]%s" % (pl.teamname, pl.name), pl.kills,  pl.getWeaponsKills(pl.kills,   weaponsCheck))
    resultString += "{0:23s} deaths {1:3d} :: {2:100s}\n".format("",                                pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    resultString += "\n"

if len(disconnectedplayers) != 0:
    resultString += "\n"
    resultString += "Disconnected players:" + str(disconnectedplayers) + "\n"

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

# Players duels table
# allplayersByFrags = sorted(allplayers, key=methodcaller("frags"), reverse=True)
# resultString += "\n"
# resultString += "Players duels:<br>"
# headerRow=['', 'Frags', 'Kills', 'Deaths']
# playersNames = []
# for pl in allplayersByFrags:
#     headerRow.append(pl.name);
#     playersNames.append(pl.name)
# 
# colAlign=[]
# for i in xrange(len(headerRow)):
#     colAlign.append("center")
# 
# htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
#                        style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
# 
# for pl in allplayersByFrags:
#     tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
#                                     ezstatslib.htmlBold(pl.frags()),
#                                     ezstatslib.htmlBold(pl.kills),
#                                     ezstatslib.htmlBold(pl.deaths)])
#         
#     for plName in playersNames:
#         if pl.name == plName:
#             tableRow.cells.append( HTML.TableCell(str(pl.suicides), bgcolor=ezstatslib.BG_COLOR_GRAY) )
#         else:            
#             plKills = 0
#             for val in headToHead[pl.name]:
#                 if val[0] == plName:
#                     plKills = val[1]
#             
#             plDeaths = 0
#             for val in headToHead[plName]:
#                 if val[0] == pl.name:
#                     plDeaths = val[1]
#             
#             cellVal = "%s / %s" % (ezstatslib.htmlBold(plKills)  if plKills  > plDeaths else str(plKills),
#                                    ezstatslib.htmlBold(plDeaths) if plDeaths > plKills  else str(plDeaths))
#             
#             cellColor = ""
#             if plKills == plDeaths:
#                 cellColor = ezstatslib.BG_COLOR_LIGHT_GRAY
#             elif plKills > plDeaths:
#                 cellColor = ezstatslib.BG_COLOR_GREEN
#             else:
#                 cellColor = ezstatslib.BG_COLOR_RED
#             
#             tableRow.cells.append( HTML.TableCell(cellVal, bgcolor=cellColor) )
#             
#     htmlTable.rows.append(tableRow)  
# 
# resultString += str(htmlTable)

resultString += "\n"
resultString += "Players duels:<br>"

# team1
headerRow=["[" + team2.name + "]", 'Frags', 'Kills', 'Deaths']
playersNames = []
for pl in players1ByFrags:
    headerRow.append(pl.name);
    playersNames.append(pl.name)

colAlign=[]
for i in xrange(len(headerRow)):
    colAlign.append("center")

htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

for pl in players2ByFrags:
    tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                    ezstatslib.htmlBold(pl.frags()),
                                    ezstatslib.htmlBold(pl.kills),
                                    ezstatslib.htmlBold(pl.deaths)])
        
    for pll in players1ByFrags:
        plName = pll.name
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

# team 2
htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
resultString += "\n"
headerRow=["[" + team1.name + "]", 'Frags', 'Kills', 'Deaths']
playersNames = []
for pl in players2ByFrags:
    headerRow.append(pl.name);
    playersNames.append(pl.name)

colAlign=[]
for i in xrange(len(headerRow)):
    colAlign.append("center")

htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

for pl in players1ByFrags:
    tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                    ezstatslib.htmlBold(pl.frags()),
                                    ezstatslib.htmlBold(pl.kills),
                                    ezstatslib.htmlBold(pl.deaths)])
        
    for pll in players2ByFrags:
        plName = pll.name
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

resultString += "\nTeammate telefrags: " + str(teammateTelefrags) + "\n"

print resultString

def writeHtmlWithScripts(f, teams, resStr):    
    pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
    pageTitle = "%s %s %s" % ("TEAM", mapName, matchdate)  # global values
    pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", pageTitle)
    
    f.write(pageHeaderStr)
    
    # highcharts battle progress -->
    highchartsBattleProgressFunctionStr = ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION
            
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
        
        # graphGranularity = 1.0 / (float)(ezstatslib.HIGHCHARTS_BATTLE_PROGRESS_GRANULARITY)
        graphGranularity = 1.0
        for minEl in matchProgressDict:
            rowLines += ",[%f,%d]" % (graphGranularity, minEl[tt.name])  # TODO format, now is 0.500000
            graphGranularity += 1.0
            
        rowLines += "]\n"        
    
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("ADD_STAT_ROWS", rowLines)
    
    # tooltip style
    highchartsBattleProgressFunctionStr = highchartsBattleProgressFunctionStr.replace("TOOLTIP_STYLE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_FUNCTION_TOOLTIP_SIMPLE)
                
    f.write(highchartsBattleProgressFunctionStr)
    # <-- highcharts battle progress
    
    # highcharts teams battle progress -->
    matchMinutesCnt = len(matchProgressDict)
    
    minutesStr = ""
    for i in xrange(1,matchMinutesCnt+1):
        minutesStr += "'%d'," % (i)
    minutesStr = minutesStr[:-1]
    
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
                plPoints += "%d," % (minEl[pl.name])
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
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("ADD_ROWS", rowLines)
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("TEAM_POINTS", teamPointsStr)
        
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("MAX_PLAYER_FRAGS", str(int(maxPlayerFrags*1.2)))
        highchartsTeamBattleProgressFunctionStr = highchartsTeamBattleProgressFunctionStr.replace("MAX_TOTAL_FRAGS",  str(int(maxTotalFrags*1.2)))
                    
        f.write(highchartsTeamBattleProgressFunctionStr)
        
        tn = 2
    # <-- highcharts teams battle progress
    
    f.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)
    
    # add divs
    resStr = resStr.replace("HIGHCHART_BATTLE_PROGRESS_PLACE",      ezstatslib.HTML_SCRIPT_HIGHCHARTS_BATTLE_PROGRESS_DIV_TAG)
    # resStr = resStr.replace("HIGHCHART_TEAM_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM1 + "\n" + \
    #                                                                 ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG_TEAM2 )
    resStr = resStr.replace("HIGHCHART_TEAM_BATTLE_PROGRESS_PLACE", ezstatslib.HTML_SCRIPT_HIGHCHARTS_TEAM_BATTLE_PROGRESS_DIV_TAG)
    
    f.write(resStr)
    
    f.write(ezstatslib.HTML_PRE_CLOSE_TAG)
    
    # add script section for folding
    f.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)  
       
    f.write(ezstatslib.HTML_FOOTER_NO_PRE)


formatedDateTime = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S %Z').strftime('%Y-%m-%d_%H_%M_%S')
filePath     = "TEAM_" + mapName + "_" + formatedDateTime + ".html"
filePathFull = "../" + filePath

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

# TODO move to lib
def htmlLink(fname, gifPath = "", linkText = "", isBreak = True):
    return "<a href=\"%s\">%s</a>%s%s" % (fname, fname if linkText == "" else linkText, gifPath, "<br>" if isBreak else "")

# index file
logsIndexPath    = "../" + ezstatslib.TEAM_LOGS_INDEX_FILE_NAME
tmpLogsIndexPath = "../" + ezstatslib.TEAM_LOGS_INDEX_FILE_NAME + ".tmp"

files = os.listdir("../")

teamFiles = []

headerRow = HTML.TableRow(cells=[], header=True)
attrs = {} # attribs    
attrs['colspan'] = 2
headerRow.cells.append( HTML.TableCell("Date", header=True) )
headerRow.cells.append( HTML.TableCell("Time", header=True) )
headerRow.cells.append( HTML.TableCell("Matches", attribs=attrs, header=True) )

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
        formattedTime = gg[1].strftime("%H-%M-%S")        
        
        tableRow = HTML.TableRow(cells=[formattedDate,formattedTime])        
        tableRow.cells.append( HTML.TableCell( htmlLink(gg[0]) ) )
        
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