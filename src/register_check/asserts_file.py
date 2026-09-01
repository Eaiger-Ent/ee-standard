"""File-shaped assertions: a file exists and matches a shape.

One implementation, many callers — the checker runs these directly, and the
Phase-2 gate skills verify their own deployments through the same functions
rather than a private copy (docs/02-skill-family.md § The gates).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

from register_check.predicates import compile_predicate
from register_check.provenance import EXPECTED, stamps_by_file
from register_check.repo import Repo, git, load_jsonc

if TYPE_CHECKING:  # `register` imports the assert registries — importing it
    from register_check.register import Ecosystem, Gate, Register, Stack  # at runtime: circular


@dataclass(frozen=True)
class AssertResult:
    passed: bool
    message: str


# Asserts take the register as well as the repository, from contract 3. A rule
# that decides a verdict belongs in the register (ADR 0018), so an assert that
# cannot read the register would have nowhere to read the rule from — which is
# how the checker became a second source of truth in the first place.
AssertFn = Callable[[Repo, "Register", Mapping[str, object]], AssertResult]

#: The one key in that mapping the register did not write. The runner adds the
#: id of the control whose verify block is running, because an assert that reads
#: a stamp back has to know *whose* stamp and the block already sits inside the
#: control that answers it. It is evaluation context, not a rule — and the
#: schema rejects a register that supplies the key itself, since a control's own
#: id written into its own entry is a second copy of it (ADR 0018).
CONTROL_ARG = "control"

#: The placeholder a `lock_entry` pattern carries in place of the package name.
#: Substituted rather than `str.format`-ed, because a regular expression is full
#: of braces — `\d{2}` would be a formatting error — and the register writes
#: regular expressions in three other fields already. It lives here beside
#: CONTROL_ARG for the same reason: the register imports this module, never the
#: reverse.
PACKAGE_PLACEHOLDER = "{package}"


def substitute_package(pattern: str, package: str) -> str:
    """A `lock_entry` pattern with the package name substituted, regex-escaped."""
    return pattern.replace(PACKAGE_PLACEHOLDER, re.escape(package))



def _ok(message: str) -> AssertResult:
    return AssertResult(True, message)


def _fail(message: str) -> AssertResult:
    return AssertResult(False, message)


def precommit_hook_present(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    hook_id = str(args.get("id", ""))
    if not hook_id:
        return _fail("assert requires an 'id' argument naming the hook")
    if not repo.exists(".pre-commit-config.yaml"):
        return _fail(".pre-commit-config.yaml does not exist")
    config = yaml.safe_load(repo.read(".pre-commit-config.yaml"))
    if not isinstance(config, dict):
        return _fail(".pre-commit-config.yaml is not a mapping")
    for repo_block in config.get("repos") or []:
        if not isinstance(repo_block, dict):
            continue
        for hook in repo_block.get("hooks") or []:
            if isinstance(hook, dict) and hook.get("id") == hook_id:
                return _ok(f"pre-commit hook '{hook_id}' is configured")
    return _fail(f"no pre-commit hook with id '{hook_id}' in .pre-commit-config.yaml")


def _ecosystems_present(repo: Repo, register: Register) -> dict[str, Ecosystem]:
    """Ecosystems this repo is in, detected by manifest, defined by the register.

    Before contract 3 this was a checker-side dictionary knowing Python and
    Node, so a Go, Rust or Java repository with no lockfile at all passed
    SUP-001 — an exemption nobody decided and no `review_by` could surface
    (ADR 0018).
    """
    return {
        name: ecosystem
        for name, ecosystem in register.ecosystems.items()
        if any(repo.exists(manifest) for manifest in ecosystem.manifest)
    }


def lockfile_present_and_tracked(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    present = _ecosystems_present(repo, register)
    if not present:
        return _ok("no package manager detected — nothing to lock")
    missing = [
        name
        for name, ecosystem in present.items()
        if not any(lock in repo.tracked for lock in ecosystem.lockfiles)
    ]
    if missing:
        return _fail(
            "no tracked lockfile for: "
            + ", ".join(
                f"{m} (one of {', '.join(present[m].lockfiles)})" for m in sorted(missing)
            )
        )
    return _ok(f"tracked lockfile present for: {', '.join(sorted(present))}")


def stack_tool_pinned_in_lockfile(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """Each applicable stack's gate tool for `role` is pinned in a tracked lockfile.

    The other half of [ADR 0020](../../docs/adr/0020-a-locus-reaches-the-pinned-artefact.md).
    That ADR made every locus invoke the artefact its lockfile owns, and measured
    the one case the invocation cannot cover: `uv run <tool>` falls through to
    `PATH` when the tool is absent from the project altogether (case C). An
    invocation cannot assert the existence of the thing it invokes, so the
    existence is asserted here.

    Everything that decides the verdict is a register fact. Which ecosystem's
    lockfile pins a stack's tools is `stacks.<stack>.ecosystem`, what a package
    looks like inside that lockfile is `ecosystems.<name>.lock_entry`, and the
    name to look for is the gate's `package` where it differs from its `tool`.
    """
    role = str(args.get("role", ""))
    if not role:
        return _fail("assert requires a 'role' argument naming a gate in the register")
    problems: list[str] = []
    found: list[str] = []
    for stack_name, stack in sorted(register.stacks.items()):
        gate = stack.gates.get(role)
        if gate is None:
            continue
        if not compile_predicate(register.predicates.get(stack_name, False))(repo):
            continue
        problem, note = _pin_problem(repo, register, stack, gate)
        if problem:
            problems.append(f"{stack_name}: {problem}")
        else:
            found.append(note)
    if problems:
        return _fail("; ".join(problems))
    if not found:
        return _ok(f"no stack with a {role} gate is present")
    return _ok("; ".join(found))


def _pin_problem(
    repo: Repo,
    register: Register,
    stack: Stack,
    gate: Gate,
) -> tuple[str | None, str]:
    """Why this gate's tool is not pinned, or the lockfile that pins it."""
    package = gate.package or gate.tool
    ecosystem = register.ecosystems.get(stack.ecosystem)
    if ecosystem is None:
        # Unreachable through a validated register — the schema rejects a stack
        # naming no defined ecosystem. Stated rather than assumed, because an
        # assert that silently passes on a register it cannot read is the
        # vacuous verdict this control exists to stop.
        return f"names ecosystem '{stack.ecosystem}', which the register does not define", ""
    tracked = [lock for lock in ecosystem.lockfiles if lock in repo.tracked]
    if not tracked:
        return (
            f"{package} cannot be pinned — no tracked {stack.ecosystem} lockfile "
            f"(one of {', '.join(ecosystem.lockfiles)})",
            "",
        )
    patterns = [substitute_package(pattern, package) for pattern in ecosystem.lock_entry]
    unreadable: list[str] = []
    for lock in tracked:
        try:
            text = repo.read(lock)
        except (OSError, UnicodeDecodeError):
            # A binary lockfile — bun.lockb is one — is reported as a lockfile
            # that could not be read. Treating it as a match would pass every
            # package, and treating it as absent would hide why.
            unreadable.append(lock)
            continue
        if any(re.search(pattern, text) for pattern in patterns):
            return None, f"{gate.tool} pinned in {lock}"
    searched = ", ".join(tracked)
    if unreadable:
        return (
            f"{package} not found in {searched} — {', '.join(unreadable)} could not be "
            f"read as text, so no pin could be confirmed",
            "",
        )
    return f"{package} is not pinned in {searched}, so {gate.invocation} resolves from PATH", ""


