import schedule
import threading
import time
from datetime import datetime
from twilio.rest import Client
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUM = os.getenv("FROM_NUM")
TO_NUM = os.getenv("TO_NUM")

if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, FROM_NUM, TO_NUM]):
    print("⚠️ Warning: Twilio environment variables not found. SMS functionality will be disabled.")
    print("Please set: TWILIO_SID, TWILIO_AUTH_TOKEN, FROM_NUM, TO_NUM")
    twilio_client = None
else:
    twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Scheduler flags
stop_flag = threading.Event()
thread = None

# Toggle test mode
TEST_MODE = False  # ← Now runs only at exact slot times

# Scheduler time slots
SLOTS = {"morning": "08:00", "afternoon": "14:02", "night": "20:43"}

# SMS sender
def send_sms(med):
    message = f"Reminder: Take {med['name']} - {med['dosage']}"
    print(f"📲 Trying to send SMS: {message}")
    
    if twilio_client is None:
        print(f"⚠️ SMS not sent (Twilio not configured): {message}")
        return
        
    try:
        twilio_client.messages.create(
            body=message,
            from_=FROM_NUM,
            to=TO_NUM
        )
        print(f"✅ SMS Sent: {message}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

# Background thread loop
def scheduler_loop():
    while not stop_flag.is_set():
        schedule.run_pending()
        time.sleep(1)

# Start scheduler
def start_scheduler():
    global thread
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    print("🕒 Scheduler started.")

# Stop scheduler
def stop_scheduler():
    stop_flag.set()
    if thread:
        thread.join()
    print("🛑 Scheduler stopped.")

# Main scheduling logic
def schedule_medicines(meds):
    for med in meds:
        name = med.get("name", "Unknown")
        dosage = med.get("dosage", "")
        freq_str = med.get("frequency", "").strip().lower()
        
        try:
            print(f"📅 Scheduling {name} - {freq_str}")

            # Handle "1-0-1" format
            if re.fullmatch(r"[01]-[01]-[01]", freq_str):
                parts = freq_str.split("-")
                if parts[0] == '1':
                    schedule.every().day.at(SLOTS["morning"]).do(send_sms, med=med)
                if parts[1] == '1':
                    schedule.every().day.at(SLOTS["afternoon"]).do(send_sms, med=med)
                if parts[2] == '1':
                    schedule.every().day.at(SLOTS["night"]).do(send_sms, med=med)
                continue

            # Handle numeric keywords like "2 times", "3x"
            if "2" in freq_str or "twice" in freq_str:
                schedule.every().day.at(SLOTS["morning"]).do(send_sms, med=med)
                schedule.every().day.at(SLOTS["night"]).do(send_sms, med=med)
            elif "3" in freq_str or "thrice" in freq_str:
                schedule.every().day.at(SLOTS["morning"]).do(send_sms, med=med)
                schedule.every().day.at(SLOTS["afternoon"]).do(send_sms, med=med)
                schedule.every().day.at(SLOTS["night"]).do(send_sms, med=med)
            elif "once" in freq_str or "1" in freq_str:
                schedule.every().day.at(SLOTS["morning"]).do(send_sms, med=med)
            else:
                print(f"⚠️ Unrecognized frequency format '{freq_str}' for {name}. Skipping.")

        except Exception as e:
            print(f"⚠️ Error scheduling {name}: {e}")
