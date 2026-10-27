"""Registry diagnostics require real DVC/data identities, independently of run names."""

from types import SimpleNamespace as NS

import pytest

from src.verify_registry import validate_run_lineage


@pytest.mark.parametrize("defect", [None, "run", "protocol", "dataset", "hash", "launcher"])
def test_champion_lineage_rejects_incompatible_run(defect):
    run = NS(
        info=NS(run_id="dvc-run", status="FINISHED"),
        data=NS(
            tags={
                "protocol": "A",
                "protocol_id": "mlops_A_v1",
                "dataset": "hr",
                "data_md5": "data-hash",
                "launched_by": "dvc",
            }
        ),
    )
    if defect == "run":
        run.info.run_id = "grid-run"
    elif defect:
        field = {"hash": "data_md5", "launcher": "launched_by"}.get(defect, defect)
        run.data.tags[field] = "different"
    if defect:
        with pytest.raises(ValueError):
            validate_run_lineage(run, NS(name="hr"), "data-hash", "dvc-run", True)
    else:
        validate_run_lineage(run, NS(name="hr"), "data-hash", "dvc-run", True)
