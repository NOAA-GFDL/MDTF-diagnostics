import os
import subprocess

#============================================================
# generate_ncl_call - call a ncl_script via subprocess call
#============================================================
def generate_ncl_call(ncl_script):
    """generate_plots_call - call a ncl_script via subprocess call
        Arguments:
            ncl_script (string) - full path to ncl plotting file name
    """
   # check if the ncl_script exists -
   # don't exit if it does not exists just print a warning.
    try:
        pipe = subprocess.Popen(['ncl {0}'.format(ncl_script)], shell=True, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = pipe.communicate()[0]
        # don't need pipe.poll since pipe.communicate waits for process to finish
        output = '\t'+output.replace('\n','\n\t') # indent output
        print('NCL routine {0}:\n{1}'.format(ncl_script, output))
    except OSError as e:
        print('WARNING',e.errno,e.strerror)

    return 0

## print os.environ["POD_HOME"]
