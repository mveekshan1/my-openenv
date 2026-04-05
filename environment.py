"""
OpenEnv-compliant AI Security Policy Enforcement & Firewall Optimization Environment
"""

import random
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class DataSensitivity(Enum):
    """Data sensitivity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThreatType(Enum):
    """Threat types in the system"""
    DATA_EXFILTRATION = "data_exfiltration"
    BRUTE_FORCE = "brute_force"
    INTRUSION = "intrusion"
    NONE = "none"


@dataclass
class FirewallRule:
    """Firewall rule structure"""
    rule_action: str  # "allow" or "block"
    target: str  # "ip" or "endpoint"
    duration: str  # e.g., "24h", "1h"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityEvent:
    """Security event in the environment"""
    event_id: str
    logs: List[str]
    user_role: str
    data_sensitivity: str
    status: str = "open"
    decision: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "logs": self.logs,
            "user_role": self.user_role,
            "data_sensitivity": self.data_sensitivity,
            "status": self.status,
            "decision": self.decision
        }


class AiSecurityEnv:
    """
    OpenEnv environment for AI Security Policy Enforcement.
    Simulates a cybersecurity environment where an AI agent detects threats,
    prevents data leakage, and dynamically generates firewall rules.
    """

    def __init__(self, seed: int = 42):
        """Initialize the environment."""
        self.seed = seed
        random.seed(seed)
        self.current_event: Optional[SecurityEvent] = None
        self.step_count = 0
        self.max_steps = 10
        self.task_scenarios = self._initialize_scenarios()

    def _initialize_scenarios(self) -> List[Dict[str, Any]]:
        """Initialize predefined task scenarios."""
        return [
            {
                "name": "Data Leakage Prevention",
                "difficulty": "easy",
                "event_id": "EVT-001",
                "logs": ["User initiated data export", "2GB data transfer to external IP"],
                "user_role": "employee",
                "data_sensitivity": DataSensitivity.HIGH.value,
                "expected": {
                    "allow": False,
                    "threat_type": ThreatType.DATA_EXFILTRATION.value,
                    "response_action": "block"
                }
            },
            {
                "name": "Threat Detection",
                "difficulty": "medium",
                "event_id": "EVT-002",
                "logs": [
                    "Failed login attempt from 192.168.1.50",
                    "Failed login attempt from 192.168.1.50",
                    "Failed login attempt from 192.168.1.50",
                    "Successful login from 192.168.1.50"
                ],
                "user_role": "unknown",
                "data_sensitivity": DataSensitivity.MEDIUM.value,
                "expected": {
                    "allow": False,
                    "threat_type": ThreatType.BRUTE_FORCE.value,
                    "response_action": "block_ip"
                }
            },
            {
                "name": "Advanced Threat Response",
                "difficulty": "hard",
                "event_id": "EVT-003",
                "logs": [
                    "Unusual data transfer volume detected",
                    "Access from unknown IP 203.0.113.45",
                    "Admin login at 02:30 UTC (outside business hours)",
                    "Database query on sensitive customer records"
                ],
                "user_role": "admin",
                "data_sensitivity": DataSensitivity.HIGH.value,
                "expected": {
                    "allow": False,
                    "threat_type": ThreatType.INTRUSION.value,
                    "response_action": "block + alert",
                    "firewall_rule": {
                        "rule_action": "block",
                        "target": "ip",
                        "duration": "24h"
                    }
                }
            }
        ]

    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment and return initial state.
        OpenEnv API: reset() -> state
        """
        self.step_count = 0
        scenario = self.task_scenarios[random.randint(0, len(self.task_scenarios) - 1)]
        self.current_event = SecurityEvent(
            event_id=scenario["event_id"],
            logs=scenario["logs"],
            user_role=scenario["user_role"],
            data_sensitivity=scenario["data_sensitivity"]
        )
        return self._get_state()

    def _get_state(self) -> Dict[str, Any]:
        """Get current state."""
        if self.current_event is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self.current_event.to_dict()

    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        OpenEnv API: step(action) -> (observation, reward, done, info)

        Args:
            action: Dictionary with agent's decision
                {
                    "allow": bool,
                    "threat_type": str,
                    "response_action": str,
                    "firewall_rule": {...}  # optional
                }

        Returns:
            observation: Current state after action
            reward: Reward signal [0.0, 1.0]
            done: Episode termination flag
            info: Additional info (grading details)
        """
        self.step_count += 1

        # Execute grading
        grade: Dict[str, Any] = self._grade_action(action)
        reward: float = grade["reward"]
        done: bool = (reward == 1.0) or (self.step_count >= self.max_steps)

        observation: Dict[str, Any] = self._get_state()
        info: Dict[str, Any] = {
            "grade": grade,
            "step": self.step_count,
            "done": done
        }

        if done and self.current_event:
            self.current_event.status = "processed"
            self.current_event.decision = action

        return observation, reward, done, info

    def _grade_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic grading function.
        Scoring: allow(0.3), threat_type(0.3), response_action(0.2), firewall_rule(0.2)
        """
        if self.current_event is None:
            return {"score": 0.0, "reward": 0.0, "details": {}}

        # Get expected output for current scenario
        scenario: Optional[Dict[str, Any]] = self._find_current_scenario()
        if scenario is None:
            return {"score": 0.0, "reward": 0.0, "details": {}}

        expected: Dict[str, Any] = scenario["expected"]
        details = {}
        total_score = 0.0

        # Grade "allow" field (0.3 weight)
        allow_score = 1.0 if action.get("allow") == expected["allow"] else 0.0
        details["allow"] = {
            "expected": expected["allow"],
            "actual": action.get("allow"),
            "score": allow_score
        }
        total_score += allow_score * 0.3

        # Grade "threat_type" field (0.3 weight)
        threat_score = 1.0 if action.get("threat_type") == expected["threat_type"] else 0.0
        details["threat_type"] = {
            "expected": expected["threat_type"],
            "actual": action.get("threat_type"),
            "score": threat_score
        }
        total_score += threat_score * 0.3

        # Grade "response_action" field (0.2 weight)
        response_score = 1.0 if action.get("response_action") == expected["response_action"] else 0.0
        details["response_action"] = {
            "expected": expected["response_action"],
            "actual": action.get("response_action"),
            "score": response_score
        }
        total_score += response_score * 0.2

        # Grade "firewall_rule" field (0.2 weight)
        firewall_score: float = 0.0
        if "firewall_rule" in expected:
            expected_rule: Any = expected["firewall_rule"]
            actual_rule: Any = action.get("firewall_rule", {})
            if (
                isinstance(actual_rule, dict) and
                actual_rule.get("rule_action") == expected_rule.get("rule_action") and
                actual_rule.get("target") == expected_rule.get("target") and
                actual_rule.get("duration") == expected_rule.get("duration")
            ):
                firewall_score = 1.0
        elif action.get("firewall_rule") is None:
            firewall_score = 1.0  # Correct to omit when not expected

        details["firewall_rule"] = {
            "expected": expected.get("firewall_rule"),
            "actual": action.get("firewall_rule"),
            "score": firewall_score
        }
        total_score += firewall_score * 0.2

        # Apply step penalty
        step_penalty = max(0, (self.step_count - 1) * 0.05)
        final_score = max(0.0, total_score - step_penalty)

        return {
            "score": round(final_score, 4),
            "reward": round(final_score, 4),
            "details": details,
            "step_penalty": step_penalty
        }

    def _find_current_scenario(self) -> Optional[Dict[str, Any]]:
        """Find the scenario matching current event."""
        if self.current_event is None:
            return None
        for scenario in self.task_scenarios:
            if scenario["event_id"] == self.current_event.event_id:
                return scenario
        return None


# OpenEnv API compliance check
def validate_openenv_api():
    """Validate the environment implements required OpenEnv API."""
    env = AiSecurityEnv()
    
    # Check required methods
    assert hasattr(env, 'reset'), "Missing reset() method"
    assert hasattr(env, 'step'), "Missing step() method"
    assert callable(env.reset), "reset is not callable"
    assert callable(env.step), "step is not callable"
    
    # Test reset
    state = env.reset()
    assert isinstance(state, dict), "reset() should return dict"
    assert "event_id" in state, "state missing event_id"
    
    # Test step
    action: Dict[str, Any] = {
        "allow": False,
        "threat_type": "data_exfiltration",
        "response_action": "block"
    }
    obs: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]
    obs, reward, done, info = env.step(action)
    assert isinstance(obs, dict), "observation should be dict"
    assert isinstance(reward, float), "reward should be float"
    assert isinstance(done, bool), "done should be bool"
    assert isinstance(info, dict), "info should be dict"
    
    print("[OK] OpenEnv API compliance validated")


if __name__ == "__main__":
    validate_openenv_api()
