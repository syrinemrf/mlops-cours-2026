"""Offline tests using generated records, never copies of the source dataset."""

import copy
import hashlib
import io
import urllib.error
import zipfile
from dataclasses import replace

import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from src import download
from src.dataset_config import load_config


@pytest.fixture
def source_frame():
    row = {col: 1 for col in download.SOURCE_COLUMNS}
    row.update({col: sorted(values)[0] for col, values in download.TEXT_DOMAINS.items()})
    row.update(download.CONSTANTS)
    frame = pd.DataFrame([row] * 1470, columns=download.SOURCE_COLUMNS)
    frame[download.ID_COLUMN] = range(1, 1471)
    frame["Attrition"] = ["Yes"] * 237 + ["No"] * 1233
    frame["Age"] = [20, 40] * 735
    # Keep all other source fields variable, except the three declared constants.
    for col in download.SOURCE_COLUMNS:
        if col in download.CONSTANTS or col in {"Attrition", "Age", download.ID_COLUMN}:
            continue
        if col in download.TEXT_DOMAINS:
            values = sorted(download.TEXT_DOMAINS[col])
            frame.loc[1, col] = values[-1]
        elif col in download.ORDINAL_LEVELS:
            frame.loc[1, col] = 2
        else:
            frame.loc[1, col] = 2
    return frame


@pytest.fixture
def payload_and_cfg(source_frame):
    payload = source_frame.to_csv(index=False).encode("utf-8")
    cfg = load_config()
    raw = copy.deepcopy(cfg.raw)
    raw["source"]["sha256"] = hashlib.sha256(payload).hexdigest()
    return payload, replace(cfg, raw=raw)


def test_export_separates_predictors_sensitive_and_identifier(payload_and_cfg):
    payload, cfg = payload_and_cfg
    frame, report = download.prepare_export(payload, cfg)
    assert frame.shape == (1470, 32)
    assert list(frame) == ["EmployeeNumber", *cfg.columns]
    assert len(cfg.numeric) == 13 and len(cfg.categorical) == 14
    assert set(cfg.extra_sensitive) == {"Age", "Gender", "MaritalStatus"}
    X, y = cfg.split_xy(frame)
    assert X.shape == (1470, 27) and y.sum() == 237
    assert not {"EmployeeNumber", *download.CONSTANTS, *cfg.extra_sensitive} & set(X)
    assert not cfg.sensitive_frame(frame).isna().any().any()
    assert frame["Education"].str.contains("Below College|College").all()
    assert report["missing_values"] == report["duplicate_rows"] == 0


def test_changed_bytes_rejected(payload_and_cfg):
    payload, cfg = payload_and_cfg
    with pytest.raises(ValueError, match="SHA-256"):
        download.prepare_export(payload + b"\n", cfg)


@pytest.mark.parametrize("version", [None, 0, 2, "1"])
def test_unpinned_version_rejected(version):
    source = dict(load_config().raw["source"], version=version)
    with pytest.raises(ValueError, match="version 1"):
        download.download_url(source)


def test_wrong_source_or_digest_rejected():
    source = load_config().raw["source"]
    with pytest.raises(ValueError):
        download.download_url(dict(source, kaggle_ref="arbitrary/mirror"))
    with pytest.raises(ValueError):
        download.download_url(dict(source, sha256=""))
    assert download.download_url(source).endswith("datasetVersionNumber=1")


