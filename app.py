from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

## Require login function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to view this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


## Home page
@app.route('/')
def home():
    return render_template('index.html')

## Register users 
## Only to be shown to Admin
@app.route('/register', methods=['GET', 'POST'])
@login_required
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
@login_required
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


## Add Seasons ##
## Registered User Only
@app.route('/add_season', methods=['GET', 'POST'])
@login_required
def add_season():

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        seasonyear = request.form['seasonyear']
        seasondesc = request.form['seasondesc']
        
        
        try:
            cursor.execute("INSERT INTO seasons (season_year, season_desc) VALUES (?, ?)", (seasonyear, seasondesc))
            conn.commit()
            flash('Added season!', 'success')
            return redirect(url_for('add_season'))
        except sqlite3.IntegrityError:
            flash('Season already exists. Please choose a different one.', 'error')
        
    # Query the list of users
    cursor.execute("SELECT season_id, season_year, season_desc FROM seasons")
    seasons = cursor.fetchall()  # Fetch all rows as a list of tuples

    conn.close()
    
    return render_template('add_season.html', seasons=seasons)


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

# Initialize an empty 10x10 grid
grid_size = 10
grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
assigned_spots = {}

##Set up grid, add participants to the football squares
@app.route('/assign', methods=['GET', 'POST'])
@login_required
def assign():
    conn = get_db()
    cursor = conn.cursor()

    # Fetch the list of users from the database
    cursor.execute("SELECT part_id, first_name, last_name FROM participants")
    participants = cursor.fetchall()

    # Fetch the list of seasons
    cursor.execute("SELECT season_id, season_year, season_desc FROM seasons")
    seasons = cursor.fetchall()

    global assigned_spots
    if request.method == 'POST':
        name = request.form['name']
        selected_squares = request.form.getlist('squares')

        # Validate that exactly 5 squares are selected
        if len(selected_squares) != 5:
            flash('You must select exactly 5 squares.', 'error')
        else:
            row_counts = [int(square) // grid_size for square in selected_squares]
            middle_rows = [2, 3, 6, 7]

            # Validate that two squares are in the third, fourth, seventh, or eighth row
            middle_row_count = sum(1 for row in row_counts if row in middle_rows)
            if middle_row_count < 2:
                flash('At least two squares must be in rows 3, 4, 7, or 8.', 'error')
            else:
                # Assign the squares to the user
                for square in selected_squares:
                    assigned_spots[int(square)] = name
                flash('Squares assigned successfully!', 'success')
                return redirect(url_for('assign'))

    return render_template('assign.html', grid=grid, assigned_spots=assigned_spots, participants=participants, seasons=seasons)

##Logging out of applications
@app.route('/logout')
def logout():
    # Clear the session data, logging the user out
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
