import sqlite3
import hashlib

def sqlinit():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS "Files" ("name" TEXT, "date" TEXT, "size" TEXT,"share" INTEGER,"sharedate" TEXT, "downloads" INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS "ShortUrls" ("url" TEXT, "file" TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS "Users" ("username" TEXT, "password" TEXT)')
    #if no users exist, create admin user
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()
    if not users:
        #create admin user password = "admin"
        username = 'admin'
        password = "admin"
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        cur.execute("INSERT INTO Users VALUES (?, ?)", (username, password_hash))
    con.commit()
    con.close()

if __name__ == "__main__":
    sqlinit()