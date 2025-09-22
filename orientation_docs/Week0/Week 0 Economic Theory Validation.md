# Week 0 Economic Theory Validation

## Purpose
Define explicit criteria for validating that our three preference implementations are theoretically sound and educationally effective.

## Three Preference Types - Validation Framework

### 1. Cobb-Douglas Preferences: U(x,y) = x^α * y^(1-α)

**Mathematical Properties to Validate:**
- [ ] **Convex indifference curves** - No kinks or flat segments
- [ ] **Diminishing marginal utility** - ∂²U/∂x² < 0, ∂²U/∂y² < 0
- [ ] **Positive marginal utilities** - ∂U/∂x > 0, ∂U/∂y > 0
- [ ] **Homothetic preferences** - Income expansion paths are straight lines through origin

**Optimization Validation:**
- [ ] **Tangency condition**: MUx/MUy = Px/Py at optimum
- [ ] **Budget constraint satisfied**: Px*x + Py*y = I
- [ ] **Interior solutions** for α ∈ (0,1), Px,Py > 0, I > 0

**Expected Agent Behavior (Week 0 Validation):**
```python
# Test case: α = 0.5, Px = 2, Py = 1, I = 10
expected_x = 2.5  # I * α / Px = 10 * 0.5 / 2
expected_y = 5.0  # I * (1-α) / Py = 10 * 0.5 / 1
expected_utility = 3.54  # (2.5)^0.5 * (5.0)^0.5

# Validation code
def validate_cobb_douglas(alpha, px, py, income):
    x_opt = income * alpha / px
    y_opt = income * (1 - alpha) / py
    utility = (x_opt ** alpha) * (y_opt ** (1 - alpha))
    return x_opt, y_opt, utility
```

### 2. Perfect Substitutes: U(x,y) = ax + by

**Mathematical Properties to Validate:**
- [ ] **Linear indifference curves** - Constant slope = -a/b
- [ ] **Constant marginal utilities** - ∂U/∂x = a, ∂U/∂y = b
- [ ] **No diminishing marginal utility** - Second derivatives = 0

**Optimization Validation:**
- [ ] **Corner solutions when a/b ≠ Px/Py**
- [ ] **Multiple optima when a/b = Px/Py** (entire budget line)
- [ ] **Budget constraint binding**: Px*x + Py*y = I

**Expected Agent Behavior (Week 0 Validation):**
```python
# Test case 1: a=2, b=1, Px=1, Py=2, I=10
# Since a/b = 2 > Px/Py = 0.5, choose corner: all X
expected_corner_1 = (10, 0)  # x = I/Px = 10, y = 0

# Test case 2: a=1, b=2, Px=2, Py=1, I=10  
# Since a/b = 0.5 < Px/Py = 2, choose corner: all Y
expected_corner_2 = (0, 10)  # x = 0, y = I/Py = 10

# Validation code
def validate_perfect_substitutes(a, b, px, py, income):
    mrs = a / b
    price_ratio = px / py
    
    if mrs > price_ratio:
        return (income / px, 0)  # All X
    elif mrs < price_ratio:
        return (0, income / py)  # All Y
    else:
        return "indifferent"  # Any point on budget line
```

### 3. Leontief (Perfect Complements): U(x,y) = min(x/a, y/b)

**Mathematical Properties to Validate:**
- [ ] **L-shaped indifference curves** - Right angles at kink points
- [ ] **Undefined marginal utilities** at kink (need special handling)
- [ ] **Fixed proportion consumption** at optimum: x/a = y/b

**Optimization Validation:**
- [ ] **Kink point optimum**: x* = a*k, y* = b*k for some k > 0
- [ ] **Budget constraint binding**: Px*(a*k) + Py*(b*k) = I
- [ ] **Solve for k**: k = I / (Px*a + Py*b)

**Expected Agent Behavior (Week 0 Validation):**
```python
# Test case: a=2, b=1, Px=3, Py=2, I=15
# Optimal k = I / (Px*a + Py*b) = 15 / (3*2 + 2*1) = 15/8 = 1.875
expected_x = 3.75  # a * k = 2 * 1.875
expected_y = 1.875  # b * k = 1 * 1.875
expected_utility = 1.875  # min(3.75/2, 1.875/1) = min(1.875, 1.875)

# Validation code
def validate_leontief(a, b, px, py, income):
    k = income / (px * a + py * b)
    x_opt = a * k
    y_opt = b * k
    utility = min(x_opt / a, y_opt / b)  # Should equal k
    return x_opt, y_opt, utility
```

