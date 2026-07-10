from app.task_registry import scheduled_task


@scheduled_task(
    id="uniportal_sync",
    name="UniPortal 项目同步",
    description="定期从 UniPortal 同步项目和需求数据",
    seconds=300,
    kwargs={"requirement_path": "document-validator/requirement.json"},
)
def synchronize_uniportal(storage, requirement_path):
    storage.synchronize_uniportal(requirement_path)
