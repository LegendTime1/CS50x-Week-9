import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    #db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

    portfolio_db = db.execute("SELECT symbol, name, SUM(shares) as shares, price FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
    user_db = db.execute("SELECT cash, username FROM users WHERE id = ?", user_id)
    user_cash = user_db[0]["cash"]
    username = user_db[0]["username"]
    stocks_value = 0
    for stock in portfolio_db:
        stocks_value += stock["shares"] * stock["price"]
    total = user_cash + stocks_value

    return render_template("index.html", portfolio=portfolio_db, cash=user_cash, uname = username, total = total, stocks_value = stocks_value)

    #return jsonify(portfolio_db)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")


    symbol = request.form.get("symbol")
    num_shares = int(request.form.get("shares"))
    stock_info = lookup(symbol)
    timestamp = datetime.datetime.now()
    if not symbol:
        return apology("must give stock symbol")

    #Valid symbol or not
    if stock_info == None:
        return apology("Enter valid symbol")

    if num_shares < 0:
        return apology("enter valid number of shares")

    user_id = session["user_id"]

    transaction_cost = num_shares * stock_info["price"]

    #user_cash_db is a list of dictionary something like [{cash:10000}]
    user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    user_real_cash = user_cash_db[0]["cash"]

    if user_real_cash < transaction_cost:
        return apology("Insufficient balance")

    updated_cash = user_real_cash - transaction_cost

    #UPDATE table_name SET column1 = value1, column2 = value2, ... WHERE condition;
    db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)

    #Updating transactions
    #db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
    db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price, date) VALUES (?, ?, ?, ?, ?, ?)", user_id, stock_info["symbol"], stock_info["name"], num_shares, stock_info["price"], timestamp)

    return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", transactions = transactions_db)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

@app.route("/delete")
@login_required
def delete():
    """Deletes user_id"""
    user_id = session["user_id"]
    db.execute("DELETE FROM users WHERE id = ?", user_id)
    # Redirect user to login form
    return redirect("/login")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Addes Additional Cash"""
    user_id = session["user_id"]
    if request.method == "GET":
        return render_template("add.html")

    add_cash = int(request.form.get("add_cash"))
    if not add_cash:
        return apology("Enter some money to add")

    user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    user_real_cash = user_cash_db[0]["cash"]

    updated_cash = user_real_cash + add_cash

    #UPDATE table_name SET column1 = value1, column2 = value2, ... WHERE condition;
    db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)

    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    #User reached via POST(form submission)
    symbol = request.form.get("symbol")
    if not symbol:
        return apology("must give stock symbol")
    stock_info = lookup(symbol)

    #Valid symbol or not
    if stock_info:
        return render_template("quoted.html", stock = stock_info)
    else:
        return apology("Enter valid symbol")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("must provide username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")
        if not password or not confirm_password:
            return apology("must provide password")
        if password != confirm_password:
            return apology("Passwords do not match")

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
        except:
            return apology("Username already exists!")


        return redirect("/")

    #User reached via GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    if request.method == "GET":
        symbols_user = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)

        #return jsonify(shares_user)
        return render_template("sell.html", symbols = symbols_user)

    #User reaches via form submission i.e. POST
    symbol = request.form.get("symbol")
    num_shares = int(request.form.get("shares"))
    stock_info = lookup(symbol)
    shares_user_db = db.execute("SELECT shares from transactions WHERE user_id = ? AND symbol = ? GROUP BY symbol", user_id, symbol)
    shares_user = shares_user_db[0]["shares"]

    timestamp = datetime.datetime.now()
    if not symbol:
        return apology("must give stock symbol")

    #Valid symbol or not
    #if stock_info == None:
    #    return apology("Enter valid symbol")

    if num_shares < 0:
        return apology("enter valid number of shares")

    transaction_cost = num_shares * stock_info["price"]

    #user_cash_db is a list of dictionary something like [{cash:10000}]
    user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    user_real_cash = user_cash_db[0]["cash"]

    if num_shares > shares_user:
        return apology("Do not have this many shares")

    updated_cash = user_real_cash + transaction_cost

    #UPDATE table_name SET column1 = value1, column2 = value2, ... WHERE condition;
    db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)

    #Updating transactions
    #db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
    db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price, date) VALUES (?, ?, ?, ?, ?, ?)", user_id, stock_info["symbol"], stock_info["name"], (-1)*num_shares, stock_info["price"], timestamp)

    return redirect("/")
