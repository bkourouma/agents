#!/usr/bin/env python3
"""
Check SQL Server connectivity and configuration
"""

import socket
import subprocess
import sys

def check_port_open(host, port):
    """Check if a port is open on a host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def check_sql_server_services():
    """Check SQL Server Windows services"""
    try:
        # Check for SQL Server services
        result = subprocess.run(['sc', 'query', 'type=service', 'state=all'], 
                              capture_output=True, text=True, shell=True)
        
        services = result.stdout
        sql_services = []
        
        for line in services.split('\n'):
            if 'SQL' in line.upper() and 'SERVICE_NAME' in line:
                service_name = line.split(':')[1].strip()
                sql_services.append(service_name)
        
        return sql_services
    except Exception as e:
        print(f"Error checking services: {e}")
        return []

def main():
    print("=== SQL Server Connectivity Check ===\n")
    
    # Check common SQL Server ports
    hosts_to_check = ['localhost', '127.0.0.1']
    ports_to_check = [1433, 1434]
    
    print("1. Checking port connectivity:")
    for host in hosts_to_check:
        for port in ports_to_check:
            is_open = check_port_open(host, port)
            status = "OPEN" if is_open else "CLOSED"
            print(f"   {host}:{port} - {status}")
    
    print("\n2. Checking SQL Server services:")
    services = check_sql_server_services()
    if services:
        for service in services:
            print(f"   Found service: {service}")
    else:
        print("   No SQL Server services found")
    
    print("\n3. Common solutions:")
    print("   - Start SQL Server service in Windows Services")
    print("   - Enable TCP/IP in SQL Server Configuration Manager")
    print("   - Check SQL Server is listening on port 1433")
    print("   - Add Windows Firewall exception for port 1433")
    print("   - Try connecting with SQL Server Management Studio first")
    
    print("\n4. Alternative connection strings to try:")
    print("   - Use 127.0.0.1 instead of localhost")
    print("   - Try different ports (1434 for named instances)")
    print("   - Include instance name: localhost\\SQLEXPRESS")

if __name__ == "__main__":
    main()
