import sqlite3

DB_NAME = "meridian_port.db"

connection = sqlite3.connect(DB_NAME)

with open("schema.sql", "r") as f:
    connection.executescript(f.read())

with open("seed.sql", "r") as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Database created successfully!")
