from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from marshmallow import Schema, fields
import redis
from redis.commands.search.field import TextField, NumericField, TagField

class MonsterSchema(Schema):
    """
    Schema for the Monster model.
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

def create_monster_schema(redis_conn):
    try:
        # Create a Redis search index for the Monster model
        redis_conn.ft().create_index([
            redis.commands.search.field.TextField("$.index", as_name="index"),
            redis.commands.search.field.TextField("$.url", as_name="url"),
            redis.commands.search.field.TextField("$.name", as_name="name"),
            redis.commands.search.field.TextField("$.desc", as_name="desc", no_stem=True),
            redis.commands.search.field.TextField("$.size", as_name="size"),
            redis.commands.search.field.TextField("$.type", as_name="type"),
            redis.commands.search.field.TextField("$.subtype", as_name="subtype"),
            redis.commands.search.field.TextField("$.alignment", as_name="alignment"),
            redis.commands.search.field.TextField("$.armor_class", as_name="armor_class"),
            redis.commands.search.field.NumericField("$.hit_points", as_name="hit_points"),
            redis.commands.search.field.TextField("$.hit_dice", as_name="hit_dice"),
            redis.commands.search.field.TextField("$.hit_points_roll", as_name="hit_points_roll"),
            redis.commands.search.field.TextField("$.speed", as_name="speed"),
            redis.commands.search.field.NumericField("$.strength", as_name="strength"),
            redis.commands.search.field.NumericField("$.dexterity", as_name="dexterity"),
            redis.commands.search.field.NumericField("$.constitution", as_name="constitution"),
            redis.commands.search.field.NumericField("$.intelligence", as_name="intelligence"),
            redis.commands.search.field.NumericField("$.wisdom", as_name="wisdom"),
            redis.commands.search.field.NumericField("$.charisma", as_name="charisma"),
            redis.commands.search.field.TagField("$.proficiencies", as_name="proficiencies"),
            redis.commands.search.field.TagField("$.damage_vulnerabilities", as_name="damage_vulnerabilities"),
            redis.commands.search.field.TagField("$.damage_resistances", as_name="damage_resistances"),
            redis.commands.search.field.TagField("$.damage_immunities", as_name="damage_immunities"),
            redis.commands.search.field.TagField("$.condition_immunities", as_name="condition_immunities"),
            redis.commands.search.field.TextField("$.senses", as_name="senses"),
            redis.commands.search.field.TextField("$.languages", as_name="languages"),
            redis.commands.search.field.NumericField("$.challenge_rating", as_name="challenge_rating"),
            redis.commands.search.field.NumericField("$.proficiency_bonus", as_name="proficiency_bonus"),
            redis.commands.search.field.NumericField("$.xp", as_name="xp"),
            redis.commands.search.field.TextField("$.actions", as_name="actions"),
            redis.commands.search.field.TextField("$.legendary_actions", as_name="legendary_actions"),
            redis.commands.search.field.TextField("$.special_abilities", as_name="special_abilities"),
        ], prefix=["monster:"])
        print("Monster schema created successfully")
    except Exception as e:
        print(f"Error creating schema: {e}")

@dataclass
class Monster:
    """
        Description: 

        The Monster model. Currently the data is fetched from the DnD API and mapped to this model.
        This model is used to represent a monster returned from the DND SRD.

        Methods:

        to_dict: Returns a dictionary representation of the Monster model.
    
    """

    __schema__: MonsterSchema 
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
        """
        data: Dict[str, Any]
            The data to initialize the Monster model with.
            {
                "index": "ancient-bronze-dragon",
                "name": "Ancient Bronze Dragon",
                "url": "/api/monsters/ancient-bronze-dragon"
            }
        """
        self.__schema__ = MonsterSchema()
        monster = self.__schema__.load(data)
        self.__dict__.update({key: monster[key] for key in monster})

    def to_dict(self) -> Dict[str, Any]:
        data = self.__schema__.dump(self)
        return {k: v for k, v in data.items() if v is not None}