## Comparative Behavior Validation

### Income Effects (Week 0 Test)
**All three types should show:**
- [ ] **Positive income effects** - More income → more of both goods (normal goods case)
- [ ] **Proportional increases** for Cobb-Douglas and Leontief
- [ ] **Corner solution persistence** for Perfect Substitutes

### Price Effects (Week 0 Test)
**Substitution patterns should differ:**
- [ ] **Cobb-Douglas**: Smooth substitution, both goods remain positive
- [ ] **Perfect Substitutes**: Complete switching at price ratio threshold
- [ ] **Leontief**: No substitution, maintain fixed proportions

### Cross-Price Elasticity Patterns
```python
def validate_cross_price_effects():
    """Test how each preference type responds to relative price changes"""
    
    # Base case
    base_params = {'income': 20, 'px': 2, 'py': 2}
    
    # Price increase scenario: Px doubles
    shock_params = {'income': 20, 'px': 4, 'py': 2}
    
    # Expected responses:
    # CD: Both goods decrease, smooth adjustment
    # PS: Possible complete switch to Y
    # Leontief: Proportional decrease in both
```

## Educational Validation Criteria

### Visual Distinction (Week 0 Requirement)
- [ ] **Different agent movement patterns** observable in spatial grid
- [ ] **Distinct response to parameter changes** in real-time
- [ ] **Clear preference type identification** from behavior alone

### Progressive Complexity (Educational Effectiveness)
- [ ] **Start with Cobb-Douglas** (most intuitive smooth curves)
- [ ] **Add Perfect Substitutes** (introduce corner solutions)  
- [ ] **Finish with Leontief** (demonstrate extreme complementarity)

### Common Student Misconceptions to Address
- [ ] **"People don't act like math"** → Show behavioral variety across types
- [ ] **"Economics assumes perfect rationality"** → Demonstrate framework flexibility
- [ ] **"Utility isn't measurable"** → Focus on ordinal rankings and choices

## Week 0 Implementation Checkpoints

### Day 1-2: Basic Preference Classes
```python
class PreferenceBase:
    def utility(self, x, y):
        raise NotImplementedError
    
    def optimal_choice(self, px, py, income):
        raise NotImplementedError
    
    def marginal_utility_x(self, x, y):
        raise NotImplementedError

# Implement all three, validate against analytical solutions
```

### Day 3-4: Parameter Sensitivity
- [ ] Test utility calculations across parameter ranges
- [ ] Validate optimization routines with known solutions
- [ ] Check boundary cases (zero prices, zero income)

### Day 5-6: Spatial Integration
- [ ] Agents can move to improve utility
- [ ] Movement respects budget constraints
- [ ] Different preference types show distinct spatial patterns

### Day 7: Educational Interface
- [ ] Real-time parameter adjustment
- [ ] Visual feedback for preference type switching
- [ ] Clear labeling of current preference assumptions

## Spatial Collection Behavior Validation

### **Collection-Based Validation Framework**
Transform abstract utility maximization into observable spatial behavior through collection-return-consume cycles.

#### **Spatial Scenario Setup**
```python
# Test environment for preference validation
def create_collection_scenario():
    grid_size = 15  # Large enough for meaningful choice
    good_type_A_positions = [(2,3), (8,7), (12,4), (5,11)]  # Coffee locations  
    good_type_B_positions = [(4,2), (9,9), (13,8), (6,12)]  # Tea locations
    agent_home = (7, 7)  # Center starting position
    energy_budget = 20   # Limited movement energy
```

#### **Cobb-Douglas Spatial Validation**
```python
def test_cobb_douglas_collection_behavior():
    agent = CobbDouglasAgent(alpha=0.5, home=(7,7), energy=20)
    goods_scenario = create_collection_scenario()
    
    planned_route = agent.plan_collection_route(goods_scenario)
    
    # Validation criteria:
    assert len([g for g in planned_route if g.type == 'A']) >= 2  # Collects both types
    assert len([g for g in planned_route if g.type == 'B']) >= 2  # Balanced collection
    assert abs(collected_A_count - collected_B_count) <= 1       # Roughly equal
    
    # Route efficiency validation:
    total_utility = agent.preference.utility(collected_A, collected_B)
    max_possible = calculate_theoretical_maximum(goods_scenario, agent.preference)
    assert total_utility >= 0.8 * max_possible  # At least 80% efficient
```

