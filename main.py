from flask import Flask, render_template, flash, request, url_for, redirect, session
from functools import wraps
from passlib.hash import sha256_crypt
import gc
from wtforms import *
from datetime import *
from dbconnect import connection
from content_management import *
import pandas as pd
import pygal
from fixerio import Fixerio
app = Flask(__name__)


@app.route('/')
def getStarted():
    session.clear()
    if 'logged_in' in session:
        if session['logged_in'] == True:
            print("Already logged in in start part")
    c.execute("""drop view user_view cascade""")
    c.execute("""CREATE view user_view as 
            select user_stocks.user_id,user_stocks.company_id, company, open, last,sector,turnover
            from user_stocks inner join nse_stocks on user_stocks.company_id=nse_stocks.company_id;""")
    return render_template('index.html')

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)

        else:
            flash("You need to login/register first")
            return redirect(url_for('getStarted'))
    return wrap

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




@app.route('/login/')
@app.route('/login/', methods = ['GET', 'POST'])
def login_page():
    if 'logged_in' in session:
        if session['logged_in'] == True:
            flash("You are already logged in")
            return redirect(url_for('homepage'))
    error = ''
    try:
        if(request.method == "POST"):

            data = c.execute(("Select * from user_details where email = {0};").format("'" + request.form['email'] + "'"))
            data = c.fetchone()[5]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True

                c.execute("""SELECT user_id from user_details where email='{}'""".format(request.form['email']))
                data=c.fetchone()
                session['uid']=data[0]
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
               

                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                c.execute("select user_id from user_details where username='{}'".format(session['username']))
                d=c.fetchone()
                print(d)
                session['uid']=d[0]
                print(session['uid'])
                c.close()
                conn.close()
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



@app.route('/homepage/')
@login_required
def homepage():
    c.execute("""SELECT company_id, company, open, ((open-last)/open)*100 as change, total_trade_qty
               FROM nse_stocks
               WHERE sector in (SELECT sector from nse_stocks, user_stocks where user_id={}) order by total_trade_qty desc limit(10);""".format(session['uid']))
    data=c.fetchall()

    print('data ',data)
    c.execute('drop table networth')
    c.execute("""CREATE table networth(quantity numeric,price numeric,total numeric)""")
    c.execute("""INSERT into networth
                SELECT  distinct quantity,close,quantity*close as total
                FROM user_stocks inner join nse_stocks on user_stocks.company_id=nse_stocks.company_id
                WHERE user_id={};""".format(session['uid']))
    c.execute("""INSERT into networth
                SELECT distinct quantity,buying_price,quantity*buying_price as total
                FROM user_mutual_funds inner join mutual_funds on user_mutual_funds.fund_code=mutual_funds.fund_code
                WHERE user_id={};""".format(session['uid']))
    c.execute("""INSERT into networth
                select distinct u.loan_balance,-1,u.loan_balance*(-1)
                from user_loan u,user_details d
                where u.user_id={};""".format(session['uid']))
    c.execute("""SELECT * from networth;
                   SELECT sum(total) from networth;""")
    nworth=c.fetchall()
    return render_template('profile.html',data=data,nworth=nworth)

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("You have been logged out")
    gc.collect()
    return redirect(url_for('getStarted'))

class addStock(Form):
    company = TextField('Company',[validators.Required()], render_kw = {'placeholder': 'Company', 'class': 'form-control'})
    quantity = TextField('Quantity',[validators.Required()], render_kw = {'placeholder': 'Quantity', 'class': 'form-control'})
    price = TextField('Price', [validators.Required()], render_kw = {'placeholder': 'Price', 'class': 'form-control'})
    date = DateField('Date',[validators.Required()], render_kw = {'class': 'form-control'},format='%Y-%m-%d')
    submit=SubmitField('Add to Profile' , render_kw = {'class': 'btn btn-primary'})

