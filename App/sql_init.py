import sqlite3
import hashlib

default_password = 'admin'

def sqlinit():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS "Files" ("name" TEXT, "date" TEXT, "size" TEXT,"share" INTEGER,"sharedate" TEXT, "downloads" INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS "ShortUrls" ("url" TEXT, "file" TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS "Users" ("username" TEXT, "password" TEXT)')

    #check if admin user exists
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()
    if not users:
        cur.execute("INSERT INTO Users VALUES (?, ?)", ('admin', hashlib.sha256(default_password.encode('utf-8')).hexdigest()))
    con.commit()
    con.close()

if __name__ == "__main__":
    sqlinit()