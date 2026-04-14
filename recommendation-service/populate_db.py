from neo4j import GraphDatabase
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Get the script's directory
SCRIPT_DIR = os.path.dirname(__file__)

# 🔐 Aura Credentials
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Validate credentials
if not URI or not USERNAME or not PASSWORD:
    print("Error: Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env or environment.")
    exit(1)

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

BATCH_SIZE = 1000


# =========================
# 0. CHECK FILES
# =========================

def check_files():
    files = ["movies.csv", "ratings.csv", "tags.csv", "links.csv"]
    for f in files:
        full_path = os.path.join(SCRIPT_DIR, f)
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            return False
    return True


# =========================
# 1. CREATE CONSTRAINTS
# =========================
def create_constraints():
    print("Creating constraints...")
    queries = [
        "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE",
        "CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movieId IS UNIQUE",
        "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)


# =========================
# 2. LOAD MOVIES
# =========================
def insert_movies(file_path):
    print("Inserting movies...")
    df = pd.read_csv(file_path)

    def batch_insert(tx, rows):
        tx.run("""
        UNWIND $rows AS row
        MERGE (m:Movie {movieId: row.movieId})
        SET m.title = row.title,
            m.genres = row.genres
        """, rows=rows)

    with driver.session() as session:
        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]

            rows = [
                {
                    "movieId": int(r["movieId"]),
                    "title": r["title"],
                    "genres": r["genres"]
                }
                for _, r in batch.iterrows()
            ]

            session.execute_write(batch_insert, rows)
            print(f"Movies inserted: {i}")


# =========================
# 3. CREATE GENRES
# =========================
def create_genres():
    print("Creating genres and relationships...")

    query = """
    MATCH (m:Movie)
    WHERE m.genres IS NOT NULL AND m.genres <> '(no genres listed)'
    WITH m, split(m.genres, '|') AS genres
    UNWIND genres AS genre
    MERGE (g:Genre {name: genre})
    MERGE (m)-[:IN_GENRE]->(g)
    """
    with driver.session() as session:
        session.run(query)
    print("Genres created")


# =========================
# 4. LOAD RATINGS
# =========================
def insert_ratings(file_path):
    print("Inserting ratings...")

    df = pd.read_csv(file_path)

    # 🔥 Filter for neo4j Aura to reduce nodes and relationship limit
    # df = df[df["rating"] >= 3.0 and df["rating"] <= 4.0]

    def batch_insert(tx, rows):
        tx.run("""
        UNWIND $rows AS row
        MERGE (u:User {userId: row.userId})
        MERGE (m:Movie {movieId: row.movieId})
        MERGE (u)-[r:RATED]->(m)
        SET r.rating = row.rating,
            r.timestamp = row.timestamp
        """, rows=rows)

    with driver.session() as session:
        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]

            rows = [
                {
                    "userId": int(r["userId"]),
                    "movieId": int(r["movieId"]),
                    "rating": float(r["rating"]),
                    "timestamp": int(r["timestamp"])
                }
                for _, r in batch.iterrows()
            ]

            session.execute_write(batch_insert, rows)
            print(f"Ratings inserted: {i}")


# =========================
# 5. LOAD TAGS
# =========================
def insert_tags(file_path):
    print("Inserting tags...")

    df = pd.read_csv(file_path)

    def batch_insert(tx, rows):
        tx.run("""
        UNWIND $rows AS row
        MERGE (u:User {userId: row.userId})
        MERGE (m:Movie {movieId: row.movieId})
        MERGE (u)-[t:TAGGED]->(m)
        SET t.tag = row.tag,
            t.timestamp = row.timestamp
        """, rows=rows)

    with driver.session() as session:
        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]

            rows = [
                {
                    "userId": int(r["userId"]),
                    "movieId": int(r["movieId"]),
                    "tag": r["tag"],
                    "timestamp": int(r["timestamp"])
                }
                for _, r in batch.iterrows()
            ]

            session.execute_write(batch_insert, rows)
            print(f"Tags inserted: {i}")


# =========================
# 6. LOAD LINKS
# =========================
def insert_links(file_path):
    print("Inserting links...")

    df = pd.read_csv(file_path)

    def batch_insert(tx, rows):
        tx.run("""
        UNWIND $rows AS row
        MERGE (m:Movie {movieId: row.movieId})
        SET m.imdbId = row.imdbId,
            m.tmdbId = row.tmdbId
        """, rows=rows)

    with driver.session() as session:
        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]

            rows = [
                {
                    "movieId": int(r["movieId"]),
                    "imdbId": int(r["imdbId"]),
                    "tmdbId": None if pd.isna(r["tmdbId"]) else int(r["tmdbId"])
                }
                for _, r in batch.iterrows()
            ]

            session.execute_write(batch_insert, rows)
            print(f"Links inserted: {i}")


# =========================
# MAIN EXECUTION ORDER
# =========================
if __name__ == "__main__":
    if not check_files():
        print("One or more required files are missing. Please ensure 'movies.csv', 'ratings.csv', 'tags.csv', and 'links.csv' are in the current directory.")
        exit(1)
    
    start_time = time.time()
    create_constraints()

    insert_movies(os.path.join(SCRIPT_DIR, "movies.csv"))
    create_genres()

    insert_ratings(os.path.join(SCRIPT_DIR, "ratings.csv"))
    insert_tags(os.path.join(SCRIPT_DIR, "tags.csv"))
    insert_links(os.path.join(SCRIPT_DIR, "links.csv"))

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time for bulk upload: {:.2f} seconds".format(elapsed_time))

    driver.close()