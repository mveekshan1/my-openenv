# AI Security OpenEnv

## Overview

AI Security OpenEnv is a deterministic security environment for evaluating AI agents on threat detection and incident response tasks. The environment simulates realistic cybersecurity scenarios where agents must analyze security events, classify threats, and recommend appropriate containment actions. Each scenario presents a complete security event with logs, user context, and data sensitivity indicators.

The environment follows the OpenEnv framework (state-action-reward-done pattern) and is designed for benchmarking AI decision-making in security operations center (SOC) workflows.

## Problem Statement

Real-world security operations require rapid threat classification and response decisions. Security analysts must:

1. Analyze incoming security events with incomplete information
2. Classify the type of threat present
3. Recommend immediate containment or remediation actions
4. Balance between false positives (blocking legitimate activity) and false negatives (missing actual threats)

Automating these decisions requires AI agents capable of pattern recognition, contextual reasoning, and understanding security trade-offs. Traditional rules-based systems lack the flexibility to handle novel attack patterns, while AI agents must achieve high accuracy on diverse threat scenarios.

This environment provides a controlled benchmark for measuring AI capability in security decision-making across varying threat complexity.

## Solution

AI Security OpenEnv addresses this problem through:

1. **Deterministic Environment**: Each security event is reproducible, enabling fair agent comparison
2. **Dynamic Scenario Generation**: Generates randomized threat scenarios with varying complexity levels (easy, medium, hard)
3. **Graded Complexity**: Tasks range from obvious threats (easy) to cases with conflicting signals (hard)
4. **Structured Evaluation**: Weighted scoring across decision components (allow/block, threat classification, response action, firewall rules)
5. **Semantic Flexibility**: Accepts equivalent formatting while maintaining strict semantic requirements
6. **Production Realism**: Security events mirror real SOC alerts with logs, anomalies, and context

## Environment Design

### State

The environment presents each security event as a structured dictionary containing:

```python
{
    "event_id": str,              # Unique identifier (e.g., "EVT-001")
    "logs": List[str],            # Security event details and logs
    "user_role": str,             # Role of user involved (employee, admin, unknown)
    "data_sensitivity": str,      # Classification level (low, medium, high)
    "status": str,                # Event status (open, closed, escalated)
    "decision": Optional[Dict]    # Previous decision if any
}
```

The agent receives complete information needed to make a decision but must reason under uncertainty (e.g., unknown IP reputation, incomplete user history).

### Action

The agent responds with a structured action dictionary:

```python
{
    "allow": bool,                    # True to allow, False to block
    "threat_type": str,               # Classification (e.g., "data_exfiltration", "brute_force")
    "response_action": str,           # Action taken (e.g., "block", "block + alert", "monitor")
    "firewall_rule": Optional[Dict],  # Optional firewall configuration if action is block
    "severity": Optional[str]         # Optional severity indicator
}
```

### Observation

After each step, the environment returns:

```python
observation    # Updated state (Dict[str, Any])
reward         # Score [0.0, 1.0] based on grading
done           # Boolean indicating episode completion (always True for single-step events)
info           # Metadata dictionary containing:
               # - "grade": Detailed grading breakdown
               # - "expected_output": Correct answer
               # - "feedback": Human-readable explanation
```

### Termination

Episodes are single-step (one event → one decision):

1. Environment presents a security event via `reset()`
2. Agent analyzes and generates response via `step(action)`
3. Environment grades response and returns reward
4. Episode terminates (done=True)

This single-step design reflects real SOC workflows where decisions must be made immediately upon alert arrival.

## Tasks

### Task 1 — Data Leakage Prevention (Easy)

**Objective**: Detect and block unauthorized data exfiltration

**Input**:
```
Event ID: EVT-001
User Role: employee
Data Sensitivity: HIGH
Logs:
  - User initiated data export (2GB)
  - Detected transfer to external IP 203.0.113.10
  - Transfer destination unknown
```

**Expected Output**:
```json
{
  "allow": false,
  "threat_type": "data_exfiltration",
  "response_action": "block"
}
```

**Grading**: Boolean match on all components (0.0 = any mismatch, 1.0 = perfect match)

---

### Task 2 — Brute Force Detection (Medium)

**Objective**: Identify brute-force authentication attack and implement containment

**Input**:
```
Event ID: EVT-002
User Role: unknown
Data Sensitivity: MEDIUM
Logs:
  - Failed login attempt 1/3 from 192.168.1.50
  - Failed login attempt 2/3 from 192.168.1.50
  - Failed login attempt 3/3 from 192.168.1.50
  - Successful login from 192.168.1.50 after failed attempts
```

**Expected Output**:
```json
{
  "allow": false,
  "threat_type": "brute_force",
  "response_action": "block_ip",
  "firewall_rule": {
    "action": "block",
    "target": "ip",
    "duration": "1h"
  }
}
```

