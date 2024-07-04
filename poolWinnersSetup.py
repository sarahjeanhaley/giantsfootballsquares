## Setup table for the winners of the weekly pool
## need the week number, first place winner, and touching winners
## dollar value of the winnings
## Week, User, Win Type, Amount


import sqlite3

#Store winners in table
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS winner2023')

# Create a table
cursor.execute('''
    CREATE TABLE winner2023 (
    weekNum INTEGER,
    user TEXT,
    winType TEXT,
    Amount INTEGER,
    PRIMARY KEY (weekNum, user)
    )
''')





