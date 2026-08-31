"""`START-HERE.md` stays runnable, and stays free of values it does not own.

The quickstart's whole value is that a junior can paste its blocks and have them
work. That makes it the same class of artefact as `docs/08-adopting.md` § 2.0,
and it earns the same treatment: the commands are **executed** here rather than
reimplemented, because a reimplementation is a second copy free to keep working
after the documented ones have stopped.

`docs/17-adopter-onboarding-review.md` § E is why the extraction check comes
first — a `grep -A4` that returned empty and exited zero survived for months in
a shipped file, and an assertion on the exit code alone would have passed it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT, a_register

START_HERE = REPO_ROOT / "START-HERE.md"
HOW_IT_WORKS = REPO_ROOT / "HOW-IT-WORKS.md"
TEXT = START_HERE.read_text(encoding="utf-8")

_FENCED_BASH = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_TABLE_ROW = re.compile(r"^\|(?!\s*[-: ]+\|)(.+)\|\s*$", re.MULTILINE)

#: A literal this document must not carry. The register owns every one of them,
#: and `tests/test_plugin.py` holds the same rule for `plugins/`.
_VERSION_LITERAL = re.compile(r"\b\d+\.\d+\.\d+\b")
_DIGEST_LITERAL = re.compile(r"\b[0-9a-f]{64}\b")


def test_both_root_documents_exist_and_link_each_other() -> None:
    """Neither is reachable without the other: one routes, one explains."""
    assert START_HERE.is_file() and HOW_IT_WORKS.is_file()
    assert "HOW-IT-WORKS.md" in TEXT, "START-HERE.md does not link the explanation"
    assert "START-HERE.md" in HOW_IT_WORKS.read_text(encoding="utf-8"), (
        "HOW-IT-WORKS.md does not route a reader who wants to adopt"
    )


def test_the_register_extraction_still_finds_its_values(tmp_path: Path) -> None:
    """Step 4's own commands, run against the real register.

    The network lines are cut the way `tests/test_devcontainer_placeholders.py`
    cuts them — the aarch64 digest is fetched from the release, and the pair the
    register holds is what a file test can settle.
    """
    blocks = [b for b in _FENCED_BASH.findall(TEXT) if "uv_block()" in b]
    assert len(blocks) == 1, f"expected one block defining uv_block(), found {len(blocks)}"
    lines = [
        line
        for line in blocks[0].splitlines()
        # The aarch64 digest is fetched from the release; a file test must not
        # depend on the network. Its `echo` dereferences the variable with `:?`,
        # so the line that sets it and the line that reads it go together.
        if "curl" not in line and "uv_sha_arm" not in line
    ]
    script = "\n".join(
        ["set -euo pipefail", *lines, 'printf "%s\\n%s\\n" "$uv_version" "$uv_sha_x86"']
    )
    shutil.copy(REPO_ROOT / "controls.yaml", tmp_path / "controls.yaml")
    result = subprocess.run(
        ["bash", "-c", script], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    version, sha = result.stdout.splitlines()
    uv = a_register().tools["uv"]
    assert version == uv.version, f"extracted {version!r}, register holds {uv.version!r}"
    assert sha == uv.sha256, "the extracted x86_64 digest is not the register's"


def test_no_block_reaches_the_checker_off_path() -> None:
    """ADR 0020, held for this file as `test_adopter_guide.py` holds it for the guide.

    A bare `register-check` resolves against `PATH` and would report success
    against some other copy entirely — the exact failure this standard describes
    for `npx --no-install`.
    """
    offenders = [
        line.strip()
        for block in _FENCED_BASH.findall(TEXT)
        for line in block.splitlines()
        if re.match(r"^\s*register-check\b", line)
    ]
    assert not offenders, f"reaches the checker off PATH: {offenders}"


def test_every_prerequisite_row_has_an_install_and_a_check() -> None:
    """A blank cell is how the gap this document exists to close happened.

    `docs/17-adopter-onboarding-review.md` § A: the route named seven tools and
    gave an install command for none of them.
    """
    section = TEXT.split("### B — Install these tools", 1)[1].split("\n### ", 1)[0]
    rows = [
        [c.strip() for c in row.split("|")]
        for row in _TABLE_ROW.findall(section)
    ]
    body = [r for r in rows if r and r[0] not in ("Tool", "")]
    assert len(body) >= 5, f"the prerequisites table has only {len(body)} rows"
    for row in body:
        tool, install, check = row[0], row[1], row[2]
        assert install, f"{tool} has no install cell"
        assert check, f"{tool} has no verification cell"


@pytest.mark.parametrize(
    ("pattern", "what"),
    [(_VERSION_LITERAL, "a version"), (_DIGEST_LITERAL, "a digest")],
)
def test_the_document_owns_no_value_another_file_owns(pattern: re.Pattern[str], what: str) -> None:
    """Rule 3 of the template: derive it or link to it, never copy it.

    The memory figure is deliberately exempt — 8 GB is a Docker Desktop setting
    this document is entitled to state, not a value the register pins.
    """
    hits = {m.group(0) for m in pattern.finditer(TEXT)}
    hits -= {"0.0", "1.1", "2.0", "4.2", "4.3"}  # section references
    assert not hits, f"START-HERE.md carries {what} it does not own: {sorted(hits)}"


def test_it_says_where_the_commands_run() -> None:
    """A junior asked "run step 1 from where?" and the document had no answer.

    Step 1 is directory-independent — `claude plugin install` writes only into
    `~/.claude/`. Every step after it writes into the working directory, so the
    wrong one leaves a register in the reader's home folder and a
    `.devcontainer/` nothing will use. Cheap to state, invisible when missing.
    """
    where = TEXT.split("### C — Get a repository, and stand in it", 1)
    assert len(where) == 2, "START-HERE.md no longer says where its commands run"
    section = where[1].split("\n### ", 1)[0]
    assert "cd " in section, "the section does not actually tell the reader to cd"


def test_it_handles_the_reader_who_has_no_repository_yet() -> None:
    """Measured on a real Mac: `git status` in an ordinary folder, and a dead end.

        nathan@Nathans-MacBook-Pro-3 git % git status
        fatal: not a git repository (or any of the parent directories): .git

    Everything from step 2 needs a repository *and* a GitHub remote — step 2
    commits the register, step 3 calls `gh api repos/OWNER/REPO/...`, SEC-001
    reads what git tracks and CI-001 reads what GitHub enforces. The guide
    assumed one and offered no route to getting one, so the first `git` command
    read as a broken instruction rather than a missing precondition.
    """
    where = TEXT.split("### C — Get a repository, and stand in it", 1)[1].split("\n### ", 1)[0]
    assert "not a git repository" in where, (
        "START-HERE.md does not name the error a reader without a repository actually sees"
    )
    assert "git init" in where and "gh repo create" in where, (
        "it diagnoses the missing repository but gives no route to having one"
    )
    assert "gh repo clone" in where, (
        "it covers the new-project case but not the far commoner one — a repository "
        "somebody else already set up"
    )


def test_it_names_the_session_file_that_must_not_be_committed() -> None:
    """`.claude/settings.local.json` holds per-developer state and may hold an `env`.

    The shipped template's `.gitignore` cannot carry the rule — it is copied to
    `.devcontainer/.gitignore`, where the path would resolve one directory down
    and ignore nothing — so the document is the only place it can be said.
    """
    assert ".claude/settings.local.json" in TEXT, (
        "START-HERE.md does not tell the reader to gitignore their local settings"
    )
    assert ".gitignore" in TEXT, "it names the file but not where the rule goes"


def test_the_step_overview_names_rights_rather_than_people() -> None:
    """A reader who is an admin does step 3 themselves.

    The first version headed this column "Needs anyone but you?" — a yes/no
    question whose cells answered with a noun — and the proposed replacement,
    "Who can do this?", reads as *not you* for a reader who holds the rights.
    Naming the right is accurate either way.
    """
    section = TEXT.split("## What you are about to do", 1)[1].split("\n## ", 1)[0]
    assert "Rights needed" in section, "the step overview no longer names rights"
    assert "Can you stop after" not in section, (
        "a column whose every cell read 'yes' has come back — it is one sentence, "
        "not a column"
    )
    assert "stop after any" in section, (
        "dropping the column also dropped the fact it carried"
    )


def test_no_command_block_carries_a_placeholder_to_fill_in() -> None:
    """Measured on a real Mac: the block was pasted verbatim, as promised.

        % gh api repos/OWNER/REPO/rulesets
        {"message": "Not Found", ... "status": "404"}

    The repeating unit promises "copy-pasteable as a block, no placeholders to
    think about", and step 3 shipped `OWNER/REPO`. `gh` resolves `{owner}` and
    `{repo}` from the local remote, so the promise is keepable rather than
    aspirational.

    `<owner>/<repo>` in angle brackets is allowed and is not the same thing: it
    appears only in `gh repo clone`, which by definition runs outside the
    repository it names, where nothing can resolve it.
    """
    for block in _FENCED_BASH.findall(TEXT):
        for token in ("OWNER/REPO", "repos/O/R", "/BRANCH"):
            assert token not in block, (
                f"a command block carries {token!r}, which a reader will paste verbatim"
            )


def test_the_platform_checks_look_up_the_default_branch() -> None:
    """`{branch}` resolves to the branch you are *on*, not the default one.

    The quieter half of the same finding. An adopter running step 3 from a
    feature branch gets `.protected: false` and an empty effective-rule list for
    a branch that is correctly protected — an answer shaped exactly like a real
    one. Measured here: `false` and `[]` from a feature branch, `true` and four
    rule types from the default.
    """
    step = TEXT.split("## 3 — The platform steps", 1)[1].split("\n## ", 1)[0]
    assert "default_branch" in step, (
        "step 3 does not look the default branch up — it will answer about "
        "whichever branch the reader happens to be on"
    )
    assert "/branches/{branch}" not in step, (
        "step 3 uses gh's {branch}, which resolves to the current branch"
    )


def test_the_private_repository_constraint_surfaces_before_the_work() -> None:
    """Two controls need a paid plan, and finding that out at step 3 wastes four steps.

    The same argument as § B of the review: a platform assumption belongs on the
    first screen, not at the point where it fails. And the section it points at
    must state today's behaviour — the checker *fails* these two rather than
    skipping them, so an adopter on a free private plan gets exit 1, not 3.
    """
    before = TEXT.split("## Before you start", 1)[1].split("\n## What you are about to do", 1)[0]
    assert "What your repository can support" in before, (
        "the plan constraint is not raised before the steps"
    )
    tail = TEXT.split("## If your plan has no rulesets", 1)
    assert len(tail) == 2, "there is no section explaining what a plan without rulesets costs"
    assert "exits `1`" in tail[1], (
        "the section does not say the checker fails these controls rather than skipping them"
    )


def test_the_plan_waiver_is_never_described_as_a_pass() -> None:
    """ADR 0047 rule 1, guarded in the document a reader acts from.

    This test began as its own inverse — it held that the guide must not read as
    though the mechanism existed while ADR 0047 was Proposed. The mechanism is
    now built, so the risk changed rather than went away: a waiver described as
    though it satisfied the control is worse than one described as unbuilt,
    because the reader stops looking for the gap.
    """
    section = TEXT.split("## If your plan has no rulesets", 1)[1]
    assert "UNAVAILABLE (plan)" in section, (
        "the guide does not tell a constrained reader what the report will say"
    )
    assert "not a pass" in section, (
        "the guide offers the waiver without saying the control still does not hold"
    )
    assert "review_by" in section and "fails the build" in section, (
        "the guide does not say the entry expires, which is what stops it being "
        "a permanent exemption"
    )


def test_it_says_where_the_checker_comes_from() -> None:
    """Reported from a real run: "register-check isn't available in claude".

    The guide named `uv run register-check` twice, both at the very end, and
    never said that step 5 installs it, that it is a command rather than a slash
    command, or that it runs inside the container. Three ways to be stuck, and
    the document distinguished none of them.
    """
    done = TEXT.split("## You are done when", 1)[1].split("\n## ", 1)[0]
    assert "Step 5 is what put the checker there" in done, (
        "the guide does not say where register-check comes from"
    )
    assert "not a slash command" in done, (
        "the guide does not head off the commonest reading — that it is a /command"
    )
    assert "inside the container" in done, "it does not say where to run it"


def test_the_python_constraint_is_raised_before_the_steps() -> None:
    """The checker installs as a Python dependency and only python declares the
    spelling. A non-Python adopter gets gates that enforce and no command that
    verifies — which decides whether the route is worth starting, so it belongs
    on the first screen rather than at the last one."""
    before = TEXT.split("## Before you start", 1)[1].split("\n## What you are about to do", 1)[0]
    assert "Is it a Python project?" in before, (
        "the ecosystem constraint is not raised before the work"
    )
    assert "0032" in before, "it states the limit without citing where it is recorded"


def test_step_three_branches_before_it_asks_for_anything() -> None:
    """Reported mid-run: nothing told a private-repo reader to skip to step 4.

    The first fix put that in **Done when**, which the reader reaches only after
    following the instruction to enable push protection — so they had already
    gone looking for a Settings page that does not exist on their plan. A branch
    that arrives after the work is not a branch.

    So the constrained path is the *first* thing in the step, and the test
    checks position rather than presence: the escape must come before the
    instruction it excuses the reader from.
    """
    step = TEXT.split("## 3 — The platform steps", 1)[1].split("\n## 4 ", 1)[0]
    skip = step.find("go to step 4")
    push_protection = step.find("enable secret-scanning push protection")
    assert skip != -1, "step 3 never tells a constrained reader where to go"
    assert push_protection != -1, "step 3 no longer names the one manual act"
    assert skip < push_protection, (
        "the skip-to-step-4 branch comes after the push-protection instruction, so a "
        "reader on a plan without it goes hunting for the setting first"
    )


def test_the_keychain_step_expects_an_existing_entry() -> None:
    """Reported mid-run, and it hits every second project on a machine:

        security: SecKeychainItemCreateFromContent (<default>): The specified
        item already exists in the keychain.

    The service names carry no project prefix on purpose — one credential store
    serves every ee project — so an existing entry is the expected state for
    anybody who has done this before, and `add-generic-password` refuses to
    overwrite. `docs/06-devcontainer-setup.md` has documented the delete-first
    rotation since Phase 0.5; the adopter route did not, which is § A's shape
    again: the contributor guide knows and the adopter guide does not.
    """
    step = TEXT.split("## 4 — The container", 1)[1].split("\n## 5 ", 1)[0]
    assert "find-generic-password" in step, (
        "step 4 does not let the reader check whether the credential is already set"
    )
    assert "will not overwrite" in step, (
        "step 4 does not warn that add-generic-password fails on an existing entry"
    )
    assert "delete-generic-password" in step, "step 4 gives no way to replace one"


def test_the_github_token_has_a_route_not_just_a_destination() -> None:
    """Asked mid-run: "where is the optional gh credential configured?"

    The table named the credential, its scope in three words, and the Keychain
    service — and nothing about creating it. § A's shape once more: a thing the
    reader needs, with no route to having it.

    The permissions are checked by name because `Administration: write` is the
    one people miss and it fails late — `gate-repo` stops at its pre-flight
    rather than writing half a deployment.
    """
    section = TEXT.split("#### Creating the GitHub token", 1)
    assert len(section) == 2, "there is no section on creating the token"
    body = section[1].split("\n## ", 1)[0]
    for needed in ("fine-grained", "Only select repositories", "Metadata", "Contents"):
        assert needed in body, f"the token section does not mention {needed!r}"
    assert "Administration" in body and "Read and write" in body, (
        "the section does not say Administration must be writable, which gate-repo needs"
    )
    assert "add-generic-password" in body, "it says what to create and not where to put it"
    assert "find-generic-password" in body, "it gives no way to check the token works"


def test_it_does_not_ask_for_three_github_tokens() -> None:
    """Working out how to document the `gh` token showed the table implied three.

    There are two. One lives in the Keychain and is used by the reader *and by
    the gates* from inside the container — `gate-repo` reads it from the same
    env-file, so it is the admin token rather than a separate one. The other
    goes to Actions and never leaves the platform.
    """
    before = TEXT.split("### E — Get these credentials", 1)[1].split("\n#### ", 1)[0]
    assert "Two GitHub tokens, not three" in before, (
        "the credentials table no longer states how many GitHub tokens are needed"
    )


def test_preparation_comes_before_the_thing_it_prepares_for() -> None:
    """Reported by a reader starting again: "how do I run § Is your repository
    private? when I have not created the repository yet?"

    The section asked a question about a repository, and the section that gets
    you a repository was two headings further down, past the credentials and the
    step overview. For a reader new to software engineering there is nothing to
    infer from — the commands simply fail.

    The fix is ordering, so the test is ordering: get a repository, then ask
    what it can support, then get credentials for it.
    """
    get_repo = TEXT.index("### C — Get a repository")
    can_support = TEXT.index("### D — What your repository can support")
    credentials = TEXT.index("### E — Get these credentials")
    first_step = TEXT.index("## 1 — Install the plugin")
    assert get_repo < can_support, (
        "the guide asks what the repository can support before telling the reader "
        "how to have one"
    )
    assert can_support < credentials < first_step, (
        "preparation is out of order — each of A to E is needed by the one after it"
    )


def test_the_preparation_letters_do_not_collide_with_the_step_numbers() -> None:
    """A to E prepare, 1 to 6 do the work. Numbering both 1..n gave a reader two
    different things called "step 3"."""
    before = TEXT.split("## Before you start", 1)[1].split("\n## What you are about to do", 1)[0]
    for letter in "ABCDE":
        assert f"### {letter} — " in before, f"preparation step {letter} is missing"
    assert "### 1 — " not in before, (
        "a preparation heading is numbered, which collides with the six steps below"
    )


def test_getting_a_repository_handles_a_second_attempt() -> None:
    """Reported by a reader recreating a repository they had made before:

        warning: re-init: ignored --initial-branch=main
        GraphQL: Name already exists on this account (createRepository)

    The block assumed a clean slate. `git init` in an existing repository
    silently ignores `-b main` — so a repository whose branch is not `main` stays
    that way while the reader believes otherwise — and `gh repo create` fails
    outright on a name already taken.

    It also hardcoded `my-project` in three places, so a reader working in a
    directory of any other name would have created a GitHub repository whose name
    did not match their folder. That is the OWNER/REPO shape again: a literal in
    a block the document promises is copy-pasteable.
    """
    section = TEXT.split("### C — Get a repository", 1)[1].split("\n### ", 1)[0]
    assert "Name already exists on this account" in section, (
        "the section does not name the error a second attempt produces"
    )
    assert "git remote add origin" in section, (
        "it diagnoses the collision but gives no way out of it"
    )
    assert "Do not run a block that does not match" in section, (
        "the section offers several blocks without telling the reader to pick one"
    )
    assert 'basename "$PWD"' in section, (
        "the repository name is still a literal rather than derived from the "
        "directory, so the two can disagree"
    )
