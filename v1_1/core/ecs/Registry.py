#ECS Registry
from collections import defaultdict


class World:
    def __init__(self):
        self.entities = set()
        self.components = defaultdict(dict)
        self._next_entity_id = 0

    def create_entity(self):
        e = self._next_entity_id
        self._next_entity_id += 1
        self.entities.add(e)
        return e


    def add_component(self, entity, component):
        self.components.setdefault(type(component), {})[entity] = component

    def get(self, component_type):
        return self.components.get(component_type, {})

    def remove_entity(self, entity):
        self.entities.discard(entity)
        for comp_dict in self.components.values():
            comp_dict.pop(entity, None)

    def remove_component(self, entity, component_type):
        comps = self.components.get(component_type)
        if comps and entity in comps:
            del comps[entity]
