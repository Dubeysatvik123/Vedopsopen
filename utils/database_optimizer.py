"""
Database optimization utilities for VedOps
"""

import sqlite3
import threading
import logging
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
import time
from .performance import profile, cached

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database performance optimization utilities"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.max_connections = 10
        self.query_cache = {}
        self.cache_lock = threading.Lock()
        
        # Initialize connection pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize database connection pool"""
        with self.pool_lock:
            for _ in range(self.max_connections):
                conn = self._create_optimized_connection()
                self.connection_pool.append(conn)
    
    def _create_optimized_connection(self) -> sqlite3.Connection:
        """Create optimized database connection"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode
        )
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Optimize for performance
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get optimized database connection from pool"""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    conn = self._create_optimized_connection()
            
            yield conn
            
        finally:
            if conn:
                with self.pool_lock:
                    if len(self.connection_pool) < self.max_connections:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()
    
    @profile("database_query")
    def execute_query(self, query: str, params: tuple = None, 
                     fetch_one: bool = False, fetch_all: bool = True) -> Any:
        """Execute optimized database query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            start_time = time.perf_counter()
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            duration = time.perf_counter() - start_time
            
            # Log slow queries
            if duration > 1.0:  # Queries taking more than 1 second
                logger.warning(f"Slow query ({duration:.2f}s): {query[:100]}...")
            
            return result
    
    @cached(ttl=300)  # Cache for 5 minutes
    def execute_cached_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query with caching for read-only operations"""
        result = self.execute_query(query, params, fetch_all=True)
        return [dict(row) for row in result] if result else []
    
    def execute_batch(self, query: str, param_list: List[tuple]) -> int:
        """Execute batch operations efficiently"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            return cursor.rowcount
    
    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """Execute multiple operations in a transaction"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                
                for op in operations:
                    query = op['query']
                    params = op.get('params', ())
                    conn.execute(query, params)
                
                conn.execute("COMMIT")
                return True
                
            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Transaction failed: {e}")
                raise
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze database performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get database stats
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            
            # Get table stats
            cursor.execute("""
                SELECT name, COUNT(*) as row_count 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            table_stats = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                table_stats[table_name] = row_count
            
            return {
                'database_size_mb': (page_count * page_size) / (1024 * 1024),
                'page_count': page_count,
                'page_size': page_size,
                'cache_size': cache_size,
                'table_stats': table_stats,
                'connection_pool_size': len(self.connection_pool)
            }
    
    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization operations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            start_time = time.perf_counter()
            
            # Analyze tables
            cursor.execute("ANALYZE")
            
            # Vacuum database
            cursor.execute("VACUUM")
            
            # Reindex
            cursor.execute("REINDEX")
            
            duration = time.perf_counter() - start_time
            
            logger.info(f"Database optimization completed in {duration:.2f}s")
            
            return {
                'optimization_duration': duration,
                'operations': ['ANALYZE', 'VACUUM', 'REINDEX']
            }
    
    def create_indexes(self, index_definitions: List[Dict[str, str]]):
        """Create database indexes for performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for index_def in index_definitions:
                index_name = index_def['name']
                table_name = index_def['table']
                columns = index_def['columns']
                unique = index_def.get('unique', False)
                
                unique_clause = "UNIQUE " if unique else ""
                
                try:
                    cursor.execute(f"""
                        CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} ({columns})
                    """)
                    logger.info(f"Created index {index_name} on {table_name}({columns})")
                    
                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
    
    def get_query_plan(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Get query execution plan for optimization"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query, params or ())
            
            plan = cursor.fetchall()
            return [dict(row) for row in plan]
    
    def cleanup_old_data(self, table_name: str, date_column: str, 
                        days_to_keep: int) -> int:
        """Cleanup old data efficiently"""
        query = f"""
            DELETE FROM {table_name} 
            WHERE {date_column} < datetime('now', '-{days_to_keep} days')
        """
        
        result = self.execute_query(query, fetch_all=False)
        logger.info(f"Cleaned up {result} old records from {table_name}")
        
        return result
    
    def close_all_connections(self):
        """Close all connections in pool"""
        with self.pool_lock:
            for conn in self.connection_pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            self.connection_pool.clear()
