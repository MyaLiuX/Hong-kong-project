from flask import Flask, render_template, flash, redirect, request, url_for
from WaitingTime import WaitingTimeClient 
import os
from dotenv import load_dotenv
from Feedbackdb import db, Feedback
import threading, time
from datetime import datetime 
from zoneinfo import ZoneInfo

# --- Constants and Initial Data Structures ---
CONTROL_POINT_CODES = ["HYW", "HZM", "LMC", "LSC", "LWS", "MKT", "SBC", "STK"]
DEFAULT_QUEUE_STATUS = "Loading..."
INFO_UNAVAILABLE_STATUS = "Info Unavailable"
FETCH_ERROR_STATUS = "Fetch Error"
DEFAULT_LAST_UPDATE = "N/A"
FETCH_INTERVAL_SECONDS = 900 # 15 minutes

def initialize_control_point_data_structure():
    data_structure = {}
    for code in CONTROL_POINT_CODES:
        data_structure[code] = {
            "arrQueue": DEFAULT_QUEUE_STATUS,
            "depQueue": DEFAULT_QUEUE_STATUS,
            "lastUpdate": DEFAULT_LAST_UPDATE
        }
    return data_structure

resident_data_global = initialize_control_point_data_structure()
visitor_data_global = initialize_control_point_data_structure()
last_update = "N/A"

# --- Flask App Setup ---
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key_!ChangeThis!")
client = WaitingTimeClient()

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///./feedback_app_data.db") # Renamed DB file slightly
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# --- Background Data Fetching Thread ---
def data_fetch_and_update_loop():
    global resident_data_global, visitor_data_global, last_update
    print("🚀 Background data fetching thread started.")
    while True:
        current_timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"🔄 [{current_timestamp_str}] Background Fetch: Cycle starting...")
        try:
            client.refresh()
            api_processed_resident_data = client.get_resident_times()
            api_processed_visitor_data = client.get_visitor_times()

            temp_resident_data = initialize_control_point_data_structure()
            if api_processed_resident_data:
                common_lu_res = DEFAULT_LAST_UPDATE
                first_valid_item_res = next((item for item in api_processed_resident_data.values() if isinstance(item, dict) and 'lastUpdate' in item), None)
                if first_valid_item_res: common_lu_res = first_valid_item_res['lastUpdate']
                for code in CONTROL_POINT_CODES:
                    if code in api_processed_resident_data and isinstance(api_processed_resident_data.get(code), dict):
                        temp_resident_data[code] = api_processed_resident_data[code]
                    else:
                        temp_resident_data[code].update({'arrQueue': INFO_UNAVAILABLE_STATUS, 'depQueue': INFO_UNAVAILABLE_STATUS, 'lastUpdate': common_lu_res})
            else:
                for code in CONTROL_POINT_CODES: temp_resident_data[code].update({'arrQueue': FETCH_ERROR_STATUS, 'depQueue': FETCH_ERROR_STATUS, 'lastUpdate': DEFAULT_LAST_UPDATE})
            resident_data_global = temp_resident_data

            temp_visitor_data = initialize_control_point_data_structure()
            if api_processed_visitor_data:
                common_lu_vis = DEFAULT_LAST_UPDATE
                first_valid_item_vis = next((item for item in api_processed_visitor_data.values() if isinstance(item, dict) and 'lastUpdate' in item), None)
                if first_valid_item_vis: common_lu_vis = first_valid_item_vis['lastUpdate']
                for code in CONTROL_POINT_CODES:
                    if code in api_processed_visitor_data and isinstance(api_processed_visitor_data.get(code), dict):
                        temp_visitor_data[code] = api_processed_visitor_data[code]
                    else:
                        temp_visitor_data[code].update({'arrQueue': INFO_UNAVAILABLE_STATUS, 'depQueue': INFO_UNAVAILABLE_STATUS, 'lastUpdate': common_lu_vis})
            else:
                for code in CONTROL_POINT_CODES: temp_visitor_data[code].update({'arrQueue': FETCH_ERROR_STATUS, 'depQueue': FETCH_ERROR_STATUS, 'lastUpdate': DEFAULT_LAST_UPDATE})
            visitor_data_global = temp_visitor_data

            last_update = datetime.now(ZoneInfo("Asia/Hong_Kong")) .strftime("%Y-%m-%d %H:%M:%S %Z")
            print(f"🕒 Updated global last_update = {last_update}")
            
            print(f"✅ [{current_timestamp_str}] Background Fetch: Data updated. Sample (HYW Res Arr): {resident_data_global.get('HYW', {}).get('arrQueue')}")
        except Exception as e:
            current_timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"❌ [{current_timestamp_str}] Background Fetch: Unhandled error in loop: {e}")
        print(f"ℹ️ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Background Fetch: Sleeping for {FETCH_INTERVAL_SECONDS} seconds.")
        time.sleep(FETCH_INTERVAL_SECONDS)

