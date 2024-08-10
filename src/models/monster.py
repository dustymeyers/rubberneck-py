from dataclasses import dataclass
from typing import Any, Dict, Optional
from typing import List

from marshmallow import Schema, fields

class MonsterSchema(Schema):
    """
    
    """
    index = fields.Str(required=True)
    url = fields.Str(required=True)
    name = fields.Str(required=True)
    desc = fields.Str(allow_none=True)
    size = fields.Str(allow_none=True)
    type = fields.Str(allow_none=True)
    subtype = fields.Str(allow_none=True)
    alignment = fields.Str(allow_none=True)
    armor_class = fields.Dict(allow_none=True)
    hit_points = fields.Int(allow_none=True)
    hit_dice = fields.Str(allow_none=True)
    hit_points_roll = fields.Str(allow_none=True)
    speed = fields.Dict(allow_none=True)
    strength = fields.Int(allow_none=True)
    dexterity = fields.Int(allow_none=True)
    constitution = fields.Int(allow_none=True)
    intelligence = fields.Int(allow_none=True)
    wisdom = fields.Int(allow_none=True)
    charisma = fields.Int(allow_none=True)
    proficiencies = fields.List(fields.Str(), allow_none=True)
    damage_vulnerabilities = fields.List(fields.Str(), allow_none=True)
    damage_resistances = fields.List(fields.Str(), allow_none=True)
    damage_immunities = fields.List(fields.Str(), allow_none=True)
    condition_immunities = fields.List(fields.Str(), allow_none=True)
    senses = fields.Dict(allow_none=True)
    languages = fields.Str(allow_none=True)
    challenge_rating = fields.Int(allow_none=True)
    proficiency_bonus = fields.Int(allow_none=True)
    xp = fields.Int(allow_none=True)
    actions = fields.List(fields.Dict(), allow_none=True)
    legendary_actions = fields.List(fields.Dict(), allow_none=True)
    special_abilities = fields.List(fields.Dict(), allow_none=True)

@dataclass
class Monster:
    __schema__: MonsterSchema = MonsterSchema()
    index: str
    url: str
    name: str
    desc: Optional[str] = None
    size: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    alignment: Optional[str] = None
    armor_class: Optional[Dict[str, Any]] = None
    hit_points: Optional[int] = None
    hit_dice: Optional[str] = None
    hit_points_roll: Optional[str] = None
    speed: Optional[Dict[str, str]] = None
    strength: Optional[int] = None
    dexterity: Optional[int] = None
    constitution: Optional[int] = None
    intelligence: Optional[int] = None
    wisdom: Optional[int] = None
    charisma: Optional[int] = None
    proficiencies: Optional[List[str]] = None
    damage_vulnerabilities: Optional[List[str]] = None
    damage_resistances: Optional[List[str]] = None
    damage_immunities: Optional[List[str]] = None
    condition_immunities: Optional[List[str]] = None
    senses: Optional[Dict[str, str]] = None
    languages: Optional[str] = None
    challenge_rating: Optional[int] = None
    proficiency_bonus: Optional[int] = None
    xp: Optional[int] = None
    actions: Optional[List[Dict[str, Any]]] = None
    legendary_actions: Optional[List[Dict[str, Any]]] = None
    special_abilities: Optional[List[Dict[str, Any]]] = None

    def __init__(self, data: Dict[str, Any]):
        monster = self.__schema__.load(data)
        self.__dict__.update({key: getattr(monster, key) if getattr(monster, key) is not None else None for key in self.__annotations__})

    def to_dict(self) -> Dict[str, Any]:
        data = self.__schema__.dump(self)
        return {k: v for k, v in data.items() if v is not None}

