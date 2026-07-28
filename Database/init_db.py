import sqlite3
import os

DB_NAME = "meridian_port.db"

if os.path.exists(DB_NAME):
    os.remove(DB_NAME)


connection = sqlite3.connect(DB_NAME)

with open("schema.sql", "r") as f:
    connection.executescript(f.read())

with open("seed.sql", "r") as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Database created successfully!")
