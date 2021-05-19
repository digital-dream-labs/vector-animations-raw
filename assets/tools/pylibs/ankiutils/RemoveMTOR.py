import os
import sys
import subprocess
COZMO_ANIM_DIR = os.path.join( os.environ['HOME'], 'workspace','cozmo-animation','scenes','anim')
VICTOR_ANIM_DIR = os.path.join( os.environ['HOME'], 'workspace','victor-animation','scenes','anim')
def run_command_core(cmd):
    stdout_pipe = subprocess.PIPE
    stderr_pipe = subprocess.PIPE
    # print("Running: %s" % cmd)
    try:
        p = subprocess.Popen(cmd, stdout=stdout_pipe, stderr=stderr_pipe,
                             shell=False)
    except OSError as err:
        #cmds.warning("Failed to execute '%s' because: %s" % (cmd, err))
        return (None, None, None)
    (stdout, stderr) = p.communicate()
    status = p.poll()
    return (status, stdout, stderr)



req = 'requires "mtor" "4.0";'

cmd = ['grep','-lr','mtor',COZMO_ANIM_DIR]
st, std, ste = run_command_core(cmd)

tmpfile = os.path.join (os.environ['TMPDIR'],'mtor_temp_file.ma')
print tmpfile


mtor_files = std.split('\n')
for m in mtor_files:
    if m.endswith('.ma'):
        print "doing ",m
        fout = open(tmpfile,'w')
        fid = open(m,'r')
        for line in fid:
            if req not in line:
                fout.write(line)
        #stop -= 1
        #if stop ==0:
        #    fid.close()
        #    fout.close()
        #    break
        fid.close()
        fout.close()
        os.rename(tmpfile, m)








