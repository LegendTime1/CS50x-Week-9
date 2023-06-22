# Implements a registration form, storing registrants in a dictionary, with error messages
from flask import Flask, render_template, request, redirect
from cs50 import SQL

db = SQL("sqlite:///froshims.db")

app = Flask(__name__)

REGISTRANTS = {}

SPORTS =[
    "Basketball",
    "Soccer",
    "Cricket"
]

@app.route("/")
def index():
    return render_template("index.html", sports=SPORTS)

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("name")
    #Validate name
    if not name:
        return render_template("error.html", message="Missing name")

    #Validate sport
    sport = request.form.get("sport")
    if not sport:
        return render_template("error.html", message="Missing sport")

    if sport not in SPORTS:
        return render_template("error.html", message="Invalid sport")

    #Remembering registrants
    REGISTRANTS[name] = sport

    #redirect to another route that will display registered students
    return redirect("/registrants")

@app.route("/registrants")
def registrants():
    return render_template("registrants.html", registrants=REGISTRANTS)
