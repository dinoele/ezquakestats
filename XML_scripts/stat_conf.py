import ConfigParser
import io

from optparse import OptionParser,OptionValueError

class SectionlessConfig(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[config]\n'

    def readline(self):
        if self.sechead:
            try: 
                return self.sechead
            finally: 
                self.sechead = None
        else: 
            return self.fp.readline()

def read_config() :
   global nquakesv_root
   global scripts_root
   global reports_dir
   global matches_dir

   config = ConfigParser.SafeConfigParser()
   config.readfp(SectionlessConfig(open('stat.conf')))

   nquakesv_root = config.get("config", "nquakesv_root")
   scripts_root = config.get("config", "scripts_root")
   reports_dir = config.get("config", "reports_dir")
   matches_dir = config.get("config", "matches_dir")

