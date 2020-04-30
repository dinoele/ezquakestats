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
statsMatchesPath = stat_conf.matches_dir
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
os.system("cp %s %s" % (pathXML, statsMatchesPath))
os.system("cp %s %s" % (pathTXT, statsMatchesPath))
