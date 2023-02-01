import pandas as pd
import json
import plotly
import plotly.express as px
from flask import render_template, url_for, flash, redirect, request,send_file
from sma import app, db, bcrypt
from sma.forms import RegistrationForm, LoginForm
from sma.models import User
from flask_login import login_user, current_user, logout_user, login_required
app.app_context().push()

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/market")
@login_required
def market():
    return render_template('market.html', title='Market')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account")
def account():
    return render_template('account.html', title='Account')

@app.route('/learn/<endpoint>')
def learn(endpoint):
    if endpoint=='basic':
        return render_template('/learn/learn.html')
    elif endpoint=='fundamental':
        return render_template('/learn/fundamental.html')
    elif endpoint=='technical':
        return render_template('/learn/technical.html')

@app.route('/stock/<stockname>')
@login_required
def stock(stockname='SBILIFE'):
    return render_template('stock.html',stockname=stockname)

@app.route('/stock')
@login_required
def stock2():
    return render_template('stock.html')

@app.route('/callback/<endpoint>')
def cb(endpoint):
    if endpoint == "getStock":
        return gm(request.args.get('data'))
    elif endpoint == "getInfo":
        stock = request.args.get('data')
        f = open(f'./sma/static/companyInfo/{stock}.json', "r")
        # Reading from file
        data = json.loads(f.read())
        max = data['fiftyTwoWeekHigh']['0']
        min = data['fiftyTwoWeekLow']['0']
        symbol = stock
        logo = url_for('static',filename=f'images/logo_imgs/{stock}.png')
        info = {"a52high": max, "a52low": min,
                "shortName": data['longName']['0'] , "symbol": symbol,"logo":logo,"about":data['longBusinessSummary']['0'],
                "fullTimeEmployees":data['fullTimeEmployees']['0'],
                "city":data['city']['0'],
                "website":data['website']['0'],
                "phone":data['phone']['0'],"sector":data['sector']['0'],
                }
        tableinfo=['grossProfits','totalCash','totalDebt','totalRevenue','totalCashPerShare','revenuePerShare','bookValue','priceToBook','marketCap','averageVolume']
        for i in tableinfo:
            info[i]=data[i]['0']
        return json.dumps(info)

    elif endpoint == "fetchListOfStocks":
        df = pd.read_csv("./sma/static/csv/nifty500.csv")
        companyName=(df['Company Name']).to_list()
        symbol = (df['Symbol']).to_list()
        listOf500 = {"symbol":symbol,
        "companyName":companyName
        }
        return json.dumps(listOf500)

    else:
        return "Bad endpoint", 400


# Return the JSON data (Plotly graph)
def gm(stock):
    df = pd.read_csv(f"./sma/static/csv/nifty_500_data/{stock}.csv")
    df = df.reset_index()
    max = (df['Close'].max())
    min = (df['Close'].min())
    range = max - min
    margin = range * 0.05
    max = max + margin
    min = min - margin
    fig = px.area(df, x='Date', y="Close",
                  hover_data=("Open", "Close", "Volume"),
                  range_y=(min, max), template="seaborn")

    #JSON representation of the graph
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

@app.route('/fetchListOfStocks')
def fetchListOfStocks():
    df = pd.read_csv("./sma/static/nifty500.csv")
    info=df.Industry+"("+df.Symbol+")"
    symbol = df.Symbol
    listOf500 = {"info":1,
    "info2":2,
    # "symbol":symbol
    }
    return json.dumps(listOf500)

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
@login_required
def download(filename):   
    return send_file(f'./static/csv/nifty_500_data/{filename}',as_attachment=True)