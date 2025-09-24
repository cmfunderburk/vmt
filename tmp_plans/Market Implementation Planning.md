// ...user input...
Let's start planning the market behavior.

At the end of this phase, we should have two additional simulation options to select in the GUI.

In both versions:
    - Instead of goods spawning on the grid, each agent's home starts with a random endowment of goods (we will need to decide upon a distribution rule)
    - The agents remove the goods from their home inventory (and place them in their personal/carry inveotry), and then continue with their behavior logic
    - Utility is determined for each agent by their total inventories (home + personal carry)

The first: Bilateral Exchange
    - Agents seek the nearest agent that they have not yet traded with (tiebreaks by agent id num in case of equidistance).
    - They then pathfind to adjacent squares.
    - When they are on adjacent squares, they engage in trade if there is a possibility of mutual gains from trade (we will have to decide upon the bargaining rule or exchange ratios). If they cannot mutually gain from trade, they move on in their search
    - After each trade, they repeat this process until everyone has attempted to trade with each other at least once.
    - Once an agent has traded with every other agent, return to their home and deposit their goods.
The second: Market Exchange
    - A "marketplace" centralized on the NxN grid (defaults to a 2x2 area, configurable)
    - Agents can buy from and sell to the marketplace, but not directly with each other.
    - Once an agent has retrieved their initial endowment from their home, they travel to the marketplace and begin a day of trading. The agent will remain at the marketplace and attempt to make additional net-utility trades with the marketplace each turn for at least 5 turns. After 5 turns, if the agent can no longer make net-benficial trades, the agent returns home.
    - Market prices are determined locally -- that is, supply and demand are determined only by agents currently in the marketplace and their current inventories plus whatever items have been sold to the marketplace and not yet purchased by other agents. Agents can only trade with the marketplace at market price ratios.
    - The marketplace is initially stocked with a small assortment of goods to ensure at least one initial trade can begin
    -
// ...user input...

--------------------------------
Planning Scaffold (Deterministic, Minimal Diff)
--------------------------------

1. Goals (Incremental)
   G1 Add two new selectable scenarios: bilateral_exchange, market_exchange.
   G2 Preserve core loop invariants (single QTimer, O(agents+resources) per step).
   G3 Maintain determinism hash stability (hash only changes after we append new serialized state fields intentionally).
   G4 Provide seed-dependent but unbiased initial endowments (home + carry merged for utility).
   G5 Introduce no per-step quadratic partner scans beyond controlled sets.

2. New Scenario Flags (Config)
   SimConfig additions (append-only): mode: Literal["baseline","bilateral_exchange","market_exchange"]; market_size: tuple[int,int]=(2,2).
   Activation: Start Menu adds two entries mapping to SimConfig.mode.
   Determinism: Use existing global seed; derive sub-seeds:
     endowment_seed = base_seed + 5001
     market_seed    = base_seed + 5003

