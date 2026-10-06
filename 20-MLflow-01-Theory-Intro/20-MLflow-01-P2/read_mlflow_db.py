import sqlite3

conn = sqlite3.connect("./mlflow.db")

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

# print("---")
# print("---")
# print("---")

# print("Tables:", tables)

# print("---")
# print("---")
# print("---")

query = conn.execute("SELECT * FROM experiments;").fetchall()

print(query)
