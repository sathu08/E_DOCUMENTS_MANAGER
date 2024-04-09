import datetime
import secrets
import socket
import sqlite3
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, UserMixin
import os
import time
import threading

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
database = 'EDoc_Mang.db'
current_login_page = ''
create_depart_location = ''
delete_depart_location = ''
create_line_location = ''
delete_line_location = ''
depart_path = ''
line_path = ''
create_branch_location = ''
delete_branch_location = ''
branch_path = ''
file_full_location = ''
station_path = ''
delete_station_location = ''
create_station_location = ''
login_type = False


def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "Failed to retrieve local IP address"


def time_counter():
    global login_type
    # 300 s is 10 m
    seconds = 2
    while seconds > 0:
        time.sleep(1)
        seconds -= 1
    login_type = False


def start_time_counter():
    thread = threading.Thread(target=time_counter)
    thread.daemon = True
    thread.start()


def read_depart_db(table):
    conn = sqlite3.connect(database)
    conn.cursor()
    data = conn.execute('SELECT Depart_name FROM "{}"'.format(table)).fetchall()
    conn.close()
    unique_words = set(word for row in data for word in row[0].split())
    word = [word for word in sorted(unique_words)]
    return word


def read_line_db(table):
    conn = sqlite3.connect(database)
    conn.cursor()
    data = conn.execute('SELECT line_name FROM "{}"'.format(table)).fetchall()
    conn.close()
    expected_value = [item[0] for item in data]
    return expected_value


def read_branch_db(table):
    conn = sqlite3.connect(database)
    conn.cursor()
    data = conn.execute('SELECT line_name FROM "{}"'.format(table)).fetchall()
    conn.close()
    unique_words = set(word for row in data for word in row[0].split())
    word = [word for word in sorted(unique_words)]
    return word


def read_station_db(table, line_name):
    conn = sqlite3.connect(database)
    conn = conn.cursor()
    rows = conn.execute('SELECT Station FROM "{}" WHERE line_name=?'.format(table), (line_name,)).fetchall()
    conn.connection.commit()
    conn.close()
    expected_value = [item[0] for item in rows]
    return expected_value


def create_depart_folder(create_table_location, target_line):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO "{create_table_location}" (Depart_name) VALUES (?)',
                   (target_line,))
    constant_value = cursor.execute('SELECT line_name FROM demo_values').fetchone()
    cursor.execute('CREATE TABLE IF NOT EXISTS "{}" (line_name TEXT)'.format(target_line))
    conn.commit()
    conn.close()
    os.makedirs("static/" + target_line, exist_ok=True)
    create_line_folder(target_line, constant_value[0])


def create_line_folder(create_table_location, target_line):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    constant_value = cursor.execute('SELECT line_name FROM demo_values').fetchone()
    stations = read_station_db("demo_values", constant_value[0])
    cursor.execute(f'INSERT INTO "{create_table_location}" (line_name) VALUES (?)',
                   (target_line,))
    table_name = create_table_location + '/' + target_line
    cursor.execute('CREATE TABLE IF NOT EXISTS "{}" (line_name TEXT, Station TEXT)'.format(table_name))
    for station in stations:
        cursor.execute(f'INSERT INTO "{table_name}" (line_name, Station) VALUES (?,?)',
                       (target_line, station))
        conn.commit()
    conn.close()
    for station in stations:
        path_suffix = f"{target_line}/" if depart_path == 'FA' else ''
        os.makedirs("static/" + create_table_location + '/' + target_line + '/' + path_suffix + station, exist_ok=True)


def create_folder(create_table_location, target_line):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    constant_value = cursor.execute('SELECT line_name FROM demo_values').fetchone()
    stations = read_station_db("demo_values", constant_value[0])
    table_name = create_table_location
    for station in stations:
        cursor.execute(f'INSERT INTO "{table_name}" (line_name, Station) VALUES (?,?)',
                       (target_line, station))
        conn.commit()
    conn.close()