@pytest.mark.parametrize(
    "defect",
    [
        "shape",
        "column",
        "duplicate_header",
        "missing",
        "duplicate_row",
        "identifier",
        "target",
        "constant",
        "integer",
        "ordinal",
        "category",
    ],
)
def test_source_validation_rejects_drift(source_frame, defect):
    frame = source_frame.copy()
    if defect == "shape":
        frame = frame.iloc[:-1]
    elif defect == "column":
        frame = frame.rename(columns={"Age": "Unexpected"})
    elif defect == "duplicate_header":
        frame.columns = ["Age", *list(frame.columns)[1:-1], "Age"]
    elif defect == "missing":
        frame.loc[0, "Age"] = float("nan")
    elif defect == "duplicate_row":
        frame.iloc[1] = frame.iloc[0]
    elif defect == "identifier":
        frame.loc[1, "EmployeeNumber"] = frame.loc[0, "EmployeeNumber"]
    elif defect == "target":
        frame.loc[0, "Attrition"] = "Maybe"
    elif defect == "constant":
        frame["StandardHours"] = 40
    elif defect == "integer":
        frame["DailyRate"] = frame["DailyRate"].astype(float) + 0.1
    elif defect == "ordinal":
        frame.loc[0, "Education"] = 6
    elif defect == "category":
        frame.loc[0, "Gender"] = "Unexpected"
    with pytest.raises(ValueError):
        download.validate_source(frame)


def test_archive_and_csv_use_identical_verified_bytes(payload_and_cfg):
    payload, cfg = payload_and_cfg
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(cfg.raw["source"]["filename"], payload)
        archive.writestr("../never-extracted", "irrelevant")
    assert download.extract_csv(buffer.getvalue(), cfg.raw["source"]["filename"]) == payload
    assert download.extract_csv(payload, cfg.raw["source"]["filename"]) == payload
    with pytest.raises(ValueError, match="expected CSV"):
        download.extract_csv(buffer.getvalue(), "missing.csv")


def test_size_limit_enforced(monkeypatch):
    monkeypatch.setattr(download, "MAX_BYTES", 10)
    with pytest.raises(ValueError, match="size"):
        download.extract_csv(b"x" * 11, "a.csv")


def test_http_auth_error_does_not_disclose_response(monkeypatch):
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError(
            "https://example/?secret=never-print", 401, "private", {}, None
        )

    monkeypatch.setattr(download.urllib.request, "urlopen", fail)
    with pytest.raises(RuntimeError, match="Kaggle HTTP 401") as error:
        download.fetch_archive("https://www.kaggle.com/")
    assert "never-print" not in str(error.value)


def test_main_is_deterministic_and_does_not_overwrite_on_invalid_input(
    payload_and_cfg,
    tmp_path,
    monkeypatch,
):
    payload, cfg = payload_and_cfg
    output = tmp_path / "dataset.csv"
    monkeypatch.setattr(download, "load_config", lambda: replace(cfg, raw_path=str(output)))
    monkeypatch.setattr(download, "fetch_archive", lambda url: payload)
    monkeypatch.setattr("sys.argv", ["download"])
    assert download.main() == 0
    first = output.read_bytes()
    assert download.main() == 0 and output.read_bytes() == first
    monkeypatch.setattr(download, "fetch_archive", lambda url: payload + b"\n")
    with pytest.raises(ValueError, match="SHA-256"):
        download.main()
    assert output.read_bytes() == first


def test_course_split_stratification_and_train_only_preprocessing(payload_and_cfg):
    payload, cfg = payload_and_cfg
    frame, _ = download.prepare_export(payload, cfg)
    train, test = train_test_split(
        frame,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=cfg.encode_target(frame[cfg.target]),
    )
    assert (len(train), len(test)) == (1176, 294)
    assert (
        cfg.encode_target(train[cfg.target]).sum(),
        cfg.encode_target(test[cfg.target]).sum(),
    ) == (
        190,
        47,
    )
    assert not set(train.EmployeeNumber) & set(test.EmployeeNumber)
    pre = cfg.build_preprocessor()
    X_train, _ = cfg.split_xy(train)
    X_test, _ = cfg.split_xy(test)
    pre.fit(X_train)
    scaler = pre.named_transformers_["num"].named_steps["scale"]
    before = scaler.mean_.copy()
    pre.transform(X_test)
    assert (scaler.mean_ == before).all()
    assert scaler.mean_ == pytest.approx(X_train[cfg.numeric].mean().to_numpy())
