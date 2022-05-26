import os
import configparser
import sys
import readline  # Don't delete this, so you can use arrow key when input string
from datetime import datetime
from src.C_Database import MediaDB
from src.utils import exe_cmd, backup_db
from src.C_WeCom import WeCom


# todo backup


def config_loader():
    config = configparser.ConfigParser()
    running_py = os.path.realpath(__file__)
    working_dir = running_py[:running_py.rfind("/")]
    config.read(os.path.join(working_dir, "ptmm.conf"))

    common_settings = [config["common"]["log-level"], config["common"]["wecom"],
                       [x.strip() for x in config["common"]["block_exts"].split(",")]]
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
        self.log_level, self.wecom_enable, self.block_exts = common_settings
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

    def _only_macos_hidden_file(self, media_path):
        """:return: return if the path only contain '.DS_Store' and '._*' files, 1 for yes, 0 for no"""
        macos_hidden_file_count = 0
        file_count = 0
        for root, dirs, files in os.walk(media_path):
            for file in files:
                file_count += 1
                if file == ".DS_Store" or file[:2] == "._":
                    macos_hidden_file_count += 1
        if file_count == macos_hidden_file_count and file_count != 0:
            result = 1
        else:
            result = 0
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

                for block_ext in self.block_exts:
                    for file in files:
                        if file[-1 * len(block_ext):] == block_ext:
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
        current_entry_all = self.database.entry_get()
        if new_entry_name == "":
            exit(1)
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
        confirm = input("Confirm? y/n: ")
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
            scan = input("Source path changed, re-scan now? [y/n]")
            if scan == "y" or scan == "Y":
                self.media_scan()

    def media_scan(self):
        delete_list = []
        add_list = []
        entry_all = self.database.entry_get()
        for entry_name in entry_all:
            delete_list = []
            add_list = []
            print(f"\nScanning {entry_name}")
            _, source_path, link_path = self.database.path_get(entry_name=entry_name)

            # delete
            media_data = self.database.media_get_by_entry(entry_name)
            if len(media_data) != 0:
                for media_data_single in media_data:
                    media_name = media_data_single[1]
                    # delete link if source not exist
                    if not os.path.exists(os.path.join(source_path, media_name)):
                        exe_cmd(["rm", "-rf", os.path.join(link_path, media_name)])
                        self._media_del(entry_name=entry_name, media_name=media_name)
                        delete_list.append(media_name)
                    # delete link and source if source only contain system hidden file
                    elif self._only_macos_hidden_file(os.path.join(source_path, media_name)) == 1:
                        exe_cmd(["rm", "-rf", os.path.join(source_path, media_name)])
                        exe_cmd(["rm", "-rf", os.path.join(link_path, media_name)])
                        self._media_del(entry_name=entry_name, media_name=media_name)
                        delete_list.append(media_name)
            if len(delete_list) == 0:
                print("Deleted: nothing")
            else:
                print(f"Deleted: {delete_list}")

            # add
            media_name_all = os.listdir(source_path)

            # sort
            media_name_all_sort = []
            for media_name in media_name_all:
                media_name_all_sort.append(os.path.join(source_path, media_name))
            media_name_all_sort.sort(key=os.path.getctime)
            media_name_all = []
            for media_name in media_name_all_sort:
                media_name_all.append(media_name.replace(source_path + "/", ""))

            for media_name in media_name_all:
                if not (media_name == ".DS_Store" or media_name[:2] == "._"):
                    if not self._check_exist(entry_name=entry_name, media_name=media_name):
                        self._media_add(entry_name=entry_name, new_media_name=media_name)
                        add_list.append(media_name)
            if len(add_list) == 0:
                print("Added: nothing")
            else:
                print(f"Added: {add_list}")
        return delete_list, add_list

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
        confirm = input("Confirm? y/n: ")
        if confirm == "y" or confirm == "Y":
            self._media_del(entry_name=entry_name, media_name=media_name)

    def background_run(self):
        delete_list, add_list = self.media_scan()
        self._wecom_msg(", ".join(delete_list) + "deleted")
        self._wecom_msg(", ".join(add_list) + "added")

    def commit(self):
        self.database.commit()

    def close(self):
        self.database.close()


if __name__ == "__main__":
    ptmm = PTMM()
    try:
        argv = str(sys.argv[1])
    except IndexError:
        print("0\t-h     --help\n"
              "1\t-l     --list-media\n"
              "2\t-s     --scan-media\n"
              "3\t-a     --add-entry\n"
              "4\t-d     --del-entry\n"
              "5\t-e     --edit-entry\n"
              "6\t-lp    --list-path\n"
              "7\t-dm    --del-media-manually\n")
        argv = input("Please select from menu: ")
        if argv == "":
            exit(0)
    if argv == "-h" or argv == "--help" or argv == "0":
        print("0\t-h     --help\n"
              "1\t-l     --list-media\n"
              "2\t-s     --scan-media\n"
              "3\t-a     --add-entry\n"
              "4\t-d     --del-entry\n"
              "5\t-e     --edit-entry\n"
              "6\t-lp    --list-path\n"
              "7\t-dm    --del-media-manually\n")
    elif argv == "-l" or argv == "--list-media" or argv == "1":
        ptmm.list_media_all()
    elif argv == "-s" or argv == "--scan-media" or argv == "2":
        ptmm.media_scan()
    elif argv == "-a" or argv == "--add-entry" or argv == "3":
        ptmm.entry_add()
    elif argv == "-d" or argv == "--del-entry" or argv == "4":
        ptmm.entry_del()
    elif argv == "-e" or argv == "--edit-entry" or argv == "5":
        ptmm.entry_edit()
    elif argv == "-lp" or argv == "--list-path" or argv == "6":
        ptmm.list_path_all()
    elif argv == "-dm" or argv == "--del-media-manually" or argv == "7":
        ptmm.media_del_manually()
    elif argv == "-b":
        ptmm.background_run()
    else:
        print("use -h or --help for help")

    ptmm.commit()
    ptmm.close()
