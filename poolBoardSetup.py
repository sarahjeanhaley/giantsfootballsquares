# Need to set up a table
# Week ID, List of numbers for x, Lsit of numbers for Y

import sqlite3
import random

def getRandomOrderX():
    listX = list(range(0,10))
    random.shuffle(listX)
    return listX

def getRandomOrderY():
    listY = list(range(0,10))
    random.shuffle(listY)
    return listY

#list of NFL Week numbers
weekNums = list(range(1,19))

#make a dicontary to store the data
week_data = {}

for week in weekNums:
    listX = getRandomOrderX()
    listY = getRandomOrderY()
    week_data[week] = {'weekNum': week, 'listX': listX, 'listY': listY}
        

#Store boards in table
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS board')

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS board (
        weekNum INTEGER PRIMARY KEY,
        listX TEXT,
        listY TEXT
    )
''')

# Insert data into the table
for weekNum, data in week_data.items():
    listX_str = ','.join(map(str, data['listX']))
    listY_str = ','.join(map(str, data['listY']))
    cursor.execute('INSERT INTO board (weekNum, listX, listY) VALUES (?, ?, ?)', (weekNum, listX_str, listY_str))


# Commit changes and close connection
conn.commit()
conn.close()

print("Data inserted successfully into SQLite database.")