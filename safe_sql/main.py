import click
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
from enum import Enum
from typing import Optional, Dict, Any
import re
import logging
from datetime import datetime
import hashlib
import json

class Mode(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class SafeSQL:
    def __init__(self, connection_string: str, mode: Mode = Mode.READ):
        self.engine = create_engine(connection_string)
        self.mode = mode
        self.logger = self._setup_logger()
        self.inspector = inspect(self.engine)

    def _setup_logger(self):
        logger = logging.getLogger('SafeSQL')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('safe_sql.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        with self.engine.begin() as connection:
            try:
                if self.mode == Mode.READ:
                    if not query.strip().upper().startswith("SELECT"):
                        raise ValueError("Only SELECT queries are allowed in READ mode")
                    return self._execute_read_query(connection, query, params)
                elif self.mode == Mode.WRITE:
                    if query.strip().upper().startswith(("UPDATE", "DELETE")):
                        return self._execute_unsafe_query(connection, query, params)
                    return self._execute_write_query(connection, query, params)
                elif self.mode == Mode.ADMIN:
                    return self._execute_admin_query(connection, query, params)
            except Exception as e:
                self.logger.error(f"Query execution failed: {str(e)}")
                raise

    def _execute_read_query(self, connection, query, params):
        self.logger.info(f"Executing READ query: {query}")
        return connection.execute(text(query), params)

    def _execute_write_query(self, connection, query, params):
        self.logger.info(f"Executing WRITE query: {query}")
        return connection.execute(text(query), params)

    def _execute_admin_query(self, connection, query, params):
        self.logger.warning(f"Executing ADMIN query: {query}")
        return connection.execute(text(query), params)

    def _execute_unsafe_query(self, connection, query, params):
        self._check_unsafe_query(query, connection)
        self._create_backup(connection, query)
        result = connection.execute(text(query), params)
        self.logger.info(f"Executed unsafe query: {query}")
        return result

    def _check_unsafe_query(self, query: str, connection):
        table_name = self._extract_table_name(query)
        
        # Get the SELECT equivalent
        select_query = self._get_select_equivalent(query)
        print(f"Equivalent SELECT query: {select_query}")
        
        # Execute the SELECT query to show affected rows
        result = connection.execute(text(select_query))
        affected_rows = result.rowcount
        print(f"Number of rows that will be affected: {affected_rows}")
        
        # Check for common pitfalls
        self._check_common_pitfalls(query, table_name, affected_rows)
        
        # Validate schema
        self._validate_schema(query, table_name)
        
        # Ask for confirmation
        confirmation = input("Do you want to proceed with this query? (y/n): ")
        if confirmation.lower() != 'y':
            raise ValueError("Query execution cancelled by user")

    def _extract_table_name(self, query: str) -> str:
        match = re.search(r'\s+(?:FROM|UPDATE|DELETE\s+FROM)\s+(\w+)', query, re.IGNORECASE)
        if match:
            return match.group(1)
        raise ValueError("Could not extract table name from query")

    def _get_select_equivalent(self, query: str) -> str:
        if query.strip().upper().startswith("UPDATE"):
            table_name = self._extract_table_name(query)
            where_clause = re.search(r'WHERE\s+(.+)(?:ORDER BY|LIMIT|$)', query, re.IGNORECASE | re.DOTALL)
            where_clause = where_clause.group(1) if where_clause else ''
            return f"SELECT * FROM {table_name} WHERE {where_clause}"
        elif query.strip().upper().startswith("DELETE"):
            return query.replace("DELETE", "SELECT *", 1)
        else:
            raise ValueError("Unsupported query type for SELECT equivalent")

    def _check_common_pitfalls(self, query: str, table_name: str, affected_rows: int):
        if "company" in table_name.lower():
            print("Warning: You are modifying company data. Please double-check your query.")
        if "WHERE" not in query.upper():
            print("Warning: No WHERE clause found. This will affect all rows in the table.")
        if affected_rows > 1000:
            print(f"Warning: This query will affect {affected_rows} rows. Are you sure this is intended?")
        if re.search(r'WHERE\s+\w+\s*=\s*NULL', query, re.IGNORECASE):
            print("Warning: Using 'WHERE column = NULL' will not work as intended. Use 'WHERE column IS NULL' instead.")

    def _validate_schema(self, query: str, table_name: str):
        columns = self.inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        
        # Check if all columns in the query exist in the table
        for match in re.finditer(r'\b(\w+)\s*=', query):
            col_name = match.group(1)
            if col_name not in column_names:
                print(f"Warning: Column '{col_name}' not found in table '{table_name}'")

    def _create_backup(self, connection, query):
        table_name = self._extract_table_name(query)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table_name = f"{table_name}_backup_{timestamp}"
        
        # Create a backup of the affected rows
        select_query = self._get_select_equivalent(query)
        backup_query = f"CREATE TABLE {backup_table_name} AS {select_query}"
        connection.execute(text(backup_query))
        
        self.logger.info(f"Created backup table: {backup_table_name}")
        print(f"Backup created: {backup_table_name}")

    def get_query_hash(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def cache_query_result(self, query: str, result):
        query_hash = self.get_query_hash(query)
        cache_file = f"query_cache/{query_hash}.json"
        with open(cache_file, 'w') as f:
            json.dump(result, f)

    def get_cached_result(self, query: str):
        query_hash = self.get_query_hash(query)
        cache_file = f"query_cache/{query_hash}.json"
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

@click.group()
def cli():
    print("Are we reaching here?")

@cli.command()
@click.option('--connection-string', required=True, help='Database connection string')
@click.option('--mode', type=click.Choice(['read', 'write', 'admin']), default='read', help='Operation mode')
@click.option('--query', required=True, help='SQL query to execute')
def execute(connection_string, mode, query):
    safe_sql = SafeSQL(connection_string, Mode(mode))
    result = safe_sql.execute_query(query)
    click.echo(result.fetchall())

if __name__ == '__main__':
    cli()