from app.task_registry import scheduled_task


@scheduled_task(
    id="uniportal_sync",
    name="UniPortal 项目同步",
    description="定期从 UniPortal 同步项目和需求数据",
    seconds=300,
)
def synchronize_uniportal(storage):
    storage.synchronize_uniportal()
