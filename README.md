__Brian Blaylock__  
__July 2018__  
__[Website](http://home.chpc.utah.edu/~u0553130/Brian_Blaylock/home.html)__

# pyBKB_v3
These scripts help me be a successful meteorologist and were primarily used throughout my Ph.D. research at the University of Utah 2017-2019. 


# Anaconda Environment
> Please read the documents for managing environments.  
> Reference: https://github.com/Unidata/unidata-users-workshop  
> Reference: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html


I installed the Anaconda python distribution and created a new environment using the `environment.yml` file provided in this directory. The name of the environment is pyBKB_v3

    conda env create -f ./environment.yml

> NOTE: `pygrib` is not available on Windows, so that line should be commented out if installing on Windows.

On a windows computer, to activate the `pyBKB_v3` environment, do this in the Windows Command Prompt:

    activate pyBKB_v3

Or, if you are in the PowerShell

    cmd
    activate pyBKB_v3

If you are using a `bash` shell in Linux:

    conda init bash  # Only need to do this once to initialize the correct shell
    conda activate pyBKB_v3

If you are using a `tcsh` shell in Linux:

    conda init tsch  # Only need to do this once to initialize the correct shell
    conda activate pyBKB_v3



## Update environment
Deactivate the environment

    conda deactivate pyBKB_v3

Update the environment.yml file, and update the conda environment

    conda env update -f environment.yml

List all the available environments

    conda info --envs

