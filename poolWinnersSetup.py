## Setup table for the winners of the weekly pool
## need the week number, first place winner, and touching winners
## dollar value of the winnings
## Week, User, Win Type, Amount


import sqlite3

#Store winners in table
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS winners2023')

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS winner2023 (
        weekNum INTEGER PRIMARY KEY,
        user INTEGER,
        winType TEXT,
        Amount INTEGER
    )
''')