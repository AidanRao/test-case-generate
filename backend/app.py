import argparse
from app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000, help="Port number to run the server on")
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port)
