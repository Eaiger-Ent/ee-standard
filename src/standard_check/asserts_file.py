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

from standard_check.repo import Repo, load_jsonc

if TYPE_CHECKING:  # `register` imports the assert registries — importing it
    from standard_check.register import Ecosystem, Register  # at runtime: circular


@dataclass(frozen=True)
class AssertResult:
    passed: bool
    message: str


# Asserts take the register as well as the repository, from contract 3. A rule
# that decides a verdict belongs in the register (ADR 0018), so an assert that
# cannot read the register would have nowhere to read the rule from — which is
# how the checker became a second source of truth in the first place.
AssertFn = Callable[[Repo, "Register", Mapping[str, object]], AssertResult]


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


# Where a pinned tool version can appear. Each pattern captures the version, so
# a locus that disagrees with the register is named with what it says.
_VERSION_SITES = (
    ".pre-commit-config.yaml",
    ".devcontainer/setup.sh",
    ".github/workflows/lint.yml",
    ".github/workflows/standard-check.yml",
)


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
    """
    if not register.tools:
        return _ok("the register pins no tool versions")
    problems: list[str] = []
    checked = 0
    # A lockfile-sourced tool has nothing to reconcile: the loci invoke it
    # through the package manager, so there is no version at any locus to
    # disagree with. What must hold instead is that the lockfile is there.
    literal = [tool for tool in register.tools.values() if tool.source == "literal"]
    for tool in register.tools.values():
        if tool.source == "lockfile" and tool.lockfile and tool.lockfile not in repo.tracked:
            problems.append(
                f"{tool.name} is sourced from {tool.lockfile}, which is not tracked"
            )
    seen: dict[str, int] = {tool.name: 0 for tool in literal}
    for path in _VERSION_SITES:
        if not repo.exists(path):
            continue
        text = repo.read(path)
        for tool in literal:
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
            pattern = re.compile(
                rf"{re.escape(tool.name)}[^\n]*?[@=:\s]v?(\d+\.\d+\.\d+)",
                re.IGNORECASE,
            )
            for match in pattern.finditer(text):
                checked += 1
                seen[tool.name] += 1
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
    # A literal tool nothing pins is not a tool in agreement — it is a tool this
    # assert cannot see. Silence used to read as a pass, which is the verdict
    # overstating what was checked (§ A).
    problems.extend(
        f"{name} is declared `source: literal` but is pinned at no known locus "
        f"({', '.join(_VERSION_SITES)}), so no copy of its version was compared"
        for name, count in sorted(seen.items())
        if count == 0
    )
    if problems:
        return _fail("; ".join(sorted(set(problems))))
    sourced = len(register.tools) - len(literal)
    return _ok(
        f"{checked} version pin(s) across {len(literal)} literal tool(s) match the register; "
        f"{sourced} sourced from a lockfile, with no version to keep in step"
    )


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
}

# Remote assert names are part of the closed set from Phase 1 so a typo is a
# schema error today, but their execution is deliberately deferred to Phase 3 —
# implementing them now would mean stubbing exactly the part that must not be
# stubbed. Until then every `kind: remote` block reports SKIPPED (no
# credentials), which is never a pass.
REMOTE_ASSERTS: frozenset[str] = frozenset(
    {
        "github_push_protection_enabled",
        "default_branch_ruleset_satisfies",
    }
)
