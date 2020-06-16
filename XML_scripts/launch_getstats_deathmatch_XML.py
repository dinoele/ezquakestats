#!/usr/bin/python

from datetime import timedelta, date, datetime
import subprocess

from stat import S_ISREG, ST_CTIME, ST_MODE, ST_SIZE, ST_MTIME
import sys, time

import fileinput
import os

from optparse import OptionParser,OptionValueError

import stat_conf

stat_conf.read_config()

# =================================================================================================
path = stat_conf.nquakesv_root + "/ktx/demos"
matchesPath = stat_conf.matches_dir + "dm"
# =================================================================================================

parser = OptionParser(usage="", version="")
parser.add_option("--net-copy", action="store_true",   dest="netCopy", default=False,   help="")
(options, restargs) = parser.parse_args()

pathBak = path
# get all entries in the directory w/ stats
entries = (os.path.join(path, fn) for fn in os.listdir(path))
entries = ((os.stat(path), path) for path in entries if ".xml" in path and "ffa" in path)

# leave only regular files, insert creation date
entries = ((stat[ST_MTIME], stat[ST_SIZE], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))

pathXML = ""

for cdate, size, path in sorted(entries, reverse=True):
    #print time.ctime(cdate), size, os.path.basename(path)	
	#print "AAA", cdate, size, path
	if size > 150000:
		pathXML = path
		break	

path = pathBak
entriesTXT = (os.path.join(path, fn) for fn in os.listdir(path))
entriesTXT = ((os.stat(path), path) for path in entriesTXT if ".txt" in path and "ffa" in path)
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

os.system("python getstats_deathmatch_XML.py --league Premier --fxml %s --fjson %s %s" % (pathXML, pathTXT, "--net-copy" if options.netCopy else ""))

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
