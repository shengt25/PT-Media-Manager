import os
import configparser
import sys
import readline  # Don't delete this, so you can use arrow key when input string
from datetime import datetime
from src.C_Database import MediaDB
from src.utils import exe_cmd, backup_db, write_log
from src.C_WeCom import WeCom


# todo exclude not complete
def print_help():
    print("-h       --help              show this help\n"
          "-l       --list              list all media\n"
          "-s       --scan              scan media in all source and make link\n"
          "-ss      --scan-silently     scan silently(no confirmation)\n"
          "-a       --add-entry         add entry(source path, target link path)\n"
          "-d       --del-entry         delete entry and delete the target link path\n"
          "-e       --edit-entry        edit entry name, source path or link path\n"
          "-lp      --list-path         list all entry path\n"
          "-dm      --del-media         delete media manually(debug)\n")


def config_loader():
    config = configparser.ConfigParser()
    running_py = os.path.realpath(__file__)
    working_dir = running_py[:running_py.rfind("/")]
    config.read(os.path.join(working_dir, "ptmm.conf"))

    common_settings = [config["common"]["wecom"],
                       [x.strip() for x in config["common"]["incomplete-ext"].split(",")],
                       [x.strip() for x in config["common"]["ignore-ext"].split(",")]]
    wecom_settings = []
    if config["common"]["wecom"] == "yes":
        wecom_settings = [config["wecom"]["corp-id"], config["wecom"]["secret"], config["wecom"]["agent-id"],
                          [x.strip() for x in config["wecom"]["user-ids"].split(",")]]
    return common_settings, wecom_settings


