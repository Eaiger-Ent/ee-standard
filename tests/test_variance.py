"""Direction classification, and the three cases where it declines.

[ADR 0040](../docs/adr/0040-a-declined-classification-is-a-verdict.md).
`01-register-schema.md` § `variance` has named three cases since Phase 0 where
the answer is `UNCLASSIFIED` rather than a guess. These tests hold each of them
as a *verdict the mechanism produces* rather than a path it falls through, which
is the whole difference: a classifier that answers "narrowing" when it does not
know launders a guess into a report, and the reader cannot tell the two apart.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from conftest import a_register, make_repo, register_with
from register_check.cli import main
from register_check.variance import (
    NO_POLARITY,
    NOT_DECLARATIVE,
    REPLACED,
    SHAPE_CHANGED,
    UNREADABLE,
    Direction,
    build_variance,
    classify_file,
    gated_configs,
    render_variance,
)

POLARITY = {"line_length": "lower", "floor": "higher", "strict": "true", "allow_dirty": "false"}


def _yaml(path: str, before: str, after: str, polarity: dict[str, str] | None = None) -> Any:
    return classify_file(path, before, after, POLARITY if polarity is None else polarity)


# --- the two directions ----------------------------------------------------


def test_a_rule_added_is_a_narrowing() -> None:
    delta = _yaml("c.yaml", "rules:\n  A: true\n", "rules:\n  A: true\n  B: true\n")
    assert delta.direction is Direction.NARROWING
    assert "added B" in str(delta.keys[0])


def test_a_rule_removed_is_a_loosening() -> None:
    delta = _yaml("c.yaml", "rules:\n  A: true\n  B: true\n", "rules:\n  A: true\n")
    assert delta.direction is Direction.LOOSENING
    assert "removed B" in str(delta.keys[0])


@pytest.mark.parametrize(
    ("key", "before", "after", "expected"),
    [
        ("line_length", 250, 100, Direction.NARROWING),
        ("line_length", 100, 250, Direction.LOOSENING),
        ("floor", 80, 90, Direction.NARROWING),
        ("floor", 90, 80, Direction.LOOSENING),
        ("strict", "false", "true", Direction.NARROWING),
        ("strict", "true", "false", Direction.LOOSENING),
        ("allow_dirty", "true", "false", Direction.NARROWING),
        ("allow_dirty", "false", "true", Direction.LOOSENING),
    ],
)
def test_a_scalar_moves_the_way_the_register_says(
    key: str, before: object, after: object, expected: Direction
) -> None:
    """Both polarities and both value kinds, because a sign error passes one half.

    A classifier that had `lower` and `higher` the wrong way round would still
    return a direction for every case, and half of them would be wrong — which
    is the failure ADR 0040 names as worse than declining.
    """
    delta = _yaml("c.yaml", f"{key}: {before}\n", f"{key}: {after}\n")
    assert delta.direction is expected, delta.keys


# --- the three declining cases --------------------------------------------


def test_case_one_a_member_replaced_by_a_differently_named_one() -> None:
    """`01-register-schema.md`'s first case, and the reason it cannot be guessed.

    Whether `ISORT` covers what `I` covered is a fact about the tool's rule
    catalogue. Nothing in the config says so, and reading the rename as a wash
    would let a rule be dropped under cover of one being added.
    """
    delta = _yaml("c.yaml", "rules:\n  I: true\n", "rules:\n  ISORT: true\n")
    assert delta.direction is Direction.UNCLASSIFIED
    assert REPLACED in str(delta.keys[0])
    assert "added ISORT" in str(delta.keys[0]) and "removed I" in str(delta.keys[0])


def test_case_two_a_threshold_whose_polarity_the_register_does_not_give() -> None:
    """The second case, and the one a repository can close for itself.

    The message says the register gives no polarity, rather than saying the
    change is unknowable — because a one-line register edit makes it knowable,
    and a reader has to be able to tell that from the case that has no fix.
    """
    delta = _yaml("c.yaml", "some_limit: 5\n", "some_limit: 9\n")
    assert delta.direction is Direction.UNCLASSIFIED
    assert NO_POLARITY in str(delta.keys[0])
    assert "5" in str(delta.keys[0]) and "9" in str(delta.keys[0])


def test_case_two_closes_when_the_register_names_the_key() -> None:
    """The same delta, classified — so the message above is a fixable state."""
    delta = _yaml("c.yaml", "some_limit: 5\n", "some_limit: 9\n", {"some_limit": "higher"})
    assert delta.direction is Direction.NARROWING


def test_case_three_a_config_that_is_executable_code() -> None:
    """The third case, and the only one that is a property of the file itself.

    A program's effective settings are whatever it computes at run time, so
    there is no delta of one kind to read — and the whole file declines rather
    than each key, because there are no keys.
    """
    delta = classify_file(
        "eslint.config.js", "module.exports = {a: 1}\n", "module.exports = {a: 2}\n", POLARITY
    )
    assert delta.direction is Direction.UNCLASSIFIED
    assert delta.whole_file is not None
    assert NOT_DECLARATIVE in delta.whole_file.detail
    assert delta.keys == ()


def test_a_config_that_will_not_parse_declines_and_says_so() -> None:
    """Not one of the three, and not a crash either."""
    delta = _yaml("c.yaml", "a: 1\n", "a: [unclosed\n")
    assert delta.direction is Direction.UNCLASSIFIED
    assert delta.whole_file is not None and UNREADABLE in delta.whole_file.detail


def test_a_value_that_changes_shape_declines() -> None:
    delta = _yaml("c.yaml", "line_length: 100\n", "line_length: off\n")
    assert delta.direction is Direction.UNCLASSIFIED
    assert SHAPE_CHANGED in str(delta.keys[0])


def test_a_boolean_is_not_a_number_however_python_feels_about_it() -> None:
    """`isinstance(False, int)` is `True`, and it produced a wrong direction.

    YAML reads `off` as `False`, so a ceiling of 100 turned off compared as
    `False < 100` and reported a **narrowing** — a relaxation dressed as a
    tightening, which is the single outcome ADR 0040 exists to prevent. Found by
    the test above before the code shipped; kept as its own case because the
    cause is the language rather than the design, and a future refactor could
    reintroduce it without touching anything this file otherwise covers.
    """
    for spelling in ("off", "false", "true", "on"):
        delta = _yaml("c.yaml", "line_length: 100\n", f"line_length: {spelling}\n")
        assert delta.direction is Direction.UNCLASSIFIED, spelling


# --- the ordering ----------------------------------------------------------


def test_a_mixed_delta_is_a_loosening_not_a_wash() -> None:
    """ADR 0040 point 4, and the reason the enum carries the order.

    One key tightens and another relaxes. Averaging them reports a change that
    weakens a control as though nothing had happened, which is how a weakening
    gets merged under a green line.
    """
    delta = _yaml(
        "c.yaml",
        "line_length: 250\nfloor: 90\n",
        "line_length: 100\nfloor: 80\n",
    )
    assert {k.direction for k in delta.keys} == {Direction.NARROWING, Direction.LOOSENING}
    assert delta.direction is Direction.LOOSENING


def test_a_narrowing_beside_an_unclassified_is_unclassified() -> None:
    delta = _yaml(
        "c.yaml", "line_length: 250\nsome_limit: 5\n", "line_length: 100\nsome_limit: 9\n"
    )
    assert delta.direction is Direction.UNCLASSIFIED


# --- sections and files ----------------------------------------------------


def test_a_section_narrows_what_is_read() -> None:
    """`pyproject.toml` holds every tool; a gate's delta is its own table's."""
    before = '[tool.ruff]\nline_length = 250\n[tool.other]\nx = 1\n'
    after = '[tool.ruff]\nline_length = 250\n[tool.other]\nx = 2\n'
    assert classify_file(
        "pyproject.toml", before, after, POLARITY, "tool.ruff"
    ).direction is Direction.UNCHANGED
    assert classify_file(
        "pyproject.toml", before, after, POLARITY, "tool.other"
    ).direction is Direction.UNCLASSIFIED


def test_a_glob_is_expanded_against_the_files_git_can_see(tmp_path: Path) -> None:
    """A `config.file` may be a pattern — eslint's is — and a pattern is not a path.

    Passing it through was the first thing this command did wrong:
    `git show <ref>:.eslintrc*` does not fail, it resolves the argument as a
    revision and prints the commit, so two commit messages were classified as
    configuration.
    """
    register = a_register()
    present = {".eslintrc.json", "pyproject.toml", "README.md"}
    found = dict(gated_configs(register, present))
    assert ".eslintrc.json" in found
    assert not any("*" in path for path in found), found


def test_a_pattern_matching_nothing_contributes_nothing() -> None:
    found = gated_configs(a_register(), {"pyproject.toml"})
    assert all("eslint" not in path for path, _ in found), found


def test_a_file_absent_at_the_base_is_new_rather_than_unchanged() -> None:
    """An absent baseline and an identical baseline are different answers."""
    report = build_variance(
        lambda p: None, lambda p: "line_length: 100\n", a_register(), [("new.yaml", None)]
    )
    assert report.missing_baseline == ["new.yaml"]
    assert report.files == []
    assert "NEW" in render_variance(report, "HEAD")


# --- the register is the authority ----------------------------------------


def test_polarity_comes_from_the_register_and_not_from_this_module(tmp_path: Path) -> None:
    """Only the register moves, and the verdict moves with it.

    A polarity table held privately in the checker would pass the happy path and
    fail here — which is ADR 0018's boundary test written as a test.
    """
    def flip(document: dict[str, Any]) -> None:
        document["variance"]["polarity"]["line_length"] = "higher"

    flipped = register_with(tmp_path, flip)
    assert a_register().variance_polarity["line_length"] == "lower"
    assert flipped.variance_polarity["line_length"] == "higher"
    args = ("c.yaml", "line_length: 250\n", "line_length: 100\n")
    assert classify_file(*args, a_register().variance_polarity).direction is Direction.NARROWING
    assert classify_file(*args, flipped.variance_polarity).direction is Direction.LOOSENING


def test_a_polarity_the_classifier_cannot_act_on_is_a_schema_error(tmp_path: Path) -> None:
    """Validated at load, because a bad polarity surfaces as a wrong direction.

    Every other failure mode here is loud. This one would report a loosening as
    a narrowing, which is the single outcome ADR 0040 exists to prevent, so it
    has to fail before a verdict is computed rather than after.
    """
    from register_check.register import load_register

    document = (Path("controls.yaml")).read_text(encoding="utf-8")
    broken = document.replace("line_length: lower", "line_length: smaller")
    path = tmp_path / "controls.yaml"
    path.write_text(broken, encoding="utf-8")
    register, errors = load_register(path)
    assert register is None
    assert any("variance.polarity.line_length" in e.field for e in errors), errors


def test_an_unquoted_yaml_boolean_polarity_is_accepted(tmp_path: Path) -> None:
    """`strict: true` is a YAML boolean, and it is the value the author meant.

    Rejecting it would fail a register whose intent is unambiguous, over a
    quoting rule nothing else in this file has.
    """
    def unquote(document: dict[str, Any]) -> None:
        document["variance"]["polarity"]["strict"] = True

    assert register_with(tmp_path, unquote).variance_polarity["strict"] == "true"


# --- the command -----------------------------------------------------------


def _repo(tmp_path: Path, first: dict[str, str], then: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    make_repo(root, first)
    for rel, text in then.items():
        (root / rel).write_text(text, encoding="utf-8")
    return root


def _run(root: Path, capsys: pytest.CaptureFixture[str], *extra: str) -> tuple[int, str]:
    code = main(
        [
            "--repo", str(root),
            "--register", str(Path("controls.yaml").resolve()),
            "variance", "--against", "HEAD", *extra,
        ]
    )
    return code, capsys.readouterr().out


_PY = "[tool.ruff]\nline-length = 100\n[tool.mypy]\nstrict = true\n"
_BASE = {"pyproject.toml": _PY}


def test_the_command_exits_zero_when_nothing_moved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run(_repo(tmp_path, _BASE, {}), capsys)
    assert code == 0
    assert "no gated configuration moved" in out


def test_the_command_exits_one_on_a_loosening(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(
        tmp_path,
        _BASE,
        {"pyproject.toml": _PY.replace("line-length = 100", "line-length = 200")},
    )
    code, out = _run(root, capsys)
    assert code == 1
    assert "LOOSENING" in out and "line-length" in out


def test_the_command_exits_three_when_it_declines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR 0016's vocabulary, unchanged: 3 is *could not be verified*."""
    # A key that *changed*, not one that was added: adding a setting is a
    # membership delta and classifies as a narrowing. The declining case is a
    # value moving with no polarity to move it against.
    root = _repo(
        tmp_path,
        {"pyproject.toml": _PY.replace("line-length = 100", "line-length = 100\nunknown = 1")},
        {"pyproject.toml": _PY.replace("line-length = 100", "line-length = 100\nunknown = 2")},
    )
    code, out = _run(root, capsys)
    assert code == 3
    assert "UNCLASSIFIED" in out


def test_a_base_that_is_not_a_revision_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With no baseline there is no delta — which is not 'nothing moved'."""
    root = _repo(tmp_path, _BASE, {})
    code = main(
        [
            "--repo", str(root),
            "--register", str(Path("controls.yaml").resolve()),
            "variance", "--against", "no-such-ref",
        ]
    )
    assert code == 2
    assert "no baseline" in capsys.readouterr().err


def test_an_extra_path_is_classified_too(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--path` reaches gated config the register's `stacks:` does not name.

    DOC-001's markdown config is the case: it is `lint-md`'s control, in another
    plugin, so no `stacks.<stack>.gates.<role>.config` entry names it.
    """
    root = _repo(
        tmp_path,
        {**_BASE, ".markdownlint.yaml": "MD013:\n  line_length: 250\n"},
        {".markdownlint.yaml": "MD013:\n  line_length: 400\n"},
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    code, out = _run(root, capsys, "--path", ".markdownlint.yaml")
    assert code == 1
    assert "MD013.line_length" in out
