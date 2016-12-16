#!/usr/bin/python
import subprocess
import pdb

OPTION_WITH_RANK = True

groupALogs = [              
              "PL_[blizz]_2016-12-06_11_35_38.html",
              "PL_[baldm6]_2016-12-06_13_09_20.html",
              "PL_[dad2]_2016-12-07_10_43_20.html",
              "PL_[utressor]_2016-12-07_12_50_30.html",
              "PL_[warfare]_2016-12-08_12_20_48.html",
              "PL_[travelert6]_2016-12-08_13_45_53.html",
              "PL_[skull]_2016-12-09_10_46_06.html",
              "PL_[aerowalk]_2016-12-12_10_44_35.html",
              "PL_[baldm7]_2016-12-13_11_28_00.html",
              "PL_[spinev2]_2016-12-14_12_11_03.html",
             ]

groupBLogs = [                            
              "FD_[dad2]_2016-12-07_10_36_10.html",
              "FD_[skull]_2016-12-07_12_53_46.html",
              "FD_[blizz]_2016-12-08_11_31_18.html",
              "FD_[aerowalk]_2016-12-08_13_24_12.html",
              "FD_[baldm7]_2016-12-12_14_24_10.html",
              "FD_[spinev2]_2016-12-13_13_40_31.html",
              "FD_[baldm6]_2016-12-14_09_34_44.html",
              "FD_[utressor]_2016-12-14_10_38_40.html",
              "FD_[warfare]_2016-12-14_12_13_26.html",
              "FD_[travelert6]_2016-12-15_10_55_40.html",
             ]

HTML_SCRIPT_HIGHCHARTS_GAMES_PROGRESS_FUNCTION = \
"<script type=\"text/javascript\">\n" \
"$(function () {\n" \
"Highcharts.theme = {\n" \
"   chart: {\n" \
"      backgroundColor: null,\n" \
"      style: {\n" \
"         fontFamily: \"Dosis, sans-serif\"\n" \
"      }\n" \
"   },\n" \
"   title: {\n" \
"      style: {\n" \
"         fontSize: '16px',\n" \
"         fontWeight: 'bold',\n" \
"         textTransform: 'uppercase'\n" \
"      }\n" \
"   },\n" \
"   tooltip: {\n" \
"      borderWidth: 0,\n" \
"      backgroundColor: 'rgba(219,219,216,0.8)',\n" \
"      shadow: true\n" \
"   },\n" \
"   legend: {\n" \
"      itemStyle: {\n" \
"         fontWeight: 'bold',\n" \
"         fontSize: '13px'\n" \
"      }\n" \
"   },\n" \
"   xAxis: {\n" \
"      \n" \
"      gridLineWidth: 1,\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   yAxis: {\n" \
"      title: {\n" \
"         style: {\n" \
"            textTransform: 'uppercase'\n" \
"         }\n" \
"      },\n" \
"      labels: {\n" \
"         style: {\n" \
"            fontSize: '12px'\n" \
"         }\n" \
"      }\n" \
"   },\n" \
"   plotOptions: {\n" \
"      candlestick: {\n" \
"         lineColor: '#404048'\n" \
"      }\n" \
"   },\n" \
"\n" \
"\n" \
"   // General\n" \
"   background2: '#F0F0EA'\n" \
"\n" \
"};\n" \
"\n" \
"// Apply the theme\n" \
"Highcharts.setOptions(Highcharts.theme);\n" \
"\n" \
"    $('#highchart_games_a_progress').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Group A progress',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            categories: [GROUP_A_X_AXIS_CATEGORIES],\n" \
"            title: {\n" \
"                text:  'Maps'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Maps'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: '',\n" \
"            shared: true,\n" \
"            formatter: function() {\n" \
"            var s = '<strong>'+ this.x +'</strong>';\n" \
"            var sortedPoints = this.points.sort(function(a, b){\n" \
"                  return ((a.y < b.y) ? 1 : ((a.y > b.y) ? -1 : 0));\n  " \
"              });\n" \
"            $.each(sortedPoints , function(i, point) {\n" \
"            s += '<br/>'+ point.series.name +': '+ point.y;\n" \
"            });\n" \
"            return s;\n" \
"            },\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"GROUP_A_ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"    $('#highchart_games_b_progress').highcharts({\n" \
"        chart: {\n" \
"                zoomType: 'x'\n" \
"            },\n" \
"        title: {\n" \
"            text: 'Group B progress',\n" \
"            x: -20 //center\n" \
"        },\n" \
"        subtitle: {\n" \
"            text: '',\n" \
"            x: -20\n" \
"        },\n" \
"        xAxis: {\n" \
"            categories: [GROUP_B_X_AXIS_CATEGORIES],\n" \
"            title: {\n" \
"                text:  'Maps'\n" \
"            },\n" \
"        },\n" \
"        yAxis: {\n" \
"            title: {\n" \
"                text: 'Maps'\n" \
"            },\n" \
"            plotLines: [{\n" \
"                value: 0,\n" \
"                width: 1,\n" \
"                color: '#808080'\n" \
"            }]\n" \
"        },\n" \
"        tooltip: {\n" \
"            valueSuffix: '',\n" \
"            shared: true,\n" \
"            formatter: function() {\n" \
"            var s = '<strong>'+ this.x +'</strong>';\n" \
"            var sortedPoints = this.points.sort(function(a, b){\n" \
"                  return ((a.y < b.y) ? 1 : ((a.y > b.y) ? -1 : 0));\n  " \
"              });\n" \
"            $.each(sortedPoints , function(i, point) {\n" \
"            s += '<br/>'+ point.series.name +': '+ point.y;\n" \
"            });\n" \
"            return s;\n" \
"            },\n" \
"        },\n" \
"        legend: {\n" \
"            layout: 'vertical',\n" \
"            align: 'right',\n" \
"            verticalAlign: 'middle',\n" \
"            borderWidth: 0\n" \
"        },\n" \
"        series: [{\n" \
"GROUP_B_ADD_STAT_ROWS" \
"        }]\n" \
"    });\n" \
"});\n" \
"</script>"

