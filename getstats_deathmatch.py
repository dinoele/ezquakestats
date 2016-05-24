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

# TODO error log
# TODO skip lines separate log

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
#f = fileinput.input(options.inputFile)

if options.inputFile:
    f = fileinput.input(options.inputFile)
else:
    f = sys.stdin

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

# clear players with 0 kills and 0 deaths
# TODO change progressSrt structure to be able to clean zero players in battle progress (source data: zero_player_in_stats)
# TODO clear headToHead of zero player
for pl in allplayers:
    if pl.kills == 0 and pl.deaths == 0:
        allplayers.remove(pl);

allplayersByFrags = sorted(allplayers, key=methodcaller("frags"), reverse=True)

# fill final battle progress
s = ""
for pl in allplayersByFrags:    
    s += "{0:14s}".format(pl.name + "(" + str(pl.frags()) + ")")    
progressStr.append(s)
    
# generate output string
resultString = ""
print
resultString += "\n================== " + options.leagueName + " ==================\n"
resultString += "matchdate: " + matchdate + "\n"
resultString += "map: " + mapName + "\n"
resultString += "\n"

for pl in allplayersByFrags:
    resultString += "{0:10s} {1:3d}    ({2:s})\n".format(pl.name, pl.calcDelta(), pl.getFormatedStats_noTeamKills())

resultString += "\n"
resultString += "Power ups:\n"
for pl in allplayersByFrags:
    resultString += "{0:10s}  {1:s}\n".format(pl.name, pl.getFormatedPowerUpsStats())

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
resultString += "Streaks:    " + " [ " + ezstatslib.sortPlayersBy(allplayers,"streaks") + " ]\n"
resultString += "SpawnFrags: " + " [ " + ezstatslib.sortPlayersBy(allplayers,"spawnfrags") + " ]\n"
resultString += "\n"
resultString += "RL skill DH:" + " [ " + ezstatslib.sortPlayersBy(allplayers, "rlskill_dh") + " ]\n"
resultString += "RL skill AD:" + " [ " + ezstatslib.sortPlayersBy(allplayers, "rlskill_ad") + " ]\n"
resultString += "\n"
resultString += "Weapons:\n"
resultString += "RL:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_rl", units="%") + " ]\n"
resultString += "LG:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_lg", units="%") + " ]\n"
resultString += "GL:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_gl", units="%") + " ]\n"
resultString += "SG:         " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_sg", units="%") + " ]\n"
resultString += "SSG:        " + " [ " + ezstatslib.sortPlayersBy(allplayers, "w_ssg", units="%") + " ]\n"
resultString += "\n"

resultString += "Players weapons:\n"
weaponsCheck = ezstatslib.getWeaponsCheck(allplayers)
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    resultString += "{0:10s} kills  {1:3d} :: {2:100s}\n".format(pl.name, pl.kills, pl.getWeaponsKills(pl.kills, weaponsCheck))
    resultString += "{0:10s} deaths {1:3d} :: {2:100s}\n".format("",      pl.deaths, pl.getWeaponsDeaths(pl.deaths, weaponsCheck))
    resultString += "\n"

if len(disconnectedplayers) != 0:
    resultString += "\n"
    resultString += "Disconnected players: " + str(disconnectedplayers) + "\n"
    resultString += "\n"

i = 1
resultString += "\n"
resultString += "battle progress:\n"
for p in progressStr:
    resultString += "%d:%s %s\n" % (i, "" if i >= 10 else " ",  p)
    i += 1

# H2H stats
resultString += "\n"
resultString += "Head-to-Head stats (who :: whom)\n"
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    resStr = ""
    for el in sorted(headToHead[pl.name], key=lambda x: x[1], reverse=True):
        resStr += "%s%s(%d)" % ("" if resStr == "" else ", ", el[0], el[1])
    resultString += "{0:10s} {1:3d} :: {2:100s}\n".format(pl.name, pl.kills, resStr)
resultString += "\n"

# ============================================================================================================

