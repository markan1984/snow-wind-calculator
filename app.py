import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



# create a sqlite3 connection to SQL database
connection = sqlite3.connect('database.db')
cur = connection.cursor()



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/snow1", methods=["GET", "POST"])
def snow():
    if request.method == "POST":

        #1 take the data value from the form
        slope = request.form.get("slope")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]

        #2 Check the data exist
        if not slope or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклон кровли либо город", 400)

        #3 Check the city data input
        cities = cur.execute("SELECT city FROM cities;")
        cities = cur.fetchall()

        cities_list=[]
        for row in cities:
            cities_list.append(row[0])

        if city not in cities_list:
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #4 Check the slope is integer or not
        try:
            slope = int(slope)
        except ValueError:
            return apology("Значение уклона должно быть целым числом", 400)
        if slope < 0 or slope > 89:
            return apology("Уклон должен быть положительным числом от 0 до 90", 400)

        #5 Check the Ce and Ct data
        try:
            Ce = float(Ce)
            Ct = float(Ct)
        except ValueError:
            return apology("Пожалуйста не меняйте стандартные значения! :(", 400)
        if Ce != 0.8:
            if Ce != 1:
                return apology("Пожалуйста не меняйте стандартные значения! :(", 400)
        if Ct != 0.8:
            if Ct != 1:
                return apology("Пожалуйста не меняйте стандартные значения! :(", 400)


        #6 Get the snow area data and level data (if the city is already correct)
        snow_area = cur.execute("SELECT snow FROM cities WHERE city = ?", (city,))
        snow_area = cur.fetchone()[0]
        level = cur.execute("SELECT level FROM cities WHERE city = ?", (city,))
        level = int(cur.fetchone()[0])

        #7 Check the current_level input
        print(current_level)
        if current_level != "":
            try:
                current_level = int(current_level)
            except ValueError:
                return apology("Значение отметки местности должно быть целым числом", 400)
            if current_level < 100 or current_level > 320:
                return apology("Значение отметки местности должно быть положительным числом от 100 до 320", 400)
            level = current_level

        #8 get the roof_check data from form
        roof_check = request.form.get("roof_check")

        #9 Calculating of mui
        if slope <= 30:
            mui = 0.8
        elif slope > 30 and slope < 60:
            if roof_check == None:
                mui = 0.8 * (60 - slope) / 30
            else:
                mui = 0.8
        else:
            mui = 0

        #10 Calculating of Sk
        if snow_area == "1а":
            Sk = int(1350)
            Sk_formula = ""
        elif snow_area == "1б":
            Sk = int((1.35 + 2.2 * (level - 155) / 100)*1000)
            Sk_formula = "1.35+2.2∙(A-155)/100="
        elif snow_area == "1в":
            Sk = int((1.35 + 0.38 * (level - 140) / 100)*1000)
            Sk_formula = "1.35+0.38∙(A-140)/100="
        elif snow_area == "2а":
            Sk = int((1.45 + 0.6 * (level - 125) / 100)*1000)
            Sk_formula = "1.45+0.6∙(A-125)/100="
        elif snow_area == "2б":
            Sk = int((1.45 + 0.6 * (level - 150) / 100)*1000)
            Sk_formula = "1.45+0.6∙(A-150)/100="
        elif snow_area == "2в":
            Sk = int((1.45 + 0.6 * (level - 210) / 100)*1000)
            Sk_formula = "1.45+0.6∙(A-210)/100="
            if Sk < 1000:
                Sk = 1000
        elif snow_area == "3":
            Sk = int(1550)
        else:
            return apology("Неверное значение снегового района (проверьте базу данных)", 500)

        return render_template("snow1-done.html",
            slope = slope,
            Ce = Ce,
            Ct = Ct,
            city = city,
            mui = mui,
            level = level,
            snow_area = snow_area,
            roof_check = roof_check,
            Sk = float(Sk/1000),
            Sk_formula = Sk_formula,
            snow_load = round(float(Sk / 1000) * Ce * Ct * mui, 2))


    # User reached route via GET
    else:
        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow1.html", cities=cities)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        row = cur.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        row = cur.fetchone()

        # Ensure username exists and password is correct
        if row == None or not check_password_hash(row[2], request.form.get("password")):
            return apology("Неверное имя и/или пароль", 400)

        # Remember which user has logged in
        session["user_id"] = row[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Необходимо указать имя", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Необходимо указать пароль", 400)

        # Ensure password and confirmation do not match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Вводимый пароль и пароль подтверждения не совпадают", 400)

        # Query database for username
        rows1 = cur.execute("SELECT username FROM users WHERE username = ?", (request.form.get("username"),))
        rows1 = cur.fetchall()

        # Ensure username do not exists
        if len(rows1) != 0:
            return apology("Пользователь с таким именем уже существует", 400)

        # Add the registration data into the database
        cur.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (request.form.get("username"),
        generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)))
        connection.commit()

        # Register the user
        user = cur.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        user = cur.fetchone()
        session["user_id"] = user[0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function