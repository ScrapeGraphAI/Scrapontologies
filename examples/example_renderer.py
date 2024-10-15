from scrapontologies import Entity, Relation
from scrapontologies.renderers import PyechartsRenderer

# Define entities with nested attributes
entities = [
    Entity(id="1", type="Person", attributes={
        "name": "Alice", 
        "age": 30, 
        "address": {
            "city": "New York",
            "zip": "10001"
        }
    }),
    Entity(id="2", type="Person", attributes={
        "name": "Bob", 
        "age": 40,
        "address": {
            "city": "Los Angeles",
            "zip": "90001"
        }
    }),
    Entity(id="3", type="Company", attributes={
        "name": "Acme Corp", 
        "industry": "Tech",
        "headquarters": {
            "city": "San Francisco",
            "zip": "94105"
        }
    })
]

# Define relations between the entities
relations = [
    Relation(id="r1", source="1", target="2", name="Friend"),
    Relation(id="r2", source="1", target="3", name="Employee"),
    Relation(id="r3", source="2", target="3", name="Employer"),
]

# Initialize the PyechartsRenderer
renderer = PyechartsRenderer(repulsion=2000, title="Graph Example with Nested Entities")

# Render the graph using the provided nodes and links
graph = renderer.render(entities, relations, output_path="graph_nested.html")
