---
name: register-variance
description: >
  Report which way a change to gated configuration moved — narrowing, loosening
  or neither — and say which keys could not be classified and why. Triggers:
  'classify this variance', 'which way did this config move', '/register-variance'.
argument-hint: "[--against <ref>] [--repo <path>] [--register <path>]"
allowed-tools: Read, Bash, AskUserQuestion
---

# /register-variance — which way did this change move?

You are running the **register-variance** skill. It answers one question about a
change to gated configuration: **narrowing, loosening, or neither** — and where
it cannot answer, it says which of the three known reasons applies.

**It writes nothing.** No config, no stamp, no register edit. Every artefact
belongs to the gate that owns its control, and this skill only reads. That is
also why it deploys no control and appears in no `deploys.json`: a provenance
stamp names a control, and there is none to name.

**It is not a gate.** The controls that must fail on a weakening already do,
through their own asserts —
[ADR 0019](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0019-exemptions-cannot-hide-tracked-files.md)
fails a build over an exemption that hides a tracked file, and DOC-001 fails one
over a ceiling above the register's. This report runs on demand and must never
become the place those checks move to.

---

## Why declining is the interesting part

A classifier that answers *narrowing* when it does not know is worse than no
classifier: it launders a guess into a verdict, and the person reading the
report has no way to tell the two apart. So every path that cannot decide
reports `UNCLASSIFIED` **with the reason**, and your job when reporting is to
carry that reason through rather than summarising it away.

`01-register-schema.md` § `variance` names three, and each needs a different
response from you:

| Reason | What it means | What to say |
| --- | --- | --- |
| A member was removed and another added | Whether the new rule covers the old is a fact about the tool's catalogue, not about the file | Ask the author which it was. There is no mechanical answer and pretending otherwise is the failure this skill exists to avoid |
| The register gives no polarity for the key | Which end is stricter has not been recorded | **This one has a fix.** Offer to add the key to the register's `variance.polarity` block — one line, and the next run classifies it |
| The config is executable code | A program's effective settings are whatever it computes at run time | Say so plainly. Moving the config to declarative data is a change the repository may not want, and it is not yours to propose unasked |

The second is the only one you may offer to close. Confusing it with the first
tells someone a one-line fix exists where it does not.

---

## Say what each write is for, before you make it

This skill writes one thing and only when asked — the register edit in Step 4 —
and that one is still a write. **Read
`${CLAUDE_PLUGIN_ROOT}/reference/write-narration.md` and use the shape it gives
before making it.** The person approving sees a diff and nothing else, and a
one-line `variance.polarity` entry is exactly the kind of change whose reason is
invisible in the diff: the value is a word, and why that end is the stricter one
is not in the file. The shape is held there rather than here because eight
copies of a rule is the drift this standard exists to prevent — see ADR 0036. If
`${CLAUDE_PLUGIN_ROOT}` is unset, the skill was reached as a project skill
rather than through the plugin, and the file is at
`plugins/control-register/reference/` in the standard's repository.

---

## Step 1 — Pre-flight

| State var | From |
| --- | --- |
| `REPO` | `--repo`, else the working directory |
| `REGISTER` | `--register`, else `<REPO>/controls.yaml` |
| `AGAINST` | `--against`, else leave unset and let the checker pick the merge base |
| `CHECKER` | `tools.register-check.invocation` in the register |

**If the checker is not installed**, stop and say so: this skill reports what
the checker computes and has no second implementation to fall back on. Point at
`/register-install`.

**If `variance.polarity` is absent from the register**, say so before running.
Every scalar will be declined, the report will be almost entirely
`UNCLASSIFIED`, and a reader who does not know why will read that as the tool
being broken rather than as the register being silent.

---

## Step 2 — Run the classifier, and never a second one

```bash
<CHECKER> --repo "$REPO" --register "$REGISTER" variance [--against "$AGAINST"]
```

**Do not read the config files yourself to decide a direction.** A second
opinion computed a second way is exactly the disagreement that surfaces at the
worst moment, and the register's `variance.polarity` block is the only thing
entitled to say which end of a setting is stricter.

Add `--path <file>` for gated configuration the register's `stacks:` does not
name. DOC-001's markdown config is the case that comes up: it is `lint-md`'s
control, in another plugin, so no `stacks.<stack>.gates.<role>.config` entry
names it.

---

## Step 3 — Report

Give the checker's verdict as it stands, then one line per file. Exit codes are
the register's usual vocabulary and mean what they always mean:

