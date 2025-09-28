"""Educational logging enhancements for VMT EconSim.

Provides educational context and explanations for economic events
to improve learning value of the debug logging system.
"""

from __future__ import annotations

import os
from typing import Optional


def explain_utility_change(old_utility: float, new_utility: float, 
                          reason: str = "", good_type: str = "") -> str:
    """Generate educational explanation for utility changes.
    
    Args:
        old_utility: Previous utility value
        new_utility: New utility value  
        reason: Reason for the change (e.g., "trade", "collection")
        good_type: Type of good involved
        
    Returns:
        Educational explanation string
    """
    delta = new_utility - old_utility
    
    if abs(delta) < 0.01:
        return f"Utility unchanged ({old_utility:.2f}) - no significant economic impact"
    
    direction = "increased" if delta > 0 else "decreased"
    magnitude = "significantly" if abs(delta) > 1.0 else "slightly"
    
    explanation = f"Utility {direction} {magnitude} from {old_utility:.2f} to {new_utility:.2f} (Δ{delta:+.2f})"
    
    if reason == "trade":
        if delta > 0:
            explanation += " - beneficial trade improving agent's welfare through specialization"
        else:
            explanation += " - trade resulted in net loss, possibly due to suboptimal exchange"
    elif reason == "collection":
        if good_type:
            explanation += f" - collected {good_type}, increasing wealth and consumption possibilities"
        else:
            explanation += " - resource collection expanded agent's economic opportunities"
    elif reason == "deposit":
        explanation += " - secured goods at home base, preserving wealth for future use"
    elif reason:
        explanation += f" - {reason}"
        
    return explanation


def explain_trade_decision(agent1_utility_gain: float, agent2_utility_gain: float,
                          good1: str, good2: str) -> str:
    """Generate educational explanation for trade decisions.
    
    Args:
        agent1_utility_gain: Utility gain for first agent
        agent2_utility_gain: Utility gain for second agent
        good1: Good given by agent 1
        good2: Good given by agent 2
        
    Returns:
        Educational explanation string
    """
    if agent1_utility_gain > 0 and agent2_utility_gain > 0:
        return (f"Mutually beneficial trade: both agents gain utility "
                f"(Δ{agent1_utility_gain:+.2f}, Δ{agent2_utility_gain:+.2f}) "
                f"by exchanging {good1}↔{good2}, demonstrating gains from specialization")
    elif agent1_utility_gain > 0:
        return (f"Agent 1 benefits more (Δ{agent1_utility_gain:+.2f}) than Agent 2 "
                f"(Δ{agent2_utility_gain:+.2f}) in {good1}↔{good2} exchange")
    elif agent2_utility_gain > 0:
        return (f"Agent 2 benefits more (Δ{agent2_utility_gain:+.2f}) than Agent 1 "
                f"(Δ{agent1_utility_gain:+.2f}) in {good1}↔{good2} exchange")
    else:
        return (f"Surprising trade with negative utility for both agents "
                f"(Δ{agent1_utility_gain:+.2f}, Δ{agent2_utility_gain:+.2f}) - "
                f"possible computational error or forced exchange")


def explain_agent_mode(old_mode: str, new_mode: str, context: str = "") -> str:
    """Generate educational explanation for agent mode transitions.
    
    Args:
        old_mode: Previous agent mode
        new_mode: New agent mode
        context: Additional context about the transition
        
    Returns:
        Educational explanation string
    """
    transitions = {
        ("idle", "forage"): "Agent begins resource collection to increase wealth",
        ("forage", "return_home"): "Agent heads home to secure collected resources", 
        ("return_home", "idle"): "Agent completed deposit and awaits next opportunity",
        ("idle", "move_to_partner"): "Agent identified beneficial trading partner",
        ("move_to_partner", "idle"): "Agent completed or abandoned trade attempt",
        ("forage", "idle"): "Agent paused foraging, possibly due to competition or better opportunities",
        ("return_home", "forage"): "Agent interrupted return to pursue immediate resource",
    }
    
    key = (old_mode.lower(), new_mode.lower())
    base_explanation = transitions.get(key, f"Agent changed from {old_mode} to {new_mode}")
    
    if context:
        if "stagnation" in context.lower():
            base_explanation += " (triggered by stagnation recovery mechanism)"
        elif "deposit" in context.lower():
            base_explanation += " (carrying goods to secure)"
        elif "target" in context.lower():
            base_explanation += " (responding to environmental opportunities)"
            
    return base_explanation


def explain_decision_logic(decision_type: str, target_info: str = "", 
                          utility_gain: float = 0.0, distance: int = 0) -> str:
    """Generate educational explanation for agent decision-making.
    
    Args:
        decision_type: Type of decision (resource, partner, idle)
        target_info: Information about the target
        utility_gain: Expected utility gain
        distance: Distance to target
        
    Returns:
        Educational explanation string
    """
    if decision_type == "resource":
        explanation = f"Targeting resource for expected utility gain of {utility_gain:.2f}"
        if distance > 0:
            explanation += f" at distance {distance} (cost-benefit analysis)"
        if utility_gain > 1.0:
            explanation += " - high-value target justifies movement cost"
        elif utility_gain > 0.1:
            explanation += " - moderate benefit worth pursuing"
        else:
            explanation += " - marginal benefit, efficient market behavior"
    elif decision_type == "partner":
        explanation = f"Seeking trade partner for mutual benefit (expected Δ{utility_gain:+.2f})"
        if distance > 0:
            explanation += f" at distance {distance}"
        explanation += " - demonstrates market-seeking behavior"
    elif decision_type == "idle":
        explanation = "No beneficial opportunities identified - rational economic inaction"
    else:
        explanation = f"Decision: {decision_type}"
        if utility_gain != 0:
            explanation += f" (Δ{utility_gain:+.2f})"
            
    return explanation


def get_economic_context(phase: Optional[int] = None, agents: int = 0, 
                        resources: int = 0) -> str:
    """Generate economic context explanation for current simulation state.
    
    Args:
        phase: Current simulation phase
        agents: Number of agents
        resources: Number of available resources
        
    Returns:
        Economic context explanation
    """
    context = f"Market with {agents} economic agents and {resources} available resources"
    
    if resources == 0:
        context += " - scarcity conditions, expect increased competition"
    elif resources > agents * 2:
        context += " - abundant resources, expect efficient allocation"
    elif resources < agents:
        context += " - resource constraints driving competitive behavior"
    else:
        context += " - balanced resource availability"
        
    if phase is not None:
        phase_contexts = {
            1: "Initial market exploration phase",
            2: "Market development with emerging patterns", 
            3: "Mature market with established behaviors",
            4: "Advanced market with complex interactions"
        }
        context += f". {phase_contexts.get(phase, f'Phase {phase} market dynamics')}"
        
    return context


def should_add_educational_context() -> bool:
    """Check if educational context should be added to log messages."""
    return os.environ.get("ECONSIM_LOG_EXPLANATIONS") == "1"


def should_explain_decisions() -> bool:
    """Check if decision reasoning should be added to log messages."""
    return os.environ.get("ECONSIM_LOG_DECISION_REASONING") == "1"


# Additional utility functions can be added here as needed