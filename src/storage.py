# -*- coding: utf-8 -*-
import sqlite3

import cfg


def handle_user(user):
    cursor.execute("SELECT * FROM " + cfg.CHANNEL + " WHERE user_name='" + user + "'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO " + cfg.CHANNEL + " VALUES (?, ?)", (user, 0))
        database.commit()


def get_user_permission(user):
    cursor.execute("SELECT user_permission FROM " + cfg.CHANNEL + " WHERE user_name='" + user + "'")
    result = cursor.fetchone()
    if result is None:
        handle_user(user)
        return 0
    else:
        perm = result[0]
        if isinstance(perm, int):
            return perm
        else:
            update_user_permission(user, 0)
            return 0


def update_user_permission(user, permission_lvl):
    cursor.execute("UPDATE " + cfg.CHANNEL + " SET user_permission=? WHERE user_name=?", (permission_lvl, user))
    database.commit()


database = sqlite3.connect(cfg.DATABASE_PATH)
cursor = database.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + cfg.CHANNEL + "'")
if cursor.fetchone() is None:
    cursor.execute("CREATE TABLE " + cfg.CHANNEL + " (user_name TEXT, user_permission INTEGER, PRIMARY KEY (user_name))")
    database.commit()