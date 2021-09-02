import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, send_file
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from docx import Document
from docx.shared import Inches
from helpers import city_check, login_required, apology, errorhandler, C_check, level_check, mui_calc, Sk_calc, get_citydata, mu_calc
from snowdoc import snow1_to_docx, snow2_to_docx, snow3_to_docx, snow4_to_docx, snow5_to_docx, snow6_to_docx, snow7_to_docx
from math import sin, radians

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


@app.route("/")
def index():
    return render_template("index.html")

#----------------------------------------------SNOW 1 (Singleslope)-------------------------------------------------
@app.route("/snow1", methods=["GET", "POST"])
def snow1():
    if request.method == "POST":

        #--1-- take the data value from the form
        slope = request.form.get("slope")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]
        roof_check = request.form.get("roof_check")

        #--2-- Check the data exist
        if not slope or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклон кровли либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            slope = int(slope)
        except ValueError:
            return apology("Значение уклона должно быть целым числом", 400)
        if slope < 0 or slope > 89:
            return apology("Уклон должен быть положительным числом от 0 до 90", 400)

        #--5-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        b = get_citydata(city)
        snow_area = b[0]
        level = b[1]

        #--7-- Check the current_level input
        level = level_check(level, current_level)

        #--8-- Calculating of mui
        mui = mui_calc(slope, roof_check)

        #--9-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = a[0]
        Sk_formula = a[1]

        #---10---Finally calculate the snow load:
        s = round(float(Sk / 1000) * Ce * Ct * mui, 2)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow1_to_docx(slope, Ce, Ct, city, mui, level, snow_area, Sk, Sk_formula, s)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
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
                snow_load = s)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database and create a list of cities
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow1.html", cities=cities)
        #Close SQLite thread
        connection.commit
        connection.close()

#----------------------------------------------SNOW 2 (Doubleslope)-------------------------------------------------
@app.route("/snow2", methods=["GET", "POST"])
def snow2():
    if request.method == "POST":

        #--1-- take the data value from the form
        slope1 = request.form.get("slope1")
        slope2 = request.form.get("slope2")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]
        roof_check1 = request.form.get("roof_check1")
        roof_check2 = request.form.get("roof_check2")

        #--2-- Check the data exist
        if not slope1 or not slope2 or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклоны кровли либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            slope1 = int(slope1)
            slope2 = int(slope2)
        except ValueError:
            return apology("Значения уклонов должны быть целыми числами", 400)
        if slope1 < 0 or slope1 > 89 or slope2 < 0 or slope2 > 89:
            return apology("Уклоны должны быть положительными числами от 0 до 90", 400)

        #--5-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        b = get_citydata(city)
        snow_area = b[0]
        level = b[1]

        #--7-- Check the current_level input
        level = level_check(level, current_level)

        #--8-- Calculating of mui
        mui1 = mui_calc(slope1, roof_check1)
        mui2 = mui_calc(slope2, roof_check2)

        #--9-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = a[0]
        Sk_formula = a[1]

        #---10---Finally calculate the snow load:
        s1 = round(float(Sk / 1000) * Ce * Ct * mui1, 2)
        s2 = round(float(Sk / 1000) * Ce * Ct * mui2, 2)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow2_to_docx(slope1, slope2, Ce, Ct, city, mui1, mui2, level, snow_area, Sk, Sk_formula, s1, s2)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow2-done.html",
                slope1 = slope1,
                slope2 = slope2,
                Ce = Ce,
                Ct = Ct,
                city = city,
                mui1 = mui1,
                mui2 = mui2,
                level = level,
                snow_area = snow_area,
                Sk = float(Sk/1000),
                Sk_formula = Sk_formula,
                s1 = s1,
                s2 = s2)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()

        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow2.html", cities=cities)

        #Close SQLite thread
        connection.commit
        connection.close()


