import json
import os
import tempfile
from copy import deepcopy
from contextlib import contextmanager
from threading import Lock, RLock


class JsonIO:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._locks = {}
        self._locks_guard = Lock()
        os.makedirs(self.base_dir, exist_ok=True)

    @contextmanager
    def lock(self, path):
        normalized_path = os.path.abspath(path)
        with self._locks_guard:
            path_lock = self._locks.setdefault(normalized_path, RLock())
        with path_lock:
            yield

    def load(self, path, default):
        with self.lock(path):
            if not os.path.exists(path):
                self.save(path, default)
                return deepcopy(default)
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    def save(self, path, data):
        with self.lock(path):
            directory = os.path.dirname(path) or self.base_dir
            os.makedirs(directory, exist_ok=True)
            file_descriptor, temporary_path = tempfile.mkstemp(
                dir=directory,
                prefix=f".{os.path.basename(path)}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(file_descriptor, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporary_path, path)
            except Exception:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
                raise
