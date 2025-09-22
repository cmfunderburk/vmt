# Theory Progression Considerations

## Decision Summary

**Final Decision**: **Option 3 - Foundation + Economic Rigor** for MVP
**Date**: September 22, 2025
**Rationale**: Address the "people don't behave like that" criticism upfront while demonstrating the platform's full educational potential.

## The Theory Progression Problem

The original planning document had unclear boundaries between:
- MVP: "Preference-Choice-Utility Foundation"
- Post-MVP Phase 1: "Consumer Theory Extension" 
- Post-MVP Phase 2: "Multi-Agent and Market Theory"

**Key Issue**: What constitutes "foundation" vs "extension" was ambiguous, risking scope creep or inadequate MVP validation.

## Three Options Considered

### Option 1: Pure Foundation (Ultra-MVP)
- Single good type
- Single constraint type  
- Single preference type
- **Rejected**: Too simple to demonstrate real economic insight

### Option 2: Foundation + Basic Trade-offs
- Two good types requiring choice trade-offs
- Budget constraint system
- Simple preference functions (Cobb-Douglas only)
- **Considered**: Good balance of complexity and manageability

### Option 3: Foundation + Economic Rigor (CHOSEN)
- Multiple preference functions (Cobb-Douglas, Perfect Substitutes, Leontief)
- Full constraint system
- Demand curve generation capability
- Consumer surplus visualization
- **Selected**: Addresses pedagogical concerns and demonstrates platform potential

## Why Option 3 Was Chosen

### Primary Pedagogical Argument
The most common student objection to microeconomic theory is **"people don't behave like that"** - referring to specific utility function assumptions. By showing multiple preference types from the start, we transform this criticism into a strength:

*"Economics doesn't assume people are identical. It provides a framework flexible enough to represent different types of people. Watch how different preference types lead to different spatial behaviors."*

### Supporting Arguments
1. **Higher pedagogical engagement** - more parameters to adjust, more scenarios to explore
2. **Better instructor adoption potential** - can adapt to specific teaching needs
3. **Demonstrates platform sophistication** - shows this isn't just a toy
4. **Stronger research foundation** - easier transition to research capabilities
5. **Addresses realism immediately** - prevents common student disengagement

## Concrete MVP Specification (Option 3)

### Core Preference Types
1. **Cobb-Douglas** (balanced trade-offs)
   - Visual: Agent balances between both goods smoothly
   - Student insight: "This person likes variety"

2. **Perfect Substitutes** (straight-line indifference)
   - Visual: Agent focuses entirely on cheaper good
   - Student insight: "This person sees goods as interchangeable"

3. **Leontief/Perfect Complements** (right-angle indifference)
   - Visual: Agent always takes goods in fixed proportion
   - Student insight: "This person needs both goods together"

### MVP Components
- Agent choosing between 2 types of items (A and B) on grid
- All three preference function types available
- Full budget constraint system
- Movement cost constraints
- Real-time parameter adjustment for all preference types
- Side-by-side comparison view
- Progressive tutorial revealing complexity gradually

### Implementation Strategy
**Week 1-2**: Build flexible preference system architecture
- Design extensible preference function interface
- Implement spatial optimization engine for any preference type
- Build parameter adjustment UI for different function types

**Week 3-4**: Implement the three core preference types
- Focus on visually distinct spatial behaviors
- Build tutorial showing all three types in action
- Create comparison interface

**Week 5-6**: Polish and educational validation
- A/B testing: single vs multiple preference functions
- Refine based on actual learning outcome data

### Risk Mitigation
**For "Too Complex" Risk**:
- Progressive disclosure in tutorials
- Clear visual distinction between preference types
- Always relate back to "different people, different trade-offs"

**For "Implementation Complexity" Risk**:
- Abstraction layer for extensible preference system
- Mathematical validation before visual implementation
- Modular, testable components

## Extension Path (Post-MVP)

### Extension Phase 1: Advanced Consumer Theory
- Additional preference functions (CES, Stone-Geary, etc.)
- Income and substitution effect decomposition
- Advanced comparative statics
- Welfare analysis tools

### Extension Phase 2: Multi-Agent Markets
- Multiple agents with different preference types
- Simple trading mechanisms
- Market equilibrium visualization
- Price formation dynamics

## Impact on Planning Document

### Changes Needed in initial_planning.md:

1. **Update MVP Milestone Definition** - specify three preference functions as core requirement
2. **Revise Scaffold Components** - ensure S-08 through S-12 reflect multi-preference architecture
3. **Update Success Metrics** - include preference flexibility as validation criterion
4. **Modify Risk Assessment** - address implementation complexity vs pedagogical benefit trade-off
5. **Clarify Timeline** - adjust for additional complexity while maintaining 6-week MVP target

### Key Planning Document Updates Required:
- Section 1: Update success metrics to include preference flexibility
- Section 2: Revise user scenarios to showcase multiple preference types
- Section 6: Update domain model to reflect flexible preference architecture  
- Section 14: Revise roadmap timeline and milestones
- Section 15: Add decision record for Option 3 selection

## Next Steps
1. Update initial_planning.md with Option 3 specifications
2. Define specific preference function implementations
3. Design progressive tutorial structure
4. Plan A/B testing methodology for educational validation
