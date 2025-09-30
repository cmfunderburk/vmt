"""Trading handler: trading intent enumeration and optional execution.

Extracts the trading portion of the former monolithic Simulation.step logic.
Maintains deterministic ordering and single-intent execution semantics.

Determinism invariants preserved:
 - Co-location map built in agent list order → dict preserves insertion order
 - Intents enumeration order matches legacy logic
 - ≤1 trade executed per step (best intent chosen inside execute_single_intent)
 - Hash-neutral parity mode restores inventories (ECONSIM_TRADE_HASH_NEUTRAL=1)

Cross-handler data:
 - Movement/Collection populate simulation._transient_foraged_ids (optional set)
   used for gating trading after foraging ("forage first then trade").

Metrics collected:
 - intents_count, executed_flag, funnel stats (drafted/pruned counts, max ΔU)
 - executed_trade metadata when present (seller_id, buyer_id, give_type, take_type)
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple, Set

from ..result import StepResult
from ..context import StepContext
from . import BaseStepHandler
from ...agent import Agent
from ...trade import (
	enumerate_intents_for_cell,
	TradeEnumerationStats,
	TradeIntent,
	execute_single_intent,
)


class TradingHandler(BaseStepHandler):
	def __init__(self) -> None:
		super().__init__("trading")

	def _execute_impl(self, context: StepContext) -> StepResult:
		sim = context.simulation
		features = context.feature_flags

		if not features.is_trading_enabled():
			# Clear any lingering intents & pairings if trading disabled
			sim.trade_intents = None
			self._clear_stale_pairings(sim)
			return StepResult.with_metrics(self.handler_name, intents_count=0, executed=0)

		draft_enabled = features.trade_draft_enabled
		exec_enabled = features.trade_execution_enabled

		# Build co-location index (O(n))
		cell_map: Dict[Tuple[int, int], List[Agent]] = {}
		for a in sim.agents:
			cell_map.setdefault((a.x, a.y), []).append(a)

		intents: List[TradeIntent] = []
		funnel_stats = TradeEnumerationStats()

		# Foraged gating: if both foraging & trading active AND some agents foraged, exclude them
		foraged_ids: Set[int] = getattr(sim, "_transient_foraged_ids", set()) or set()
		use_foraged_filter = features.forage_enabled and len(foraged_ids) > 0 and draft_enabled

		for coloc_agents in cell_map.values():
			if len(coloc_agents) <= 1:
				continue
			if use_foraged_filter:
				filtered = [ag for ag in coloc_agents if ag.id not in foraged_ids]
				if len(filtered) > 1:
					intents.extend(enumerate_intents_for_cell(filtered, funnel_stats))
			else:
				intents.extend(enumerate_intents_for_cell(coloc_agents, funnel_stats))

		sim.trade_intents = intents  # store for GUI / observability

		executed: TradeIntent | None = None
		parity_snapshot = None
		hash_neutral = os.environ.get("ECONSIM_TRADE_HASH_NEUTRAL") == "1"

		if exec_enabled and intents:
			if hash_neutral:
				parity_snapshot = [(a.id, dict(a.carrying)) for a in sim.agents]

			agents_by_id: Dict[int, Agent] = {a.id: a for a in sim.agents}
			executed = execute_single_intent(intents, agents_by_id, context.step_number)

			# Emit trade execution event for observer system
			if executed is not None:
				self._notify_trade_execution_event(context, executed)

			# Highlight (for renderer) – 12 step lifetime consistent with legacy
			if executed is not None:
				seller_agent = agents_by_id.get(executed.seller_id)
				if seller_agent is not None:
					sim._last_trade_highlight = (
						int(getattr(seller_agent, "x", 0)),
						int(getattr(seller_agent, "y", 0)),
						sim._steps + 12,
					)

		# Metrics collector integration
		if sim.metrics_collector is not None:
			try:
				mc = sim.metrics_collector  # type: ignore[attr-defined]
				mc.trade_intents_generated += len(intents)  # type: ignore[attr-defined]
				if exec_enabled:
					if executed is not None:
						seller_delta_u = getattr(executed, "delta_utility", 0.0)
						buyer_delta_u = seller_delta_u  # approximation placeholder (legacy parity)
						mc.register_executed_trade(  # type: ignore[attr-defined]
							step=sim._steps,
							agent1_id=executed.seller_id,
							agent2_id=executed.buyer_id,
							agent1_give=executed.give_type,
							agent1_take=executed.take_type,
							agent1_delta_u=seller_delta_u,
							agent2_delta_u=buyer_delta_u,
							realized_utility_gain=seller_delta_u,
							hash_neutral=hash_neutral,
						)
					else:
						mc.no_trade_ticks += 1  # type: ignore[attr-defined]
			except Exception:  # pragma: no cover - defensive
				pass

		# Parity debug snapshots (optional)
		if executed is not None and os.environ.get("ECONSIM_DEBUG_TRADE_PARITY") == "1":  # pragma: no cover
			try:
				import json as _json
				snap = [
					{
						"id": a.id,
						"x": a.x,
						"y": a.y,
						"c": dict(a.carrying),
						"h": dict(a.home_inventory),
					}
					for a in sorted(sim.agents, key=lambda ag: ag.id)
				]
				print("[PARITY_EXEC_SNAP]" + _json.dumps(snap))
			except Exception:
				pass

		# Hash-neutral restoration (after metrics & debug)
		if parity_snapshot is not None:
			id_map = {a.id: a for a in sim.agents}
			for aid, carry in parity_snapshot:
				agent = id_map.get(aid)
				if agent is not None:
					agent.carrying.clear()
					agent.carrying.update(carry)

		# Pairing cleanup for stale sessions
		self._cleanup_pairings(sim, executed)

		# Funnel instrumentation (GUI debug logger, non-fatal)
		if funnel_stats.drafted > 0:
			try:  # pragma: no cover - logging side-effect only
				from ...gui.debug_logger import get_gui_logger  # type: ignore
				logger = get_gui_logger()
				executed_count = 1 if executed is not None else 0
				builder_result = logger.build_trade_intent_funnel(
					drafted=funnel_stats.drafted,
					pruned_micro=funnel_stats.pruned_micro,
					pruned_nonpositive=funnel_stats.pruned_nonpositive,
					executed=executed_count,
					max_delta_u=funnel_stats.max_delta_u,
				)
				logger.emit_built_event(context.step_number, builder_result)
			except Exception:
				pass

		return StepResult.with_metrics(
			self.handler_name,
			intents_count=len(intents),
			executed=1 if executed is not None else 0,
			drafted=funnel_stats.drafted,
			pruned_micro=funnel_stats.pruned_micro,
			pruned_nonpositive=funnel_stats.pruned_nonpositive,
			max_delta_u=funnel_stats.max_delta_u,
		)

	# --- Internal helpers -------------------------------------------------
	def _clear_stale_pairings(self, sim) -> None:
		for a in sim.agents:
			if getattr(a, 'trade_partner_id', None) is not None:
				try:
					a.clear_trade_partner()
				except Exception:
					pass

	def _notify_trade_execution_event(self, context: StepContext, executed_intent) -> None:
		"""Emit trade execution event to observer system."""
		from ....observability.events import TradeExecutionEvent
		
		if context.observer_registry.has_observers():
			# Calculate utility changes (approximation for now)
			seller_delta_u = getattr(executed_intent, "delta_utility", 0.0)
			buyer_delta_u = seller_delta_u  # Legacy parity approximation
			
			# Get trade location if available
			trade_x, trade_y = -1, -1
			try:
				# Try to get seller agent position as trade location
				sim = context.simulation
				agents_by_id = {a.id: a for a in sim.agents}
				seller_agent = agents_by_id.get(executed_intent.seller_id)
				if seller_agent:
					trade_x, trade_y = seller_agent.x, seller_agent.y
			except Exception:
				pass  # Keep default -1, -1
			
			event = TradeExecutionEvent.create(
				step=context.step_number,
				seller_id=executed_intent.seller_id,
				buyer_id=executed_intent.buyer_id,
				give_type=executed_intent.give_type,
				take_type=executed_intent.take_type,
				delta_u_seller=seller_delta_u,
				delta_u_buyer=buyer_delta_u,
				trade_location_x=trade_x,
				trade_location_y=trade_y
			)
			context.observer_registry.notify(event)

	def _cleanup_pairings(self, sim, executed: TradeIntent | None) -> None:
		try:
			active_pairs: Set[Tuple[int,int]] = set()
			for it in sim.trade_intents or []:
				pair = (min(it.seller_id, it.buyer_id), max(it.seller_id, it.buyer_id))
				active_pairs.add(pair)
			executed_pair: Tuple[int,int] | None = None
			if executed is not None:
				executed_pair = (min(executed.seller_id, executed.buyer_id), max(executed.seller_id, executed.buyer_id))
			seen: Set[int] = set()
			for agent in sorted(sim.agents, key=lambda a: a.id):
				pid = getattr(agent, 'trade_partner_id', None)
				if pid is None or agent.id in seen:
					continue
				partner = self._find_agent_by_id(sim, pid)
				if partner is None:
					agent.clear_trade_partner(); continue
				pair_key = (min(agent.id, pid), max(agent.id, pid))
				if executed_pair is not None and pair_key == executed_pair:
					agent.end_trading_session(partner)
				else:
					if (agent.x, agent.y) == (partner.x, partner.y) and pair_key not in active_pairs:
						agent.end_trading_session(partner)
				seen.add(agent.id); seen.add(pid)
		except Exception:  # pragma: no cover
			pass

	def _find_agent_by_id(self, sim, aid: int) -> Agent | None:
		for a in sim.agents:
			if a.id == aid:
				return a
		return None

