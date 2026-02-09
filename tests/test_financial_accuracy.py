"""Financial accuracy tests.

Risk category: DIRECT MONETARY HARM
If these fail, members are overcharged or the plan overpays.
Each test documents the specific financial risk if the assertion is wrong.
"""

from decimal import Decimal

from policy.models import DeductibleType


# ---------------------------------------------------------------------------
# Deductible structure
# ---------------------------------------------------------------------------

class TestDeductibles:

    def test_in_network_individual(self, policy):
        """Risk: Member charged wrong deductible → delayed access to benefits."""
        assert policy.deductibles.in_network.individual == Decimal("1500")

    def test_in_network_family(self, policy):
        assert policy.deductibles.in_network.family == Decimal("3000")

    def test_in_network_embedded(self, policy):
        """Risk: Non-embedded applied to in-network → one family member must satisfy
        full $3000 before plan pays, instead of individual $1500 cap."""
        assert policy.deductibles.in_network.type == DeductibleType.EMBEDDED

    def test_out_of_network_individual(self, policy):
        assert policy.deductibles.out_of_network.individual == Decimal("3000")

    def test_out_of_network_family(self, policy):
        assert policy.deductibles.out_of_network.family == Decimal("6000")

    def test_out_of_network_non_embedded(self, policy):
        """Risk: Embedded applied to OON → plan pays prematurely before family
        deductible is satisfied, creating actuarial exposure."""
        assert policy.deductibles.out_of_network.type == DeductibleType.NON_EMBEDDED

    def test_cross_accumulation_independent(self, policy):
        """Risk: Cross-accumulation enabled → in-network spend reduces OON deductible,
        inflating OON benefits beyond contracted terms."""
        assert policy.deductibles.cross_accumulation is False

    def test_embedded_individual_cap_within_family(self, policy):
        """Risk: Embedded deductible means no single member should exceed the individual
        amount. Family deductible must be >= 2x individual for embedded to work."""
        ded = policy.deductibles.in_network
        assert ded.type == DeductibleType.EMBEDDED
        assert ded.family >= ded.individual * 2


# ---------------------------------------------------------------------------
# Out-of-pocket maximum
# ---------------------------------------------------------------------------

class TestOOPMax:

    def test_in_network_individual(self, policy):
        assert policy.oop_max.in_network.individual == Decimal("4500")

    def test_in_network_family(self, policy):
        assert policy.oop_max.in_network.family == Decimal("9000")

    def test_out_of_network_individual(self, policy):
        assert policy.oop_max.out_of_network.individual == Decimal("9000")

    def test_out_of_network_family(self, policy):
        assert policy.oop_max.out_of_network.family == Decimal("18000")

    def test_oop_includes_deductible(self, policy):
        """Risk: Deductible not counting toward OOP → member pays deductible + full OOP,
        exceeding contracted maximum."""
        assert "deductible" in policy.oop_max.includes

    def test_oop_includes_copays(self, policy):
        assert "copayments" in policy.oop_max.includes

    def test_oop_includes_coinsurance(self, policy):
        assert "coinsurance" in policy.oop_max.includes

    def test_oop_excludes_premiums(self, policy):
        """Risk: Premiums counting toward OOP → member hits max too soon → plan
        pays 100% prematurely."""
        assert "premiums" in policy.oop_max.excludes

    def test_oop_excludes_balance_billing(self, policy):
        assert "balance_billed_charges" in policy.oop_max.excludes

    def test_oop_excludes_prior_auth_penalties(self, policy):
        """Risk: Auth penalties counting toward OOP undermines the penalty's purpose
        as a cost-control mechanism."""
        assert "prior_auth_penalties" in policy.oop_max.excludes


# ---------------------------------------------------------------------------
# Accumulator adjustment program
# ---------------------------------------------------------------------------

class TestAccumulatorAdjustment:

    def test_enabled(self, policy):
        """Risk: Disabled → manufacturer copay cards count toward OOP → member hits
        max artificially early → plan pays 100% on brand/specialty drugs."""
        assert policy.oop_max.accumulator_adjustment.enabled is True

    def test_excluded_from_deductible(self, policy):
        assert policy.oop_max.accumulator_adjustment.excluded_from_deductible is True

    def test_excluded_from_oop(self, policy):
        assert policy.oop_max.accumulator_adjustment.excluded_from_oop is True

    def test_applies_to_brand_tiers(self, policy):
        """Risk: Accumulator applied to wrong tiers → generics inappropriately excluded
        or brand drugs inappropriately included."""
        tiers = policy.oop_max.accumulator_adjustment.applies_to_tiers
        assert 3 in tiers  # preferred brand
        assert 4 in tiers  # non-preferred brand
        assert 1 not in tiers  # preferred generic should NOT be affected
        assert 2 not in tiers  # non-preferred generic should NOT be affected


