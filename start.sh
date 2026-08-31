#!/bin/bash

CONDA_ENV_NAME="test-case-generate"
PYTHON_VERSION="3.11"
UNIPORTAL_STORAGE_PATH="${UNIPORTAL_STORAGE_PATH:-$(pwd)/backend/uniportal}"
UNIPORTAL_SYNC_INTERVAL_SECONDS="${UNIPORTAL_SYNC_INTERVAL_SECONDS:-30}"
export UNIPORTAL_STORAGE_PATH
export UNIPORTAL_SYNC_INTERVAL_SECONDS

echo "Checking conda environment..."
if ! conda env list | grep -E "^$CONDA_ENV_NAME\s"; then
    echo "Conda environment '$CONDA_ENV_NAME' not found. Creating..."
    conda create -n $CONDA_ENV_NAME python=$PYTHON_VERSION -y
else
    echo "Conda environment '$CONDA_ENV_NAME' already exists."
fi

# Also update existing environments when backend dependencies change.
echo "Installing backend dependencies..."
/opt/miniconda3/condabin/conda run -n "$CONDA_ENV_NAME" python -m pip install -r backend/requirements.txt || exit 1

echo "Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Frontend dependencies already installed."
fi
cd ..

for PORT in 5050 5173 5174; do
    echo "Checking for processes on port $PORT..."
    PORT_PID=$(lsof -ti:"$PORT")
    if [ -n "$PORT_PID" ]; then
        echo "Killing process $PORT_PID on port $PORT..."
        kill -9 $PORT_PID
        sleep 1
    fi
done

echo "Starting backend server..."
echo "UniPortal local data path: $UNIPORTAL_STORAGE_PATH"
echo "UniPortal sync interval: ${UNIPORTAL_SYNC_INTERVAL_SECONDS}s"
cd backend
conda run -n $CONDA_ENV_NAME python app.py --port 5050 &
BACKEND_PID=$!
cd ..

echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Both servers are running."
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

wait