| Exit | Meaning | What to say |
| --- | --- | --- |
| `0` | Nothing moved, or everything that moved narrowed | Report the direction; no action |
| `1` | Something loosened | Name the file and the key. Then check that control's `variance:` — a loosening of a `narrowing-only` control is a violation, and of a control with no such constraint it is a decision |
| `3` | Something could not be classified | Work the table above, reason by reason |
| `2` | The base revision does not exist | With no baseline there is no delta. Say that rather than reporting *unchanged* |

**A mixed delta is a loosening.** Where one key tightens and another relaxes,
the file's verdict is the relaxation — do not describe it as balanced, and do
not lead with the tightening. Averaging them is how a weakening gets merged
under a green line.

**Then say what the direction does not tell you.** A narrowing is not automatic
approval: tightening a gate can break a build for everyone, and this report says
which way the change moved, never whether it should land.

---

## Step 4 — Offer the one fix there is

Where the report declined for want of a polarity, and only there, offer via
**AskUserQuestion** to add the key to the register.

Options: **Add it to `variance.polarity` / Leave it declined.**

If they accept, add one entry — the setting's **leaf name**, and one of `lower`,
`higher`, `true` or `false` — and say which you added and why that end is the
stricter one. Do not add keys the report did not decline on; a polarity nobody
needed is a claim about a tool nobody checked.

**Bump `meta.register_contract` if you edit the register**, per the rules in
`docs/01-register-schema.md`, and tell the user you did.

---

## Output

**A clean report:**

```text
register-variance — working tree against <ref>
  <n> gated config file(s) read; nothing moved.
Direction: UNCHANGED
```

**A loosening:**

```text
register-variance — working tree against <ref>
  <file>  LOOSENING
      <key>: <before> → <after>
  <control> declares variance: narrowing-only — this is a violation, not a choice.
Direction: LOOSENING (exit 1)
```

**A declined classification:**

```text
register-variance — working tree against <ref>
  <file>  UNCLASSIFIED
      <key>: the register gives no polarity for this key
  Fixable: add `<key>: <lower|higher|true|false>` to variance.polarity.
Direction: UNCLASSIFIED (exit 3)
```

## Completion states

| State | Trigger |
| --- | --- |
| Reported | The checker ran and its verdict was carried through |
| Stopped — no checker | `register-check` is not installed; `/register-install` first |
| Stopped — no baseline | The revision to compare against does not exist |

## Idempotency

Re-running against the same working tree and the same `--against` ref produces
byte-identical output and the same exit code. This skill reads; it writes no
file, opens no issue, and makes no platform call, so Q2 and Q3 of the
idempotency standard do not apply to it — there is nothing to check for
existence before writing.

The one thing that changes a repeat run's answer is the register itself: adding
a `variance.polarity` entry for a key previously reported `UNCLASSIFIED` moves
that key into a real direction on the next run, and the exit code moves from 3
to 0 or 1 accordingly. That is the intended way to close a declined
classification, and it is why the `Fixable:` line names the entry to add.

## Standards

- Human-readable overview, and why declining beats guessing:
  `${CLAUDE_SKILL_DIR}/README.md`
- The polarity vocabulary and the `variance` declaration it reads are the
  register's, not this skill's — the register is the canonical source for both.

## Calibration

- **Strong:** `${CLAUDE_SKILL_DIR}/examples.md` §Strong — a deployment where
  every value came from the register, every declared locus is wired and stamped,
  and the checker's verdict is reported as given.
- **Weak:** `${CLAUDE_SKILL_DIR}/examples.md` §Weak — a run whose output
  claims more than the artefacts deliver.

## Co-update partners

Canonical source for both shared standards below:
`${CLAUDE_PLUGIN_ROOT}/reference/`. Registered in
`docs/02-skill-family.md`.

- **Write narration shape** (`reference/write-narration.md`) — shared with
  `gate-build`, `gate-iac`, `gate-quality`, `gate-repo`, `gate-secrets`,
  `gate-supply-chain`, `register-adopt`, `register-install` and
  `register-variance`. Change the shape there, never here; ADR 0036 is the
  reason it is one file rather than nine copies.
- **Pre-commit runner precondition** (`reference/pre-commit-runner.md`) —
  shared with every gate skill that writes a pre-commit hook: `gate-build`,
  `gate-iac`, `gate-quality`, `gate-secrets` and `gate-supply-chain`.
- **Provenance stamp and verify contract** — every skill here stamps what it
  writes and verifies through `register-check`. The stamp fields and the
  checker's exit codes are the register's contract, not any one skill's;
  co-update all nine when the contract version changes.
