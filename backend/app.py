"""
Flask application entry point.
Starts the Kafka producer/consumer threads on launch and serves the API + SocketIO.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

from config import SECRET_KEY, DEBUG
from db import init_db, SessionLocal
from routes.vitals import vitals_bp
from routes.anomalies import anomalies_bp
from kafka_producer import start_producer
from kafka_consumer import start_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Register blueprints
app.register_blueprint(vitals_bp)
app.register_blueprint(anomalies_bp)


@app.route("/")
def health():
    return jsonify({
        "status": "online",
        "service": "AI Healthcare Anomaly Detection API",
        "version": "1.0.0",
    })


@socketio.on("connect")
def on_connect():
    print("[SocketIO] Client connected")


@socketio.on("disconnect")
def on_disconnect():
    print("[SocketIO] Client disconnected")


if __name__ == "__main__":
    # Initialize database tables
    init_db()
    print("[DB] Tables initialised ✓")

    # Start simulated Kafka producer and consumer
    start_producer()
    start_consumer(app, socketio, SessionLocal)

    print("[App] Starting Flask-SocketIO on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
