from snekmud.typing import Entity
from snekmud import WORLD, COMPONENTS
import mudforge


def serialize_entity(ent: Entity) -> dict:
    data = {}

    for c in WORLD.components_for_entity(ent):
        if not c:
            continue
        if c.should_save():
            data[c.save_name()] = c.export()

    return data


def deserialize_entity(data: dict, register=False) -> Entity:
    ent = WORLD.create_entity()

    for k, v in COMPONENTS.items():
        if k not in data:
            continue
        WORLD.add_component(ent, v.deserialize(data.pop(k), ent))

    if register and (comp := WORLD.try_component(ent, COMPONENTS['EntityID'])):
        mudforge.GAME.register_entity(ent, comp)

    return ent