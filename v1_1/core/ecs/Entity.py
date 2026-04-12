#ECS Entity

class Entity:
    _id = 0

    def __init__(self):
        self.id = Entity._id
        Entity._id += 1