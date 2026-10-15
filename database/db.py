import sqlite3
import os
import re
import logging
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

# Try importing mysql.connector
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    MySQLError = Exception

_active_engine = None  # 'mysql' or 'sqlite'

def test_mysql_connection():
    """Test if MySQL server is reachable with configured credentials."""
    if not MYSQL_AVAILABLE:
        return False
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            connection_timeout=2
        )
        if conn.is_connected():
            conn.close()
            return True
    except Exception as e:
        logger.debug(f"MySQL connection check failed: {e}")
        return False
    return False

def get_active_engine():
    """Determine the active database engine based on config and availability."""
    global _active_engine
    if _active_engine is not None:
        return _active_engine

    if Config.DB_ENGINE == 'mysql':
        _active_engine = 'mysql'
    elif Config.DB_ENGINE == 'sqlite':
        _active_engine = 'sqlite'
    else:  # 'auto'
        if test_mysql_connection():
            _active_engine = 'mysql'
            logger.info("Auto-detected MySQL server. Using MySQL database engine.")
        else:
            _active_engine = 'sqlite'
            logger.info("MySQL server not detected or offline. Using local SQLite database engine fallback.")
    return _active_engine

class SQLiteDictCursor:
    """Wrapper to make SQLite cursor behave similarly to MySQL dictionary cursor."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        # Convert %s to ? for SQLite compatibility
        sqlite_query = re.sub(r'%s', '?', query)
        if params is None:
            return self._cursor.execute(sqlite_query)
        return self._cursor.execute(sqlite_query, params)

    def executemany(self, query, seq_of_params):
        sqlite_query = re.sub(r'%s', '?', query)
        return self._cursor.executemany(sqlite_query, seq_of_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

class DatabaseConnection:
    """Encapsulates a database connection to provide a unified interface."""
    def __init__(self, engine, raw_conn):
        self.engine = engine
        self.raw_conn = raw_conn

    def cursor(self, dictionary=True):
        if self.engine == 'mysql':
            return self.raw_conn.cursor(dictionary=dictionary)
        else:
            raw_cur = self.raw_conn.cursor()
            return SQLiteDictCursor(raw_cur)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

def get_db_connection():
    """Establishes and returns a connection wrapper."""
    engine = get_active_engine()
    
    if engine == 'mysql':
        try:
            raw_conn = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                autocommit=False
            )
            return DatabaseConnection('mysql', raw_conn)
        except Exception as e:
            if Config.DB_ENGINE == 'auto':
                logger.warning(f"MySQL connection error ({e}). Falling back to SQLite.")
                # Switch to SQLite
                raw_conn = sqlite3.connect(Config.SQLITE_DB_PATH)
                raw_conn.row_factory = sqlite3.Row
                return DatabaseConnection('sqlite', raw_conn)
            raise e
    else:
        # SQLite
        os.makedirs(os.path.dirname(os.path.abspath(Config.SQLITE_DB_PATH)), exist_ok=True)
        raw_conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        raw_conn.row_factory = sqlite3.Row
        return DatabaseConnection('sqlite', raw_conn)

@contextmanager
def get_db():
    """Context manager for obtaining a database connection and cursor."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

@contextmanager
def transaction():
    """Context manager for explicit transaction handling."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def query_db(query, args=(), one=False, commit=False):
    """Executes a parameterized query safely."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, args)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return {'lastrowid': last_id, 'rowcount': affected}
        
        result = cursor.fetchall()
        return (result[0] if result else None) if one else result
    finally:
        cursor.close()
        conn.close()
