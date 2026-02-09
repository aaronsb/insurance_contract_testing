"""Benefit determination tests.

Risk category: COVERAGE DENIAL / INCORRECT ADJUDICATION
If these fail, claims are approved when they should be denied, or denied when they
should be approved. Either direction causes harm.
"""

from decimal import Decimal

from policy.models import DentalClass, Gender, NetworkStatus


# ---------------------------------------------------------------------------
# Preventive care — the reclassification trap
# ---------------------------------------------------------------------------

class TestPreventiveCare:

    def test_annual_cleanings_count(self, policy):
        """Risk: System allows 3 cleanings → plan overpays. System allows 1 → member
        loses entitled benefit."""
        cleaning = next(
            s for s in policy.preventive_care.services if s.name == "dental_cleaning"
        )
        assert cleaning.frequency_per_plan_year == 2

    def test_mammogram_gender_restriction(self, policy):
        """Risk: Mammogram offered to all genders → unnecessary utilization and cost.
        Or restricted incorrectly → eligible members denied screening."""
        mammo = next(
            s for s in policy.preventive_care.services if s.name == "screening_mammogram"
        )
        assert mammo.gender == Gender.FEMALE
        assert mammo.age_min == 40

    def test_colonoscopy_age_threshold(self, policy):
        """Risk: Wrong age threshold → members under 45 not flagged for screening,
        or system denies eligible 45+ members."""
        colon = next(
            s for s in policy.preventive_care.services if s.name == "screening_colonoscopy"
        )
        assert colon.age_min == 45

    def test_preventive_requires_in_network(self, policy):
        """Risk: OON preventive billed at $0 → plan overpays. Should apply
        deductible + 40% coinsurance for OON preventive."""
        for svc in policy.preventive_care.services:
            assert svc.network_requirement == NetworkStatus.IN_NETWORK

    def test_split_billing_allowed(self, policy):
        """Risk: Entire visit reclassified as diagnostic when only a portion is →
        member loses $0 preventive benefit entirely."""
        assert policy.preventive_care.split_billing_allowed is True

    def test_colonoscopy_reclassification_rule_exists(self, policy):
        """Risk: No reclassification rule → polyp removal billed at $0 (plan overpays)
        or entire colonoscopy billed as diagnostic (member overcharged)."""
        triggers = [r.trigger for r in policy.preventive_care.reclassification_rules]
        assert "polyp_removal_during_screening_colonoscopy" in triggers

    def test_reclassified_diagnostic_portion_has_cost_share(self, policy):
        """Risk: Diagnostic portion at $0 → plan pays for procedures that should
        have member cost sharing."""
        rule = next(
            r for r in policy.preventive_care.reclassification_rules
            if r.trigger == "polyp_removal_during_screening_colonoscopy"
        )
        assert rule.preventive_portion_cost == Decimal("0")
        assert rule.diagnostic_portion.subject_to_deductible is True
        assert rule.diagnostic_portion.coinsurance == Decimal("0.20")


# ---------------------------------------------------------------------------
# Observation vs. inpatient
# ---------------------------------------------------------------------------

class TestObservationStatus:

    def test_observation_uses_outpatient_benefits(self, policy):
        """Risk: Observation status processed as inpatient → member gets lower cost
        sharing than contracted; plan overpays."""
        assert policy.inpatient.observation_status.uses_outpatient_benefits is True

    def test_er_copay_not_waived_for_observation(self, policy):
        """Risk: ER copay waived for observation stay → member avoids $350 copay
        that should apply. Copay waiver is ONLY for true inpatient admission."""
        assert policy.inpatient.observation_status.er_copay_waived is False


# ---------------------------------------------------------------------------
# Visit limits and shared pools
# ---------------------------------------------------------------------------

class TestVisitLimits:

    def test_pt_limit(self, policy):
        pt = next(v for v in policy.rehab.visit_limits if v.service == "physical_therapy")
        assert pt.max_visits == 30

    def test_pt_ot_shared_pool(self, policy):
        """Risk: PT and OT tracked independently → member gets 30 PT + 30 OT = 60 total
        when contract allows 60 combined. Plan overpays."""
        pt = next(v for v in policy.rehab.visit_limits if v.service == "physical_therapy")
        ot = next(v for v in policy.rehab.visit_limits if v.service == "occupational_therapy")
        assert "occupational_therapy" in pt.shared_with
        assert "physical_therapy" in ot.shared_with

    def test_speech_therapy_separate_limit(self, policy):
        """Risk: Speech therapy incorrectly shares pool with PT/OT → member loses
        entitled speech visits when PT/OT pool is exhausted."""
        st = next(v for v in policy.rehab.visit_limits if v.service == "speech_therapy")
        assert st.max_visits == 30
        assert st.shared_with == []

    def test_chiropractic_limit(self, policy):
        chiro = next(v for v in policy.rehab.visit_limits if v.service == "chiropractic")
        assert chiro.max_visits == 20

    def test_aba_exempt_from_visit_limits(self, policy):
        """Risk: ABA subject to visit limits → violates state mandates for autism
        coverage. Regulatory exposure."""
        assert policy.rehab.aba_exempt_from_limits is True


# ---------------------------------------------------------------------------
# Dental benefit determination
# ---------------------------------------------------------------------------