_RENOVATE_CONFIGS = (
    "renovate.json",
    "renovate.json5",
    ".renovaterc",
    ".renovaterc.json",
    ".github/renovate.json",
    ".github/renovate.json5",
)


def _required_update_ecosystems(repo: Repo, register: Register) -> dict[str, tuple[str, ...]]:
    """Dependabot ecosystems this repo needs, with acceptable spellings.

    The package ecosystems come from the register (ADR 0018). The four below
    stay in the checker: they are not package ecosystems with manifests and
    lockfiles but repository features, detected by predicates the register
    already owns, and a repo could not reasonably need their Dependabot
    spellings to differ — those names are GitHub's, not ours.
    """
    required: dict[str, tuple[str, ...]] = {
        name: ecosystem.dependabot
        for name, ecosystem in _ecosystems_present(repo, register).items()
    }
    if repo.workflow_files():
        required["github-actions"] = ("github-actions",)
    if repo.exists(".devcontainer/devcontainer.json"):
        required["devcontainers"] = ("devcontainers",)
    if repo.dockerfiles():
        required["docker"] = ("docker",)
    if repo.glob_basename("*.tf"):
        required["terraform"] = ("terraform",)
    return required


def _renovate_covers_ecosystems(config: object) -> bool:
    """Whether a Renovate config proposes package-ecosystem updates at all.

    Renovate covers every ecosystem it detects *by default*, but a config may
    narrow `enabledManagers`. This repo does exactly that — Renovate is enabled
    for `custom.regex` only, to update the two version literals Dependabot
    cannot see, while Dependabot keeps the ecosystems it understands. Reading
    the file's presence as blanket coverage would report a coverage that had
    been switched off two lines further down.
    """
    if not isinstance(config, dict):
        return True  # unparseable: fall back to the default, which is coverage
    enabled = config.get("enabledManagers")
    if not isinstance(enabled, list):
        return True
    return any(str(manager).removeprefix("custom.") != "regex" for manager in enabled)


