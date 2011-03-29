import os
# this should be in apache config rather rather than code, but I like
# coding more than I like figuring out apache configuration.  Sorry if it
# is killing you, feel free to change it for your setup
os.chdir('/home/rrenaud/dominionstats')  

import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)
import web

from frontend import *

application = application.wsgifunc()