@app.route('/profile_stocks',methods = ['GET', 'POST'])
def add_stock():
    form=addStock(request.form)
    if request.method == "POST":
        command="INSERT INTO user_stocks values('{}','{}','{}',{},{})".format(session['uid'],form.company.data,form.date.data,float(form.price.data),float(form.quantity.data))
        c.execute(command)
        c.execute("""SELECT user_stocks.company_id,user_stocks.timestamp_d,user_stocks.buying_price,user_stocks.quantity, nse_stocks.open,((close-open)/close)*100 as change, user_stocks.quantity*open as value
                    from user_stocks inner join nse_stocks on user_stocks.company_id=nse_stocks.company_id
                    where user_id='{}'""".format(session['uid']))
        data = c.fetchall()
        c.execute("""SELECT t.sec,t.change
        			from 
	        			(SELECT n.sector as sec, avg(((last-open)/last)*100) as change
	        			from nse_stocks n, user_stocks u
	        			where n.company_id=u.company_id and u.user_id=5
	        			group by sector order by change desc limit 1 ) as t
	        		where t.change>0;
	        			""".format(session['uid'])
        			)
        top=c.fetchall()
        c.execute("""   SELECT n.sector as sec, avg(((last-open)/last)*100) as change
                        from nse_stocks n, user_stocks u
                        where n.company_id=u.company_id and u.user_id={}
                        group by sector order by change asc limit 1 """.format(session['uid'])
                    )
        worst=c.fetchall()

        return render_template('add_stock.html',form=form,data=data,top=top,worst=worst)
    else:
        c.execute("""SELECT user_stocks.company_id,user_stocks.timestamp_d,user_stocks.buying_price,user_stocks.quantity, nse_stocks.open,((close-open)/close)*100 as change,user_stocks.quantity*open as value
                    from user_stocks inner join nse_stocks on user_stocks.company_id=nse_stocks.company_id
                    where user_id={}""".format(session['uid']))
        data = c.fetchall()

        c.execute("""SELECT company_id, company, open,turnover
                        from nse_stocks 
                        where open between 
                            (select min(open)from user_stocks join nse_stocks on user_stocks.company_id=nse_stocks.company_id) 
                            and 
                            (select max(open)from user_stocks join nse_stocks on user_stocks.company_id=nse_stocks.company_id) 
                            and sector=(select sector 
                                        from user_stocks join nse_stocks on user_stocks.company_id=nse_stocks.company_id 
                                        group by sector having count(sector)= 
                                                                (select max(c) 
                                                                 from 
                                                                    (select sector, count(*) as c 
                                                                     from user_stocks join nse_stocks on user_stocks.company_id=nse_stocks.company_id and user_id={} 
                                                                     group by sector order by c desc limit 1) as t) limit 1) order by turnover desc limit 5;""".format(session['uid']))
        rec=c.fetchall()

        c.execute("""SELECT company_id,company,sector,open,turnover from user_view
                        where user_id in (
                            select h.user_id 
                            from user_stocks as h
                            where exists

                                (select v.sector from nse_stocks v ,user_view n where n.user_id=h.user_id and n.user_id <> {}
                                intersect
                                (select sector 
                                    from user_view k
                                    where k.user_id={}
                                    group by sector having count(sector)= 
                                                            (select max(c) 
                                                             from 
                                                                (select sector, count(*) as c 
                                                                 from user_view where user_view.user_id={}
                                                                 group by sector order by c desc limit 1) as t)))) order by turnover desc limit(5);""".format(session['uid'],session['uid'],session['uid']))
        rec_other=c.fetchall()

        c.execute("""SELECT t.sec,t.change
        			from 
	        			(SELECT n.sector as sec, avg(((last-open)/last)*100) as change
	        			from nse_stocks n, user_stocks u
	        			where n.company_id=u.company_id and u.user_id=5
	        			group by sector order by change desc limit 1 ) as t
	        		where t.change>0;
	        			""".format(session['uid'])
        			)
        top=c.fetchall()
        c.execute("""   SELECT n.sector as sec, avg(((last-open)/last)*100) as change
                        from nse_stocks n, user_stocks u
                        where n.company_id=u.company_id and u.user_id={}
                        group by sector order by change asc limit 1 """.format(session['uid'])
                    )
        worst=c.fetchall()
        return render_template('add_stock.html',form=form,data=data,rec=rec,rec_other=rec_other,top=top,worst=worst)


