"""
Add embedding column to knowledge_base_documents table.
"""

import sqlite3
import os

def add_embedding_column():
    """Add embedding column to knowledge_base_documents table."""
    
    # Get database path
    db_path = "ai_agents.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Creating new database with embedding column.")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if embedding column already exists
        cursor.execute("PRAGMA table_info(knowledge_base_documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'embedding' in columns:
            print("Embedding column already exists in knowledge_base_documents table.")
            return
        
        # Add embedding column
        print("Adding embedding column to knowledge_base_documents table...")
        cursor.execute("""
            ALTER TABLE knowledge_base_documents 
            ADD COLUMN embedding TEXT
        """)
        
        conn.commit()
        print("Successfully added embedding column.")
        
    except Exception as e:
        print(f"Error adding embedding column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_embedding_column()
