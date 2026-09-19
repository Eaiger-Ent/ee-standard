#!/usr/bin/env -S uv run python
"""Publish the Craft profiles into the plugin an adopter installs — S5.

**The plugin ships what it writes, not what decides it.** `craft/` is the
register and stays here; `plugins/craft/profiles/` is the rendered output an
installer copies. That split is the whole design, and it has three reasons:

1. **An adopter installs a plugin, not a repository.** The register would have
   to travel for the skill to resolve a rule at install time, and a second copy
   of 2,600 lines of YAML is the duplication this repository exists to prevent.
2. **The installer runs where no toolchain is guaranteed.** A React-only
   repository has Node and may have no Python at all, so a skill that resolved
   the register at install time would need one. A skill that copies a file
   needs nothing, and `docs/craft/plan.md` § What this workstream will not do
   is about claiming more than you have.
3. **Enforcement is never Claude, and neither is rule selection.** A 141-rule
   selection assembled in context is a selection nobody can diff. Rendering it
   here, committing it, and testing that it still matches is how the artefact
   stays something a reviewer can read.

`tests/test_craft_plugin.py` re-runs this and fails on any difference, so a
change to `craft/` that nobody published is a broken build rather than a plugin
quietly a version behind.

Run it after any change to the register:

    uv run python scripts/craft_publish.py          # write
    uv run python scripts/craft_publish.py --check  # what a test does
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from craft_render import render, render_react, render_residue, scoped
from craft_select import REPO_ROOT, load, resolve

PROFILES = ("python/standard", "python/strict", "react/standard", "react/strict")
PLUGIN = REPO_ROOT / "plugins" / "craft"


def _slug(profile: str) -> str:
    return profile.replace("/", "-")


def artefacts(meta: dict[str, Any]) -> dict[str, str]:
    """Every file the plugin ships, keyed by its path under `plugins/craft/`.

    One directory per profile, and the file names are what they are for rather
    than where they go: an installer places a region inside a file the control
    register names, so `pyproject-region.toml` is a fragment and not a document.
    """
    out: dict[str, str] = {}
    for profile in PROFILES:
        into = f"profiles/{_slug(profile)}"
        if profile.startswith("python/"):
            out[f"{into}/pyproject-region.toml"] = render(profile, meta)
            if nested := scoped(profile, meta):
                out[f"{into}/src-ruff.toml"] = nested
        else:
            out[f"{into}/eslint.config.mjs"] = render_react(profile, meta)

    # The residue depends on the level of every profile installed, because a
    # level binds properties the level below leaves unenforced. Eight documents
    # is every combination a repository can ask for, and generating them is
    # cheaper than a skill merging two at install time and getting it wrong.
    for python in ("python/standard", "python/strict"):
        for react in ("react/standard", "react/strict"):
            out[f"profiles/{_slug(python)}+{_slug(react)}/unenforced.md"] = render_residue(
                [python, react], meta
            )
    for profile in PROFILES:
        out[f"profiles/{_slug(profile)}/unenforced.md"] = render_residue([profile], meta)

    out["profiles/manifest.json"] = json.dumps(manifest(meta, out), indent=2) + "\n"
    return out


def manifest(meta: dict[str, Any], rendered: dict[str, str]) -> dict[str, Any]:
    """What the chooser presents, and what a re-run compares against.

    The Python cost figures are re-derived from the installed ruff every time
    this runs, so they carry the version that answered — `review.bench.md`
    § What each rule costs is why a number without its version is a claim. The
    React side carries counts and no cost: reading `meta.fixable` needs the six
    plugins resolved from a `node_modules`, which neither this repository nor a
    repository at its first install has. `docs/craft/build.installer.md` § What
    the chooser shows is what an installer does about that.
    """
    profiles: dict[str, Any] = {}
    for profile in PROFILES:
        resolved = resolve(profile, meta)
        entry: dict[str, Any] = {
            "version": meta["profiles"][profile]["version"],
            "stack": resolved["stack"],
            "level": resolved["level"],
            "properties": len(resolved["properties"]),
            # Read back from what was rendered rather than restated. The first
            # version of this listed the files per level and was already wrong:
            # `python/standard` scopes `S101` to the package source, so it has a
            # nested configuration too.
            "files": sorted(
                path.split("/")[-1]
                for path in rendered
                if path.startswith(f"profiles/{_slug(profile)}/")
            ),
        }
        if resolved["stack"] == "python":
            catalogue = resolved["catalogue"]
            costs = Counter(catalogue[code]["fix_availability"] for code in resolved["codes"])
            entry |= {
                "rules": len(resolved["codes"]),
                "read_from": resolved["tool_version"],
                "declares_a_fix": costs["Always"] + costs["Sometimes"],
                "hand_work": costs["None"],
            }
        else:
            entry |= {
                "rules": len(resolved["rules"]),
                "plugins": sorted(
                    {rule.rsplit("/", 1)[0] for rule in resolved["rules"]},
                ),
                "cost": "unread — needs the plugins resolved from a node_modules",
            }
        profiles[profile] = entry
    return {
        "craft_contract": meta["craft_contract"],
        "levels": list(meta["levels"]),
        "profiles": profiles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change instead of writing it",
    )
    args = parser.parse_args()

    meta = load("meta")
    written = artefacts(meta)
    stale: list[str] = []
    for path, body in sorted(written.items()):
        target = PLUGIN / path
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == body:
            continue
        stale.append(path)
        if not args.check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    published = {
        str(path.relative_to(PLUGIN))
        for path in (PLUGIN / "profiles").rglob("*")
        if path.is_file()
    }
    orphans = sorted(published - set(written))
    for path in orphans:
        stale.append(f"{path} (no longer rendered)")
        if not args.check:
            (PLUGIN / path).unlink()

    verb = "differ" if args.check else "written"
    print(f"{len(written)} artefacts, {len(stale)} {verb}")
    for path in stale:
        print(f"  {path}")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
