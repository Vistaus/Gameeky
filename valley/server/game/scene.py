import math

from typing import Dict, Tuple, List, cast

from gi.repository import GLib

from .entity import Entity, EntityRegistry

from ...common.action import Action
from ...common.entity import Entity as CommonEntity
from ...common.entity import EntityType, Vector
from ...common.scanner import Description
from ...common.direction import Direction
from ...common.definitions import TICK, TILES_X, TILES_Y
from ...common.scene import Scene as CommonScene


class SpatialPartition:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._entity_by_position: Dict[Tuple[int, int], List[Entity]] = {}

    def add(self, entity: Entity) -> None:
        position = (
            math.floor(entity.position.x),
            math.floor(entity.position.y),
        )

        if position not in self._entity_by_position:
            self._entity_by_position[position] = []

        self._entity_by_position[position].append(entity)

    def remove(self, entity: Entity) -> None:
        position = (
            math.floor(entity.position.x),
            math.floor(entity.position.y),
        )

        self._entity_by_position[position].remove(entity)

        if len(self._entity_by_position[position]) == 0:
            del self._entity_by_position[position]

    def find_by_direction(self, entity: Entity) -> List[Entity]:
        if entity.direction == Direction.RIGHT:
            x = math.ceil(entity.position.x)
            y = round(entity.position.y)
        elif entity.direction == Direction.UP:
            x = round(entity.position.x)
            y = math.floor(entity.position.y)
        elif entity.direction == Direction.LEFT:
            x = math.floor(entity.position.x)
            y = round(entity.position.y)
        elif entity.direction == Direction.DOWN:
            x = round(entity.position.x)
            y = math.ceil(entity.position.y)

        return self._entity_by_position.get((x, y), [])

    def find_by_distance(
        self,
        target: Entity,
        distance_x: int,
        distance_y: int,
    ) -> List[Entity]:
        entities = []

        from_range_x = math.floor(max(target.position.x - distance_x, 0))
        to_range_x = math.floor(min(target.position.x + distance_x, self.width))

        from_range_y = math.floor(max(target.position.y - distance_y, 0))
        to_range_y = math.floor(min(target.position.y + distance_y, self.height))

        for y in range(from_range_y, to_range_y):
            for x in range(from_range_x, to_range_x):
                entities += self._entity_by_position.get((x, y), [])

        return entities


class Scene:
    def __init__(self, width: int, height: int, spawn: Vector) -> None:
        self._index = 0
        self._entity_by_id: Dict[int, Entity] = {}
        self._partition = SpatialPartition(width=width, height=height)

        self.width = width
        self.height = height
        self.spawn = spawn

        GLib.timeout_add(TICK, self.__on_scene_ticked)

    def __on_scene_ticked(self) -> int:
        self.tick()
        return GLib.SOURCE_CONTINUE

    def tick(self) -> None:
        for entity in self._entity_by_id.values():
            self._partition.remove(entity)

            if entity.action == Action.IDLE:
                entity.idle()
            elif entity.action == Action.MOVE:
                obstacles = self._partition.find_by_direction(entity)
                solids = [o for o in obstacles if o.solid is True]

                if not solids:
                    entity.move()
                else:
                    entity.tick()

            self._partition.add(entity)

    def add(self, type_id: int, position: Vector) -> int:
        entity = EntityRegistry.new_from_values(
            id=self._index,
            type_id=type_id,
            position=position,
        )

        self._index += 1
        self._entity_by_id[entity.id] = entity
        self._partition.add(entity)

        return entity.id

    def update(self, entity_id: int, action: Action, value: float) -> None:
        entity = self._entity_by_id[entity_id]

        if action == Action.IDLE:
            pass
        if action == Action.MOVE:
            entity.direction = Direction(int(value))

        entity.action = action

    def remove(self, entity_id: int) -> None:
        entity = self._entity_by_id[entity_id]

        del self._entity_by_id[entity_id]
        self._partition.remove(entity)

    def prepare_for_entity_id(self, entity_id: int) -> CommonScene:
        entity = self._entity_by_id[entity_id]
        distance_x = math.ceil(TILES_X / 2)
        distance_y = math.ceil(TILES_Y / 2)

        entities = self._partition.find_by_distance(
            target=entity,
            distance_x=distance_x,
            distance_y=distance_y,
        )

        return CommonScene(
            width=TILES_X,
            height=TILES_Y,
            anchor=entity.position,
            entities=cast(List[CommonEntity], entities),
        )

    @property
    def entities(self):
        return list(self._entity_by_id.values())

    @classmethod
    def new_from_description(cls, description: Description) -> "Scene":
        scene = cls(
            width=description.width,
            height=description.height,
            spawn=Vector(
                x=description.spawn.x,
                y=description.spawn.y,
                z=description.spawn.z,
            ),
        )

        for depth, layer in enumerate(description.layers):
            for index, type_id in enumerate(layer.entities):
                if type_id == EntityType.EMPTY:
                    continue

                position = Vector()
                position.x = index % scene.width
                position.y = int(index / scene.width)
                position.z = depth

                scene.add(type_id, position)

        return scene
