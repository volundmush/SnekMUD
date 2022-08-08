from snekmud.typing import Entity
from snekmud import WORLD, COMPONENTS, METATYPE_INTEGRITY
import mudforge


def serialize_entity(ent: Entity) -> dict:
    data = {}

    for c in WORLD.components_for_entity(ent):
        if not c:
            continue
        if c.should_save():
            data[c.save_name()] = c.export()

    return data


def integrity_check(ent: Entity):
    if (meta_comp := WORLD.try_component(ent, COMPONENTS["MetaTypes"])):
        for t in meta_comp.types:
            for func in METATYPE_INTEGRITY.get(t, list()):
                func(ent)


def deserialize_entity(data: dict, register=False) -> Entity:
    ent = WORLD.create_entity()

    for k, v in COMPONENTS.items():
        if k not in data:
            continue
        WORLD.add_component(ent, v.deserialize(data.pop(k), ent))

    integrity_check(ent)

    for comp in WORLD.components_for_entity(ent):
        if (func := getattr(comp, "at_post_deserialize", None)):
            func(ent)

    if register and (comp := WORLD.try_component(ent, COMPONENTS['EntityID'])):
        mudforge.GAME.register_entity(ent, comp)

    return ent