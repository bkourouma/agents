#!/usr/bin/env python3
"""
Analyser les transactions MoMoney.
"""

import sqlite3
import json
from datetime import datetime

def analyze_momoney_transactions():
    """Analyser les transactions MoMoney."""
    print("📊 Analyse des transactions MoMoney")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_agent_platform.db')
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("PRAGMA table_info(transactionsmobiles)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"📋 Colonnes de la table: {column_names}")
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM transactionsmobiles")
        total = cursor.fetchone()[0]
        print(f"\n📈 Total des transactions: {total}")
        
        # Transactions par réseau
        cursor.execute("""
            SELECT network, COUNT(*) as count, SUM(amount) as total_amount
            FROM transactionsmobiles
            GROUP BY network
            ORDER BY count DESC
        """)
        networks = cursor.fetchall()
        print(f"\n📱 Transactions par réseau:")
        for net in networks:
            print(f"  - {net[0]}: {net[1]} transactions, {net[2]:,.0f} FCFA")

        # Transactions par type
        cursor.execute("""
            SELECT transactiontype, COUNT(*) as count, SUM(amount) as total_amount
            FROM transactionsmobiles
            GROUP BY transactiontype
            ORDER BY count DESC
        """)
        types = cursor.fetchall()
        print(f"\n💰 Transactions par type:")
        for t in types:
            print(f"  - {t[0]}: {t[1]} transactions, {t[2]:,.0f} FCFA")
        
        # Statistiques des montants
        cursor.execute("""
            SELECT 
                MIN(amount) as min_amount,
                MAX(amount) as max_amount,
                AVG(amount) as avg_amount,
                SUM(amount) as total_amount
            FROM transactionsmobiles
        """)
        stats = cursor.fetchone()
        print(f"\n💵 Statistiques des montants:")
        print(f"  - Montant minimum: {stats[0]:,.0f} FCFA")
        print(f"  - Montant maximum: {stats[1]:,.0f} FCFA")
        print(f"  - Montant moyen: {stats[2]:,.0f} FCFA")
        print(f"  - Montant total: {stats[3]:,.0f} FCFA")
        
        # Transactions récentes
        cursor.execute("""
            SELECT transactionid, network, transactiontype, timestamp, amount
            FROM transactionsmobiles
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        print(f"\n🕒 10 transactions les plus récentes:")
        for r in recent:
            print(f"  - {r[0]}: {r[1]} {r[2]} - {r[4]:,.0f} FCFA ({r[3]})")
        
        # Transactions par jour (derniers jours)
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM transactionsmobiles 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """)
        daily = cursor.fetchall()
        print(f"\n📅 Transactions par jour (7 derniers jours):")
        for d in daily:
            print(f"  - {d[0]}: {d[1]} transactions, {d[2]:,.0f} FCFA")
        
        # Top 10 des plus gros montants
        cursor.execute("""
            SELECT transactionid, network, transactiontype, amount, timestamp
            FROM transactionsmobiles
            ORDER BY amount DESC
            LIMIT 10
        """)
        top_amounts = cursor.fetchall()
        print(f"\n🏆 Top 10 des plus gros montants:")
        for i, t in enumerate(top_amounts, 1):
            print(f"  {i}. {t[0]}: {t[1]} {t[2]} - {t[3]:,.0f} FCFA ({t[4]})")
        
        conn.close()
        print(f"\n✅ Analyse terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_momoney_transactions()
