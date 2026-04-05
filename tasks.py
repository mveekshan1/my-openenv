"""
Task definitions and grading utilities for AI Security Environment
Includes advanced grading robustness with semantic normalization.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


# =============================================================================
# GRADING ROBUSTNESS: Semantic Normalization
# =============================================================================

class SemanticNormalizer:
    """
    Normalizes agent outputs for semantic equivalence.
    Enables flexible grading while maintaining determinism.
    """

    # Mapping of equivalent response actions
    RESPONSE_ACTION_EQUIVALENCES = {
        # Block IP variations
        "block_ip": ["block_ip", "block ip", "ip_block", "blockip", "blockip"],
        "block_endpoint": ["block_endpoint", "block endpoint", "endpoint_block", "blockendpoint"],
        "block": ["block", "deny", "reject"],
        "allow": ["allow", "permit", "accept"],
        "block + alert": ["block + alert", "block+alert", "block_and_alert", "alert_and_block"],
        "alert": ["alert", "notify", "warn"],
        
        # Threat type variations
        "data_exfiltration": ["data_exfiltration", "data exfiltration", "exfiltration", "data-exfiltration"],
        "brute_force": ["brute_force", "brute force", "bruteforce", "brute-force"],
        "intrusion": ["intrusion", "intrusion_attack", "intrusion attack"],
        "insider_threat": ["insider_threat", "insider threat", "insider-threat", "insiderthreat"],
        "none": ["none", "unknown", "normal"],
    }

    # Reverse mapping for normalization
    _NORMALIZATION_MAP: Dict[str, str] = {}

    @classmethod
    def _build_map(cls):
        """Build reverse normalization map on first use"""
        if not cls._NORMALIZATION_MAP:
            for canonical, variants in cls.RESPONSE_ACTION_EQUIVALENCES.items():
                for variant in variants:
                    cls._NORMALIZATION_MAP[variant.lower().strip()] = canonical

    @classmethod
    def normalize(cls, value: str) -> str:
        """
        Normalize a string to canonical form.
        Returns lowercased, stripped, canonical version.
        If no mapping exists, returns original lowercased version.
        """
        cls._build_map()
        normalized = value.lower().strip() if isinstance(value, str) else str(value).lower().strip()
        return cls._NORMALIZATION_MAP.get(normalized, normalized)

    @classmethod
    def is_equivalent(cls, actual: str, expected: str) -> bool:
        """Check if two values are semantically equivalent"""
        if actual == expected:
            return True
        
        normalized_actual = cls.normalize(actual)
        normalized_expected = cls.normalize(expected)
        
        return normalized_actual == normalized_expected


class TaskDifficulty(Enum):
    """Task difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class TaskDefinition:
    """Task definition with input and expected output"""
    name: str
    difficulty: TaskDifficulty
    description: str
    event_id: str
    logs: List[str]
    user_role: str
    data_sensitivity: str
    expected_output: Dict[str, Any]


# Task Registry
TASKS = {
    "data_leakage_prevention": TaskDefinition(
        name="Data Leakage Prevention",
        difficulty=TaskDifficulty.EASY,
        description="Detect and block attempts to exfiltrate high-sensitivity data",
        event_id="EVT-001",
        logs=[
            "User initiated data export",
            "2GB data transfer to external IP: 203.0.113.10"
        ],
        user_role="employee",
        data_sensitivity="high",
        expected_output={
            "allow": False,
            "threat_type": "data_exfiltration",
            "response_action": "block",
            "reason": "Attempt to exfiltrate high-sensitivity customer data"
        }
    ),
    "threat_detection_brute_force": TaskDefinition(
        name="Threat Detection: Brute Force",
        difficulty=TaskDifficulty.MEDIUM,
        description="Identify brute-force login attack and block source IP",
        event_id="EVT-002",
        logs=[
            "Failed login attempt from 192.168.1.50 (attempt 1/3)",
            "Failed login attempt from 192.168.1.50 (attempt 2/3)",
            "Failed login attempt from 192.168.1.50 (attempt 3/3)",
            "Successful login from 192.168.1.50 after failed attempts"
        ],
        user_role="unknown",
        data_sensitivity="medium",
        expected_output={
            "allow": False,
            "threat_type": "brute_force",
            "response_action": "block_ip",
            "firewall_rule": {
                "rule_action": "block",
                "target": "ip",
                "duration": "1h"
            },
            "reason": "Brute-force attack detected: 3 failed attempts followed by success"
        }
    ),
    "advanced_threat_response": TaskDefinition(
        name="Advanced Threat Response: Intrusion Detection",
        difficulty=TaskDifficulty.HARD,
        description="Identify multi-stage intrusion attack with severity assessment",
        event_id="EVT-003",
        logs=[
            "Unusual data transfer volume: 50GB in 5 minutes (5x baseline)",
            "Access from unknown IP 203.0.113.45 (reputation: unknown)",
            "Admin login at 02:30 UTC (outside business hours - anomaly)",
            "Database query on sensitive_customers table (rare access pattern)",
            "Concurrent connection from multiple IPs (potential lateral movement)"
        ],
        user_role="admin",
        data_sensitivity="high",
        expected_output={
            "allow": False,
            "threat_type": "intrusion",
            "response_action": "block + alert",
            "firewall_rule": {
                "rule_action": "block",
                "target": "ip",
                "duration": "24h"
            },
            "severity": "critical",
            "reason": "Multi-stage intrusion detected: unusual patterns, off-hours access, lateral movement"
        }
    ),
    "insider_threat_detection": TaskDefinition(
        name="Insider Threat Detection: Anomalous Privileged Access",
        difficulty=TaskDifficulty.HARD,
        description="Distinguish between legitimate and malicious insider activity with conflicting signals",
        event_id="EVT-004",
        logs=[
            "User: john.smith@company.com (Finance Manager, 3-year tenure, clean record)",
            "Authentication: Successful login from usual office IP 10.0.1.150 at 09:15 UTC",
            "Action: Accessed HR_salaries.xlsx (legitimate business need)",
            "Flag: File accessed outside normal SOC business hours (02:30 UTC) - UNEXPECTED",
            "Warning: Downloaded 2.3GB financial data to personal cloud storage (Dropbox)",
            "Context: User recently passed security awareness training",
            "Background: Recent layoff announcements in finance department (motive: possible)",
            "History: No prior anomalies, clean background check, bonded employee"
        ],
        user_role="finance_manager",
        data_sensitivity="high",
        expected_output={
            "allow": False,
            "threat_type": "insider_threat",
            "response_action": "block + alert",
            "severity": "medium",
            "confidence": "high",
            "reasoning": "Despite clean history and legitimate access, off-hours access + cloud upload of sensitive financial data indicates potential insider threat. Recommend investigation.",
            "firewall_rule": {
                "rule_action": "block",
                "target": "endpoint",
                "duration": "12h"
            }
        }
    )
}


