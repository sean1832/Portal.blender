import json

from .packet import Packet


class Payload:
    def __init__(self, meta: dict | None = None):
        self.data = {}
        self.items = []
        self.meta = meta if meta else {}

    def add_items(self, dicts: dict | list[dict]) -> None:
        if isinstance(dicts, dict):
            self.items.append(dicts)
        elif isinstance(dicts, list):
            self.items.extend(dicts)

    def set_meta(self, meta: dict) -> None:
        self.meta = meta

    def to_dict(self) -> dict:
        return {"Items": self.items, "Meta": self.meta}

    def to_json_str(self) -> str:
        return json.dumps(self.to_dict())

    def to_packet(self) -> bytes:
        return Packet(self.to_json_str().encode("utf-8")).serialize()
