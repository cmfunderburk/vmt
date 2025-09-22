# Theory Progression Considerations

## The Theory Progression Problem

The current roadmap doesn't clearly define what's minimally needed to demonstrate the core educational value vs what adds depth and completeness. Let me break down the economic theory progression to clarify what should be "foundation" vs "extension."

The current roadmap mentions:
- MVP: "Preference-Choice-Utility Foundation"
- Post-MVP Phase 1: "Consumer Theory Extension"
- Post-MVP Phase 2: "Multi-Agent and Market Theory"

But what exactly constitutes "foundation" vs "extension"? Where's the line?

Let's examine this through the lens of **educational dependency chains**.

## **Foundation** (Minimum Viable Economic Education)

**What students absolutely need to understand first:**

1. **Spatial Agent Rationality** 
   - Agent has preferences over spatial locations/items
   - Agent makes consistent choices (if A preferred to B yesterday, still preferred today)
   - Visual: Agent reliably moves toward preferred items

2. **Preference-Choice Connection**
   - Student can see that changing preferences changes behavior
   - Visual: Slider changes preference weights → agent immediately changes movement pattern
   - This is the **core insight**: preferences drive choices

3. **Constraint Recognition**
   - Agent can't have everything (budget constraint, movement costs, time limits)
   - Visual: Agent stops short of preferred item due to constraint
   - This demonstrates **scarcity**

4. **Optimization Intuition**
   - Agent finds the "best available" option given constraints
   - Visual: Agent chooses reachable item with highest utility, not globally optimal item
   - This is **constrained optimization** made concrete

**Foundation Success Metric**: Student can predict agent behavior when you change preferences or constraints.

## **Extension** (Consumer Theory Completeness)

**What adds depth but isn't essential for the core insight:**

1. **Multiple Goods with Trade-offs**
   - Agent choosing between different types of items (food vs entertainment)
   - Substitution effects when relative prices change
   - Income effects when budget changes

2. **Demand Curve Generation**
   - Systematically varying prices and recording quantity demanded
   - Connecting individual spatial choices to market demand curves

3. **Consumer Surplus Analysis**
   - Measuring how much better off the agent is from having choices
   - Visualizing welfare loss from constraints

4. **Comparative Statics**
   - "What happens when income doubles?"
   - "What happens when preferences shift?"

## **The Critical Boundary Question**

**Where exactly should the MVP stop?**

**Option 1: Pure Foundation (Ultra-MVP)**
- Single good type (e.g., just "food items" scattered on grid)
- Single constraint type (e.g., just movement cost)
- Single preference type (e.g., simple distance-based utility)
- No trade-offs, no complex calculations

**Option 2: Foundation + Basic Trade-offs**
- Two good types requiring choice trade-offs
- Budget constraint system
- Simple preference functions (Cobb-Douglas)
- Basic optimization demonstration

**Option 3: Foundation + Economic Rigor**
- Multiple preference functions
- Full constraint system
- Demand curve generation
- Consumer surplus visualization

## **My Recommendation: Option 2**

**Rationale**: Option 1 might be too simple to demonstrate real economic insight (just "agents move toward things they like"). Option 3 might be too complex for initial validation. Option 2 gives you:

- **Real Economic Content**: Students see genuine trade-offs and optimization
- **Clear Educational Value**: The spatial visualization actually adds insight beyond traditional graphs
- **Manageable Scope**: Can be implemented and tested with real users quickly
- **Extension Path**: Clear progression to more sophisticated theory

## **Concrete Foundation/Extension Boundary**

**Foundation MVP includes:**
- Agent choosing between 2 types of items (A and B) on grid
- Budget constraint (can afford X units total)
- Simple preference weighting (prefers A vs B at some ratio)
- Movement cost (distance matters)
- Real-time parameter adjustment
- One complete tutorial walking through a choice scenario

**Extension Phase 1 adds:**
- Multiple preference functions (Cobb-Douglas, perfect substitutes, Leontief)
- Demand curve generation by varying prices
- Consumer surplus calculation and visualization
- Comparative statics (income effects, preference shifts)

**Extension Phase 2 adds:**
- Multiple agents
- Simple trading/exchange
- Market clearing mechanisms

## **Key Questions to Resolve This**

1. **Educational Testing**: What's the minimum example that would let you test whether spatial visualization actually helps students understand economic choice?

2. **Implementation Complexity**: Which requires more work - making trade-offs between 2 goods visually clear, or implementing multiple preference functions?

3. **User Validation**: Would an economics instructor be convinced of the platform's value from seeing trade-offs between 2 goods, or do they need to see demand curves?

## **Decision Framework**

The MVP should demonstrate **genuine economic trade-offs** (2 goods, budget constraint), not just **pure preference demonstration** (agent just likes some locations more than others).

**Why**: The core value proposition is that spatial visualization makes economic concepts more intuitive. If there's no real economic concept being demonstrated (like trade-offs and optimization), then the spatial visualization is just decoration, not education.

**Success Criteria for MVP**: An economics instructor watches a student use the platform and says "Now I see why this is better than just drawing utility curves on a whiteboard."

## **Next Steps**

1. Define the exact MVP scenario (what 2 goods, what budget constraint, what preference function)
2. Identify the minimum viable tutorial that demonstrates the educational value
3. Clarify what gets deferred to Extension Phase 1 vs Extension Phase 2
4. Update the roadmap with these clearer boundaries