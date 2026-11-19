#ECS Registry

from v1_1.audio.audio import Audio
from v1_1.config.settings import Settings
from v1_1.config.themes import Themes
from v1_1.core.game_state import StateMachine


class World:
    """Entities and components, plus the shared resources every system can reach.

    Resources (settings, theme, audio, state) are not entities: clear() keeps them.
    Each World gets fresh ones by default, so tests never share state.
    """

    def __init__(self, settings=None, theme=None, audio=None, state=None):
        self.components = {}
        self._next_entity_id = 0

        self.settings = settings or Settings()
        self.theme = theme or Themes()
        self.audio = audio or Audio()
        self.state = state or StateMachine()

    def create_entity(self):
        e = self._next_entity_id
        self._next_entity_id += 1
        return e

    def clear(self):
        self.components.clear()

    def add_component(self, entity, component):
        self.components.setdefault(type(component), {})[entity] = component

    def get(self, component_type):
        return self.components.get(component_type, {})

    def remove_entity(self, entity):
        for comp_dict in self.components.values():
            comp_dict.pop(entity, None)

    def remove_component(self, entity, component_type):
        comps = self.components.get(component_type)
        if comps and entity in comps:
            del comps[entity]
