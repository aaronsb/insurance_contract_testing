"""Correspondence and state-specific compliance tests.

Risk category: REGULATORY / MEMBER EXPERIENCE
If these fail, members receive non-compliant communications — wrong pronouns,
missing required disclosures, absent translations. Can trigger state regulatory
action, fines, and member complaints.
"""

import re


# ---------------------------------------------------------------------------
# Gendered language by state
# ---------------------------------------------------------------------------

class TestGenderedLanguage:

    def test_default_pronoun_style_is_neutral(self, policy):
        """Risk: Default 'he/she' or 'him/her' → non-compliant in states requiring
        gender-neutral language. Correspondence templates must default to neutral."""
        assert policy.correspondence.default_pronoun_style == "they/them"

    def test_california_requires_neutral(self, policy):
        """Risk: 'him/her' in CA correspondence → violation of CA Insurance Code
        and Gender Recognition Act. Regulatory action."""
        ca = next(
            (s for s in policy.correspondence.state_rules if s.state == "CA"), None
        )
        assert ca is not None, "Missing CA state rules"
        assert ca.requires_gender_neutral_language is True

    def test_new_york_requires_neutral(self, policy):
        ny = next(
            (s for s in policy.correspondence.state_rules if s.state == "NY"), None
        )
        assert ny is not None, "Missing NY state rules"
        assert ny.requires_gender_neutral_language is True

    def test_oregon_requires_neutral(self, policy):
        """Risk: OR explicitly supports non-binary gender markers. Using binary
        pronouns violates OR insurance regulations."""
        ore = next(
            (s for s in policy.correspondence.state_rules if s.state == "OR"), None
        )
        assert ore is not None, "Missing OR state rules"
        assert ore.requires_gender_neutral_language is True

    def test_texas_does_not_require_neutral(self, policy):
        """Risk: Applying gender-neutral language in TX where not required isn't a
        violation, but incorrectly flagging TX as requiring it adds unnecessary
        process burden."""
        tx = next(
            (s for s in policy.correspondence.state_rules if s.state == "TX"), None
        )
        assert tx is not None, "Missing TX state rules"
        assert tx.requires_gender_neutral_language is False

    def test_states_requiring_neutral_is_subset(self, policy):
        """Verify that we have an explicit decision for every state in our rules —
        no accidental None values."""
        for state_rule in policy.correspondence.state_rules:
            assert isinstance(state_rule.requires_gender_neutral_language, bool), (
                f"State {state_rule.state}: gender_neutral_language must be explicitly True or False"
            )


# ---------------------------------------------------------------------------
# Language requirements
# ---------------------------------------------------------------------------

class TestLanguageRequirements:

    def test_california_spanish(self, policy):
        """Risk: CA has the largest Spanish-speaking population. Missing Spanish
        translation → violation of CA Health & Safety Code § 1367.04."""
        ca = next(s for s in policy.correspondence.state_rules if s.state == "CA")
        assert "Spanish" in ca.language_requirements

    def test_california_threshold_languages(self, policy):
        """Risk: CA requires translations in threshold languages. Missing any →
        regulatory non-compliance."""
        ca = next(s for s in policy.correspondence.state_rules if s.state == "CA")
        required = {"Spanish", "Chinese", "Tagalog", "Vietnamese", "Korean"}
        actual = set(ca.language_requirements)
        missing = required - actual
        assert not missing, f"CA missing threshold languages: {missing}"

    def test_new_york_threshold_languages(self, policy):
        ny = next(s for s in policy.correspondence.state_rules if s.state == "NY")
        required = {"Spanish", "Chinese", "Russian", "Bengali", "Haitian_Creole"}
        actual = set(ny.language_requirements)
        missing = required - actual
        assert not missing, f"NY missing threshold languages: {missing}"

    def test_every_state_has_spanish(self, policy):
        """Risk: Spanish is the most common non-English language in the US.
        Any state without Spanish translation creates access barriers."""
        for state_rule in policy.correspondence.state_rules:
            assert "Spanish" in state_rule.language_requirements, (
                f"State {state_rule.state}: missing Spanish language requirement"
            )


