#!/bin/bash
# Start the FastAPI backend server

echo "Starting FastAPI backend..."
echo "API will be available at http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn api.main:app --reload --port 8000

