#!/usr/bin/python
import pdb
import time, sys
from datetime import timedelta, date, datetime
import time
import re
from operator import itemgetter, attrgetter, methodcaller

from optparse import OptionParser,OptionValueError

import fileinput

import ezstatslib
from ezstatslib import Team,Player

def fillH2H(who,whom):
    for elem in headToHead[who]:
        if elem[0] == whom:
            elem[1] += 1

usageString = "" 
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("-f",   action="store",       dest="inputFile",      type="str",  metavar="LOG_FILE", help="")
parser.add_option("--league", action="store",   dest="leagueName",     type="str",  metavar="LEAGUE",   help="")

(options, restargs) = parser.parse_args()

if not options.leagueName:
    options.leagueName = "";

# check rest arguments
if len(restargs) != 0:
    parser.error("incorrect parameters count(%d)" % (len(restargs)))
    exit(0)

#f = open(options.inputFile, "r")
f = fileinput.input(options.inputFile)

matchdate = ""
matchlog = []
isStart = False
isEnd = False

allplayers = []
disconnectedplayers = []
dropedplayers = []
spectators = []

readLinesNum = 0

#line = f.readline()
#readLinesNum += 1
line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

#while not "matchdate" in line:
#    line = f.readline()
#matchdate = line.split("matchdate: ")[1].split("\n")[0]

while not ezstatslib.isMatchStart(line):
    if "telefrag" in line and not "teammate" in line: # telefrags before match start
        matchlog.append(line)

    if "matchdate" in line:    
        matchdate = line.split("matchdate: ")[1].split("\n")[0]

#    line = f.readline()
#    readLinesNum += 1
    line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

line = f.readline()
readLinesNum += 1
while not ezstatslib.isMatchEnd(line):
    matchlog.append(line)
#    line = f.readline()
#    readLinesNum += 1
    line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

    # rea[rbf] left the game with 23 frags
    if "left the game" in line:
        plname = line.split(" ")[0];
        pl = Player( "", plname, 0, 0, 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
        dropedplayers.append(pl); 

    # Majority votes for mapchange
    if "Majority votes for mapchange" in line:
        print "Majority votes for mapchange"
        exit(1)
        
    # Match stopped by majority vote
    if "Match stopped by majority vote" in line:
        print "Match stopped by majority vote"
        exit(1)

while not "Player statistics" in line:
#    line = f.readline()
#    readLinesNum += 1
    line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)
    

line = f.readline()  # (=================================)
line = f.readline()  # Frags (rank) . efficiency
line = f.readline()
readLinesNum += 3

while not "top scorers" in line:
    playerName = line.split(' ')[1].split(':')[0]  # zrkn:

    if playerName[0] == "_":
        playerName = playerName[1:]
        disconnectedplayers.append(playerName)


    line = f.readline()    # "  45 (2) 51.1%"
    readLinesNum += 1

    stats = line.split(' ')

    pl = Player( "", playerName, int(stats[2]), int( stats[3].split('(')[1].split(')')[0]), 0 )  #def __init__(self, teamname, name, score, origDelta, teamkills):
        
    line = f.readline() # Wp: rl52.1% sg12.2%
    readLinesNum += 1

    pl.parseWeapons(line)

    line = f.readline() # RL skill: ad:82.2 dh:25
    readLinesNum += 1
    pl.rlskill_ad = float(line.split("ad:")[1].split(" ")[0])
    pl.rlskill_dh = float(line.split("dh:")[1].split(" ")[0])

    line = f.readline() # Armr&mhs: ga:0 ya:4 ra:1 mh:1
    readLinesNum += 1
    pl.ga = int(line.split("ga:")[1].split(" ")[0])
    pl.ya = int(line.split("ya:")[1].split(" ")[0])
    pl.ra = int(line.split("ra:")[1].split(" ")[0])
    pl.mh = int(line.split("mh:")[1].split(" ")[0])

    line = f.readline() # Damage: Tkn:4279 Gvn:4217 Tm:284
    readLinesNum += 1
    pl.tkn = int(line.split("Tkn:")[1].split(" ")[0])
    pl.gvn = int(line.split("Gvn:")[1].split(" ")[0])
    pl.tm  = int(line.split("Tm:")[1].split(" ")[0])

    line = f.readline() # Streaks: Frags:3 QuadRun:0
    readLinesNum += 1
    pl.streaks = int(line.split("Streaks: Frags:")[1].split(" ")[0])

    line = f.readline() # SpawnFrags: 4
    readLinesNum += 1
    pl.spawnfrags = int(line.split("SpawnFrags: ")[1].split(" ")[0])

    allplayers.append(pl)

    while not "#" in line:
        if "top scorers" in line:
            break;
        else:
            #line = f.readline()
            #readLinesNum += 1
            line,readLinesNum = ezstatslib.readLineWithCheck(f, readLinesNum)

