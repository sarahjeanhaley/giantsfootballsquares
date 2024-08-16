import random
import sqlite3

DATABASE = 'database.db'
def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

conn = get_db()
cursor = conn.cursor()

# Fetch X axis and Y axis numbers as individual integers
cursor.execute('''SELECT y_axis FROM weeks WHERE season_id = 2 AND week_id = 2''')
y_axis = cursor.fetchone()

cursor.execute('''SELECT x_axis FROM weeks WHERE season_id = 2 AND week_id = 2''')
x_axis = cursor.fetchone()
    
y_axis_export_tuple = y_axis[0]
y_axis_string=str(y_axis_export_tuple)
y_axis_list = [int(char) for char in y_axis_string]

x_axis_export_tuple = x_axis[0]
x_axis_string=str(x_axis_export_tuple)
x_axis_list = [int(char) for char in x_axis_string]
 