# ---------------------------------------------------------------------------
# ER financial rules
# ---------------------------------------------------------------------------

class TestERFinancials:

    def test_er_copay_amount(self, policy):
        assert policy.emergency.er.facility_copay == Decimal("350")

    def test_er_copay_waived_on_admission(self, policy):
        """Risk: Copay NOT waived → member double-charged (ER copay + inpatient copay)
        when admitted from ER. Direct financial harm."""
        assert policy.emergency.er.copay_waived_if_admitted is True

    def test_er_admission_window(self, policy):
        """Risk: Wrong window → copay waiver applied to admissions >24h after ER,
        or denied for admissions within 24h."""
        assert policy.emergency.er.admission_window_hours == 24


# ---------------------------------------------------------------------------
# Prior auth financial penalties
# ---------------------------------------------------------------------------

class TestPriorAuthPenalties:

    def test_inpatient_prior_auth_penalty_amount(self, policy):
        assert policy.inpatient.prior_auth_penalty == Decimal("500")

    def test_penalty_excluded_from_oop(self, policy):
        """Risk: Penalty counts toward OOP → defeats purpose of penalty as cost
        control; member hits OOP max faster."""
        assert policy.inpatient.prior_auth_penalty_counts_toward_oop is False

    def test_in_network_member_held_harmless(self, policy):
        """Risk: In-network member billed for provider's failure to obtain auth →
        member penalized for provider error."""
        assert policy.prior_authorization.penalty.in_network_member_held_harmless is True

    def test_oon_benefit_reduction(self, policy):
        """Risk: Wrong reduction percentage → member under- or over-charged for
        failure to obtain prior auth."""
        assert policy.prior_authorization.penalty.out_of_network_benefit_reduction == Decimal("0.25")


# ---------------------------------------------------------------------------
# Pharmacy financial rules
# ---------------------------------------------------------------------------

class TestPharmacyFinancials:

    def test_tier1_copay(self, policy):
        t1 = next(t for t in policy.pharmacy.tiers if t.tier == 1)
        assert t1.retail_30day_copay == Decimal("10")

    def test_tier5_coinsurance_with_cap(self, policy):
        """Risk: No per-fill cap on specialty → member exposure unbounded on
        high-cost biologics ($10k+/fill)."""
        t5 = next(t for t in policy.pharmacy.tiers if t.tier == 5)
        assert t5.retail_30day_coinsurance == Decimal("0.30")
        assert t5.retail_30day_max_per_fill == Decimal("350")

    def test_tier5_no_mail_order(self, policy):
        """Risk: Specialty drugs shipped via mail order without proper cold-chain
        or monitoring → safety and financial exposure."""
        t5 = next(t for t in policy.pharmacy.tiers if t.tier == 5)
        assert t5.mail_90day_available is False

    def test_maintenance_penalty_not_toward_oop(self, policy):
        """Risk: Retail fill penalty counting toward OOP → member hits max sooner →
        plan pays 100% on all Rx prematurely."""
        assert policy.pharmacy.maintenance_med_rule.penalty_counts_toward_oop is False

    def test_generic_cost_difference_not_toward_oop(self, policy):
        """Risk: Brand-vs-generic cost difference counts toward OOP → incentive
        to request brand eliminated."""
        assert policy.pharmacy.mandatory_generic.cost_difference_counts_toward_oop is False

    def test_mail_order_discount_ratio(self, policy):
        """Risk: Mail order 90-day cost >= 3x retail 30-day → no incentive to use
        mail order, undermining cost control."""
        for tier in policy.pharmacy.tiers:
            if tier.mail_90day_copay and tier.retail_30day_copay:
                assert tier.mail_90day_copay < tier.retail_30day_copay * 3, (
                    f"Tier {tier.tier}: mail 90-day ({tier.mail_90day_copay}) should be "
                    f"less than 3x retail 30-day ({tier.retail_30day_copay * 3})"
                )