# check droped players and add them to allplayers collection
for pl1 in dropedplayers:
    exist = False
    for pl2 in allplayers: 
        if pl1.name == pl2.name:
            exist = True
    if not exist:
        allplayers.append(pl1);

mapName = ""
# map name
#while not "top scorers" in line:
#    line = f.readline()
mapName = line.split(" ")[0]

f.close()

# check that there are more than 1 players
if len(allplayers) == 0:
    print "No players at all"
    exit(1)

if len(allplayers) == 1:
    print "Only one player:", allplayers[0].name
    exit(1)

# check that there at least one kill
killsSum = 0
for pl in allplayers:
    killsSum += pl.origScore;
if killsSum == 0:
    print "There are no kills"
    exit(1)

# head-to-head stats init
headToHead = {}
for pl1 in allplayers:
    headToHead[pl1.name] = []
    for pl2 in allplayers:
        if pl1.name != pl2.name:
            headToHead[pl1.name].append([pl2.name,0])

progressStr = []
for logline in matchlog:
    if logline == "":
        continue

    # battle progress
#    if "time over, the game is a draw" in logline: # time over, the game is a draw
#        progressStr.append("tie (overtime)")
#        continue
#
    if "remaining" in logline or "overtime" in logline:  # [9] minutes remaining
        allplayersByFrags = sorted(allplayers, key=methodcaller("frags"), reverse=True)
        s = ""
        for pl in allplayersByFrags:
            #s += "%s%s(%d)" % ("" if s == "" else ",", pl.name, pl.frags())
            s += "{0:14s}".format(pl.name + "(" + str(pl.frags()) + ")")
        progressStr.append(s)
        continue

    # telefrag
    checkres,who,whom = ezstatslib.talefragDetection(logline, [])
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
            print "ERROR: count telefrag", who, "-", whom, ":", logline
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
            print "ERROR: count suicides"
            exit(0)

        continue

    # spectator detection
    if "Spectator" in logline: # Spectator zrkn connected
        spectators.append(logline.split(" ")[1])
        continue

    cres,who,whom,weap = ezstatslib.commonDetection(logline)

    if cres:
        if not weap in ezstatslib.possibleWeapons:
            print "ERROR: unknown weapon:", weap
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
            print "ERROR: count common", who, "-", whom, ":", logline
            exit(0)

        continue

# output
print
print "=================="
print "matchdate:", matchdate
print "map:", mapName
print

allplayersByFrags = sorted(allplayers, key=methodcaller("frags"), reverse=True)
for pl in allplayersByFrags:
    print "{0:10s} {1:3d}    ({2:s})".format(pl.name, pl.calcDelta(), pl.getFormatedStats_noTeamKills())

print
print "Power ups:"
for pl in allplayersByFrags:
    print "{0:10s}  {1:s}".format(pl.name, pl.getFormatedPowerUpsStats())

# fill final battle progress
s = ""
for pl in allplayersByFrags:
    #s += "%s%s(%d)" % ("" if s == "" else ",", pl.name, pl.frags())
    s += "{0:14s}".format(pl.name + "(" + str(pl.frags()) + ")")
progressStr.append(s)

