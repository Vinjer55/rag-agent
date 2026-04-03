import redis
import os
import json

from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=6379,
    decode_responses=True
)

def get_conversation_history(session_id: str, max_turns: int = 10):
    key = f"conversation:{session_id}"
    history = redis_client.get(key)
    
    if not history:
        return []
    
    messages = json.loads(history)
    # Return last N turns only (keeps context manageable)
    return messages[-(max_turns * 2):]  # *2 because user+assistant = 1 turn

def save_conversation_turn(session_id: str, user_msg: str, assistant_msg: str):
    key = f"conversation:{session_id}"
    
    # Get existing history
    history = get_conversation_history(session_id, max_turns=50)
    
    # Add new turn
    history.extend([
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": assistant_msg}
    ])
    
    # Save with 24-hour expiration
    redis_client.setex(
        key,
        timedelta(hours=24),
        json.dumps(history)
    )