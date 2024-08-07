## Safe SQL

Install Safe SQL from [PyPI](https://pypi.org/project/safe-sql/)

Safe SQL offers a safety net around SQL operations. Company data stored in SQL is succesptible to data losses. Deletion and updating are very common operations, but extra care should be taken. Safe SQL address this exact issue. Here are the key features of Safe-SQL :

1. **Improved Query Parsing:** Before update/delete queries, safe-sql provides a SELECT query for the user to perform sanity check.


2. **Mode Specifier:** Safe SQL provides 3 modes(read, write, admin), and implements safety checks before query execution.

3. **Enhanced Safet Checks:** Common pitfalls such as showing number of rows affected, notifying the user when missing **WHERE** clause with **UPDATE** and **DELETE** and checks when data is modified.

4. **Schema Validation:** Safe SQL checks if all columns used in the query exists.

5. **Backup Creation:** Before executing unsafe queries, Safe SQL creates a backup of the affected rows in a new table.

6. **Query Caching:** Safe SQL provides methods to cache query results and retrieve them, for frequently executed read queries. All queries are executed within a transaction.

7. **CLI Interface:** Safe SQL is managed through poetry dependency manager, and a robust CLI is provided to execute queries. 

## Why Safe SQL?

Working with database is complicated because of the stakes involved. Company data is valuable, and although backups always exist, there needs to be a tool to perform sanity checks on common pitfalls. Safe SQL is a tool that tries to address some of the problems. Contributions are always welcome.

## Installation and Usage

### Development
Safe SQL is managed through poetry, so to install the package use the following command(after cloning the repository and cd-ing into the project folder): 

```
poetry install
```

To run the Safe SQL using query using the command line, use :

```
poetry run safe_sql execute --connection-string "your_connection_string" --mode write --query "Your SQL query"
```

### Main

Safe SQL is available on PyPI, and can be installed with the follwing command : 

```
pip install safe-sql
```

Behind the scene, Safe SQL uses SQLAlchemy to interact with the database, so you don't have to deal with different dialect of MySQL, PostgreSQL, Oracle and can more efficiently query your data.

Safe SQL manages all the interaction with the databased based on the `--connection-string` CLI argument. After that, just set the mode and give the query, and leave the rest to Safe SQL.

## Future Work
PRs are always welcome. You can always work on these tasks : 

- Adding functionality for other common pitfalls.