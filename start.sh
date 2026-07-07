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
    echo "Installing backend dependencies..."
    conda run -n $CONDA_ENV_NAME pip install -r backend/requirements.txt
else
    echo "Conda environment '$CONDA_ENV_NAME' already exists."
fi

echo "Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Frontend dependencies already installed."
fi
cd ..

echo "Checking for processes on port 5050..."
PID_5050=$(lsof -ti:5050)
if [ ! -z "$PID_5050" ]; then
    echo "Killing process $PID_5050 on port 5050..."
    kill -9 $PID_5050
    sleep 1
fi

echo "Checking for processes on port 5173..."
PID_5173=$(lsof -ti:5173)
if [ ! -z "$PID_5173" ]; then
    echo "Killing process $PID_5173 on port 5173..."
    kill -9 $PID_5173
    sleep 1
fi

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