# all players
print 
print "All players:"
print "GreenArm:   ", " [", ezstatslib.sortPlayersBy(allplayers, "ga"), "]"
print "YellowArm:  ", " [", ezstatslib.sortPlayersBy(allplayers, "ya"), "]"
print "RedArm:     ", " [", ezstatslib.sortPlayersBy(allplayers, "ra"), "]"
print "MegaHealth: ", " [", ezstatslib.sortPlayersBy(allplayers, "mh"), "]"
print
print "TakenDam:   ", " [", ezstatslib.sortPlayersBy(allplayers, "tkn"), "]"
print "GivenDam:   ", " [", ezstatslib.sortPlayersBy(allplayers, "gvn"), "]"
print "DeltaDam:   ", " [", ezstatslib.sortPlayersBy(allplayers,"damageDelta", fieldType="method"), "]"
print
print "Kills:      ", " [", ezstatslib.sortPlayersBy(allplayers, "kills"), "]"
print "Deaths:     ", " [", ezstatslib.sortPlayersBy(allplayers, "deaths"), "]"
print "Suicides:   ", " [", ezstatslib.sortPlayersBy(allplayers, "suicides"), "]"
print
print "Streaks:    ", " [", ezstatslib.sortPlayersBy(allplayers,"streaks"), "]"
print "SpawnFrags: ", " [", ezstatslib.sortPlayersBy(allplayers,"spawnfrags"), "]"
print
print "RL skill DH:", " [", ezstatslib.sortPlayersBy(allplayers, "rlskill_dh"), "]"
print "RL skill AD:", " [", ezstatslib.sortPlayersBy(allplayers, "rlskill_ad"), "]"
print 
print "Weapons:"
print "RL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "w_rl", units="%"), "]"
print "LG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "w_lg", units="%"), "]"
print "GL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "w_gl", units="%"), "]"
print "SG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "w_sg", units="%"), "]"
print "SSG:        ", " [", ezstatslib.sortPlayersBy(allplayers, "w_ssg", units="%"), "]"
print
#print "Weapons kills:"
#print "RL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "rl_kills"), "]"
#print "LG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "lg_kills"), "]"
#print "GL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "gl_kills"), "]"
#print "SG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "sg_kills"), "]"
#print "SSG:        ", " [", ezstatslib.sortPlayersBy(allplayers, "ssg_kills"), "]"
#print "TODO:       ", " [", ezstatslib.sortPlayersBy(allplayers, "TODO_kills"), "]"
#print
#print "Weapons deaths:"
#print "RL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "rl_deaths"), "]"
#print "LG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "lg_deaths"), "]"
#print "GL:         ", " [", ezstatslib.sortPlayersBy(allplayers, "gl_deaths"), "]"
#print "SG:         ", " [", ezstatslib.sortPlayersBy(allplayers, "sg_deaths"), "]"
#print "SSG:        ", " [", ezstatslib.sortPlayersBy(allplayers, "ssg_deaths"), "]"
#print "TODO:       ", " [", ezstatslib.sortPlayersBy(allplayers, "TODO_deaths"), "]"
#print
print "Players weapons:"
weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    print "{0:10s} kills  {1:3d} :: {2:100s}".format(pl.name, pl.kills, pl.getWeaponsKills(pl.kills, weaponsCheck))
    print "{0:10s} deaths {1:3d} :: {2:100s}".format("",      pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    print

if len(disconnectedplayers) != 0:
    print
    print "Disconnected players:", disconnectedplayers
    print

i = 1
print
print "battle progress:"
for p in progressStr:
    print "%d:%s %s" % (i, "" if i >= 10 else " ",  p)
    i += 1

# H2H stats
print
print "Head-to-Head stats (who :: whom)"
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    print "{0:10s} {1:3d} :: {2:100s}".format(pl.name, pl.kills, resStr)
print

if len(dropedplayers) != 0:
    dropedStr = ""
    for pl in dropedplayers:
        dropedStr += "%s," % (pl.name)

    dropedStr = dropedStr[:-1]
    print "Droped players:", dropedStr

if len(spectators) != 0:
    print "Spectators:", spectators

#for pl in allplayers:
#    print pl.name, pl.killRatio()
