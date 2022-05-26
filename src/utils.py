import subprocess
import os
from datetime import datetime

config_path = os.path.join(os.getenv("HOME"), ".config/ptmm/")


def backup_db(max_backup=5):
    if max_backup < 1:
        pass
    else:
        if not os.path.exists(os.path.join(config_path, "bak")):
            exe_cmd(["mkdir", "-p", os.path.join(config_path, "bak")])
        if os.path.exists(os.path.join(config_path, "bak", "ptmm.db." + str(max_backup))):
            exe_cmd(["rm", "-rf", os.path.join(config_path, "bak", "ptmm.db." + str(max_backup))])

        for i in range(1, max_backup):
            if os.path.exists(os.path.join(config_path, "bak", "ptmm.db." + str(max_backup - i))):
                exe_cmd(["mv", os.path.join(config_path, "bak", "ptmm.db." + str(max_backup - i)),
                         os.path.join(config_path, "bak", "ptmm.db." + str(max_backup - i + 1))])
        exe_cmd(["cp", os.path.join(config_path, "ptmm.db"), os.path.join(config_path, "bak", "ptmm.db.1")])


def write_log(content: str):
    if not os.path.isdir(os.path.join(config_path, "log")):
        exe_cmd(["mkdir", "-p", os.path.join(config_path, "log")])
    date = datetime.now().strftime("%Y-%m-%d")
    date_time = datetime.now().strftime("%Y-%m-%d, %H:%M:%S ")
    with open(os.path.join(config_path, "log", date), "a") as log_file:
        log_file.write(date_time + " " + content + "\n\n")


def exe_cmd(cmd: list):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    errcode = process.returncode
    return_content = str(out.decode("utf-8")) + " " + str(err.decode("utf-8"))
    if errcode == 0:
        log_content = "[info] " + return_content + " ok: " + " ".join(cmd)
        write_log(log_content)
    else:
        log_content = "[error] " + return_content + " fail: " + " ".join(cmd)
        write_log(log_content)

    return errcode, return_content
