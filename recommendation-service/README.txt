# Movie Recommendation Service Database Scripts

This folder contains two Python scripts for managing a Neo4j database with movie recommendation data.

## Scripts

### 1. populate_db.py

**Purpose:**  
Populates a Neo4j graph database with movie recommendation data from CSV files. The script creates nodes for Users, Movies, and Genres, and relationships for ratings and tags.

**What it does:**
- Creates database constraints for unique IDs
- Loads movies with titles and genres
- Creates genre nodes and relationships
- Loads user ratings and creates User-Movie relationships
- Loads user tags and creates tagging relationships
- Adds external links (IMDB, TMDB) to movies

**Requirements:**
- Python 3.x
- Neo4j database (local or Aura)
- Required packages: neo4j, pandas, python-dotenv
- CSV data files (see below)

**How to run:**
1. Ensure you have a `.env` file in the parent directory with:
   ```
   NEO4J_URI=your_neo4j_connection_uri
   NEO4J_USERNAME=your_username
   NEO4J_PASSWORD=your_password
   ```
2. Place the required CSV files in this directory
3. Run: `python populate_db.py`

### 2. clear_db.py

**Purpose:**  
Completely clears all data from the Neo4j database, including nodes, relationships, constraints, and indexes.

**What it does:**
- Drops all constraints
- Drops all indexes
- Deletes all relationships in batches
- Deletes all nodes in batches
- Provides progress updates and final verification

**Requirements:**
- Python 3.x
- Neo4j database connection
- Required packages: neo4j, python-dotenv

**How to run:**
1. Ensure you have a `.env` file with Neo4j credentials (same as above)
2. Run: `python clear_db.py`
3. The script will warn you and ask for confirmation before proceeding

**⚠️ Warning:** This script will permanently delete ALL data in your database. Use with caution!

## Required CSV Files

The following CSV files must be present in the `recommendation-service/` directory for `populate_db.py` to work:

1. **movies.csv** - Movie information (movieId, title, genres)
2. **ratings.csv** - User ratings (userId, movieId, rating, timestamp)
3. **tags.csv** - User tags (userId, movieId, tag, timestamp)
4. **links.csv** - External links (movieId, imdbId, tmdbId)

### Downloading the Data

These files are from the MovieLens dataset provided by GroupLens Research.

**Download location:** https://grouplens.org/datasets/movielens/

**Recommended datasets:**
- **ml-latest-small.zip** (for testing/small scale): ~1MB, contains 100,000 ratings
- **ml-latest.zip** (full dataset): ~300MB, contains ~33 million ratings

After downloading and extracting, copy the CSV files to this directory.

**Note:** The `ratings.csv` and `tags.csv` files from the full dataset are very large and are not included in this repository's git history due to GitHub's file size limits. You must download them separately.

## Installation

Install required Python packages:

```bash
pip install neo4j pandas python-dotenv
```

## Database Setup

You can use either:
- **Neo4j Desktop** (local installation)
- **Neo4j Aura** (cloud-hosted)

For Neo4j Aura, get your connection details from the Aura console and set them in the `.env` file.

## Example Usage

```bash
# Clear existing data (optional)
python clear_db.py

# Populate with new data
python populate_db.py
```

The scripts will provide progress updates during execution.