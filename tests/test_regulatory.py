"""Regulatory compliance tests.

Risk category: LEGAL / AUDIT EXPOSURE
If these fail, the plan violates federal or state law. Consequences include
fines, lawsuits, regulatory action, and loss of certification.
"""

from decimal import Decimal


# ---------------------------------------------------------------------------
# Mental Health Parity (MHPAEA)
# ---------------------------------------------------------------------------

class TestMentalHealthParity:
    """MHPAEA requires MH/SUD benefits at parity with medical/surgical.
    Base policy: MHPAEA (29 USC § 1185a)."""

    def test_parity_flag(self, policy):
        assert policy.mental_health.parity_compliant is True

    def test_no_separate_visit_limits(self, policy):
        """Risk: Separate MH visit limits → MHPAEA violation. Federal enforcement
        action, plan disqualification."""
        assert policy.mental_health.separate_visit_limits is False

    def test_no_separate_day_limits(self, policy):
        assert policy.mental_health.separate_day_limits is False

    def test_no_higher_cost_share(self, policy):
        """Risk: MH copay > medical copay → quantitative treatment limitation
        violation under MHPAEA."""
        assert policy.mental_health.higher_cost_share_than_medical is False

    def test_mh_copay_not_exceeding_medical_pcp(self, policy):
        """Risk: Therapy copay exceeds PCP visit copay → potential parity violation
        on financial requirements."""
        pcp = next(s for s in policy.primary_care if s.name == "pcp_office_visit")
        therapy = policy.mental_health.outpatient_individual
        assert therapy.in_network.copay <= pcp.in_network.copay

    def test_mh_inpatient_matches_medical_inpatient(self, policy):
        """Risk: MH inpatient copay/coinsurance exceeds medical inpatient →
        quantitative treatment limitation violation."""
        med = policy.inpatient.in_network
        mh = policy.mental_health.inpatient
        assert mh.facility_copay <= med.facility_copay
        assert mh.facility_coinsurance <= med.facility_coinsurance

    def test_base_policy_linked(self, policy):
        """Risk: No regulatory traceability → audit finding for missing
        compliance documentation."""
        assert "MHPAEA" in policy.mental_health.base_policies


# ---------------------------------------------------------------------------
# No Surprises Act (NSA)
# ---------------------------------------------------------------------------

class TestNoSurprisesAct:
    """NSA protects members from surprise billing in emergency and certain
    non-emergency scenarios. Base policy: NSA (Public Law 116-260)."""

    def test_emergency_oon_at_in_network_rates(self, policy):
        """Risk: OON emergency billed at OON rates → NSA violation, member
        balance-billed illegally."""
        assert policy.emergency.er.oon_covered_at_in_network_rates is True

    def test_prudent_layperson_standard(self, policy):
        """Risk: Prudent layperson not applied → plan denies legitimate ER claims
        based on retrospective diagnosis."""
        assert policy.emergency.er.prudent_layperson_standard is True

    def test_post_stabilization_oon_applies(self, policy):
        """Risk: Post-stabilization care at in-network rates indefinitely →
        plan overpays. NSA only covers initial emergency + stabilization."""
        assert policy.emergency.er.post_stabilization_oon_applies is True

    def test_base_policy_linked(self, policy):
        assert "NSA" in policy.emergency.base_policies


# ---------------------------------------------------------------------------
# Newborns' and Mothers' Health Protection Act (NMHPA)
# ---------------------------------------------------------------------------

class TestNewbornsAct:
    """NMHPA mandates minimum maternity hospital stays."""

    def test_vaginal_delivery_minimum_stay(self, policy):
        """Risk: Stay < 48h → NMHPA violation. Cannot require early discharge
        for vaginal delivery."""
        assert policy.inpatient.min_stay_vaginal_hours >= 48

    def test_cesarean_minimum_stay(self, policy):
        """Risk: Stay < 96h → NMHPA violation for cesarean delivery."""
        assert policy.inpatient.min_stay_cesarean_hours >= 96

    def test_base_policy_linked(self, policy):
        assert "NMHPA" in policy.inpatient.base_policies


