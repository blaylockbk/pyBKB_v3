**Brian Blaylock**  
**October 10, 2019**

# Your Custom Anaconda Build


_If these instructions are out of date or incomplete, please update this document._

## Download and install Anaconda in your home directory. 
1. Download the 64-Bit installer for Linux from Anaconda.org to your home directory.
1. Execute module purge to clear out any preloaded python software.
 - This is an important step so that the instillation will not run into any path conflicts.
1. Run the `.sh` script to install Anaconda. I installed it in my home directory.
 - Anaconda will ask to install VS Code. I recommend using that text editor, but you will not have the correct privileges to install it in the path it wants to and will fail. If you want to install VS Code, do it after finishing the Anaconda build or on your local machine.

## Set up a custom module
Wim Cardon showed me how to make my own module to load anaconda3.
1. Make a new directory for custom modules. Mine is called `BB_modules`.
1. Make a directory in `BB_modules` called `bbanaconda3`. This name refers to my installed anaconda.
1. In `bbanaconda3`, create a new file called `5.2.0.lua`. This name refers to the Anaconda version 5.2.0. That file should contain the following (note, you will need need to change the python path to `python3.7` if that is the version you downloaded):
       
       --  -*- lua -*-
       help([[Module which sets the PATH variable for anaconda 5.2.0
              i.e.  python 3.6.5
              To  check the available packages: pip list
       ]])
       local home = os.getenv("HOME")
       local myana = pathJoin(home,"anaconda3")
       prepend_path("PATH",pathJoin(myana,"bin"))
       prepend_path("PYTHONPATH",pathJoin(myana,"lib/python3.6/site-packages"))

       whatis("Name         : Anaconda 5.2.0 | Python 3.6.5")
       whatis("Version      : 5.2.0 & Python 3.6.5 ")
       whatis("Category     : Compiler")
       whatis("Description  : Python environment ")
       whatis("URL          : http://www.continuum.io/ ")
       whatis("Installed on : 06/21/2018 ")
       whatis("Modified on  : --- ")
       whatis("Installed by : Brian Blaylock")

       family("python")

1. In your `.custom.csh` file  (located in your home directory), at the beginning add `module use ~/BB_modules`.
1. Restart your terminal and type `module avail` and you should see that `bbanaconda3/5.2.0` is available.
1. Since there is only one version of `bbanaconda3`, you can simply load with `module load bbanaconda3` or `module load bbanaconda3/5.2.0`.
1. Type `which python` and you will see you are using that custom version of python you just loaded.
1. Type `which conda` to confirm you are also using that custom version of conda.

Now you can manage your python version and install new packages with `conda install`.

---
### After you have an environment installed...

This assumes you have the `pyBKB_v3` environment...

There is some weirdness with the shell and the path variables being use. To activate an environment try:

       conda activate pyBKB_v3

If that doesn't work, try:

       conda init tcsh

and then retry

       conda activate pyBKB_v3

If that doesn't work, try:

       bash
       source activate pyBKB_v3