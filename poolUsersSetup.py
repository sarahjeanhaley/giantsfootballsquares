import sqlite3
import random
import names


# Function to generate 100 random coordinates on a 10x10 board
def generate_random_coordinates(board_size=10, num_names=100):
    coordinates = [(x, y) for x in range(board_size) for y in range(board_size)]
    random.shuffle(coordinates)
    return coordinates[:num_names]

#generate the 1 - 100 index for the table
indexList = list(range(1,101))

# Generate 100 random names
random_names = [names.get_full_name() for _ in range(100)]

# Generate 100 random coordinates
random_coordinates = generate_random_coordinates()

# Combine names and coordinates
name_location_pairs = list(zip(indexList, random_names, random_coordinates))

#Store participants in table
conn = sqlite3.connect('database.db')
cursor = conn.cursor()


cursor.execute('DROP TABLE IF EXISTS users')


# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        xloc INTEGER,
        yloc INTEGER
    )
''')

# Insert data into the table
for id, name, (x, y) in name_location_pairs:
    cursor.execute('INSERT INTO users (id, name, xloc, yloc) VALUES (?, ?, ?, ?)', (id, name, x, y))


# Commit changes and close connection
conn.commit()
conn.close()

print("Data inserted successfully into SQLite database.")
