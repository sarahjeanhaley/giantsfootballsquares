from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import sqlite3
import random
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use environment variables for secret key


##############################################################################
#######     **Not a Page**    Database connection 
##############################################################################
DATABASE_URL = 'postgresql://uchhf1qoegiojq:p439a8000da39297b69db023b6195f279ee5740b495255951979d5b929debb1c8@c3gtj1dt5vh48j.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcn9ih1ds3smg8'
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

## local sqlitedb info, commented out - moving to postgres on heroku
# DATABASE = 'database.db'
#def get_db():
#     conn = sqlite3.connect(DATABASE)
#     return conn

##############################################################################
#######     **Not a Page**    Require login function
##############################################################################
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
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
#######     Login   ** Updated to postgres
##############################################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trim(username), trim(password) FROM app_user WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            db_username, db_password = user
            if check_password_hash(db_password, password):
                # Assuming you have a way to uniquely identify users (e.g., session ID or similar)
                session['username'] = db_username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        else:
            flash('User not found. Please try again.', 'error')

    return render_template('login.html')

##############################################################################
#######     Register new users for using backend of application   ** Updated to postgres
##############################################################################
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')


        try:
            cursor.execute("INSERT INTO app_user (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('home'))
        except psycopg2.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')

    # Query the list of users
    cursor.execute("SELECT trim(username) FROM app_user")
    user_list = cursor.fetchall()

    conn.close()

    return render_template('register.html', user_list=user_list)

##############################################################################
#######     Edit User Password
##############################################################################
@app.route('/edit_user/<username>', methods=['GET', 'POST'])
@login_required
def edit_user(username):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            cursor.execute("UPDATE app_user SET password = %s WHERE username = %s", (hashed_password, username))
            conn.commit()
            flash('User updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('register'))

    conn.close()
    username= username.strip()
    return render_template('edit_user.html', username=username)
 
##############################################################################
#######     Add new participants to the application ** Updated to postgres
##############################################################################
@app.route('/add_part', methods=['GET', 'POST'])
@login_required
def add_part():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        
        try:
            cursor.execute("INSERT INTO participants (name) VALUES (%s)", (name,))
            conn.commit()
            flash('Added participant!', 'success')
        except sqlite3.IntegrityError:
            flash('Participant already exists. Please choose a different one.', 'error')
        return redirect(url_for('add_part'))
    
    # Query the list of participants
    cursor.execute("SELECT part_id, trim(name) FROM participants")
    participants = cursor.fetchall()

    participant_count = len(participants)

    conn.close()

    return render_template('add_part.html', participants=participants, participant_count=participant_count)

##############################################################################
#######     Edit participant - Sub of Add Part ** Updated to postgres
##############################################################################
@app.route('/edit_part/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_name = request.form['name']
        
        try:
            cursor.execute("UPDATE participants SET name = %s WHERE part_id = %s", (new_name, part_id))
            conn.commit()
            flash('Participant updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating participant: {str(e)}', 'error')
        return redirect(url_for('add_part'))

    # Fetch the current participant details
    cursor.execute("SELECT trim(name) FROM participants WHERE part_id = %s", (part_id,))
    participant = cursor.fetchone()

    conn.close()

    return render_template('edit_part.html', participant=participant, part_id=part_id)

##############################################################################
#######     delete participant - Sub of Add Part ** Updated to postgres
##############################################################################
@app.route('/delete_part/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM participants WHERE part_id = %s", (part_id,))
        conn.commit()
        flash('Participant deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting participant: {str(e)}', 'error')
    
    conn.close()

    return redirect(url_for('add_part'))

##############################################################################
#######     Manage seasons (Add, assign users to squares) ** Updated to postgres
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
            cursor.execute("INSERT INTO seasons (season_year, season_desc) VALUES (%s, %s)", (seasonyear, seasondesc))
            conn.commit()
            flash('Added season!', 'success')
            return redirect(url_for('add_season'))
        except sqlite3.IntegrityError:
            flash('Season already exists. Please choose a different one.', 'error')
        
    # Query the list of seasons
    cursor.execute("SELECT season_id, season_year, trim(season_desc) FROM seasons")
    seasons = cursor.fetchall()  # Fetch all rows as a list of tuples

    conn.close()
    
    return render_template('add_season.html', seasons=seasons)


##############################################################################
#######     Update season
##############################################################################
@app.route('/update_season_status/<int:season_id>/<string:status>', methods=['GET', 'POST'])
@login_required
def update_season_status(season_id, status):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE seasons SET season_status = %s WHERE season_id = %s", (status, season_id))
        conn.commit()
        flash('Season status updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating season status: {e}', 'error')

    if status == 'F':
        print('finalizewd')
    elif status =='C':  
        print('complete')

    # Query the list of seasons
    cursor.execute("SELECT season_id, season_year, trim(season_desc), season_status FROM seasons")
    seasons = cursor.fetchall()  # Fetch all rows as a list of tuples

    cursor.close()
    conn.close()
    
    return render_template('add_season.html', seasons=seasons)


##############################################################################
#######     Assign participants to the grid, by the season ** Updated to postgres
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
    cursor.execute('SELECT season_id, season_year, season_desc FROM seasons WHERE season_id = %s', (season_id,))
    seasons = cursor.fetchone()

    # Fetch already assigned spots for this season, including the participant name
    cursor.execute('''SELECT grid_index, participants.name 
                  FROM grid_spots 
                  JOIN participants ON grid_spots.user_part_id = participants.part_id 
                  WHERE seasonID = %s''', (season_id,))
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
                            "INSERT INTO grid_spots (seasonID, user_part_id, grid_index) VALUES (%s, %s, %s)",
                            (season_id, user_part_id, int(square))
                        )
                    conn.commit()
                    flash('Squares assigned successfully!', 'success')
                    return redirect(url_for('assign', season_id=season_id))
                except Exception as e:
                    flash(f'Error assigning squares: {str(e)}', 'error')
    
    return render_template('assign.html', grid_size=grid_size, assigned_spots=assigned_spots, participants=participants, seasons=seasons)

##############################################################################
#######     Set up weekly grid, Manage weeks
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
            "INSERT INTO weeks (season_id, season_week_number, game_date, x_axis, y_axis) VALUES (%s, %s, %s, %s, %s)",
            (season_id, week_number, game_date, x_string, y_string)
                    )
            conn.commit()
            flash('Week setup successfully!', 'success')
            return redirect(url_for('setup_week', season_id=season_id))
        except Exception as e:
            flash(f'Error setting up week: {str(e)}', 'error')

    # Fetch the list of weeks for the selected season
    cursor.execute("SELECT week_id, season_week_number, game_date, giants, opponent, status FROM weeks where season_id = %s", (season_id,))
    weeks_info = cursor.fetchall()
    weeks_info = sorted(weeks_info, key=lambda x: x[1])

    conn.close()
    return render_template('setup_week.html', season_id=season_id, weeks_info=weeks_info)

##############################################################################
#######     View Week 
##############################################################################
@app.route('/view_week/<int:season_id>/<int:week_id>')
def view_week(season_id, week_id):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch X axis and Y axis numbers as individual integers
    cursor.execute('''SELECT y_axis FROM weeks WHERE season_id = %s AND week_id = %s''', (season_id, week_id))
    y_axis = cursor.fetchone()

    cursor.execute('''SELECT x_axis FROM weeks WHERE season_id = %s AND week_id = %s''', (season_id, week_id))
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

    #Fetch the participants' grid positions
    cursor.execute('''SELECT name, grid_index
                      FROM participants 
                      LEFT JOIN grid_spots ON part_id = user_part_id
                      WHERE seasonid = %s''', (season_id,))
    grid_data = cursor.fetchall()
    grid_dict = {index: name for name, index in grid_data}
    # Close the connection
    conn.close()

    # Organize data into a dictionary for easy lookup
    #grid_dict = {(listx, listy): name for name, listx, listy in grid_data}

    return render_template('view_week.html', x_axis=x_axis, y_axis=y_axis, grid_dict=grid_dict, week_id=week_id, season_id=season_id)

##############################################################################
#######     Enter Score (For Season - Week)  ** Updated for postgres
##############################################################################
@app.route('/enter_score/<int:season_id>/<int:week_id>', methods=['GET', 'POST'])
@login_required
def enter_score(season_id, week_id):
    conn = get_db()
    cursor = conn.cursor()

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        giants = request.form['giants']
        opponent = request.form['opponent']
        try:
            cursor.execute('''UPDATE weeks SET giants = %s, opponent = %s WHERE season_id = %s AND week_id = %s''', (giants, opponent, season_id, week_id))
            conn.commit()
            flash('Added score!', 'success')
            return redirect(url_for('setup_week', week_id=week_id, season_id=season_id))
        
        except sqlite3.IntegrityError:
            flash('Score already exists. Please choose a different one.', 'error')

    conn.close()
    
    return render_template('enter_score.html', week_id=week_id, season_id=season_id)

##############################################################################
#######     Edit Score (For Season - Week)  ** Updated for postgres
##############################################################################
@app.route('/edit_score/<int:season_id>/<int:week_id>', methods=['GET', 'POST'])
@login_required
def edit_score(season_id, week_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        giants = request.form['giants']
        opponent = request.form['opponent']
        try:
            cursor.execute('''UPDATE weeks SET giants = %s, opponent = %s WHERE season_id = %s AND week_id = %s''', (giants, opponent, season_id, week_id))
            conn.commit()
            flash('Edited score!', 'success')
            return redirect(url_for('setup_week', week_id=week_id, season_id=season_id))
        
        except sqlite3.IntegrityError:
            flash('Score already exists. Please choose a different one.', 'error')

    # Fetch the current score data
    cursor.execute("SELECT giants, opponent FROM weeks WHERE season_id = %s AND week_id = %s", (season_id, week_id,))
    score = cursor.fetchone()

    #Get week date data to display
    cursor.execute("SELECT season_week_number, game_date FROM weeks WHERE season_id = %s and week_id = %s", (season_id, week_id))
    week_data = cursor.fetchone()

    #Get the season name to display
    cursor.execute("SELECT season_desc FROM seasons WHERE season_id = %s", (season_id,))
    season_data = cursor.fetchone()

    conn.close()
    
    return render_template('edit_score.html', week_id=week_id, season_id=season_id, score=score, week_data=week_data, season_data=season_data)

##############################################################################
#######     Update week status
##############################################################################
@app.route('/update_week_status/<int:season_id>/<int:week_id>/<string:status>', methods=['GET', 'POST'])
@login_required
def update_week_status(season_id, week_id, status):
    conn = get_db()
    cursor = conn.cursor()

    if status == 'C':
        try:
            cursor.execute("UPDATE weeks SET status = 'O' WHERE status = 'C' AND week_id != %s", (week_id,))
            cursor.execute("UPDATE weeks SET status = %s WHERE week_id = %s", (status, week_id))
            conn.commit()        
            flash('Week status updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating week status: {e}', 'error')
    else:
        try:
            cursor.execute("UPDATE weeks SET status = %s WHERE week_id = %s", (status, week_id))
            conn.commit()        
            flash('Week status updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating week status: {e}', 'error')

    cursor.close()
    conn.close()
    
    return redirect(url_for('setup_week', season_id=season_id))


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
