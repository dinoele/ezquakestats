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
    for elem in headToHead[who]:
        if elem[0] == whom:
            elem[1] += 1

def fillExtendedBattleProgress():
    players1ByFrags = sorted(players1, key=methodcaller("frags"), reverse=True)
    s = "[%s]" % (players1[0].teamname)
    
    fragsSum = 0
    for pl in players1ByFrags:
        fragsSum += pl.frags()
    #s += " %d: " % (fragsSum)
    s += " {0:3d}: ".format(fragsSum)

    for pl in players1ByFrags:
        s += "{0:20s}".format(pl.name + "(" + str(pl.frags()) + ")")
        #s += "%s(%d)," % (pl.name, pl.frags())
    s = s[:-1]
    
    players2ByFrags = sorted(players2, key=methodcaller("frags"), reverse=True)
    
    fragsSum = 0
    for pl in players2ByFrags:
        fragsSum += pl.frags()

    s += " vs. [%s]" % (players2[0].teamname)
    s += " {0:3d}: ".format(fragsSum)
    for pl in players2ByFrags:
        s += "{0:20s}".format(pl.name + "(" + str(pl.frags()) + ")")
        #s += "%s(%d)," % (pl.name, pl.frags())
    s = s[:-1]

    extendedProgressStr.append(s)

usageString = "" 
versionString = ""
parser = OptionParser(usage=usageString, version=versionString)

parser.add_option("-f",        action="store",       dest="inputFile",      type="str",  metavar="LOG_FILE", help="")
parser.add_option("--net-log", action="store_true",  dest="netLog",         default=False,                   help="")

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
    playerName = line.split(' ')[1].split(':')[0]
    
    if playerName[0] == "_":
        playerName = playerName[1:]
        disconnectedplayers.append(playerName)

    line = f.readline()

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
    playerName = line.split(' ')[1].split(':')[0]

    if playerName[0] == "_":
        playerName = playerName[1:]
        disconnectedplayers.append(playerName)

    line = f.readline()

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
mapName = line.split(" ")[0]


# total score
totalScore = []
while not "Team scores" in line:
    line = f.readline()
line = f.readline()
line = f.readline()

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

    # battle progress
    if "time over, the game is a draw" in logline: # time over, the game is a draw
        progressStr.append("tie (overtime)")
        fillExtendedBattleProgress()
        continue

    if "remaining" in logline:  # [9] minutes remaining
        isProgressLine = True
        continue

    if isProgressLine: # Team [red] leads by 4 frags || tie
        isProgressLine = False
        if "tie" in logline:
            progressStr.append("tie")
            fillExtendedBattleProgress()
            continue
        else:
            if not "leads" in logline:
                print "ERROR: progress"
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
            print "ERROR: count teamkills"
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

print
# validate score
fragsSum1 = 0
for pl in players1:
    fragsSum1 += pl.frags()

fragsSum2 = 0
for pl in players2:
    fragsSum2 += pl.frags()

if players1[0].teamname == totalScore[0][0]:
   if fragsSum1 != totalScore[0][1]:
        print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum1, players1[0].teamname, totalScore[0][1])
   if fragsSum2 != totalScore[1][1]:
        print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum2, players2[0].teamname, totalScore[1][1])
else:
   if fragsSum2 != totalScore[0][1]:
        print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum2, players1[0].teamname, totalScore[0][1])
   if fragsSum1 != totalScore[1][1]:
        print "WARNING: frags sum(%d) for team [%s] is NOT equal to score(%d)" % (fragsSum1, players2[0].teamname, totalScore[1][1])
    

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

print "teammateTelefrags:", teammateTelefrags

# output
print
print "=================="
print "matchdate:", matchdate
print "map:", mapName
print

print "teams:"

s1 = ""
for pl in players1:
    sign = "" if s1 == "" else ", "
    if s1 == "":
        s1 = "[%s]: " % (pl.teamname)
    s1 += "%s%s" % (sign, pl.name)
print s1

s2 = ""
for pl in players2:
    sign = "" if s2 == "" else ", "
    if s2 == "":
        s2 = "[%s]: " % (pl.teamname)
    s2 += "%s%s" % (sign, pl.name)
print s2