@app.before_request
def start_background_thread_if_not_running():
    if not hasattr(app, 'background_thread_started_flag_main_v2'): # Unique flag name
        print("🚦 Main App: Starting background data fetching thread...")
        background_thread = threading.Thread(target=data_fetch_and_update_loop, daemon=True)
        background_thread.start()
        app.background_thread_started_flag_main_v2 = True

@app.context_processor
def inject_last_update():
    return {"last_update": last_update}

# --- Routes ---
@app.route('/')
def home():
    raw_res_data_for_home = client.fetch_resident()
    raw_vis_data_for_home = client.fetch_visitor()
    home_show_statuses = client.home_page_showing(raw_res_data_for_home, raw_vis_data_for_home)
    overall_last_update = DEFAULT_LAST_UPDATE
    if raw_res_data_for_home and "lastUpdate" in raw_res_data_for_home:
        overall_last_update = raw_res_data_for_home["lastUpdate"]
    elif raw_vis_data_for_home and "lastUpdate" in raw_vis_data_for_home:
        overall_last_update = raw_vis_data_for_home["lastUpdate"]
    return render_template(
        'index.html',
        title='Immigration Control Points - Waiting Times',
        home_show=home_show_statuses,
        last_update=overall_last_update,
        control_points=CONTROL_POINT_CODES # Pass control point codes for feedback form dropdown
    )


def render_control_point_page(template_name, title, point_code):
    # Helper to avoid repetition
    return render_template(
        template_name,
        title=title,
        resident_data=resident_data_global,
        visitor_data=visitor_data_global,
        current_point_code=point_code, # For pre-selecting in feedback form
        control_points=CONTROL_POINT_CODES # For feedback form dropdown
    )

@app.route('/hyw')
def hyw():
    return render_control_point_page('hyw.html', 'Heung Yuen Wai Control Point', 'HYW')

@app.route('/hzm')
def hzm():
    return render_control_point_page('hzm.html', 'Hong Kong-Zhuhai-Macao Bridge', 'HZM')

@app.route('/lmc')
def lmc():
    return render_control_point_page('lmc.html', 'Lok Ma Chau Control Point', 'LMC')

@app.route('/lsc')
def lsc():
    return render_control_point_page('lsc.html', 'Lok Ma Chau Spur Line', 'LSC')

@app.route('/lws')
def lws():
    return render_control_point_page('lws.html', 'Lo Wu Control Point', 'LWS')

@app.route('/mkt')
def mkt():
    return render_control_point_page('mkt.html', 'Man Kam To Control Point', 'MKT')

@app.route('/sbc')
def sbc():
    return render_control_point_page('sbc.html', 'Shenzhen Bay Control Point', 'SBC')

@app.route('/stk')
def stk():
    return render_control_point_page('stk.html', 'Sha Tau Kok Control Point', 'STK')


# --- Feedback Routes ---
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

# --- Main Execution ---
if __name__ == '__main__':
    # Configure basic logging for Flask app
    import logging
    logging.basicConfig(level=logging.INFO) # Or logging.DEBUG for more verbosity
    app.logger.info("Flask application starting...")
    
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    app.run(debug=True, use_reloader=not is_reloader_child, host="0.0.0.0", port=5001)