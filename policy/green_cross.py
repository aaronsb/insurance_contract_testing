"""Green Cross PPO Select — contract data as a Policy instance.

Every value here traces back to contracts/green-cross-policy.md.
Tests assert against this data to verify platform compliance.
"""

from datetime import date
from decimal import Decimal

from policy.models import (
    AccumulatorAdjustment,
    AmbulanceBenefit,
    AppealsLevel,
    BasePolicy,
    ClaimsAndAppeals,
    COBRule,
    CorrespondenceRules,
    CostShare,
    Deductibles,
    DeductibleTier,
    DeductibleType,
    DentalBenefits,
    DentalClass,
    DentalService,
    DentalWaitingPeriod,
    EmergencyCare,
    ERBenefit,
    FormularyTransitionRule,
    Gender,
    InpatientCare,
    InpatientCostShare,
    MaintenanceMedRule,
    MandatoryGenericRule,
    MentalHealthBenefits,
    MissingToothClause,
    NetworkQuirk,
    NetworkStatus,
    ObservationStatus,
    OOPMaxTier,
    Orthodontia,
    OutOfPocketMax,
    PharmacyBenefits,
    PlanType,
    Policy,
    PreventiveCare,
    PreventiveService,
    PreventiveToDiagnosticRule,
    PriorAuthorization,
    PriorAuthPenalty,
    RegulatoryReference,
    RehabBenefits,
    RxTier,
    ServiceBenefit,
    SpecialProvisions,
    StateCorrespondenceRule,
    StepTherapyRule,
    TravelEmergency,
    VisionBenefits,
    VisionHardware,
    VisitLimit,
)


# ---------------------------------------------------------------------------
# Foundational policies (statutes / regulations this plan must comply with)
# ---------------------------------------------------------------------------

