#want to take each week and display the board for the users
#want to them figure out who the winner is, and the touching winners
#need to figure out how to do this for each week of data
#calculate their prize money, then store the winners in a new SQL table

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

#Retrieve giants scores for 2023
cursor.execute('SELECT weekNum, giantsScore, opponetScore from giants2023')
giantsResults = cursor.fetchall()

# Retrieve the user data
cursor.execute('SELECT id, xloc, yloc FROM users')
userSelectedRows = cursor.fetchall()

# Retrieve the weekly numbers for week 1
cursor.execute('SELECT listX, listY FROM board WHERE weekNum = 1')
weeklyNumbers = cursor.fetchone()
listX = [int(x) for x in weeklyNumbers[0].split(',')]  # Convert string to list of integers
listY = [int(y) for y in weeklyNumbers[1].split(',')]  # Convert string to list of integers

# Close the database connection
conn.close()

# Initialize a 10x10 grid with empty values
displayGrid = [['' for _ in range(10)] for _ in range(10)]

# Populate the grid with the user IDs
for row in userSelectedRows:
    id, xloc, yloc = row
    displayGrid[yloc][xloc] = id

# Print the grid with weekly numbers as headers
print_grid(displayGrid, listX, listY)

#Now need to show who the winner is for this week
print(giantsResults)
