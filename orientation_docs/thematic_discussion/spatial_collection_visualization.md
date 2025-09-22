# Spatial Collection Visualization Specification

## Core Concept

Agents with different preference types demonstrate spatial economic choice through a **collection-return-consume** cycle that makes abstract utility maximization concrete and visually compelling.

## Visualization Mechanics

### **Grid Setup**
```
Grid Size: N x N where N ≥ 3 × num_agents (default: N = 15 for 1-5 agents)
Good Type A: Randomly placed items (e.g., "Coffee" - red dots)  
Good Type B: Randomly placed items (e.g., "Tea" - blue dots)
Agent Homes: Starting positions marked distinctly (e.g., house icons)
Movement Grid: Discrete movement, agents move one cell per time step
```

### **Agent Behavior Cycle**

#### **Phase 1: Route Planning**
```python
def plan_collection_route(agent, grid_state):
    available_goods = scan_grid_for_goods(grid_state)
    
    for good in available_goods:
        utility_gain = agent.preference.marginal_utility(good.type)
        movement_cost = calculate_distance(agent.position, good.position) 
        efficiency_ratio = utility_gain / movement_cost
        
    optimal_route = agent.preference.optimize_collection_sequence(
        goods=available_goods,
        energy_budget=agent.energy,
        home_position=agent.home
    )
    
    return optimal_route
```

#### **Phase 2: Collection Execution**
```python
def execute_collection(agent, planned_route):
    for waypoint in planned_route:
        move_toward(agent, waypoint.position)
        if reached(waypoint):
            if waypoint.has_good():
                collect_good(agent, waypoint.good)
                update_utility(agent)
                agent.energy -= movement_cost
```

#### **Phase 3: Return and Consumption**
```python
def return_and_consume(agent):
    move_toward(agent, agent.home)
    if at_home(agent):
        final_utility = agent.preference.utility(agent.collected_A, agent.collected_B)
        display_utility_achievement(agent, final_utility)
        reset_for_next_round(agent)
```

## Preference Type Differentiation

### **Cobb-Douglas Agent (α = 0.5)**
```
Route Planning Strategy:
- Seeks balanced collection: roughly equal A and B goods
- Willing to travel farther for variety
- Plans routes to maintain goods ratio near 1:1

Expected Visual Behavior:
- Zigzag movement patterns collecting both types
- May backtrack to balance collection
- Efficient but not single-minded routes

Educational Insight: "This person values variety and balance"
```

### **Perfect Substitutes Agent (U = A + 2B)**  
```
Route Planning Strategy:
- Focuses entirely on higher-value good type (B in this case)
- Only collects A if B is unavailable or much farther
- Optimizes for single good type efficiency

Expected Visual Behavior:  
- Beeline movement toward preferred good type
- Ignores other goods even if closer
- Most efficient routes within preferred category

Educational Insight: "This person sees goods as interchangeable with clear preferences"
```

### **Leontief Agent (U = min(A, B))**
```
Route Planning Strategy:
- Must collect goods in equal proportions  
- Will backtrack to maintain 1:1 ratio
- Routes prioritize balanced collection over efficiency

Expected Visual Behavior:
- Alternating collection pattern (A, then B, then A, etc.)
- May pass by goods to maintain proper proportions
- Least efficient routes but most balanced outcomes  

Educational Insight: "This person needs goods together in fixed combinations"
```

## Progressive Complexity Scenarios

### **Tutorial Scenario 1: Single Agent, Clear Preferences**
```
Grid: 10x10
Agents: 1 (user selects preference type)  
Goods: 4 of type A, 4 of type B, well-separated
Energy: Unlimited
Goal: Students observe how different preferences create different movement patterns
```

### **Tutorial Scenario 2: Budget Constraints**
```
Grid: 15x15  
Agents: 1
Goods: 6 of type A, 6 of type B, scattered
Energy: Limited (can only reach ~8 goods total)
Goal: Students see trade-offs between accessibility and preference
```

### **Tutorial Scenario 3: Multi-Agent Competition**
```
Grid: 15x15
Agents: 3 (one of each preference type)
Goods: 8 of type A, 8 of type B
Energy: Limited  
Goal: Students observe how different strategies perform under competition
```

### **Tutorial Scenario 4: Market Dynamics**
```
Grid: 20x20
Agents: 5+ with mixed preference types
Goods: Limited quantities, scarcity
Energy: Limited
Goal: Students see emergent market behavior and specialization
```

## Technical Implementation Considerations

