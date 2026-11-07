# A question the adoption plan showed is answered by the plan

One home for this rule rather than a copy in each skill (ADR 0036, in the
standard's own repository). The decision is ADR 0062.

Read by `register-adopt` and by every gate: `gate-build`, `gate-supply-chain`,
`gate-secrets`, `gate-quality`, `gate-iac` and `gate-repo`.

## Why

On a first deployment every gate question is answered *yes*. Asked one at a
time, mid-run, each has less context than the plan had. So the gates report
their questions before anything runs, the plan lists them in plain English,
and one answer covers every question the plan showed.

**A question the plan did not show is still asked.** That is the whole safety
of this rule. An answer covers what was on screen, and nothing else.

## `--plan`: report the questions, write nothing

A gate given `--plan` runs its pre-flight and its "report the plan" step, then
stops. It writes no file, makes no call other than a `GET`, and asks nothing.
It ends with this block, one row per question it would ask:

```text
QUESTIONS <gate>
kind      subject                                   answer           says
takeover  .devcontainer/Dockerfile                  Adopt and stamp  rewrites the image line to a digest pin, and stamps the file
choice    test command                              uv run pytest    wires `uv run pytest` at pre-push and in CI
removal   .flake8                                   Remove           deletes .flake8; ruff replaces it
platform  POST /repos/{owner}/{name}/rulesets       Apply now        protects main for every collaborator: PRs only, a passing check, no force-push
          body sha256 <64 hex>
END
```

- **kind** is one of `takeover`, `removal`, `choice` or `platform`.
- **subject** is the exact file, the question's name for a choice, or the
  method and route for a platform call. A platform row also carries the SHA-256
  of the request body exactly as it would be sent. For `gate-repo` that is the
  ruleset body Step 1 would record, worked out without writing it.
- **answer** is one of the options the question offers. For a choice it is the
  answer the gate would propose: the one already in use, else the register's
  first accepted spelling that reaches the pinned artefact.
- **says** is one plain-English sentence saying what that answer will do. It
  is what the person reads, so it names the file and the effect, not the
  question.

A gate with no questions prints `QUESTIONS <gate>` and `END` with nothing
between them.

## `--answers <path>`: use the plan's answer, or ask

`register-adopt` writes the answers it was given to
`$(git rev-parse --git-dir)/register-adopt/answers.json`. That is inside `.git`,
so it is never tracked or committed. Each entry has `gate`, `kind`, `subject`,
`answer` and `says`, and a platform entry also has `body_sha256`.

Before asking any question, a gate given `--answers` looks for an entry for
itself with the same kind and subject:

| Kind | It is the same question when |
| --- | --- |
| `takeover` | Same file |
| `removal` | Same file or hook |
| `choice` | Same question, and the answer is still one the register accepts |
| `platform` | Same method and route, and the same `body_sha256` as the body about to be sent |

**On a match**, use the answer, and print one line in place of the question:

```text
Answered in the adoption plan: <says> → <answer>
```

**On no match, ask**, exactly as the skill would without `--answers`. A
platform call whose body or method changed since the plan is a different call.
For example, a `POST` that became a `PUT` because a ruleset appeared. A `PUT`
replaces a ruleset entire, so it is asked.

**An entry is never stretched.** An answer to one file is not an answer to its
neighbour. An answer to a `POST` is not an answer to a `DELETE`.

## What this does not change

- **Ordering.** `gate-repo` still lands the earlier gates' work before its
  first call. It still removes classic protection only after the ruleset reads
  back as active, and that read is a `GET`.
- **`--yes`.** No gate takes it. What `--yes` answers is
  `reference/unattended.md`'s, and it does not answer a plan that lists a
  platform call.
- **Errors.** A question that exists because something is wrong, such as a
  register that cannot be satisfied, is not foreseeable from a plan. It is
  never listed, so it is always asked.
