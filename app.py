from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")

def index():
    return render_template("index.html")

@app.route("/greet", methods=["POST"])
def greet():
    name = request.form.get("name", "world")
    #request.args is for inputs from a GET request,
    #we have to use request.form in Flask for inputs from a POST request.
    #get function allows for a default value, which in this case is world

    return render_template("greet.html", name=name)