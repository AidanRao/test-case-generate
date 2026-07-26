class CoverageStore:
    def __init__(self, io, path):
        self.io = io
        self.path = path

    def _load_records(self):
        raw = self.io.load(self.path, [])
        return raw if isinstance(raw, list) else []

    def get_coverage(self, project_id):
        for item in self._load_records():
            if isinstance(item, dict) and str(item.get("project_id")) == str(project_id):
                return {
                    key: value
                    for key, value in item.items()
                    if key != "project_id"
                }
        return None

    def save_coverage(self, project_id, payload):
        with self.io.lock(self.path):
            records = self._load_records()
            data = {"project_id": str(project_id), **dict(payload or {})}
            for index, item in enumerate(records):
                if isinstance(item, dict) and str(item.get("project_id")) == str(project_id):
                    records[index] = data
                    break
            else:
                records.append(data)
            self.io.save(self.path, records)
        return {
            key: value
            for key, value in data.items()
            if key != "project_id"
        }

    def delete_by_project(self, project_id):
        with self.io.lock(self.path):
            records = self._load_records()
            filtered = [
                item
                for item in records
                if not (
                    isinstance(item, dict)
                    and str(item.get("project_id")) == str(project_id)
                )
            ]
            if len(filtered) == len(records):
                return False
            self.io.save(self.path, filtered)
            return True
