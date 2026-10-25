"""Leakage-aware static Home Credit snapshot and feature contracts."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd

HOME_CREDIT_TARGET = "TARGET"
HOME_CREDIT_ID = "SK_ID_CURR"
HOME_CREDIT_SPLIT_SEED = 42
HOME_CREDIT_FEATURE_VERSION_V0 = "features-v0"
HOME_CREDIT_FEATURE_VERSION_V2 = "features-v2"

HOME_CREDIT_AUDIT_ONLY_COLUMNS = (
    "CODE_GENDER",
    "DAYS_BIRTH",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
)

HOME_CREDIT_APPLICATION_FEATURES = (
    "NAME_CONTRACT_TYPE",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "NAME_INCOME_TYPE",
    "NAME_TYPE_SUITE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "FLAG_MOBIL",
    "FLAG_EMP_PHONE",
    "FLAG_WORK_PHONE",
    "FLAG_PHONE",
    "FLAG_EMAIL",
    "CNT_FAM_MEMBERS",
    "REGION_RATING_CLIENT",
    "REGION_RATING_CLIENT_W_CITY",
    "REG_CITY_NOT_LIVE_CITY",
    "REG_CITY_NOT_WORK_CITY",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "AMT_REQ_CREDIT_BUREAU_HOUR",
    "AMT_REQ_CREDIT_BUREAU_DAY",
    "AMT_REQ_CREDIT_BUREAU_WEEK",
    "AMT_REQ_CREDIT_BUREAU_MON",
    "AMT_REQ_CREDIT_BUREAU_QRT",
    "AMT_REQ_CREDIT_BUREAU_YEAR",
)

HOME_CREDIT_DERIVED_FEATURES = (
    "BUREAU_COUNT",
    "BUREAU_ACTIVE_COUNT",
    "BUREAU_OVERDUE_MAX",
    "BUREAU_CREDIT_SUM",
    "BUREAU_DEBT_SUM",
    "PREVIOUS_APPLICATION_COUNT",
    "PREVIOUS_APPROVED_COUNT",
    "PREVIOUS_REFUSED_COUNT",
    "PREVIOUS_CREDIT_SUM",
    "PREVIOUS_DAYS_DECISION_MIN",
    "INSTALLMENT_COUNT",
    "INSTALLMENT_LATE_COUNT",
    "INSTALLMENT_SHORTFALL_SUM",
    "INSTALLMENT_PAYMENT_SUM",
    "INSTALLMENT_AMOUNT_DUE_SUM",
)

HOME_CREDIT_ENGINEERED_FEATURES_V2 = (
    "APP_CREDIT_INCOME_RATIO",
    "APP_ANNUITY_INCOME_RATIO",
    "APP_GOODS_CREDIT_RATIO",
    "APP_INCOME_PER_FAMILY",
    "EXT_SOURCE_MEAN",
    "EXT_SOURCE_MIN",
    "EXT_SOURCE_MAX",
    "EXT_SOURCE_STD",
    "EXT_SOURCE_MISSING_COUNT",
    "BUREAU_DEBT_CREDIT_RATIO",
    "BUREAU_ACTIVE_RATIO",
    "BUREAU_OVERDUE_FLAG",
    "PREVIOUS_APPROVAL_RATE",
    "PREVIOUS_REFUSAL_RATE",
    "PREVIOUS_CREDIT_MEAN",
    "INSTALLMENT_LATE_RATE",
    "INSTALLMENT_PAYMENT_COVERAGE",
)


def validate_application_frame(frame: pd.DataFrame) -> None:
    """Validate the application contract before any feature engineering."""
    required = {HOME_CREDIT_ID, HOME_CREDIT_TARGET, *HOME_CREDIT_APPLICATION_FEATURES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"application frame missing required columns: {missing}")
    if frame[HOME_CREDIT_ID].isna().any() or not frame[HOME_CREDIT_ID].is_unique:
        raise ValueError("application entity IDs must be present and unique")
    target = set(frame[HOME_CREDIT_TARGET].dropna().unique())
    if target != {0, 1} or frame[HOME_CREDIT_TARGET].isna().any():
        raise ValueError("TARGET must be complete and contain both binary classes")
    if set(HOME_CREDIT_AUDIT_ONLY_COLUMNS) & set(HOME_CREDIT_APPLICATION_FEATURES):
        raise ValueError("audit-only columns cannot be model features")


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series[Any]:
    return pd.to_numeric(frame[column], errors="coerce")


def aggregate_bureau(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate bureau history available at or before the application snapshot."""
    required = {
        HOME_CREDIT_ID,
        "CREDIT_ACTIVE",
        "DAYS_CREDIT",
        "CREDIT_DAY_OVERDUE",
        "AMT_CREDIT_SUM",
        "AMT_CREDIT_SUM_DEBT",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"bureau frame missing required columns: {missing}")
    historical = frame[_numeric(frame, "DAYS_CREDIT").fillna(0) <= 0].copy()
    historical["_overdue"] = _numeric(historical, "CREDIT_DAY_OVERDUE")
    historical["_credit"] = _numeric(historical, "AMT_CREDIT_SUM")
    historical["_debt"] = _numeric(historical, "AMT_CREDIT_SUM_DEBT")
    historical["_active"] = historical["CREDIT_ACTIVE"].eq("Active").astype(int)
    return historical.groupby(HOME_CREDIT_ID, as_index=False).agg(
        BUREAU_COUNT=(HOME_CREDIT_ID, "size"),
        BUREAU_ACTIVE_COUNT=("_active", "sum"),
        BUREAU_OVERDUE_MAX=("_overdue", "max"),
        BUREAU_CREDIT_SUM=("_credit", "sum"),
        BUREAU_DEBT_SUM=("_debt", "sum"),
    )


