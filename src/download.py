"""Download pinned Kaggle IBM HR data; verify bytes and schema before export.

Usage: python -m src.download [--from-file official-v1.zip|official-v1.csv]
Public HTTPS requires no credentials at verification time. If access becomes gated,
use the official Kaggle client with local credentials and --from-file; never a mirror.
The pinned digest is a first-observation integrity anchor, not independent authenticity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from src.dataset_config import DatasetConfig, load_config

KAGGLE_REF = "pavansubhasht/ibm-hr-analytics-attrition-dataset"
MAX_BYTES = 5_000_000
ID_COLUMN = "EmployeeNumber"
CONSTANTS = {"EmployeeCount": 1, "Over18": "Y", "StandardHours": 80}
SOURCE_COLUMNS = [
    "Age",
    "Attrition",
    "BusinessTravel",
    "DailyRate",
    "Department",
    "DistanceFromHome",
    "Education",
    "EducationField",
    "EmployeeCount",
    "EmployeeNumber",
    "EnvironmentSatisfaction",
    "Gender",
    "HourlyRate",
    "JobInvolvement",
    "JobLevel",
    "JobRole",
    "JobSatisfaction",
    "MaritalStatus",
    "MonthlyIncome",
    "MonthlyRate",
    "NumCompaniesWorked",
    "Over18",
    "OverTime",
    "PercentSalaryHike",
    "PerformanceRating",
    "RelationshipSatisfaction",
    "StandardHours",
    "StockOptionLevel",
    "TotalWorkingYears",
    "TrainingTimesLastYear",
    "WorkLifeBalance",
    "YearsAtCompany",
    "YearsInCurrentRole",
    "YearsSinceLastPromotion",
    "YearsWithCurrManager",
]
TEXT_COLUMNS = {
    "Attrition",
    "BusinessTravel",
    "Department",
    "EducationField",
    "Gender",
    "JobRole",
    "MaritalStatus",
    "Over18",
    "OverTime",
}
# Ordered source codes are retained in the labels, but treated nominally by the course pipeline.
ORDINAL_LEVELS = {
    "Education": ["Below College", "College", "Bachelor", "Master", "Doctor"],
    "EnvironmentSatisfaction": ["Low", "Medium", "High", "Very High"],
    "JobInvolvement": ["Low", "Medium", "High", "Very High"],
    "JobLevel": ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
    "JobSatisfaction": ["Low", "Medium", "High", "Very High"],
    "PerformanceRating": ["Low", "Good", "Excellent", "Outstanding"],
    "RelationshipSatisfaction": ["Low", "Medium", "High", "Very High"],
    "StockOptionLevel": ["Level 0", "Level 1", "Level 2", "Level 3"],
    "WorkLifeBalance": ["Bad", "Good", "Better", "Best"],
}
TEXT_DOMAINS = {
    "Attrition": {"No", "Yes"},
    "BusinessTravel": {"Non-Travel", "Travel_Rarely", "Travel_Frequently"},
    "Department": {"Human Resources", "Research & Development", "Sales"},
    "EducationField": {
        "Human Resources",
        "Life Sciences",
        "Marketing",
        "Medical",
        "Other",
        "Technical Degree",
    },
    "Gender": {"Female", "Male"},
    "JobRole": {
        "Healthcare Representative",
        "Human Resources",
        "Laboratory Technician",
        "Manager",
        "Manufacturing Director",
        "Research Director",
        "Research Scientist",
        "Sales Executive",
        "Sales Representative",
    },
    "MaritalStatus": {"Divorced", "Married", "Single"},
    "Over18": {"Y"},
    "OverTime": {"No", "Yes"},
}


def download_url(source: dict) -> str:
    """Only use the requested official dataset and an explicitly pinned version."""
    if source.get("kaggle_ref") != KAGGLE_REF or source.get("version") != 1:
        raise ValueError("Expected official IBM HR Kaggle version 1; review any version change.")
    digest = source.get("sha256", "")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("A pinned lowercase SHA-256 is required.")
    return f"https://www.kaggle.com/api/v1/datasets/download/{KAGGLE_REF}?datasetVersionNumber=1"


def fetch_archive(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "mlops-itbs-ibm-hr/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Do not echo redirect URLs, headers, credentials or response bodies.
        raise RuntimeError(
            f"Kaggle HTTP {exc.code}; use official local Kaggle credentials and --from-file."
        ) from None
    if len(content) > MAX_BYTES:
        raise ValueError("Kaggle response exceeds the allowed size.")
    return content


def extract_csv(content: bytes, filename: str) -> bytes:
    if len(content) > MAX_BYTES:
        raise ValueError("Input exceeds the allowed size.")
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return content  # An offline CSV is still checked against the pinned digest.
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()
        if names.count(filename) != 1:
            raise ValueError("Archive must contain exactly one expected CSV member.")
        if archive.getinfo(filename).file_size > MAX_BYTES:
            raise ValueError("CSV member exceeds the allowed size.")
        return archive.read(filename)  # Never extract paths onto the filesystem.


def validate_source(df: pd.DataFrame) -> dict:
    """Validate the full source schema before excluding any columns."""
    if df.shape != (1470, 35) or list(df.columns) != SOURCE_COLUMNS:
        raise ValueError("Expected 1470 rows and the exact 35-column IBM HR source schema.")
    if df.isna().any().any() or df.duplicated().any():
        raise ValueError("Source contains missing values or duplicate rows.")
    for col in set(SOURCE_COLUMNS) - TEXT_COLUMNS:
        if not pd.api.types.is_integer_dtype(df[col]) or (df[col] < 0).any():
            raise ValueError(f"Expected nonnegative integers in {col}.")
    for col, allowed in TEXT_DOMAINS.items():
        if not set(df[col]) <= allowed:
            raise ValueError(f"Unexpected categorical values in {col}.")
    for col, levels in ORDINAL_LEVELS.items():
        start = 0 if col == "StockOptionLevel" else 1
        if not df[col].between(start, start + len(levels) - 1).all():
            raise ValueError(f"Invalid ordinal code in {col}.")
    if not df[ID_COLUMN].is_unique or (df[ID_COLUMN] <= 0).any():
        raise ValueError("EmployeeNumber must contain unique positive technical identifiers.")
    observed = {c: df[c].iloc[0] for c in df if df[c].nunique() == 1}
    if observed != CONSTANTS:
        raise ValueError("Unexpected constant columns or values.")
    counts = df["Attrition"].value_counts().to_dict()
    if counts != {"No": 1233, "Yes": 237}:
        raise ValueError("Unexpected target distribution for pinned version 1.")
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": 0,
        "duplicate_rows": 0,
        "unique_identifiers": True,
        "target_counts": counts,
        "constants": CONSTANTS,
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


def prepare_export(csv_bytes: bytes, cfg: DatasetConfig) -> tuple[pd.DataFrame, dict]:
    source = cfg.raw["source"]
    download_url(source)
    digest = hashlib.sha256(csv_bytes).hexdigest()
    if digest != source["sha256"]:
        raise ValueError("CSV SHA-256 differs from the pinned first-observation digest.")
    header = next(csv.reader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    if header != SOURCE_COLUMNS:
        raise ValueError("Unexpected source CSV header (including duplicate column names).")
    df = pd.read_csv(io.BytesIO(csv_bytes), encoding="utf-8-sig")
    report = validate_source(df)
    if ID_COLUMN in cfg.features or set(CONSTANTS) & set(cfg.columns):
        raise ValueError("Identifiers and constant columns cannot be predictors.")
    for col, levels in ORDINAL_LEVELS.items():
        start = 0 if col == "StockOptionLevel" else 1
        mapping = {i: f"{i}: {label}" for i, label in enumerate(levels, start)}
        df[col] = df[col].map(mapping)
    for col in cfg.numeric:
        df[col] = pd.to_numeric(df[col], errors="raise")
    cfg.validate_columns(df)
    result = df[[ID_COLUMN, *cfg.columns]].copy()
    report.update(
        {
            "source_sha256": digest,
            "export_columns": list(result.columns),
            "predictor_count": len(cfg.features),
        }
    )
    return result, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--from-file", type=Path, help="official version 1 ZIP or CSV, checked offline"
    )
    args = parser.parse_args()
    cfg = load_config()
    url = download_url(cfg.raw["source"])
    if args.from_file:
        with args.from_file.open("rb") as stream:
            content = stream.read(MAX_BYTES + 1)
    else:
        content = fetch_archive(url)
    csv_bytes = extract_csv(content, cfg.raw["source"]["filename"])
    df, report = prepare_export(csv_bytes, cfg)
    output = df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    report.update(
        {
            "dataset_ref": KAGGLE_REF,
            "version": 1,
            "download_url": url,
            "export_sha256": hashlib.sha256(output).hexdigest(),
            "integrity_anchor": "first observation; not independent authentication",
        }
    )
    out = Path(cfg.raw_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".csv.tmp")
    temporary.write_bytes(output)
    temporary.replace(out)
    out.with_suffix(".provenance.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Source: 1470 x 35; export: {len(df)} x {len(df.columns)} -> {out}")
    print(
        f"Predictors: {len(cfg.features)}; Attrition=Yes: 237/1470; "
        f"SHA-256: {report['export_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
