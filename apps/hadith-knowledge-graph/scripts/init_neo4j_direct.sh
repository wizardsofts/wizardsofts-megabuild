#!/bin/bash
# Initialize Neo4j schema directly using cypher-shell

set -e

echo "Initializing Neo4j schema..."

# Constraints
echo "Creating constraints..."
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.id IS UNIQUE"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE CONSTRAINT hadith_id_unique IF NOT EXISTS FOR (h:Hadith) REQUIRE h.hadith_id IS UNIQUE"

# Regular indexes
echo "Creating indexes..."
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.canonical_name)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX person_type_idx IF NOT EXISTS FOR (p:Person) ON (p.person_type)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX place_name_idx IF NOT EXISTS FOR (p:Place) ON (p.canonical_name)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX place_type_idx IF NOT EXISTS FOR (p:Place) ON (p.place_type)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX event_name_idx IF NOT EXISTS FOR (e:Event) ON (e.canonical_name)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX event_date_idx IF NOT EXISTS FOR (e:Event) ON (e.date_hijri_year)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX topic_name_idx IF NOT EXISTS FOR (t:Topic) ON (t.canonical_name)"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE INDEX topic_category_idx IF NOT EXISTS FOR (t:Topic) ON (t.category)"

# Full-text indexes
echo "Creating full-text indexes..."
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS FOR (p:Person) ON EACH [p.canonical_name]"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE FULLTEXT INDEX place_fulltext IF NOT EXISTS FOR (p:Place) ON EACH [p.canonical_name]"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE FULLTEXT INDEX event_fulltext IF NOT EXISTS FOR (e:Event) ON EACH [e.canonical_name]"
docker exec hadith-neo4j cypher-shell -u neo4j -p hadithknowledge2025 "CREATE FULLTEXT INDEX topic_fulltext IF NOT EXISTS FOR (t:Topic) ON EACH [t.canonical_name]"

echo "✅ Neo4j schema initialization complete!"
