from flask import Flask
from flask import Flask, render_template, request

# Creating a Flask web application instance
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"]) 
def hello():
    return "<h1>Hello, World! 23<h1>"

@app.route("/feature", methods=["GET", "POST"]) 

def feature():
    return "<h1>This is our feature 1<h1>"
app.run(debug=True)