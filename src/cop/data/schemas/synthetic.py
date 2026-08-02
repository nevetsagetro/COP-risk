"""Logical schema and feature roles for synthetic v1."""

from __future__ import annotations

INPUT_FEATURE_COLUMNS = (
    "requested_amount",
    "requested_term_months",
    "monthly_income",
    "employment_tenure_months",
    "existing_monthly_debt",
    "open_credit_lines",
    "revolving_balance",
    "credit_limit",
    "utilization_ratio",
    "recent_inquiries_count",
    "prior_delinquencies_count",
    "debt_to_income",
)

FEATURE_AVAILABILITY = {
    "requested_amount": "application_available_at",
    "requested_term_months": "application_available_at",
    "monthly_income": "income_available_at",
    "employment_tenure_months": "income_available_at",
    "existing_monthly_debt": "bureau_available_at",
    "open_credit_lines": "bureau_available_at",
    "revolving_balance": "bureau_available_at",
    "credit_limit": "bureau_available_at",
    "utilization_ratio": "bureau_available_at",
    "recent_inquiries_count": "bureau_available_at",
    "prior_delinquencies_count": "bureau_available_at",
    "debt_to_income": "income_available_at",
}

FEATURE_DEPENDENCIES = {
    "debt_to_income": ("existing_monthly_debt", "monthly_income"),
    "utilization_ratio": ("revolving_balance", "credit_limit"),
}

APPLICATION_COLUMNS = (
    "application_id",
    "borrower_id",
    "decision_timestamp",
    "application_available_at",
    "income_available_at",
    "bureau_available_at",
    *INPUT_FEATURE_COLUMNS,
    "horizon_end",
    "followup_end",
    "outcome_timestamp",
    "label_observed_at",
    "label_ready_at",
    "label_available_at",
    "label_status",
    "censoring_reason",
    "default_within_horizon",
)

LEDGER_COLUMNS = (
    "application_id",
    "installment_number",
    "due_at",
    "event_at",
    "event_available_at",
    "scheduled_amount",
    "paid_amount",
    "days_past_due",
)

AUDIT_ONLY_COLUMNS = ("application_id", "borrower_id", "age_band", "sex_group")
