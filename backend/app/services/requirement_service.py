class RequirementService:
    def __init__(self, storage):
        self.storage = storage

    def list_requirements(self, project_id, module=None, req_type=None, keyword=None):
        return self.storage.list_requirements(project_id, module, req_type, keyword)

    def get_requirement(self, project_id, requirement_id):
        return self.storage.get_requirement(project_id, requirement_id)

    def update_requirement(self, project_id, requirement_id, payload):
        return self.storage.update_requirement(project_id, requirement_id, payload)

    def complete_requirements(self, project_id, requirements, scope):
        return self.storage.complete_requirements(project_id, requirements, scope)

    def create_requirement(self, project_id, payload):
        return self.storage.create_requirement(project_id, payload)

    def delete_requirement(self, project_id, requirement_id):
        return self.storage.delete_requirement(project_id, requirement_id)
