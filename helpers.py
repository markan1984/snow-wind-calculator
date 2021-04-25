import sqlite3
from flask import redirect, render_template, request, session
from werkzeug.exceptions import HTTPException, InternalServerError

def city_check(city):
    #Open SQLite connection
    connection = sqlite3.connect('database.db')
    cur = connection.cursor()
    cities = cur.execute("SELECT city FROM cities;")
    cities = cur.fetchall()

    cities_list=[]
    for row in cities:
        cities_list.append(row[0])

    #Close SQLite thread
    connection.commit
    connection.close()

    if city not in cities_list:
        return False
    else:
        return True

#Check the Ce and Ct data
def C_check(C):
    try:
        C = float(C)
    except ValueError:
        return apology("Пожалуйста не меняйте стандартные значения! :(", 400)
    if C != 0.8:
        if C != 1:
            return apology("Пожалуйста не меняйте стандартные значения! :(", 400)
    return C

#apology function definition
def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message), code

def level_check(level, current_level):
    if current_level != "":
        try:
            current_level = int(current_level)
        except ValueError:
            return apology("Значение отметки местности должно быть целым числом", 400)
        if current_level < 100 or current_level > 320:
            return apology("Значение отметки местности должно быть положительным числом от 100 до 320", 400)
        level = current_level
    return level


# Calculating of mui (coefficients without extra snow load)
def mui_calc(slope, roof_check):
    if slope <= 30:
        return 0.8
    elif slope > 30 and slope < 60:
        if roof_check == None:
            return round(0.8 * (60 - slope) / 30, 3)
        else:
            return 0.8
    else:
        return 0

# Calculating of mu (coefficient with extra snow load)
def mu_calc(slope1, slope2):
    slope = (slope1 + slope2) / 2
    if slope <= 30:
        return (0.8 + 0.8 * slope / 30)
    else:
        return 1.6


def Sk_calc(level, snow_area):
    if snow_area == "1а":
        Sk = int(1350)
        Sk_formula = ""
        return (Sk, Sk_formula)
    elif snow_area == "1б":
        Sk = int((1.35 + 2.2 * (level - 155) / 100)*1000)
        Sk_formula = "1.35+2.2∙(A-155)/100="
        return (Sk, Sk_formula)
    elif snow_area == "1в":
        Sk = int((1.35 + 0.38 * (level - 140) / 100)*1000)
        Sk_formula = "1.35+0.38∙(A-140)/100="
        return (Sk, Sk_formula)
    elif snow_area == "2а":
        Sk = int((1.45 + 0.6 * (level - 125) / 100)*1000)
        Sk_formula = "1.45+0.6∙(A-125)/100="
        return (Sk, Sk_formula)
    elif snow_area == "2б":
        Sk = int((1.45 + 0.6 * (level - 150) / 100)*1000)
        Sk_formula = "1.45+0.6∙(A-150)/100="
        return (Sk, Sk_formula)
    elif snow_area == "2в":
        Sk = int((1.45 + 0.6 * (level - 210) / 100)*1000)
        Sk_formula = "1.45+0.6∙(A-210)/100 {но не менее 1,00}="
        if Sk < 1000:
            Sk = 1000
        return (Sk, Sk_formula)
    elif snow_area == "3":
        Sk = int(1550)
        Sk_formula = ""
        return (Sk, Sk_formula)
    else:
        return apology("Неверное значение снегового района (проверьте базу данных)", 500)


def get_citydata(city):
    connection = sqlite3.connect('database.db')
    cur = connection.cursor()
    snow_area = cur.execute("SELECT snow FROM cities WHERE city = ?", (city,))
    snow_area = cur.fetchone()[0]
    level = cur.execute("SELECT level FROM cities WHERE city = ?", (city,))
    level = int(cur.fetchone()[0])
    connection.commit
    connection.close()
    return (snow_area, level)


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

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)