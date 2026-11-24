"""A dashboard-spawned ``zeus -p <other> ...`` child keeps the launch environment's
launch-only keys (#135200). The named-profile scrub drops every key the root/home ``.env``
names, but a launch-only key is never loaded from ``.env``: the value in ``os.environ`` is the
administrator's, so a planted ``ZEUS_MANAGED_DIR=`` line must not remove it from the child.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("planted_name", ["ZEUS_MANAGED_DIR", "zeus_managed_dir"])
def test_planted_dotenv_line_does_not_strip_launch_managed_dir(tmp_path, monkeypatch, planted_name):
    root = tmp_path / "zeus"
    (root / "profiles" / "other").mkdir(parents=True)
    (root / "profiles" / "other" / "config.yaml").write_text("{}\n")
    (root / ".env").write_text(f"{planted_name}={tmp_path}/planted\nFOO_RESIDUE=1\n", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("ZEUS_HOME", str(root))
    monkeypatch.setenv("ZEUS_MANAGED_DIR", "/etc/org-policy")
    monkeypatch.setenv("FOO_RESIDUE", "1")
    import zeus_constants
    monkeypatch.setattr(zeus_constants, "_default_zeus_root_memo", None)

    from zeus_cli.web_server_gateway import _profile_action_environment

    env = _profile_action_environment(["-p", "other", "gateway", "status"])
    assert env["ZEUS_HOME"] == str(root / "profiles" / "other")
    assert env.get("ZEUS_MANAGED_DIR") == "/etc/org-policy"
    assert "FOO_RESIDUE" not in env  # ordinary launch .env residue is still dropped