### **Path Planning Algorithm**
```python
class PreferenceAwarePathPlanner:
    def __init__(self, preference_type):
        self.preference = preference_type
        
    def plan_optimal_route(self, current_pos, available_goods, energy_budget):
        # Use A* pathfinding with preference-weighted heuristic
        # Heuristic: utility_gain / movement_cost for each good
        # Constraint: total energy budget
        # Optimization: maximize total utility collected
        
        return optimized_collection_sequence
```

### **Performance Optimization**
```python
# Spatial indexing for good lookup
goods_grid = SpatialHashGrid(cell_size=3)  

# Precompute distance matrices for pathfinding
distance_cache = precompute_all_distances(grid_size)

# Update only changed agents per frame
dirty_agent_tracking = set()
```

### **Visual Design Elements**
```python
# Agent visualization
agent_sprites = {
    'cobb_douglas': green_circle_with_balance_icon,
    'perfect_substitutes': blue_triangle_with_arrow_icon, 
    'leontief': red_square_with_proportion_icon
}

# Movement visualization  
movement_trails = colored_dotted_lines_showing_recent_path
planned_routes = translucent_arrows_showing_intended_path

# Good visualization
good_type_A = coffee_cup_icon_or_red_dot
good_type_B = tea_cup_icon_or_blue_dot
collected_goods = smaller_icons_following_agent

# Home base visualization
home_base = house_icon_with_inventory_display
```

## Educational Assessment Integration

### **Learning Objective Validation**
```
After each scenario, students answer:
1. "Which agent type collected the most goods?" (efficiency question)
2. "Which agent type got the highest utility?" (preference satisfaction question)  
3. "How would behavior change if good B became much scarcer?" (prediction question)
4. "Which agent type best represents your own shopping behavior?" (personal connection question)
```

### **Misconception Detection**
```
Common student errors to detect and address:
- "The efficient agent is always best" → Show utility vs efficiency trade-offs
- "Preferences are just opinions" → Show systematic, predictable behavior differences  
- "Economics assumes everyone is the same" → Demonstrate multiple preference types
- "Utility is unrealistic" → Connect to observable spatial behavior
```

### **Progressive Revelation Strategy**
```
Stage 1: Show movement only, ask students to guess agent differences
Stage 2: Reveal preference types, connect to movement patterns
Stage 3: Allow parameter adjustment, observe behavior changes
Stage 4: Multiple agents, observe interactions and competition
Stage 5: Market scenarios, connect to price formation and equilibrium
```

## Integration with Validation Gates

### **Gate 2: Economic Theory Implementation**
```
Validation Requirements for Collection Visualization:
- [ ] All three preference types produce mathematically correct collection sequences
- [ ] Route optimization matches theoretical utility maximization under spatial constraints
- [ ] Edge cases handled (unreachable goods, insufficient energy, empty grid)
- [ ] Performance maintains real-time response with pathfinding calculations
```

### **Gate 3: Spatial Integration**  
```
Validation Requirements for Spatial Behavior:
- [ ] Preference differences create visually distinguishable movement patterns
- [ ] Students can identify agent types from behavior alone (>80% accuracy)
- [ ] Multiple agents perform simultaneously without conflicts or performance degradation
- [ ] Real-time parameter changes update agent behavior within 100ms
```

### **Gate 4: Educational Interface**
```
Validation Requirements for Educational Effectiveness:
- [ ] Tutorial progression successfully teaches preference concepts
- [ ] Students demonstrate understanding through assessment questions
- [ ] Interface intuitive enough for economics students without programming background
- [ ] Comparative scenarios effectively highlight differences between preference types
```

## This Visualization Addresses Core Planning Goals

### **Spatial-Economic Integration**
✅ Makes abstract utility maximization spatially concrete
✅ Demonstrates how preferences drive observable behavior
✅ Creates natural laboratory for economic experimentation

### **Educational Mission**  
✅ Addresses "people don't behave like that" criticism directly
✅ Shows economic theory as flexible framework, not rigid assumption
✅ Provides concrete, visual foundation for abstract concepts

### **Technical Feasibility**
✅ Built on proven pathfinding and spatial simulation techniques
✅ Scales from simple single-agent demos to complex multi-agent markets
✅ Performance requirements achievable with standard optimization techniques

### **Progressive Complexity**
✅ Supports tutorial progression from simple to sophisticated
✅ Enables both classroom demonstration and individual exploration
✅ Provides foundation for advanced market and equilibrium concepts

This collection-based visualization transforms the abstract question "how do preferences affect choice?" into the concrete, observable question "watch how these different agent types move around the grid - can you spot the differences?"