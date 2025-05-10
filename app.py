from flask import Flask, request, jsonify, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from authlib.integrations.flask_client import OAuth
from fraud_detector import FraudDetector
import redis
import os
from dotenv import load_dotenv
from datetime import datetime
import user_agents
import json
import numpy as np
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config.update({
    "SECRET_KEY": os.getenv("FLASK_SECRET_KEY"),
    "JWT_SECRET_KEY": os.getenv("JWT_SECRET"),
    "JWT_ACCESS_TOKEN_EXPIRES": 3600,
    "PER_MINUTE_LIMIT": 5,
    "BIOMETRIC_THRESHOLD": float(os.getenv("BIOMETRIC_THRESHOLD", "0.7")),
    "BIO_FEATURE_WEIGHTS": {
        'mouse_velocity': 0.3,
        'mouse_distance': 0.3,
        'keystroke_dwell': 0.2,
        'keystroke_flight': 0.2
    }
})

jwt = JWTManager(app)

# Initialize services
try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True
    )
    r.ping()
except (redis.ConnectionError, redis.RedisError) as e:
    raise RuntimeError(f"Redis connection failed: {str(e)}")

fraud_detector = FraudDetector()

def analyze_biometrics(biometrics_data):
    """Analyze biometric patterns against user's historical data with dynamic thresholds"""
    try:
        # Get user's historical patterns
        user_bio = r.hget(f"user:biometrics:{get_jwt_identity()}", "data")
        if not user_bio:
            # First login, store current data as baseline
            r.hset(f"user:biometrics:{get_jwt_identity()}", "data", json.dumps(biometrics_data))
            return True
            
        user_bio = json.loads(user_bio)
        
        # Calculate similarity scores for each biometric feature
        scores = {
            'mouse_velocity': compare_values(
                biometrics_data['mouse']['avgVelocity'],
                user_bio['mouse']['avgVelocity'],
                threshold=0.25
            ),
            'mouse_distance': compare_values(
                biometrics_data['mouse']['totalDistance'],
                user_bio['mouse']['totalDistance'],
                threshold=0.25
            ),
            'keystroke_dwell': compare_values(
                biometrics_data['keyboard']['avgDwellTime'],
                user_bio['keyboard']['avgDwellTime'],
                threshold=0.35
            ),
            'keystroke_flight': compare_values(
                biometrics_data['keyboard']['avgFlightTime'],
                user_bio['keyboard']['avgFlightTime'],
                threshold=0.35
            )
        }
        
        # Calculate weighted score
        weighted_score = sum(
            scores[feature] * app.config["BIO_FEATURE_WEIGHTS"][feature]
            for feature in scores
        )
        
        return weighted_score >= app.config["BIOMETRIC_THRESHOLD"]
        
    except Exception as e:
        app.logger.error(f"Biometric analysis error: {str(e)}")
        return False
    

def compare_values(current, historical, threshold):
    """Compare current value to historical with allowed threshold"""
    if historical == 0:
        return 1.0  # Avoid division by zero
    deviation = abs(current - historical) / historical
    return 1.0 - min(deviation / threshold, 1.0)

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return jsonify({"success": False, "message": "Username and password required"}), 400

        username = data["username"]
        ip = request.remote_addr
        now = datetime.now()

        # Rate limiting
        minute_key = f"rate:{ip}:{username}:{now.minute}"
        current_count = r.incr(minute_key)
        r.expire(minute_key, 60)

        if current_count > app.config["PER_MINUTE_LIMIT"]:
            return jsonify({"success": False, "message": "Too many attempts"}), 429

        # Feature extraction
        features = {
            'login_attempts_1h': current_count,
            'ip_changes_24h': int(r.exists(f"last_ip:{username}") and 
                           ip != r.get(f"last_ip:{username}")),
            'user_agent_mismatch': int(request.headers.get('User-Agent', '') != 
                                    r.hget(f"user:{username}", "user_agent") or ''),
            'time_since_last_login': (now - datetime.fromisoformat(
                r.hget(f"user:{username}", "last_login") or now.isoformat()
            )).total_seconds() / 60,
            'location_change': int(data.get('location', '') != 
                                r.hget(f"user:{username}", "last_location") or '')
        }

        # Fraud detection
        if fraud_detector.predict(features, data.get('biometrics')):
            r.hincrby(f"user:{username}", "fraud_attempts", 1)
            return jsonify({
               "success": False,
                "message": "Suspicious activity detected",
                "requires2fa": True
            }), 403

        if username in ["1@gmail.com", "test@example.com"]:
            features["is_whitelisted"] = True
        
        # Biometric verification (if provided)
        if 'biometrics' in data:
            if not analyze_biometrics(data['biometrics']):
                return jsonify({
                    "success": False,
                    "message": "Behavioral verification failed",
                    "requires2fa": True
                }), 403

        # Update user session
        user_data = {
            "last_ip": ip,
            "last_login": now.isoformat(),
            "user_agent": request.headers.get('User-Agent', ''),
            "last_location": data.get('location', '')
        }
        if 'biometrics' in data:
            r.hset(f"user:biometrics:{username}", "data", json.dumps(data['biometrics']))

        for field, value in user_data.items():
            r.hset(f"user:{username}", field, value)

        return jsonify({
            "success": True,
            "token": create_access_token(identity=username),
            "username": username
        })

    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "Internal server error"}), 500
    


@app.route("/user/<username>", methods=["GET"])
@jwt_required()
def get_user(username):
    if get_jwt_identity() != username:
        return jsonify({"error": "Unauthorized"}), 403
        
    try:
        user_data = r.hgetall(f"user:{username}")
        bio_data = r.hget(f"user:biometrics:{username}", "data")
        
        return jsonify({
            "username": username,
            "riskScore": calculate_risk_score(username),
            "biometrics": json.loads(bio_data) if bio_data else None,
            **user_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_risk_score(username):
    """Calculate user risk score based on historical data"""
    attempts = int(r.hget(f"user:{username}", "fraud_attempts") or 0)
    return min(attempts * 15, 100)

if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
