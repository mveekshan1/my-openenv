"""
Simple FastAPI server for testing OpenEnv API compliance.
"""
from fastapi import FastAPI, Request
from typing import Dict, Any
from environment import AiSecurityEnv

app = FastAPI()

# Global environment instance
env = AiSecurityEnv(seed=42)

@app.post("/reset")
async def reset() -> Dict[str, Any]:
    """Reset the environment and return initial state."""
    try:
        state = env.reset()
        return state
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/step")
async def step(request: Request) -> Dict[str, Any]:
    """Execute a step in the environment."""
    try:
        body = await request.json()
        action = body.get("action", {})
        observation, reward, done, info = env.step(action)
        return {
            "observation": observation,
            "reward": reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/state")
async def get_state() -> Dict[str, Any]:
    """Get current environment state."""
    try:
        state = env.state()
        return state
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "environment": "ai-security-openenv",
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)