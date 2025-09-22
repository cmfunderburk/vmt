# Educational Scenarios Specification

## Purpose
Transform the spatial collection visualization framework into concrete educational content with specific parameterizations, tutorial scripts, and learning assessments for effective microeconomics education.

## Educational Philosophy and Objectives

### **Core Educational Mission**
Address the common student criticism "people don't behave like that" by demonstrating:
1. **Economic theory provides a flexible framework**, not rigid assumptions
2. **Different preference types create observable spatial behaviors**
3. **Mathematical models capture real patterns** of choice and optimization
4. **Spatial visualization makes abstract concepts concrete** and testable

### **Learning Progression Strategy**
- **Progressive Complexity**: Start with simple concepts, build systematically
- **Visual First**: Lead with observable behavior, follow with mathematical explanation  
- **Interactive Discovery**: Students explore and discover patterns through manipulation
- **Assessment Integration**: Measurable learning outcomes with immediate feedback

## Scenario Categories and Progression

### **Category 1: Basic Spatial Choice (Tutorial Scenarios)**

#### **Scenario 1.1: Single Good Collection**
**Educational Objective**: Introduce spatial constraint and energy budgets
**Economic Concepts**: Opportunity cost, budget constraints, spatial optimization

**Parameters**:
```json
{
  "scenario_id": "basic_single_good",
  "grid_size": 10,
  "agent_home": [5, 5],
  "agent_energy": 15,
  "good_type_A_locations": [[2, 3], [7, 8], [3, 7]],
  "good_type_B_locations": [],
  "good_value_A": 10,
  "good_value_B": 0,
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Introduction**: "Your agent needs to collect valuable goods but has limited energy for movement"
2. **Prediction**: "Which good should the agent collect first? Why?"
3. **Observation**: "Watch the agent's movement. Does it match your prediction?"
4. **Explanation**: "The agent chooses the closest high-value good to maximize benefit per energy spent"
5. **Experimentation**: "Move the goods or change energy. How does behavior change?"

**Assessment Questions**:
- [ ] "If energy increases from 15 to 25, how many more goods can the agent collect?"
- [ ] "If the good at (7,8) is moved to (9,9), will the agent still collect it? Why?"
- [ ] "What happens to the agent's route if movement cost doubles?"

#### **Scenario 1.2: Two Goods Introduction**
**Educational Objective**: Introduce trade-offs between different goods
**Economic Concepts**: Substitution, relative values, choice under constraint

**Parameters**:
```json
{
  "scenario_id": "basic_two_goods",
  "grid_size": 12,
  "agent_home": [6, 6],
  "agent_energy": 20,
  "good_type_A_locations": [[3, 4], [9, 8]],
  "good_type_B_locations": [[4, 3], [8, 9]],
  "good_value_A": 8,
  "good_value_B": 12,
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Setup**: "Now there are two types of goods: A (value 8) and B (value 12)"
2. **Prediction**: "Which type should the agent prefer? What route will it take?"
3. **Observation**: "Notice how the agent weighs distance against value"
4. **Parameter Adjustment**: "Change the values - make A worth 15 and B worth 6"
5. **Analysis**: "How does behavior change? What does this tell us about preferences?"

### **Category 2: Preference Type Demonstration (Core Educational Scenarios)**

#### **Scenario 2.1: Cobb-Douglas Balanced Collection**
**Educational Objective**: Demonstrate balanced preference behavior
**Economic Concepts**: Diminishing marginal utility, balanced consumption, interior solutions

**Parameters**:
```json
{
  "scenario_id": "cobb_douglas_demo",
  "grid_size": 15,
  "agent_home": [7, 7],
  "agent_energy": 30,
  "preference_type": "cobb_douglas",
  "alpha": 0.5,
  "good_type_A_locations": [[2, 3], [12, 4], [5, 11], [8, 2]],
  "good_type_B_locations": [[4, 2], [13, 8], [6, 12], [9, 3]],
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Introduction**: "This agent has Cobb-Douglas preferences: U = A^0.5 * B^0.5"
2. **Mathematical Insight**: "Equal exponents mean the agent values balance between A and B"
3. **Prediction**: "What collection pattern do you expect to see?"
4. **Observation**: "Watch the agent collect roughly equal amounts of A and B"
5. **Experimentation**: "Change alpha to 0.3 or 0.7. How does behavior change?"
6. **Economic Insight**: "This shows how preferences shape observable behavior"

**Assessment Activities**:
- [ ] **Pattern Recognition**: "Identify Cobb-Douglas behavior in a mixed scenario"
- [ ] **Parameter Effects**: "Predict behavior changes when alpha changes from 0.5 to 0.3"
- [ ] **Optimization Understanding**: "Explain why the agent doesn't collect only the closest goods"

#### **Scenario 2.2: Perfect Substitutes Focused Collection**  
**Educational Objective**: Demonstrate corner solution behavior
**Economic Concepts**: Perfect substitutability, corner solutions, relative price effects

**Parameters**:
```json
{
  "scenario_id": "perfect_substitutes_demo",
  "grid_size": 15,
  "agent_home": [7, 7],
  "agent_energy": 30,
  "preference_type": "perfect_substitutes",
  "substitution_rate": 2,
  "good_type_A_locations": [[2, 3], [12, 4], [5, 11], [8, 2]],
  "good_type_B_locations": [[4, 2], [13, 8], [6, 12], [9, 3]],
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Introduction**: "Perfect substitute preferences: U = A + 2*B"
2. **Mathematical Insight**: "This agent treats 2 units of A as equivalent to 1 unit of B"
3. **Prediction**: "Will the agent collect both types or focus on one?"
4. **Observation**: "Notice the agent strongly prefers B (worth 2x as much)"
5. **Distance Effect**: "But if A is much closer, the agent might collect A instead"
6. **Economic Insight**: "This shows how transportation costs affect choice even with clear preferences"

**Assessment Activities**:
- [ ] **Corner Solution Recognition**: "Identify when the agent will collect only one good type"
- [ ] **Substitution Rate Effects**: "Predict changes when substitution rate changes from 2 to 0.5"  
- [ ] **Spatial Economics**: "Explain how distance can override preference strength"

#### **Scenario 2.3: Leontief Proportional Collection**
**Educational Objective**: Demonstrate fixed proportion behavior  
**Economic Concepts**: Complementarity, fixed proportions, Leontief preferences

**Parameters**:
```json
{
  "scenario_id": "leontief_demo", 
  "grid_size": 15,
  "agent_home": [7, 7],
  "agent_energy": 30,
  "preference_type": "leontief",
  "proportion_a": 1,
  "proportion_b": 1,
  "good_type_A_locations": [[2, 3], [12, 4], [5, 11], [8, 2]],
  "good_type_B_locations": [[4, 2], [13, 8], [6, 12], [9, 3]],
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Introduction**: "Leontief preferences: U = min(A, B)"
2. **Mathematical Insight**: "The agent needs goods in fixed proportions - like shoes (left and right)"
3. **Prediction**: "How will the need for equal quantities affect collection behavior?"
4. **Observation**: "Watch the agent maintain equal collection even when it's inefficient"
5. **Efficiency Trade-off**: "The agent passes by nearby goods to maintain proportions"
6. **Economic Insight**: "This shows how complementarity creates different optimization patterns"

**Assessment Activities**:
- [ ] **Proportion Maintenance**: "Predict agent behavior when starting with unequal goods"
- [ ] **Inefficiency Recognition**: "Identify when proportional collection creates spatial inefficiency"
- [ ] **Complementarity Understanding**: "Explain why the agent doesn't just collect the closest goods"

### **Category 3: Comparative Analysis (Advanced Educational Scenarios)**

#### **Scenario 3.1: Three Agents Comparison**
**Educational Objective**: Direct comparison of all three preference types
**Economic Concepts**: Preference heterogeneity, behavioral prediction, choice patterns

**Parameters**:
```json
{
  "scenario_id": "three_agent_comparison",
  "grid_size": 20,
  "agents": [
    {"home": [5, 10], "energy": 25, "type": "cobb_douglas", "alpha": 0.5},
    {"home": [10, 10], "energy": 25, "type": "perfect_substitutes", "rate": 1.5},
    {"home": [15, 10], "energy": 25, "type": "leontief", "proportions": [1, 1]}
  ],
  "good_type_A_locations": [[3, 5], [8, 6], [12, 7], [17, 8], [5, 15], [15, 15]],
  "good_type_B_locations": [[4, 4], [9, 5], [13, 6], [18, 7], [6, 16], [16, 16]],
  "movement_cost": 1
}
```

**Tutorial Script**:
1. **Setup**: "Three agents with different preferences in the same environment"
2. **Prediction Challenge**: "Predict which agent will collect which goods"
3. **Simultaneous Observation**: "Watch all three agents move simultaneously"
4. **Pattern Analysis**: "Identify the distinct movement patterns"
5. **Economic Explanation**: "How do different preferences create different behaviors?"
6. **Prediction Test**: "Given a new scenario, predict each agent's behavior"

#### **Scenario 3.2: Parameter Sensitivity Analysis**
**Educational Objective**: Understand how preference parameters affect behavior
**Economic Concepts**: Sensitivity analysis, parameter effects, behavioral stability

**Interactive Parameters**:
- **Cobb-Douglas α**: Slider from 0.1 to 0.9
- **Perfect Substitutes rate**: Slider from 0.5 to 3.0  
- **Leontief proportions**: Adjustable A:B ratios
- **Movement cost**: Slider from 0.5 to 2.0
- **Agent energy**: Slider from 10 to 50

**Assessment Framework**:
- [ ] **Parameter Sensitivity**: "How does Cobb-Douglas behavior change as α moves from 0.3 to 0.7?"
- [ ] **Threshold Effects**: "At what substitution rate does Perfect Substitutes behavior flip?"
- [ ] **Cost Sensitivity**: "How does increased movement cost affect each preference type?"

### **Category 4: Research and Extension Scenarios**

#### **Scenario 4.1: Income Effects Demonstration**
**Educational Objective**: Show how budget constraints affect choice patterns
**Economic Concepts**: Income effects, budget expansion, choice under different constraints

**Variable Parameters**:
- **Low Budget**: Energy = 15, limited collection
- **Medium Budget**: Energy = 30, moderate collection  
- **High Budget**: Energy = 50, extensive collection

**Research Questions**:
- "How does budget expansion affect collection patterns for each preference type?"
- "Do income effects differ systematically across preference types?"
- "At what budget levels do agents reach satiation points?"

#### **Scenario 4.2: Goods Scarcity and Abundance**
**Educational Objective**: Examine behavior under resource constraints
**Economic Concepts**: Scarcity effects, abundance effects, resource allocation

**Scenarios**:
- **Scarcity**: 2-3 goods total, high competition  
- **Abundance**: 20+ goods, no meaningful constraint
- **Asymmetric**: Abundant A, scarce B (or vice versa)

## Assessment and Learning Measurement Framework

### **Immediate Assessment (Within-Scenario)**
1. **Prediction Accuracy**: Student predictions vs. actual agent behavior
2. **Pattern Recognition**: Ability to identify preference types from behavior
3. **Parameter Effects**: Understanding of how parameter changes affect behavior
4. **Economic Reasoning**: Quality of explanations for observed behavior

### **Progressive Assessment (Across-Scenario)**
1. **Transfer Learning**: Apply knowledge from simple to complex scenarios
2. **Comparative Analysis**: Distinguish between preference types in mixed scenarios
3. **Economic Intuition**: Develop general principles from specific observations
4. **Predictive Capability**: Forecast behavior in novel scenarios

### **Comprehensive Assessment (Course-Level)**
1. **Conceptual Integration**: Connect spatial behavior to abstract economic theory
2. **Model Limitations**: Understand when/why models might not apply to reality
3. **Policy Implications**: Analyze how preference heterogeneity affects outcomes
4. **Research Application**: Design new scenarios to test economic hypotheses

## Implementation Integration

### **Tutorial System Integration**
```python
# Example tutorial step structure
{
  "step_id": "cobb_douglas_intro_1",
  "scenario_file": "scenarios/cobb_douglas_demo.json",
  "instruction_text": "This agent has Cobb-Douglas preferences...",
  "prediction_prompt": "What collection pattern do you expect?",
  "observation_guidance": "Watch for balanced collection behavior...",
  "explanation_text": "The mathematical form U = A^α * B^(1-α) creates...",
  "assessment_question": {
    "type": "multiple_choice",
    "question": "If α increases from 0.5 to 0.7, the agent will...",
    "options": ["Collect more A", "Collect more B", "Collection unchanged"],
    "correct": 0,
    "explanation": "Higher α increases the weight on good A..."
  }
}
```

### **Content Management System**
- **Scenario Library**: JSON-based scenario definitions with versioning
- **Tutorial Scripts**: Structured tutorial content with assessment integration  
- **Progress Tracking**: Student progress through tutorial sequences
- **Adaptive Difficulty**: Scenario complexity adjusts to student performance
- **Instructor Dashboard**: Progress monitoring and performance analytics

### **Educational Effectiveness Measurement**
- **Engagement Metrics**: Time spent, interactions, exploration patterns
- **Learning Outcomes**: Pre/post assessment improvements, concept mastery
- **Retention Testing**: Long-term knowledge retention measurement
- **Transfer Validation**: Application of concepts to new scenarios
- **Instructor Feedback**: Qualitative assessment of educational effectiveness

This educational scenarios specification provides the concrete content framework needed to transform your spatial collection visualization into an effective microeconomics education platform, with measurable learning outcomes and systematic pedagogical progression.