#----------------------------------------------SNOW 3 (multislopes)-------------------------------------------------
@app.route("/snow3", methods=["GET", "POST"])
def snow3():
    if request.method == "POST":

        #--1-- take the data value from the form
        slope1 = request.form.get("slope1")
        slope2 = request.form.get("slope2")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]
        roof_check1 = request.form.get("roof_check1")
        roof_check2 = request.form.get("roof_check2")

        #--2-- Check the data exist
        if not slope1 or not slope2 or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклоны кровли либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            slope1 = int(slope1)
            slope2 = int(slope2)
        except ValueError:
            return apology("Значения уклонов должны быть целыми числами", 400)
        if slope1 < 0 or slope1 > 89 or slope2 < 0 or slope2 > 89:
            return apology("Уклоны должны быть положительными числами от 0 до 90", 400)

        #--5-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        b = get_citydata(city)
        snow_area = b[0]
        level = b[1]

        #--7-- Check the current_level input
        level = level_check(level, current_level)

        #--8-- Calculating of mui (snow without extra load) and mu2 (Snow with the extra load)
        mui1 = mui_calc(slope1, roof_check1)
        mui2 = mui_calc(slope2, roof_check2)
        #coefficient for the inner slopes for the I case of load:
        mui1a = mui_calc(slope1, 1)
        mui2a = mui_calc(slope2, 1)
        #coefficient for the inner slopes for the II case of load:
        mu2 = round(mu_calc(slope1, slope2),3)

        #--9-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = a[0]
        Sk_formula = a[1]

        #---10---Finally calculate the snow load:
        s1 = round(float(Sk / 1000) * Ce * Ct * mui1, 2)
        s1a = round(float(Sk / 1000) * Ce * Ct * mui1a, 2)
        s2 = round(float(Sk / 1000) * Ce * Ct * mui2, 2)
        s2a = round(float(Sk / 1000) * Ce * Ct * mui2a, 2)
        s3 = round(float(Sk / 1000) * Ce * Ct * mu2, 2)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow3_to_docx(slope1, slope2, Ce, Ct, city, mui1, mui1a, mui2, mui2a, mu2, level, snow_area, Sk, Sk_formula, s1, s1a, s2, s2a, s3)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow3-done.html",
                slope1 = slope1,
                slope2 = slope2,
                Ce = Ce,
                Ct = Ct,
                city = city,
                mui1 = mui1,
                mui1a = mui1a,
                mui2 = mui2,
                mui2a = mui2a,
                mu2 = mu2,
                level = level,
                snow_area = snow_area,
                Sk = float(Sk/1000),
                Sk_formula = Sk_formula,
                s1 = s1,
                s1a = s1a,
                s2 = s2,
                s2a = s2a,
                s3 = s3)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()

        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow3.html", cities=cities)

        #Close SQLite thread
        connection.commit
        connection.close()


#----------------------------------------------SNOW 4 (Arcslope)-------------------------------------------------
@app.route("/snow4", methods=["GET", "POST"])
def snow4():
    if request.method == "POST":

        #--1-- take the data value from the form
        b = request.form.get("b")
        h = request.form.get("h")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]

        #--2-- Check the data exist
        if not b or not h or not Ce or not Ct or not city:
            return apology("Вы забыли указать габариты кровли либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the roof dimensions is p;ositive integer or not
        try:
            b = int(b)
            h = int(h)
        except ValueError:
            return apology("Значения габаритов кровли должны быть целыми числами (указывайте значения в миллиметрах)", 400)
        if b < 0 or b > 200000 or h < 0 or h > 200000:
            return apology("Габариты кровли должны быть положительными числами от 0 до 200000", 400)

        #--5-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        c = get_citydata(city)
        snow_area = c[0]
        level = c[1]

        #--7-- Check the current_level input
        level = level_check(level, current_level)

        #--8-- Calculating of mui (snow without extra load) and mu2 (Snow with the extra load)
        mu3 = round(0.2 + 10 * h / b, 3)
        if mu3 > 2:
            mu3 = 2

        #--9-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = a[0]
        Sk_formula = a[1]

        #---10---Finally calculate the snow load:
        s1 = round(float(Sk / 1000) * Ce * Ct * 0.8, 2)
        s2 = round(float(Sk / 1000) * Ce * Ct * mu3, 2)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow4_to_docx(b, h, Ce, Ct, city, mu3, level, snow_area, Sk, Sk_formula, s1, s2)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow4-done.html",
                b = b,
                h = h,
                Ce = Ce,
                Ct = Ct,
                city = city,
                mu3 = mu3,
                level = level,
                snow_area = snow_area,
                Sk = float(Sk/1000),
                Sk_formula = Sk_formula,
                s1 = s1,
                s2 = s2)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()

        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow4.html", cities=cities)

        #Close SQLite thread
        connection.commit
        connection.close()

