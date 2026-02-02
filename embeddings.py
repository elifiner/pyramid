import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite_vec
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


MAX_TOKENS_PER_REQUEST = 250000
CHARS_PER_TOKEN = 4


def estimate_tokens(text):
    return len(text) // CHARS_PER_TOKEN


def get_embedding(text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def get_embeddings_batch(texts):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def batch_by_tokens(texts, max_tokens=MAX_TOKENS_PER_REQUEST):
    batches = []
    current_batch = []
    current_tokens = 0
    
    for text in texts:
        tokens = estimate_tokens(text)
        if current_tokens + tokens > max_tokens and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(text)
        current_tokens += tokens
    
    if current_batch:
        batches.append(current_batch)
    
    return batches


def embed_many(texts, max_workers=10, on_progress=None):
    batches = batch_by_tokens(texts)
    results = [None] * len(batches)
    completed = 0
    
    def process_batch(batch_idx):
        return batch_idx, get_embeddings_batch(batches[batch_idx])
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, i) for i in range(len(batches))]
        for future in as_completed(futures):
            batch_idx, embeddings = future.result()
            results[batch_idx] = embeddings
            completed += len(embeddings)
            if on_progress:
                on_progress(completed, len(texts))
    
    return [emb for batch in results for emb in batch]


def serialize_embedding(embedding):
    return struct.pack(f'{len(embedding)}f', *embedding)


def deserialize_embedding(blob):
    count = len(blob) // 4
    return list(struct.unpack(f'{count}f', blob))


def enable_vec(conn):
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)


def create_vec_table(conn, table_name, dim=EMBEDDING_DIM):
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {table_name}_vec USING vec0(
            embedding float[{dim}]
        )
    """)


def search_similar(conn, table_name, query_embedding, limit=10):
    query_blob = serialize_embedding(query_embedding)
    
    results = conn.execute(f"""
        SELECT rowid, distance
        FROM {table_name}_vec
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
    """, [query_blob, limit]).fetchall()
    
    return results


def init_memory_vec(conn):
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS memory_vec USING vec0(
            id INTEGER PRIMARY KEY,
            source_type TEXT,
            source_id INTEGER,
            embedding float[{EMBEDDING_DIM}]
        )
    """)


def get_existing_embeddings(conn):
    return set(
        (row[0], row[1]) 
        for row in conn.execute("SELECT source_type, source_id FROM memory_vec").fetchall()
    )


def store_embeddings(conn, items, embeddings):
    for i, (source_type, source_id, _) in enumerate(items):
        conn.execute(
            "INSERT INTO memory_vec (source_type, source_id, embedding) VALUES (?, ?, ?)",
            [source_type, source_id, serialize_embedding(embeddings[i])]
        )
    conn.commit()


def search_memory(conn, query_text, limit=20):
    query_embedding = get_embedding(query_text)
    results = conn.execute("""
        SELECT source_type, source_id, distance
        FROM memory_vec
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
    """, [serialize_embedding(query_embedding), limit]).fetchall()
    return results
