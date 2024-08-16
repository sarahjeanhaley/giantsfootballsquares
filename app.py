from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import sqlite3
import random
import sqlitecloud
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key


##############################################################################
#######     **Not a Page**    Database connection - moving to sqlite in cloud for production
##############################################################################
DATABASE = 'database.db'
def get_db():
    conn = sqlite3.connect(DATABASE)
    #conn = sqlitecloud.connect("sqlitecloud://con7fzjcsk.sqlite.cloud:8860/database.db?apikey=nMQ31rYJ8SnQifqjx8bKRfazMf9d5GCeGUQ7VsaZCYM")
    return conn


##############################################################################
#######     **Not a Page**    Require login function
##############################################################################
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to view this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


##############################################################################
#######     Home Page
##############################################################################
@app.route('/')
def home():
    return render_template('index.html')

##############################################################################
#######     Register new users for using backend of application
##############################################################################
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

    conn = get_db()
    cursor = conn.cursor()   

    # Fetch all current users
    cursor.execute("SELECT username FROM app_user")
    users = cursor.fetchall()
    conn.close()

    return render_template('register.html', users=users)


##############################################################################
#######     Add new participants to the application
##############################################################################
@app.route('/add_part', methods=['GET', 'POST'])
@login_required
def add_part():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        
        try:
            cursor.execute("INSERT INTO participants (name) VALUES (?)", (name,))
            conn.commit()
            flash('Added participant!', 'success')
        except sqlite3.IntegrityError:
            flash('Participant already exists. Please choose a different one.', 'error')

        return redirect(url_for('add_part'))
    
    # Query the list of participants
    cursor.execute("SELECT part_id, name FROM participants")
    participants = cursor.fetchall()

    participant_count = len(participants)

    conn.close()

    return render_template('add_part.html', participants=participants, participant_count=participant_count)

