from flask import Flask, render_template
from WaitingTime import WaitingTimeClient
import os
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
api_key = os.environ.get("API_KEY")
client = WaitingTimeClient()   # instantiate once


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

