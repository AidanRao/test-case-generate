import argparse
from app import create_app
from app.services.system_task_service import SystemTaskService

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000, help="Port number to run the server on")
    args = parser.parse_args()
    SystemTaskService(app.config["STORAGE"]).start_tasks()
    app.run(host="0.0.0.0", port=args.port)
