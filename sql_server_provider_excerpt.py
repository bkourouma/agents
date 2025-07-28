# SQL Server Provider Implementation (Key Methods)

class SQLServerProvider(DatabaseProvider):
    """SQL Server database provider."""
    
    def build_connection_string(self) -> str:
        """Build SQL Server connection string."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 1433)
        database = self.config.get("database", "master")
        username = self.config.get("username", "sa")
        password = self.config.get("password", "")
        
        # Try different ODBC drivers in order of preference
        try:
            import pyodbc
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server", 
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]
            
            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None
            
            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break
            
            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    driver = "ODBC Driver 17 for SQL Server"  # Fallback
            
            # URL encode the driver name for the connection string
            encoded_driver = urllib.parse.quote_plus(driver)
            
        except ImportError:
            # Fallback if pyodbc not available
            encoded_driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")
        
        conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={encoded_driver}&TrustServerCertificate=yes&Encrypt=no"
        self.connection_string = conn_str
        return conn_str
    
    async def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test SQL Server connection."""
        try:
            import pyodbc
            import asyncio
            
            if not self.connection_string:
                self.build_connection_string()
            
            # Extract connection parameters for pyodbc
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 1433)
            database = self.config.get("database", "master")
            username = self.config.get("username", "")
            password = self.config.get("password", "")
            
            # Try different ODBC drivers in order of preference
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server", 
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]
            
            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None
            
            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break
            
            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    raise Exception("No SQL Server ODBC drivers found. Please install Microsoft ODBC Driver for SQL Server.")
            
            conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Encrypt=no"
            
            # Test connection in a thread since pyodbc is synchronous
            def test_sync():
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, test_sync)
            
            return True, "Connection successful", None
            
        except ImportError:
            return False, "pyodbc driver not installed. Please install: pip install pyodbc", {"error": "Missing driver"}
        except Exception as e:
            error_msg = str(e)
            # Check for specific error types
            if "timeout" in error_msg.lower() or "wait operation timed out" in error_msg.lower():
                return False, f"Connection timeout: Server not reachable or not responding. Check hostname, port, and server status.", {"error": error_msg}
            elif "server is unavailable" in error_msg.lower() or "server not found" in error_msg.lower() or "introuvable" in error_msg.lower():
                return False, f"Server not found: Check hostname and port. Ensure SQL Server is running and accessible.", {"error": error_msg}
            elif "login failed" in error_msg.lower() or "cannot open database" in error_msg.lower():
                return False, f"Authentication or database access failed: {error_msg}", {"error": error_msg}
            elif "no driver" in error_msg.lower() or "driver not found" in error_msg.lower():
                return False, "ODBC Driver not found. Please install Microsoft ODBC Driver for SQL Server.", {"error": error_msg}
            else:
                return False, f"Connection failed: {error_msg}", {"error": error_msg}