#### **Perfect Substitutes Spatial Validation**  
```python
def test_perfect_substitutes_collection_behavior():
    agent = PerfectSubstitutesAgent(a=1, b=2, home=(7,7), energy=20)  # Prefers B
    goods_scenario = create_collection_scenario()
    
    planned_route = agent.plan_collection_route(goods_scenario) 
    collected_goods = execute_collection_simulation(agent, planned_route)
    
    # Validation criteria:
    collected_B = [g for g in collected_goods if g.type == 'B']
    collected_A = [g for g in collected_goods if g.type == 'A']
    
    assert len(collected_B) >= len(collected_A)  # Focuses on preferred type
    
    # Only collects A if B is unavailable or much less efficient
    if len(collected_A) > 0:
        for a_good in collected_A:
            nearest_b = find_nearest_good_type_B(a_good.position, goods_scenario)
            assert distance(agent.home, a_good) < distance(agent.home, nearest_b)
```

#### **Leontief Spatial Validation**
```python  
def test_leontief_collection_behavior():
    agent = LeontiefAgent(a=1, b=1, home=(7,7), energy=20)  # Equal proportions
    goods_scenario = create_collection_scenario()
    
    planned_route = agent.plan_collection_route(goods_scenario)
    collected_goods = execute_collection_simulation(agent, planned_route)
    
    # Validation criteria:
    collected_A = [g for g in collected_goods if g.type == 'A']  
    collected_B = [g for g in collected_goods if g.type == 'B']
    
    assert abs(len(collected_A) - len(collected_B)) <= 1  # Equal proportions maintained
    
    # Agent should pass by goods to maintain proportions if needed
    route_analysis = analyze_collection_sequence(planned_route)
    assert route_analysis.maintains_proportions == True
```

### **Visual Pattern Validation**
```python
def test_preference_visual_distinction():
    """Validate that different preferences create visually distinguishable movement patterns"""
    
    scenarios = generate_multiple_collection_scenarios(n=10)
    
    for scenario in scenarios:
        cd_agent = CobbDouglasAgent(alpha=0.5)
        ps_agent = PerfectSubstitutesAgent(a=1, b=2) 
        lf_agent = LeontiefAgent(a=1, b=1)
        
        cd_route = cd_agent.plan_collection_route(scenario)
        ps_route = ps_agent.plan_collection_route(scenario)  
        lf_route = lf_agent.plan_collection_route(scenario)
        
        # Routes should be distinguishable
        assert routes_are_different(cd_route, ps_route, threshold=0.3)
        assert routes_are_different(ps_route, lf_route, threshold=0.3) 
        assert routes_are_different(cd_route, lf_route, threshold=0.3)
        
        # Pattern characteristics should match theory
        assert cd_route.has_balanced_collection()
        assert ps_route.has_focused_collection()  
        assert lf_route.has_proportional_collection()
```

## Validation Test Suite Structure
```
tests/economic_validation/
├── test_cobb_douglas.py           # Analytical solution validation
├── test_perfect_substitutes.py    # Corner solution validation  
├── test_leontief.py               # Fixed proportion validation
├── test_spatial_collection.py     # NEW: Collection behavior validation
├── test_route_optimization.py     # NEW: Pathfinding with preferences
├── test_visual_patterns.py        # NEW: Visual distinction validation
├── test_comparative_statics.py    # Income/price effect validation
└── test_educational_scenarios.py  # Pedagogical effectiveness
```

## Success Metrics (Measurable)
- [ ] **100% analytical solution match** for all test cases
- [ ] **Distinct visual patterns** for each preference type in spatial collection scenarios
- [ ] **Route optimization accuracy** >80% of theoretical maximum utility
- [ ] **<100ms response time** for parameter changes and route recalculation
- [ ] **Zero mathematical errors** in optimization routines
- [ ] **Clear pedagogical progression** from simple to complex collection scenarios
- [ ] **Visual identification success** >80% accuracy distinguishing preference types from movement patterns

This validation framework ensures our economic theory implementation is both mathematically rigorous and educationally effective, with the added benefit of concrete spatial behavior validation that makes abstract preferences observable and testable.