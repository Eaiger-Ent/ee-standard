"""What a repository's GitHub plan does not sell it (ADR 0047).

Two of this register's requirements are things GitHub sells rather than things a
repository configures: rulesets on a private repository are Team and Enterprise
only, and secret-scanning push protection on a private repository needs a paid
tier. A repository without them does not merely fail to verify CI-001 and
SEC-001's remote block — it **fails** them, because the effective-rules endpoint
returns `[]`, which is a list and therefore an answer.

The cost of leaving that alone is not the two controls, it is the other
thirteen: a run that can never be green is one people stop reading, which is the
failure the sweep's own design names.

So a repository records the limit and the block reports `UNAVAILABLE (plan)`.
Six rules from ADR 0047 make it a record rather than an opt-out, and this module
holds the four that are mechanical:

* it never yields a pass — the caller maps it to `Verdict.UNAVAILABLE`;
* it names a `kind: remote` assert, never a control and never a file block;
* it expires, and an expired entry **fails** rather than reverting to the
  waiver;
* the register never carries one — this reads `deployment-decisions.yaml`,
  which is posture (ADR 0022 requirement 6).

The two it cannot hold are stated in the ADR and repeated here because someone
reading this file is the person most likely to need them. **The checker cannot
confirm a claimed limit is real**: a `403` saying *upgrade* is evidence, an
empty rule list is not, since that is also an unconfigured Team repository. And
an entry must name a capability the plan genuinely does not offer, never one it
offers by a route the checker fails to read — a Pro repository with classic
branch protection failing CI-001 would be a checker defect, and waiving it here
would hide the defect behind a record that looks deliberate.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

import yaml

from register_check.repo import Repo

#: Beside `declined:`, because both are dated records of something this
#: repository does not have, read by the same command and going stale on the
#: same terms.
DECISIONS = "deployment-decisions.yaml"


class BadPlatformLimits(Exception):
    """The record is malformed. Never read as "no limits" — see `read_limits`."""


@dataclass(frozen=True)
class PlatformLimit:
    """One remote block a repository's plan does not let it satisfy."""

    control: str
    assert_name: str
    plan: str
    lacks: str
    review_by: datetime.date

    def expired(self, today: datetime.date) -> bool:
        return today > self.review_by


def read_limits(repo: Repo, path: Path | None = None) -> tuple[PlatformLimit, ...]:
    """The platform limits on record, or an error if the file cannot be read.

    A malformed file raises rather than returning nothing, for the same reason
    `read_decisions` does: reading it as "no limits" turns a recorded, dated
    waiver into a silent failure, and the report would look ordinary while
    saying the opposite of what the repository wrote down.
    """
    target = path or repo.root / DECISIONS
    if not target.exists():
        return ()
    try:
        document = yaml.safe_load(target.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BadPlatformLimits(f"{target} is not valid YAML: {exc}") from exc
    if document is None:
        return ()
    if not isinstance(document, dict):
        raise BadPlatformLimits(f"{target} must be a mapping")
    entries = document.get("platform_limits") or []
    if not isinstance(entries, list):
        raise BadPlatformLimits(f"{target}: 'platform_limits' must be a list")
    found: list[PlatformLimit] = []
    for i, entry in enumerate(entries):
        at = f"{target}: platform_limits[{i}]"
        if not isinstance(entry, dict):
            raise BadPlatformLimits(f"{at} must be a mapping")
        required = ("control", "assert", "plan", "lacks", "review_by")
        missing = [k for k in required if k not in entry]
        if missing:
            raise BadPlatformLimits(f"{at} is missing: {', '.join(missing)}")
        review_by = entry["review_by"]
        if isinstance(review_by, str):
            try:
                review_by = datetime.date.fromisoformat(review_by)
            except ValueError as exc:
                raise BadPlatformLimits(f"{at}.review_by is not an ISO date") from exc
        if not isinstance(review_by, datetime.date):
            raise BadPlatformLimits(f"{at}.review_by must be an ISO date")
        found.append(
            PlatformLimit(
                control=str(entry["control"]),
                assert_name=str(entry["assert"]),
                plan=str(entry["plan"]),
                lacks=" ".join(str(entry["lacks"]).split()),
                review_by=review_by,
            )
        )
    return tuple(found)


def limit_for(
    limits: tuple[PlatformLimit, ...], control: str, assert_name: str
) -> PlatformLimit | None:
    """The entry covering this block, if the repository recorded one.

    Matched on the pair, never on the control alone. A control's *other* blocks
    are not waived by a limit recorded against one of them — CI-001's file half
    must still pass, so the adopter still records the ruleset they would enforce
    and the day the plan changes it is one API call rather than a fresh
    decision.
    """
    for limit in limits:
        if limit.control == control and limit.assert_name == assert_name:
            return limit
    return None
