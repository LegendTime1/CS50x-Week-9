from flask import Flask, render_template, request

app = Flask(__name__)

SPORTS =[
    "Basketball",
    "Soccer",
    "Cricket"
]

@app.route("/")
#Name of function doesn't necessarily
#have to be same as app.route or even in render_template("")

def index():
    return render_template("index.html", sports=SPORTS)

@app.route("/register", methods=["POST"])
def register():
    if not request.form.get("name") or request.form.get("sport") not in SPORTS:
        return render_template("failure.html")

    return render_template("success.html")



