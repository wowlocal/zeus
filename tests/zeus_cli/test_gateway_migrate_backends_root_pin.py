"""Every printed step targets the dry run's own home, also under a Zeus root other than ~/.zeus.

``zeus -p NAME`` resolves NAME against the root the shell's own ZEUS_HOME names
(``profiles.resolve_profile_env``), so a home under ``ZEUS_HOME=/srv/team-zeus`` must pin that root, or the
steps would act on the user's ordinary ~/.zeus. The printed line runs through ``/bin/sh`` here, with a fake
``zeus`` that resolves its ``-p`` the way the real CLI does and prints the home it lands in.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from zeus_cli import gateway_migrate_backends_plan as plan
from zeus_cli import gateway_migrate_backends_windows as win

_POSIX = pytest.mark.platforms("linux", "macos")  # runs the printed line through /bin/sh

_REPO = Path(__file__).resolve().parents[2]
_FAKE = """#!{python}
import json, os, sys
sys.path.insert(0, {repo!r})
from zeus_cli.profiles import resolve_profile_env
args = sys.argv[1:]
name = args[args.index("-p") + 1] if "-p" in args else None
home = resolve_profile_env(name) if name else os.environ.get("ZEUS_HOME")
print(json.dumps({{"home": home, "args": args}}))
"""


@pytest.fixture
def team_root(tmp_path, monkeypatch):
    """A user whose standard root is ~/.zeus, and a team root with a space and a quote in its path."""
    user = tmp_path / "user"
    (user / ".zeus").mkdir(parents=True)
    root = tmp_path / "team's zeus root"
    for home in (root, root / "profiles" / "work"):
        home.mkdir(parents=True)
        (home / "config.yaml").write_text("model:\n  default: fake\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(user))
    monkeypatch.setenv("ZEUS_HOME", str(root))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "zeus"
    fake.write_text(_FAKE.format(python=sys.executable, repo=str(_REPO)), encoding="utf-8")
    fake.chmod(0o755)
    return SimpleNamespace(user=user, root=root, bin=bin_dir)


def _run(line: str, env_home: Path, bin_dir: Path) -> dict:
    """*line* as a user types it in a fresh shell: their HOME, no ZEUS_HOME of their own."""
    env = {k: v for k, v in os.environ.items() if k != "ZEUS_HOME"}
    env.update(HOME=str(env_home), PATH=f"{bin_dir}{os.pathsep}{env.get('PATH', '')}")
    done = subprocess.run(["/bin/sh", "-c", line], env=env, cwd=env_home, capture_output=True, text=True,
                          timeout=60, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


@_POSIX
@pytest.mark.parametrize("profile", ["default", "work"])
def test_a_printed_step_under_another_root_runs_against_that_home(team_root, profile):
    home = team_root.root if profile == "default" else team_root.root / "profiles" / "work"

    line = f"{plan.zeus_command(str(home))} gateway status"
    ran = _run(line, team_root.user, team_root.bin)

    assert Path(ran["home"]) == home, line
    assert ran["args"] == ["-p", profile, "gateway", "status"]


@_POSIX
def test_every_by_hand_zeus_step_runs_against_that_home(team_root):
    home = team_root.root / "profiles" / "work"
    item = SimpleNamespace(supervisor="systemd", scope="user", unit="zeus-dashboard.service", pid=None)

    steps = [s for s in plan.manual_steps("127.0.0.1", 9119, item, env_keys=(), home=str(home))
             if not s.startswith("#") and "zeus -p" in s]

    assert steps, steps
    for step in steps:
        assert Path(_run(step, team_root.user, team_root.bin)["home"]) == home, step


@_POSIX
def test_the_standard_root_needs_no_pin(team_root, monkeypatch):
    work = team_root.user / ".zeus" / "profiles" / "work"
    work.mkdir(parents=True)
    (work / "config.yaml").write_text("model:\n  default: fake\n", encoding="utf-8")
    monkeypatch.delenv("ZEUS_HOME")

    assert plan.zeus_command(str(work)) == "zeus -p work"
    assert plan.zeus_command(str(team_root.user / ".zeus")) == "zeus -p default"


def _ps_unquote(literal: str) -> str:
    """The value of a PowerShell single-quoted string: each doubled quote mark (', ‘, ’, ‚, ‛) is one."""
    assert literal[0] == "'" and literal[-1] == "'"
    body, out, i = literal[1:-1], [], 0
    while i < len(body):
        out.append(body[i])
        if body[i] in "'\u2018\u2019\u201a\u201b":
            assert body[i + 1] == body[i], literal  # an undoubled quote would end the string
            i += 1
        i += 1
    return "".join(out)


@pytest.mark.parametrize("root", ["C:\\Teams\\team's zeus root", "C:\\Teams\\o\u2019brien $x $(Get-Date)"])
def test_the_windows_pin_is_one_powershell_single_quoted_string(root):
    line = plan.pin_zeus_home(root, "zeus -p work", powershell=True)

    assert line.startswith("$env:ZEUS_HOME=") and line.endswith("'; zeus -p work")
    assert _ps_unquote(line[len("$env:ZEUS_HOME="):-len("; zeus -p work")]) == root


@_POSIX  # the team root is a POSIX path here; the pin's quoting is tested above on any host
def test_the_windows_recipe_pins_the_root_on_every_zeus_line(team_root):
    home = str(team_root.root / "profiles" / "work")
    item = SimpleNamespace(supervisor="scheduled-task", unit="Zeus Dashboard", unit_path=None, pid=11)

    steps = win.manual_steps("127.0.0.1", 9119, item, home=home)

    pin = plan.pin_zeus_home(team_root.root, "zeus -p work", powershell=True)
    commands = [s for s in steps if not s.startswith("#") and "zeus" in s]
    assert commands and all(s.startswith(pin + " ") for s in commands), steps
    assert steps[0].startswith("# ") and "PowerShell" in steps[0]


@_POSIX
def test_the_windows_status_branch_still_reads_as_three_pinned_commands(team_root):
    from tests.zeus_cli.test_gateway_migrate_backends_steps_wording import _groups
    home = str(team_root.root / "profiles" / "work")
    item = SimpleNamespace(supervisor="scheduled-task", unit="Zeus Dashboard", unit_path=None, pid=11)

    groups = _groups(win.manual_steps("127.0.0.1", 9119, item, home=home))

    pin = plan.pin_zeus_home(team_root.root, "zeus -p work", powershell=True)
    assert [command for _quoted, command in groups] == [f"{pin} gateway {verb}"
                                                        for verb in ("install", "start", "restart")]


def _make_homes(root: Path) -> Path:
    for home in (root, root / "profiles" / "work"):
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.yaml").write_text("model:\n  default: fake\n", encoding="utf-8")
    return root / "profiles" / "work"


@_POSIX
@pytest.mark.parametrize("profile", ["default", "work"])
def test_a_root_nested_inside_the_standard_root_is_pinned(team_root, monkeypatch, profile):
    """~/.zeus/team/profiles/work: `zeus -p work` alone would select ~/.zeus/profiles/work."""
    nested = team_root.user / ".zeus" / "team"
    work = _make_homes(nested)
    _make_homes(team_root.user / ".zeus")  # the profile a bare `-p work` would wrongly pick
    home = nested if profile == "default" else work
    monkeypatch.setenv("ZEUS_HOME", str(home))

    line = f"{plan.zeus_command(str(home))} gateway status"

    assert line.startswith("ZEUS_HOME="), line
    assert Path(_run(line, team_root.user, team_root.bin)["home"]) == home, line


@_POSIX
@pytest.mark.parametrize("profile", ["default", "work"])
def test_a_relative_root_is_pinned_as_an_absolute_path(team_root, tmp_path, monkeypatch, profile):
    """`ZEUS_HOME=team` means another directory in a fresh shell, which starts in the user's home."""
    cwd = tmp_path / "where the dry run ran"
    _make_homes(cwd / "team")
    monkeypatch.chdir(cwd)
    monkeypatch.setenv("ZEUS_HOME", "team")
    home = "team" if profile == "default" else "team/profiles/work"

    line = f"{plan.zeus_command(home)} gateway status"

    assert line.startswith(f"ZEUS_HOME={shlex.quote(str(cwd / 'team'))} "), line
    assert Path(_run(line, team_root.user, team_root.bin)["home"]) == cwd / home, line


@_POSIX
def test_a_path_that_resolves_to_the_standard_root_is_not_pinned(team_root, tmp_path, monkeypatch):
    alias = tmp_path / "alias-of-standard-root"
    alias.symlink_to(team_root.user / ".zeus")
    monkeypatch.setenv("ZEUS_HOME", str(alias))

    assert plan.zeus_command(str(alias)) == "zeus -p default"


def test_the_windows_owner_blocker_prints_the_powershell_pin(team_root):
    home = team_root.root / "profiles" / "work"
    host = SimpleNamespace(home=home, gateway_owner=lambda: ("unknown", None), os_family=lambda: "win32")

    problem = plan._owner_problem(host)

    pin = plan.pin_zeus_home(team_root.root, "zeus -p work", powershell=True)
    assert f"({pin} gateway status)" in problem, problem
    assert "ZEUS_HOME=" not in problem.replace("$env:ZEUS_HOME=", ""), problem


@pytest.mark.parametrize("powershell", [True, False])
def test_every_message_naming_a_zeus_command_follows_the_host_shell(team_root, powershell):
    """The plan's own messages (outside the printed recipes) pin the root in the host's shell: the
    stray-gateway blocker, the gateway line for systemd and launchd, and the owner blocker."""
    home = team_root.root / "profiles" / "work"
    pin = plan.pin_zeus_home(team_root.root, "zeus -p work", powershell=powershell)
    texts = {}
    for kind in ("systemd", "launchd"):
        p = plan.BackendPlan(home=str(home), powershell=powershell)
        state = {"kind": kind, "installed": False, "active": False, "running_pid": 77, "unit": None}
        host = SimpleNamespace(gateway_state=lambda state=state: state, linger=lambda: None,
                               gateway_preflight=lambda: None)
        plan._gateway(p, host)
        texts[f"{kind} stray gateway"] = (" ".join(p.blockers), f"({pin} gateway stop)")
        texts[f"{kind} gateway line"] = (plan._gateway_line(p), f"({pin} gateway install;")
    owner = SimpleNamespace(home=home, gateway_owner=lambda: ("unknown", None),
                            os_family=lambda: "win32" if powershell else "linux")
    texts["owner"] = (plan._owner_problem(owner), f"({pin} gateway status)")

    for where, (text, command) in texts.items():
        assert command in text, (where, text)
        if powershell:
            assert "ZEUS_HOME=" not in text.replace("$env:ZEUS_HOME=", ""), (where, text)
        else:
            assert "$env:" not in text, (where, text)
