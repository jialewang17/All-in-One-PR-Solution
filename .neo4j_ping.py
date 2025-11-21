from neo4j import GraphDatabase
import os
uri  = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
pwd  = os.getenv("NEO4J_PASSWORD")
db   = os.getenv("NEO4J_DATABASE") or "neo4j"

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session(database=db) as s:
    print("OK:", s.run("RETURN 1 AS x").single()["x"])
driver.close()
