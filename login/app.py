from flask import Flask, render_template, request, redirect, session
from flask_session import Session

app = Flask(__name__)

#configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem" #Storing cookies on the server's hard drive
Session(app)


#session is a dictionary to store user's name
@app.route("/")
def index():

    #The get() method in dictionary returns the value of the item with the
    #specified key.
    if not session.get("name"):
        return redirect("/login")
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("name")
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")
