import json
import os
from copy import deepcopy


class JsonIO:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def load(self, path, default):
        if not os.path.exists(path):
            self.save(path, default)
            return deepcopy(default)
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return deepcopy(default)

    def save(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