def dependency_update_config_covers_all_ecosystems(
    repo: Repo, register: Register, _args: Mapping[str, object]
) -> AssertResult:
    renovate = next((p for p in _RENOVATE_CONFIGS if repo.exists(p)), None)
    if renovate is not None:
        # Any renovate filename used to be accepted unparsed, so a config whose
        # entire content was `{"enabled": false}` satisfied a control about
        # updates being proposed automatically (§ D).
        config = load_jsonc(repo.root / renovate)
        if isinstance(config, dict) and config.get("enabled") is False:
            return _fail(f"{renovate} sets enabled: false — no updates are proposed")
        if _renovate_covers_ecosystems(config):
            return _ok(f"{renovate} present (covers all ecosystems by default)")
        # Narrowed to custom managers: it proposes the literals, not the
        # ecosystems, so something else must still cover those.
    dependabot = next(
        (p for p in (".github/dependabot.yml", ".github/dependabot.yaml") if repo.exists(p)),
        None,
    )
    if dependabot is None:
        if renovate is not None:
            return _fail(
                f"{renovate} enables custom managers only, so it proposes no package-ecosystem "
                "updates, and there is no .github/dependabot.yml to cover them"
            )
        return _fail("no dependency update configuration (.github/dependabot.yml or renovate)")
    config = yaml.safe_load(repo.read(dependabot))
    if not isinstance(config, dict):
        return _fail(f"{dependabot} is not a mapping")
    covered = {
        str(update.get("package-ecosystem", ""))
        for update in config.get("updates") or []
        if isinstance(update, dict)
    }
    missing = [
        name
        for name, spellings in _required_update_ecosystems(repo, register).items()
        if not any(s in covered for s in spellings)
    ]
    if missing:
        return _fail(f"{dependabot} does not cover: {', '.join(missing)}")
    return _ok(f"{dependabot} covers every ecosystem present")


def _feature_id(reference: str) -> str:
    """Feature reference without version tag or digest."""
    base = reference.split("@")[0]
    head, _, tail = base.rpartition(":")
    return head if head and "/" not in tail else base


def devcontainer_lock_covers_all_features(
    repo: Repo, _register: Register, _args: Mapping[str, object]
) -> AssertResult:
    if not repo.exists(".devcontainer/devcontainer.json"):
        return _fail(".devcontainer/devcontainer.json does not exist")
    config = load_jsonc(repo.root / ".devcontainer/devcontainer.json")
    if not isinstance(config, dict):
        return _fail(".devcontainer/devcontainer.json is not a mapping")
    declared = {_feature_id(ref) for ref in config.get("features") or {}}
    if not repo.exists(".devcontainer/devcontainer-lock.json"):
        if declared:
            return _fail(".devcontainer/devcontainer-lock.json does not exist")
        return _ok("no features declared, no lock file required")
    lock = json.loads(repo.read(".devcontainer/devcontainer-lock.json"))
    if not isinstance(lock, dict):
        return _fail(".devcontainer/devcontainer-lock.json is not a mapping")
    locked: dict[str, str] = {}
    for ref, entry in (lock.get("features") or {}).items():
        if isinstance(entry, dict):
            locked[_feature_id(str(ref))] = str(entry.get("resolved", ""))
    problems = []
    for feature in sorted(declared):
        resolved = locked.get(feature)
        if resolved is None:
            problems.append(f"{feature} is not in the lock file")
        elif "@sha256:" not in resolved:
            problems.append(f"{feature} is locked without a resolved digest")
    if problems:
        return _fail("; ".join(problems))
    return _ok(f"lock file pins all {len(declared)} declared features by digest")


