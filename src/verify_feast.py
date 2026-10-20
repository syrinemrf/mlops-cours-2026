"""Check synthetic snapshot joins and serving; publish only aggregate evidence."""

import json
from pathlib import Path

import pandas as pd
import yaml
from feast import FeatureStore

from src.dataset_config import load_config


def main():
    cfg = load_config()
    params = yaml.safe_load(Path("params.yaml").read_text())["prepare"]
    key = params["id_column"]
    snapshot = pd.Timestamp(params["event_timestamp"])
    train = pd.read_csv("data/processed/train.csv")
    source = pd.read_parquet("data/processed/features.parquet")
    assert len(source) == 1470 and source[key].is_unique
    assert set(source) == {key, *cfg.features, "event_timestamp"}
    assert not {cfg.target, *cfg.extra_sensitive} & set(source)
    assert source.event_timestamp.eq(snapshot).all()
    store = FeatureStore(repo_path="features")
    service = store.get_feature_service("scoring_v1")
    entities = train[[key, cfg.target]].assign(event_timestamp=snapshot)
    offline = store.get_historical_features(entity_df=entities, features=service).to_df()
    expected = train.set_index(key)[cfg.features].sort_index().copy()
    expected[cfg.numeric] = expected[cfg.numeric].astype("float64")
    expected[cfg.categorical] = expected[cfg.categorical].astype(str)
    actual = offline.set_index(key)[cfg.features].sort_index()
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
    # Synthetic time boundary test only; not evidence about real HR chronology.
    before = entities.head(3).copy()
    before["event_timestamp"] = snapshot - pd.Timedelta(seconds=1)
    missing = store.get_historical_features(entity_df=before, features=service).to_df()
    assert missing[cfg.features].isna().all().all()
    identifier = int(train[key].iloc[0])
    online = store.get_online_features(features=service, entity_rows=[{key: identifier}]).to_dict()
    wanted = expected.loc[identifier]
    for column in cfg.features:
        value = online[column][0]
        assert value is not None and not pd.isna(value), column
        assert value == wanted[column], column
    report = {
        "protocol": "A",
        "entity": "employee",
        "entity_key": key,
        "feature_view": "request_features",
        "feature_service": "scoring_v1",
        "source_rows": len(source),
        "offline_shape": list(offline.shape),
        "numeric_features": len(cfg.numeric),
        "categorical_features": len(cfg.categorical),
        "all_27_offline_features_match_train": True,
        "three_before_snapshot_queries_have_only_missing_features": True,
        "online_entities_checked": 1,
        "online_features_checked": len(cfg.features),
        "all_online_features_match_prepared_values": True,
        "timestamp": snapshot.isoformat(),
        "timestamp_role": "technical_synthetic_snapshot",
        "temporal_production_leakage_claim": False,
    }
    Path("reports/m1/final-feast-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
