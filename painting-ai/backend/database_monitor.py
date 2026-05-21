"""
Database Monitoring Service for Painting.ai

Monitors:
- Connection pool usage
- Query execution times
- Slow queries (>1 second)
- Table sizes and growth
- Index usage statistics
- Dead tuples and vacuum needs

Can be run as:
1. Standalone monitoring service
2. Integrated into FastAPI app
3. Scheduled task for periodic checks
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Monitor database performance and health"""

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://paintingai:changeme123@localhost:5432/paintingai"
            )

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_pool_status(self) -> Dict:
        """Get current connection pool status"""
        pool = self.engine.pool

        status = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Calculate utilization percentage
        total = status["pool_size"] + status["overflow"]
        if total > 0:
            status["utilization_percent"] = (status["checked_out"] / total) * 100
        else:
            status["utilization_percent"] = 0

        return status

    def get_active_connections(self) -> List[Dict]:
        """Get list of active database connections"""
        query = text("""
            SELECT
                pid,
                usename,
                application_name,
                client_addr,
                state,
                query,
                state_change,
                now() - state_change AS duration
            FROM pg_stat_activity
            WHERE datname = current_database()
                AND pid != pg_backend_pid()
            ORDER BY state_change DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query)
            connections = []

            for row in result:
                connections.append({
                    "pid": row[0],
                    "user": row[1],
                    "application": row[2],
                    "client_addr": str(row[3]) if row[3] else None,
                    "state": row[4],
                    "query": row[5][:100] if row[5] else None,  # Truncate long queries
                    "state_change": row[6].isoformat() if row[6] else None,
                    "duration_seconds": row[7].total_seconds() if row[7] else 0
                })

            return connections

    def get_slow_queries(self, threshold_seconds: float = 1.0) -> List[Dict]:
        """Get currently running slow queries"""
        query = text("""
            SELECT
                pid,
                usename,
                state,
                query,
                now() - query_start AS duration
            FROM pg_stat_activity
            WHERE datname = current_database()
                AND state = 'active'
                AND query NOT LIKE '%pg_stat_activity%'
                AND now() - query_start > interval ':threshold seconds'
            ORDER BY duration DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query, {"threshold": threshold_seconds})
            slow_queries = []

            for row in result:
                slow_queries.append({
                    "pid": row[0],
                    "user": row[1],
                    "state": row[2],
                    "query": row[3],
                    "duration_seconds": row[4].total_seconds() if row[4] else 0
                })

            return slow_queries

    def get_table_sizes(self) -> List[Dict]:
        """Get table sizes and row counts"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                pg_total_relation_size(schemaname||'.'||tablename) AS total_size_bytes,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                    pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
                n_live_tup AS row_count,
                n_dead_tup AS dead_rows
            FROM pg_tables t
            LEFT JOIN pg_stat_user_tables s ON t.tablename = s.relname AND t.schemaname = s.schemaname
            WHERE t.schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query)
            tables = []

            for row in result:
                tables.append({
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "total_size_bytes": row[3],
                    "table_size": row[4],
                    "indexes_size": row[5],
                    "row_count": row[6],
                    "dead_rows": row[7]
                })

            return tables

    def get_index_usage(self) -> List[Dict]:
        """Get index usage statistics"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan AS index_scans,
                idx_tup_read AS tuples_read,
                idx_tup_fetch AS tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query)
            indexes = []

            for row in result:
                indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                    "tuples_read": row[4],
                    "tuples_fetched": row[5],
                    "size": row[6]
                })

            return indexes

    def get_unused_indexes(self) -> List[Dict]:
        """Find indexes that are not being used"""
        query = text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
                AND idx_scan = 0
                AND indexrelname NOT LIKE '%_pkey'  -- Exclude primary keys
            ORDER BY pg_relation_size(indexrelid) DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query)
            unused_indexes = []

            for row in result:
                unused_indexes.append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "size": row[3]
                })

            return unused_indexes

    def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
        query = text("""
            SELECT
                pg_database_size(current_database()) AS db_size_bytes,
                pg_size_pretty(pg_database_size(current_database())) AS db_size,
                (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) AS connections,
                (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND state = 'active') AS active_queries;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query).fetchone()

            return {
                "size_bytes": result[0],
                "size": result[1],
                "total_connections": result[2],
                "active_queries": result[3],
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_vacuum_stats(self) -> List[Dict]:
        """Get vacuum and analyze statistics"""
        query = text("""
            SELECT
                schemaname,
                relname AS table_name,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze,
                n_dead_tup AS dead_tuples,
                n_live_tup AS live_tuples,
                CASE
                    WHEN n_live_tup > 0
                    THEN round(100.0 * n_dead_tup / n_live_tup, 2)
                    ELSE 0
                END AS dead_tuple_percent
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY n_dead_tup DESC;
        """)

        with self.SessionLocal() as session:
            result = session.execute(query)
            stats = []

            for row in result:
                stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "last_vacuum": row[2].isoformat() if row[2] else None,
                    "last_autovacuum": row[3].isoformat() if row[3] else None,
                    "last_analyze": row[4].isoformat() if row[4] else None,
                    "last_autoanalyze": row[5].isoformat() if row[5] else None,
                    "dead_tuples": row[6],
                    "live_tuples": row[7],
                    "dead_tuple_percent": float(row[8])
                })

            return stats

    def check_health(self) -> Dict:
        """Comprehensive health check"""
        health = {
            "status": "healthy",
            "checks": {},
            "warnings": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Check connection pool
        pool_status = self.get_pool_status()
        health["checks"]["connection_pool"] = pool_status

        if pool_status["utilization_percent"] > 80:
            health["warnings"].append(
                f"Connection pool utilization high: {pool_status['utilization_percent']:.1f}%"
            )

        # Check slow queries
        slow_queries = self.get_slow_queries(threshold_seconds=1.0)
        health["checks"]["slow_queries"] = len(slow_queries)

        if slow_queries:
            health["warnings"].append(f"Found {len(slow_queries)} slow queries")

        # Check table bloat
        vacuum_stats = self.get_vacuum_stats()
        bloated_tables = [t for t in vacuum_stats if t["dead_tuple_percent"] > 20]

        if bloated_tables:
            health["warnings"].append(
                f"Found {len(bloated_tables)} tables with >20% dead tuples"
            )

        # Check database size
        db_stats = self.get_database_stats()
        health["checks"]["database_stats"] = db_stats

        # Set overall status
        if health["warnings"]:
            health["status"] = "warning"

        return health

    def print_report(self):
        """Print comprehensive monitoring report"""
        print("\n" + "=" * 80)
        print("DATABASE MONITORING REPORT")
        print("=" * 80)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print()

        # Database stats
        print("DATABASE STATISTICS")
        print("-" * 80)
        db_stats = self.get_database_stats()
        print(f"  Database Size: {db_stats['size']}")
        print(f"  Total Connections: {db_stats['total_connections']}")
        print(f"  Active Queries: {db_stats['active_queries']}")
        print()

        # Connection pool
        print("CONNECTION POOL")
        print("-" * 80)
        pool = self.get_pool_status()
        print(f"  Pool Size: {pool['pool_size']}")
        print(f"  Checked Out: {pool['checked_out']}")
        print(f"  Checked In: {pool['checked_in']}")
        print(f"  Overflow: {pool['overflow']}")
        print(f"  Utilization: {pool['utilization_percent']:.1f}%")
        print()

        # Table sizes
        print("TABLE SIZES (Top 10)")
        print("-" * 80)
        tables = self.get_table_sizes()[:10]
        for t in tables:
            print(f"  {t['table']:25} {t['total_size']:>12} ({t['row_count']:,} rows)")
        print()

        # Slow queries
        print("SLOW QUERIES (>1 second)")
        print("-" * 80)
        slow = self.get_slow_queries()
        if slow:
            for q in slow:
                print(f"  PID {q['pid']}: {q['duration_seconds']:.2f}s")
                print(f"    {q['query'][:100]}...")
        else:
            print("  No slow queries detected")
        print()

        # Unused indexes
        print("UNUSED INDEXES")
        print("-" * 80)
        unused = self.get_unused_indexes()
        if unused:
            for idx in unused[:10]:
                print(f"  {idx['table']}.{idx['index']:30} {idx['size']:>12}")
        else:
            print("  No unused indexes detected")
        print()

        # Vacuum stats
        print("VACUUM STATISTICS (Tables needing attention)")
        print("-" * 80)
        vacuum = self.get_vacuum_stats()
        needs_vacuum = [v for v in vacuum if v['dead_tuple_percent'] > 10]
        if needs_vacuum:
            for v in needs_vacuum[:10]:
                print(f"  {v['table']:25} {v['dead_tuple_percent']:>6.1f}% dead tuples")
        else:
            print("  All tables healthy")
        print()

        print("=" * 80)


def main():
    """Run monitoring as standalone script"""
    monitor = DatabaseMonitor()

    # Print full report
    monitor.print_report()

    # Health check
    health = monitor.check_health()
    print("\nHEALTH CHECK")
    print("-" * 80)
    print(f"Status: {health['status'].upper()}")

    if health["warnings"]:
        print("\nWarnings:")
        for warning in health["warnings"]:
            print(f"  - {warning}")
    else:
        print("  No warnings")


if __name__ == "__main__":
    main()