# Players duels table
resultString += "\n"
resultString += "Players duels:<br>"
headerRow=['', 'Frags', 'Kills']
playersNames = []
for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    headerRow.append(pl.name);
    playersNames.append(pl.name)

colAlign=[]
for i in xrange(len(headerRow)):
    colAlign.append("center")

htmlTable = HTML.Table(header_row=headerRow, border="2", cellspacing="3", col_align=colAlign,
                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")

for pl in sorted(allplayers, key=attrgetter("kills"), reverse=True):
    tableRow = HTML.TableRow(cells=[ezstatslib.htmlBold(pl.name),
                                    ezstatslib.htmlBold(pl.frags()),
                                    ezstatslib.htmlBold(pl.kills)])
        
    for plName in playersNames:
        if pl.name == plName:
            tableRow.cells.append( HTML.TableCell(pl.suicides, bgcolor=ezstatslib.BG_COLOR_GRAY) )
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
    

if len(dropedplayers) != 0:
    dropedStr = ""
    for pl in dropedplayers:
        dropedStr += "%s," % (pl.name)

    dropedStr = dropedStr[:-1]
    resultString += "Droped players: " + dropedStr + "\n"

if len(spectators) != 0:
    resultString += "Spectators: " + str(spectators) + "\n"

print resultString

# ============================================================================================================

# check and write output file
leaguePrefix = ""
if "Premier" in options.leagueName:
    leaguePrefix = "PL_"
if "First" in options.leagueName:
    leaguePrefix = "FD_"
 
formatedDateTime = datetime.strptime(matchdate, '%Y-%m-%d %H:%M:%S %Z').strftime('%Y-%m-%d_%H_%M_%S')
filePath     = leaguePrefix + mapName + "_" + formatedDateTime + ".html"
filePathFull = "../" + filePath

isFileNew = False
if os.path.exists(filePathFull):
    # temp file 
    tmpFilePathFull = "../" + filePath + ".tmp"
    if os.path.exists(tmpFilePathFull):
       os.path.remove(tmpFilePathFull)
    
    tmpf = open(tmpFilePathFull, "w")
    tmpf.write(ezstatslib.HTML_HEADER_STR)
    tmpf.write(resultString)
    tmpf.write(ezstatslib.HTML_FOOTER_STR)
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
    outf.write(ezstatslib.HTML_HEADER_STR)
    outf.write(resultString)
    outf.write(ezstatslib.HTML_FOOTER_STR)
    outf.close()
    isFileNew = True
    
    #newGifTag = "<img src=\"new2.gif\" alt=\"New\" style=\"width:48px;height:36px;\">";
    #
    # # edit contents file
    # logsIndexPath = "../" + ezstatslib.LOGS_INDEX_FILE_NAME
    # if not os.path.exists(logsIndexPath):
    #     logsf = open(logsIndexPath, "w")
    #     logsf.write(ezstatslib.HTML_HEADER_STR)
    #     logsf.write("<a href=\"" + filePath + "\">" + filePath + "</a>" + newGifTag + "\n")
    #     logsf.write(ezstatslib.HTML_FOOTER_STR)
    #     logsf.close()
    # else:
    #     logsf = open(logsIndexPath, "r")
    #     tt = logsf.readlines()        
    #     logsf.close()
    #     
    #     logsf = open(logsIndexPath, "w")
    #             
    #     tres = ""
    #     for t in tt:
    #         if newGifTag in t:
    #             t = t.replace(newGifTag, "")
    #         if "<pre>" in t:
    #             t = t.replace("<pre>", "<pre><a href=\"" + filePath + "\">" + filePath + "</a>" + newGifTag + "<br>\n")
    #         tres += t
    #         
    #     logsf.write(tres)
    #     logsf.close()
    
# update contents file
logsIndexPath    = "../" + ezstatslib.LOGS_INDEX_FILE_NAME
tmpLogsIndexPath = "../" + ezstatslib.LOGS_INDEX_FILE_NAME + ".tmp"

files = os.listdir("../")

newGifTag = "<img src=\"new2.gif\" alt=\"New\" style=\"width:48px;height:36px;\">";
headerRow = ["Date", "Premier League", "First Division"]
filesTable = HTML.Table(header_row=headerRow, border="1", cellspacing="3", cellpadding="8")

filesMap = {}  # key: dt, value: [[PL1,PL2,..],[FD1, FD2,..]]

zerodt = datetime(1970,1,1)
filesMap[zerodt] = [[],[]]  # files with problems
for fname in files:
    if "html" in fname and ("PL" in fname or "FD" in fname):
                
        #"PL_[dad2]_2016-05-23_18_45_16.html"
        #nameSplit = fname.split("_")  # ['PL', '[dad2]', '2016-05-23', '18', '45', '16.html']
        #dateSplit = nameSplit[2].split("-")        
        
        dateRes = re.search("(?<=]_).*(?=.html)", fname)
                
        if dateRes:
            try:
                dt = datetime.strptime(dateRes.group(0), "%Y-%m-%d_%H_%M_%S")
                dateStruct = datetime.strptime(dateRes.group(0).split("_")[0], "%Y-%m-%d")
            
                if not dateStruct in filesMap.keys(): # key exist
                    filesMap[dateStruct] = [[],[]]
                    
                if "PL" in fname:
                    filesMap[dateStruct][0].append(fname)
                else: # FD
                    filesMap[dateStruct][1].append(fname)
            except Exception, ex:
                if "PL" in fname:
                    filesMap[zerodt][0].append(fname)
                else: # FD
                    filesMap[zerodt][1].append(fname)
                break;
                
        else: # date parse failed
            if "PL" in fname:
                filesMap[zerodt][0].append(fname)
            else: # FD
                filesMap[zerodt][1].append(fname)
        
        
        # if isFileNew and filePath == fname:
        #     tableRow = HTML.TableRow(cells=[ HTML.TableCell("<a href=\"" + fname + "\">" + fname + "</a>" + newGifTag + "<br>\n") ])
        # else:
        #     tableRow = HTML.TableRow(cells=[ HTML.TableCell("<a href=\"" + fname + "\">" + fname + "</a>" + "<br>\n") ])
        # filesTable.rows.append(tableRow)
        # modTime = os.stat("../" + fname).st_mtime # TODO newGifTag <-> modTime

sorted_filesMap = sorted(filesMap.items(), key=itemgetter(0), reverse=True)

for el in sorted_filesMap: # el: (datetime.datetime(2016, 5, 5, 0, 0), [[], ['FD_[spinev2]_2016-05-05_16_12_52.html', 'FD_[skull]_2016-05-05_13_38_11.html']])
    formattedDate = el[0]
    if el[0] != "undef":
        formattedDate = el[0].strftime("%Y-%m-%d")
    
    maxcnt = max(len(el[1][0]), len(el[1][1]))
    attrs = {} # attribs
    attrs['rowspan'] = maxcnt
    
    tableRow = HTML.TableRow(cells=[ HTML.TableCell(formattedDate, attribs=attrs) ])
    
    i = 0
    for i in xrange(maxcnt):
        if i != 0:
            tableRow = HTML.TableRow(cells=[])
        
        if i < len(el[1][0]): # PLs
            tableRow.cells.append( HTML.TableCell("<a href=\"" + el[1][0][i] + "\">" + el[1][0][i] + "</a>" + "<br>") )
        else: # no PLs
            tableRow.cells.append( HTML.TableCell("") )
            
        if i < len(el[1][1]): # FDs
            tableRow.cells.append( HTML.TableCell("<a href=\"" + el[1][1][i] + "\">" + el[1][1][i] + "</a>" + "<br>") )
        else: # no FDs
            tableRow.cells.append( HTML.TableCell("") )
            
        filesTable.rows.append(tableRow)
        i += 1

logsf = open(tmpLogsIndexPath, "w")
logsf.write(ezstatslib.HTML_HEADER_STR)
logsf.write(str(filesTable))
logsf.write(ezstatslib.HTML_FOOTER_STR)
logsf.close()

if os.path.exists(logsIndexPath):
    os.remove(logsIndexPath)
os.rename(tmpLogsIndexPath, logsIndexPath)

    
