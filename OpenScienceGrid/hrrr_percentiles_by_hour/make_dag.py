# Brian Blaylock
# August 7, 2018

"""
Make a new DAGMan file for a set of jobs for a given variable. One job per
hour of the year.

Also:
    Create a ./log directory, if one doesn't exist
    Removes all old dag files.
"""

import os
from datetime import datetime, timedelta

variable = 'TMP:2-m'

# The date range (leap year)
sDATE = datetime(2016, 1, 1)
eDATE = datetime(2016, 1, 31)
# Which hours and forecasts
hours = range(1)
fxx = range(0,1)
window = 15
jobs_per_worker = 2

retry = 10

print('Creating DAGMan for:', variable)

# =============================================================================
# === Remove previous dag.dag.* files =========================================
"""
These files are created when you submit the dag.dag with condor_submit_dag,
but a new job cannot run if these files exist.
WARNING! We do not want to remove the submit.dag file, but if you do, it's ok
because this script makes a new one.
"""
rm = os.system('rm dag.dag.*')

# =============================================================================
# === Create a log directory if it doesn't exist ==============================
if not os.path.isdir('./log'):
    os.mkdir('./log')
    print('  - created ./log directory.')

# =============================================================================
# === Write the submit.dag file =+++==========================================
"""
This file is used to specify input arguments for each job

DAGMan File structure:
    JOB <job_id> <submit_file>
    VARS <job_id> <space_separated_list_of_variables>
    RETRY <job_id> 10
"""

var = variable.replace(' ', '-')
DATES = [sDATE + timedelta(days=d) for d in range((eDATE-sDATE).days)]


# length of DATES* length of hours must be divisible by jobs_per_worker.
# If DATES is all hours of the year equal to 1, 2, 3, 4, 6, 8, 9, 12, 16 if
# doing all hours of the year.

# Filter by number of jobs each worker works on (a worker will work on a date
# and then the next x number of days defined by jobs_per_worker).
jobDATES = DATES[::jobs_per_worker]
if len(DATES)*len(hours)%jobs_per_worker != 0:
        raise ValueError("job_per_worker must be divisible by %s" % len(DATES)*len(hours))
else:
    print('Writing %s unique jobs' % (len(jobDATES)*len(hours)))

# List the arguments for each job
args = [[D.month, D.day, hour, f]
        for D in jobDATES
        for hour in hours
        for f in fxx]

with open("submit.dag", "w") as f:
    for i, (month, day, hour, fxx) in enumerate(args):
        f.write('JOB %s.%s %s\n' % (var, i, "job.submit"))
        f.write('VARS %s.%s ID="%04d" var="%s" month="%s" day="%s" hour="%s" fxx="%s" window="%s" jobs_per_worker="%s"\n'
                 % (var, i, i, var, month, day, hour, fxx, window, jobs_per_worker))
        f.write('RETRY %s.%s %s\n' % (var, i, retry))
        f.write('\n')

print("  - Wrote a new submit.dag file for %s jobs." % len(args))