def aggregate_previous_applications(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate prior applications using their relative decision date."""
    required = {
        HOME_CREDIT_ID,
        "DAYS_DECISION",
        "NAME_CONTRACT_STATUS",
        "AMT_CREDIT",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"previous application frame missing required columns: {missing}"
        )
    historical = frame[_numeric(frame, "DAYS_DECISION").fillna(0) <= 0].copy()
    historical["_credit"] = _numeric(historical, "AMT_CREDIT")
    historical["_approved"] = (
        historical["NAME_CONTRACT_STATUS"].eq("Approved").astype(int)
    )
    historical["_refused"] = (
        historical["NAME_CONTRACT_STATUS"].eq("Refused").astype(int)
    )
    historical["_days_decision"] = _numeric(historical, "DAYS_DECISION")
    return historical.groupby(HOME_CREDIT_ID, as_index=False).agg(
        PREVIOUS_APPLICATION_COUNT=(HOME_CREDIT_ID, "size"),
        PREVIOUS_APPROVED_COUNT=("_approved", "sum"),
        PREVIOUS_REFUSED_COUNT=("_refused", "sum"),
        PREVIOUS_CREDIT_SUM=("_credit", "sum"),
        PREVIOUS_DAYS_DECISION_MIN=("_days_decision", "min"),
    )


def aggregate_installments(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate prior installment behavior without using future-relative rows."""
    required = {
        HOME_CREDIT_ID,
        "DAYS_INSTALMENT",
        "DAYS_ENTRY_PAYMENT",
        "AMT_INSTALMENT",
        "AMT_PAYMENT",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"installments frame missing required columns: {missing}")
    installment_days = _numeric(frame, "DAYS_INSTALMENT")
    payment_days = _numeric(frame, "DAYS_ENTRY_PAYMENT")
    historical = frame[
        (installment_days.fillna(0) <= 0) & (payment_days.fillna(0) <= 0)
    ].copy()
    amount_due = _numeric(historical, "AMT_INSTALMENT").fillna(0)
    amount_paid = _numeric(historical, "AMT_PAYMENT").fillna(0)
    historical["_late"] = (
        payment_days.loc[historical.index] > installment_days.loc[historical.index]
    ).astype(int)
    historical["_amount_due"] = amount_due
    historical["_shortfall"] = (amount_due - amount_paid).clip(lower=0)
    historical["_payment"] = amount_paid
    return historical.groupby(HOME_CREDIT_ID, as_index=False).agg(
        INSTALLMENT_COUNT=(HOME_CREDIT_ID, "size"),
        INSTALLMENT_LATE_COUNT=("_late", "sum"),
        INSTALLMENT_SHORTFALL_SUM=("_shortfall", "sum"),
        INSTALLMENT_PAYMENT_SUM=("_payment", "sum"),
        INSTALLMENT_AMOUNT_DUE_SUM=("_amount_due", "sum"),
    )


def add_engineered_features_v2(frame: pd.DataFrame) -> pd.DataFrame:
    """Add documented ratios and missingness signals to the frozen v0 frame."""
    result = frame.copy()

    def ratio(numerator: str, denominator: str) -> pd.Series[Any]:
        denominator_values = _numeric(result, denominator)
        denominator_values = denominator_values.mask(denominator_values == 0)
        return _numeric(result, numerator) / denominator_values

    result["APP_CREDIT_INCOME_RATIO"] = ratio("AMT_CREDIT", "AMT_INCOME_TOTAL")
    result["APP_ANNUITY_INCOME_RATIO"] = ratio("AMT_ANNUITY", "AMT_INCOME_TOTAL")
    result["APP_GOODS_CREDIT_RATIO"] = ratio("AMT_GOODS_PRICE", "AMT_CREDIT")
    family = _numeric(result, "CNT_FAM_MEMBERS").clip(lower=1)
    result["APP_INCOME_PER_FAMILY"] = _numeric(result, "AMT_INCOME_TOTAL") / family

    external = result[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]].apply(
        pd.to_numeric, errors="coerce"
    )
    result["EXT_SOURCE_MEAN"] = external.mean(axis=1)
    result["EXT_SOURCE_MIN"] = external.min(axis=1)
    result["EXT_SOURCE_MAX"] = external.max(axis=1)
    result["EXT_SOURCE_STD"] = external.std(axis=1, ddof=0)
    result["EXT_SOURCE_MISSING_COUNT"] = external.isna().sum(axis=1).astype(float)

    result["BUREAU_DEBT_CREDIT_RATIO"] = ratio("BUREAU_DEBT_SUM", "BUREAU_CREDIT_SUM")
    result["BUREAU_ACTIVE_RATIO"] = ratio("BUREAU_ACTIVE_COUNT", "BUREAU_COUNT")
    result["BUREAU_OVERDUE_FLAG"] = (
        _numeric(result, "BUREAU_OVERDUE_MAX").fillna(0) > 0
    ).astype(float)
    result["PREVIOUS_APPROVAL_RATE"] = ratio(
        "PREVIOUS_APPROVED_COUNT", "PREVIOUS_APPLICATION_COUNT"
    )
    result["PREVIOUS_REFUSAL_RATE"] = ratio(
        "PREVIOUS_REFUSED_COUNT", "PREVIOUS_APPLICATION_COUNT"
    )
    result["PREVIOUS_CREDIT_MEAN"] = ratio(
        "PREVIOUS_CREDIT_SUM", "PREVIOUS_APPLICATION_COUNT"
    )
    result["INSTALLMENT_LATE_RATE"] = ratio(
        "INSTALLMENT_LATE_COUNT", "INSTALLMENT_COUNT"
    )
    result["INSTALLMENT_PAYMENT_COVERAGE"] = ratio(
        "INSTALLMENT_PAYMENT_SUM", "INSTALLMENT_AMOUNT_DUE_SUM"
    )
    return result


