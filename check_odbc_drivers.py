#!/usr/bin/env python3
"""
Check available ODBC drivers on the system
"""

try:
    import pyodbc
    
    print("Available ODBC drivers:")
    drivers = pyodbc.drivers()
    
    for i, driver in enumerate(drivers, 1):
        print(f"{i}. {driver}")
    
    print(f"\nTotal drivers found: {len(drivers)}")
    
    # Check specifically for SQL Server drivers
    sql_server_drivers = [x for x in drivers if 'SQL Server' in x]
    print(f"\nSQL Server drivers found: {len(sql_server_drivers)}")
    for driver in sql_server_drivers:
        print(f"  - {driver}")
        
    if not sql_server_drivers:
        print("\nNo SQL Server ODBC drivers found!")
        print("You need to install Microsoft ODBC Driver for SQL Server.")
        print("Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
    
except ImportError:
    print("pyodbc is not installed. Run: pip install pyodbc")
except Exception as e:
    print(f"Error checking drivers: {e}")
