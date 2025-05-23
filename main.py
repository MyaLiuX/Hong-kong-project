from flask import Flask, render_template, flash, redirect,request
from WaitingTime import WaitingTimeClient
import os
from dotenv import load_dotenv
from Feedbackdb import db, Feedback
import threading, time

# Create the web application
load_dotenv()
app = Flask(__name__)
api_key = os.environ.get("API_KEY")
app.secret_key = "my_secret_key"
client = WaitingTimeClient()   # instantiate once

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Fetch data every 15 minutes
resident_data = {}
visitor_data = {}

def fetch_api_loop():
    global resident_data, visitor_data
    while True:
        print(f"🔄 Refreshing API at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        resident_data = client.get_resident_times()
        visitor_data = client.get_visitor_times()
        print("✅ Resident keys:", list(resident_data.keys()))
        print("✅ Visitor keys:", list(visitor_data.keys()))
        time.sleep(900)  # 15 minutes



@app.route('/')
def home():
    # force refresh every time user visits the homepag
    home_show=client.home_page_showing()

    return render_template(
        'index.html',
        title='Home Page',
        home_show=home_show,
    )

@app.route('/hyw')
def hyw():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'hyw.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/hzm')
def hzm():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'hzm.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/lmc')
def lmc():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'lmc.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/lsc')
def lsc():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'lsc.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/lws')
def lws():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'lws.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/mkt')
def mkt():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'mkt.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/sbc')
def sbc():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'sbc.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route('/stk')
def stk():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()

    return render_template(
        'stk.html',
        title='Secondary Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    point = request.form.get("point")
    message = request.form.get("message")

    if not point or not message:
        flash("Please complete all fields before submitting.", "error")
    else:
        new_feedback = Feedback(point=point, message=message)
        db.session.add(new_feedback)
        db.session.commit()
        flash("Your feedback was submitted.", "success")

    return redirect("/")  

@app.route("/check-db")
def check_db():
    feedbacks = Feedback.query.all()
    return render_template('check_db.html', feedbacks=feedbacks)


if __name__ == '__main__':
    threading.Thread(target=fetch_api_loop, daemon=True).start()
    app.run(debug=True)