HTML_SCRIPT_HIGHCHARTS_GROUP_A_GAMES_PROGRESS_DIV_TAG = "<div id=\"highchart_games_a_progress\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"
HTML_SCRIPT_HIGHCHARTS_GROUP_B_GAMES_PROGRESS_DIV_TAG = "<div id=\"highchart_games_b_progress\" style=\"min-width: 310px; height: 500px; margin: 0 auto\"></div>"


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
"HIGHCHART_SCRIPT_PLACE" \
"</head>"



T_MAIN_HEADER = \
"<body>\n" \
"<div id=\"main\">\n" \
"<h1><a href=\"http://challonge.com/adriverquake2016\">PlayOff Brackets</a></h1>\n"


T_GROUP = \
"	<div>\n" \
"		<h1>Group GROUP_NAME POINT_ALGORITHM_PLACE</h1>\n" \
"		<table cellspacing=\"1\" class=\"tablesorter\">\n" \
"		<thead>\n" \
"				<tr>\n" \
"GROUP_HEADER" \
"				</tr>\n" \
"			</thead>\n" \
"			<tbody>\n" \
"GROUP_MAIN" \
"			</tbody>\n" \
"		</table>\n" \
"		\n" \
"		<table cellspacing=\"1\" class=\"tablesorter\" border=\"0\">\n" \
"			<tbody>\n" \
"GROUP_LOGS" \
"			</tbody>\n" \
"		</table>\n" \
"	</div>\n"

T_MAIN_FOOTER = \
"</div>\n" \
"<script src=\"https://code.highcharts.com/highcharts.js\"></script>\n" \
"<script src=\"https://code.highcharts.com/modules/exporting.js\"></script>\n" \
"</body>\n" \
"</html>"

