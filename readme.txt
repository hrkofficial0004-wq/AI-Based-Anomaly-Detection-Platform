# Healthcare Anomaly Detection System

## Overview
This project is a full-stack system designed to detect anomalies in healthcare data (patient vitals) using machine learning. It simulates real-time data streaming and provides a dashboard for visualization and alerting.

## Project Structure
- `backend/`: Flask API, Machine Learning models, and data processing logic.
- `frontend/`: Real-time dashboard using HTML, CSS, and JavaScript.
- `start_backend.bat`: Script to quickly start the backend server.

## Getting Started

### Backend Setup
1. Navigate to the `backend` directory.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
   Alternatively, you can run the `start_backend.bat` script from the root directory.

### Frontend Setup
1. Open `frontend/index.html` in any modern web browser to view the dashboard.

## Key Features
- **Real-time Monitoring**: Visualization of patient vital signs.
- **Anomaly Detection**: Uses ML models to identify critical health patterns.
- **Alerting System**: Notifies users when anomalies are detected.