class GradingEngine:
    """
    Deterministic grading engine for security tasks.
    Enhanced with semantic normalization for flexible yet rigorous evaluation.
    """

    # Scoring weights
    WEIGHTS = {
        "allow": 0.3,
        "threat_type": 0.3,
        "response_action": 0.2,
        "firewall_rule": 0.2
    }

    @staticmethod
    def grade(task: TaskDefinition, agent_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade agent output against expected output with semantic normalization.
        Uses GradingEngine.grade_with_normalization() for flexible comparison.

        Returns:
            {
                "score": float [0.0, 1.0],
                "reward": float [0.0, 1.0],
                "details": {field: {expected, actual, score, match}},
                "passed": bool,
                "feedback": str
            }
        """
        details: Dict[str, Dict[str, Any]] = {}
        total_score: float = 0.0

        # Grade "allow" field (strict boolean match)
        expected_allow: bool = task.expected_output.get("allow", False)
        actual_allow: Optional[bool] = agent_output.get("allow")
        allow_match = expected_allow == actual_allow
        allow_score = 1.0 if allow_match else 0.0
        details["allow"] = {
            "expected": expected_allow,
            "actual": actual_allow,
            "score": allow_score,
            "match": allow_match
        }
        total_score += allow_score * GradingEngine.WEIGHTS["allow"]

        # Grade "threat_type" field (with semantic normalization)
        expected_threat: str = task.expected_output.get("threat_type", "")
        actual_threat: Optional[str] = agent_output.get("threat_type")
        threat_match = GradingEngine._match_with_normalization(actual_threat, expected_threat)
        threat_score = 1.0 if threat_match else 0.0
        details["threat_type"] = {
            "expected": expected_threat,
            "actual": actual_threat,
            "score": threat_score,
            "match": threat_match
        }
        total_score += threat_score * GradingEngine.WEIGHTS["threat_type"]

        # Grade "response_action" field (with semantic normalization)
        expected_action: str = task.expected_output.get("response_action", "")
        actual_action: Optional[str] = agent_output.get("response_action")
        action_match = GradingEngine._match_with_normalization(actual_action, expected_action)
        action_score = 1.0 if action_match else 0.0
        details["response_action"] = {
            "expected": expected_action,
            "actual": actual_action,
            "score": action_score,
            "match": action_match
        }
        total_score += action_score * GradingEngine.WEIGHTS["response_action"]

        # Grade "firewall_rule" field (strict match, only if expected)
        expected_rule: Optional[Dict[str, Any]] = task.expected_output.get("firewall_rule")
        actual_rule: Optional[Dict[str, Any]] = agent_output.get("firewall_rule")
        rule_match: bool = True
        
        if expected_rule is not None:
            if not isinstance(actual_rule, dict):
                rule_match = False
            else:
                rule_match = (
                    actual_rule.get("rule_action") == expected_rule.get("rule_action") and
                    actual_rule.get("target") == expected_rule.get("target") and
                    actual_rule.get("duration") == expected_rule.get("duration")
                )
        else:
            # No firewall rule expected
            rule_match = actual_rule is None

        rule_score = 1.0 if rule_match else 0.0
        details["firewall_rule"] = {
            "expected": expected_rule,
            "actual": actual_rule,
            "score": rule_score,
            "match": rule_match
        }
        total_score += rule_score * GradingEngine.WEIGHTS["firewall_rule"]

        # Final score
        final_score = min(1.0, max(0.0, total_score))
        passed = final_score >= 0.8  # 80% threshold

        # Generate feedback
        feedback = GradingEngine._generate_feedback(details, passed)

        return {
            "score": round(final_score, 4),
            "reward": round(final_score, 4),
            "details": details,
            "passed": passed,
            "feedback": feedback,
            "max_score": 1.0
        }

    @staticmethod
    def _match_with_normalization(actual: Any, expected: Any) -> bool:
        """
        Check if actual and expected match using semantic normalization.
        Deterministic: same inputs always produce same output.
        """
        if actual is None or expected is None:
            return actual == expected
        
        # Convert to strings and normalize
        actual_str = str(actual).strip()
        expected_str = str(expected).strip()
        
        # Use semantic normalizer
        return SemanticNormalizer.is_equivalent(actual_str, expected_str)

    @staticmethod
    def _generate_feedback(details: Dict[str, Any], passed: bool) -> str:
        """Generate human-readable grading feedback"""
        feedback_parts: List[str] = []

        if passed:
            feedback_parts.append("[PASS] Excellent! All critical fields matched expected output.")
        else:
            feedback_parts.append("[FAIL] Response did not match expected output. Review:")

        for field, result in details.items():
            if not result["match"]:
                feedback_parts.append(
                    f"  - {field}: expected '{result['expected']}', got '{result['actual']}'"
                )

        return " ".join(feedback_parts)


class TaskRegistry:
    """Registry for task management"""

    @staticmethod
    def get_task(task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID"""
        return TASKS.get(task_id)

    @staticmethod
    def list_tasks() -> List[Dict[str, Any]]:
        """List all available tasks"""
        return [
            {
                "id": task_id,
                "name": task.name,
                "difficulty": task.difficulty.value,
                "description": task.description
            }
            for task_id, task in TASKS.items()
        ]

    @staticmethod
    def get_tasks_by_difficulty(difficulty: str) -> List[TaskDefinition]:
        """Get all tasks of a specific difficulty level"""
        return [
            task for task in TASKS.values()
            if task.difficulty.value == difficulty
        ]


# Testing and validation
def test_grading():
    """Test grading engine including semantic normalization"""
    task: TaskDefinition = TASKS["data_leakage_prevention"]
    
    # Perfect match
    output: Dict[str, Any] = {
        "allow": False,
        "threat_type": "data_exfiltration",
        "response_action": "block"
    }
    result: Dict[str, Any] = GradingEngine.grade(task, output)
    assert result["score"] == 1.0, f"Expected score 1.0, got {result['score']}"
    assert result["passed"], "Expected to pass"
    print(f"[PASS] Perfect match test passed: {result['score']}")

    # Partial match
    output: Dict[str, Any] = {
        "allow": False,
        "threat_type": "brute_force",  # Wrong
        "response_action": "block"
    }
    result = GradingEngine.grade(task, output)
    assert 0.6 <= result["score"] < 1.0, f"Expected partial score, got {result['score']}"
    print(f"[PASS] Partial match test passed: {result['score']}")

    # Semantic normalization test: "block_ip" vs "block ip"
    task_brute: TaskDefinition = TASKS["threat_detection_brute_force"]
    output: Dict[str, Any] = {
        "allow": False,
        "threat_type": "brute_force",
        "response_action": "block ip",  # Semantically equivalent to "block_ip"
        "firewall_rule": {
            "rule_action": "block",
            "target": "ip",
            "duration": "1h"
        }
    }
    result = GradingEngine.grade(task_brute, output)
    assert result["passed"], f"Semantic normalization failed: score={result['score']}"
    print(f"[PASS] Semantic normalization test passed: {result['score']}")

    # Complete mismatch
    output: Dict[str, Any] = {
        "allow": True,  # Wrong
        "threat_type": "brute_force",  # Wrong for EVT-001
        "response_action": "allow",  # Wrong
        "firewall_rule": {"rule_action": "allow", "target": "ip", "duration": "1h"}  # Unexpected
    }
    result = GradingEngine.grade(task, output)
    assert result["score"] < 0.5, f"Expected low score, got {result['score']}"
    print(f"[PASS] Complete mismatch test passed: {result['score']}")


if __name__ == "__main__":
    print("Task Registry (4 Tasks):")
    for task in TaskRegistry.list_tasks():
        print(f"  - {task['name']} [{task['difficulty']}]")
    
    print("\nRunning grading tests...")
    test_grading()
    print("\nTesting semantic normalization...")
    assert SemanticNormalizer.is_equivalent("block_ip", "block ip")
    assert SemanticNormalizer.is_equivalent("block+alert", "block + alert")
    assert SemanticNormalizer.is_equivalent("insider_threat", "insider threat")
    print("[OK] Semantic normalization working correctly")
    print("[OK] All grading tests passed")
