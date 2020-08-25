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

import HTML

import json

ezstatslib.REPORTS_FOLDER = "../"
    
# generate output string
resultString = ""
    
resultString += "</pre>PLAYERS_ACHIEVEMENTS_PLACE\n<pre>"

# ============================================================================================================

def writeHtmlWithScripts(f, allachievements, resStr): 
    pageHeaderStr = ezstatslib.HTML_HEADER_SCRIPT_SECTION
    pageTitle = "ALL ACHIEVEMENTS"
    pageHeaderStr = pageHeaderStr.replace("PAGE_TITLE", pageTitle)
    pageHeaderStr += ezstatslib.HTML_HEADER_SCRIPT_GOOGLE_CHARTS_LOAD
    
    f.write(pageHeaderStr)
            
    # players achievements -->
    playersAchievementsStr = ezstatslib.HTML_PLAYERS_ACHIEVEMENTS_DIV_TAG    
    cellWidth = "500px"
    achievementsHtmlTable = HTML.Table(border="0", cellspacing="0",
                                       style="font-family: Verdana, Arial, Helvetica, sans-serif; font-size: 12pt;")
    
    rownum = 1
    for i in xrange(len(allachievements)):
    
        tableRow = HTML.TableRow(cells=[ HTML.TableCell( "%s(%d): %s" % (str(allachievements[i].toString()), allachievements[i].achtype, str(allachievements[i].description())), align="center", width=cellWidth) ])
        tableRow.cells.append( HTML.TableCell(allachievements[i].generateHtmlEx("img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 4, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 10, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 19, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 30, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 70, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 99, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 100, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 111, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 369, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 145, path = "img/"), align="center" ) )
        tableRow.cells.append( HTML.TableCell(ezstatslib.Achievement.generateHtmlExCnt(allachievements[i], "", 188, path = "img/"), align="center" ) )
        achievementsHtmlTable.rows.append(tableRow)
        
        rownum += 1
        
    playersAchievementsStr = playersAchievementsStr.replace("PLAYERS_ACHIEVEMENTS_TABLE", str(achievementsHtmlTable) + ezstatslib.Achievement.generateAchievementsLevelLegendTable())
    # <-- players achievements
 
    # write expand/collapse function
    f.write(ezstatslib.HTML_EXPAND_CHECKBOX_FUNCTION)
    f.write(ezstatslib.HTML_EXPAND_POWER_UPS_CHECKBOX_FUNCTION)
    
    f.write(ezstatslib.HTML_SCRIPT_SECTION_FOOTER)
         
    resStr = resStr.replace("PLAYERS_ACHIEVEMENTS_PLACE", playersAchievementsStr)
        
    f.write(resStr)
    
    f.write(ezstatslib.HTML_PRE_CLOSE_TAG)
    
    # add script section for folding
    f.write(ezstatslib.HTML_BODY_FOLDING_SCRIPT)    
    
    f.write(ezstatslib.HTML_FOOTER_NO_PRE)


filePath     = "all_achs.html"
filePathFull = ezstatslib.REPORTS_FOLDER + filePath

allachievements = []
for key in ezstatslib.AchievementType.__dict__.keys():
    if key != "__dict__" and key != "__doc__" and key != "__module__"and key != "__weakref__":
        exec("allachievements.append(  ezstatslib.Achievement(ezstatslib.AchievementType.%s, \"\" ) )" % (key))

# sort by id
allachievements = sorted(allachievements, key=lambda x: (x.achtype), reverse=False)        
       
isFileNew = False
if os.path.exists(filePathFull):
    # temp file 
    tmpFilePathFull = "../" + filePath + ".tmp"
    if os.path.exists(tmpFilePathFull):        
        os.remove(tmpFilePathFull)
    
    tmpf = open(tmpFilePathFull, "w")
    
    writeHtmlWithScripts(tmpf, allachievements, resultString)  
    
    tmpf.close()
    
    os.remove(filePathFull)
    os.rename(tmpFilePathFull, filePathFull)

else:  # not os.path.exists(filePathFull):
    outf = open(filePathFull, "w")
    
    writeHtmlWithScripts(outf, allachievements, resultString)
    
    outf.close()
    isFileNew = True
    

print filePathFull