def build_static_feature_frame_v2(
    application: pd.DataFrame,
    *,
    bureau: pd.DataFrame | None = None,
    previous_applications: pd.DataFrame | None = None,
    installments: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the v0 contract and append only the versioned v2 features."""
    return add_engineered_features_v2(
        build_static_feature_frame(
            application,
            bureau=bureau,
            previous_applications=previous_applications,
            installments=installments,
        )
    )


def build_static_feature_frame(
    application: pd.DataFrame,
    *,
    bureau: pd.DataFrame | None = None,
    previous_applications: pd.DataFrame | None = None,
    installments: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build a static entity-level snapshot from application and prior tables."""
    validate_application_frame(application)
    columns = [HOME_CREDIT_ID, HOME_CREDIT_TARGET, *HOME_CREDIT_APPLICATION_FEATURES]
    result = application.loc[:, columns].copy()
    aggregates = (
        aggregate_bureau(bureau) if bureau is not None else None,
        aggregate_previous_applications(previous_applications)
        if previous_applications is not None
        else None,
        aggregate_installments(installments) if installments is not None else None,
    )
    for aggregate in aggregates:
        if aggregate is not None:
            result = result.merge(
                aggregate, on=HOME_CREDIT_ID, how="left", validate="one_to_one"
            )
    return result


def stable_entity_split(
    frame: pd.DataFrame,
    *,
    seed: int = HOME_CREDIT_SPLIT_SEED,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> pd.DataFrame:
    """Create deterministic entity-disjoint static splits using hashed IDs."""
    validate_application_frame(frame)
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train and validation fractions must leave test rows")
    result = frame[[HOME_CREDIT_ID, HOME_CREDIT_TARGET]].copy()
    threshold_train = int(train_fraction * 10_000)
    threshold_validation = int((train_fraction + validation_fraction) * 10_000)

    def assign(identifier: int) -> str:
        digest = hashlib.sha256(
            f"cop-home-credit-static-v1:{seed}:{identifier}".encode()
        ).hexdigest()
        bucket = int(digest[:8], 16) % 10_000
        if bucket < threshold_train:
            return "train"
        if bucket < threshold_validation:
            return "validation"
        return "test"

    result["split"] = [assign(int(identifier)) for identifier in result[HOME_CREDIT_ID]]
    if result[HOME_CREDIT_ID].duplicated().any():
        raise ValueError("entity IDs must be unique before splitting")
    counts = result.groupby("split")[HOME_CREDIT_TARGET].nunique()
    if set(counts.index) != {"train", "validation", "test"} or (counts < 2).any():
        raise ValueError("each static split must contain both target classes")
    return result
