# session.py

import uuid
import datetime

def create_session_id():
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"session_{timestamp}_{uuid.uuid4().hex[:6]}"

def get_current_timestamp():
    return datetime.datetime.utcnow().isoformat() + "Z"