# Test Quarantine

**Purpose:** Temporary holding area for tests under review during refactoring.

## Process

### Moving Tests to Quarantine

When reviewing tests during refactoring cleanup, tests that are uncertain should be moved here:

```bash
git mv tests/unit/test_uncertain_feature.py tests/QUARANTINE/
```

Then document in `QUARANTINE_NOTES.md`:
```markdown
## test_uncertain_feature.py
- **Moved:** 2025-10-04
- **Reason:** Unclear if feature still exists or if test is still relevant
- **Questions:** 
  - Does FeatureX still work the same way?
  - Is this test redundant with test_other_feature.py?
- **Decision needed by:** 2025-10-11
```

### Review Schedule

Quarantined tests should be reviewed **weekly** to decide:
- **KEEP** - Move back to appropriate test directory
- **UPDATE** - Modify test and move back
- **REMOVE** - Delete permanently with documented rationale

### Quarantine Time Limit

Tests should not remain in quarantine longer than **2 weeks**. If uncertain after 2 weeks, default to **KEEP** (safer than deleting).

## Current Quarantine Status

See `QUARANTINE_NOTES.md` for detailed tracking of quarantined tests.

---

**Note:** This directory should be empty when refactoring is complete. Any remaining tests must be resolved before finalizing the refactor.

