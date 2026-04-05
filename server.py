"""
Simple Flask server for testing OpenEnv API compliance.
"""
from flask import Flask, jsonify, request
from environment import AiSecurityEnv
import json

app = Flask(__name__)

# Global environment instance
env = AiSecurityEnv(seed=42)

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the environment and return initial state."""
    try:
        state = env.reset()
        return jsonify({
            "status": "success",
            "observation": state
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/step', methods=['POST'])
def step():
    """Execute a step in the environment."""
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'action' in request body"
            }), 400

        action = data['action']
        observation, reward, done, info = env.step(action)

        return jsonify({
            "status": "success",
            "observation": observation,
            "reward": reward,
            "done": done,
            "info": info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/state', methods=['GET'])
def get_state():
    """Get current state."""
    try:
        state = env.state()
        return jsonify({
            "status": "success",
            "state": state
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "environment": "ai-security-openenv"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)