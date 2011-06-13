import os
import time
from datetime import date
import utils 

import sys

utils.ensure_exists('static/status')

cmds = [
    ('python scrape.py', False),             # downloads gamelogs from isotropic
    ('python parse_game.py', True),        # parses data into useable format
    ('python load_parsed_data.py', False),  # loads data into database
    ('python analyze.py', False),            # produces data for graphs
    ('python goals.py', False),
    ('python count_buys.py', False),
    ('python run_trueskill.py', False)
]

extra_args = sys.argv[1:]

# should think about how to parrallelize this for multiprocessor machines.
while True:
    for cmd, spittable in cmds:
        status_fn = (date.today().isoformat() + '-' +
                     time.strftime('%H:%M:%S') +
                     '-' + cmd.replace(' ', '_') + '.txt')
        cmd = cmd + ' ' + ' '.join(extra_args) + ' 2>&1 | tee -a ' + status_fn
        print cmd
        os.system(cmd)
        os.system('mv %s static/status' % status_fn)
    print 'sleeping'
    time.sleep(60*15)  # try to update every 15 mins
