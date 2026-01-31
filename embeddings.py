import struct
import sqlite_vec
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def get_embedding(text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


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
