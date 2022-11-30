import sqlite3

def sqlinit():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS "Files" ("name" TEXT, "date" TEXT, "size" TEXT,"share" INTEGER,"sharedate" TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS "ShortUrls" ("url" TEXT, "file" TEXT)')
    con.commit()
    con.close()

if __name__ == "__main__":
    sqlinit()