##############################################################################
#######     Edit participant - Sub of Add Part
##############################################################################
@app.route('/edit_part/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_name = request.form['name']
        
        try:
            cursor.execute("UPDATE participants SET name = ? WHERE part_id = ?", (new_name, part_id))
            conn.commit()
            flash('Participant updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating participant: {str(e)}', 'error')
        return redirect(url_for('add_part'))

    # Fetch the current participant details
    cursor.execute("SELECT name FROM participants WHERE part_id = ?", (part_id,))
    participant = cursor.fetchone()

    conn.close()

    return render_template('edit_part.html', participant=participant, part_id=part_id)

##############################################################################
#######     delete participant - Sub of Add Part
##############################################################################
@app.route('/delete_part/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM participants WHERE part_id = ?", (part_id,))
        conn.commit()
        flash('Participant deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting participant: {str(e)}', 'error')
    
    conn.close()

    return redirect(url_for('add_part'))


##############################################################################
#######     Manage seasons (Add, assign users to squares)
##############################################################################
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


##############################################################################
#######     Login
##############################################################################
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



##############################################################################
#######     ** not a page ** Function to display weekly grid data
##############################################################################
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


##############################################################################
#######     Display weekly grid
##############################################################################
@app.route('/week/<int:week_num>')
def show_week(week_num):
    list_x, list_y, display_grid, giants_results = fetch_weekly_data(week_num)
    return render_template('grid.html', week_x=list_x, week_y=list_y, grid=display_grid, giants_results=giants_results)


##############################################################################
#######     Assign participants to the grid, by the season
##############################################################################

# Initialize an empty 10x10 grid
grid_size = 10
grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
assigned_spots = {}

@app.route('/assign/<int:season_id>', methods=['GET', 'POST'])
@login_required
def assign(season_id):
    conn = get_db()
    cursor = conn.cursor()

    grid_size = 10  # Assuming a 10x10 grid

    # Fetch the list of users from the database
    cursor.execute("SELECT part_id, name FROM participants")
    participants = cursor.fetchall()

    # Fetch the specific season details
    cursor.execute('SELECT season_id, season_year, season_desc FROM seasons WHERE season_id = ?', (season_id,))
    seasons = cursor.fetchone()

    # Fetch already assigned spots for this season, including the participant name
    cursor.execute('''SELECT grid_index, participants.name 
                  FROM grid_spots 
                  JOIN participants ON grid_spots.user_part_id = participants.part_id 
                  WHERE seasonID = ?''', (season_id,))
    assigned_spots = {row[0]: row[1] for row in cursor.fetchall()}  # Convert to dictionary



    if request.method == 'POST':
        user_part_id = request.form['user_part_id']
        selected_squares = request.form.getlist('squares[]')

        # Validate that exactly 5 squares are selected
        if len(selected_squares) != 5:
            flash('You must select exactly 5 squares.', 'error')
        else:
            row_counts = [int(square) // grid_size for square in selected_squares]
            middle_rows = [2, 3, 6, 7]  # 0-based index for rows 3, 4, 7, and 8
        
            # Count the number of squares in the middle rows
            middle_row_count = sum(1 for row in row_counts if row in middle_rows)
        
            # Validate that at least two squares are in the middle rows (3, 4, 7, 8)
            if middle_row_count < 2:
                flash('At least two squares must be in rows 3, 4, 7, or 8.', 'error')
            else:
                # Save the selected squares to the database
                try:
                    for square in selected_squares:
                        cursor.execute(
                            "INSERT INTO grid_spots (seasonID, user_part_id, grid_index) VALUES (?, ?, ?)",
                            (season_id, user_part_id, int(square))
                        )
                    conn.commit()
                    flash('Squares assigned successfully!', 'success')
                    return redirect(url_for('assign', season_id=season_id))
                except Exception as e:
                    flash(f'Error assigning squares: {str(e)}', 'error')
    
    return render_template('assign.html', grid_size=grid_size, assigned_spots=assigned_spots, participants=participants, seasons=seasons)


##############################################################################
#######     Set up weekly grid 
##############################################################################

@app.route('/setup_week/<int:season_id>', methods=['GET', 'POST'])
@login_required
def setup_week(season_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        week_number = request.form['week_number']
        game_date = request.form['game_date']
        
        options = ['0','1','2','3','4','5','6','7','8','9']
        random.shuffle(options)
        x_string = ''.join(options)  
        random.shuffle(options)
        y_string = ''.join(options) 

        try:
            # Insert the week details and random numbers into the table
            cursor.execute(
            "INSERT INTO weeks (season_id, season_week_number, game_date, x_axis, y_axis) VALUES (?, ?, ?, ?, ?)",
            (season_id, week_number, game_date, x_string, y_string)
                    )
            conn.commit()
            flash('Week setup successfully!', 'success')
            return redirect(url_for('setup_week', season_id=season_id))
        except Exception as e:
            flash(f'Error setting up week: {str(e)}', 'error')
    
    # Fetch the season name based on the season_id
    cursor.execute("SELECT season_desc FROM seasons WHERE season_id = ?", (season_id,))
    season = cursor.fetchone()
    
    if season:
        season_desc = season[0]
    else:
        flash('Season not found.', 'error')
        return redirect(url_for('some_other_route'))

    # Fetch the list of weeks for the selected season
    cursor.execute("SELECT week_id, season_week_number, game_date name FROM weeks where season_id = ?", (season_id,))
    weeks_info = cursor.fetchall()

    conn.close()
    
    return render_template('setup_week.html', season_id=season_id, season_desc=season_desc, weeks_info=weeks_info)

##############################################################################
#######     View Week
##############################################################################
@app.route('/view_week/<int:season_id>/<int:week_id>')
def view_week(season_id, week_id):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch X axis and Y axis numbers as individual integers
    cursor.execute('''SELECT y_axis FROM weeks WHERE season_id = ? AND week_id = ?''', (season_id, week_id))
    y_axis = cursor.fetchone()

    cursor.execute('''SELECT x_axis FROM weeks WHERE season_id = ? AND week_id = ?''', (season_id, week_id))
    x_axis = cursor.fetchone()
    
    if x_axis is None:
        flash("No week data found for the selected season and week.", "error")
        return redirect(url_for('some_other_route'))  # Redirect to an appropriate route
    if y_axis is None:
        flash("No week data found for the selected season and week.", "error")
        return redirect(url_for('some_other_route'))  # Redirect to an appropriate route

    y_axis_export_tuple = y_axis[0]
    y_axis_string=str(y_axis_export_tuple)
    y_axis = [int(char) for char in y_axis_string]

    x_axis_export_tuple = x_axis[0]
    x_axis_string=str(x_axis_export_tuple)
    x_axis = [int(char) for char in x_axis_string]

    # Fetch the participants' grid positions
    cursor.execute('''SELECT name, listx, listy
                      FROM participants 
                      LEFT JOIN grid_spots ON part_id = user_part_id
                      LEFT JOIN board_conversion ON board_index = grid_index
                      WHERE seasonid = ?''', (season_id,))
    grid_data = cursor.fetchall()

    # Close the connection
    conn.close()

    # Organize data into a dictionary for easy lookup
    grid_dict = {(listx, listy): name for name, listx, listy in grid_data}

    return render_template('view_week.html', x_axis=x_axis, y_axis=y_axis, grid_dict=grid_dict, week_id=week_id, season_id=season_id)


##############################################################################
#######     Log Out
##############################################################################
@app.route('/logout')
def logout():
    # Clear the session data, logging the user out
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
