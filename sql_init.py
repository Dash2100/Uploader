import sqlite3

def sqlinit():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS "Files" ("name" TEXT, "date" TEXT, "size" TEXT,"share" INTEGER,"sharedate" TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS "ShortUrls" ("url" TEXT, "file" TEXT, "clicks" INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS "Users" ("username" TEXT, "password" TEXT)')
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()
    if not users:
        #create admin user password = "password"
        cur.execute("INSERT INTO Users VALUES (?, ?)", ('admin', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'))
    con.commit()
    con.close()

if __name__ == "__main__":
    sqlinit()