_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def devcontainer_image_digest_pinned(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    if not repo.exists(".devcontainer/devcontainer.json"):
        return _fail(".devcontainer/devcontainer.json does not exist")
    config = load_jsonc(repo.root / ".devcontainer/devcontainer.json")
    if not isinstance(config, dict):
        return _fail(".devcontainer/devcontainer.json is not a mapping")
    image = config.get("image")
    if isinstance(image, str):
        if not _DIGEST.search(image):
            return _fail(f"image reference is not digest-pinned: {image}")
        return _ok("devcontainer image is pinned by @sha256: digest")
    # A devcontainer may build from a Dockerfile instead of naming an image.
    # Demanding `image` failed that shape outright while never checking the
    # Dockerfile's own `FROM` pin — the thing that actually fixes the base
    # (§ D).
    build = config.get("build")
    dockerfile = build.get("dockerfile") if isinstance(build, dict) else None
    if not isinstance(dockerfile, str):
        return _fail("devcontainer.json declares neither an image nor a build.dockerfile")
    context = str(build.get("context", ".")) if isinstance(build, dict) else "."
    rel = f".devcontainer/{context}/{dockerfile}".replace("/./", "/")
    if not repo.exists(rel):
        rel = f".devcontainer/{dockerfile}"
    if not repo.exists(rel):
        return _fail(f"build.dockerfile does not exist: {dockerfile}")
    froms = [
        line.split()[1]
        for line in repo.read(rel).splitlines()
        if line.strip().upper().startswith("FROM ") and len(line.split()) > 1
    ]
    unpinned = [reference for reference in froms if not _DIGEST.search(reference)]
    if unpinned:
        return _fail(f"{rel}: FROM is not digest-pinned: {', '.join(unpinned)}")
    return _ok(f"{rel} pins every FROM by @sha256: digest")


def devcontainer_user_is_non_root(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """The devcontainer states its user, and that user is not root.

    A devcontainer built from an `image:` has no Dockerfile, so
    `dockerfile_final_user_is_non_root` has nothing to read and `hadolint` has
    nothing to lint. The property is the same one BLD-001 states — the container
    does not end as root — reached through `devcontainer.json` instead.

    **Stated, not inherited.** A devcontainer naming neither `remoteUser` nor
    `containerUser` runs as whatever the base image happens to use, which may be
    root today and may become root on any digest bump. That is the difference
    between a container that is non-root and one that is non-root by luck, and
    it is why an absent key fails here rather than deferring to the image.
    """
    path = ".devcontainer/devcontainer.json"
    if not repo.exists(path):
        return _fail(f"{path} does not exist")
    config = load_jsonc(repo.root / path)
    if not isinstance(config, dict):
        return _fail(f"{path} is not a mapping")

    # `containerUser` is who the container process runs as; `remoteUser` is who
    # the tooling and terminals act as. Either establishes a stated user, and
    # neither may be root — a `containerUser: root` beside a `remoteUser: vscode`
    # is still a container running as root.
    stated = {
        key: str(config[key]).strip()
        for key in ("containerUser", "remoteUser")
        if isinstance(config.get(key), str) and str(config[key]).strip()
    }
    if not stated:
        return _fail(
            f"{path} declares neither containerUser nor remoteUser, so the user is "
            "inherited from the image and changes whenever the image does"
        )
    root = [
        f"{key}: {value}"
        for key, value in sorted(stated.items())
        if value.split(":")[0].lower() == "root" or value.split(":")[0] == "0"
    ]
    if root:
        return _fail(f"{path} runs as root — {', '.join(root)}")
    declared = ", ".join(f"{key}: {value}" for key, value in sorted(stated.items()))
    return _ok(f"{path} states a non-root user ({declared})")


def _expand(token: str, defaults: Mapping[str, str]) -> str:
    """`${NAME}` / `$NAME` replaced by its ARG or ENV default, once."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        return defaults.get(name, match.group(0))

    return re.sub(r"\$\{(\w+)\}|\$(\w+)", replace, token)


def dockerfile_final_user_is_non_root(
    repo: Repo,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    dockerfiles = repo.dockerfiles()
    if not dockerfiles:
        return _ok("no Dockerfile present")
    problems = []
    for path in dockerfiles:
        lines = [
            line.strip()
            for line in repo.read(path).splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        last_from = max(
            (i for i, line in enumerate(lines) if line.upper().startswith("FROM ")),
            default=-1,
        )
        # ARG/ENV defaults, so `ARG USERNAME=root` + `USER ${USERNAME}` is seen
        # for what it is. Comparing the literal token meant the most common way
        # of parameterising the user hid a root container completely (§ D).
        defaults: dict[str, str] = {}
        for line in lines:
            keyword, _, rest = line.partition(" ")
            if keyword.upper() in ("ARG", "ENV") and "=" in rest:
                key, _, value = rest.strip().partition("=")
                defaults[key.strip()] = value.strip().strip("\"'")
        users = [
            line.split(None, 1)[1]
            for line in lines[last_from + 1 :]
            if line.upper().startswith("USER ")
        ]
        if not users:
            problems.append(f"{path}: final stage declares no USER")
            continue
        user = _expand(users[-1].split(":")[0].strip(), defaults)
        if user.lower() == "root" or user == "0":
            problems.append(f"{path}: final stage runs as {user}")
    if problems:
        return _fail("; ".join(problems))
    return _ok(f"final stage of {len(dockerfiles)} Dockerfile(s) is non-root")


# `markdownlint_config_present` lived here and asserted exactly what its name
# said: that a file existed. DOC-001's `enforces` names a ceiling and three
# loci, none of which it read, so `line_length: 100000` passed and so did
# deleting the CI step (§ A). It is superseded by
# `markdown_gate_wired_at_all_loci` in `asserts_command`, which reads all four.


#: A version-shaped line in a toolchain file. The whole content is the value, so
#: unlike every other pin in this repository there is no tool name beside it to
#: match on (ADR 0027). Comment lines are skipped: uv accepts them in
#: `.python-version`, and the `# renovate:` annotation a bot reads lives in one.
#:
#: One implementation, read by the assert below and by
#: `tests/test_renovate_managers.py`, which has to know the same thing to check
#: that the bot's manager extracts the value the file actually names.
_TOOLCHAIN_VALUE = re.compile(r"^\s*(?!#)\s*v?(\d+(?:\.\d+)*)\s*$", re.MULTILINE)


def toolchain_version(text: str) -> str | None:
    """The version a toolchain file names, or None if it names none."""
    match = _TOOLCHAIN_VALUE.search(text)
    return match.group(1) if match else None


def _who_needs(tool: str, register: Register) -> str:
    """Which control wants this tool, and who deploys it — appended to a failure.

    An absent lockfile reads as a broken supply chain. Usually it means the
    control that needs the tool has not been deployed yet, and those are very
    different problems with one message. Measured on the first adoption outside
    this repository: `markdownlint-cli2 is sourced from package-lock.json, which
    is not tracked` sent a reader looking at SUP-001 when the fix was to deploy
    DOC-001.

    Read from the register rather than held here: which control names a tool is
    a register fact, and a lookup table in the checker would be a second copy of
    it (ADR 0018).
    """
    for control in register.controls:
        for block in control.verify:
            if tool in {str(v) for v in block.args.values()}:
                by = f", deployed by {control.deployed_by}" if control.deployed_by else ""
                return (
                    f" — that tool belongs to {control.id}{by}. If you have not "
                    f"deployed {control.id} yet, this is that rather than a "
                    "supply-chain defect"
                )
    return ""


def tool_versions_match_register(
    repo: Repo,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """Every locus pins the version the register names.

    The register is the single definition; this assert is what makes that true
    in fact rather than in aspiration. Before contract 3 no version existed in
    the register at all while four documents said one did, and
    markdownlint-cli2 was pinned in four separate places with nothing comparing
    them — a comment in lint.yml even told humans to "change all three
    together" where there were four.

    **Which loci is a register fact** from contract 8. It was a four-entry tuple
    here, holding this repository's own filenames: renaming a workflow took it
    out of comparison with no verdict changing, and an adopting repository that
    pinned the same tools in files of its own naming was told they were "pinned
    at no known locus" — this repo's paths quoted at it as though they were the
    standard (§ H2).
    """
    if not register.tools:
        return _ok("the register pins no tool versions")
    problems: list[str] = []
    checked = 0
    # A lockfile-sourced tool has nothing to reconcile: the loci invoke it
    # through the package manager, so there is no version at any locus to
    # disagree with. What must hold instead is that the lockfile is there.
    #
    # A toolchain-sourced tool is the same shape for a different reason
    # (ADR 0027): a human writes the file and every locus reads it, so again no
    # locus repeats the value. An untracked one is worse than a drifted pin —
    # every locus falls back to whatever it would have resolved anyway, which is
    # the state that put CI on 3.14 and the devcontainer on 3.13 with nothing
    # reporting it.
    literal = [tool for tool in register.tools.values() if tool.source == "literal"]
    for tool in register.tools.values():
        if tool.source == "lockfile" and tool.lockfile and tool.lockfile not in repo.tracked:
            problems.append(
                f"{tool.name} is sourced from {tool.lockfile}, which is not tracked"
                + _who_needs(tool.name, register)
            )
        if tool.source == "toolchain" and tool.toolchain:
            if tool.toolchain not in repo.tracked:
                problems.append(
                    f"{tool.name} is sourced from {tool.toolchain}, which is not tracked"
                    + _who_needs(tool.name, register)
                )
            elif toolchain_version(repo.read(tool.toolchain)) is None:
                # The same silence one level down as a declared `pinned_at` site
                # holding no pin: the file is tracked and names no version, so
                # every locus resolves as though it were absent.
                problems.append(
                    f"{tool.toolchain} names no version, though the register records it as "
                    f"the authority for {tool.name}"
                )
    for tool in literal:
        for path in tool.pinned_at:
            # A declared site that is not there is the rename this check used to
            # miss entirely: the file left the checker's list by being renamed,
            # and silence read as agreement.
            if not repo.exists(path):
                problems.append(
                    f"{tool.name} is recorded as pinned at {path}, which does not exist"
                )
                continue
            text = repo.read(path)
            # Match the tool name next to a version-shaped token, whatever the
            # separator each locus uses: `@1.2.3`, `==1.2.3`, `=1.2.3`,
            # `v1.2.3`, `: v1.2.3`.
            #
            # Case-insensitively, because a shell locus spells the same pin
            # `GITLEAKS_VERSION=8.30.1`. Matching case-sensitively meant
            # gitleaks was compared at **no** locus while this assert reported
            # a pass: drifting setup.sh to 9.99.9 changed nothing. Renovate's
            # own dashboard found it, by listing five managed sites where the
            # register implies six.
            # An optional quote after the separator, because a pin is still a
            # pin when it is quoted. Without it `uv_version="0.12.6"` reported
            # *no pin found* — a correctly pinned, shellcheck-clean line read as
            # an unpinned one — and the workaround was an instruction to
            # substitute unquoted, which is this checker's brittleness written
            # up as a rule for every repository to follow. Measured on the
            # published `control-register` template, whose placeholders an
            # upstream `shellcheck-clean` commit quoted (2026-08-29).
            #
            # It also reaches a JSON site, `"uv": "0.12.6"`, which the unquoted
            # form could not read at all. No `pinned_at` here is JSON today, so
            # that is a hole closed rather than a defect found.
            pattern = re.compile(
                rf"{re.escape(tool.name)}[^\n]*?[@=:\s][\"']?v?(\d+\.\d+\.\d+)",
                re.IGNORECASE,
            )
            found = list(pattern.finditer(text))
            # A declared site holding no pin is the same silence one level down:
            # the file is there and the version is not, so nothing was compared.
            if not found:
                problems.append(
                    f"{path}: no {tool.name} version pin found, though the register records "
                    "one here"
                )
            for match in found:
                checked += 1
                if match.group(1) != tool.version:
                    problems.append(
                        f"{path}: {tool.name} pinned at {match.group(1)}, "
                        f"register says {tool.version}"
                    )
            # Only a locus that downloads the tool carries its checksum.
            if (
                tool.sha256
                and tool.sha256 not in text
                and re.search(rf"{re.escape(tool.name)}[^\n]*\.tar\.gz", text)
            ):
                problems.append(f"{path}: {tool.name} checksum does not match the register")
    if problems:
        return _fail("; ".join(sorted(set(problems))))
    sourced = len(register.tools) - len(literal)
    sites = sum(len(tool.pinned_at) for tool in literal)
    return _ok(
        f"{checked} version pin(s) across {sites} declared locus/loci and {len(literal)} "
        f"literal tool(s) match the register; {sourced} sourced from a lockfile or a "
        "toolchain file, with no version to keep in step"
    )


def provenance_stamp_present(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The gate that deploys this control left a stamp *for this control*.

    Phase 2's criterion is that every gate writes a provenance stamp *its own
    verify step reads back*. A gate that writes a stamp nothing reads has
    recorded a claim, not established one — which is how three of the four
    `lint-md` artefacts came to carry no stamp at all while `CLAUDE.md` stated
    as fact that they did (§ F).

    **Per control, not per gate.** Matching on the skill alone was the shape
    this assert shipped with, and it credited a gate for any stamp it had
    written anywhere: `gate-quality` deploys three controls, so a stamp naming
    TST-001 satisfied LNT-001's read-back and the editor locus could go
    unstamped with nothing reporting it. The control being evaluated arrives as
    `args[CONTROL_ARG]`, supplied by the runner rather than by the register —
    writing a control's own id into its own entry would be a second copy of it
    in the file that exists to prevent second copies.

    What this still does not check is *how many* artefacts the gate should have
    stamped, or at which loci. That list is the plugin's `deploys.json` rather
    than the register's, and reading a plugin from the checker is Phase 5's
    sweep. So: each control now proves its own deployment was recorded, and no
    control proves the deployment was complete.

    Read back here, deliberately, is **soundness and not currency**. A stamp
    behind the register is staleness, which `docs/00-concepts.md` § Notify,
    never redeploy says is reported and never enforced; failing a build over one
    would be enforcing redeployment. A stamp that names a control the register
    does not define, or claims a contract the register has not reached, is a
    defect in the deployment, and those fail.

    The deploying skill comes from the register (`args.skill`, which the schema
    holds equal to the control's `deployed_by`): which skill owns a control's
    artefacts is a fact about a repository's tooling, not about the checker
    (ADR 0018).
    """
    skill = str(args.get("skill", ""))
    if not skill:
        return _fail("assert requires a 'skill' argument naming the deploying gate")
    this_control = str(args.get(CONTROL_ARG, ""))
    if not this_control:
        # Reachable only through `register-check assert <name>`, the debugging
        # entry point, which evaluates an assert outside any control. Saying so
        # beats inventing a verdict for a question that was not asked.
        return _fail(
            "assert reads back the stamp of the control it is evaluating, and was "
            "run outside one — use `register-check run --control <ID>`"
        )

    known = {control.id for control in register.controls} | {
        control.id for control in register.meta_controls
    }
    mine = {
        path: [stamp for stamp in stamps if stamp.skill == skill]
        for path, stamps in stamps_by_file(repo).items()
    }
    mine = {path: stamps for path, stamps in mine.items() if stamps}
    if not mine:
        return _fail(
            f"no tracked file carries a provenance stamp naming '{skill}' — "
            f"expected `{EXPECTED}` in each artefact the gate deploys"
        )

    problems = [
        f"{path}: stamp names {stamp.control}, which the register does not define"
        for path, stamps in mine.items()
        for stamp in stamps
        if stamp.control not in known
    ] + [
        f"{path}: stamp claims register contract {stamp.register_contract}, "
        f"but the register is at {register.register_contract}"
        for path, stamps in mine.items()
        for stamp in stamps
        if stamp.register_contract > register.register_contract
    ]
    if problems:
        return _fail("; ".join(sorted(problems)))

    for_this = sorted(
        path for path, stamps in mine.items() if any(s.control == this_control for s in stamps)
    )
    if not for_this:
        return _fail(
            f"'{skill}' stamped {', '.join(sorted(mine))}, and no stamp names "
            f"{this_control} — a gate that deploys several controls records each "
            "artefact against the control whose locus it is"
        )
    return _ok(
        f"{skill} stamped {len(for_this)} artefact{'s' if len(for_this) != 1 else ''} "
        f"for {this_control} ({', '.join(for_this)})"
    )


def secret_files_are_gitignored(
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The files a host writes credentials into cannot be committed by accident.

    SEC-001's other blocks all act *after* the fact: `gitleaks` reads what git
    already carries, and push protection reads what reached the remote. The
    ignore rule is the one part of the control that acts before a credential
    is ever a git object, and until contract 18 nothing read it. Two files in
    this repository — and two in every repository the template is copied into —
    are written on every container start by a script whose own header says
    *SEC-001 depends on these two lines*, and that dependency was prose.

    Three ways this fails, and all three are quiet:

    **Tracked.** The file is already in git, so an ignore rule changes nothing
    about it. Reported as its own case rather than as "not ignored", because
    the remedy is different: an ignore rule fixes the second, and only a
    history rewrite and a credential rotation fix the first.

    **Not ignored.** The next `git add -A` commits it. This is the case the
    prose was guarding and the one a checker can see instantly.

    **Ignored by a rule git does not carry** — `.git/info/exclude`, a global
    excludes file, or a `.gitignore` nobody committed. This is the reason the
    assert reads `check-ignore -v` for the *source* of the match rather than
    taking exit 0 as the answer. The rule works on the machine that has it and
    on no other, so the file is unignored in every clone but the author's,
    which is precisely the shape `08-adopting.md` warns about: it does not fail
    a build, it fails quietly, later, in someone else's clone.

    Which files hold fetched credentials is a fact about a repository, not
    about the checker (ADR 0018), so `paths` is the register's. The mechanism —
    what git means by ignored, and that a rule must be tracked to travel — is
    not something a repository can reasonably differ on, so it stays here.
    """
    raw = args.get("paths")
    paths = [str(entry) for entry in raw] if isinstance(raw, list) else []
    if not paths:
        return _fail(
            "assert requires a non-empty 'paths' list naming the files that hold "
            "fetched credentials — an empty list would pass without checking anything"
        )

    problems: list[str] = []
    covered: list[str] = []
    for path in paths:
        if path in repo.tracked:
            problems.append(
                f"{path} is tracked — git already carries it, and an ignore rule added "
                "now would neither remove it from history nor un-leak what is in it"
            )
            continue
        # `--no-index` asks what the ignore rules say, rather than what they say
        # about a file git is not already tracking. The tracked case is handled
        # above and has a different remedy, so conflating the two would report
        # the wrong fix.
        result = git(repo.root, "check-ignore", "--no-index", "-v", "--", path)
        matched = result.stdout.strip()
        if result.returncode != 0 or not matched:
            problems.append(
                f"{path} is not ignored — the next `git add -A` commits the credentials "
                "in it, and a secret that reaches a remote is not undone by deleting it"
            )
            continue
        source = matched.split(":", 1)[0]
        if source not in repo.tracked:
            problems.append(
                f"{path} is ignored by {source}, which git does not track — the rule "
                "does not travel, so the file is ignored here and unignored in every "
                "other clone"
            )
            continue
        covered.append(f"{path} ({source})")

    if problems:
        return _fail("; ".join(problems))
    return _ok("ignored by a rule git carries: " + ", ".join(covered))


FILE_ASSERTS: dict[str, AssertFn] = {
    "tool_versions_match_register": tool_versions_match_register,
    "precommit_hook_present": precommit_hook_present,
    "lockfile_present_and_tracked": lockfile_present_and_tracked,
    "dependency_update_config_covers_all_ecosystems": (
        dependency_update_config_covers_all_ecosystems
    ),
    "devcontainer_lock_covers_all_features": devcontainer_lock_covers_all_features,
    "devcontainer_image_digest_pinned": devcontainer_image_digest_pinned,
    "dockerfile_final_user_is_non_root": dockerfile_final_user_is_non_root,
    "devcontainer_user_is_non_root": devcontainer_user_is_non_root,
    "provenance_stamp_present": provenance_stamp_present,
    "stack_tool_pinned_in_lockfile": stack_tool_pinned_in_lockfile,
    "secret_files_are_gitignored": secret_files_are_gitignored,
}

