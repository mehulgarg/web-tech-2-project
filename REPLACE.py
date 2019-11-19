from flask import Flask, render_template, flash, request, url_for, redirect, session
from functools import wraps
from passlib.hash import sha256_crypt
import gc
from wtforms import *
import pygal
from dbconnect import connection
from content_management import *
from fixerio import Fixerio
from datetime import *
import pandas as pd

app = Flask(__name__)


@app.route('/')
def getStarted():
    return render_template('index.html')

@app.route('/search/')
def search():
    return render_template('search.html')


@app.route('/login/')
@app.route('/login/', methods = ['GET', 'POST'])
def login_page():
    if 'logged_in' in session:
        if session['logged_in'] == True:
            flash("You are already logged in")
            return redirect(url_for('homepage'))
    error = ''
    try:
        c, conn = connection()
        if(request.method == "POST"):

            data = c.execute(("Select * from user_details where email = {0};").format("'" + request.form['email'] + "'"))
            data = c.fetchone()[5]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True

                flash("You are now logged in");
                return redirect(url_for("homepage"))

            else:
                error = "Invalid Credentials"

        gc.collect()

        return render_template("login.html", error = error)

    except Exception as e:
        flash(e)
        error = 'Invalid Credentials'
        return render_template("login.html", error = error)

class RegistrationForm(Form):
    firstname = TextField('', render_kw = {'placeholder': 'First Name', 'class': 'form-control'})
    lastname = TextField('', render_kw = {'placeholder': 'Last Name', 'class': 'form-control'})
    username = TextField('', [validators.Length(min = 4)], render_kw = {'placeholder': 'Username', 'class': 'form-control'})
    email = TextField('', [validators.Length(min = 6)], render_kw = {'placeholder': 'Email', 'class': 'form-control'})
    password = PasswordField('', [validators.Required(), validators.EqualTo('confirm', message = "Password must match")],  render_kw = {'placeholder': 'Password', 'class': 'form-control'})
    confirm = PasswordField('', render_kw = {'placeholder': 'Confirm Password', 'class': 'form-control'})

@app.route('/register/', methods = ['GET', 'POST'])
def register_page():
    if 'logged_in' in session:
        if session['logged_in'] == True:
            flash("You are already logged in")
            return redirect(url_for('homepage'))
    try:
        form = RegistrationForm(request.form)
        if request.method == "POST" and form.validate():
            firstname = form.firstname.data
            lastname  = form.lastname.data
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))
            c, conn = connection()

            x = c.execute(("Select * from user_details where username = {0} or email = {1}").format("'" + username + "'", "'" + email + "'"))
            if len(c.fetchall()) > 0:
                flash("Useranme/Email is already taken")
                return render_template('register.html', form = form)
            else:
                tracking_info = 'NULL'
                c.execute("Insert into user_details (firstname, lastname, username, email, password) values (%s, %s, %s, %s, %s)", (firstname, lastname, username, email, password))

                conn.commit()
                flash("Thanks for registering")
                c.close()
                conn.close()

                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                try:
                    return redirect(url_for('homepage'))
                except Exception as e:
                    return redirect(url_for(page_not_found))
        else:
             return render_template("register.html", form = form)
    except Exception as e:
        return(str(e))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", error = e)

@app.errorhandler(405)
def random_error(e):
    return render_template("405.html", error = e)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

        else:
            flash("You need to login/register first")
            return redirect(url_for('getStarted'))
    return wrap

@app.route('/homepage/')
@login_required
def homepage():
    return render_template('homepage.html')

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("You have been logged out")
    gc.collect()
    return redirect(url_for('getStarted'))


@app.route('/Stocks/')
@app.route('/Stocks/<int:offset>')
@app.route('/Stocks/<int:offset>')
@app.route('/Stocks/<int:offset>/<string:filterData>/')
@app.route('/Stocks/<int:offset>/<int:costFilter>')
@app.route('/Stocks/<int:offset>//<int:costFilter>')
@app.route('/Stocks/<int:offset>/<string:filterData>/<int:costFilter>')
@login_required
def stocks(filterData = '', offset=0, costFilter = 0):
    print(filterData)
    if len(filterData) > 0 or costFilter > 0:
        print("inside if")
        data = filter_data(filterData, costFilter)
    else:
        data = stock_data()
    length = len(data)
    sector = sectors()
    return render_template('stocks.html', data = data, offset = offset, length = length, sectors= sector, sectorFilter = filterData, costFilter = costFilter)

@app.route('/company/<companyid>')
@login_required
def company_page(companyid):
    c_data = company_data(companyid)
    c_timeseries = company_timeSeries(companyid)
    timeList = time_format(c_timeseries)
    price_list = price_format(c_timeseries)
    line_chart = pygal.Line(x_label_rotation=45)
    line_chart.title = 'Time Series'
    line_chart.x_labels = map(str, timeList)
    line_chart.add('Close', price_list)
    graph_data = line_chart.render_data_uri()
    return render_template("company.html", company_data = c_data, company_timeSeries = c_timeseries, graph_data = graph_data)

@app.route('/mutualfunds/')
@app.route('/mutualfunds/<int:offset>')
@app.route('/mutualfunds/<int:offset>/<int:price>')
@login_required
def mutual_funds(offset=0, price = 0):
    if price == 0:
        data = mutualFunds_data()
    else:
        data = mutualFundFilter(price)
    length = len(data)
    return render_template('mutualfunds.html', data = data, offset = offset, length=length, priceFilter = price)


@app.route('/forex/', methods = ['GET', 'POST'])
@login_required
def forex():
    forex = forex_table_generator()
    error = ''
    try:
        forex = forex_table_generator()
        if request.method == "POST":
            forex = forex_table_generator()
            start_date = date(2018, 2, 25)
            end_date = date(2018, 4, 1)
            values = []
            dates = []
            line1 = []
            line2 = []
            a = request.form['cur1'].strip()
            b = request.form['cur2'].strip()
            base = request.form['base'].strip()
            datelist = pd.date_range(start_date, end_date).to_pydatetime()
            datelist.tolist()
            for dt in datelist:
                dates.append(dt.strftime("%Y-%m-%d"))
            fxrio = Fixerio()
            for d in dates:
                values.append(fxrio.historical_rates(base=base,date=d,symbols=[a,b]))
            for i in range(len(values)):
                line1.append(values[i]['rates'][a])
                line2.append(values[i]['rates'][b])
            line_chart = pygal.Line(x_label_rotation = 30)
            line_chart.title = a + ' vs ' + b + ' with base as ' + base
            line_chart.x_labels = map(str, dates)
            line_chart.add(a, line1)
            line_chart.add(b, line2)
            graph_data = line_chart.render_data_uri()
            return render_template('forex.html', graph_data = graph_data, forex = forex)


        else:
            error = 'Invalid Data'

        return render_template('forex.html', forex = forex)


    except Exception as e:
        flash(e)
        return render_template('forex.html', error = error)









if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug = True)