# ---------------------------------------------------------------------------
# COBRA
# ---------------------------------------------------------------------------

class TestCOBRA:
    """COBRA continuation coverage requirements."""

    def test_employee_months(self, policy):
        """Risk: < 18 months offered → COBRA violation. Member loses coverage
        prematurely after qualifying event."""
        assert policy.special_provisions.cobra_months_employee >= 18

    def test_dependent_months(self, policy):
        """Risk: < 36 months for qualifying dependents → COBRA violation."""
        assert policy.special_provisions.cobra_months_dependent >= 36

    def test_premium_percentage(self, policy):
        """Risk: Premium > 102% → member overcharged. Premium < 102% → plan
        subsidizing COBRA beyond required amount."""
        assert policy.special_provisions.cobra_premium_pct == Decimal("1.02")


# ---------------------------------------------------------------------------
# ERISA — Claims & Appeals
# ---------------------------------------------------------------------------

class TestClaimsAndAppeals:
    """ERISA requires specific claims/appeals timelines and member rights."""

    def test_oon_filing_deadline(self, policy):
        """Risk: Deadline shorter than 365 days → member with late-submitted
        OON claim incorrectly denied."""
        assert policy.claims_and_appeals.oon_filing_deadline_days >= 365

    def test_internal_appeal_filing_window(self, policy):
        """Risk: Window < 180 days → ERISA violation on appeal rights."""
        internal = next(
            a for a in policy.claims_and_appeals.appeals_levels
            if a.name == "internal_appeal"
        )
        assert internal.filing_deadline_days >= 180

    def test_internal_appeal_decision_timeline(self, policy):
        """Risk: Decision > 30 days for pre-service → ERISA violation."""
        internal = next(
            a for a in policy.claims_and_appeals.appeals_levels
            if a.name == "internal_appeal"
        )
        assert internal.decision_deadline_days <= 30

    def test_expedited_review_available(self, policy):
        """Risk: No expedited review → ERISA violation for urgent/concurrent
        care situations."""
        internal = next(
            a for a in policy.claims_and_appeals.appeals_levels
            if a.name == "internal_appeal"
        )
        assert internal.expedited_deadline_hours is not None
        assert internal.expedited_deadline_hours <= 72

    def test_external_review_available(self, policy):
        """Risk: No external review → ERISA/ACA violation. Member has no
        independent review path."""
        external_names = [a.name for a in policy.claims_and_appeals.appeals_levels]
        assert "external_review" in external_names

    def test_member_right_to_clinical_criteria(self, policy):
        """Risk: Criteria not disclosed → member cannot prepare meaningful
        appeal. ERISA procedural violation."""
        assert "request_clinical_criteria" in policy.claims_and_appeals.member_rights

    def test_member_right_to_representative(self, policy):
        """Risk: No authorized representative → disabled or incapacitated
        member cannot exercise appeal rights."""
        assert "appoint_authorized_representative" in policy.claims_and_appeals.member_rights


# ---------------------------------------------------------------------------
# Foundational policy traceability
# ---------------------------------------------------------------------------

class TestRegulatoryTraceability:
    """Every compliance-sensitive benefit should trace back to its authorizing
    statute. Without traceability, auditors cannot verify compliance."""

    def test_all_base_policies_have_references(self, policy):
        """Risk: Base policy with no citation → unverifiable compliance claim."""
        for bp in policy.base_policies:
            assert len(bp.references) > 0, (
                f"Base policy '{bp.id}' has no regulatory references"
            )

    def test_all_base_policies_have_statute(self, policy):
        for bp in policy.base_policies:
            for ref in bp.references:
                assert ref.statute, (
                    f"Base policy '{bp.id}' reference missing statute name"
                )

    def test_required_base_policies_present(self, policy):
        """Risk: Missing foundational policy → entire compliance domain untested."""
        ids = {bp.id for bp in policy.base_policies}
        required = {"ACA", "MHPAEA", "NSA", "NMHPA", "COBRA", "ERISA"}
        missing = required - ids
        assert not missing, f"Missing base policies: {missing}"