PLAYER_TR = \
"				<tr>\n" \
"					<td>PLAYER_NAME_PLACE</td>\n" \
"					<td>PLAYER_TOTAL_POINTS_PLACE</td>  <!-- Total -->\n" \
"PLAYER_RANK_TD" \
"PLAYER_MAPS_PLACE" \
"				</tr>\n"

MAP_TD = "					<td>POINTS</td>\n"

MATCH_LOGS_TR = \
"				<tr>\n" \
"WWWWWW" \
"PPPPPP" \
"				</tr>\n" \

MATCH_LOGS_EMPTY_TD  = "					<td width=WIDTH_PLACE%>MatchLog</td>\n"
MATCH_LOGS_FILLED_TD = "					<td width=WIDTH_PLACE%><a href=\"../LOG_NAME\">MatchLog</a></td>\n"

allMaps = ["warfare", "travelert6", "dad2", "skull", "blizz", "aerowalk", "baldm7", "spinev2", "baldm6", "utressor"]
groupA = ["zrkn", "Onanim", "SHAROK", "EEE", "random"]
groupB = ["ss", "AREXP", "girgelezobeton", "ASHOT_HEADSHOT", "twinhooker", "bw"]

def generatePlayerTR(plName, pointsDict):
    res = PLAYER_TR
    res = res.replace("PLAYER_NAME_PLACE", plName)
    totalPoints = 0
    totalRank = 0
    mapsSection = ""
    for mapName in allMaps:
        if pointsDict.has_key(mapName):
            mapsSection += MAP_TD.replace("POINTS", str(pointsDict[mapName][0]))
            totalPoints += pointsDict[mapName][0]
            totalRank   += pointsDict[mapName][1]
        else:
            mapsSection += MAP_TD.replace("POINTS", "-")
    res = res.replace("PLAYER_MAPS_PLACE", mapsSection)
    res = res.replace("PLAYER_TOTAL_POINTS_PLACE", str(totalPoints))
    res = res.replace("PLAYER_RANK_TD", "					<td>%s</td>\n" % (str(totalRank)) if OPTION_WITH_RANK else "")
    
    return res

def generateGroupDiv(yy, groupName, pointsAlg = 1, isDescription = False):
    # group     = groupA if groupName == "A" else groupB
    # groupLogs = groupALogs if groupName == "A" else groupBLogs
    exec( "group = group%s" % (groupName) )
    exec( "groupLogs = group%sLogs" % (groupName) )
    
    pointsD = {}
    for nn in group:
        pointsD[nn] = {}    
    
    playedMaps = []
    for log in groupLogs:
        mapName = log.split("_")[1].replace("[","").replace("]","")
        playedMaps.append([mapName, log])
        
        logHeadStr = subprocess.check_output(["head", "%s" % ("../" + log), "-n 20"])
        playsStr = ""
        if "GAME_PLAYERS" in logHeadStr:
            playsStr = logHeadStr.split("GAME_PLAYERS")[1].split("-->")[0]
                
        plays = []
        if playsStr != "":
            playsStr = playsStr.replace("\n","")
            plays = playsStr.split(" ")
        
        rankStr = ""
        if "PLAYERS_RANK" in logHeadStr:
            rankStr = logHeadStr.split("PLAYERS_RANK")[1].split("-->")[0]
                
        ranks = []
        if rankStr != "":
            rankStr = rankStr.replace("\n","")
            ranks = rankStr.split(" ")
        
        plCount = len(plays)
        i = len(plays) - 1
        pnt = 1
        while i >= 0:
            name = plays[i].split("(")[0]
            plRank = int( ranks[i].split("(")[1].split(")")[0] )
            
            if not pointsD.has_key(name):
                pointsD[name] = {}
            
            pointsD[name][mapName] = [pnt,plRank]
            
            i -= 1
            
            if pointsAlg == 1: # 1+1+..+2
                pnt += 1 if i != 0 else 2
            elif pointsAlg == 2: # 1+1..+2+3
                if i == 0:
                    pnt += 3
                elif i == 1:
                    pnt += 2
                else:
                    pnt += 1
            elif pointsAlg == 3: # 1+1
                pnt += 1
            elif pointsAlg == 4: # 1+1..+2+2
                if i == 0 or i == 1: 
                    pnt += 2
                else:
                    pnt += 1
    
    tt = ""    
    for k in pointsD.keys():
        tt += generatePlayerTR(k, pointsD[k])
    
    # header
