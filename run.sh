#!/bin/bash

CONDA_ENV_NAME="test-case-generate"
PYTHON_VERSION="3.11"

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

echo "Starting backend server..."
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