3. Initial Endowment Rule (Phase A)
    Objective: Provide each agent with a deterministic, seed‑dependent initial ownership of goods using one of four selectable distribution patterns (GUI dropdown) that illustrate contrasting wealth/endowment structures. Immediately after assignment, each agent (while on its home square) transfers its entire home inventory into carrying (making it liquid) in a single deterministic step before any movement or trade logic. This allows comparative educational scenarios about inequality without introducing transport delays yet.

    GUI Selection (endowment_distribution):
        uniform | oligarchic | middle_class | hollowed_out_middle
        (default: uniform; appended field in SimConfig; persisted in snapshot later when we extend schema). Deterministic hash impact deferred until serialization field is appended—planning only here.

    Notation & Set‑Up:
        n            = number of agents (id-sorted ascending list defines rank order)
        E            = endowment_max_units (config; default 3, clamp to 1..16)
        base_seed    = existing simulation seed
        endowment_rng = RNG(seed = base_seed + 5001)  (ONLY used for tie-breaks when fractional remainders collide; distributions themselves are formulaic)
        We allocate per-good counts independently using identical pattern (Phase A simplification). Future: allow asymmetric good patterns.

    Approach (Deterministic Weighted Allocation):
        1. Define a weight vector w_i per agent based on chosen pattern (see below). Sum W = Σ w_i.
        2. Define total units per good T = n * E  (keeps average near previous upper bound; adjustable later via config endowment_total_units_per_good if needed).
        3. Raw share r_i = (w_i / W) * T.
        4. Integer allocation a_i = floor(r_i).
        5. Remainder R = T - Σ a_i. Distribute remaining R units one at a time to agents sorted by:
              (-fractional_part(r_i), agent_id)   (largest fractional first; tie-break by id) for determinism.
        6. Guarantee Minimum: After remainder distribution, if any a_i == 0, raise it to 1 and decrement from agents with largest a_j (j ≠ i) using same stable ordering; maintain total T.
        7. Assign (a_i, b_i) to home_inventory for goods A,B respectively.
        8. Immediate Withdrawal: At simulation step 0 (before agent decision loop), perform withdraw_all_from_home_to_carry(agent) for every agent (constant-time pass, deterministic id order). After this, home_inventory for each good becomes 0; carrying holds the allocated endowment. (We still conceptually treat ownership = home + carry for future features; current home is zero post-step 0.)

    Distribution Patterns (Weight Vector Definitions):
        1. uniform:
             w_i = 1 for all i.
             (Replicates previous “equal opportunity” baseline; inequality arises only from later trades.)
        2. oligarchic (top 10% own ~80% of goods):
             Let t = max(1, round(0.10 * n)). Define set Top = highest t agent ids.
             Assign preliminary weights:
                 w_i = 0.8 / t    if i ∈ Top
                 w_i = 0.2 / (n - t) otherwise
             (Equivalent to proportional weights; scale factor irrelevant—handled by normalization.)
        3. middle_class (central 60% own 90%; bottom 5% own 1%; top 5% own 9%):
             Let b = max(1, round(0.05 * n)), h = max(1, round(0.05 * n)). Middle indices are the remaining agents.
             Group weights (pre-normalization):
                 Bottom group total share = 0.01
                 Middle group total share = 0.90
                 Top group total share    = 0.09
             Per-agent weights = group_share / group_size.
        4. hollowed_out_middle (extremes dominate: bottom 20% ~45%, top 20% ~45%, middle 60% ~10%):
             Let g = max(1, round(0.20 * n)). Bottom = lowest g ids; Top = highest g ids; Middle = rest.
             Group total shares: 0.45 / 0.10 / 0.45 distributed as above.
             Per-agent weights computed as group_share / group_size.

        NOTE: If group partitions overlap due to tiny n (e.g., n < 10), we collapse overlapping boundaries by recomputing with unique indices then renormalize final weights to sum 1. This keeps determinism without special-case branching in core logic.

    Example (oligarchic, illustrative):
        n=10, E=3 → T = 30 units per good. t=1 (top agent). Raw shares: top gets 0.8*30=24, others collectively 6 (≈0.666 each). Integer phase: top 24, others 0, remainder distributed raising others toward 1 until total 30. Minimum guarantee ensures every non-top gets at least 1. Final: top 24, others sum 6 → exactly 80/20 split.

    Why Immediate Withdrawal (Instead of Leaving Stock at Home Initially):
        * Matches stated requirement: agents “transfer and then head off” — no early logistic delay noise.
        * Simplifies Phase A trade mechanics (all inventory liquid) while preserving future extensibility (we can later disable auto-withdrawal for transport lessons).
        * Keeps withdrawal API reusable (single call path) and deterministic.

    Invariants (refined / restated):
       I-01 Ownership Decomposition: total_owned_g = home_g + carrying_g (still true; home becomes 0 after step 0 in Phase A scenarios).
       I-02 Utility Domain (market modes): U(bundle) uses total_owned (effectively carrying post-step 0 here).
       I-03 Trade Feasibility: Only carrying units are tradable (all units tradable immediately after withdrawal).
       I-04 No Implicit Mutation: Utility evaluation never triggers allocation or withdrawal.
       I-05 Deterministic Endowment: (seed, n, E, distribution_pattern) uniquely determine allocation vector.
       I-06 Remainder Stability: Fractional tie resolution uses ordered (-fraction_part, agent_id) — seed only used if an extremely rare floating precision full tie occurs (guard path).

    Edge Cases / Guards:
       * E < 1 → force E=1.
       * n so small that group sizes collapse → fallback normalization after merging overlapping indices.
       * If after minimum guarantee adjustment total deviates from T (should not), perform final single-pass correction by trimming from largest allocations (id order) until total == T.
       * Leontief / zero-quantity preference corner cases unchanged (utility layer epsilon bootstrapping still applies).

    Alternatives (Deferred):
       ALT-A Stochastic per-agent draws around target shares (adds variance) — deferred to keep strict reproducibility for teaching inequality shapes.
       ALT-B Distinct distributions per good (e.g., capital vs labor good asymmetry) — postpone to avoid combinatorial scenario explosion.
       ALT-C Logistic delay (multi-step retrieval instead of instant) — future “transport frictions” module.

    Snapshot Impact (Phase A): No immediate schema change (home + carrying already serialized). When we later persist the chosen distribution pattern we will append a field (order-preserving) and update hash tests.

