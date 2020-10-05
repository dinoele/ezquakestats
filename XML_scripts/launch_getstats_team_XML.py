#!/usr/bin/python
from datetime import timedelta, date, datetime
import subprocess
import re

from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE, ST_MTIME
import sys, time

import fileinput
import os
from optparse import OptionParser,OptionValueError
import stat_conf

stat_conf.read_config()

# =================================================================================================
path = stat_conf.nquakesv_root + "/ktx/demos"
matchesPath = stat_conf.matches_dir + "team"
# =================================================================================================

parser = OptionParser(usage="", version="")
parser.add_option("--net-copy", action="store_true",   dest="netCopy", default=False,   help="")
(options, restargs) = parser.parse_args()

# get all entries in the directory w/ stats
entriesXML = (os.path.join(path, fn) for fn in os.listdir(path))
entriesXML = ((os.stat(path), path) for path in entriesXML if ".xml" in path and "vs" in path)
# leave only regular files, insert creation date
entriesXML = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entriesXML if S_ISREG(stat[ST_MODE]))

pathXML = ""
for cdate, size, filePath in sorted(entriesXML, reverse=True):
    #print time.ctime(cdate), size, os.path.basename(path)	
	#print "AAA", cdate, size, path
	if size > 150000:
		pathXML = filePath
		break	

# get all entries in the directory w/ stats
entriesTXT = (os.path.join(path, fn) for fn in os.listdir(path))
entriesTXT = ((os.stat(path), path) for path in entriesTXT if ".txt" in path and "vs" in path)
# leave only regular files, insert creation date
entriesTXT = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entriesTXT if S_ISREG(stat[ST_MODE]))

pathTXT = ""
for cdate, size, path in sorted(entriesTXT, reverse=True):
    #print time.ctime(cdate), size, os.path.basename(path)	
	#print "AAA", cdate, size, path
	if size > 100:
		pathTXT = path
		break	

        
print "RES", pathXML
print "RES", pathTXT

# os.system("python getstats_deathmatch_NEW.py --league Premier --fxml %s " % (pathXML))
# os.system("cp %s /cygdrive/d/tmp/qstats/matches" % (pathXML))

# dateRes = re.search("(?<=]).*(?=.xml)", pathXML)

os.system("python getstats_team_XML.py --fxml %s --fjson %s %s" % (pathXML, pathTXT, "--net-copy" if options.netCopy else ""))
os.system("python generate_common_pages.py")

if not os.path.exists(stat_conf.matches_dir):
    os.system("mkdir %s" % (stat_conf.matches_dir))

mPath = matchesPath
if not os.path.exists(mPath):
    os.system("mkdir %s" % (mPath))
    
nameXMLHead, nameXMLTail = os.path.split(pathXML)
nameTXTHead, nameTXTTail = os.path.split(pathTXT)

destPathXML = os.path.join(mPath, nameXMLTail)
destPathTXT = os.path.join(mPath, nameTXTTail)

if os.path.exists(destPathXML):
    xmlStatDest = os.stat(destPathXML)
    xmlStatSrc  = os.stat(pathXML)
    if xmlStatDest[ST_SIZE] != xmlStatSrc[ST_SIZE]:    
        nameXMLExtHead, nameXMLExtTail = os.path.splitext(destPathXML)
        destPathXML = "%s_%d%s" % (nameXMLExtHead, int(time.time()), nameXMLExtTail)

if os.path.exists(destPathTXT):
    txtStatDest = os.stat(destPathTXT)
    txtStatSrc  = os.stat(pathTXT)
    if txtStatDest[ST_SIZE] != txtStatSrc[ST_SIZE]:            
        nameTXTExtHead, nameTXTExtTail = os.path.splitext(destPathTXT)
        destPathTXT = "%s_%d%s" % (nameTXTExtHead, int(time.time()), nameTXTExtTail)
    
os.system("mv %s %s" % (pathXML, destPathXML))
os.system("mv %s %s" % (pathTXT, destPathTXT))
