from neo4j import GraphDatabase
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the script's directory to find .env file
SCRIPT_DIR = os.path.dirname(__file__)

# 🔐 Neo4j Credentials
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# Validate credentials
if not URI or not USERNAME or not PASSWORD:
    print("Error: Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in .env or environment.")
    exit(1)

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

BATCH_SIZE = 10000  # Delete in batches of 10,000 to avoid memory issues


def get_node_count():
    """Get total count of nodes in the database"""
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        return result.single()["count"]


def get_relationship_count():
    """Get total count of relationships in the database"""
    with driver.session() as session:
        result = session.run("MATCH ()-[r]-() RETURN count(r) as count")
        return result.single()["count"]


def delete_relationships_in_batches():
    """Delete all relationships in batches"""
    print("Deleting relationships in batches...")

    with driver.session() as session:
        total_deleted = 0
        while True:
            result = session.run(f"""
                MATCH ()-[r]-()
                WITH r LIMIT {BATCH_SIZE}
                DELETE r
                RETURN count(r) as deleted
            """)

            deleted = result.single()["deleted"]
            total_deleted += deleted

            if deleted > 0:
                print(f"  Deleted {deleted} relationships (total: {total_deleted})")
            else:
                break

        print(f"✅ All relationships deleted. Total: {total_deleted}")


def delete_nodes_in_batches():
    """Delete all nodes in batches"""
    print("Deleting nodes in batches...")

    with driver.session() as session:
        total_deleted = 0
        while True:
            result = session.run(f"""
                MATCH (n)
                WITH n LIMIT {BATCH_SIZE}
                DELETE n
                RETURN count(n) as deleted
            """)

            deleted = result.single()["deleted"]
            total_deleted += deleted

            if deleted > 0:
                print(f"  Deleted {deleted} nodes (total: {total_deleted})")
            else:
                break

        print(f"✅ All nodes deleted. Total: {total_deleted}")


def drop_all_constraints():
    """Drop all constraints in the database"""
    print("Dropping all constraints...")

    with driver.session() as session:
        # Get all constraints
        result = session.run("SHOW CONSTRAINTS")
        constraints = list(result)

        if not constraints:
            print("  No constraints found.")
            return

        dropped_count = 0
        for record in constraints:
            constraint_name = record["name"]
            try:
                session.run(f"DROP CONSTRAINT {constraint_name}")
                print(f"  Dropped constraint: {constraint_name}")
                dropped_count += 1
            except Exception as e:
                print(f"  Failed to drop constraint {constraint_name}: {e}")

        print(f"✅ Dropped {dropped_count} constraints.")


def drop_all_indexes():
    """Drop all indexes (optional, but good practice before bulk operations)"""
    print("Dropping all indexes...")

    with driver.session() as session:
        # Get all indexes (excluding system indexes)
        result = session.run("SHOW INDEXES WHERE type <> 'LOOKUP'")
        indexes = list(result)

        if not indexes:
            print("  No indexes found.")
            return

        dropped_count = 0
        for record in indexes:
            index_name = record["name"]
            try:
                session.run(f"DROP INDEX {index_name}")
                print(f"  Dropped index: {index_name}")
                dropped_count += 1
            except Exception as e:
                print(f"  Failed to drop index {index_name}: {e}")

        print(f"✅ Dropped {dropped_count} indexes.")


def main():
    """Main function to clear the entire database"""
    print("🚨 WARNING: This will delete ALL data from your Neo4j database!")
    print("Press Enter to continue or Ctrl+C to cancel...")

    try:
        input()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return

    print("\n" + "="*50)
    print("🗑️  STARTING DATABASE CLEAR OPERATION")
    print("="*50)

    try:
        # add time call here to measure total time taken for the operation
        start_time = time.time()
        # Get initial counts
        initial_nodes = get_node_count()
        initial_relationships = get_relationship_count()

        print(f"📊 Initial state: {initial_nodes} nodes, {initial_relationships} relationships")

        # Drop constraints first (to avoid conflicts)
        drop_all_constraints()

        # Drop indexes (optional but recommended)
        drop_all_indexes()

        # Delete data in batches
        delete_relationships_in_batches()
        delete_nodes_in_batches()

        # Final verification
        final_nodes = get_node_count()
        final_relationships = get_relationship_count()

        end_time = time.time()
        elapsed_time = end_time - start_time

        print("\n" + "="*50)
        print("✅ DATABASE CLEAR OPERATION COMPLETED")
        print("="*50)
        print(f"📊 Final state: {final_nodes} nodes, {final_relationships} relationships")
        print(f"⏱️  Elapsed time: {elapsed_time:.2f} seconds")

        if final_nodes == 0 and final_relationships == 0:
            print("🎉 Database is now completely empty!")
        else:
            print("⚠️  Warning: Some data may still remain. Check manually.")

    except Exception as e:
        print(f"❌ Error during database clear operation: {e}")
        print("The database may be in an inconsistent state.")

    finally:
        driver.close()
        print("🔒 Database connection closed.")


if __name__ == "__main__":
    main()