# "					<th width=12%>Player Name</th>\n" \
# "					<th width=8%>Total points</th>\n" \
# "					<th width=8%>warfare</th>\n" \
# "					<th width=8%>travelert6</th>\n" \
# "					<th width=8%>dad2</th>\n" \
# "					<th width=8%>skull</th>\n" \
# "					<th width=8%>blizz</th>\n" \
# "					<th width=8%>aerowalk</th>\n" \
# "					<th width=8%>baldm7</th>\n" \
# "					<th width=8%>spinev2</th>\n" \
# "					<th width=8%>baldm6</th>\n" \
# "					<th width=8%>utressor</th>\n" \
    headerStr = ""
    headerCnt = len(allMaps) + (3 if OPTION_WITH_RANK else 2) # name,total,rank
    delim = 100 / headerCnt
    nameWidth = 100 - ( delim * (headerCnt - 1) )
    
    headerStr  = "					<th width=%s%s>Player Name</th>\n" % (nameWidth, "%")
    headerStr += "					<th width=%s%s>Total points</th>\n" % (delim, "%")
    
    if OPTION_WITH_RANK:
        headerStr += "					<th width=%s%s>Total rank</th>\n" % (delim, "%")
        
    for m in allMaps:
        headerStr += "					<th width=%s%s>%s</th>\n" % (delim, "%", m)
    
    uu = ""
    for m in allMaps:
            
        logN = ""
        for xx in playedMaps:
            if xx[0] == m:
                logN = xx[1]
        
        if logN != "":
            uu += MATCH_LOGS_FILLED_TD.replace("LOG_NAME", logN).replace("WIDTH_PLACE", str(delim))
        else:
            uu += MATCH_LOGS_EMPTY_TD.replace("WIDTH_PLACE", str(delim))
    
    ff = MATCH_LOGS_TR.replace("PPPPPP", uu)
    
    ggg  = "					<td width=%s%s></td>\n" % (nameWidth, "%")
    
    if OPTION_WITH_RANK:
        ggg += "					<td width=%s%s></td>\n" % (delim, "%")
        
    ggg += "					<td width=%s%s></td>\n" % (delim, "%")
    
    ff = ff.replace("WWWWWW", ggg)
    
    yy = yy.replace("GROUP_NAME", groupName)
    yy = yy.replace("GROUP_MAIN", tt)
    yy = yy.replace("GROUP_LOGS", ff)
    yy = yy.replace("GROUP_HEADER", headerStr)
    
    pointsDescr = ""
    if pointsAlg == 1:   # 1+1+..+2
        pointsDescr = "  (1->2->3->4->6)" if groupName == "A" else "  (1->2->3->4->5->7)"
    elif pointsAlg == 2: # 1+1..+2+3
        pointsDescr = "  (1->2->3->5->8)" if groupName == "A" else "  (1->2->3->4->6->9)"
    elif pointsAlg == 3: # 1+1
        pointsDescr = "  (1->2->3->4->5)" if groupName == "A" else "  (1->2->3->4->5->6)"
    elif pointsAlg == 4: # 1+1..+2+2
        pointsDescr = "  (1->2->3->5->7)" if groupName == "A" else "  (1->2->3->4->6->8)"

    yy = yy.replace("POINT_ALGORITHM_PLACE", pointsDescr if isDescription else "")
    
    return yy, pointsD

