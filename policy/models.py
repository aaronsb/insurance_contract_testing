"""Contract models for health insurance policy verification.

Each model maps to a section of the source policy document.
Fields are typed to support deterministic assertion in tests.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NetworkStatus(str, Enum):
    IN_NETWORK = "in_network"
    OUT_OF_NETWORK = "out_of_network"


class DeductibleType(str, Enum):
    EMBEDDED = "embedded"          # individual cap within family
    NON_EMBEDDED = "non_embedded"  # full family must be met first


class PlanType(str, Enum):
    PPO = "PPO"
    HMO = "HMO"
    EPO = "EPO"
    POS = "POS"


class DentalClass(str, Enum):
    PREVENTIVE = "I"
    BASIC = "II"
    MAJOR = "III"


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"
    ALL = "all"


# ---------------------------------------------------------------------------
# Foundational: regulatory authority references
# ---------------------------------------------------------------------------

class RegulatoryReference(BaseModel):
    """Links a benefit or rule to its authorizing statute / regulation."""
    statute: str                          # e.g. "Mental Health Parity and Addiction Equity Act"
    citation: Optional[str] = None        # e.g. "29 USC § 1185a"
    cfr: Optional[str] = None             # e.g. "45 CFR § 146.136"
    effective_date: Optional[date] = None
    notes: Optional[str] = None


class BasePolicy(BaseModel):
    """A foundational / parent policy that the plan inherits from."""
    id: str                               # e.g. "MHPAEA", "ACA-preventive", "NSA-2022"
    name: str
    references: list[RegulatoryReference] = []
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Cost sharing primitives
# ---------------------------------------------------------------------------

class CostShare(BaseModel):
    copay: Optional[Decimal] = None
    coinsurance: Optional[Decimal] = None   # 0.20 = 20%
    subject_to_deductible: bool = True
    covered: bool = True


# ---------------------------------------------------------------------------
# Deductibles
# ---------------------------------------------------------------------------

class DeductibleTier(BaseModel):
    individual: Decimal
    family: Decimal
    type: DeductibleType


class Deductibles(BaseModel):
    in_network: DeductibleTier
    out_of_network: DeductibleTier
    cross_accumulation: bool = False        # False = independent accumulators
    excluded_services: list[str] = []       # not subject to deductible


# ---------------------------------------------------------------------------
# Out-of-pocket maximum
# ---------------------------------------------------------------------------

class OOPMaxTier(BaseModel):
    individual: Decimal
    family: Decimal


class AccumulatorAdjustment(BaseModel):
    """Manufacturer copay assistance accumulation rules."""
    enabled: bool = False
    excluded_from_deductible: bool = False
    excluded_from_oop: bool = False
    applies_to_tiers: list[int] = []        # Rx tiers affected


class OutOfPocketMax(BaseModel):
    in_network: OOPMaxTier
    out_of_network: OOPMaxTier
    includes: list[str] = []
    excludes: list[str] = []
    accumulator_adjustment: AccumulatorAdjustment = AccumulatorAdjustment()


# ---------------------------------------------------------------------------
# Service benefits
# ---------------------------------------------------------------------------

class ServiceBenefit(BaseModel):
    name: str
    in_network: CostShare
    out_of_network: CostShare = CostShare(covered=False)
    prior_auth_required: bool = False


class VisitLimit(BaseModel):
    service: str
    max_visits: int
    period: str = "plan_year"
    shared_with: list[str] = []             # other services sharing this pool
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Preventive care
# ---------------------------------------------------------------------------

class PreventiveService(BaseModel):
    name: str
    frequency_per_plan_year: Optional[int] = None
    frequency_description: str
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Gender = Gender.ALL
    network_requirement: NetworkStatus = NetworkStatus.IN_NETWORK
    notes: Optional[str] = None


class PreventiveToDiagnosticRule(BaseModel):
    trigger: str
    preventive_portion_cost: Decimal = Decimal("0")
    diagnostic_portion: CostShare


class PreventiveCare(BaseModel):
    services: list[PreventiveService]
    reclassification_rules: list[PreventiveToDiagnosticRule] = []
    oon_preventive_cost_share: CostShare = CostShare(
        coinsurance=Decimal("0.40"), subject_to_deductible=True,
    )
    split_billing_allowed: bool = True
    base_policies: list[str] = []           # IDs of foundational policies


# ---------------------------------------------------------------------------
# Emergency care
# ---------------------------------------------------------------------------

class ERBenefit(BaseModel):
    facility_copay: Decimal
    facility_coinsurance: Decimal
    physician_coinsurance: Decimal
    subject_to_deductible: bool = True
    copay_waived_if_admitted: bool = True
    admission_window_hours: int = 24
    prudent_layperson_standard: bool = True
    oon_covered_at_in_network_rates: bool = True
    post_stabilization_oon_applies: bool = True


class AmbulanceBenefit(BaseModel):
    ground_copay: Decimal
    ground_coinsurance: Decimal
    air_copay: Decimal
    air_coinsurance: Decimal
    subject_to_deductible: bool = True
    non_emergency_prior_auth: bool = True


class EmergencyCare(BaseModel):
    er: ERBenefit
    urgent_care: ServiceBenefit
    ambulance: AmbulanceBenefit
    base_policies: list[str] = []


# ---------------------------------------------------------------------------
# Inpatient care
# ---------------------------------------------------------------------------

class InpatientCostShare(BaseModel):
    facility_copay: Decimal
    facility_coinsurance: Decimal
    physician_coinsurance: Decimal
    subject_to_deductible: bool = True


class ObservationStatus(BaseModel):
    uses_outpatient_benefits: bool = True
    er_copay_waived: bool = False
    notes: str = ""


class InpatientCare(BaseModel):
    in_network: InpatientCostShare
    out_of_network: InpatientCostShare
    prior_auth_required: bool = True
    prior_auth_penalty: Decimal = Decimal("500")
    prior_auth_penalty_counts_toward_oop: bool = False
    observation_status: ObservationStatus = ObservationStatus()

    # maternity
    maternity_in_network: InpatientCostShare
    min_stay_vaginal_hours: int = 48
    min_stay_cesarean_hours: int = 96

    # SNF
    snf_in_network_days_per_year: int = 60
    snf_out_of_network_days_per_year: int = 30

    base_policies: list[str] = []


# ---------------------------------------------------------------------------
# Mental health & substance use
# ---------------------------------------------------------------------------

class MentalHealthBenefits(BaseModel):
    outpatient_individual: ServiceBenefit
    outpatient_group: ServiceBenefit
    psychiatric_med_mgmt: ServiceBenefit
    telehealth: ServiceBenefit
    inpatient: InpatientCostShare

    parity_compliant: bool = True
    separate_visit_limits: bool = False
    separate_day_limits: bool = False
    higher_cost_share_than_medical: bool = False

    base_policies: list[str] = []


# ---------------------------------------------------------------------------
# Pharmacy
# ---------------------------------------------------------------------------

class RxTier(BaseModel):
    tier: int
    name: str
    retail_30day_copay: Optional[Decimal] = None
    retail_30day_coinsurance: Optional[Decimal] = None
    retail_30day_max_per_fill: Optional[Decimal] = None
    mail_90day_copay: Optional[Decimal] = None
    mail_90day_coinsurance: Optional[Decimal] = None
    mail_90day_available: bool = True


class StepTherapyRule(BaseModel):
    drug_class: str
    required_first_try: list[str]
    override_criteria: list[str]


class MaintenanceMedRule(BaseModel):
    max_initial_retail_fills: int = 2
    required_channels: list[str]
    penalty_description: str
    penalty_counts_toward_oop: bool = False


class MandatoryGenericRule(BaseModel):
    enabled: bool = True
    member_pays_brand_copay: bool = True
    member_pays_cost_difference: bool = True
    cost_difference_counts_toward_oop: bool = False
    daw_exception_allowed: bool = True


class FormularyTransitionRule(BaseModel):
    transition_supply_days: int = 90
    at_prior_tier_cost: bool = True


class PharmacyBenefits(BaseModel):
    tiers: list[RxTier]
    step_therapy: list[StepTherapyRule]
    maintenance_med_rule: MaintenanceMedRule
    mandatory_generic: MandatoryGenericRule
    formulary_transition: FormularyTransitionRule
    prior_auth_categories: list[str] = []


# ---------------------------------------------------------------------------
# Dental
# ---------------------------------------------------------------------------

class DentalService(BaseModel):
    name: str
    dental_class: DentalClass
    coverage_pct: Decimal
    subject_to_deductible: bool
    frequency: Optional[str] = None
    notes: Optional[str] = None


class DentalWaitingPeriod(BaseModel):
    dental_class: DentalClass
    months: int


class MissingToothClause(BaseModel):
    enabled: bool = True
    exception_extracted_after_effective: bool = True
    exception_prior_creditable_months: int = 12


class Orthodontia(BaseModel):
    coverage_pct: Decimal
    lifetime_max: Decimal
    age_limit: Optional[int] = None
    adult_covered: bool = False
    waiting_period_months: int = 12
    subject_to_deductible: bool = True


class DentalBenefits(BaseModel):
    deductible_individual: Decimal
    deductible_family: Decimal
    annual_max_per_member: Decimal
    services: list[DentalService]
    waiting_periods: list[DentalWaitingPeriod]
    missing_tooth_clause: MissingToothClause
    orthodontia: Orthodontia


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------

class VisionHardware(BaseModel):
    frame_allowance: Decimal
    frame_frequency: str
    lens_copay: Decimal
    contact_allowance: Decimal
    contact_in_lieu_of_glasses: bool = True


class VisionBenefits(BaseModel):
    exam_copay: Decimal
    exam_frequency_per_year: int = 1
    hardware: VisionHardware
    oon_exam_reimbursement: Decimal
    oon_frame_reimbursement: Decimal


# ---------------------------------------------------------------------------
# Rehab / habilitation
# ---------------------------------------------------------------------------

class RehabBenefits(BaseModel):
    copay: Decimal
    subject_to_deductible: bool = False
    visit_limits: list[VisitLimit]
    aba_exempt_from_limits: bool = True
    aba_prior_auth_required: bool = True
    extended_limit_conditions: list[str] = []


# ---------------------------------------------------------------------------
# Prior authorization
# ---------------------------------------------------------------------------

class PriorAuthPenalty(BaseModel):
    in_network_member_held_harmless: bool = True
    out_of_network_benefit_reduction: Decimal   # 0.25 = 25%
    penalty_counts_toward_oop: bool = False


class PriorAuthorization(BaseModel):
    required_services: list[str]
    penalty: PriorAuthPenalty
    retrospective_window_hours: int = 48


# ---------------------------------------------------------------------------
# Correspondence & state rules
# ---------------------------------------------------------------------------

class StateCorrespondenceRule(BaseModel):
    state: str
    requires_gender_neutral_language: bool = False
    required_appeal_rights_verbiage: Optional[str] = None
    surprise_billing_notice_required: bool = False
    required_disclosures: list[str] = []
    language_requirements: list[str] = []
    balance_billing_protections: bool = False


class CorrespondenceRules(BaseModel):
    default_pronoun_style: str = "they/them"
    state_rules: list[StateCorrespondenceRule] = []
    eob_required_fields: list[str] = []
    denial_letter_required_fields: list[str] = []


# ---------------------------------------------------------------------------
# Claims & appeals
# ---------------------------------------------------------------------------

class AppealsLevel(BaseModel):
    name: str
    filing_deadline_days: int
    decision_deadline_days: int
    expedited_deadline_hours: Optional[int] = None


class ClaimsAndAppeals(BaseModel):
    oon_filing_deadline_days: int = 365
    appeals_levels: list[AppealsLevel]
    member_rights: list[str]


# ---------------------------------------------------------------------------
# Special provisions
# ---------------------------------------------------------------------------

class COBRule(BaseModel):
    dependent_rule: str         # "birthday_rule"
    employee_primary_rule: str


class TravelEmergency(BaseModel):
    geographic_scope: str
    max_trip_days: int
    cost_share_same_as: str
    repatriation_max: Decimal
    follow_up_requires_transfer: bool = True


class SpecialProvisions(BaseModel):
    cob: COBRule
    travel_emergency: TravelEmergency
    cobra_months_employee: int = 18
    cobra_months_dependent: int = 36
    cobra_premium_pct: Decimal
    grace_period_days: int = 31


# ---------------------------------------------------------------------------
# Network quirks
# ---------------------------------------------------------------------------

class NetworkQuirk(BaseModel):
    id: str
    name: str
    description: str
    risk: str
    affected_services: list[str]


# ---------------------------------------------------------------------------
# Top-level policy
# ---------------------------------------------------------------------------

class Policy(BaseModel):
    # metadata
    plan_name: str
    policy_number: str
    group_number: str
    effective_date: date
    plan_year_start: date
    plan_year_end: date
    plan_type: PlanType
    sbc_version: str

    # foundational policies this plan inherits / must comply with
    base_policies: list[BasePolicy] = []

    # financials
    deductibles: Deductibles
    oop_max: OutOfPocketMax

    # benefits
    preventive_care: PreventiveCare
    primary_care: list[ServiceBenefit]
    specialist_care: list[ServiceBenefit]
    emergency: EmergencyCare
    inpatient: InpatientCare
    mental_health: MentalHealthBenefits
    pharmacy: PharmacyBenefits
    dental: DentalBenefits
    vision: VisionBenefits
    rehab: RehabBenefits

    # rules
    prior_authorization: PriorAuthorization
    correspondence: CorrespondenceRules
    claims_and_appeals: ClaimsAndAppeals
    exclusions: list[str]
    special_provisions: SpecialProvisions
    network_quirks: list[NetworkQuirk] = []