#----------------------------------------------SNOW 5 (drop roof)-------------------------------------------------
@app.route("/snow5", methods=["GET", "POST"])
def snow5():
    if request.method == "POST":

        #--1-- take the data value from the form
        b1 = request.form.get("b1")
        b2 = request.form.get("b2")
        h = request.form.get("h")
        L = request.form.get("L")
        slope1 = request.form.get("slope1")
        slope2 = request.form.get("slope2")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]
        roof_check1 = request.form.get("roof_check1")
        roof_check2 = request.form.get("roof_check2")

        #--2-- Check the data exist
        if not slope1 or not slope2 or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклоны кровли либо город", 400)
        if not b1 or not b2 or not h or not L:
            return apology("Вы забыли указать габариты кровли и перепад", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            slope1 = int(slope1)
            slope2 = int(slope2)
        except ValueError:
            return apology("Значения уклонов должны быть целыми числами", 400)
        if slope1 < 0 or slope1 > 89 or slope2 < 0 or slope2 > 89:
            return apology("Уклоны должны быть положительными числами от 0 до 90", 400)

        #--5-- Check the roof dimensions is positive integer or not
        try:
            b1 = int(b1)
            b2 = int(b2)
            h = int(h)
            L = int(L)
        except ValueError:
            return apology("Значения габаритов кровли должны быть целыми числами (указывайте значения в миллиметрах)", 400)
        if b1 < 0 or b1 > 500000 or b2 < 0 or b2 > 500000 or h < 0 or h > 500000 or L < 0 or L > 500000:
            return apology("Габариты кровли должны быть положительными числами от 0 до 500000", 400)

        #--6-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--7-- Get the snow area data and level data (if the city is already correct)
        b = get_citydata(city)
        snow_area = b[0]
        level = b[1]

        #--8-- Check the current_level input
        level = level_check(level, current_level)

        #--9-- Calculating of mui
        mui1 = mui_calc(slope1, roof_check1)
        mui2 = mui_calc(slope2, roof_check2)

        #--10-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = a[0]
        Sk_formula = a[1]

        #---11--- Calculate the snow load on the roof for the case I:

        s1 = round(float(Sk / 1000) * Ce * Ct * mui1, 2) #- это нагрузка на высокую кровлю без аккумуляции
        s2 = round(float(Sk / 1000) * Ce * Ct * mui2, 2) #- это нагрузка на низкую кровлю без аккумуляции

        #---12--- Calculating of ls and picture_link
        if 2 * h > 6000:
            ls = 6
        elif 2 * h < 2000:
            ls = 2
        else:
            ls = round(2 * h/1000,2)

        if b2/1000 > ls:
            p_link1 = "/static/snow_pictures/snow_load5a.jpg"
            p_link2 = "/static/snow_pictures/snow_load5a-1.jpg"
            p_link3 = "/static/snow_pictures/snow_load5a-2.jpg"
        else:
            p_link1 = "/static/snow_pictures/snow_load5b.jpg"
            p_link2 = "/static/snow_pictures/snow_load5b-1.jpg"
            p_link3 = "/static/snow_pictures/snow_load5b-2.jpg"

        #--13-- Calculating of the area of the buttom roof (slope2)
        S = round(float(L/1000*b2/1000),2)

        #--14-- Calculating of mus
        if slope1 <= 15 or roof_check1 == 1:
            mus = 0
        else:
            mus = round(0.5 * s1, 3)

        #--14-- Calculating of muw
        muw = min(round((b1 + b2) / (2 * h), 3), round(2 * h / Sk, 3))

        if S >= 6 and muw > 0.8:
            muw = min(2.5, muw)
        elif S >= 2 and muw > 0.8:
            muw = min(0.25*(S - 2)+1.5, muw)
        elif S >= 1 and muw > 0.8:
            muw = min((S-1)*0.7+0.8, muw)
        else:
            muw = 0.8

        #--15-- Finally Calculating of mu3 and s3:
        mu2 = mus + muw
        s3 = round(float(Sk / 1000) * Ce * Ct * mu2, 2) #- это нагрузка на низкую кровлю с учетом аккумуляции

        #- Расчет нагрузки на краю низкой кровли в случае когда зона повышенного снегоотложения длиннее ширины кровли
        if b2/1000 > ls:
            sx = s2
        else:
            sx = round(s3-float(b2/1000)/ls*(s3-s2),2)


        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow5_to_docx(b1,b2,h,L,S,slope1, slope2, Ce, Ct, city, mui1, mui2, mus, muw, mu2, ls, p_link1, p_link2, p_link3, level, snow_area, Sk, Sk_formula, s1, s2, s3, sx)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow5-done.html",
                b1 = float(b1/1000),
                b2 = float(b2/1000),
                h = float(h/1000),
                L = float(L/1000),
                S = S,
                slope1 = slope1,
                slope2 = slope2,
                Ce = Ce,
                Ct = Ct,
                city = city,
                mui1 = mui1,
                mui2 = mui2,
                mus = mus,
                muw = muw,
                mu2 = round(mu2,3),
                ls = ls,
                p_link1 = p_link1,
                p_link2 = p_link2,
                p_link3 = p_link3,
                level = level,
                snow_area = snow_area,
                Sk = float(Sk/1000),
                Sk_formula = Sk_formula,
                s1 = s1,
                s2 = s2,
                s3 = s3,
                sx = sx)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()

        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow5.html", cities=cities)

        #Close SQLite thread
        connection.commit
        connection.close()