_base_policies = [
    BasePolicy(
        id="ACA",
        name="Affordable Care Act",
        description="Preventive care coverage requirements, essential health benefits, OOP max limits",
        references=[
            RegulatoryReference(
                statute="Patient Protection and Affordable Care Act",
                citation="42 USC § 18001 et seq.",
                cfr="45 CFR § 147.130",
                effective_date=date(2010, 3, 23),
            ),
        ],
    ),
    BasePolicy(
        id="MHPAEA",
        name="Mental Health Parity and Addiction Equity Act",
        description="Mental health and substance use benefits must be at parity with medical/surgical",
        references=[
            RegulatoryReference(
                statute="Mental Health Parity and Addiction Equity Act",
                citation="29 USC § 1185a",
                cfr="45 CFR § 146.136",
                effective_date=date(2008, 10, 3),
            ),
        ],
    ),
    BasePolicy(
        id="NSA",
        name="No Surprises Act",
        description="Surprise billing protections for emergency and certain non-emergency services",
        references=[
            RegulatoryReference(
                statute="No Surprises Act",
                citation="Public Law 116-260, Division BB, Title I",
                cfr="45 CFR Part 149",
                effective_date=date(2022, 1, 1),
            ),
        ],
    ),
    BasePolicy(
        id="NMHPA",
        name="Newborns' and Mothers' Health Protection Act",
        description="Minimum hospital stay requirements for childbirth",
        references=[
            RegulatoryReference(
                statute="Newborns' and Mothers' Health Protection Act",
                citation="29 USC § 1185",
                effective_date=date(1998, 1, 1),
            ),
        ],
    ),
    BasePolicy(
        id="COBRA",
        name="Consolidated Omnibus Budget Reconciliation Act",
        description="Continuation of coverage after qualifying events",
        references=[
            RegulatoryReference(
                statute="COBRA",
                citation="29 USC § 1161-1168",
                effective_date=date(1986, 4, 7),
            ),
        ],
    ),
    BasePolicy(
        id="ERISA",
        name="Employee Retirement Income Security Act",
        description="Claims and appeals process requirements",
        references=[
            RegulatoryReference(
                statute="ERISA",
                citation="29 USC § 1001 et seq.",
                cfr="29 CFR § 2560.503-1",
                effective_date=date(1974, 9, 2),
            ),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Policy instance
# ---------------------------------------------------------------------------

green_cross_policy = Policy(
    plan_name="Green Cross PPO Select",
    policy_number="GCX-2025-PPO-4417",
    group_number="BNO-00382",
    effective_date=date(2025, 1, 1),
    plan_year_start=date(2025, 1, 1),
    plan_year_end=date(2025, 12, 31),
    plan_type=PlanType.PPO,
    sbc_version="2025-R3",
    base_policies=_base_policies,

    # ------------------------------------------------------------------
    # Deductibles  (§1)
    # ------------------------------------------------------------------
    deductibles=Deductibles(
        in_network=DeductibleTier(
            individual=Decimal("1500"),
            family=Decimal("3000"),
            type=DeductibleType.EMBEDDED,
        ),
        out_of_network=DeductibleTier(
            individual=Decimal("3000"),
            family=Decimal("6000"),
            type=DeductibleType.NON_EMBEDDED,
        ),
        cross_accumulation=False,
        excluded_services=[
            "preventive_care_in_network",
            "pediatric_well_child_in_network",
            "telehealth_pcp_in_network",
            "tier1_preventive_rx",
        ],
    ),

    # ------------------------------------------------------------------
    # Out-of-pocket maximum  (§2)
    # ------------------------------------------------------------------
    oop_max=OutOfPocketMax(
        in_network=OOPMaxTier(individual=Decimal("4500"), family=Decimal("9000")),
        out_of_network=OOPMaxTier(individual=Decimal("9000"), family=Decimal("18000")),
        includes=["deductible", "copayments", "coinsurance"],
        excludes=[
            "premiums",
            "balance_billed_charges",
            "non_covered_services",
            "prior_auth_penalties",
        ],
        accumulator_adjustment=AccumulatorAdjustment(
            enabled=True,
            excluded_from_deductible=True,
            excluded_from_oop=True,
            applies_to_tiers=[3, 4],
        ),
    ),

    # ------------------------------------------------------------------
    # Preventive care  (§4)
    # ------------------------------------------------------------------
    preventive_care=PreventiveCare(
        base_policies=["ACA"],
        services=[
            PreventiveService(
                name="annual_physical",
                frequency_per_plan_year=1,
                frequency_description="1 per plan year",
                age_min=18,
                notes="Must use PCP or designated wellness provider",
            ),
            PreventiveService(
                name="well_woman_exam",
                frequency_per_plan_year=1,
                frequency_description="1 per plan year",
                age_min=18,
                gender=Gender.FEMALE,
            ),
            PreventiveService(
                name="pediatric_well_child",
                frequency_description="Per AAP Bright Futures schedule",
                age_max=17,
            ),
            PreventiveService(
                name="routine_immunizations",
                frequency_description="Per CDC schedule",
            ),
            PreventiveService(
                name="screening_colonoscopy",
                frequency_description="1 per 10 years",
                age_min=45,
                notes="Diagnostic colonoscopy subject to deductible + coinsurance",
            ),
            PreventiveService(
                name="screening_mammogram",
                frequency_per_plan_year=1,
                frequency_description="1 per plan year",
                age_min=40,
                gender=Gender.FEMALE,
            ),
            PreventiveService(
                name="dental_cleaning",
                frequency_per_plan_year=2,
                frequency_description="2 per plan year",
                notes="Prophylaxis only; periodontal maintenance is NOT preventive",
            ),
            PreventiveService(
                name="dental_exam",
                frequency_per_plan_year=2,
                frequency_description="2 per plan year",
                notes="Includes bitewing X-rays 1x/year",
            ),
            PreventiveService(
                name="routine_vision_exam",
                frequency_per_plan_year=1,
                frequency_description="1 per plan year",
            ),
            PreventiveService(
                name="psa_screening",
                frequency_per_plan_year=1,
                frequency_description="1 per plan year",
                age_min=55,
                gender=Gender.MALE,
            ),
            PreventiveService(
                name="cervical_cancer_screening",
                frequency_description="Per USPSTF schedule",
                age_min=21,
                age_max=65,
                gender=Gender.FEMALE,
            ),
        ],
        reclassification_rules=[
            PreventiveToDiagnosticRule(
                trigger="polyp_removal_during_screening_colonoscopy",
                preventive_portion_cost=Decimal("0"),
                diagnostic_portion=CostShare(
                    coinsurance=Decimal("0.20"),
                    subject_to_deductible=True,
                ),
            ),
            PreventiveToDiagnosticRule(
                trigger="new_diagnosis_during_annual_physical",
                preventive_portion_cost=Decimal("0"),
                diagnostic_portion=CostShare(
                    copay=Decimal("30"),
                    subject_to_deductible=False,
                ),
            ),
        ],
        split_billing_allowed=True,
    ),

    # ------------------------------------------------------------------
    # Primary care  (§5.1)
    # ------------------------------------------------------------------
    primary_care=[
        ServiceBenefit(
            name="pcp_office_visit",
            in_network=CostShare(copay=Decimal("30"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        ServiceBenefit(
            name="telehealth_pcp",
            in_network=CostShare(copay=Decimal("10"), subject_to_deductible=False),
            out_of_network=CostShare(covered=False),
        ),
        ServiceBenefit(
            name="after_hours_pcp",
            in_network=CostShare(copay=Decimal("45"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
    ],

    # ------------------------------------------------------------------
    # Specialist care  (§5.2)
    # ------------------------------------------------------------------
    specialist_care=[
        ServiceBenefit(
            name="specialist_office_visit",
            in_network=CostShare(copay=Decimal("60"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        ServiceBenefit(
            name="telehealth_specialist",
            in_network=CostShare(copay=Decimal("45"), subject_to_deductible=False),
            out_of_network=CostShare(covered=False),
        ),
    ],

    # ------------------------------------------------------------------
    # Emergency care  (§6)
    # ------------------------------------------------------------------
    emergency=EmergencyCare(
        base_policies=["NSA"],
        er=ERBenefit(
            facility_copay=Decimal("350"),
            facility_coinsurance=Decimal("0.20"),
            physician_coinsurance=Decimal("0.20"),
            subject_to_deductible=True,
            copay_waived_if_admitted=True,
            admission_window_hours=24,
            prudent_layperson_standard=True,
            oon_covered_at_in_network_rates=True,
            post_stabilization_oon_applies=True,
        ),
        urgent_care=ServiceBenefit(
            name="urgent_care",
            in_network=CostShare(copay=Decimal("75"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        ambulance=AmbulanceBenefit(
            ground_copay=Decimal("300"),
            ground_coinsurance=Decimal("0.20"),
            air_copay=Decimal("500"),
            air_coinsurance=Decimal("0.20"),
            subject_to_deductible=True,
            non_emergency_prior_auth=True,
        ),
    ),

    # ------------------------------------------------------------------
    # Inpatient care  (§7)
    # ------------------------------------------------------------------
    inpatient=InpatientCare(
        base_policies=["NMHPA"],
        in_network=InpatientCostShare(
            facility_copay=Decimal("500"),
            facility_coinsurance=Decimal("0.20"),
            physician_coinsurance=Decimal("0.20"),
        ),
        out_of_network=InpatientCostShare(
            facility_copay=Decimal("0"),
            facility_coinsurance=Decimal("0.40"),
            physician_coinsurance=Decimal("0.40"),
        ),
        prior_auth_required=True,
        prior_auth_penalty=Decimal("500"),
        prior_auth_penalty_counts_toward_oop=False,
        observation_status=ObservationStatus(
            uses_outpatient_benefits=True,
            er_copay_waived=False,
            notes="Observation status does NOT trigger inpatient benefits; ER copay NOT waived",
        ),
        maternity_in_network=InpatientCostShare(
            facility_copay=Decimal("500"),
            facility_coinsurance=Decimal("0.20"),
            physician_coinsurance=Decimal("0.20"),
        ),
        min_stay_vaginal_hours=48,
        min_stay_cesarean_hours=96,
        snf_in_network_days_per_year=60,
        snf_out_of_network_days_per_year=30,
    ),

    # ------------------------------------------------------------------
    # Mental health  (§8)
    # ------------------------------------------------------------------
    mental_health=MentalHealthBenefits(
        base_policies=["MHPAEA"],
        outpatient_individual=ServiceBenefit(
            name="individual_therapy",
            in_network=CostShare(copay=Decimal("30"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        outpatient_group=ServiceBenefit(
            name="group_therapy",
            in_network=CostShare(copay=Decimal("15"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        psychiatric_med_mgmt=ServiceBenefit(
            name="psychiatric_med_mgmt",
            in_network=CostShare(copay=Decimal("60"), subject_to_deductible=False),
            out_of_network=CostShare(coinsurance=Decimal("0.40"), subject_to_deductible=True),
        ),
        telehealth=ServiceBenefit(
            name="telehealth_therapy",
            in_network=CostShare(copay=Decimal("10"), subject_to_deductible=False),
            out_of_network=CostShare(covered=False),
        ),
        inpatient=InpatientCostShare(
            facility_copay=Decimal("500"),
            facility_coinsurance=Decimal("0.20"),
            physician_coinsurance=Decimal("0.20"),
        ),
        parity_compliant=True,
        separate_visit_limits=False,
        separate_day_limits=False,
        higher_cost_share_than_medical=False,
    ),

    # ------------------------------------------------------------------
    # Pharmacy  (§9)
    # ------------------------------------------------------------------
    pharmacy=PharmacyBenefits(
        tiers=[
            RxTier(tier=1, name="Preferred generic",
                   retail_30day_copay=Decimal("10"), mail_90day_copay=Decimal("25")),
            RxTier(tier=2, name="Non-preferred generic",
                   retail_30day_copay=Decimal("30"), mail_90day_copay=Decimal("75")),
            RxTier(tier=3, name="Preferred brand",
                   retail_30day_copay=Decimal("60"), mail_90day_copay=Decimal("150")),
            RxTier(tier=4, name="Non-preferred brand",
                   retail_30day_copay=Decimal("100"), mail_90day_copay=Decimal("250")),
            RxTier(tier=5, name="Specialty",
                   retail_30day_coinsurance=Decimal("0.30"),
                   retail_30day_max_per_fill=Decimal("350"),
                   mail_90day_available=False),
        ],
        step_therapy=[
            StepTherapyRule(
                drug_class="proton_pump_inhibitors",
                required_first_try=["omeprazole"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
            StepTherapyRule(
                drug_class="statins",
                required_first_try=["atorvastatin", "rosuvastatin"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
            StepTherapyRule(
                drug_class="ssri_snri",
                required_first_try=["sertraline", "escitalopram"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
            StepTherapyRule(
                drug_class="tnf_inhibitors",
                required_first_try=["adalimumab_biosimilar"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
            StepTherapyRule(
                drug_class="glp1_agonists",
                required_first_try=["metformin"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
            StepTherapyRule(
                drug_class="adhd_stimulants",
                required_first_try=["methylphenidate_generic"],
                override_criteria=["adverse_reaction", "contraindication", "therapeutic_failure"],
            ),
        ],
        maintenance_med_rule=MaintenanceMedRule(
            max_initial_retail_fills=2,
            required_channels=["90day_retail", "mail_order"],
            penalty_description="Third+ 30-day retail fill covered at 50% of copay; excess does not count toward OOP",
            penalty_counts_toward_oop=False,
        ),
        mandatory_generic=MandatoryGenericRule(
            enabled=True,
            member_pays_brand_copay=True,
            member_pays_cost_difference=True,
            cost_difference_counts_toward_oop=False,
            daw_exception_allowed=True,
        ),
        formulary_transition=FormularyTransitionRule(
            transition_supply_days=90,
            at_prior_tier_cost=True,
        ),
        prior_auth_categories=[
            "tier5_specialty",
            "glp1_weight_loss",
            "biologics_biosimilars",
            "growth_hormone",
            "opioids_above_90mme",
            "compounds_above_300",
        ],
    ),

    # ------------------------------------------------------------------
    # Dental  (§11)
    # ------------------------------------------------------------------
    dental=DentalBenefits(
        deductible_individual=Decimal("75"),
        deductible_family=Decimal("225"),
        annual_max_per_member=Decimal("2500"),
        services=[
            DentalService(name="prophylaxis", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="2 per plan year"),
            DentalService(name="periodic_oral_exam", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="2 per plan year"),
            DentalService(name="bitewing_xrays", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="1 set per plan year"),
            DentalService(name="full_mouth_xrays", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="1 set per 3 plan years"),
            DentalService(name="fluoride_treatment", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="2 per plan year, age 18 and under"),
            DentalService(name="sealants", dental_class=DentalClass.PREVENTIVE,
                          coverage_pct=Decimal("1.0"), subject_to_deductible=False,
                          frequency="per permanent molar, once per tooth per lifetime",
                          notes="Age 6-16"),
            DentalService(name="fillings", dental_class=DentalClass.BASIC,
                          coverage_pct=Decimal("0.80"), subject_to_deductible=True,
                          notes="Posterior composite limited to amalgam allowance"),
            DentalService(name="simple_extractions", dental_class=DentalClass.BASIC,
                          coverage_pct=Decimal("0.80"), subject_to_deductible=True),
            DentalService(name="root_canal_anterior", dental_class=DentalClass.BASIC,
                          coverage_pct=Decimal("0.80"), subject_to_deductible=True),
            DentalService(name="root_canal_molar", dental_class=DentalClass.BASIC,
                          coverage_pct=Decimal("0.80"), subject_to_deductible=True),
            DentalService(name="perio_srp", dental_class=DentalClass.BASIC,
                          coverage_pct=Decimal("0.80"), subject_to_deductible=True,
                          frequency="1 per quadrant per 2 plan years"),
            DentalService(name="crowns", dental_class=DentalClass.MAJOR,
                          coverage_pct=Decimal("0.50"), subject_to_deductible=True,
                          frequency="1 per tooth per 5 plan years"),
            DentalService(name="bridges", dental_class=DentalClass.MAJOR,
                          coverage_pct=Decimal("0.50"), subject_to_deductible=True),
            DentalService(name="dentures", dental_class=DentalClass.MAJOR,
                          coverage_pct=Decimal("0.50"), subject_to_deductible=True,
                          frequency="1 per arch per 5 plan years"),
            DentalService(name="implants", dental_class=DentalClass.MAJOR,
                          coverage_pct=Decimal("0.50"), subject_to_deductible=True,
                          notes="Max $2,000 per implant"),
            DentalService(name="surgical_extractions", dental_class=DentalClass.MAJOR,
                          coverage_pct=Decimal("0.50"), subject_to_deductible=True),
        ],
        waiting_periods=[
            DentalWaitingPeriod(dental_class=DentalClass.PREVENTIVE, months=0),
            DentalWaitingPeriod(dental_class=DentalClass.BASIC, months=6),
            DentalWaitingPeriod(dental_class=DentalClass.MAJOR, months=12),
        ],
        missing_tooth_clause=MissingToothClause(
            enabled=True,
            exception_extracted_after_effective=True,
            exception_prior_creditable_months=12,
        ),
        orthodontia=Orthodontia(
            coverage_pct=Decimal("0.50"),
            lifetime_max=Decimal("2000"),
            age_limit=19,
            adult_covered=False,
            waiting_period_months=12,
            subject_to_deductible=True,
        ),
    ),

    # ------------------------------------------------------------------
    # Vision  (§12)
    # ------------------------------------------------------------------
    vision=VisionBenefits(
        exam_copay=Decimal("0"),
        exam_frequency_per_year=1,
        hardware=VisionHardware(
            frame_allowance=Decimal("175"),
            frame_frequency="1 per plan year",
            lens_copay=Decimal("25"),
            contact_allowance=Decimal("175"),
            contact_in_lieu_of_glasses=True,
        ),
        oon_exam_reimbursement=Decimal("50"),
        oon_frame_reimbursement=Decimal("75"),
    ),

    # ------------------------------------------------------------------
    # Rehab  (§13)
    # ------------------------------------------------------------------
    rehab=RehabBenefits(
        copay=Decimal("45"),
        subject_to_deductible=False,
        visit_limits=[
            VisitLimit(service="physical_therapy", max_visits=30, shared_with=["occupational_therapy"],
                       notes="PT and OT share combined 60-visit limit"),
            VisitLimit(service="occupational_therapy", max_visits=30, shared_with=["physical_therapy"],
                       notes="PT and OT share combined 60-visit limit"),
            VisitLimit(service="speech_therapy", max_visits=30),
            VisitLimit(service="chiropractic", max_visits=20),
            VisitLimit(service="cardiac_rehab", max_visits=36),
            VisitLimit(service="pulmonary_rehab", max_visits=36),
        ],
        aba_exempt_from_limits=True,
        aba_prior_auth_required=True,
        extended_limit_conditions=["stroke", "traumatic_brain_injury"],
    ),

    # ------------------------------------------------------------------
    # Prior authorization  (§10)
    # ------------------------------------------------------------------
    prior_authorization=PriorAuthorization(
        required_services=[
            "non_emergency_inpatient",
            "outpatient_surgery_select",
            "advanced_imaging_mri_ct_pet",
            "dme_above_1000",
            "home_health",
            "genetic_testing",
            "infusion_therapy",
            "transplant",
            "residential_treatment",
            "non_emergency_air_ambulance",
        ],
        penalty=PriorAuthPenalty(
            in_network_member_held_harmless=True,
            out_of_network_benefit_reduction=Decimal("0.25"),
            penalty_counts_toward_oop=False,
        ),
        retrospective_window_hours=48,
    ),

    # ------------------------------------------------------------------
    # Correspondence  (state-specific rules)
    # ------------------------------------------------------------------
    correspondence=CorrespondenceRules(
        default_pronoun_style="they/them",
        state_rules=[
            StateCorrespondenceRule(
                state="CA",
                requires_gender_neutral_language=True,
                surprise_billing_notice_required=True,
                balance_billing_protections=True,
                required_disclosures=["independent_medical_review_rights"],
                language_requirements=["Spanish", "Chinese", "Tagalog", "Vietnamese", "Korean"],
            ),
            StateCorrespondenceRule(
                state="NY",
                requires_gender_neutral_language=True,
                surprise_billing_notice_required=True,
                balance_billing_protections=True,
                required_disclosures=["external_appeal_rights", "utilization_review_agent_info"],
                language_requirements=["Spanish", "Chinese", "Russian", "Bengali", "Haitian_Creole"],
            ),
            StateCorrespondenceRule(
                state="TX",
                requires_gender_neutral_language=False,
                surprise_billing_notice_required=True,
                balance_billing_protections=True,
                required_disclosures=["mediation_rights"],
                language_requirements=["Spanish"],
            ),
            StateCorrespondenceRule(
                state="FL",
                requires_gender_neutral_language=False,
                surprise_billing_notice_required=False,
                balance_billing_protections=False,
                required_disclosures=[],
                language_requirements=["Spanish"],
            ),
            StateCorrespondenceRule(
                state="IL",
                requires_gender_neutral_language=True,
                surprise_billing_notice_required=True,
                balance_billing_protections=True,
                required_disclosures=["network_adequacy_notice"],
                language_requirements=["Spanish", "Polish"],
            ),
            StateCorrespondenceRule(
                state="OR",
                requires_gender_neutral_language=True,
                surprise_billing_notice_required=True,
                balance_billing_protections=True,
                required_disclosures=["non_binary_gender_marker_support"],
                language_requirements=["Spanish", "Vietnamese", "Russian"],
            ),
        ],
        eob_required_fields=[
            "claim_number", "date_of_service", "provider_name",
            "billed_amount", "allowed_amount", "plan_paid",
            "member_responsibility", "deductible_applied",
            "coinsurance_applied", "copay_applied",
            "remaining_deductible", "remaining_oop",
            "appeal_rights_notice",
        ],
        denial_letter_required_fields=[
            "denial_reason", "clinical_criteria_used",
            "appeal_instructions", "appeal_deadline",
            "external_review_rights", "contact_information",
            "member_rights_statement",
        ],
    ),

    # ------------------------------------------------------------------
    # Claims & appeals  (§16)
    # ------------------------------------------------------------------
    claims_and_appeals=ClaimsAndAppeals(
        oon_filing_deadline_days=365,
        appeals_levels=[
            AppealsLevel(
                name="internal_appeal",
                filing_deadline_days=180,
                decision_deadline_days=30,    # pre-service
                expedited_deadline_hours=72,
            ),
            AppealsLevel(
                name="external_review",
                filing_deadline_days=120,     # 4 months from L1 exhaustion
                decision_deadline_days=45,
                expedited_deadline_hours=72,
            ),
        ],
        member_rights=[
            "request_clinical_criteria",
            "submit_additional_documentation",
            "request_expedited_review",
            "appoint_authorized_representative",
        ],
    ),

    # ------------------------------------------------------------------
    # Exclusions  (§14)
    # ------------------------------------------------------------------
    exclusions=[
        "cosmetic_surgery_non_reconstructive",
        "weight_loss_surgery_below_bmi_thresholds",
        "infertility_treatment_beyond_diagnostic",
        "experimental_investigational",
        "services_by_family_member",
        "long_term_custodial_care",
        "otc_medications",
        "adult_hearing_aids",
        "cosmetic_dental_implants",
        "adult_orthodontia",
        "no_legal_obligation_to_pay",
        "workers_compensation_covered",
        "auto_no_fault_covered",
        "non_emergency_outside_us",
        "private_duty_nursing_unapproved",
        "acupuncture_non_chronic_lbp",
    ],

    # ------------------------------------------------------------------
    # Special provisions  (§15)
    # ------------------------------------------------------------------
    special_provisions=SpecialProvisions(
        cob=COBRule(
            dependent_rule="naic_birthday_rule",
            employee_primary_rule="employee_plan_is_primary",
        ),
        travel_emergency=TravelEmergency(
            geographic_scope="worldwide",
            max_trip_days=60,
            cost_share_same_as="in_network_emergency",
            repatriation_max=Decimal("25000"),
            follow_up_requires_transfer=True,
        ),
        cobra_months_employee=18,
        cobra_months_dependent=36,
        cobra_premium_pct=Decimal("1.02"),
        grace_period_days=31,
    ),

    # ------------------------------------------------------------------
    # Network quirks  (Appendix A)
    # ------------------------------------------------------------------
    network_quirks=[
        NetworkQuirk(
            id="lab_work_trap",
            name="Lab Work Trap",
            description="In-network physicians may send lab work to out-of-network labs",
            risk="Member unexpectedly billed at OON rates for routine lab work",
            affected_services=["laboratory"],
        ),
        NetworkQuirk(
            id="anesthesia_oon",
            name="Anesthesia Billing",
            description="Anesthesiologists at in-network facilities may be OON",
            risk="Balance billing for elective procedures with advance OON consent",
            affected_services=["anesthesia", "surgery"],
        ),
        NetworkQuirk(
            id="facility_professional_split",
            name="Facility vs Professional Split",
            description="Hospital outpatient services generate two separate claims",
            risk="Member expects one cost share but receives two",
            affected_services=["outpatient_hospital", "imaging"],
        ),
        NetworkQuirk(
            id="observation_vs_inpatient",
            name="Observation vs Inpatient Status",
            description="Observation status uses outpatient benefits, not inpatient",
            risk="Higher cost sharing than expected; ER copay not waived",
            affected_services=["emergency", "inpatient"],
        ),
        NetworkQuirk(
            id="preventive_diagnostic_reclass",
            name="Preventive-to-Diagnostic Reclassification",
            description="Screening procedures reclassified as diagnostic based on findings",
            risk="$0 preventive visit becomes subject to deductible + coinsurance",
            affected_services=["preventive_care", "colonoscopy"],
        ),
        NetworkQuirk(
            id="telehealth_state_licensure",
            name="Telehealth Originating Site",
            description="Telehealth only covered when member is in provider's licensed state",
            risk="Claim denied when traveling out of state",
            affected_services=["telehealth"],
        ),
        NetworkQuirk(
            id="er_followup_oon",
            name="Emergency Follow-Up at OON Facility",
            description="Post-stabilization follow-up at OON facility uses OON rates",
            risk="Member assumes all care at ER facility is at in-network rates",
            affected_services=["emergency", "follow_up"],
        ),
    ],
)
