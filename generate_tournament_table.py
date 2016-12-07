
import subprocess

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



T_MAIN = \
"<body>\n" \
"<div id=\"main\">\n" \
"	<div>\n" \
"		<h1>Group A</h1>\n" \
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
"	</div>\n" \
"	<div>\n" \
"		<h1>Group B</h1>\n" \
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
"	</div>\n" \
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

groupALogs = ["PL_[dad2]_2016-12-07_10_43_20.html","PL_[blizz]_2016-12-06_11_35_38.html","PL_[baldm6]_2016-12-06_13_09_20.html","PL_[utressor]_2016-12-07_12_50_30.html"]
groupBLogs = ["FD_[warfare]_2016-12-06_13_11_29.html","FD_[travelert6]_2016-12-06_11_35_15.html","FD_[dad2]_2016-12-07_10_36_10.html","FD_[skull]_2016-12-07_12_53_46.html"]

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
    
def A():
    pointsD = {}
    for nn in groupA:
        pointsD[nn] = {}    
    
    playedMaps = []
    for log in groupALogs:
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
            pnt += 1 if i != 0 else 2
    
    
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
    
    yy = T_MAIN.replace("GROUP_A_MAIN", tt)
    yy = yy.replace("GROUP_A_LOGS", ff)
    
    return yy

def B(yy):
    pointsD = {}
    for nn in groupB:
        pointsD[nn] = {}    
    
    playedMaps = []
    for log in groupBLogs:
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
            pnt += 1 if i != 0 else 2
    
    
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
    
    yy = yy.replace("GROUP_B_MAIN", tt)
    yy = yy.replace("GROUP_B_LOGS", ff)
    
    return yy

hh = A()

print T_HEADER + B(hh)
