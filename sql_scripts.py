
import psycopg2

DATABASE_URL = 'postgresql://uchhf1qoegiojq:p439a8000da39297b69db023b6195f279ee5740b495255951979d5b929debb1c8@c3gtj1dt5vh48j.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcn9ih1ds3smg8'
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn
conn = get_db()
cursor = conn.cursor()

# # Example grid data (placeholders)
# x_values = [9, 0, 1, 3, 8, 6, 5, 4, 2, 7]
# y_values = [0, 2, 9, 3, 7, 4, 1, 6, 8, 5]

# # Winning scores
# winning_x = 2
# winning_y = 1

# # Determine actual row and column based on the placeholder values
# actual_x2 = x_values.index(winning_x)
# actual_y2 = y_values.index(winning_y)

# # Calculate the 1-based index number
# index_number1 = actual_y2 * 10 + (actual_x2 + 1)

# print(f"The index number is {index_number1}.")
#############################################################
### Get the week data
cursor.execute("SELECT giants, opponent, x_axis, y_axis FROM weeks WHERE week_id = 2")
week_data = cursor.fetchone()

giants_x = week_data[0]
opponent_y = week_data[1]
all_x_values = week_data[2]
all_y_values = week_data[3]

x_values = [int(char) for char in all_x_values]
y_values = [int(char) for char in all_y_values]

print(giants_x)
print(opponent_y)

print(x_values)
print(y_values)

# Determine actual row and column based on the placeholder values
actual_x = x_values.index(giants_x)
actual_y = y_values.index(opponent_y)

print(actual_x)
print(actual_y)

# Calculate the 1-based index number
index_number = actual_y * 10 + (actual_x + 1)
print(index_number)

 
