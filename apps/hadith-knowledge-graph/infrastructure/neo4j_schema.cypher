// ============================================
// Neo4j Schema for Hadith Knowledge Graph
// ============================================

// ============================================
// CONSTRAINTS (Unique identifiers)
// ============================================

// Person nodes
CREATE CONSTRAINT person_id_unique IF NOT EXISTS
FOR (p:Person) REQUIRE p.id IS UNIQUE;

// Place nodes
CREATE CONSTRAINT place_id_unique IF NOT EXISTS
FOR (p:Place) REQUIRE p.id IS UNIQUE;

// Event nodes
CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (e:Event) REQUIRE e.id IS UNIQUE;

// Topic nodes
CREATE CONSTRAINT topic_id_unique IF NOT EXISTS
FOR (t:Topic) REQUIRE t.id IS UNIQUE;

// Hadith nodes
CREATE CONSTRAINT hadith_id_unique IF NOT EXISTS
FOR (h:Hadith) REQUIRE h.hadith_id IS UNIQUE;

// QuranVerse nodes
CREATE CONSTRAINT quran_verse_unique IF NOT EXISTS
FOR (v:QuranVerse) REQUIRE (v.surah, v.ayah) IS NODE KEY;

// ============================================
// INDEXES (Performance optimization)
// ============================================

// Person indexes
CREATE INDEX person_name_idx IF NOT EXISTS
FOR (p:Person) ON (p.canonical_name);

CREATE INDEX person_type_idx IF NOT EXISTS
FOR (p:Person) ON (p.person_type);

CREATE INDEX person_reliability_idx IF NOT EXISTS
FOR (p:Person) ON (p.reliability_grade);

// Place indexes
CREATE INDEX place_name_idx IF NOT EXISTS
FOR (p:Place) ON (p.canonical_name);

CREATE INDEX place_type_idx IF NOT EXISTS
FOR (p:Place) ON (p.place_type);

// Event indexes
CREATE INDEX event_name_idx IF NOT EXISTS
FOR (e:Event) ON (e.canonical_name);

CREATE INDEX event_date_idx IF NOT EXISTS
FOR (e:Event) ON (e.date_hijri_year);

// Topic indexes
CREATE INDEX topic_name_idx IF NOT EXISTS
FOR (t:Topic) ON (t.canonical_name);

CREATE INDEX topic_category_idx IF NOT EXISTS
FOR (t:Topic) ON (t.category);

// Hadith indexes
CREATE INDEX hadith_grading_idx IF NOT EXISTS
FOR (h:Hadith) ON (h.grading);

CREATE INDEX hadith_collection_idx IF NOT EXISTS
FOR (h:Hadith) ON (h.collection);

// QuranVerse indexes
CREATE INDEX quran_surah_idx IF NOT EXISTS
FOR (v:QuranVerse) ON (v.surah);

// ============================================
// FULL-TEXT SEARCH INDEXES
// ============================================

// Person full-text search
CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
FOR (p:Person) ON EACH [p.canonical_name, p.name_variants];

// Place full-text search
CREATE FULLTEXT INDEX place_fulltext IF NOT EXISTS
FOR (p:Place) ON EACH [p.canonical_name, p.modern_name];

// Event full-text search
CREATE FULLTEXT INDEX event_fulltext IF NOT EXISTS
FOR (e:Event) ON EACH [e.canonical_name, e.description_en];

// Topic full-text search
CREATE FULLTEXT INDEX topic_fulltext IF NOT EXISTS
FOR (t:Topic) ON EACH [t.canonical_name, t.definition_en];

// Hadith full-text search
CREATE FULLTEXT INDEX hadith_fulltext IF NOT EXISTS
FOR (h:Hadith) ON EACH [h.text_en];

// ============================================
// SAMPLE DATA STRUCTURE
// ============================================

// Example: Create a hadith with full context
// (Run this as a template for understanding the schema)