4. Utility Aggregation Adjustment
    Requirement: In market modes, utility reflects ownership (home + carry) while trades remain constrained by carrying only.

    Helper API (F-UTIL-AGG):
       Agent.total_inventory_counts() -> tuple[int,int]
          return (home_inventory['good1'] + carrying['good1'], home_inventory['good2'] + carrying['good2'])
          Pure function; no side-effects.

    Utility Call Pattern:
       baseline mode: existing calls unchanged (carry + home considered implicitly only after deposit events)
       market modes: wrap preference.utility over total_inventory_counts() result.
       Implementation Hook: introduce Simulation.flag_use_total_inventory (derived from mode) OR use mode membership check inline to avoid broad refactor.

    Determinism Safeguards:
       * Branch on mode only—no new RNG.
       * Avoid conditional caching unless deterministically invalidated by inventory mutation (Phase A likely skip caching for simplicity).

    Trading Constraint Reminder:
       * When evaluating potential trades we compute marginal utilities as ΔU of total ownership, but we validate feasibility using carrying counts.

    Tests (augment list in section 10):
       - test_total_utility_includes_home_inventory_market_mode (ownership aggregated)
       - test_utility_excludes_home_only_if_not_withdrawn_in_baseline (baseline unchanged)
       - test_trade_cannot_use_home_only_units (simulate carrying 0 but home>0: trade blocked)
       - test_endowment_determinism (seed repeatability)

    Future Extensions (Documented Hooks):
       * Partial withdrawals: agent.withdraw_from_home(good, qty)
       * Storage cost: apply penalty factor to home portion only in utility (feature flag + snapshot field append)
       * Credit / collateral: allow utility weighting to treat home differently via preference wrapper.

    Non-Goals (Phase A):
       * Distinguish temporal acquisition order
       * Apply transport delays between home and carry
       * Model perishability / depreciation

5. Bilateral Exchange Mechanics (Phase B)
   Data structures per agent:
     traded_with: bitset or boolean list length n (O(n) memory) – deterministic index by agent id.
     target_agent_id: optional int.
   Selection:
     - Candidate set = agents not self and not yet traded_with == False.
     - Choose nearest by Manhattan distance; tie-break by agent id (consistent).
   Movement:
     - Simple greedy step: move one cell in x direction toward target; if aligned, move in y. (Avoid pathfinding complexity.)
   Adjacency Check:
     - When adjacent (Manhattan distance 1), attempt trade.
   Trade Rule (Minimal):
     - Compute each agent's marginal utility per good (approx via ΔU of +1 unit).
     - If one has higher MU_A and the other higher MU_B, exchange 1 unit each (if both have at least 1 of the offered good) simultaneously if both net ΔU > 0.
     - Repeat next frame if still beneficial; else mark traded_with[target]=True and pick next.
   Completion:
     - When traded_with all True, set mode "return_home" → greedy path back; upon arrival deposit carry into home (or simply flag complete).

