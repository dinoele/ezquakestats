#!/usr/bin/python
import subprocess

groupALogs = [
              "PL_[dad2]_2016-12-07_10_43_20.html",
              "PL_[blizz]_2016-12-06_11_35_38.html",
              "PL_[baldm6]_2016-12-06_13_09_20.html",
              "PL_[utressor]_2016-12-07_12_50_30.html",
              "PL_[warfare]_2016-12-08_12_20_48.html",
              "PL_[travelert6]_2016-12-08_13_45_53.html",
             ]

groupBLogs = [
              "FD_[warfare]_2016-12-06_13_11_29.html",
              "FD_[travelert6]_2016-12-06_11_35_15.html",
              "FD_[dad2]_2016-12-07_10_36_10.html",
              "FD_[skull]_2016-12-07_12_53_46.html",
              "FD_[blizz]_2016-12-08_11_31_18.html",
              "FD_[aerowalk]_2016-12-08_13_24_12.html",
             ]

T_HEADER = \
"<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\"\n" \
"\"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n" \
"<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en-us\">\n" \
"<head>\n" \
"		<title>AdRiver Quake tournament 2016</title>\n" \
"		<link rel=\"icon\" type=\"image/png\" href=\"img/quake-icon.png\"/>\n" \
"	<link rel=\"stylesheet\" href=\"http://tablesorter.com/docs/css/jq.css\" type=\"text/css\" media=\"print, projection, screen\" />\n" \
"	<link rel=\"stylesheet\" href=\"style.css\" type=\"text/css\" id=\"\" media=\"print, projection, screen\" />\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/jquery-latest.js\"></script>\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/__jquery.tablesorter.js\"></script>\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/addons/pager/jquery.tablesorter.pager.js\"></script>\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/docs/js/chili/chili-1.8b.js\"></script>\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/docs/js/docs.js\"></script>\n" \
"	<script type=\"text/javascript\" src=\"http://tablesorter.com/docs/js/examples.js\"></script>	\n" \
"<script type=\"text/javascript\" id=\"js\">$(document).ready(function() {\n" \
"	// call the tablesorter plugin\n" \
"	//$(\"table\").tablesorter();	\n" \
"	    // call the tablesorter plugin \n" \
"	$(\"table\").tablesorter({ \n" \
"        // sort on the first column and third column, order asc \n" \
"        sortList: [[1,1]],\n" \
"        widgets: [\"zebra\"]\n" \
"    }); \n" \
"}); </script>\n" \
"</head>"



T_MAIN_HEADER = \
"<body>\n" \
"<div id=\"main\">\n"

T_GROUP_A = \
"	<div>\n" \
"		<h1>Group APOINT_ALGORITHM_PLACE</h1>\n" \
"		<table cellspacing=\"1\" class=\"tablesorter\">\n" \
"		<thead>\n" \
"				<tr>\n" \
"					<th width=12%>Player Name</th>\n" \
"					<th width=8%>Total points</th>\n" \
"					<th width=8%>warfare</th>                \n" \
"					<th width=8%>travelert6</th>\n" \
"					<th width=8%>dad2</th>\n" \
"					<th width=8%>skull</th>                \n" \
"					<th width=8%>blizz</th>\n" \
"					<th width=8%>aerowalk</th>\n" \
"					<th width=8%>baldm7</th>\n" \
"					<th width=8%>spinev2</th>\n" \
"					<th width=8%>baldm6</th>\n" \
"					<th width=8%>utressor</th>\n" \
"				</tr>\n" \
"			</thead>\n" \
"			<tbody>\n" \
"GROUP_A_MAIN" \
"			</tbody>\n" \
"		</table>\n" \
"		\n" \
"		<table cellspacing=\"1\" class=\"tablesorter\" border=\"0\">\n" \
"			<tbody>\n" \
"GROUP_A_LOGS" \
"			</tbody>\n" \
"		</table>\n" \
"	</div>\n"


T_GROUP_B = \
"	<div>\n" \
"		<h1>Group BPOINT_ALGORITHM_PLACE</h1>\n" \
"		<table cellspacing=\"1\" class=\"tablesorter\">\n" \
"		<thead>\n" \
"				<tr>\n" \
"					<th width=12%>Player Name</th>\n" \
"					<th width=8%>Total points</th>\n" \
"					<th width=8%>warfare</th>                \n" \
"					<th width=8%>travelert6</th>\n" \
"					<th width=8%>dad2</th>\n" \
"					<th width=8%>skull</th>                \n" \
"					<th width=8%>blizz</th>\n" \
"					<th width=8%>aerowalk</th>\n" \
"					<th width=8%>baldm7</th>\n" \
"					<th width=8%>spinev2</th>\n" \
"					<th width=8%>baldm6</th>\n" \
"					<th width=8%>utressor</th>\n" \
"				</tr>\n" \
"			</thead>\n" \
"			<tbody>\n" \
"GROUP_B_MAIN" \
"			</tbody>\n" \
"		</table>\n" \
"				<table cellspacing=\"1\" class=\"tablesorter\" border=\"0\">\n" \
"			<tbody>\n" \
"GROUP_B_LOGS" \
"			</tbody>\n" \
"		</table>\n" \
"	</div>\n"

T_MAIN_FOOTER = \
"</div>\n" \
"</body>\n" \
"</html>"