# ---------------------------------------------------------------------------
# Surprise billing notices
# ---------------------------------------------------------------------------

class TestSurpriseBillingNotices:

    def test_ca_surprise_billing_notice(self, policy):
        ca = next(s for s in policy.correspondence.state_rules if s.state == "CA")
        assert ca.surprise_billing_notice_required is True

    def test_ny_surprise_billing_notice(self, policy):
        ny = next(s for s in policy.correspondence.state_rules if s.state == "NY")
        assert ny.surprise_billing_notice_required is True

    def test_fl_no_surprise_billing_notice(self, policy):
        """Risk: Sending surprise billing notice in FL (not required) isn't harmful,
        but marking it as required adds unnecessary compliance tracking."""
        fl = next(s for s in policy.correspondence.state_rules if s.state == "FL")
        assert fl.surprise_billing_notice_required is False

    def test_balance_billing_protection_states(self, policy):
        """Risk: States with balance billing protections require specific member
        notifications. Missing → state regulatory action."""
        protected = [
            s for s in policy.correspondence.state_rules
            if s.balance_billing_protections
        ]
        # Every protected state must also have surprise billing notice
        for state_rule in protected:
            assert state_rule.surprise_billing_notice_required, (
                f"State {state_rule.state}: has balance billing protections but "
                f"no surprise billing notice requirement"
            )


# ---------------------------------------------------------------------------
# Required disclosures
# ---------------------------------------------------------------------------

class TestRequiredDisclosures:

    def test_ca_independent_medical_review(self, policy):
        """Risk: CA members not informed of IMR rights → DMHC enforcement action."""
        ca = next(s for s in policy.correspondence.state_rules if s.state == "CA")
        assert "independent_medical_review_rights" in ca.required_disclosures

    def test_ny_external_appeal_rights(self, policy):
        """Risk: NY members not informed of external appeal → DFS enforcement."""
        ny = next(s for s in policy.correspondence.state_rules if s.state == "NY")
        assert "external_appeal_rights" in ny.required_disclosures

    def test_or_nonbinary_support(self, policy):
        """Risk: OR requires support for non-binary gender markers. Missing
        disclosure → OID enforcement action."""
        ore = next(s for s in policy.correspondence.state_rules if s.state == "OR")
        assert "non_binary_gender_marker_support" in ore.required_disclosures


# ---------------------------------------------------------------------------
# EOB and denial letter fields
# ---------------------------------------------------------------------------

class TestDocumentFields:

    def test_eob_has_remaining_deductible(self, policy):
        """Risk: EOB missing remaining deductible → member cannot track progress
        toward deductible. ACA transparency violation."""
        assert "remaining_deductible" in policy.correspondence.eob_required_fields

    def test_eob_has_remaining_oop(self, policy):
        """Risk: EOB missing remaining OOP → member cannot track progress toward
        out-of-pocket max."""
        assert "remaining_oop" in policy.correspondence.eob_required_fields

    def test_eob_has_appeal_rights(self, policy):
        """Risk: EOB without appeal rights notice → ERISA violation."""
        assert "appeal_rights_notice" in policy.correspondence.eob_required_fields

    def test_denial_letter_has_clinical_criteria(self, policy):
        """Risk: Denial without clinical criteria → member cannot prepare appeal.
        ERISA procedural violation."""
        assert "clinical_criteria_used" in policy.correspondence.denial_letter_required_fields

    def test_denial_letter_has_appeal_deadline(self, policy):
        """Risk: No deadline stated → member misses filing window. ERISA violation."""
        assert "appeal_deadline" in policy.correspondence.denial_letter_required_fields

    def test_denial_letter_has_external_review_info(self, policy):
        """Risk: No external review information → member unaware of independent
        review rights. ACA/ERISA violation."""
        assert "external_review_rights" in policy.correspondence.denial_letter_required_fields
