# Manual Tests for Unified Target Selection Behavior

This folder contains 7 comprehensive manual tests designed to validate the unified target selection behavior across different scenarios. Each test should be run through the GUI to observe agent behavior during different phases.

## Test Structure

Each test runs for **900 turns** with the following phase structure:

| Phase | Turns | Foraging | Exchange | Expected Behavior |
|-------|-------|----------|----------|-------------------|
| 1 | 1-200 | ✅ | ✅ | **Both behaviors**: Agents forage resources, return home, withdraw goods, seek trade partners, execute trades |
| 2 | 201-400 | ✅ | ❌ | **Forage only**: Agents forage resources, return home, deposit (no withdrawal), continue foraging. Home inventory accumulates |
| 3 | 401-600 | ❌ | ✅ | **Exchange only**: Agents withdraw home inventory, seek trade partners, execute trades, return home, repeat cycle |
| 4 | 601-650 | ❌ | ❌ | **Both disabled**: Agents return home, deposit any cargo, idle at home (shortened phase) |
| 5 | 651-850 | ✅ | ✅ | **Both re-enabled**: Agents resume active behavior, withdraw goods, seek resources/partners |
| 6 | 851-900 | ❌ | ❌ | **Final idle phase**: All agents should return home and idle |

## Key Validation Points

### Phase Transitions (Watch for these behaviors)
- **Turn 201**: Agents should stop trading, continue foraging only
- **Turn 401**: Agents should stop foraging, withdraw home inventory for trading only  
- **Turn 601**: Agents should return home, deposit cargo, idle at home
- **Turn 651**: Agents should resume both behaviors from home  
- **Turn 851**: Agents should return home and idle

### Agent Behavior Validation
- **✅ No idle+cargo bugs**: Agents should never be idle while carrying goods
- **✅ Proper home transitions**: Agents with cargo should always return home to deposit
- **✅ Correct mode usage**: 
  - `FORAGE`: Seeking resources or moving toward resources
  - `RETURN_HOME`: Carrying cargo, moving toward home  
  - `MOVE_TO_PARTNER`: Paired with partner, moving to meeting point
  - `IDLE`: At home with no opportunities, or seeking trade partners
- **✅ Inventory management**: 
  - Foraging-only: Home inventory accumulates, no withdrawal
  - Exchange-only: Regular deposit/withdrawal cycles
  - Both enabled: Active cycling with withdrawals
- **✅ Trade execution**: Valid trades occur when agents are co-located with partners

### Visual Indicators to Watch
- **Yellow arrows**: `RETURN_HOME` mode (should always lead to home)
- **Blue arrows**: `FORAGE` mode (seeking resources)
- **Purple arrows**: `MOVE_TO_PARTNER` mode (converging to meeting points)
- **Agent colors**: May indicate carrying goods or home inventory
- **Trade lines**: Should appear during bilateral exchange phases
- **Resource depletion/respawn**: Should affect agent behavior appropriately

## Test Start Menu

The **Unified Test Start Menu** (`test_start_menu.py`) provides a central interface for launching all manual tests:

### Features:
- **Visual test cards** with descriptions and configuration details
- **One-click launch** for any available test
- **Duration estimates** for each speed setting
- **Test status tracking** (available vs. coming soon)
- **Integrated instructions** and phase schedule information

### Available Tests:
- ✅ **Test 1: Baseline** - Standard mixed preference validation
- ✅ **Test 2: Sparse Long-Range** - Distance-based decision making
- ✅ **Test 3: High Density Local** - Crowding behavior validation
- ✅ **Test 4: Large World Global** - Long-distance decision making
- ✅ **Test 5: Pure Cobb-Douglas** - Balanced utility optimization
- ✅ **Test 6: Pure Leontief** - Complementary resource requirements
- ✅ **Test 7: Pure Perfect Substitutes** - Resource interchangeability

## Command Reference

### Development Testing vs Manual Testing
- **`make test-unit`**: Runs automated unit/integration tests (210+ tests, ~seconds)
  - Used for development validation, determinism checks, CI/CD
  - Catches regressions and ensures correctness
- **`make manual-tests`**: Launches educational GUI tests (7 scenarios, ~15 min each)
  - Used for visual validation and educational demonstration
  - Observes agent behavior through phase transitions

## Running the Tests

### Option 1: Unified Start Menu (Recommended)
1. **Launch the start menu**: `make manual-tests` from project root, or `python test_start_menu.py` from this directory
2. **Select a test**: Click on any available test card to launch it
3. **Configure test speed**: Each test opens with a speed dropdown (default: 1 turn/second)
4. **Observe and validate**: Watch the pygame viewport and console output

### Option 2: Individual Test Scripts
1. **Start each test script**: `python test_X.py` (where X is 1-7)
2. **Configure test speed**: Use the dropdown to select speed (default: 1 turn/second)
   - **1 turn/second** - 15 minutes total (good for detailed observation)
   - **3 turns/second** - 5 minutes total 
   - **10 turns/second** - 1.5 minutes total
   - **20 turns/second** - 45 seconds total
   - **Unlimited** - ~14 seconds total (60 FPS, for quick validation)
3. **Observe GUI behavior**: Watch pygame viewport and agent movements during phase transitions
4. **Monitor console output**: Check for phase announcements and any error messages
5. **Validate at key turns**: Pay special attention to behavior at turns 201, 401, 601, 651, 851

## Test Scenarios Overview

| Test | Agents | Grid | Density | Perception | Preference Mix | Focus Area |
|------|--------|------|---------|------------|---------------|------------|
| 1 | 20 | 30×30 | 0.25 | 8 | Random | **Baseline behavior** |
| 2 | 10 | 40×40 | 0.05 | 15 | Random | **Sparse resources, long perception** |
| 3 | 100 | 30×30 | 0.5 | 2 | Random | **High density, local perception** |  
| 4 | 10 | 64×64 | 0.5 | 20 | Random | **Large world, global perception** |
| 5 | 20 | 30×30 | 0.25 | 8 | Cobb-Douglas | **Single preference type** |
| 6 | 20 | 30×30 | 0.25 | 8 | Leontief | **Complementary preferences** |
| 7 | 20 | 30×30 | 0.25 | 8 | Perfect Substitutes | **Substitution preferences** |

## Expected Outcomes

### Successful Test Results
- **No crashes or errors** throughout 1050 turns
- **Smooth phase transitions** at specified turn boundaries  
- **Proper agent lifecycle** in all phases
- **No stuck agents** (idle with cargo or improper states)
- **Appropriate resource/trade activity** based on enabled behaviors
- **Consistent performance** (no significant frame rate drops)

### Common Issues to Watch For
- **Agents stuck idle with cargo** (should never happen)
- **Improper mode transitions** at phase boundaries
- **Trading activity in forage-only phases** (should not occur)
- **Resource collection in exchange-only phases** (should not occur)
- **Agents not returning home** when both behaviors disabled
- **Performance degradation** with high agent counts or large grids

## Troubleshooting

If you observe unexpected behavior:
1. **Check console output** for error messages
2. **Note the specific turn number** when issues occur
3. **Record agent modes and positions** during problematic behavior
4. **Verify phase transitions** are occurring at correct turn boundaries
5. **Compare with expected behavior** documented above

## Test Results Documentation

For each test, document:
- ✅/❌ **Phase transitions occurred correctly**
- ✅/❌ **No idle+cargo bugs observed**  
- ✅/❌ **Appropriate inventory management**
- ✅/❌ **Trade activity in correct phases only**
- ✅/❌ **Performance remained stable**
- **Any unexpected behaviors or errors**