from app.services.collection.demo import DemoConnector

def get_connectors(names: list[str]):
    registry = {"demo": DemoConnector}
    connectors = []
    for name in names:
        cls = registry.get(name)
        if cls:
            connectors.append(cls())
    return connectors
