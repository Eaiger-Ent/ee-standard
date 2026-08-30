# register-variance — Calibration Examples

## §Strong

A classification run over the working tree against a base ref:

- exactly one classifier was run — the register's. Running a second and
  reconciling the two is how a variance verdict stops being reproducible
- every gated config file the register names was read, and the count is reported
- each changed key is classified as narrowing, loosening or neither, with its
  before and after values shown
- where a control declares `variance: narrowing-only`, a LOOSENING is reported
  as a violation rather than a choice, and the run exits 1
- keys the register gives no polarity for are reported `UNCLASSIFIED` with the
  reason, and exit 3 — declining is the honest answer, and the skill says which
  keys it declined and why
- the one available fix is offered concretely: the `variance.polarity` entry to
  add, spelled out
- a clean run reports `UNCHANGED` rather than staying silent

Output matches the **A clean report**, **A loosening** and **A declined
classification** blocks in `SKILL.md` § Output.

## §Weak

- a key guessed into a direction the register gives no polarity for, rather than
  reported `UNCLASSIFIED` — a confident wrong direction is worse than a declared
  gap, because nobody goes looking for it
- `UNCLASSIFIED` folded into `UNCHANGED`, so the exit code claims a clean tree
- a LOOSENING under `variance: narrowing-only` reported as a finding to consider
  rather than the violation it is
- a second classifier consulted when the first declined
- the `Fixable:` line omitted, leaving the reader with a gap and no remedy
- before and after values summarised in prose instead of shown, so the reader
  cannot check the classification
