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

possibleWeapons = ["lg", "gl", "rl", "sg", "ssg", "ng", "sng", "axe", "tele"]

def isMatchStart(s):
    if "The match has begun" in s:
        return True
    return False

def isMatchEnd(s):
    if "The match is over" in s:
        return True
    return False

def commonDetection(s):
    knownSkipLines = ["not enough ammo", "second", "no weapon", "Couldn't download"]
#possibleWeapons = ["lg", "gl", "rl", "sg", "ssg", "ng", "sng", "axe"]

    spl = s.split(" ")
    
    if "boomstick" in s: #zrkn chewed on SHAROK's boomstick
        return True, spl[3].split("'")[0], spl[0], "sg"

    elif "was gibbed" in s and "rocket" in s: #rea[rbf] was gibbed by Ilya's rocket
        return True, spl[4].split("'")[0], spl[0], "rl"
    
    elif "was gibbed" in s and "grenade" in s: #zrkn was gibbed by ss's grenade 
        return True, spl[4].split("'")[0], spl[0], "gl"
        
    elif "pineapple" in s: #ss eats rea[rbf]'s pineapple
        return True, spl[2].split("'")[0], spl[0], "gl"
        
    elif "rocket" in s and not "took" in s: # zrkn rides EEE's rocket
        return True, spl[2].split("'")[0], spl[0], "rl"
        
    elif "shaft" in s: # ss accepts Onanim's shaft
        return True, spl[2].split("'")[0], spl[0], "lg"
        
    elif "punctured" in s: # EEE was punctured by zrkn
        return True, spl[4].split("\n")[0], spl[0], "sng"
       
    elif "buckshot" in s: # Onanim ate 2 loads of SHAROK's buckshot
        return True, spl[5].split("'")[0], spl[0], "ssg"

    elif "ventilated" in s: # random was ventilated by ss
        return True, spl[4].split("\n")[0], spl[0], "sng"

    elif "perforated" in s: # Onanim was perforated by ss
        return True, spl[4].split("\n")[0], spl[0], "sng"

    elif "pierced" in s: # Artem was body pierced by zrkn
        return True, spl[5].split("\n")[0], spl[0], "ng"

    elif "nailed" in s: # Ilya was nailed by ss
        return True, spl[4].split("\n")[0], spl[0], "ng"

    elif "batteries" in s: # ss drains Onanim's batteries
        return True, spl[2].split("\'s")[0], spl[0], "lg"

    elif "ax-murdered" in s: # EEE was ax-murdered by Onanim
        return True, spl[4].split("\n")[0], spl[0], "axe"
 
    else:
        isKnown = False
        for l in knownSkipLines:
            if l in s:
                isKnown = True

        if not isKnown:
            print "!!!:", s ,
        
        return False,"","",""

def suicideDetection(s):
    detectStrs = ["tries to put the pin back in", \
                  "discovers blast radius", \
                  "becomes bored with life", \
                  "fell to his death", \
                  "visits the Volcano God", \
                  "turned into hot slag", \
                  "cratered", \
                  "suicides", \
                  "died", \
                  "discharges into the water", \
                  "discharges into the slime", \
                  "can't exist on slime alone", \
                  "gulped a load of slime"]
    for det in detectStrs:
         if det in s:
            return True,s.split( )[0]
    return False,""

def talefragDetection(s, teammateTelefrags):
    if "telefrag" in s:  # Ilya was telefragged by zrkn || Ilya was telefragged by his teammate
        spl = s.split(" ")
        if "teammate" in s:
            teammateTelefrags.append(spl[0])
            return True,"",spl[0]  # only death is increased
        else:
            return True,spl[4].split("\n")[0],spl[0]
    return False,"",""

def teamkillDetection(s):
    detectStrs = ["checks his glasses", \
                  "gets a frag for the other team", \
                  "loses another friend", \
                  "mows down a teammate"]
    for det in detectStrs:
         if det in s:
            return True,s.split( )[0]
    return False,""