print
print "%s[%d] x %s[%d]" % (totalScore[0][0], totalScore[0][1], totalScore[1][0], totalScore[1][1])
print

s1 = ""
players1ByFrags = sorted(players1, key=methodcaller("frags"), reverse=True)
for pl in players1ByFrags:
    if s1 == "":
        s1 = "[%s]:\n" % (pl.teamname)
    s1 +=  "{0:10s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats())
print s1

for pl in players1ByFrags:
    print "{0:10s}  {1:s}".format(pl.name, pl.getFormatedPowerUpsStats())
print

s2 = ""
players2ByFrags = sorted(players2, key=methodcaller("frags"), reverse=True)
for pl in players2ByFrags:
    if s2 == "":
        s2 = "[%s]:\n" % (pl.teamname)
    s2 +=  "{0:10s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats())
print s2

for pl in players2ByFrags:
    print "{0:10s}  {1:s}".format(pl.name, pl.getFormatedPowerUpsStats())
print

i = 1
print "battle progress:"
for p in progressStr:
    print "%d:%s %s" % (i, "" if i >= 10 else " ",  p)
    i += 1

if totalScore[0][1] > totalScore[1][1]:
    print "%d: [%s]%d" % (i, totalScore[0][0], (totalScore[0][1] - totalScore[1][1]))
else:
    print "%d: [%s]%d" % (i, totalScore[1][0], (totalScore[1][1] - totalScore[0][1]))

fillExtendedBattleProgress()
# extended battle progress
i = 1
print
print "extended battle progress:"
for p in extendedProgressStr:
    print "%d:%s %s" % (i, "" if i >= 10 else " ",  p)
    i += 1

sortedByDelta = sorted(allplayers, key=methodcaller("calcDelta"))
print
print "next captains: %s(%d) and %s(%d)" % (sortedByDelta[0].name, sortedByDelta[0].calcDelta(), sortedByDelta[1].name, sortedByDelta[1].calcDelta())

print 
print "==============================================="

# team stats output
print
print "Team stats:"
print "[%s]" % (team1.name)
print "GreenArm:   ", "{0:3d}".format(team1.ga), "  [", ezstatslib.sortPlayersBy(players1, "ga"), "]"
print "YellowArm:  ", "{0:3d}".format(team1.ya), "  [", ezstatslib.sortPlayersBy(players1, "ya"), "]"
print "RedArm:     ", "{0:3d}".format(team1.ra), "  [", ezstatslib.sortPlayersBy(players1, "ra"), "]"
print "MegaHealth: ", "{0:3d}".format(team1.mh), "  [", ezstatslib.sortPlayersBy(players1, "mh"), "]"
print
print "TakenDam: ", "{0:5d}".format(team1.tkn), "  [", ezstatslib.sortPlayersBy(players1, "tkn"), "]"
print "GivenDam: ", "{0:5d}".format(team1.gvn), "  [", ezstatslib.sortPlayersBy(players1, "gvn"), "]"
print "TeamDam:  ", "{0:5d}".format(team1.tm) , "  [", ezstatslib.sortPlayersBy(players1, "tm"), "]"
print "DeltaDam: ", "{0:5d}".format(team1.damageDelta()), "  [", ezstatslib.sortPlayersBy(players1,"damageDelta", fieldType="method"), "]"
print
print "Kills:    ", "{0:3d}".format(team1.kills),    "  [", ezstatslib.sortPlayersBy(players1, "kills"), "]"
print "Deaths:   ", "{0:3d}".format(team1.deaths),   "  [", ezstatslib.sortPlayersBy(players1, "deaths"), "]"
print "Teamkills:", "{0:3d}".format(team1.teamkills),"  [", ezstatslib.sortPlayersBy(players1, "teamkills"), "]"
print "Suicides: ", "{0:3d}".format(team1.suicides), "  [", ezstatslib.sortPlayersBy(players1, "suicides"), "]"
print
print "Streaks:    ", " [", ezstatslib.sortPlayersBy(players1,"streaks"), "]"
print "SpawnFrags: ", " [", ezstatslib.sortPlayersBy(players1,"spawnfrags"), "]"

