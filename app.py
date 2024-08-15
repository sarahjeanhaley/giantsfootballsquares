from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

## Home page
@app.route('/')
def home():
    return render_template('index.html')

## Register users 
## Only to be shown to Admin
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO app_user (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
        
        conn.close()
    
    return render_template('register.html')

## Add Participants to Table ##
## Registered User Only
@app.route('/add_part', methods=['GET', 'POST'])
def add_part():

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        first_name = request.form['First_Name']
        last_name = request.form['Last_Name']
        
        
        try:
            cursor.execute("INSERT INTO participants (first_name, last_name) VALUES (?, ?)", (first_name, last_name))
            conn.commit()
            flash('Added participant!', 'success')
            return redirect(url_for('add_part'))
        except sqlite3.IntegrityError:
            flash('Participant already exists. Please choose a different one.', 'error')
        
    # Query the list of users
    cursor.execute("SELECT part_id, first_name, last_name FROM participants")
    participants = cursor.fetchall()  # Fetch all rows as a list of tuples

    conn.close()
    
    return render_template('add_part.html', participants=participants)


## Login as Registered User ##
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM app_user WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]  # Set the session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
        
        conn.close()
    
    return render_template('login.html')




##Function used to display weekly data grid
def fetch_weekly_data(week_num):
    conn = get_db()
    cursor = conn.cursor()

    # Retrieve giants scores for the specified week
    cursor.execute('SELECT weekNum, giantsScore, opponetScore FROM giants2023 WHERE weekNum = ?', (week_num,))
    giants_results = cursor.fetchone()

    # Retrieve user data
    cursor.execute('SELECT id, xloc, yloc FROM users')
    user_selected_rows = cursor.fetchall()

    # Retrieve weekly numbers
    cursor.execute('SELECT listX, listY FROM board WHERE weekNum = ?', (week_num,))
    weekly_numbers = cursor.fetchone()
    list_x = [int(x) for x in weekly_numbers[0].split(',')]  # Convert string to list of integers
    list_y = [int(y) for y in weekly_numbers[1].split(',')]  # Convert string to list of integers

    # Initialize a 10x10 grid with empty values
    display_grid = [['' for _ in range(10)] for _ in range(10)]

    # Populate the grid with the user IDs
    for row in user_selected_rows:
        id, xloc, yloc = row
        display_grid[yloc][xloc] = id

    conn.close()

    return list_x, list_y, display_grid, giants_results

## Display Weekly Data ##
@app.route('/week/<int:week_num>')
def show_week(week_num):
    list_x, list_y, display_grid, giants_results = fetch_weekly_data(week_num)
    return render_template('grid.html', week_x=list_x, week_y=list_y, grid=display_grid, giants_results=giants_results)

##Set up grid, add participants to the football squares
@app.route('/setupgrid')
def setupgrid():
    return render_template('set_up_grid.html')

##Logging out of applications
@app.route('/logout')
def logout():
    # Clear the session data, logging the user out
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
