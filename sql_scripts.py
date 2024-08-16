import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Query to get all the grid spots data
cursor.execute("SELECT board_index, listx, listy FROM board_conversion ORDER BY board_index")
data = cursor.fetchall()

# Close the connection
conn.close()

# Define grid size
grid_size = 10

# Create an empty 2D list for the grid
grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]

# Populate the grid with data from the database
for board_index, listx, listy in data:
    # Convert 1-based indices to 0-based indices for the grid
    grid[grid_size - listy][listx - 1] = board_index

# Print the grid
for row in grid:
    print(' '.join(f'{item:2}' if item is not None else ' . ' for item in row))