**Grading**: Weighted component matching (allow: 0.3, threat_type: 0.3, response_action: 0.2, firewall_rule: 0.2)

---

### Task 3 — Intrusion Response (Hard)

**Objective**: Identify multi-stage intrusion with correlated anomalies

**Input**:
```
Event ID: EVT-003
User Role: admin
Data Sensitivity: HIGH
Logs:
  - Unusual data volume: 50GB in 5 minutes (5x baseline)
  - Login from unknown IP 203.0.113.45
  - Admin access at 02:30 UTC (outside business hours)
  - Database query on sensitive_customers table (rare pattern)
  - Concurrent connections from multiple IPs (possible lateral movement)
```

**Expected Output**:
```json
{
  "allow": false,
  "threat_type": "intrusion",
  "response_action": "block + alert",
  "firewall_rule": {
    "action": "block",
    "target": "ip",
    "duration": "24h"
  },
  "severity": "critical"
}
```

**Grading**: Multi-factor analysis with weighted components, emphasis on correlation detection

---

### Task 4 — Insider Threat Detection (Advanced)

**Objective**: Distinguish malicious from legitimate insider activity under conflicting signals

**Input**:
```
Event ID: EVT-004
User Role: finance_manager
Data Sensitivity: HIGH
Context: 3-year tenure, clean history, recent security training
Logs:
  - Successful login from usual office IP 10.0.1.150 at 09:15 UTC
  - Legitimate access: HR_salaries.xlsx
  - ANOMALY: File accessed at 02:30 UTC (outside hours)
  - ANOMALY: 2.3GB financial data downloaded to personal Dropbox
  - CONTEXT: Recent layoffs announced (possible motive)
  - HISTORY: Clean background check, bonded, no prior incidents
```

**Expected Output**:
```json
{
  "allow": false,
  "threat_type": "insider_threat",
  "response_action": "block + alert",
  "severity": "medium",
  "confidence": "high",
  "reasoning": "Despite clean history and legitimate file access, off-hours access combined with exfiltration to unmanaged storage indicates potential threat. Recommend investigation."
}
```

**Grading**: Nuanced multi-factor analysis requiring balancing conflicting signals

---

## Grading Logic

### Scoring System

All grading is deterministic and transparent. Each task component is scored independently and combined via weighted averaging.

**Component Weights**:
| Component | Weight | Criteria |
|-----------|--------|----------|
| `allow` | 0.3 | Strict boolean (allowed/blocked) |
| `threat_type` | 0.3 | Threat classification accuracy |
| `response_action` | 0.2 | Recommended security action |
| `firewall_rule` | 0.2 | Firewall rule correctness (if required) |

**Semantic Normalization**:
- `"block_ip"` ≈ `"block ip"` ≈ `"ip_block"` (all normalized to canonical form)
- `"insider_threat"` ≈ `"insider threat"` ≈ `"insiderthreat"`
- Whitespace and punctuation are normalized; semantics are strict

**Partial Scoring**:
- Getting 3 of 4 components correct yields 0.75 score (75%)
- Weighted components: classification accuracy (0.3) weighted equal to decision (0.3)
- Firewall rules weighted lower (0.2) as they are secondary to core decision

### Reward Calculation

```
reward = score - step_penalty
score = weighted_sum(component_scores)
step_penalty = 0 (single-step episodes)
```

Perfect match: reward = 1.0
Three components correct: reward = 0.75
One component correct: reward ≤ 0.4

---

## Reward System

### Reward Function

Each episode generates a reward in range [0.0, 1.0]:

- **1.0**: Perfect match on all components
- **0.75**: 3/4 components correct
- **0.50**: 2/4 components correct or major decision error with correct threat type
- **0.25**: 1/4 components correct
- **0.0**: No components correct or critical decision failure

### Penalties

- **Decision Reversal**: Blocking safe traffic or allowing threats incurs highest penalty
- **Classification Error**: Incorrect threat typing reduces score but does not eliminate reward if action is appropriate
- **Incomplete Response**: Missing required components (e.g., firewall rule when needed) fails that component

### Aggregation

Over multiple episodes:
- **Average Reward**: Mean score across all episodes
- **Success Rate**: Percentage of episodes scoring ≥0.8
- **Risk Level**:
  - LOW: average_reward ≥ 0.85 (production-ready)
  - MEDIUM: average_reward 0.70-0.84 (needs improvement)
  - HIGH: average_reward < 0.70 (not deployment-ready)

---

## Project Structure

```
ai-security-openenv/
├── environment.py           # OpenEnv environment (AiSecurityEnv class)
├── tasks.py                 # Task definitions and grading engine
├── inference.py             # Baseline agent and evaluation utilities
├── app.py                   # Gradio interface for dashboard
├── server.py                # Flask server for API testing
├── openenv.yaml             # Configuration and metadata
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── test_dynamic.py          # Tests for dynamic scenario generation
├── test_grading.py          # Tests for grading functionality
├── LICENSE                  # MIT License
└── README.md                # This documentation
```

