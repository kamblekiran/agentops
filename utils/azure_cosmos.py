import datetime
import os
from azure.cosmos import CosmosClient, PartitionKey
from config import is_simulation_mode
from dotenv import load_dotenv

load_dotenv()

def get_cosmos_client():
    """Initialize Azure Cosmos DB client"""
    endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
    key = os.getenv("AZURE_COSMOS_KEY")
    
    if not endpoint or not key:
        raise ValueError("Azure Cosmos DB endpoint and key must be set")
    
    return CosmosClient(endpoint, key)

def get_database_and_container():
    """Get or create database and container"""
    client = get_cosmos_client()
    
    database_name = "agentops"
    container_name = "sessions"
    
    # Create database if it doesn't exist
    database = client.create_database_if_not_exists(id=database_name)
    
    # Create container if it doesn't exist
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/session_id"),
        offer_throughput=400
    )
    
    return database, container

def log_session(session_id: str, agent: str, data: dict):
    """Log session data to Azure Cosmos DB"""
    if is_simulation_mode():
        return  # Don't log in simulation mode

    try:
        _, container = get_database_and_container()
        
        # Create document structure
        document = {
            "id": f"{session_id}_{agent}",
            "session_id": session_id,
            "agent": agent,
            "data": data,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        container.upsert_item(document)
    except Exception as e:
        print(f"Error logging to Cosmos DB: {e}")

def fetch_agent_history(agent: str, limit=5):
    """Fetch agent history from Azure Cosmos DB"""
    if is_simulation_mode():
        return [{
            "session_id": "mock-session",
            "timestamp": "2025-06-22T17:22:21Z",
            "data": {
                "output": f"Mock output for {agent} #0"
            }
        }]

    try:
        _, container = get_database_and_container()
        
        query = f"SELECT * FROM c WHERE c.agent = '{agent}' ORDER BY c.timestamp DESC OFFSET 0 LIMIT {limit}"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        results = []
        for item in items:
            results.append({
                "session_id": item["session_id"],
                "timestamp": item["timestamp"],
                "data": item["data"]
            })
        
        return results
    except Exception as e:
        print(f"Error fetching from Cosmos DB: {e}")
        return []

def fetch_all_sessions():
    """Fetch all sessions from Azure Cosmos DB"""
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
    
    try:
        _, container = get_database_and_container()
        
        query = "SELECT * FROM c ORDER BY c.timestamp DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Group by session_id
        sessions = {}
        for item in items:
            session_id = item["session_id"]
            agent = item["agent"]
            
            if session_id not in sessions:
                sessions[session_id] = {"agents": {}}
            
            sessions[session_id]["agents"][agent] = item["data"]
        
        return sessions
    except Exception as e:
        print(f"Error fetching all sessions from Cosmos DB: {e}")
        return {}