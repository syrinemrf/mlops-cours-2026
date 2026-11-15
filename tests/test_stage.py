"""pipelines/stage.py : une étape en échec garde ses rapports (gates du Lab 3)."""

import subprocess
import sys

import pytest

from pipelines import stage


def test_failed_stage_still_copies_reports(tmp_path, monkeypatch):
    def failing(module, args, work, env=None):
        (work / "reports").mkdir()
        (work / "reports" / "gate.json").write_text('{"success": false}')
        raise subprocess.CalledProcessError(1, [sys.executable, "-m", module])

    monkeypatch.setattr(stage, "execute", failing)
    dst, missing = tmp_path / "gate.json", tmp_path / "absent.html"
    with pytest.raises(subprocess.CalledProcessError):
        stage.run_stage(
            "src.gate", outputs={"reports/gate.json": dst, "reports/absent.html": missing}
        )
    assert dst.read_text() == '{"success": false}'
    assert not missing.exists()


def test_successful_stage_copies_outputs(tmp_path, monkeypatch):
    def ok(module, args, work, env=None):
        (work / "out.txt").write_text("ok")

    monkeypatch.setattr(stage, "execute", ok)
    stage.run_stage("src.ok", outputs={"out.txt": tmp_path / "out.txt"})
    assert (tmp_path / "out.txt").read_text() == "ok"