class User(UserMixin):
    def __init__(self, id):
        self.id = id

    @staticmethod
    def get(user_id):
        return User(user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/')
def login_pass():
    global login_type
    user_id = get_local_ip()
    user = User.get(user_id)
    login_user(user)
    login_type = False
    return redirect(url_for('home'))


@app.route('/create_branch', methods=['POST', 'GET'])
@login_required
def create_branch():
    if request.method == 'POST':
        create_value = request.form['create_value']
        checkbox_value = request.form.get('Checkbox')
        if create_value:
            conn = sqlite3.connect(database)
            conn = conn.cursor()
            check_value = conn.execute('SELECT line_name FROM "{}" WHERE line_name=?'.format(create_branch_location),
                                       (create_value,)).fetchall()
            conn.close()
            if check_value:
                flash(" '{}' Line is already exist in '{}'.".format(create_value, create_branch_location), 'warning')
            else:
                if checkbox_value == 'true':
                    create_folder(create_branch_location, create_value)
                    flash("Line Successfully Add in '{}' with the exist data.".format(create_branch_location),
                          'warning')
        else:
            flash("Please Enter the value ", 'warning')
    return render_template("create_branch.html", paths=(depart_path, line_path.upper()))


@app.route('/create_line', methods=['POST', 'GET'])
@login_required
def create_line():
    if request.method == 'POST':
        create_value = request.form['create_value']
        checkbox_value = request.form.get('Checkbox')
        if create_value:
            conn = sqlite3.connect(database)
            conn = conn.cursor()
            check_value = conn.execute('SELECT line_name FROM "{}" WHERE line_name=?'.format(create_line_location),
                                       (create_value,)).fetchall()
            conn.close()
            if check_value:
                flash(" '{}' Line is already exist in '{}'.".format(create_value, create_line_location), 'warning')
            else:
                if checkbox_value == 'true':
                    create_line_folder(create_line_location, create_value)
                    flash("Line Successfully Add in '{}' with the exist data.".format(create_line_location), 'warning')
        else:
            flash("Please Enter the value ", 'warning')
    return render_template("create_line.html", paths=depart_path)


@app.route('/create_station', methods=['POST', 'GET'])
@login_required
def create_station():
    if request.method == 'POST':
        create_value = request.form['create_value']
        checkbox_value = request.form.get('Checkbox')
        if create_value:
            conn = sqlite3.connect(database)
            conn = conn.cursor()
            check_value = conn.execute('SELECT line_name,Station FROM "{}" WHERE Station=?'.format(create_station_location),
                                       (create_value,)).fetchall()
            if check_value:
                flash(" '{}' Line is already exist in '{}'.".format(create_value, create_station_location), 'warning')
            else:
                if checkbox_value == 'true':
                    linename = branch_path if depart_path == 'FA' else line_path
                    conn.execute(f'INSERT INTO "{create_station_location}" (line_name, Station) VALUES (?, ?)',
                                 (linename, create_value))
                    flash("Line Successfully Add in '{}' with the exist data.".format(create_station_location),
                          'warning')
                    path_suffix = f"{line_path}/" if depart_path == 'FA' else ''
                    os.makedirs("static/" + create_station_location + '/' + path_suffix + '/' + create_value,
                                exist_ok=True)
            conn.connection.commit()
            conn.close()
        else:
            flash("Please Enter the value ", 'warning')
    line_pos = f"{line_path}/{branch_path}" if depart_path == 'FA' else f"{line_path}"
    return render_template("create_station.html", paths=(depart_path, line_pos.upper()))


@app.route('/create_depart', methods=['POST', 'GET'])
@login_required
def create_depart():
    if request.method == 'POST':
        create_value = request.form['create_value']
        checkbox_value = request.form.get('Checkbox')
        if create_value:
            conn = sqlite3.connect(database)
            conn = conn.cursor()
            check_value = conn.execute('SELECT * FROM "{}" WHERE Depart_name=?'.format(create_depart_location),
                                       (create_value,)).fetchall()
            conn.close()
            if check_value:
                flash(" '{}' Line is already exist in '{}'.".format(create_value, create_depart_location), 'warning')
            else:
                if checkbox_value == 'true':
                    create_depart_folder(create_depart_location, create_value)
                    flash("Line Successfully Add in '{}' with the exist data.".format(create_depart_location),
                          'warning')
        else:
            flash("Please Enter the value ", 'warning')
    return render_template("create_depart.html", paths="DEPARTMENT")


@app.route('/delete_line', methods=['POST', 'GET'])
@login_required
def delete_line():
    value_line = read_line_db(delete_line_location)
    if request.method == 'POST':
        row_id = request.form['id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "{}" WHERE line_name=?'.format(delete_line_location),
                       (row_id,))
        cursor.execute('DROP TABLE IF EXISTS "{}"'.format(depart_path + '/' + row_id))
        conn.commit()
        conn.close()
        flash(" '{}'line is successfully deleted."
              .format(row_id, ), 'warning')
    return render_template('delete_line.html', value=value_line, paths=depart_path)


@app.route('/delete_branch', methods=['POST', 'GET'])
@login_required
def delete_branch():
    value_line = read_branch_db(delete_branch_location)
    if request.method == 'POST':
        row_id = request.form['id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "{}" WHERE line_name=?'.format(delete_branch_location),
                       (row_id,))
        conn.commit()
        conn.close()
        flash(" '{}'line is successfully deleted."
              .format(row_id, ), 'warning')
    return render_template('delete_branch.html', value=value_line, paths=(depart_path, line_path.upper()))


@app.route('/delete_station', methods=['POST', 'GET'])
@login_required
def delete_station():
    linename = branch_path if depart_path == 'FA' else line_path
    value_station = read_station_db(delete_station_location, linename)
    if request.method == 'POST':
        row_id = request.form['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM "{}" WHERE line_name=? AND Station=?'.format(delete_station_location),
                       (linename, row_id))
        conn.commit()
        conn.close()
        flash("'{}' Station '{}' is successfully deleted."
              .format(linename, row_id, ), 'warning')
    line_pos = f"{linename}/{branch_path}" if depart_path == 'FA' else f"{linename}"
    return render_template('delete_station.html', value=value_station, paths=(depart_path, line_pos.upper()))


@app.route('/delete_depart', methods=['POST', 'GET'])
@login_required
def delete_depart():
    value_line = read_depart_db(delete_depart_location)
    if request.method == 'POST':
        row_id = request.form['id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM "{}" WHERE Depart_name=?'.format(delete_depart_location),
                       (row_id,))
        cursor.execute('DROP TABLE IF EXISTS "{}"'.format(row_id))
        conn.commit()
        conn.close()
        flash(" '{}'line is successfully deleted."
              .format(row_id, ), 'warning')
    return render_template('delete_depart.html', value=value_line, paths="DEPARTMENT")


@app.route('/login', methods=['GET', 'POST'])
@login_required
def login():
    global login_type, current_login_page
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
        if username == 'admin' and password == 'admin':
            login_type = True
            start_time_counter()
            return redirect(url_for(current_login_page))
        else:
            flash("Username or Password is incorrect", 'warning')
            return render_template('login.html')
    return render_template('login.html')


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    global current_login_page, create_depart_location, delete_depart_location, depart_path
    depart_value = read_depart_db('Department')
    current_login_page = 'home'
    if depart_value:
        create_depart_button = request.args.get('Add_depart')
        delete_depart_button = request.args.get('Delete_depart')
        value_depart_button = request.args.get('depart_value')
        if value_depart_button:
            depart_path = value_depart_button
            return redirect(url_for('line'))
        if create_depart_button:
            create_depart_location = create_depart_button
            return redirect(url_for('create_depart'))
        if delete_depart_button:
            delete_depart_location = delete_depart_button
            return redirect(url_for('delete_depart'))
    return render_template('home.html',
                           values=depart_value, buttontype=login_type)


@app.route('/line', methods=['GET', 'POST'])
@login_required
def line():
    global current_login_page, create_line_location, delete_line_location, \
        depart_path, line_path
    depart_value = read_line_db(depart_path)
    current_login_page = "line"
    if depart_value:
        create_line_button = request.args.get('Add_line')
        delete_line_button = request.args.get('Delete_line')
        value_line_button = request.args.get('line_button_value')
        if value_line_button:
            line_path = value_line_button
            return redirect(url_for('intermediate'))
        if create_line_button:
            create_line_location = create_line_button
            return redirect(url_for('create_line'))
        if delete_line_button:
            delete_line_location = delete_line_button
            return redirect(url_for('delete_line'))
    return render_template('line.html', path=depart_path,
                           values=depart_value, buttontype=login_type)


@app.route('/intermediate', methods=['GET', 'POST'])
@login_required
def intermediate():
    if depart_path == 'FA':
        return redirect(url_for('branch'))
    else:
        return redirect(url_for('station'))


@app.route('/branch', methods=['GET', 'POST'])
@login_required
def branch():
    global current_login_page, create_branch_location, delete_branch_location, \
        depart_path, line_path, branch_path
    branch_value = read_branch_db(depart_path + '/' + line_path)
    current_login_page = "branch"
    if branch_value:
        create_branch_button = request.args.get('Add_branch')
        delete_branch_button = request.args.get('Delete_branch')
        value_branch_button = request.args.get('branch_button_value')
        if value_branch_button:
            branch_path = value_branch_button
            return redirect(url_for('station'))
        if create_branch_button:
            create_branch_location = create_branch_button + '/' + line_path
            return redirect(url_for('create_branch'))
        if delete_branch_button:
            delete_branch_location = delete_branch_button + '/' + line_path
            return redirect(url_for('delete_branch'))
    return render_template('branch.html', path=depart_path,paths=(depart_path, line_path.upper()),
                           values=branch_value, buttontype=login_type)


@app.route('/station', methods=['POST', 'GET'])
@login_required
def station():
    global current_login_page, create_branch_location, delete_branch_location, \
        depart_path, line_path, branch_path, station_path, file_full_location, delete_station_location, \
        create_station_location
    current_login_page = 'station'
    path_suffix = branch_path if depart_path == 'FA' else line_path
    station_value = read_station_db(f"{depart_path}/{line_path}", path_suffix)
    if station_value:
        station_value_button = request.args.get('station_value_button')
        create_button_fa_details = request.args.get('Add_station')
        delete_button_fa_details = request.args.get('Delete_Station')
        if station_value_button:
            station_path = station_value_button
            middle_path = f"{branch_path}/" if depart_path == 'FA' else ""
            file_full_location = f"{depart_path}/{line_path}/{middle_path}{station_path}/example.pdf"
            return redirect(url_for('index'))
        if delete_button_fa_details:
            delete_station_location = delete_button_fa_details + '/' + line_path
            return redirect(url_for('delete_station'))
        if create_button_fa_details:
            create_station_location = create_button_fa_details + '/' + line_path
            return redirect(url_for('create_station'))
    line_pos = f"{line_path}/{branch_path}" if depart_path == 'FA' else f"{line_path}"
    return render_template('station.html', path=depart_path,
                           paths=(depart_path.upper(), line_pos.upper()),
                           values=station_value, buttontype=login_type)


@app.route('/index')
@login_required
def index():
    return render_template('index.html', path=(line_path, branch_path, station_path))


# View function for serving PDFs
@app.route('/view-pdf')
@login_required
def view_pdf():
    global file_full_location
    return send_from_directory('static', file_full_location)


# Error handler for 404 Not Found error
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


@app.errorhandler(TypeError)
def handle_type_error(error):
    error_message = 'Type Error: ' + str(error)
    with open('example.txt', 'a') as file:
        text = str(datetime.datetime.now()) + " " + error_message
        file.write(text + "\n")
    return render_template('type_error.html'), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
