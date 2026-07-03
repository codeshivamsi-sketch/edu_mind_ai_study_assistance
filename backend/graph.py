import os
from anthropic import Anthropic
from config import neo4j_driver
import json
from config import anthropic_client
import re

template = {
    "entities": ["concept1", "concept2"],
    "relationships": [["concept1", "relates_to", "concept2"]]
}

def extract_entities(chunk: str):
    response = anthropic_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=f"Extract concepts and their relationships from the text. Return JSON only in this format: {json.dumps(template)}",
        messages=[{"role": "user", "content": chunk}]
    )
    raw = response.content[0].text
    print("Extracted entities (claud resp): ", raw)
    
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    print("raw.strip(): ", raw.strip())
    return raw.strip()

def store_entities(entities_json: str):
    data = json.loads(entities_json)

    with neo4j_driver.session() as session:
        for entity in data["entities"]:
            session.run("MERGE (e:Concept {name: $name})", name=entity)
        
        for rel in data["relationships"]:
            session.run("""
                MATCH (a:Concept {name: $from_concept})
                MATCH(b:Concept {name: $to_concept})
                MERGE (a)-[:RELATES_TO]->(b)
            """, from_concept=rel[0], to_concept=rel[2])

def get_related_concepts(topic: str):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (a:Concept {name: $topic})-[:RELATES_TO]->(b:Concept)
            RETURN b.name as related
        """, topic=topic)
        return [record["related"] for record in result]