class PTMM:
    def __init__(self):
        backup_db()
        common_settings, wecom_settings = config_loader()
        config_path = os.path.join(os.getenv("HOME"), ".config/ptmm/")
        self.wecom_enable, self.incomplete_ext, self.ignore_ext = common_settings
        self.database = MediaDB(os.path.join(config_path, "ptmm.db"))
        self.wecom_settings = wecom_settings

    def _wecom_msg(self, contents):
        corp_id = self.wecom_settings[0]
        secret = self.wecom_settings[1]
        agent_id = self.wecom_settings[2]
        user_ids = self.wecom_settings[3]
        wecom = WeCom(corp_id=corp_id, secret=secret, agent_id=agent_id)
        for user_id in user_ids:
            wecom.send_message(wecom_id=user_id, msg_type="text", contents=contents)

    def _check_exist(self, entry_name, media_name):
        """:return: return if the name is duplicated, 1 for yes, 0 for no"""
        name_in_entry = self.database.media_get_by_entry(entry_name)
        duplicate = 0
        if len(name_in_entry) != 0:
            for name in name_in_entry:
                if media_name == name[1]:
                    duplicate = 1
        return duplicate

    def _system_hidden_file(self, filename):
        result = 0
        if filename == ".DS_Store" or filename[:2] == "._":
            result = 1
        return result

    def _only_system_hidden_file(self, media_path):
        """:return: return if the path only contain '.DS_Store' and '._*' files, 1 for yes, 0 for no"""
        result = 0
        system_hidden_file_count = 0
        file_count = 0
        if os.path.isdir(media_path):
            for root, dirs, files in os.walk(media_path):
                for file in files:
                    file_count += 1
                    if self._system_hidden_file(file) == 1:
                        system_hidden_file_count += 1
            if file_count == system_hidden_file_count:
                result = 1
        return result

    def _is_incomplete(self, media_path):
        """:return: return if the path contain incomplete file, 1 for yes, 0 for no"""
        result = 0
        if os.path.isfile(media_path):
            for ext in self.incomplete_ext:
                if media_path[-1 * len(ext):] == ext:
                    result = 1
                    break
        else:
            for root, dirs, files in os.walk(media_path):
                for file in files:
                    for ext in self.incomplete_ext:
                        if file[-1 * len(ext):] == ext:
                            result = 1
                            break
        return result

    def _media_add(self, entry_name, new_media_name):
        # make link
        _, source_path, link_path = self.database.path_get(entry_name=entry_name)
        # single file link
        if os.path.isfile(os.path.join(source_path, new_media_name)):
            exe_cmd(["mkdir", "-p", os.path.join(link_path, new_media_name)])
            exe_cmd(["ln", os.path.join(source_path, new_media_name),
                     os.path.join(link_path, new_media_name, new_media_name)])
        # directory links
        elif os.path.isdir(os.path.join(source_path, new_media_name)):
            for root, dirs, files in os.walk(os.path.join(source_path, new_media_name)):
                exe_cmd(["mkdir", "-p", root.replace(source_path, link_path, 1)])

                for ext in self.ignore_ext:
                    for file in files:
                        if file[-1 * len(ext):] == ext:
                            files.remove(file)

                for file in files:
                    exe_cmd(
                        ["ln", os.path.join(root, file), os.path.join(root, file).replace(source_path, link_path, 1)])
        else:
            exit(1)
        self.database.media_insert(media_name=new_media_name, entry_name=entry_name)

    def _media_del(self, entry_name, media_name):
        link_path = self.database.path_get(entry_name)[2]
        self.database.media_del(entry_name=entry_name, media_name=media_name)
        exe_cmd(["rm", "-rf", os.path.join(link_path, media_name)])

    def _entry_selector(self):
        # list and select entry
        entry_name = ""
        current_entry_name = ptmm.database.entry_get()
        for index, entry_name_ in enumerate(current_entry_name):
            print(f"{index}: {entry_name_}")
        entry_index = input("\nPlease select an entry: ")
        if entry_index == "":
            print("Exiting")
            exit(1)
        try:
            entry_name = current_entry_name[int(entry_index)]
        except IndexError:
            print("Index error")
            exit(1)
        return entry_name

    def _list_media_formated(self, data_raw):
        terminal_width = os.get_terminal_size()[0]
        # terminal_width = 70  # for test in IDE
        width_id = 6
        width_all = int(0.9 * terminal_width - 2 * 6)
        width_date = len(str(datetime.now())[:-7])
        width_name = width_all - width_id - width_date
        for data in data_raw:
            if type(data) != list:
                print(f"\n[{data}]")
            else:
                print(f"total: {len(data)}")
                print(f"{'':-<{width_all + 2 * 6 + 4}}")
                print(f"|  {'id':<{width_id + 2}}|  {'date':<{width_date + 2}}|  {'name':<{width_name + 2}}")
                print(f"{'':-<{width_id + width_date + width_name + 2 * 6 + 4}}")
                for data_single in data:
                    width_name_remain = len(data_single[1])
                    width_name_done = 0
                    while width_name_remain >= 0:
                        # print id or empty
                        if width_name_done == 0:
                            print(f"|  {data_single[0]:<{width_id + 2}}", end="")
                        else:
                            print(f"|  {' ' * (width_id + 2)}", end="")
                        # print date or empty
                        if width_name_done == 0:
                            print(f"|  {data_single[2][:-7]:<{width_date + 2}}", end="")
                        else:
                            print(f"|  {' ' * (width_date + 2)}", end="")
                        # print name
                        print(f"|  {data_single[1][width_name_done:width_name_done + width_name]:<{width_name + 2}}", )
                        width_name_done += width_name
                        width_name_remain -= width_name
                    print(f"{'':-<{width_id + width_name + width_date + 2 * 6 + 4}}")

    def list_path_all(self):
        entry_all = self.database.entry_get()
        for entry in entry_all:
            print(self.database.path_get(entry))

    def list_media_all(self):
        info_all = self.database.media_get_all()
        self._list_media_formated(info_all)

    def entry_add(self):
        # entry name no duplicated
        new_entry_name = input("Please input new entry name: ")
        if new_entry_name == "":
            exit(1)
        current_entry_all = self.database.entry_get()
        if new_entry_name in current_entry_all:
            print(f"{new_entry_name} already exist")
            exit(1)
        # source path no duplicated
        new_source_path = input("Please input source path: ")
        if new_source_path == "":
            exit(1)
        for current_entry in current_entry_all:
            current_source_path = self.database.path_get(current_entry)[1]
            if current_source_path == new_source_path:
                print(f"This path have already been used by {current_entry}")
                exit(1)
        # link path no duplicated
        new_link_path = input("Please input target path: ")
        if new_link_path == "":
            exit(1)
        for current_entry in current_entry_all:
            current_link_path = self.database.path_get(current_entry)[2]
            if current_link_path == new_link_path:
                print(f"This path have already been used by {current_entry}")
                exit(1)
        # remove ending '/'
        while new_source_path[-1] == "/":
            new_source_path = new_source_path[:-1]
        while new_link_path[-1] == "/":
            new_link_path = new_link_path[:-1]

        if not os.path.exists(new_link_path):
            exe_cmd(["mkdir", "-p", new_link_path])
        self.database.entry_create(entry_name=new_entry_name, source_path=new_source_path, link_path=new_link_path)

    def entry_del(self):
        entry_name = self._entry_selector()
        print(f"All hard link files in {entry_name} will be deleted. (Original files will NOT be deleted)")
        confirm = input("Confirm? y/N: ")
        if confirm == "y" or confirm == "Y":
            link_path = self.database.path_get(entry_name)[2]
            exe_cmd(["rm", "-rf", link_path])
            self.database.entry_del(entry_name)

    def entry_edit(self):
        entry_name = self._entry_selector()
        # new entry name
        new_entry_name = input("New entry name (leave blank to keep):")
        if new_entry_name != "":
            self.database.entry_edit(entry_name=entry_name, new_entry_name=new_entry_name)
            entry_name = new_entry_name
        # new source path
        new_source_path = input("New source path (leave blank to keep):")
        if new_source_path != "":
            self.database.entry_edit(entry_name=entry_name, new_source_path=new_source_path)
        # new link path
        new_link_path = input("New link path (leave blank to keep):")
        if new_link_path != "":
            old_link_path = self.database.path_get(entry_name)[2]
            if os.path.exists(new_link_path):
                if len(os.listdir(new_link_path)) != 0:
                    print("Path already contains file, please check")
                else:
                    self.database.entry_edit(entry_name=entry_name, new_link_path=new_link_path)
                    exe_cmd(["rm", "-rf", new_link_path])
                    exe_cmd(["mv", old_link_path, new_link_path])
            else:
                self.database.entry_edit(entry_name=entry_name, new_link_path=new_link_path)
                exe_cmd(["mv", old_link_path, new_link_path])

        if new_source_path != "":
            confirm = input("Source path changed, re-scan now? Y/n: ")
            if confirm == "y" or confirm == "Y" or confirm == "":
                self.media_scan()

    def media_scan(self, silent=False):
        entry_all = self.database.entry_get()
        # loop for every entry
        for entry_name in entry_all:
            delete_list = []
            delete_list_source = []
            add_list = []
            print(f"\nScanning {entry_name}")
            _, source_path, link_path = self.database.path_get(entry_name=entry_name)
            # get media data in entry
            media_data = self.database.media_get_by_entry(entry_name)
            # when there is data
            if len(media_data) != 0:
                for media_data_single in media_data:
                    media_name = media_data_single[1]
                    # add link to delete list if source not exist
                    if not os.path.exists(os.path.join(source_path, media_name)):
                        delete_list.append(media_name)
                    # add link and source to delete list if source only contain system hidden file
                    elif self._only_system_hidden_file(os.path.join(source_path, media_name)) == 1:
                        delete_list.append(media_name)
                        delete_list_source.append(media_name)
            # delete (and log)
            if silent:
                for delete_media_name in delete_list:
                    self._media_del(entry_name=entry_name, media_name=delete_media_name)
                for delete_media_name in delete_list_source:
                    exe_cmd(["rm", "-rf", os.path.join(source_path, delete_media_name)])
                # log
                if len(delete_list) == 0:
                    write_log("[info] Deleted: nothing")
                else:
                    write_log(f"[info] Deleted link: {delete_list}")
                    write_log(f"[info] Deleted source: {delete_list_source}")
            # ask for confirmation to delete and no log
            else:
                for delete_media_name in delete_list:
                    confirm = input(f"Deleting {delete_media_name} ,confirm? Y/n: ")
                    if confirm == "y" or confirm == "Y" or confirm == "":
                        self._media_del(entry_name=entry_name, media_name=delete_media_name)
                        print("Deleted")
                for delete_media_name in delete_list_source:
                    confirm = input(f"Deleting {delete_media_name} (from source) ,confirm? Y/n: ")
                    if confirm == "y" or confirm == "Y" or confirm == "":
                        exe_cmd(["rm", "-rf", os.path.join(source_path, delete_media_name)])
                        print("Deleted")

            # get media name from source path
            media_name_all = os.listdir(source_path)
            # sort by date
            media_name_all_sort = []
            for media_name in media_name_all:
                media_name_all_sort.append(os.path.join(source_path, media_name))
            media_name_all_sort.sort(key=os.path.getctime)
            media_name_all = []
            for media_name in media_name_all_sort:
                media_name_all.append(media_name.replace(source_path + "/", ""))
            # add to add list
            for media_name in media_name_all:
                if self._is_incomplete(media_path=os.path.join(source_path, media_name)) == 0 \
                        and self._only_system_hidden_file(media_path=os.path.join(source_path, media_name)) == 0 \
                        and self._system_hidden_file(filename=media_name) == 0:
                    if not self._check_exist(entry_name=entry_name, media_name=media_name):
                        add_list.append(media_name)
            # add (and log)
            if silent:
                for add_media_name in add_list:
                    self._media_add(entry_name=entry_name, new_media_name=add_media_name)
                    write_log(f"[info] Added: {add_media_name}")
            else:
                for add_media_name in add_list:
                    confirm = input(f"Adding {add_media_name},confirm? Y/n: ")
                    if confirm == "y" or confirm == "Y" or confirm == "":
                        self._media_add(entry_name=entry_name, new_media_name=add_media_name)
                        print("Added")

    def media_del_manually(self):
        # list and select entry
        entry_name = self._entry_selector()
        self._list_media_formated(ptmm.database.media_get_by_entry(entry_name))
        # list and select media
        media_id = input("Please input media id: ")
        if media_id == "":
            return 0
        media_name = self.database.media_get_by_id(entry_name=entry_name, media_id=media_id)[1]
        # confirm delete
        print("Delete:", media_name)
        confirm = input("Confirm? Y/n: ")
        if confirm == "y" or confirm == "Y" or confirm == "":
            self._media_del(entry_name=entry_name, media_name=media_name)

    def commit(self):
        self.database.commit()

    def close(self):
        self.database.close()


if __name__ == "__main__":
    ptmm = PTMM()
    try:
        argv = str(sys.argv[1])
        if argv == "-h" or argv == "--help":
            print_help()
        elif argv == "-l" or argv == "--list-media":
            ptmm.list_media_all()
        elif argv == "-s" or argv == "--scan-media":
            ptmm.media_scan()
        elif argv == "-ss" or argv == "--scan-silently":
            ptmm.media_scan(silent=True)
        elif argv == "-a" or argv == "--add-entry":
            ptmm.entry_add()
        elif argv == "-d" or argv == "--del-entry":
            ptmm.entry_del()
        elif argv == "-e" or argv == "--edit-entry":
            ptmm.entry_edit()
        elif argv == "-lp" or argv == "--list-path":
            ptmm.list_path_all()
        elif argv == "-dm" or argv == "--del-media-manually":
            ptmm.media_del_manually()
        else:
            print("use -h or --help for help")
    except IndexError:
        print_help()

    ptmm.commit()
    ptmm.close()
