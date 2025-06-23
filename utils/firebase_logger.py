import datetime
from google.cloud import firestore
from config import is_simulation_mode

def get_firestore_client():
    return firestore.Client()

def log_session(session_id: str, agent: str, data: dict):
    if is_simulation_mode():
        return  # Don't log in simulation mode

    db = get_firestore_client()
    doc_ref = db.collection("agentops_sessions").document(session_id)

    # Safely merge agent-specific log into `agents` map
    doc_ref.set({
        "agents": {agent: data},
        "timestamp": datetime.datetime.utcnow()
    }, merge=True)

def fetch_agent_history(agent: str, limit=5):
    if is_simulation_mode():
        return [{
            "session_id": "mock-session",
            "timestamp": "2025-06-22 17:22:21",
            "data": {
                "output": f"Mock output for {agent} #0"
            }
        }]

    db = get_firestore_client()
    sessions = db.collection("agentops_sessions")\
                 .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                 .limit(limit).stream()

    results = []
    for session in sessions:
        data = session.to_dict()
        agents = data.get("agents", {})
        if agent in agents:
            results.append({
                "session_id": session.id,
                "timestamp": data.get("timestamp"),
                "data": agents.get(agent)
            })
    return results

def fetch_all_sessions():
    if is_simulation_mode():
        return {
            "mock-session": {
                "agents": {
                    "code_review": {
                        "timestamp": "2025-06-22T17:22:21Z",
                        "status": "✅ Simulated",
                        "output": {"review": "Sample mock review"},
                        "input": {"repo_url": "https://github.com/user/mock"}
                    }
                }
            }
        }
    else:
        db = get_firestore_client()
        sessions = db.collection("agentops_sessions")\
                    .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                    .stream()
        

        results = {}
        for doc in sessions:

            data = doc.to_dict()
            if "agents" in data:
                print(data["agents"])
                results[doc.id] = { 
                    "agents": data["agents"]
                }
        return results
