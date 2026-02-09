# Contract Model

The policy contract is modeled as a hierarchy of Pydantic models in `policy/models.py`, instantiated with actual contract values in `policy/green_cross.py`.

## Design Principles

**Contract-as-code.** The source document (`contracts/green-cross-policy.md`) is a human-readable reference. The Pydantic models are the machine-readable representation. Tests assert against the models, not the document.

**Regulatory traceability.** Every compliance-sensitive benefit section links back to its authorizing statute via `base_policies`. The `BasePolicy` model carries USC citations and CFR references. Tests verify these links exist.

**Risk annotation.** Tests don't just assert values — their docstrings explain what breaks if the assertion fails. This turns the test suite into a risk register.

## Model Hierarchy

```mermaid
classDiagram
    direction TB

    class Policy {
        plan_name: str
        policy_number: str
        plan_type: PlanType
        base_policies: list~BasePolicy~
        deductibles: Deductibles
        oop_max: OutOfPocketMax
        ...
    }

    class BasePolicy {
        id: str
        name: str
        references: list~RegulatoryReference~
    }

    class RegulatoryReference {
        statute: str
        citation: str
        cfr: str
    }

    class Deductibles {
        in_network: DeductibleTier
        out_of_network: DeductibleTier
        cross_accumulation: bool
    }

    class DeductibleTier {
        individual: Decimal
        family: Decimal
        type: DeductibleType
    }

    class OutOfPocketMax {
        in_network: OOPMaxTier
        out_of_network: OOPMaxTier
        accumulator_adjustment: AccumulatorAdjustment
    }

    Policy --> BasePolicy
    Policy --> Deductibles
    Policy --> OutOfPocketMax
    BasePolicy --> RegulatoryReference
    Deductibles --> DeductibleTier
    OutOfPocketMax --> AccumulatorAdjustment
```

## Key Models

### Financial

| Model | Purpose |
|-------|---------|
| `Deductibles` | In/out-of-network deductible tiers, embedded vs non-embedded, cross-accumulation |
| `OutOfPocketMax` | OOP limits, what counts/doesn't, accumulator adjustment program |
| `CostShare` | Copay, coinsurance, deductible applicability for any service |

### Benefits

| Model | Purpose |
|-------|---------|
| `PreventiveCare` | Services, frequency, age/gender rules, reclassification traps |
| `EmergencyCare` | ER copay/coinsurance, prudent layperson, admission waiver |
| `InpatientCare` | Admission cost share, observation status rules, maternity minimums |
| `MentalHealthBenefits` | Parity compliance flags, cost share parity with medical |
| `PharmacyBenefits` | Tier copays, step therapy, maintenance med rules, mandatory generic |
| `DentalBenefits` | Class I/II/III coverage, waiting periods, missing tooth clause |

### Compliance

| Model | Purpose |
|-------|---------|
| `BasePolicy` | Statute name, USC citation, CFR reference |
| `PriorAuthorization` | Required services, penalty rules, member-held-harmless |
| `CorrespondenceRules` | Pronoun defaults, state-specific language/disclosure requirements |
| `ClaimsAndAppeals` | Filing deadlines, appeal levels, member rights |

## Adding a New Policy

To model a second plan (e.g., a high-deductible variant):

1. Create `policy/green_cross_hdhp.py`
2. Instantiate `Policy(...)` with the HDHP values
3. Add a pytest fixture in `tests/conftest.py`
4. Parametrize tests across both plans, or write plan-specific tests

The models don't change — only the data instance does.