---

## Setup Instructions

### Local Setup

**Prerequisites**: Python 3.8+, pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from environment import AiSecurityEnv; print('Installation successful')"
```

### Docker

**Prerequisites**: Docker

```bash
# Build image
docker build -t ai-security-openenv .

# Run evaluation
docker run ai-security-openenv python inference.py

# Run with custom parameters
docker run ai-security-openenv python inference.py --mode benchmark --episodes 10
```

---

## Usage

### Running the Dashboard

```bash
python app.py
```

Visit `http://localhost:7860` to access the Gradio web interface. The dashboard displays:
- Live security event with full context
- Agent decision breakdown
- Metrics (average reward, success rate, risk level)
- Execution output with detailed grading

### Running Evaluation

```bash
# Run baseline agent benchmark
python inference.py --mode benchmark --episodes 10

# Output includes average reward, success rate, and risk assessment
```

### Programmatic Usage

```python
from environment import AiSecurityEnv

# Initialize environment with dynamic scenarios
env = AiSecurityEnv(seed=42, use_dynamic=True)

# Or use static scenarios for reproducibility
# env = AiSecurityEnv(seed=42, use_dynamic=False)

# Get security event
state = env.reset()

# Generate action (your agent)
action = {
    "allow": False,
    "threat_type": state.get("detected_threat"),
    "response_action": "block"
}

# Execute and receive grade
observation, reward, done, info = env.step(action)

print(f"Reward: {reward}")
print(f"Grade Details: {info['grade']}")
```

---

## API Testing

For OpenEnv compliance testing, a Flask server is provided to test the API endpoints independently:

```bash
# Start the test server
python server.py

# Test reset endpoint
curl -X POST http://localhost:8000/reset

# Test step endpoint
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"allow": false, "threat_type": "data_exfiltration", "response_action": "block"}}'
```

**Endpoints**:
- `POST /reset` - Reset environment and return observation directly
- `POST /step` - Execute action and return {observation, reward, done, info}
- `GET /state` - Get current environment state
- `GET /health` - Health check

---

## Inference

The inference module provides:

1. **Baseline Agent**: Pattern-matching heuristic for threat detection
2. **LLM Adapter**: Template for integrating OpenAI-compatible models
3. **Evaluation Harness**: Runs multiple episodes and aggregates metrics
4. **Dynamic Scenario Support**: Environment can generate randomized scenarios or use predefined static tasks

**Configuration**:
```
API_BASE_URL: LLM endpoint (default: OpenAI)
MODEL_NAME: Model identifier (default: gpt-4)
use_dynamic: Enable dynamic scenario generation (default: True)
```

The baseline agent uses deterministic pattern matching and achieves 70-80% average reward, establishing a clear performance baseline. Dynamic scenarios provide unlimited variety while maintaining deterministic grading.

---

## Hugging Face Deployment

This project is configured for automatic deployment on Hugging Face Spaces.

**Deployment Steps**:
1. Create new Spaces repository on huggingface.co
2. Push this repository to Spaces
3. Spaces automatically detects the Dockerfile and builds the image
4. Application becomes available at `huggingface.co/spaces/your-username/ai-security-openenv`

**Features**:
- Gradio web interface accessible immediately
- Automatic rebuilds on repository updates
- Public sharing link for evaluation

---

## Evaluation

### Deterministic Grading

All evaluations are fully deterministic:
- Same input → Same output (guaranteed)
- No randomness in grading logic
- Reproducible across runs (use seed=42 for environment)

### Reproducibility

Set seed for reproducible scenario selection:

```python
env = AiSecurityEnv(seed=42)
```

With identical seed, the environment generates identical scenarios in identical order.

### Difficulty Scaling

- **Easy**: Single clear threat signal (Data Leakage)
- **Medium**: Pattern recognition required (Brute Force sequence)
- **Hard**: Multi-factor analysis, conflicting signals (Intrusion, Insider Threat)

**Dynamic Scenarios**: Set `use_dynamic=True` for unlimited randomized scenarios, or `use_dynamic=False` for reproducible static tasks.

Baseline agent performance: Easy 100%, Medium 80%, Hard 30-40%

---

## Limitations

1. **Simulated Environment**: Scenarios are rule-generated, not from production systems
2. **Static Rules**: No real-time threat intelligence or external data feeds
3. **Baseline Agent**: Pattern-matching only; no learning or adaptation
4. **Scenario Variety**: While dynamic generation provides unlimited scenarios, they follow predefined patterns rather than truly novel threats

---

## Future Improvements

- Extended threat scenario library (APT indicators, zero-days, insider threats)
- Multi-agent comparative evaluation
- Integration with real threat intelligence feeds
- Enhanced dynamic scenario generation with more complex patterns
- REST API for remote evaluation
- Advanced visualization and reporting

---

## License

MIT License