#----------------------------------------------SNOW 6 (Roof with the wall)-------------------------------------------------
@app.route("/snow6", methods=["GET", "POST"])
def snow6():
    if request.method == "POST":

        #--1-- take the data value from the form
        h = request.form.get("h")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]

        #--2-- Check the data exist
        if not h or not Ce or not Ct or not city:
            return apology("Вы забыли указать высоту надстройки либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            h = int(h)
        except ValueError:
            return apology("Значение высоты надстройки должно быть целым числом (указывайте в миллиметрах)", 400)
        if h < 0 or h > 50000:
            return apology("Значение высота надстройки должно быть положительным числом от 0 до 50000", 400)

        #--5-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        b = get_citydata(city)
        snow_area = b[0]
        level = b[1]

        #--7-- Check the current_level input
        level = level_check(level, current_level)

        #--8-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = float(a[0]/1000)
        Sk_formula = a[1]


        #---8--- Calculating of ls
        if 2 * h > 6000:
            ls = 6
        elif 2 * h < 2000:
            ls = 2
        else:
            ls = round(2 * h/1000,2)

        #--9-- Calculating of mu2
        mu1 = 0.8
        h = round(h / 1000, 2)
        mu2 = round(2*h/Sk,3)
        if mu2 > 2:
            mu2 = 2

        #---10---Finally calculate the snow load:
        s1 = round(Sk * Ce * Ct * mu1, 2)
        s2 = round(Sk * Ce * Ct * mu2, 2)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow6_to_docx(h, ls, Ce, Ct, mu1, mu2, Sk, s1, s2)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow6-done.html",
                h = h,
                ls = ls,
                Ce = Ce,
                Ct = Ct,
                mu1 = mu1,
                mu2 = mu2,
                Sk = Sk,
                s1 = s1,
                s2 = s2)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database and create a list of cities
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow6.html", cities=cities)
        #Close SQLite thread
        connection.commit
        connection.close()



