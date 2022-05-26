import sqlite3
import datetime
import os


class MediaDB:
    def __init__(self, database_file):
        is_first_time = False
        if not os.path.exists(database_file):
            is_first_time = True
        self.con = sqlite3.connect(database=database_file, timeout=10)
        self.cur = self.con.cursor()
        if is_first_time:
            self._path_init()

    def _path_init(self):
        self.cur.execute(f"""CREATE TABLE entry_path 
                            (entry_name  TEXT PRIMARY KEY   NOT NULL,
                            source_path  TEXT               NOT NULL,
                            link_path    TEXT               NOT NULL
                            )""")

    def path_get(self, entry_name):
        """:return: list [entry_name, source_path, link_path]"""
        self.cur.execute("SELECT * FROM entry_path WHERE entry_name = ?", (entry_name,))
        return self.cur.fetchall()[0]

    def entry_create(self, entry_name, source_path, link_path):
        self.cur.execute(f"""CREATE TABLE "{entry_name}"
                            (media_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                            media_name  TEXT                NOT NULL,
                            date        TEXT                NOT NULL
                            )""")
        self.cur.execute("INSERT INTO entry_path (entry_name, source_path, link_path) VALUES (?, ?, ?)",
                         (entry_name, source_path, link_path))
        # create table has to commit
        self.commit()

    def entry_del(self, entry_name):
        self.cur.execute(f"""DROP TABLE "{entry_name}" """)
        self.cur.execute("DELETE FROM entry_path WHERE entry_name = ?", (entry_name,))

    def entry_get(self):
        entry_name_all = []
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        entry_name_all_raw = self.cur.fetchall()
        for entry_name_raw in entry_name_all_raw:
            entry_name_all.append(entry_name_raw[0])
        if "sqlite_sequence" in entry_name_all:
            entry_name_all.remove("sqlite_sequence")
        if "entry_path" in entry_name_all:
            entry_name_all.remove("entry_path")
        return entry_name_all

    def entry_edit(self, entry_name, new_entry_name="", new_source_path="", new_link_path=""):
        if new_entry_name != "":
            self.cur.execute(f"""ALTER TABLE "{entry_name}" RENAME TO "{new_entry_name}" """)
            self.cur.execute("UPDATE entry_path SET entry_name = ? WHERE entry_name = ?", (entry_name, entry_name))
        if new_source_path != "":
            self.cur.execute("UPDATE entry_path SET source_path = ? WHERE entry_name = ?",
                             (new_source_path, entry_name))
        if new_link_path != "":
            self.cur.execute("UPDATE entry_path SET link_path = ? WHERE entry_name = ?", (new_link_path, entry_name))

    def media_insert(self, entry_name, media_name):
        self.cur.execute(
            f"""INSERT INTO "{entry_name}" (media_name, date) VALUES (?, ?)""",
            (media_name, str(datetime.datetime.now())))

    def media_del(self, entry_name, media_name):
        self.cur.execute(f"""DELETE FROM "{entry_name}" WHERE media_name = ?""", (media_name,))

    def media_get_by_id(self, entry_name, media_id):
        self.cur.execute(f"""SELECT * FROM "{entry_name}" WHERE media_id = ?""", (media_id,))
        return self.cur.fetchall()[0]

    def media_get_by_entry(self, entry_name):
        self.cur.execute(f"""SELECT * FROM "{entry_name}" """)
        return self.cur.fetchall()

    def media_get_all(self):
        media_info_all = []
        entry_name_all = self.entry_get()
        for entry_name in entry_name_all:
            media_info_all.append(entry_name)
            media_info_all.append(self.media_get_by_entry(entry_name))
        return media_info_all

    def id_max_get(self, entry_name):
        self.cur.execute(f"SELECT seq FROM sqlite_sequence WHERE name = ?", (entry_name,))
        return self.cur.fetchall()[0][0]

    def commit(self):
        self.con.commit()

    def close(self):
        self.con.close()