PLAYER_TR = \
"				<tr>\n" \
"					<td>PLAYER_NAME_PLACE</td>\n" \
"					<td>PLAYER_TOTAL_POINTS_PLACE</td>  <!-- Total -->\n" \
"PLAYER_MAPS_PLACE" \
"				</tr>\n"

MAP_TD = "					<td>POINTS</td>\n"

MATCH_LOGS_TR = \
"				<tr>\n" \
"					<td width=12%></td>\n" \
"					<td width=8%></td>\n" \
"PPPPPP" \
"				</tr>\n" \

MATCH_LOGS_EMPTY_TD  = "					<td width=8%>MatchLog</td>\n"
MATCH_LOGS_FILLED_TD = "					<td width=8%><a href=\"../LOG_NAME\">MatchLog</a></td>\n"

allMaps = ["warfare", "travelert6", "dad2", "skull", "blizz", "aerowalk", "baldm7", "spinev2", "baldm6", "utressor"]
groupA = ["zrkn", "Onanim", "SHAROK", "EEE", "random"]
groupB = ["ss", "AREXP", "girgelezobeton", "ASHOT_HEADSHOT", "twinhooker", "bw"]

def generatePlayerTR(plName, pointsDict):
    res = PLAYER_TR
    res = res.replace("PLAYER_NAME_PLACE", plName)
    totalPoints = 0
    mapsSection = ""
    for mapName in allMaps:
        if pointsDict.has_key(mapName):
            mapsSection += MAP_TD.replace("POINTS", str(pointsDict[mapName]))
            totalPoints += pointsDict[mapName]
        else:
            mapsSection += MAP_TD.replace("POINTS", "-")
    res = res.replace("PLAYER_MAPS_PLACE", mapsSection)
    res = res.replace("PLAYER_TOTAL_POINTS_PLACE", str(totalPoints))
    
    return res

def generateGroupDiv(yy, groupName, pointsAlg = 1, isDescription = False):
    group     = groupA if groupName == "A" else groupB
    groupLogs = groupALogs if groupName == "A" else groupBLogs
    
    pointsD = {}
    for nn in group:
        pointsD[nn] = {}    
    
    playedMaps = []
    for log in groupLogs:
        mapName = log.split("_")[1].replace("[","").replace("]","")
        playedMaps.append([mapName, log])
        
        logHeadStr = subprocess.check_output(["head", "%s" % ("../" + log)])
        if "GAME_PLAYERS" in logHeadStr:
            playsStr = logHeadStr.split("GAME_PLAYERS")[1].split("-->")[0]
                
        plays = []
        if playsStr != "":
            playsStr = playsStr.replace("\n","")
            plays = playsStr.split(" ")
        
        plCount = len(plays)
        i = len(plays) - 1
        pnt = 1
        while i >= 0:
            name = plays[i].split("(")[0]
            
            if not pointsD.has_key(name):
                pointsD[name] = {}
            
            pointsD[name][mapName] = pnt
            
            i -= 1
            
            if pointsAlg == 1:
                pnt += 1 if i != 0 else 2
            elif pointsAlg == 2:
                if i == 0:
                    pnt += 3
                elif i == 1:
                    pnt += 2
                else:
                    pnt += 1
            elif pointsAlg == 3:
                pnt += 1
    
    
    tt = ""    
    for k in pointsD.keys():
        tt += generatePlayerTR(k, pointsD[k])
    
    uu = ""
    for m in allMaps:
            
        logN = ""
        for xx in playedMaps:
            if xx[0] == m:
                logN = xx[1]
        
        if logN != "":
            uu += MATCH_LOGS_FILLED_TD.replace("LOG_NAME", logN)
        else:
            uu += MATCH_LOGS_EMPTY_TD
    
    ff = MATCH_LOGS_TR.replace("PPPPPP", uu)
    
    yy = yy.replace("GROUP_%s_MAIN" % (groupName), tt)
    yy = yy.replace("GROUP_%s_LOGS" % (groupName), ff)
    
    pointsDescr = ""
    if pointsAlg == 1:
        pointsDescr = "  (1->2->3->4->6)" if groupName == "A" else "  (1->2->3->4->5->7)"
    elif pointsAlg == 2:
        pointsDescr = "  (1->2->3->5->8)" if groupName == "A" else "  (1->2->3->4->6->9)"
    elif pointsAlg == 3:
        pointsDescr = "  (1->2->3->4->5)" if groupName == "A" else "  (1->2->3->4->5->6)"

    yy = yy.replace("POINT_ALGORITHM_PLACE", pointsDescr if isDescription else "")
    
    return yy

# print T_HEADER + T_MAIN_HEADER + generateGroupDiv(T_GROUP_A, "A") + generateGroupDiv(T_GROUP_B, "B") + T_MAIN_FOOTER

print T_HEADER + T_MAIN_HEADER + generateGroupDiv(T_GROUP_A, "A", 1, True) + generateGroupDiv(T_GROUP_A, "A", 2, True) + generateGroupDiv(T_GROUP_A, "A", 3, True) + \
                                 generateGroupDiv(T_GROUP_B, "B", 1, True) + generateGroupDiv(T_GROUP_B, "B", 2, True) + generateGroupDiv(T_GROUP_B, "B", 3, True) + T_MAIN_FOOTER
