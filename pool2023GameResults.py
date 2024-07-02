import requests
from bs4 import BeautifulSoup
import sqlite3

# URL of the Wikipedia page
url = 'https://en.wikipedia.org/wiki/2023_New_York_Giants_season'

# Send an HTTP GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the schedule section
    schedule_section = None
    headings = soup.find_all('span', class_='mw-headline')
    for heading in headings:
        if heading.text.strip() == 'Schedule':
            schedule_section = heading.parent
            break
    
    if schedule_section:
        # Find the immediate table after the schedule section
        table = schedule_section.find_next('table')
        
        if table:
            # Initialize an empty list to store table data
            table_data = []
            
            # Find all rows in the table
            rows = table.find_all('tr')
            
            # Iterate through rows and extract cell data
            for row in rows:
                # Find all cells in each row
                cells = row.find_all(['th', 'td'])
                
                # Extract text from each cell and append to table_data
                row_data = [cell.get_text(strip=True) for cell in cells]
                table_data.append(row_data)
            
        else:
            print("Table not found immediately after the schedule section.")
    else:
        print("Schedule section not found on the page.")
else:
    print(f"Error accessing URL: {url}. Status code: {response.status_code}")


giantsScores = []
dictHeader = table_data[0]

for row in table_data[1:]:
    row_dict = dict(zip(dictHeader,row))
    giantsScores.append(row_dict)

fields_to_remove = ['Record', 'Venue', 'Recap']
giantsScores = [{k: v for k, v in row.items() if k not in fields_to_remove} for row in giantsScores]

giantsScores = [row for row in giantsScores if row['Date'].lower() != 'bye']


# Edit and split the 'Result' field into 'Outcome' and 'Score'
for row in giantsScores:
    result_parts = row['Result'].split()  # Split the 'Result' field by whitespace
    row['Score'] = result_parts[0][1:] # Remaining parts as 'Score'
    del row['Result']  # Remove the original 'Result' field
    
    scoreParts = row['Score'].split('–')  # Split the 'Result' field by whitespace
    row['GiantsScore'] = scoreParts[0]  # First part of 'Result'
    row['OppponetScore'] = scoreParts[0][1:] # Remaining parts as 'Score'
    del row['Score']  # Remove the original 'Result' field


# Print or process giantsScores as needed
for row in giantsScores:
    print(row)



#Store boards in table
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS giants2023')

# Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS giants2023 (
        weekNum INTEGER PRIMARY KEY,
        date TEXT,
        opponent TEXT,
        giantsScore INTEGER,
        opponetScore INTEGER
    )
''')


for row in giantsScores:
    weekNum = row.get('Week')
    date = row.get('Date')
    Opponent = row.get('Opponent')
    giantsScore = row.get('GiantsScore')
    opponetScore = row.get('OpponetScore')

    # Insert data into the table
    cursor.execute('INSERT INTO giants2023 (weekNum, date, opponent, giantsScore, opponetScore) VALUES (?, ?, ?, ?, ?)', (weekNum, date, Opponent, giantsScore, opponetScore))


# Commit changes and close connection
conn.commit()
conn.close()

print("Data inserted successfully into SQLite database.")