def sortPlayersBy(players, param, fieldType="attr", units = ""):
    res = ""
    
    if fieldType == "attr":
        sortedPlayers = sorted(players, key=attrgetter(param), reverse=True)
    else:
        sortedPlayers = sorted(players, key=methodcaller(param), reverse=True)

    valsSum = 0
    for pl in sortedPlayers:
        exec("val = pl.%s%s" % (param, "" if fieldType == "attr" else "()"))
        valsSum += val
        res +=  "%s%s(%d%s)" % ("" if res == "" else ", ", pl.name, val, units)

    return (res if param == "damageDelta" or valsSum != 0 else "")

class Player:
    def __init__(self, teamname, name, score, origDelta, teamkills):
        self.teamname = teamname
        self.name = name
        self.origScore = score
        self.origDelta = origDelta
        self.origTeamkills = teamkills
        self.correctedDelta = 0
        self.kills = 0
        self.deaths = 0
        self.suicides = 0
        self.teamkills = 0

        self.streaks = 0
        self.spawnfrags = 0
        
        self.ga = 0
        self.ya = 0
        self.ra = 0
        self.mh = 0
        self.tkn = 0
        self.gvn = 0
        self.tm  = 0

        self.rlskill_ad = 0
        self.rlskill_dh = 0

        self.w_rl = 0
        self.w_lg = 0
        self.w_gl = 0
        self.w_sg = 0
        self.w_ssg = 0
        
        self.rl_kills = 0
        self.lg_kills = 0
        self.gl_kills = 0
        self.sg_kills = 0
        self.ssg_kills = 0
        self.ng_kills = 0
        self.sng_kills = 0
        self.axe_kills = 0
        self.tele_kills = 0
        #self.TODO_kills = 0
        
        self.rl_deaths = 0
        self.lg_deaths = 0
        self.gl_deaths = 0
        self.sg_deaths = 0
        self.ssg_deaths = 0
        self.ng_deaths = 0
        self.sng_deaths = 0
        self.axe_deaths = 0
        self.tele_deaths = 0
        #self.TODO_deaths = 0

    def frags(self):
        return (self.kills - self.teamkills - self.suicides);

    def deathsFromTeammates(self):
        return (self.origScore - self.deaths - self.suicides- self.origDelta);

    def killRatio(self): # Kill Ratio: Frags / ( Deaths + Suicides ).
        denominator = float(self.deaths + self.suicides + self.teamkills);
        return 0.0 if (denominator == 0) else (float(self.kills) / denominator)

    def efficiency(self): # Efficiency: Frags / ( Frags + Deaths + Suicides ).
        denominator = float(self.kills + self.deaths + self.suicides + self.teamkills)
        return 0.0 if (denominator == 0) else (float(self.kills) / denominator) * 100

    def damageDelta(self):
        return (self.gvn - self.tkn)
    
    def calcDelta(self):
        return (self.frags() - self.deaths)

    def toString(self):
        return "[%s] %s: %d (%d) %d : kills:%d, deaths:%d, suicides:%d, teamkills:%d, delta:%d" % (self.teamname, self.name, self.origScore, self.origDelta, self.origTeamkills, self.kills, self.deaths, self.suicides, self.teamkills, self.calcDelta())

    def getFormatedStats(self):
        return "frags:{0:3d}, kills:{1:3d}, deaths:{2:3d}, suicides:{3:3d}, teamkills:{4:3d}, teamdeaths:{5:3d}, gvn-tkn: {6:4d} - {7:4d} ({8:5d}), ratio:{9:6.3}, eff:{10:6.4}%".format(self.frags(), self.kills, self.deaths, self.suicides, self.teamkills, self.deathsFromTeammates(), self.gvn, self.tkn, self.damageDelta(), self.killRatio(), self.efficiency())
    
    def getFormatedStats_noTeamKills(self):
        return "frags:{0:3d}, kills:{1:3d}, deaths:{2:3d}, suicides:{3:3d}, gvn-tkn: {4:4d} - {5:4d} ({6:5d}), ratio:{7:6.3}, eff:{8:6.4}%".format(self.frags(), self.kills, self.deaths, self.suicides, self.gvn, self.tkn, self.damageDelta(), self.killRatio(), self.efficiency())

    def getFormatedPowerUpsStats(self):
        return "ra:{0:2d}, ya:{1:2d}, ga:{2:2d}, mh:{3:2d}".format(self.ra, self.ya, self.ga, self.mh)

    def getWeaponsKills(self, totalValue = 0):
        if totalValue == 0:
            return "rl:{0:3d}, lg:{1:3d}, gl:{2:3d}, sg:{3:3d}, ssg:{4:3d}, ng:{5:3d}, sng:{6:3d}, tele:{7:3d}".format(self.rl_kills, self.lg_kills, self.gl_kills, self.sg_kills, self.ssg_kills, self.ng_kills, self.sng_kills, self.tele_kills)
        else:
            return "rl:{0:3d}({1:5.4}%), lg:{2:3d}({3:6.3}%), gl:{4:3d}({5:6.3}%), sg:{6:3d}({7:6.3}%), ssg:{8:3d}({9:6.3}%), ng:{10:3d}({11:6.3}%), sng:{12:3d}({13:6.3}%), tele:{14:3d}({15:6.3}%)".format( \
                                                                                                                                                             self.rl_kills, \
                                                                                                                                                             (float(self.rl_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.lg_kills, \
                                                                                                                                                             (float(self.lg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.gl_kills, \
                                                                                                                                                             (float(self.gl_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.sg_kills, \
                                                                                                                                                             (float(self.sg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.ssg_kills, \
                                                                                                                                                             (float(self.ssg_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.ng_kills,  # 10 \
                                                                                                                                                             (float(self.ng_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.sng_kills, \
                                                                                                                                                             (float(self.sng_kills) / float(totalValue) * 100), \
                                                                                                                                                             self.tele_kills, \
                                                                                                                                                             (float(self.tele_kills) / float(totalValue) * 100))

    def getWeaponsKills(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl   else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_kills,   (float(self.rl_kills)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg   else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_kills,   (float(self.lg_kills)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl   else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_kills,   (float(self.gl_kills)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg   else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_kills,   (float(self.sg_kills)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg  else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_kills,  (float(self.ssg_kills)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng   else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_kills,   (float(self.ng_kills)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng  else "sng:{0:3d}({1:6.3}%), ".format( self.sng_kills,  (float(self.sng_kills)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele else "tele:{0:3d}({1:6.3}%), ".format(self.tele_kills, (float(self.tele_kills) / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, telestr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def getWeaponsDeaths(self, totalValue = 0):
        if totalValue == 0:
            return "rl:{0:3d}, lg:{1:3d}, gl:{2:3d}, sg:{3:3d}, ssg:{4:3d}, ng:{5:3d}, sng:{6:3d}, tele:{7:3d}".format(self.rl_deaths, self.lg_deaths, self.gl_deaths, self.sg_deaths, self.ssg_deaths, self.ng_deaths, self.sng_deaths, self.tele_deaths)
        else:
            return "rl:{0:3d}({1:5.4}%), lg:{2:3d}({3:6.3}%), gl:{4:3d}({5:6.3}%), sg:{6:3d}({7:6.3}%), ssg:{8:3d}({9:6.3}%), ng:{10:3d}({11:6.3}%), sng:{12:3d}({13:6.3}%), tele:{14:3d}({15:6.3}%)".format( \
                                                                                                                                                             self.rl_deaths, \
                                                                                                                                                             (float(self.rl_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.lg_deaths, \
                                                                                                                                                             (float(self.lg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.gl_deaths, \
                                                                                                                                                             (float(self.gl_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.sg_deaths, \
                                                                                                                                                             (float(self.sg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.ssg_deaths, \
                                                                                                                                                             (float(self.ssg_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.ng_deaths,  # 10 \
                                                                                                                                                             (float(self.ng_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.sng_deaths, \
                                                                                                                                                             (float(self.sng_deaths) / float(totalValue) * 100), \
                                                                                                                                                             self.tele_deaths, \
                                                                                                                                                             (float(self.tele_deaths) / float(totalValue) * 100))

    def getWeaponsDeaths(self, totalValue, weaponsCheck):
        rlstr   = "" if not weaponsCheck.is_rl   else "rl:{0:3d}({1:5.4}%), ".format(  self.rl_deaths,   (float(self.rl_deaths)   / float(totalValue) * 100));
        lgstr   = "" if not weaponsCheck.is_lg   else "lg:{0:3d}({1:6.3}%), ".format(  self.lg_deaths,   (float(self.lg_deaths)   / float(totalValue) * 100));
        glstr   = "" if not weaponsCheck.is_gl   else "gl:{0:3d}({1:6.3}%), ".format(  self.gl_deaths,   (float(self.gl_deaths)   / float(totalValue) * 100));
        sgstr   = "" if not weaponsCheck.is_sg   else "sg:{0:3d}({1:6.3}%), ".format(  self.sg_deaths,   (float(self.sg_deaths)   / float(totalValue) * 100));
        ssgstr  = "" if not weaponsCheck.is_ssg  else "ssg:{0:3d}({1:6.3}%), ".format( self.ssg_deaths,  (float(self.ssg_deaths)  / float(totalValue) * 100));
        ngstr   = "" if not weaponsCheck.is_ng   else "ng:{0:3d}({1:6.3}%), ".format(  self.ng_deaths,   (float(self.ng_deaths)   / float(totalValue) * 100));
        sngstr  = "" if not weaponsCheck.is_sng  else "sng:{0:3d}({1:6.3}%), ".format( self.sng_deaths,  (float(self.sng_deaths)  / float(totalValue) * 100));
        telestr = "" if not weaponsCheck.is_tele else "tele:{0:3d}({1:6.3}%), ".format(self.tele_deaths, (float(self.tele_deaths) / float(totalValue) * 100));

        resstr = "%s%s%s%s%s%s%s%s" % (rlstr, lgstr, glstr, sgstr, ssgstr, ngstr, sngstr, telestr);
        if len(resstr) > 2:
            resstr = resstr[:-2]
        return resstr

    def correctDelta(self):
        self.correctedDelta = self.origDelta + self.suicides

    def parseWeapons(self, s): # Wp: lg14.3% rl38.5% gl4.9% sg5.8% ssg5.2%
        for weap in possibleWeapons:
            spl = s.split(weap)
            val = 0.0
            if len(spl) == 1:
                pass
            else:
                val = float(spl[1].split("%")[0])
            exec("self.w_%s = val" % (weap))

class Team:
    def __init__(self, teamname):
        self.name = teamname
        self.ga = 0
        self.ya = 0
        self.ra = 0
        self.mh = 0
        self.tkn = 0
        self.gvn = 0
        self.tm  = 0
        
        self.kills = 0
        self.deaths = 0
        self.suicides = 0
        self.teamkills = 0
    
    def damageDelta(self):
        return (self.gvn - self.tkn)


class WeaponsCheckRes:
    def __init__(self):
        for weap in possibleWeapons:
            exec("self.is_%s = False" % weap)
        
def getWeaponsCheck(allplayers):
    res = WeaponsCheckRes();
    for pl in allplayers:
        for weap in possibleWeapons:
           weapCheck = False
           exec("weapCheck = (pl.%s_kills != 0) or (pl.%s_deaths != 0);" % (weap, weap))
           if weapCheck:
               exec("res.is_%s = True;" % (weap));
    return res;
            





#    {WEAPON, 10, 1, "(.*) sleeps with the fishes", false},
#    {WEAPON, 10, 1, "(.*) sucks it down", false},
#    {WEAPON, 10, 1, "(.*) gulped a load of slime", false},
#    {WEAPON, 10, 1, "(.*) can't exist on slime alone", false},
#    {WEAPON, 10, 1, "(.*) burst into flames", false},
#    {WEAPON, 10, 1, "(.*) turned into hot slag", false},
#    {WEAPON, 10, 1, "(.*) visits the Volcano God", false},
#    {WEAPON, 15, 1, "(.*) cratered", false},
#    {WEAPON, 15, 1, "(.*) fell to his death", false},
#    {WEAPON, 15, 1, "(.*) fell to her death", false},
#    {WEAPON, 11, 1, "(.*) blew up", false},
#    {WEAPON, 11, 1, "(.*) was spiked", false},
#    {WEAPON, 11, 1, "(.*) was zapped", false},
#    {WEAPON, 11, 1, "(.*) ate a lavaball", false},
#    {WEAPON, 12, 1, "(.*) was telefragged by his teammate", false},
#    {WEAPON, 12, 1, "(.*) was telefragged by her teammate", false},
#    {WEAPON,  0, 1, "(.*) died", false},
#    {WEAPON,  0, 1, "(.*) tried to leave", false},
#    {WEAPON, 14, 1, "(.*) was squished", false},
#    {WEAPON,  0, 1, "(.*) suicides", false},
#    {WEAPON,  6, 1, "(.*) tries to put the pin back in", false},
#    {WEAPON,  7, 1, "(.*) becomes bored with life", false},
#    {WEAPON,  7, 1, "(.*) discovers blast radius", false},
#    {WEAPON, 13, 1, "(.*) electrocutes himself.", false},
#    {WEAPON, 13, 1, "(.*) electrocutes herself.", false},
#    {WEAPON, 13, 1, "(.*) discharges into the slime", false},
#    {WEAPON, 13, 1, "(.*) discharges into the lava", false},
#    {WEAPON, 13, 1, "(.*) discharges into the water", false},
#    {WEAPON, 13, 1, "(.*) heats up the water", false},
#    {WEAPON, 16, 1, "(.*) squished a teammate", false},
#    {WEAPON, 16, 1, "(.*) mows down a teammate", false},
#    {WEAPON, 16, 1, "(.*) checks his glasses", false},
#    {WEAPON, 16, 1, "(.*) checks her glasses", false},
#    {WEAPON, 16, 1, "(.*) gets a frag for the other team", false},
#    {WEAPON, 16, 1, "(.*) loses another friend", false},
#    {WEAPON,  1, 2, "(.*) was ax-murdered by (.*)", false},
#    {WEAPON,  2, 2, "(.*) was lead poisoned by (.*)", false},
#    {WEAPON,  2, 2, "(.*) chewed on (.*)'s boomstick", false},
#    {WEAPON,  3, 2, "(.*) ate 8 loads of (.*)'s buckshot", false},
#    {WEAPON,  3, 2, "(.*) ate 2 loads of (.*)'s buckshot", false},
#    {WEAPON,  4, 2, "(.*) was body pierced by (.*)", false},
#    {WEAPON,  4, 2, "(.*) was nailed by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was perforated by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was punctured by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was ventilated by (.*)", false},
#    {WEAPON,  5, 2, "(.*) was straw-cuttered by (.*)", false},
#    {WEAPON,  6, 2, "(.*) eats (.*)'s pineapple", false},
#    {WEAPON,  6, 2, "(.*) was gibbed by (.*)'s grenade", false},
#    {WEAPON,  7, 2, "(.*) was smeared by (.*)'s quad rocket", false},
#    {WEAPON,  7, 2, "(.*) was brutalized by (.*)'s quad rocket", false},
#    {WEAPON,  7, 2, "(.*) rips (.*) a new one", true},
#    {WEAPON,  7, 2, "(.*) was gibbed by (.*)'s rocket", false},
#    {WEAPON,  7, 2, "(.*) rides (.*)'s rocket", false},
#    {WEAPON,  8, 2, "(.*) accepts (.*)'s shaft", false},
#    {WEAPON,  9, 2, "(.*) was railed by (.*)", false},
#    {WEAPON, 12, 2, "(.*) was telefragged by (.*)", false},
#    {WEAPON, 14, 2, "(.*) squishes (.*)", true},
#    {WEAPON, 13, 2, "(.*) accepts (.*)'s discharge", false},
#    {WEAPON, 13, 2, "(.*) drains (.*)'s batteries", false},
#    {WEAPON,  8, 2, "(.*) gets a natural disaster from (.*)", false},

	#DEFINE OBITUARY	PLAYER_DEATH	DROWN				" sleeps with the fishes"
	#DEFINE OBITUARY	PLAYER_DEATH	DROWN				" sucks it down"
	#DEFINE OBITUARY	PLAYER_DEATH	SLIME				" gulped a load of slime"
	#DEFINE OBITUARY	PLAYER_DEATH	SLIME				" can't exist on slime alone"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" burst into flames"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" turned into hot slag"
	#DEFINE OBITUARY	PLAYER_DEATH	LAVA				" visits the Volcano God"
	
	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" cratered"
	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" fell to his death"
	#DEFINE OBITUARY	PLAYER_DEATH	FALL				" fell to her death"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" blew up"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" was spiked"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" was zapped"
	#DEFINE OBITUARY	PLAYER_DEATH	TRAP				" ate a lavaball"
	
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN TELEFRAG		" was telefragged by his teammate"
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN TELEFRAG		" was telefragged by her teammate"
	
	
	#DEFINE OBITUARY	PLAYER_DEATH	NOWEAPON			" died"
	#DEFINE OBITUARY	PLAYER_DEATH	NOWEAPON			" tried to leave"
	#DEFINE OBITUARY	PLAYER_DEATH	SQUISH				" was squished"
	
	#DEFINE OBITUARY	PLAYER_SUICIDE	NOWEAPON			" suicides"
	
	#DEFINE OBITUARY	PLAYER_SUICIDE	GRENADE_LAUNCHER	" tries to put the pin back in"
	#DEFINE OBITUARY	PLAYER_SUICIDE	ROCKET_LAUNCHER		" becomes bored with life"
	#DEFINE OBITUARY	PLAYER_SUICIDE	ROCKET_LAUNCHER		" discovers blast radius"
	
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" electrocutes himself"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" electrocutes herself"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" railcutes himself" // rail dis
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" railcutes herself" // rail dis
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the slime"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the lava"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" discharges into the water"
	#DEFINE OBITUARY	PLAYER_SUICIDE	DISCHARGE			" heats up the water"
	
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN SQUISH			" squished a teammate"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" mows down a teammate"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" checks his glasses"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" checks her glasses"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" gets a frag for the other team"
	#DEFINE OBITUARY	X_TEAMKILLS_UNKNOWN TEAMKILL		" loses another friend"
	
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was crushed by his teammate" // ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was crushed by her teammate" // ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was jumped by his teammate"  // ktx addon for ktpro stomp tk
	#DEFINE OBITUARY	X_TEAMKILLED_UNKNOWN STOMP			" was jumped by her teammate"  // ktx addon for ktpro stomp tk
	
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" softens "   "'s fall" // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" softens "   "' fall" // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" tried to catch "      // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was crushed by "      // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was jumped by "       // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGS_Y		STOMP				" stomps "              // ktpro stomp kill
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	STOMP				" was literally stomped into particles by " // KTX instagib
	
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	AXE					" was ax-murdered by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SHOTGUN			" was lead poisoned by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SHOTGUN				" chewed on " "'s boomstick"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SHOTGUN				" chewed on " "' boomstick"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_SHOTGUN		" ate 8 loads of "   "'s buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_SHOTGUN		" ate 8 loads of "   "' buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_SHOTGUN		" ate 2 loads of "   "'s buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_SHOTGUN		" ate 2 loads of "   "' buckshot"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	NAILGUN				" was body pierced by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	NAILGUN				" was nailed by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was perforated by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was punctured by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	SUPER_NAILGUN		" was ventilated by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_SUPER_NAILGUN		" was straw-cuttered by "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" eats " "'s pineapple"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" eats " "' pineapple"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" was gibbed by " "'s grenade"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	GRENADE_LAUNCHER	" was gibbed by " "' grenade"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was smeared by "   "'s quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was smeared by "   "' quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was brutalized by " "'s quad rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_ROCKET_LAUNCHER	" was brutalized by " "' quad rocket"
	#DEFINE OBITUARY	X_FRAGS_Y		Q_ROCKET_LAUNCHER	" rips " " a new one"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" was gibbed by " "'s rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" was gibbed by " "' rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" rides " "'s rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	ROCKET_LAUNCHER		" rides " "' rocket"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	LIGHTNING_GUN		" accepts "  "'s shaft"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	LIGHTNING_GUN		" accepts "  "' shaft"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	Q_LIGHTNING_GUN		" gets a natural disaster from "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	AXE					" was axed to pieces by " // KTX instagib
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	COIL_GUN			" was instagibbed by " // KTX instagib
	
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	RAIL_GUN			" was railed by "		//for dmm8
	
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	TELEFRAG			" was telefragged by "
	#DEFINE OBITUARY	X_FRAGS_Y		SQUISH				" squishes "
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" accepts "  "'s discharge"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" accepts "  "' discharge"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" drains "   "'s batteries"
	#DEFINE OBITUARY	X_FRAGGED_BY_Y	DISCHARGE			" drains "   "' batteries"
