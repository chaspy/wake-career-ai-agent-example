from pathlib import Path
from app.main import ingest_articles, ARTICLES_DIR, VSTORE_DIR

if __name__ == "__main__":
    ingest_articles(ARTICLES_DIR, VSTORE_DIR)
    print(f"vectorstore saved to {VSTORE_DIR}")