print
print "[%s]" % (team2.name)
print "GreenArm:   ", "{0:3d}".format(team2.ga), "  [", ezstatslib.sortPlayersBy(players2, "ga"), "]"
print "YellowArm:  ", "{0:3d}".format(team2.ya), "  [", ezstatslib.sortPlayersBy(players2, "ya"), "]"
print "RedArm:     ", "{0:3d}".format(team2.ra), "  [", ezstatslib.sortPlayersBy(players2, "ra"), "]"
print "MegaHealth: ", "{0:3d}".format(team2.mh), "  [", ezstatslib.sortPlayersBy(players2, "mh"), "]"
print
print "TakenDam: ", "{0:5d}".format(team2.tkn), "  [", ezstatslib.sortPlayersBy(players2, "tkn"), "]"
print "GivenDam: ", "{0:5d}".format(team2.gvn), "  [", ezstatslib.sortPlayersBy(players2, "gvn"), "]"
print "TeamDam:  ", "{0:5d}".format(team2.tm) , "  [", ezstatslib.sortPlayersBy(players2, "tm"), "]"
print "DeltaDam: ", "{0:5d}".format(team2.damageDelta()), "  [", ezstatslib.sortPlayersBy(players2,"damageDelta", fieldType="method"), "]"
print
print "Kills:    ", "{0:3d}".format(team2.kills),    "  [", ezstatslib.sortPlayersBy(players2, "kills"), "]"
print "Deaths:   ", "{0:3d}".format(team2.deaths),   "  [", ezstatslib.sortPlayersBy(players2, "deaths"), "]"
print "Teamkills:", "{0:3d}".format(team2.teamkills),"  [", ezstatslib.sortPlayersBy(players2, "teamkills"), "]"
print "Suicides: ", "{0:3d}".format(team2.suicides), "  [", ezstatslib.sortPlayersBy(players2, "suicides"), "]"
print
print "Streaks:    ", " [", ezstatslib.sortPlayersBy(players2,"streaks"), "]"
print "SpawnFrags: ", " [", ezstatslib.sortPlayersBy(players2,"spawnfrags"), "]"

# all players
print 
print 
print "All players:"
print "GreenArm:   ", " [", ezstatslib.sortPlayersBy(allplayers, "ga"), "]"
print "YellowArm:  ", " [", ezstatslib.sortPlayersBy(allplayers, "ya"), "]"
print "RedArm:     ", " [", ezstatslib.sortPlayersBy(allplayers, "ra"), "]"
print "MegaHealth: ", " [", ezstatslib.sortPlayersBy(allplayers, "mh"), "]"
print
print "TakenDam:   ", " [", ezstatslib.sortPlayersBy(allplayers, "tkn"), "]"
print "GivenDam:   ", " [", ezstatslib.sortPlayersBy(allplayers, "gvn"), "]"
print "TeamDam:    ", " [", ezstatslib.sortPlayersBy(allplayers, "tm"), "]"
print "DeltaDam:   ", " [", ezstatslib.sortPlayersBy(allplayers,"damageDelta", fieldType="method"), "]"
print
print "Kills:      ", " [", ezstatslib.sortPlayersBy(allplayers, "kills"), "]"
print "Deaths:     ", " [", ezstatslib.sortPlayersBy(allplayers, "deaths"), "]"
print "Teamkills:  ", " [", ezstatslib.sortPlayersBy(allplayers, "teamkills"), "]"
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
print "Players weapons:"
weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    print "{0:15s} kills  {1:3d} :: {2:100s}".format("[%s]%s" % (pl.teamname, pl.name), pl.kills,  pl.getWeaponsKills(pl.kills,   weaponsCheck))
    print "{0:15s} deaths {1:3d} :: {2:100s}".format("",                                pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    print

if len(disconnectedplayers) != 0:
    print
    print "Disconnected players:", disconnectedplayers

# H2H stats
print
print "Head-to-Head stats (who :: whom)"
print "[%s]" % (team1.name)
for pl in sorted(players1, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    print "{0:10s} {1:3d} :: {2:100s}".format(pl.name, pl.kills, resStr)
print
print "[%s]" % (team2.name)
for pl in sorted(players2, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    print "{0:10s} {1:3d} :: {2:100s}".format(pl.name, pl.kills, resStr)
