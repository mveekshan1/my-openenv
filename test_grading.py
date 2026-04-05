#!/usr/bin/env python
"""Test grading with dynamic scenarios"""

from environment import AiSecurityEnv, ScenarioGenerator

# Generate a dynamic scenario
scenario = ScenarioGenerator.generate_scenario("easy")
print("Scenario difficulty:", scenario.get("difficulty"))
print("Scenario expected:", scenario.get("expected"))

# Test environment
env = AiSecurityEnv(seed=42, use_dynamic=True)
state = env.reset()
print("\nEnvironment event_id:", state.get('event_id'))

# Make decision matching expected
action = {'allow': False, 'threat_type': 'data_exfiltration', 'response_action': 'block'}
obs, reward, done, info = env.step(action)
print("Reward:", reward)
print("Grade score:", info.get('grade', {}).get('score'))
print("Grade details:", info.get('grade', {}).get('details'))
