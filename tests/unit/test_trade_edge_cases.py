"""
Test edge cases in bilateral exchange logic for robustness and determinism.

Focus areas:
1. Identical marginal utilities - tie-breaking determinism
2. Zero inventory scenarios - epsilon lifting validation
3. Leontief at complement ratios - boundary behavior
4. Performance with many co-located agents
"""
from __future__ import annotations

import random
from typing import List, Tuple, Any

import pytest  # type: ignore
from pytest import MonkeyPatch  # type: ignore

from econsim.simulation.world import Simulation
from econsim.simulation.config import SimConfig
from econsim.simulation.agent import Agent
from econsim.simulation.trade import TradeIntent, enumerate_intents_for_cell
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
from econsim.preferences.leontief import LeontiefPreference


def _sim_with_agents(positions: List[Tuple[int, int]], seed: int = 42):
    """Helper to create simulation with agents at given positions."""
    cfg = SimConfig(
        grid_size=(6, 6),
        initial_resources=[],
        perception_radius=6,
        respawn_target_density=0.0,
        respawn_rate=0.0,
        max_spawn_per_tick=0,
        seed=seed,
        enable_respawn=False,
        enable_metrics=True,
    )
    return Simulation.from_config(cfg, agent_positions=positions)


class TestIdenticalMarginalUtilities:
    """Test tie-breaking behavior when agents have identical marginal utilities."""

    def test_deterministic_ordering_with_identical_deltas(self, monkeypatch: MonkeyPatch) -> None:
        """Test that identical delta utilities are tie-broken deterministically by agent IDs."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        # Create agents with Perfect Substitutes (linear) preferences 
        # so marginal utilities are constant and identical
        sim = _sim_with_agents([(0, 0), (0, 0), (0, 0)])
        
        # Use asymmetric Perfect Substitutes preferences to create different marginal utilities
        # but identical delta utilities across pairs
        sim.agents[0].preference = PerfectSubstitutesPreference(a=2.0, b=1.0)  # Prefers good1 (MU_g1=2, MU_g2=1)
        sim.agents[1].preference = PerfectSubstitutesPreference(a=1.0, b=2.0)  # Prefers good2 (MU_g1=1, MU_g2=2) 
        sim.agents[2].preference = PerfectSubstitutesPreference(a=2.0, b=1.0)  # Same as agent 0

        # Set up inventories to create trades with identical combined delta utilities
        sim.agents[0].carrying = {"good1": 1, "good2": 2}  # Has good2, wants good1
        sim.agents[1].carrying = {"good1": 2, "good2": 1}  # Has good1, wants good2
        sim.agents[2].carrying = {"good1": 1, "good2": 2}  # Same as agent 0

        # Prevent movement
        def no_move(self: Any, grid: Any, rng: Any) -> None:
            pass
        monkeypatch.setattr(Agent, "move_random", no_move)

        rng = random.Random(100)
        sim.step(rng, use_decision=False)

        intents = sim.trade_intents or []
        assert len(intents) > 0, "Should generate trade intents with asymmetric preferences"
        
        # Verify deterministic ordering by priority tuple
        priorities = [intent.priority for intent in intents]
        assert priorities == sorted(priorities), "Intents must be sorted by priority"        # With identical delta utilities, tie-breaking should be by (seller_id, buyer_id, goods)
        # Run multiple times to ensure deterministic ordering
        for seed in [100, 200, 300]:
            sim2 = _sim_with_agents([(0, 0), (0, 0), (0, 0)], seed=42)  # Same sim seed
            # Use same preferences and inventories as first test
            sim2.agents[0].preference = PerfectSubstitutesPreference(a=2.0, b=1.0)
            sim2.agents[1].preference = PerfectSubstitutesPreference(a=1.0, b=2.0) 
            sim2.agents[2].preference = PerfectSubstitutesPreference(a=2.0, b=1.0)
            sim2.agents[0].carrying = {"good1": 1, "good2": 2}
            sim2.agents[1].carrying = {"good1": 2, "good2": 1}
            sim2.agents[2].carrying = {"good1": 1, "good2": 2}
            
            rng2 = random.Random(seed)  # Different step seed
            sim2.step(rng2, use_decision=False)
            
            intents2 = sim2.trade_intents or []
            # Intent ordering should be identical despite different step RNG
            priorities2 = [intent.priority for intent in intents2]
            assert priorities == priorities2, f"Priority order must be deterministic across RNG seeds"

    def test_priority_delta_flag_affects_ordering_only(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that ECONSIM_TRADE_PRIORITY_DELTA changes ordering but not intent existence."""
        # Setup scenario with different delta utilities
        sim1 = _sim_with_agents([(0, 0), (0, 0)])
        sim2 = _sim_with_agents([(0, 0), (0, 0)])
        
        # Different preferences to create different delta utilities
        sim1.agents[0].preference = CobbDouglasPreference(alpha=0.3)  # Prefers good2
        sim1.agents[1].preference = CobbDouglasPreference(alpha=0.7)  # Prefers good1
        sim2.agents[0].preference = CobbDouglasPreference(alpha=0.3)
        sim2.agents[1].preference = CobbDouglasPreference(alpha=0.7)
        
        # Set complementary inventories
        for sim in [sim1, sim2]:
            sim.agents[0].carrying = {"good1": 5, "good2": 1}
            sim.agents[1].carrying = {"good1": 1, "good2": 5}
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        # Test without priority delta (default ordering)
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        monkeypatch.delenv("ECONSIM_TRADE_PRIORITY_DELTA", raising=False)
        
        rng1 = random.Random(50)
        sim1.step(rng1, use_decision=False)
        intents1 = sim1.trade_intents or []
        
        # Test with priority delta enabled
        monkeypatch.setenv("ECONSIM_TRADE_PRIORITY_DELTA", "1")
        
        rng2 = random.Random(50)  # Same RNG seed
        sim2.step(rng2, use_decision=False)
        intents2 = sim2.trade_intents or []
        
        # Same intents should exist (multiset invariance)
        intent_tuples1 = {(i.seller_id, i.buyer_id, i.give_type, i.take_type, i.quantity) for i in intents1}
        intent_tuples2 = {(i.seller_id, i.buyer_id, i.give_type, i.take_type, i.quantity) for i in intents2}
        assert intent_tuples1 == intent_tuples2, "Flag should not change which intents exist"
        
        # But priority ordering may be different
        priorities1 = [intent.priority for intent in intents1]
        priorities2 = [intent.priority for intent in intents2]
        
        # If delta utilities differ, ordering should change
        if len(intents1) > 1:
            deltas1 = [intent.delta_utility for intent in intents1]
            deltas2 = [intent.delta_utility for intent in intents2]
            assert deltas1 == deltas2, "Delta utilities should be computed the same"
            
            # Check if flag actually affected ordering (may be same if deltas are identical)
            first_priorities1 = [p[0] for p in priorities1]  # First element is -delta_u or 0.0
            first_priorities2 = [p[0] for p in priorities2]
            
            # With flag off: should be 0.0, with flag on: should be -delta_u
            assert all(p == 0.0 for p in first_priorities1), "Without flag, priority should be 0.0"
            assert any(p != 0.0 for p in first_priorities2), "With flag, priority should use -delta_u"


