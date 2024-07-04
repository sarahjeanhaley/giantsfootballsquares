import sqlite3

# Function to print the grid in a readable format
def print_grid(grid, week_x, week_y):
    # Print the weekly numbers at the top (week_x)
    print("    " + " ".join(str(num).ljust(3) for num in week_x))
    print("   " + "--- " * 10)

    for y, row in enumerate(grid):
        # Print the weekly number for the current row (week_y) and the grid content
        print(f"{week_y[y]} |" + "|".join(str(cell).ljust(3) for cell in row) + "|")
        print("   " + "--- " * 10)

# Connect to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Retrieve giants scores for 2023
cursor.execute('SELECT weekNum, giantsScore, opponetScore FROM giants2023')
giantsResults = cursor.fetchall()

# Retrieve the user data
cursor.execute('SELECT id, xloc, yloc FROM users')
userSelectedRows = cursor.fetchall()

# Process each week in the giantsResults
for result in giantsResults:
    week_num, giants_score, opponent_score = result
    
    # Retrieve the weekly numbers for the current week
    cursor.execute('SELECT listX, listY FROM board WHERE weekNum = ?', (week_num,))
    weeklyNumbers = cursor.fetchone()
    if weeklyNumbers is None:
        continue  # Skip if no board data for the current week
    
    listX = [int(x) for x in weeklyNumbers[0].split(',')]  # Convert string to list of integers
    listY = [int(y) for y in weeklyNumbers[1].split(',')]  # Convert string to list of integers
    
    # Initialize a 10x10 grid with empty values
    displayGrid = [['' for _ in range(10)] for _ in range(10)]
    
    # Populate the grid with the user IDs
    for row in userSelectedRows:
        id, xloc, yloc = row
        displayGrid[yloc][xloc] = id
    
    # Print the grid with weekly numbers as headers
    print_grid(displayGrid, listX, listY)
    
    # Determine the winner based on the giants_score and opponent_score
    winner_x = giants_score % 10
    winner_y = opponent_score % 10
    winner_id = displayGrid[winner_y][winner_x]
    
    if winner_id:
        # Insert the winner data into the winner2023 table
        cursor.execute(
            'INSERT INTO winner2023 (weekNum, user, winType, Amount) VALUES (?, ?, ?, ?)', 
            (week_num, winner_id, 'win', 100)  # Assuming 'winType' is 'win' and 'Amount' is 100
        )
    
    # List of relative coordinates for neighboring cells (including diagonals)
    neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for dx, dy in neighbors:
        nx, ny = winner_x + dx, winner_y + dy
        if 0 <= nx < 10 and 0 <= ny < 10:
            neighbor_id = displayGrid[ny][nx]
            if neighbor_id:
                # Insert the neighboring winner data into the winner2023 table
                cursor.execute(
                    'INSERT INTO winner2023 (weekNum, user, winType, Amount) VALUES (?, ?, ?, ?)', 
                    (week_num, neighbor_id, 'neighbor win', 50)  # Assuming 'winType' is 'neighbor win' and 'Amount' is 50
                )

# Commit the changes to the database
conn.commit()

# Close the database connection
conn.close()