#----------------------------------------------SNOW 7 (Snow loads on snowguards and other obstacles)-------------------------------------------------
@app.route("/snow7", methods=["GET", "POST"])
def snow7():
    if request.method == "POST":

        #--1-- take the data value from the form
        slope = request.form.get("slope")
        b = request.form.get("b")
        Ce = request.form.get("Ce")
        Ct = request.form.get("Ct")
        current_level = request.form.get("level")
        city = request.form.get("city").rsplit(sep=' → ')[0]

        #--2-- Check the data exist
        if not slope or not b or not Ce or not Ct or not city:
            return apology("Вы забыли указать уклон кровли, расстояние b, либо город", 400)

        #--3-- Check the city data input
        if not city_check(city):
            return apology('Города "{}" нет в представленном списке, оставьте отзыв и я могу внести его в базу данных'.format(city), 400)

        #--4-- Check the slope is integer or not
        try:
            slope = int(slope)
        except ValueError:
            return apology("Значение уклона должно быть целым числом", 400)
        if slope < 0 or slope > 90:
            return apology("Уклон должен быть положительным числом от 0 до 90", 400)

        #--5-- Check the b is integer or not
        try:
            b = int(b)
        except ValueError:
            return apology("Значение b должно быть целым числом", 400)
        if slope < 0 or slope > 50000:
            return apology("Значение b должно быть положительным числом от 0 до 50000 (значение должно быть в миллиметрах)", 400)

        #--6-- Check the Ce and Ct data
        Ce = C_check(Ce)
        Ct = C_check(Ct)

        #--6-- Get the snow area data and level data (if the city is already correct)
        с = get_citydata(city)
        snow_area = с[0]
        level = с[1]

        #--8-- Check the current_level input
        level = level_check(level, current_level)

        #--9-- Calculating of Sk and Sk_formula
        a = Sk_calc(level, snow_area)
        Sk = float(a[0]/1000)
        Sk_formula = a[1]

        #---10---Finally calculate the snow load:
        s = round(Sk * Ce * Ct * 0.8, 2)
        Fs = round(s * b/1000 * sin(radians(slope)), 2)
        sinalfa = round(sin(radians(slope)), 3)

        #if the button "DOWLOAD" pressed by user:
        if request.form["button"]=="download":
            #Creation and sending of the docx file to user:
            return snow7_to_docx(slope, float(b/1000), sinalfa, s, Fs)

        #if the button "CREATE HTML" pressed by user:
        elif request.form["button"]=="create_html":
            return render_template("snow7-done.html",
                slope = slope,
                b = float(b/1000),
                sinalfa = sinalfa,
                s = s,
                Fs = Fs)

    # User reached route via GET
    else:
        # create a sqlite3 connection to SQL database and create a list of cities
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()
        cities = cur.execute("SELECT * FROM cities ORDER BY city;")
        cities = cur.fetchall()
        return render_template("snow7.html", cities=cities)
        #Close SQLite thread
        connection.commit
        connection.close()



@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # create a sqlite3 connection to SQL database
        connection = sqlite3.connect('database.db')
        cur = connection.cursor()

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

        connection.commit
        connection.close()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


#----------------------------------------------WIND 1-------------------------------------------------
@app.route("/wind1", methods=["GET", "POST"])
def wind1():
    return render_template("wind1.html")


@app.route("/info", methods=["GET"])
def info():
    return render_template("info.html")


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


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