/*
// 1. Create Hadith node
CREATE (h:Hadith {
  hadith_id: 12345,
  text_en: "Abu Hurairah narrated...",
  text_ar: "قال أبو هريرة...",
  collection: "Sahih Bukhari",
  book_number: "10",
  hadith_number: "520",
  grading: "Sahih",
  created_at: datetime()
})

// 2. Create Narrator
CREATE (narrator:Person {
  id: "uuid-abu-hurairah",
  canonical_name: "Abu Hurairah",
  person_type: "narrator",
  reliability_grade: "trustworthy",
  narrator_tier: 1,
  generation: "Sahaba"
})

// 3. Create Narration Chain
CREATE (h)-[:NARRATED_BY {
  role: "primary_narrator",
  chain_position: 1,
  confidence: 0.98
}]->(narrator)

// 4. Create Place
CREATE (place:Place {
  id: "uuid-medina",
  canonical_name: "Medina",
  place_type: "city",
  modern_name: "Al-Madinah"
})

CREATE (h)-[:MENTIONS_PLACE {
  context: "location_of_narration",
  confidence: 0.92
}]->(place)

// 5. Create Topic
CREATE (topic:Topic {
  id: "uuid-prayer-times",
  canonical_name: "Prayer Times",
  category: "Salah",
  topic_type: "legal"
})

CREATE (h)-[:ABOUT_TOPIC {
  relevance: 0.95,
  is_primary: true
}]->(topic)

// 6. Create Event
CREATE (event:Event {
  id: "uuid-battle-badr",
  canonical_name: "Battle of Badr",
  event_type: "battle",
  date_hijri_year: 2
})

CREATE (h)-[:DESCRIBES_EVENT]->(event)
CREATE (event)-[:OCCURRED_AT]->(place)

// 7. Link to Quran Verse
CREATE (verse:QuranVerse {
  surah: 2,
  ayah: 238,
  text_en: "Guard strictly your prayers..."
})

CREATE (h)-[:REFERENCES_QURAN {
  relationship: "explains"
}]->(verse)
*/

// ============================================
// USEFUL QUERY PATTERNS
// ============================================

// Query 1: Find all hadiths narrated by a person
// MATCH (h:Hadith)-[:NARRATED_BY]->(p:Person {canonical_name: "Abu Hurairah"})
// RETURN h.hadith_id, h.text_en
// LIMIT 10;

// Query 2: Find narration chains (isnad)
// MATCH path = (h:Hadith {hadith_id: 12345})-[:NARRATED_BY*1..5]->(p:Person)
// RETURN path;

// Query 3: Find hadiths about a topic
// MATCH (h:Hadith)-[:ABOUT_TOPIC]->(t:Topic {category: "Salah"})
// RETURN h.hadith_id, h.text_en, t.canonical_name
// LIMIT 10;

// Query 4: Find related hadiths through shared topics
// MATCH (h1:Hadith {hadith_id: 12345})-[:ABOUT_TOPIC]->(t:Topic)<-[:ABOUT_TOPIC]-(h2:Hadith)
// WHERE h1 <> h2
// RETURN h2.hadith_id, h2.text_en, count(t) as shared_topics
// ORDER BY shared_topics DESC
// LIMIT 5;

// Query 5: Find hadiths about events at specific places
// MATCH (h:Hadith)-[:DESCRIBES_EVENT]->(e:Event)-[:OCCURRED_AT]->(p:Place)
// WHERE p.canonical_name = "Medina"
// RETURN h.hadith_id, e.canonical_name, h.text_en;

// Query 6: Find common narrators between hadiths
// MATCH (h1:Hadith {hadith_id: 12345})-[:NARRATED_BY]->(p:Person)<-[:NARRATED_BY]-(h2:Hadith)
// WHERE h1 <> h2
// RETURN p.canonical_name, count(h2) as shared_hadiths
// ORDER BY shared_hadiths DESC;

// Query 7: Verify narration chain authenticity
// MATCH path = (h:Hadith)-[:NARRATED_BY*]-(prophet:Person {person_type: "prophet"})
// WITH nodes(path) as narrators
// WHERE all(n in narrators WHERE n.reliability_grade IN ['trustworthy', 'very_reliable'])
// RETURN path;

// ============================================
// DATA CLEANUP QUERIES
// ============================================

// Delete all nodes and relationships (USE WITH CAUTION!)
// MATCH (n) DETACH DELETE n;

// Count nodes by type
// MATCH (n) RETURN labels(n) as type, count(*) as count;

// Count relationships by type
// MATCH ()-[r]->() RETURN type(r) as relationship, count(*) as count;

// Find orphaned nodes (nodes with no relationships)
// MATCH (n)
// WHERE NOT (n)--()
// RETURN labels(n) as type, count(*) as count;

// ============================================
// PERFORMANCE QUERIES
// ============================================

// Show all constraints
// SHOW CONSTRAINTS;

// Show all indexes
// SHOW INDEXES;

// Show database statistics
// CALL db.stats.retrieve('GRAPH COUNTS');

// Profile a query
// PROFILE
// MATCH (h:Hadith)-[:ABOUT_TOPIC]->(t:Topic {category: "Salah"})
// RETURN h.hadith_id, t.canonical_name
// LIMIT 10;