class addLoan(Form):
    loan_type = TextField('Loan Type',[validators.Required()], render_kw = {'class': 'form-control'})
    loan_amount = TextField('Amount',[validators.Required()], render_kw = {'class': 'form-control'})
    start_date = DateField('Date',[validators.Required()], render_kw = {'class': 'form-control'},format='%Y-%m-%d')
    tenure = TextField('Tenure',[validators.Required()], render_kw = {'class': 'form-control'})
    emis_to_pay =  TextField('EMIs to pay',[validators.Required()], render_kw = {'class': 'form-control'})
    bank_name = TextField('Bank',[validators.Required()], render_kw = {'class': 'form-control'})
    loan_balance = TextField('Loan Balance',[validators.Required()], render_kw = {'class': 'form-control'})
    submit=SubmitField('Add to Profile', render_kw = {'class': 'btn btn-primary'} )

@app.route('/profile_loan',methods = ['GET', 'POST'])
def loan():
    form=addLoan(request.form)
    if request.method == "POST":
        command="""INSERT INTO user_loan
                   values ('{}','{}',{},'{}',{},{},{},'{}')""".format(session['uid'],form.loan_type.data,float(form.loan_amount.data),form.start_date.data,int(form.tenure.data),float(form.loan_balance.data),int(form.emis_to_pay.data),form.bank_name.data,)
        c.execute(command);
        c.execute("""SELECT *
                   FROM user_loan
                   WHERE user_id={}""".format(session['uid']))
        data=c.fetchall()
        return render_template('add_loan.html',form=form,data=data)

    else:
        c.execute("""SELECT *
                   FROM user_loan
                   WHERE user_id={}""".format(session['uid']))
        data=c.fetchall()
        l=[]
        for i in data:
            if(abs(datetime.datetime.strptime(str(i[3]),'%Y-%m-%d').day-datetime.datetime.today().day<7)):
                l.append(i)
                c.execute("""UPDATE user_loan
                            set emis_to_pay=emis_to_pay-1, loan_balance=loan_balance-(loan_amount/tenure)
                            where user_id={} and loan_type='{}' and bank_name='{}'""".format(session['uid'],i[1],i[7]))
                c.execute("""delete from user_loan
                            where emis_to_pay=0""")

        return render_template('add_loan.html',form=form,data=data,l=l)

class addFund(Form):
    fund_code = TextField('Fund Code',[validators.Required()], render_kw = {'class': 'form-control'})
    start_date = DateField('Date',[validators.Required()], render_kw = {'class': 'form-control'},format='%Y-%m-%d')
    price = TextField('Price',[validators.Required()], render_kw = {'class': 'form-control'})
    qty =  TextField('Units',[validators.Required()], render_kw = {'class': 'form-control'})
    submit=SubmitField('Add to Profile', render_kw = {'class': 'btn btn-primary'})

@app.route('/profile_mfunds',methods = ['GET', 'POST'])
def mfunds():
    form=addFund(request.form)
    if request.method == "POST":
        c.execute("""INSERT INTO user_mutual_funds
                     values ({},'{}','{}',{},{})""".format(session['uid'],form.fund_code.data,form.start_date.data,float(form.price.data),float(form.qty.data)))
        c.execute("""SELECT fund_code, timestamp_d,buying_price, quantity 
                    from user_mutual_funds 
                    where user_id='{}'""".format(session['uid']))
        data=c.fetchall()
        return render_template('profile_mutualfund.html',data=data,form=form)
    else:
        c.execute("""SELECT fund_code, timestamp_d,buying_price, quantity 
                    from user_mutual_funds 
                    where user_id='{}'""".format(session['uid']))
        data=c.fetchall()
        return render_template('profile_mutualfund.html',data=data,form=form)

@app.route('/delete/')
def delete_profile():
	c.execute("DELETE from user_details where user_id={}".format(session['uid']))
	session.clear()
	return render_template('delete.html')

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
    c, conn = connection()
    app.run(debug = True)
