# Brian Blaylock
# August 6, 2018

"""
Create a DAGMan to submit many jobs to the OSG
Daily job by hour
"""

import os

variable = 'TMP:2 m'
fxx = 0
months = range(1, 13)
days = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
hours = range(24)
window = 15
jobs_per_worker = 4

print('Creating dagman job scripts for:', variable)

cwd = os.getcwd()

# =============================================================================
# === Remove previous dag.dag.* files =========================================
"""
These files are created when you submit the dag.dag with condor_submit_dag,
but a new job can not run if these files exist.
WARNING! We do not want to remove the dag.dag file, but if you do, it's ok
because this script makes a new one.
"""
rm = os.system('rm dag.dag.*')

# =============================================================================
# === Create a log directory if it doesn't exist ==============================
if not os.path.isdir('./log'):
    os.mkdir('./log')
    print('  - created ./log directory.')

# =============================================================================
# === Write the splice_dag.dag file ===========================================
"""
This file is used to specify input arguments for each job

DAGMan File structure:
    JOB <job_id> <submit_file>
    VARS <job_id> <space_separated_list_of_variables>
    RETRY <job_id> 10
"""

var = variable.replace(' ','-')

args = [[var, month, day, hour, fxx, window, jobs_per_worker]
        for month in months
        for day in range(1, days[month - 1] + 1)
        for hour in hours]

osg_script = "../OSG_hourly_30/OSG_HRRR_composite_hourly30.py"
hrrr_script = "../OSG_hourly_30/HRRR_S3.py"

count = 0

with open("splice_dag.dag", "w") as f:

    for i, (v, month, day, hour, fxx) in enumerate(args):
        expected_file_here = 'OSG_HRRR_%s_m%02d_d%02d_h%02d_f%02d.h5' % (var, month, day, hour, fxx)
        expected_file_stash = '/home/blaylockbk/stash/fromScratch/%s/%s' % (var, expected_file_here)
        if os.path.exists(expected_file_here) is False and os.path.exists(expected_file_stash) is False:
            # If the expected file doesn't exist, write a dagman job for it
            count += 1
            f.write("JOB %s_%s %s\n" % (var, i, "dagman.submit"))
            f.write(("VARS %s_%s osg_python_script=\"%s\" "
                    "hrrr_s3_script=\"%s\" var=\"%s\" "
                    "month=\"%s\" day=\"%s\" hour=\"%s\" "
                    "fxx=\"%s\"\n") % (var, i, osg_script, hrrr_script,
                                        v.replace(' ', '_'), month,
                                        day, hour, fxx))
            f.write("RETRY %s_%s 10\n" % (var, i))

print "  - Wrote a new splice_dag.dag file for %s missing files." % count


# =============================================================================
# === Write the dag.dag file ==================================================
"""
Makes sure the dag.dag file uses scripts/files in the current working directory
"""
with open("dag.dag", 'w') as f:
    f.write('SPLICE utah_1 %s/splice_dag.dag\n' % cwd)
    f.write('JOB utah_1_noop2 %s/splice_dag.dag NOOP\n' % cwd)
    f.write('SCRIPT POST utah_1_noop2 %s/globus_transfer.sh\n' % cwd)
    f.write('PARENT utah_1 CHILD utah_1_noop2')

print "  - Wrote a new dag.dag file using %s as the cwd." % cwd


# =============================================================================
# === Write the globus_transfer.sh script =====================================
"""
Write the globus_transfer.sh script to transfer the output files to CHPC via Globus.
    (Must have the directory already created on the CHPC endpoint)
"""

from_here = '~/stash/fromScratch/%s/' % var
to_here = '~/../horel-group2/blaylock/HRRR_OSG/hourly30/%s/' % var

with open('globus_transfer.sh', 'w') as f:
    f.write("""#!/bin/bash

. /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash

# Redirect stdout ( > ) into a named pipe ( >() ) running "tee"
exec > >(tee -i postscript_logfile.txt)

# Without this, only stdout would be captured - i.e. your
# log file would not contain any error messages.
# SEE (and upvote) the answer by Adam Spiers, which keeps STDERR
# as a separate stream - I did not want to steal from him by simply
# adding his answer to mine.
exec 2>&1

module load python/2.7
module load globus-cli

# Move every .h5 file from the /local-scratch/blaylock directory to my stash directory
mv *.h5 %s

# https://docs.globus.org/cli/using-the-cli/
# Endpoint IDs found from 'globus endpoint search Tutorial'
# https://docs.globus.org/cli/examples/

# Endpoint IDs found from 'globus endpoint search Tutorial'
# On Globus transfer dashboard, https://www.globus.org/app/transfer,
# click on "Endpoints" and, the name, and copy the UUID.
ep1=9a8e5a67-6d04-11e5-ba46-22000b92c6ec    # OSG Stash Endpoint (Never Expires)
ep2=219793b8-c8b7-11e7-9586-22000a8cbd7d    # UofU Endpoint (Expires every 3 months)
                                            # Must login to globus to reactivate.

# Recursively transfer the fromScratch folder from stash endpoint to CHCP endpoint
globus transfer $ep1:%s $ep2:%s --recursive --label "DAGMan from OSG, %s, CLI single folder" --sync-level mtime

""" % (from_here, from_here, to_here, var))

# I think you must make this script executable, but I'm not 100% sure
os.system('chmod 755 globus_transfer.sh')

print "  - Wrote a new globus_transfer.sh script."
print ""
