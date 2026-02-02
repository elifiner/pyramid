import json
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

DEFAULT_OPENCLAW_PATH = Path.home() / '.openclaw' / 'agents' / 'main' / 'sessions'


def get_week_key(timestamp_str):
    if not timestamp_str:
        return 'unknown'
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    year, week, _ = dt.isocalendar()
    return f'{year}-W{week:02d}'


def group_messages_by_week(messages):
    by_week = {}
    for msg in messages:
        week = get_week_key(msg.get('timestamp', ''))
        if week not in by_week:
            by_week[week] = []
        by_week[week].append(msg)
    return by_week


def load_glenn_messages(source, conversation=None, user=None, limit=None):
    source_engine = create_engine(f'sqlite:///{source}')
    
    user_id = None
    user_info = None
    if user:
        with source_engine.connect() as conn:
            result = conn.execute(text("SELECT id FROM users WHERE LOWER(username) = :username"), {'username': user.lower()})
            row = result.fetchone()
            if not row:
                return [], f"User '{user}' not found in source database"
            user_id = row[0]
            user_info = f"Filtering for user '{user}' (id={user_id})"
    
    if user_id:
        query = """SELECT m.role, m.content, m.timestamp 
                   FROM messages m 
                   JOIN conversations c ON m.conversation_id = c.id 
                   WHERE m.content IS NOT NULL AND m.content != '' AND c.user_id = :user_id"""
    else:
        query = "SELECT role, content, timestamp FROM messages WHERE content IS NOT NULL AND content != ''"
    
    if conversation:
        query += f" AND conversation_id = {conversation}"
    query += " ORDER BY timestamp"
    if limit:
        query += f" LIMIT {limit}"
    
    with source_engine.connect() as conn:
        if user_id:
            result = conn.execute(text(query), {'user_id': user_id})
        else:
            result = conn.execute(text(query))
        messages = [{'role': row[0], 'content': row[1], 'timestamp': row[2]} for row in result]
    
    return messages, user_info


def load_claude_messages(source, limit=None):
    with open(source) as f:
        data = json.load(f)
    
    messages = []
    for conv in data:
        for msg in conv.get('chat_messages', []):
            sender = msg.get('sender', '')
            role = 'user' if sender == 'human' else 'assistant'
            timestamp = msg.get('created_at', '')
            
            content_parts = []
            for content in msg.get('content', []):
                if content.get('type') == 'text' and content.get('text'):
                    content_parts.append(content['text'])
            
            if content_parts:
                messages.append({
                    'role': role,
                    'content': '\n'.join(content_parts),
                    'timestamp': timestamp
                })
    
    messages.sort(key=lambda m: m.get('timestamp', ''))
    if limit:
        messages = messages[:limit]
    return messages, None


def load_openclaw_messages(source=None, limit=None):
    source_path = Path(source) if source else DEFAULT_OPENCLAW_PATH
    
    if source_path.is_file():
        session_files = [source_path]
    else:
        session_files = sorted(source_path.glob('*.jsonl'))
    
    messages = []
    for session_file in session_files:
        with open(session_file) as f:
            for line in f:
                record = json.loads(line)
                if record.get('type') != 'message':
                    continue
                
                msg = record.get('message', {})
                role = msg.get('role', '')
                if role not in ('user', 'assistant'):
                    continue
                
                content_parts = []
                for content in msg.get('content', []):
                    if content.get('type') == 'text' and content.get('text'):
                        content_parts.append(content['text'])
                
                if not content_parts:
                    continue
                
                ts_ms = msg.get('timestamp')
                if ts_ms:
                    timestamp = datetime.fromtimestamp(ts_ms / 1000).isoformat()
                else:
                    timestamp = record.get('timestamp', '')
                
                messages.append({
                    'role': role,
                    'content': '\n'.join(content_parts),
                    'timestamp': timestamp
                })
    
    messages.sort(key=lambda m: m.get('timestamp', ''))
    if limit:
        messages = messages[:limit]
    return messages, None
