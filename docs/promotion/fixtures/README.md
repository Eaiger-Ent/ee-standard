# Submission fixtures

Drafted answers to the four questions `/skill-submit-new` asks about each skill,
one directory per skill in `plugins/control-register/skills/`.

**Nothing reads these files.** The tool builds `tests/<skill>/triggers.yaml` and
`tests/<skill>/prompt.txt` from its own Q1–Q4 into temp files at submission time
and commits them onto the incubator branch; it never looks in this repository
for them. They are here so that submission 1 — nine pull requests — is nine
reviews rather than thirty-six questions answered live, at the one moment there
is no undo. See [`../../05-promotion.md`](../../05-promotion.md) § What a
submission now needs from the machine it runs on.

| File | The question it answers |
| --- | --- |
| `triggers.yaml` | Q1 (slash invocations), Q2 (natural language), Q3 (must **not** activate) |
| `prompt.txt` | The smoke-test fixture — the first `should_activate` entry carrying an argument |
| `rationale.txt` | Q4, the contribution rationale. Plain text rather than Markdown, because it is typed into a question box and never rendered |

`tests/test_submission_fixtures.py` derives the set from the plugin in both
directions and holds each file to the tool's own validation rules, so a tenth
skill added without a fixture set fails the build rather than being discovered
missing while nine submissions are being written.

## Two things worth knowing before you paste these in

**The smoke test runs `prompt.txt` for real.** `scripts/smoke-test.sh` executes
`claude -p "$(cat prompt.txt)"` under `--permission-mode bypassPermissions` with
a ten-second deadline. It runs in a **fresh empty temp repository** containing
only a shim of the skill under test, so nothing here is at risk — and because
that repository has no `controls.yaml`, every gate stops at its own pre-flight,
which is the most inert thing these skills can be asked to do. The gate's only
assertion is that the reply is not `Unknown command`.

**`register-adopt` gets no natural-language entries.** It is the one skill in
the family still carrying `disable-model-invocation: true`
([ADR 0035](../../adr/0035-a-dispatched-skill-is-reachable.md) removed it from
the other eight), and Q2 is skipped entirely for such a skill. Its three
`should_activate` entries are all slash invocations.