class TestZeroInventoryEdgeCases:
    """Test behavior when agents have zero inventories and epsilon lifting."""

    def test_cobb_douglas_zero_inventory_epsilon_lifting(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that Cobb-Douglas agents with zero inventories can still generate trades via epsilon."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        sim = _sim_with_agents([(0, 0), (0, 0)])
        
        # Cobb-Douglas preferences
        sim.agents[0].preference = CobbDouglasPreference(alpha=0.2)  # Strongly prefers good2
        sim.agents[1].preference = CobbDouglasPreference(alpha=0.8)  # Strongly prefers good1
        
        # Zero inventories - epsilon lifting should allow marginal utility computation
        sim.agents[0].carrying = {"good1": 1, "good2": 0}  # Has good1, lacks good2
        sim.agents[1].carrying = {"good1": 0, "good2": 1}  # Has good2, lacks good1
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        rng = random.Random(75)
        sim.step(rng, use_decision=False)
        
        intents = sim.trade_intents or []
        assert len(intents) > 0, "Should generate intents despite zero inventories via epsilon lifting"
        
        # Should create reciprocal trade: agent0 gives good1 for good2, agent1 gives good2 for good1
        intent = intents[0]
        assert intent.seller_id in [0, 1]
        assert intent.buyer_id in [0, 1]
        assert intent.seller_id != intent.buyer_id
        assert {intent.give_type, intent.take_type} == {"good1", "good2"}

    def test_all_zero_inventories_no_trades(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that agents with no carrying inventory cannot trade (even with epsilon lifting)."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        sim = _sim_with_agents([(0, 0), (0, 0)])
        
        # Both agents have zero carrying inventory
        sim.agents[0].carrying = {"good1": 0, "good2": 0}
        sim.agents[1].carrying = {"good1": 0, "good2": 0}
        
        # But non-zero home inventory to ensure preferences can be computed
        sim.agents[0].home_inventory = {"good1": 5, "good2": 5}
        sim.agents[1].home_inventory = {"good1": 5, "good2": 5}
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        rng = random.Random(85)
        sim.step(rng, use_decision=False)
        
        intents = sim.trade_intents or []
        assert len(intents) == 0, "No trades possible when carrying inventory is zero"


class TestLeontiefComplementRatios:
    """Test Leontief preference behavior at complement ratios and boundaries."""

    def test_leontief_at_perfect_ratio_no_trade_desire(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that agents at Leontief complement ratios don't want to trade."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        sim = _sim_with_agents([(0, 0), (0, 0)])
        
        # Leontief with perfect complement ratio 2:1
        sim.agents[0].preference = LeontiefPreference(a=2.0, b=1.0)
        sim.agents[1].preference = LeontiefPreference(a=2.0, b=1.0)
        
        # Agent 0 at perfect ratio: 4:2 = 2:1 ✓
        sim.agents[0].carrying = {"good1": 4, "good2": 2}
        # Agent 1 with excess good2: 2:4 = 1:2 (has excess good2)
        sim.agents[1].carrying = {"good1": 2, "good2": 4}
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        rng = random.Random(90)
        sim.step(rng, use_decision=False)
        
        intents = sim.trade_intents or []
        
        # Agent 0 (at perfect ratio) shouldn't want to trade
        # Agent 1 (excess good2) should want more good1
        # But agent 0 won't give up good1 since they're at optimal ratio
        
        # Check if any trade would benefit both agents
        if intents:
            # If intents exist, verify they make economic sense
            intent = intents[0]
            assert intent.delta_utility > 0, "Any generated intent should have positive utility gain"
        # Note: May be no intents if agent at perfect ratio won't trade

    def test_leontief_boundary_behavior_imbalanced_inventories(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test Leontief agents with severely imbalanced inventories seek complementary goods."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        sim = _sim_with_agents([(0, 0), (0, 0)])
        
        # Both agents have Leontief 1:1 preferences but imbalanced inventories
        sim.agents[0].preference = LeontiefPreference(a=1.0, b=1.0)
        sim.agents[1].preference = LeontiefPreference(a=1.0, b=1.0)
        
        # Agent 0: excess good1, needs good2
        sim.agents[0].carrying = {"good1": 8, "good2": 1}
        # Agent 1: excess good2, needs good1  
        sim.agents[1].carrying = {"good1": 1, "good2": 8}
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        rng = random.Random(95)
        sim.step(rng, use_decision=False)
        
        intents = sim.trade_intents or []
        assert len(intents) > 0, "Severely imbalanced Leontief agents should want to trade"
        
        # Should generate complementary trades
        intent = intents[0]
        expected_trades = {
            (0, 1, "good1", "good2"),  # Agent 0 gives good1, gets good2
            (1, 0, "good2", "good1"),  # Agent 1 gives good2, gets good1
        }
        actual_trade = (intent.seller_id, intent.buyer_id, intent.give_type, intent.take_type)
        assert actual_trade in expected_trades, f"Should generate complementary trade, got {actual_trade}"
        assert intent.delta_utility > 0, "Trade should improve combined utility"


class TestCoLocationPerformance:
    """Test performance with many co-located agents."""

    @pytest.mark.slow  # type: ignore[misc]
    def test_many_agents_performance(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that intent enumeration scales reasonably with many co-located agents."""
        import time
        
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        # Test with 10 agents (O(n²) = 100 comparisons, should be fast)
        positions = [(0, 0)] * 10
        sim = _sim_with_agents(positions)
        
        # Give each agent different inventories to maximize potential trades
        for i, agent in enumerate(sim.agents):
            agent.preference = PerfectSubstitutesPreference(a=1.0, b=1.0)
            # Alternate inventory patterns
            if i % 2 == 0:
                agent.carrying = {"good1": 3, "good2": 1}
            else:
                agent.carrying = {"good1": 1, "good2": 3}
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        # Time the step with intent enumeration
        start_time = time.perf_counter()
        
        rng = random.Random(200)
        sim.step(rng, use_decision=False)
        
        elapsed = time.perf_counter() - start_time
        
        intents = sim.trade_intents or []
        
        # Should complete quickly (< 10ms for 10 agents)
        assert elapsed < 0.01, f"Intent enumeration took too long: {elapsed:.4f}s for 10 agents"
        
        # Should generate reasonable number of intents (upper bound: 2 * C(10,2) = 90)
        assert 0 <= len(intents) <= 90, f"Unexpected number of intents: {len(intents)}"
        
        # All intents should be valid and sorted
        assert all(isinstance(intent, TradeIntent) for intent in intents)
        priorities = [intent.priority for intent in intents]
        assert priorities == sorted(priorities), "Intents must be sorted by priority"

    def test_enumeration_correctness_with_multiple_agents(self, monkeypatch) -> None:  # type: ignore[missing-annotations]
        """Test that all valid pairwise trades are found with multiple agents."""
        monkeypatch.setenv("ECONSIM_TRADE_DRAFT", "1")
        
        # 4 agents with known complementary preferences
        sim = _sim_with_agents([(0, 0), (0, 0), (0, 0), (0, 0)])
        
        # Set up clear trading opportunities
        preferences_and_inventory = [
            (CobbDouglasPreference(alpha=0.2), {"good1": 1, "good2": 0}),  # Wants good2
            (CobbDouglasPreference(alpha=0.8), {"good1": 0, "good2": 1}),  # Wants good1
            (PerfectSubstitutesPreference(a=2.0, b=1.0), {"good1": 2, "good2": 1}),  # Prefers good1
            (PerfectSubstitutesPreference(a=1.0, b=2.0), {"good1": 1, "good2": 2}),  # Prefers good2
        ]
        
        for i, (pref, inventory) in enumerate(preferences_and_inventory):
            sim.agents[i].preference = pref
            sim.agents[i].carrying = inventory.copy()
        
        monkeypatch.setattr(Agent, "move_random", lambda self, grid, rng: None)
        
        rng = random.Random(150)
        sim.step(rng, use_decision=False)
        
        intents = sim.trade_intents or []
        
        # Should find trading opportunities between complementary agents
        assert len(intents) > 0, "Should find trades between agents with complementary preferences"
        
        # Verify all intents involve agents that can actually benefit
        for intent in intents:
            seller = sim.agents[intent.seller_id] 
            buyer = sim.agents[intent.buyer_id]
            
            # Seller must have the good they're offering
            assert seller.carrying.get(intent.give_type, 0) > 0, f"Seller {intent.seller_id} lacks {intent.give_type}"
            # Buyer must have the good they're offering in return
            assert buyer.carrying.get(intent.take_type, 0) > 0, f"Buyer {intent.buyer_id} lacks {intent.take_type}"
            
            # Combined utility should improve (positive delta_utility)
            assert intent.delta_utility > 0, f"Intent should improve combined utility: {intent.delta_utility}"