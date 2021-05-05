
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import requests, json, os
from ibm_watson import VisualRecognitionV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import MySQLdb.cursors
import re




app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'deek1234'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config["MYSQL_PORT"] = 3306
app.config['MYSQL_USER'] = '4of66GAB8K'
app.config['MYSQL_PASSWORD'] = 'ZCre1Gh7Pu'
app.config['MYSQL_DB'] = '4of66GAB8K'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/')
def home():
   return render_template('home.html')

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('submission'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)
# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/submission')
def submission():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('submission.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/pythonlogin/submission/display', methods = ["POST", "GET"])
def display():
    if request.method == "POST":
        image = request.files["food"] 
        authenticator = IAMAuthenticator('2A6BucKErMHbNpKGwdyGMBTsAZYxRYmm8Rxr0chzTvfm')
        visual_recognition = VisualRecognitionV3(
        version='2018-03-19',
        authenticator=authenticator)
        visual_recognition.set_service_url('https://api.us-south.visual-recognition.watson.cloud.ibm.com/instances/80c78105-880f-4bb7-b79c-93764795ee73') 
        classes = visual_recognition.classify(images_filename=image.filename, 
                                              images_file=image ,classifier_ids='food').get_result() 
        data=json.loads(json.dumps(classes,indent=4))

        foodName=data["images"][0]['classifiers'][0]["classes"][0]["class"]
        nutrients = {}
        USDAapiKey = '9f8yGs19GGo5ExPpBj7fqjKOFlXXxkJdMyJKXwG3'
        response = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search?api_key={}&query={}&requireAllWords={}'.format(USDAapiKey, foodName, True))

        data = json.loads(response.text)
        concepts = data['foods'][0]['foodNutrients']
        arr = ["Sugars","Energy", "Vitamin A","Vitamin D","Vitamin B", "Vitamin C", "Protein","Fiber","Iron","Magnesium",
               "Phosphorus","Cholestrol","Carbohydrate","Total lipid (fat)", "Sodium", "Calcium",]
        for x in concepts:
            if x['nutrientName'].split(',')[0] in arr:
                if(x['nutrientName'].split(',')[0]=="Total lipid (fat)"):
                    nutrients['Fat'] = str(x['value'])+" " + x['unitName']
                else:    
                    nutrients[x['nutrientName'].split(',')[0]] = str(x['value'])+" " +x['unitName']
                    
        return render_template('display.html', x = foodName, data = nutrients, account = session['username'])
    else:
        return render_template('submission.html')



if __name__=='__main__':
    app.run(debug=True)