6. Market Exchange Mechanics (Phase C)
   Marketplace State:
     - Coordinates rectangle centered (grid_w//2, grid_h//2) of size market_size.
     - marketplace_inventory: dict[ResourceType,int].
   Price Computation (Deterministic):
     - Once per step while agents present: price_ratio_A_to_B = (aggregate_desire_for_A + 1)/(aggregate_desire_for_B + 1).
       aggregate_desire_for_X ≈ sum over agents of marginal utility of +1 unit X (based on total inventory).
     - Represent prices as rational pair (num,den) reduced or store float with fixed rounding (e.g., 4 decimals) to avoid hash drift.
   Agent Behavior:
     - Travel to nearest edge cell of marketplace (greedy).
     - Trading phase: for min 5 steps attempt one unit trade per step:
         If MU_A / MU_B > price_ratio_A_to_B → sell A buy B if inventory allows and market has B or accepts A.
         Else if MU_B / MU_A > 1/price_ratio_A_to_B → mirror.
     - Market accepts goods (inventory increases) and dispenses goods if present; no credit.
     - Exit if after min 5 steps no beneficial unit trade found for K consecutive steps (K=2).
   Determinism Notes:
     - Order of agent trade resolution: iterate agents in id order; each may execute at most one unit trade per step.

7. Snapshot / Serialization Additions
   Append-only fields:
     - mode
     - For bilateral: list of traded_with bitmasks (pack into ints) OR reconstructible from steps? (Choose explicit for simplicity.)
     - For market: marketplace_inventory, price numerator/denominator, agent phase counters (trading_step_count, idle_consec).
   Update tests: new snapshot parity for new modes.

8. Performance Guardrails
   - Greedy movement O(1).
   - MU computations: reuse preference utility function; cache last per-agent inventory to avoid duplicate ΔU in same frame (optional micro-opt later).
   - Marketplace aggregate desire: single pass O(agents).
   - No nested agent-agent scans beyond per-agent candidate selection; optimizing candidate selection:
       Precompute list of remaining partners; nearest search is O(n). Acceptable for small n; if n grows, spatial index (future flag).

9. Determinism Risks & Mitigations
   R1 Unordered dict iteration for marketplace_inventory → always iterate sorted(resource_type).
   R2 Floating arithmetic drift → store price as (int_numer,int_denom) from rational approximation with fixed denominator (e.g., scale*).
   R3 Set-based partner selection → use list comprehension preserving original agent ordering.

10. Testing Plan (New Tests)
   - test_bilateral_trade_progress: all traded_with become True under conditions.
   - test_bilateral_trade_determinism_hash: stable across two runs with same seed.
   - test_market_price_determinism: identical (num,den) sequence for same seed.
   - test_market_agent_exit_condition: agent leaves after insufficient beneficial trades post threshold.
   - test_initial_endowment_distribution_repeatable: same endowments for repeated seeds.
   - test_no_respawn_in_market_modes: respawn scheduler disabled / skipped when mode != baseline.

11. GUI Additions
   - Start Menu: two new scenario buttons mapping to config.mode.
   - Overlay: display mode label + price ratio when in market mode (cost <2% budget).
   - Optional future: show partner progress or market inventory (later).

12. Incremental Implementation Order
   Phase A: Config mode + endowments + utility aggregation (flagged).
   Phase B: Bilateral structures, movement, simple trade rule.
   Phase C: Marketplace state, price computation, agent trading loop.
   Phase D: GUI scenario buttons + overlay info.
   Phase E: Snapshot + tests + perf/hash validation.

13. Open Decisions (Need Confirmation)
   D1 Endowment distribution: Uniform [1..E] vs fixed vector? (Proposed: Uniform.)
   D2 Utility aggregation: Always aggregate or only in market modes? (Proposed: only in new modes.)
   D3 Price formula sophistication (simple MU ratio vs supply-demand inventory weighting). (Proposed: simple MU ratio first.)
   D4 Trade unit size >1? (Proposed: 1 per step for determinism & clarity.)
   D5 Partner pathfinding beyond greedy axis step? (Proposed: greedy only.)

14. Minimal Data Structure Additions
   - Agent.extra_state dict (or dedicated fields) with:
       bilateral_traded_with_bitmask (int)
       trading_phase_counter (int)
       market_idle_consec (int)
   - Simulation.market (None or Marketplace dataclass)
   - Simulation.mode (string enum)

15. Constraints to Respect (Mirror Core Invariants)
   - Single QTimer only.
   - No additional per-frame RNG apart from seeded simulation RNG.
   - Deterministic iteration order for all multi-entity loops.
   - Append-only snapshot schema.

16. Next Actions (You choose which to confirm)
   Confirm D1–D5.
   If accepted, I will draft skeleton diffs (no logic yet) creating:
     simulation/market.py (dataclass + placeholder)
     simulation/trade_rules.py (bilateral + market stubs)
     Extend SimConfig + scenario registration
     GUI Start Menu entries
     Tests placeholders.

--------------------------------
Awaiting confirmations for D1–D5 or modifications.