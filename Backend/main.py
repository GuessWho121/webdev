import os
from flask import Flask, render_template, request, redirect

template_dir = os.path.abspath('../FrontEnd/dasHbOArd')
app = Flask(__name__, template_folder=template_dir)



@app.route("/")
def index():
    return render_template("db.html")









if __name__ in "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
