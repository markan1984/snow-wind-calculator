import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

# create a sqlite3 connection to SQL database
connection = sqlite3.connect('database.db')
cur = connection.cursor()

username = "markan"
password = "fucker"

# Query database for username
row = cur.execute("SELECT * FROM users WHERE username = ?", (username,))
row = cur.fetchone()

print(row)

# Ensure username exists and password is correct
if row == None or not check_password_hash(rows[2], password):
    print("Неверное имя и/или пароль")
    quit()

# Remember which user has logged in
print(f"user_id:{row[0]}")


