from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference


def test_cobb_douglas_alpha_weight_shift():
    """Higher alpha should increase relative utility of bundles skewed to good1.

    We compare two bundles: one rich in good1, one symmetric. As alpha increases,
    the utility ratio (good1-heavy vs symmetric) should not decrease.
    This is a directional sensitivity sanity check (not a full comparative static).
    """
    bundle_heavy = (8, 2)
    bundle_sym = (5, 5)
    alphas = [0.2, 0.4, 0.6, 0.8]
    ratios: list[float] = []
    for a in alphas:
        pref = CobbDouglasPreference(alpha=a)
        u_heavy = pref.utility(bundle_heavy)
        u_sym = pref.utility(bundle_sym)
        ratios.append(u_heavy / u_sym)
    # Ratios should be monotonically non-decreasing (allow tiny float noise)
    for earlier, later in zip(ratios, ratios[1:], strict=False):
        assert later + 1e-9 >= earlier


def test_perfect_substitutes_weight_increase():
    """Increasing coefficient on good1 should (weakly) raise relative utility when good1 dominates.

    Compare bundle A (good1-heavy) vs bundle B (good2-heavy). As coeff1 grows
    relative to coeff2, utility advantage of bundle A should not fall.
    """
    bundle_a = (9, 1)
    bundle_b = (1, 9)
    coeff_sets = [(1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]
    diffs: list[float] = []
    for c1, c2 in coeff_sets:
        pref = PerfectSubstitutesPreference(a=c1, b=c2)
        ua = pref.utility(bundle_a)
        ub = pref.utility(bundle_b)
        diffs.append(ua - ub)
    for earlier, later in zip(diffs, diffs[1:], strict=False):
        assert later + 1e-9 >= earlier
