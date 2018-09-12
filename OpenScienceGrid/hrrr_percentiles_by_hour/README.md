<img src='../OSG_logo.png' align=right height=120>

Brian Blaylock  
August 7, 2018

# High-Resolution Rapid Refresh Model Hourly Empirical Cumulative Distribution Climatology 

This set of files manages the Open Science Grid (OSG) workflow  used to computes hourly empirical cumulative distribution at all grid points in the High-Resolution Rapid Refresh (HRRR) model domain for the archive record. The [Pando HRRR archive](http://hrrr.chpc.utah.edu/) currently has two years of data stored (July 2016-Present). To increase the sample size of the empirical cumulative distribution for each hour, percentiles are calculated with a 31 day window centered on the hour (+/- 15 days).

For example, the December 15th 0000 UTC cumulative distribution used all 0000 UTC grids between November 30 through December 30 from the year 2016 and 2017, a total of 62 samples.

---

## Workflow
Four basic steps are performed by each worker node:

1. The HRRR grids are downloaded from the Pando HRRR Archive.
2. A set of percentiles is computed with `numpy.percentiles()`.
3. The results are written in an HDF5 file.
4. The HDF5 file is transferred to the Pando archive via `rclone`.

Each remote worker on the OSG is sent instructions to perform work for a unique hour of the year.

> **Note:** Running these scripts requires Python 3 with pygrib installed. These are installed in the Docker/Singularity container. For more information, read the Python 3 and Docker section below.

> **Note:** This work requires functions and scripts from **`pyBKB_v3`**. Use `git clone https://github.com/blaylockbk/pyBKB_v3.git` or `git pull https://github.com/blaylockbk/pyBKB_v3.git` to retrieve the package of custom scripts. Then copy the directories `BB_HRRR` and `BB_wx_calcs` to the working directory you will submit OSG jobs from. Also, copy from **`pyBKB_v3`** the script `/OpenScienceGrid/hrrr_percentiles_by_hour/percentiles.py` to the current working directory.

> **Note:** Please create a directory in your submit directory named `log`. The jobs will dump error, output, and log information here.

### Work Script: `percentiles.py`
This script is responsible for completing the three steps described above for the hour of the year it is assigned.
The inputs required by `percentiles.py` is the following: 

1. _var_: The HRRR variable the statistics are to be computed for. Must be in the form similar to the GRIB2 .idx file with a `-` used instead of spaces. For example, `TMP:2-m`, `REFC:entire`, `HGT:500-mb`, `UVGRD:10-m`, `WIND:10-m`, etc.
2. _month_: The month of the year to work on. A number between 1 and 12. This represents the valid datetime.
3. _day_: The day of the month to work on.
4. _hour_: The hour of the day to work on. Note: month, day, and hour represent the model's _valid_ time.
5. _fxx_: The forecast lead time. A number between 0 and 18. Typically will use fxx=0, unless you want to compare cumulative distributions at different lead times.
6. _window_: The number of days, before and after, to include in the percentile calculations for each hour. This work uses a window of 15 days +/- the hour of interest. Thus, each computation uses 31 grids for each year. With two years of data available, this means each computation uses 62 samples.
7. _jobs_per_worker_: Defines the number of days each worker node should work on. If this is set to 1, then each worker does one hour. However, to improve download efficiency from Pando, a worker can utilize the same model grids it has already downloaded for computations spanning the next day. A good number to use here is between 2 and 8.

This script defines what statistics are computed. It currently computes the mean and the following percentiles: 
> 0 (minimum), 1, 2, 3, 4, 5, 10, 25, 33, 50 (medium), 66, 75, 90, 95, 96, 97, 98, 99, 100 (maximum).

The output HDF5 files contain information about the number of cpus used, time spend downloading, time spent doing the calculation, number of samples used, and the date range of the files. It is saved in the following format: 
> OSG_HRRR_TMP-2-m_m01_d01_h00_f00.h5

>>>**Future Implementation** The HDF5 file is then transferred to the the Pando archive OSG bucket using `rclone`. In order to do this we have to transfer the configuration file `.rclone.conf`.

This script can be tested by supplying appropriate input arguments. For example, the following generates a file for 2 meter temperature on January 1, 0000 UTC for the model analysis (fxx=0) with a 15 day window (31 days) and the job will complete 1 job.

    $ python percentiles.py TMP:2-m 1 1 0 0 15 1

### Wrapper Script: `runthis.sh`
This wrapper script appends the `PATH` so we can use Python in the container (see section below about Python and Docker) and then runs the `percentiles.py` script with the arguments described above.

    #!/bin/bash
    # Link path to Python in the singularity image
    PATH=/opt/conda/bin:$PATH
    echo $PATH
    which python
    python percentiles.py $1 $2 $3 $4 $5 $6 $7

The script arguments required by `percentiles.py` come from the `job.submit` file.

### HTCondor Job Submit Script: `job.submit`
This file is an HTCondor submit file. It is used to define the job requirements and specifications to run the job on the OSG. It contains the following parts:

First, set the universe to use the "vanilla" or default settings. Also require the worker to have Singularity, which our jobs will run in. The Singularity image we use is linked.

    universe = vanilla
    requirements = HAS_SINGULARITY == True
    +SingularityImage = "/cvmfs/singularity.opensciencegrid.org/blaylockbk/miniconda3_osg:latest"

The next section is specific to running the job executable `runthis.sh`. The arguments are variable defined by VARS in the `submit.dag` file. We also must transfer the script `percentiles.py` and the directories `BB_HRRR` and `BB_wx_calcs` which contains functions used by `percentiles.py`. These two directories and this script must be in the working directory the job is submitted from.

    executable = runthis.sh
    arguments = $(var) $(month) $(day) $(hour) $(fxx) $(window) $(jobs_per_worker)
    transfer_input_files = percentiles.py, BB_HRRR, BB_wx_calcs

Then we tell the job to return the output files ON_EXIT.

    should_transfer_files = YES
    when_to_transfer_output = ON_EXIT

Now we specify a location to save the log, error, and output files. If you have not already, create a directory called `log` to store all these files. Name the files by the ID given in DAGMan so we can troubleshoot a specific job, if needed.

    error = ./log/job_$(ID).err
    output = ./log/job_$(ID).out
    log = ./log/job_$(ID).log

Specify the hardware requirements. This requires some testing and viewing the tail of the log file to determine how much memory or disk is needed. These settings work well for requesting ~60 single variable HRRR grids. By commenting the `request_cpus` we will not limit our job by available cpus. Instead, we will use all available.

    request_memory = 6GB
    request_disk = 150MB
    #request_cpus = 1

Sometimes, jobs run away and run much longer than they are supposed to. The following will hold jobs that are running longer than 20 minutes (1200 seconds) and then resubmit those jobs after 10 minutes (600 seconds).

    periodic_hold = (CurrentTime - JobCurrentStartDate) >= 1200
    periodic_release = (NumJobStarts < 5) && ((CurrentTime - EnteredCurrentStatus) >= 600)


Finally, the queue statement is added to submit the job

    queue

### DAGMan Jobs: `submit.dag`
HTCondor job submissions are managed by DAGMan. The `submit.dag` file defines each of the jobs that are to run (`job.submit`), the variable used for the submission arguments, and the number of retries (10) in case the job fails for any reason, like preemption. There is a unique set of entries for each job and follows the following format:

    JOB TMP:2-m.0 job.submit
    VARS TMP:2-m.0 ID="0000" var="TMP:2-m" month="1" day="1" hour="0" fxx="0" window="15" jobs_per_worker="2"
    RETRY TMP:2-m.0 10

The python script `make_dag.py` automatically creates the `submit.dag` file for a defined set of variables.

### Submit Jobs to OSG
Jobs are submitted to the OSG through the HTCondor scheduler

    $ condor_submit_dag submit.dag

Monitor the progress of the jobs with any of these commands:

    $ condor_q                        # show the batch of jobs
    $ condor_q -nobatch -dag          # shows names of each dag job with name
    $ watch condor_q -nobatch -dag    # ctrl+c to exit watch mode

If for whatever reason you need to remove the jobs, you can resubmit them where you left of with the same `condor_submit_dag` command. DAGMan will use the rescue dag file to only submit those jobs that haven't finished.

---

## Python 3 and Docker
The Docker image you used is [`blaylockbk/miniconda3_osg`](https://hub.docker.com/r/blaylockbk/miniconda3_osg/). OSG routinely updates the image with any changes across the network and converts that image to a Singularity container.

To use this image on OSG, include the following two lines in the `submit` file:

    requirements = HAS_SINGULARITY == True
    
    +SingularityImage = "/cvmfs/singularity.opensciencegrid.org/blaylockbk/miniconda3_osg:latest"

For testing scripts, you may use the image interactively with the following command:

    singularity shell /cvmfs/singularity.opensciencegrid.org/blaylockbk/miniconda3_osg:latest/

> **Warning!** Exit the Singularity container before you submit condor jobs.

In both the wrapper script executed upon submission or if you are working in the container interactivley, you must append the `PATH` variable before you can use python. 

    $ PATH=/opt/conda/bin:$PATH