class TestDentalBenefits:

    def test_preventive_no_deductible(self, policy):
        """Risk: Deductible applied to preventive dental → member charged for
        cleanings/exams that should be at 100%."""
        preventive = [
            s for s in policy.dental.services
            if s.dental_class == DentalClass.PREVENTIVE
        ]
        for svc in preventive:
            assert svc.subject_to_deductible is False
            assert svc.coverage_pct == Decimal("1.0")

    def test_basic_coverage_at_80pct(self, policy):
        basic = [
            s for s in policy.dental.services
            if s.dental_class == DentalClass.BASIC
        ]
        for svc in basic:
            assert svc.coverage_pct == Decimal("0.80")
            assert svc.subject_to_deductible is True

    def test_major_coverage_at_50pct(self, policy):
        major = [
            s for s in policy.dental.services
            if s.dental_class == DentalClass.MAJOR
        ]
        for svc in major:
            assert svc.coverage_pct == Decimal("0.50")
            assert svc.subject_to_deductible is True

    def test_annual_max(self, policy):
        """Risk: Wrong annual max → plan overpays beyond $2500 or prematurely
        stops coverage before $2500."""
        assert policy.dental.annual_max_per_member == Decimal("2500")

    def test_missing_tooth_clause_enabled(self, policy):
        """Risk: Clause disabled → plan pays for replacement of teeth missing before
        effective date. Significant cost exposure."""
        assert policy.dental.missing_tooth_clause.enabled is True

    def test_missing_tooth_exception_post_effective(self, policy):
        """Risk: Exception not honored → member denied replacement for tooth extracted
        AFTER effective date. Incorrect denial."""
        assert policy.dental.missing_tooth_clause.exception_extracted_after_effective is True

    def test_missing_tooth_creditable_coverage_exception(self, policy):
        """Risk: 12-month creditable coverage exception not applied → member with
        prior continuous coverage incorrectly denied."""
        assert policy.dental.missing_tooth_clause.exception_prior_creditable_months == 12

    def test_orthodontia_adult_excluded(self, policy):
        """Risk: Adult ortho covered → significant uncontracted expense."""
        assert policy.dental.orthodontia.adult_covered is False

    def test_orthodontia_lifetime_max_separate(self, policy):
        """Risk: Ortho and dental share annual max → $2000 ortho lifetime consumed
        from $2500 dental annual, leaving only $500 for dental."""
        # Ortho has lifetime max; dental has annual max — they're separate pools
        assert policy.dental.orthodontia.lifetime_max == Decimal("2000")
        assert policy.dental.annual_max_per_member == Decimal("2500")


# ---------------------------------------------------------------------------
# Dental waiting periods
# ---------------------------------------------------------------------------

class TestDentalWaitingPeriods:

    def test_preventive_no_waiting(self, policy):
        """Risk: Waiting period on preventive → new member can't get cleanings for
        6 months. Incorrect denial."""
        wp = next(
            w for w in policy.dental.waiting_periods
            if w.dental_class == DentalClass.PREVENTIVE
        )
        assert wp.months == 0

    def test_basic_6_month_waiting(self, policy):
        wp = next(
            w for w in policy.dental.waiting_periods
            if w.dental_class == DentalClass.BASIC
        )
        assert wp.months == 6

    def test_major_12_month_waiting(self, policy):
        wp = next(
            w for w in policy.dental.waiting_periods
            if w.dental_class == DentalClass.MAJOR
        )
        assert wp.months == 12


# ---------------------------------------------------------------------------
# Step therapy
# ---------------------------------------------------------------------------

class TestStepTherapy:

    def test_ppi_requires_omeprazole_first(self, policy):
        """Risk: Step therapy not enforced → non-preferred PPI dispensed without
        trying generic → unnecessary cost."""
        ppi = next(
            s for s in policy.pharmacy.step_therapy
            if s.drug_class == "proton_pump_inhibitors"
        )
        assert "omeprazole" in ppi.required_first_try

    def test_all_step_therapy_has_override_criteria(self, policy):
        """Risk: No override path → member stuck on ineffective drug with no escape.
        Every step therapy rule MUST have override criteria."""
        for rule in policy.pharmacy.step_therapy:
            assert len(rule.override_criteria) > 0, (
                f"{rule.drug_class}: no override criteria defined"
            )

    def test_override_criteria_include_adverse_reaction(self, policy):
        """Risk: Adverse reaction not an override → member forced to continue
        medication causing harm."""
        for rule in policy.pharmacy.step_therapy:
            assert "adverse_reaction" in rule.override_criteria, (
                f"{rule.drug_class}: missing adverse_reaction override"
            )


# ---------------------------------------------------------------------------
# Maintenance medication rules
# ---------------------------------------------------------------------------

class TestMaintenanceMeds:

    def test_max_initial_retail_fills(self, policy):
        """Risk: Wrong fill count → penalty applied on 2nd fill (too early) or
        4th fill (too late, cost leakage)."""
        assert policy.pharmacy.maintenance_med_rule.max_initial_retail_fills == 2

    def test_required_channels_exist(self, policy):
        channels = policy.pharmacy.maintenance_med_rule.required_channels
        assert "90day_retail" in channels
        assert "mail_order" in channels
