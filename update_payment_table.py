#!/usr/bin/env python3
"""
Update the payment table to allow NULL payment_date
"""

import sqlite3
import os

def update_payment_table():
    """Update the premium_payments table to allow NULL payment_date"""
    print("🔧 Updating Payment Table Schema")
    print("=" * 40)
    
    db_path = "insurance.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='premium_payments'")
        if not cursor.fetchone():
            print("❌ premium_payments table not found!")
            return
        
        print("✅ Found premium_payments table")
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(premium_payments)")
        columns = cursor.fetchall()
        print(f"📋 Current table structure:")
        for col in columns:
            print(f"   - {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Create new table with correct schema
        print("\n🔄 Creating new table with updated schema...")
        
        cursor.execute("""
            CREATE TABLE premium_payments_new (
                id TEXT PRIMARY KEY,
                contract_id TEXT,
                payment_date DATE,
                due_date DATE NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                transaction_id TEXT,
                late_fee REAL DEFAULT 0,
                grace_period_used BOOLEAN DEFAULT 0,
                processed_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES insurance_contracts(id)
            )
        """)
        
        # Copy existing data if any
        cursor.execute("SELECT COUNT(*) FROM premium_payments")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"📦 Copying {count} existing records...")
            cursor.execute("""
                INSERT INTO premium_payments_new 
                SELECT * FROM premium_payments
            """)
        else:
            print("📦 No existing records to copy")
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE premium_payments")
        cursor.execute("ALTER TABLE premium_payments_new RENAME TO premium_payments")
        
        conn.commit()
        print("✅ Table updated successfully!")
        
        # Verify the new structure
        cursor.execute("PRAGMA table_info(premium_payments)")
        new_columns = cursor.fetchall()
        print(f"\n📋 Updated table structure:")
        for col in new_columns:
            print(f"   - {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating table: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
    
    print(f"\n" + "=" * 40)
    print(f"🎉 Payment Table Update Complete!")

if __name__ == "__main__":
    update_payment_table()
