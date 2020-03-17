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

---
## How to using these modules
`pyBKB_v3` is kept in `$HOME/pyBKB_v3`. One way to use these modules into your scripts is to append the sys path in your script.

```python
import sys
sys.path.append('/path/to/folder/pyBKB_v3')

# Load some module from pyBKB_v3
import BB_mesowest
```

But that is a little cumbersome when you just want to get started quick.

Instead, you can update the `PYTHONPATH` variable in your environment to automatically append the path. I inserted the following into my `.bashrc` file.

```bash
export PYTHONPATH=$HOME/pyBKB_v3:$PYTHONPATH
```

After that variable is applied, when you open python and print out the value of `sys.path`, you will see that the pyBKB_v3 directory is included. This means that a simple ```module load BB_mesowest``` in your python script will load the module. **This is an important change to know if you are not Brian and you are using these my modules, as some of my scripts assume the PYTHONPATH as been set while others will explicily append the sys.path.**

---

## Tunnel Jupyter Lab through Putty
When running Jupyter Lab on a remote computer, you can tunnel Jupyter to your local browser window.

To configure Putty for an ssh Tunnel...

1. In the left, click `Connection` > `SSH` > `Tunnels`
2. In the source port, replace #### with a port number you chose between 7000 and 8000.
3. In the destination, add `localhost:####`
4. Click `Add`
5. Confirm that you see `L####   localhost:####` in the list of forwarded paths.
6. REMEMBER TO SAVE THE SESSION!

![](./images/putty_config_tunnel.png)

Now, on the remote machine, run Jupyter Lab

    jupyter lab --no-browser --port=####

Jupyter will fire up and provide a URL and token you can copy and paste into your local browser. Something like this...

    copy and paste the URL:
        http://localhost:####/?token=.........

I added an alias to my ~/.bashrc file on my remote machine as a short cut

    alias jupy='cd / && jupyter lab --no-browser -port=7686

Note that I first change to the root direcotry, `cd /`, so I have access to the full system rather than just being confined to the directory from with I open Jupyter.
