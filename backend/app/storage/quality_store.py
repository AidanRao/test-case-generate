class QualityStore:
    QUALITY_FIELDS = ("duration", "fail_count", "iterations", "success_count")

    def __init__(self, io, path):
        self.io = io
        self.path = path

    def _load_quality_records(self):
        raw = self.io.load(self.path, [])
        return raw if isinstance(raw, list) else []

    def get_quality(self, project_id):
        for item in self._load_quality_records():
            if isinstance(item, dict) and str(item.get("project_id")) == str(project_id):
                return self._quality_payload(item)
        return None

    def save_quality(self, project_id, payload):
        records = self._load_quality_records()
        data = {"project_id": str(project_id), **self._quality_payload(payload or {})}
        updated = False
        for idx, item in enumerate(records):
            if isinstance(item, dict) and str(item.get("project_id")) == str(project_id):
                records[idx] = data
                updated = True
                break
        if not updated:
            records.append(data)
        self.io.save(self.path, records)
        return data

    def _quality_payload(self, payload):
        return {key: payload[key] for key in self.QUALITY_FIELDS if key in payload}

    def delete_by_project(self, project_id):
        records = self._load_quality_records()
        filtered = [
            item
            for item in records
            if not (isinstance(item, dict) and str(item.get("project_id")) == str(project_id))
        ]
        if len(filtered) == len(records):
            return False
        self.io.save(self.path, filtered)
        return True