def generateGraph(pointsD, groupName, funcStr):
    catsStr = ""
    playedMaps = []
    
    exec("groupLogs = group%sLogs" % (groupName))
    for log in groupLogs:
        catsStr += "'%s'," % (log.split("_[")[1].split("]_")[0])
        playedMaps.append(log.split("_[")[1].split("]_")[0])
    catsStr = catsStr[:-1]
    
    # grA = HTML_SCRIPT_HIGHCHARTS_GRAPH.replace("GRAPH_NAME", "highchart_games_a_progress")
    # grA = grA.replace("GRAPH_TITLE", "Group A progress")
    # 
    # grB = HTML_SCRIPT_HIGHCHARTS_GRAPH.replace("GRAPH_NAME", "highchart_games_b_progress")
    # grB = grB.replace("GRAPH_TITLE", "Group B progress")
    
    highchartsProgressFunctionStr = funcStr
    highchartsProgressFunctionStr = highchartsProgressFunctionStr.replace("GROUP_%s_X_AXIS_CATEGORIES" % (groupName), catsStr)
    
    hcDelim = "}, {\n"
    rowLines = ""        
    for pl in pointsD.keys():
        if rowLines != "":
            rowLines += hcDelim
        
        rowLines += "name: '%s',\n" % (pl)
        rowLines += "data: ["
        
        totalPoints = 0
        for m in playedMaps:
            totalPoints += pointsD[pl][m][0] if pointsD[pl].has_key(m) else 0
            rowLines += "%d," % (totalPoints)            
        rowLines = rowLines[:-1]
            
        rowLines += "]\n"        
    
    highchartsProgressFunctionStr = highchartsProgressFunctionStr.replace("GROUP_%s_ADD_STAT_ROWS" % (groupName), rowLines)
    
    return highchartsProgressFunctionStr

# resA, pointsA = generateGroupDiv(T_GROUP_A, "A")
# resB, pointsB = generateGroupDiv(T_GROUP_B, "B")
resA, pointsA = generateGroupDiv(T_GROUP, "A")
resB, pointsB = generateGroupDiv(T_GROUP, "B")

chartStr = generateGraph(pointsA, "A", HTML_SCRIPT_HIGHCHARTS_GAMES_PROGRESS_FUNCTION)
chartStr = generateGraph(pointsB, "B", chartStr)

# charts
print T_HEADER.replace("HIGHCHART_SCRIPT_PLACE", chartStr) + T_MAIN_HEADER + resA + HTML_SCRIPT_HIGHCHARTS_GROUP_A_GAMES_PROGRESS_DIV_TAG + "<hr>" + resB + HTML_SCRIPT_HIGHCHARTS_GROUP_B_GAMES_PROGRESS_DIV_TAG + T_MAIN_FOOTER

# no charts
# print T_HEADER.replace("HIGHCHART_SCRIPT_PLACE", "") + T_MAIN_HEADER + generateGroupDiv(T_GROUP_A, "A")[0]+ generateGroupDiv(T_GROUP_B, "B")[0] + T_MAIN_FOOTER

# print T_HEADER.replace("HIGHCHART_SCRIPT_PLACE", "") + T_MAIN_HEADER + \
#                        generateGroupDiv(T_GROUP, "A", 1, True)[0] + generateGroupDiv(T_GROUP, "A", 2, True)[0] + generateGroupDiv(T_GROUP, "A", 3, True)[0] + generateGroupDiv(T_GROUP, "A", 4, True)[0] + \
#                        generateGroupDiv(T_GROUP, "B", 1, True)[0] + generateGroupDiv(T_GROUP, "B", 2, True)[0] + generateGroupDiv(T_GROUP, "B", 3, True)[0] + generateGroupDiv(T_GROUP, "B", 4, True)[0] + T_MAIN_FOOTER