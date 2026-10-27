"""Create deterministic stratified train/test CSVs and the Feast offline source.

Column names come from dataset.yaml and params.yaml. No learned transformation is
fitted here. Audit attributes stay in train/test but never enter the Feast view.
"""

from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from src.dataset_config import DatasetConfig, load_config

PROCESSED = Path("data/processed")


def prepare_frames(
    df: pd.DataFrame, cfg: DatasetConfig, params: dict
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg.validate_columns(df)
    id_col = params["id_column"]
    if id_col in cfg.columns:
        raise ValueError("Technical identifier must be separate from features, audit and target.")
    df = df.copy()
    if id_col not in df:
        df.insert(0, id_col, range(1, len(df) + 1))
    if (
        df[id_col].isna().any()
        or not pd.api.types.is_integer_dtype(df[id_col])
        or not df[id_col].is_unique
        or (df[id_col] <= 0).any()
    ):
        raise ValueError("Technical identifiers must be unique positive nonmissing integers.")
    if df[cfg.target].isna().any() or df[cfg.target].nunique() != 2:
        raise ValueError("Expected a nonmissing binary target.")
    y = cfg.encode_target(df[cfg.target])
    if y.nunique() != 2:
        raise ValueError("Positive class is absent from the binary target.")
    if any(s.column in cfg.features for s in cfg.sensitive):
        raise ValueError("This project's audit attributes must stay outside predictors.")
    timestamp = pd.Timestamp(params["event_timestamp"])
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError("Feast requires an explicit, fixed timezone-aware timestamp.")
    df = df[[id_col, *cfg.columns]]
    train, test = train_test_split(
        df, test_size=cfg.test_size, random_state=cfg.random_state, stratify=y
    )
    features = df[[id_col, *cfg.features]].copy()
    features[cfg.numeric] = features[cfg.numeric].astype("float64")
    features[cfg.categorical] = features[cfg.categorical].astype(str)
    features["event_timestamp"] = timestamp.tz_convert("UTC")
    return train, test, features


def main() -> None:
    cfg = load_config()
    params = yaml.safe_load(Path("params.yaml").read_text(encoding="utf-8"))["prepare"]
    train, test, features = prepare_frames(pd.read_csv(cfg.raw_path), cfg, params)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    train.to_csv(PROCESSED / "train.csv", index=False, lineterminator="\n")
    test.to_csv(PROCESSED / "test.csv", index=False, lineterminator="\n")
    features.to_parquet(PROCESSED / "features.parquet", index=False)
    rate = cfg.encode_target(train[cfg.target]).mean(), cfg.encode_target(test[cfg.target]).mean()
    print(
        f"Train: {len(train)} / Test: {len(test)}; "
        f"positive '{cfg.positive_class}': {rate[0]:.1%} / {rate[1]:.1%}"
    )


if __name__ == "__main__":
    main()
