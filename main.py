from flask import Flask, render_template, flash, redirect,request
from WaitingTime import WaitingTimeClient
import os
from dotenv import load_dotenv
from Feedbackdb import db, Feedback

# Create the web application
load_dotenv()
app = Flask(__name__)
api_key = os.environ.get("API_KEY")
app.secret_key = "my_secret_key"
client = WaitingTimeClient()   # instantiate once

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

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

    return redirect("/")  # or wherever your homepage is


@app.route('/')
def home():
    resident_data = client.get_resident_times()
    visitor_data  = client.get_visitor_times()
    return render_template(
        'index.html',
        title='Home Page',
        resident_data=resident_data,
        visitor_data=visitor_data
    )

if __name__ == '__main__':
    app.run(debug=True)

