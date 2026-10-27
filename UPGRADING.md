# Upgrading an adoption

You adopted the standard with [`START-HERE.md`](START-HERE.md) and a new release
is out. These are the steps to move your repository onto it: six of them, run in
order, with the evidence for each.

**An upgrade moves three things, and they are not linked.** Nothing moves the
others when one moves:

| What | Where it lives | Step |
| --- | --- | --- |
| The plugin: the skills that deploy the gates | The container's Claude Code install | 1 |
| The register's pin: which checker your repository runs | `tools.register-check.install.ref` in your `controls.yaml` | 3 |
| The checker | Your manifest and lockfile, written by `/register-install` | 4 |

Move the plugin and not the pin, and your gates and your checker come from
different releases. That pairing has already failed in practice, so do every step.

**Everything here runs inside the container**, as `START-HERE.md` § 5 does. On
your Mac, `uv run` resolves to a different uv
([`docs/08-adopting.md`](docs/08-adopting.md) § 2.0a). Work on a branch: an
upgrade is a reviewable change like any other.

## 1 — Update the plugin

**Find out where yours came from first.** The plugin is published to two
marketplaces, each install is a separate copy, and both can be installed at once.
Update the copy you have, and do not add the other.

**Every command in this step runs inside Claude Code**, so you never leave the
session. The plugin commands take a `/plugin` prefix there. A shell command takes
a `!` prefix, which runs it in the session and shows the output:

```text
! claude plugin list | grep control-register
```

This must print **one** row. Update that one and no other:

| The row ends | Run |
| --- | --- |
| `@ee-standard` | `/plugin marketplace update ee-standard`, then `/plugin update control-register@ee-standard` |
| `@ee-skills` | `/ee-skills-manage:skill-update` in Claude Code. It updates every plugin from that marketplace, and reports which gates are owed a re-run |

**Two rows means two copies**, and every skill is registered twice. Keep one
and uninstall the other. `ee-standard` is the copy this guide assumes, and it
gets each release first, while `ee-skills` gets it when the release is promoted.
To keep `ee-standard`:

```text
/plugin uninstall control-register@ee-skills
```

Then run `/reload-plugins`, or restart Claude Code. The skills you invoke next
are the new release's.

**Done when** `! claude plugin list | grep control-register` prints one row, at a
version newer than the one you had.

## 2 — See what changed

Find which release you are on and which is newest. Your register names the
first; the second is resolved rather than written here, because a version number
in this file would be out of date the day after the next release:

```bash
old=$(awk '/^    install:/{f=1} f && /ref:/{print $2; exit}' controls.yaml)
new=$(git ls-remote --tags --refs https://github.com/Eaiger-Ent/ee-standard | awk -F/ '{print $NF}' | sort -V | tail -1)
echo "$old -> $new"
```

Both must print. If they are the same, you are current and can stop here.

Read the release notes for every release between the two on the
[releases page](https://github.com/Eaiger-Ent/ee-standard/releases). Each one
leads with a table of what moved, and says what an adopter meets on upgrade.
**A register contract that moved** means a control changed, and step 5 will
name gates to re-run.

Then compare the register each release publishes:

```bash
base=https://raw.githubusercontent.com/Eaiger-Ent/ee-standard
curl -fsSL "$base/$old/controls.published.yaml" -o /tmp/controls.old.yaml
curl -fsSL "$base/$new/controls.published.yaml" -o /tmp/controls.new.yaml
diff /tmp/controls.old.yaml /tmp/controls.new.yaml
```

That diff is the whole of what the standard changed in the register. Step 3
applies it.

## 3 — Move your register

**Edit your `controls.yaml`; do not replace it.** It became yours the moment you
changed it ([`docs/08-adopting.md`](docs/08-adopting.md) § 3.7), and a fresh copy
would overwrite every decision you recorded in it.

Apply each hunk of the diff from step 2 by hand. A release that changes no
control produces one hunk, the `ref:` line under `tools.register-check.install`.
That line must be applied: `/register-install` reads it in step 4, so it decides
which checker you get.

**Done when** the `ref:` line names `$new`:

```bash
grep -A2 '^    install:' controls.yaml
```

## 4 — Move the checker

In Claude Code:

```text
/register-install --repo . --register ./controls.yaml
```

It reads the address from your register, rewrites the pin in your manifest, and
relocks. Re-running it is the intended way to move the pin, and it writes nothing
when the pin is already current.

**Done when** it reports `moved register-check from <old ref> to <new ref>`, and
the checker accepts your register:

```bash
uv run register-check --repo . --register ./controls.yaml schema
```

## 5 — Re-run the gates that are owed

Ask which gates are behind the release you just installed. Name the plugin: in a
shell, nothing tells the checker where Claude Code keeps it.

```bash
plugin=$(claude plugin list --json | uv run --no-project python -c "import json,sys; print(next(p['installPath'] for p in json.load(sys.stdin) if p['id'].startswith('control-register@')))")
uv run register-check deployments --plugin "$plugin"
```

Re-run each gate it names as `STALE`, `UNRECORDED` or `NEVER DEPLOYED` with that
gate's own command, such as `/gate-secrets`. The table of states, and what
each one asks of you, is [`docs/08-adopting.md`](docs/08-adopting.md) § 4.4.

**Done when** the summary line reads `0 owed a deployment`. A release whose notes
say no contract moved should already read that after step 4. If it does not,
the gate was already owed before this upgrade.

## 6 — Run the whole register, and land it

```bash
uv run register-check --repo . --register ./controls.yaml
```

Read the verdict as you did at adoption: `START-HERE.md` § Your first full report
says what each failure means. Exit `3` locally is expected, because the remote
checks answer only inside CI.

Commit the register, manifest, lockfile and anything a gate rewrote, as one
change, and open a pull request. The conformance job in CI runs the register
again with the credential your laptop does not hold. That run is the verdict.

## What an upgrade does not touch

- **Your devcontainer.** The template was copied once, at adoption, and is yours
  now; `gate-build` pins it but never re-copies it. To take a template change,
  compare `plugins/control-register/templates/devcontainer/` between the two
  tags and apply it by hand.
- **Decisions you recorded.** Your `deployment-decisions.yaml` entries stay as
  they are. If one names a version the release moved past, step 5 reports it
  as a **stale record**, which is how you find it.
- **The bots.** Dependabot and Renovate keep their configuration. It changes
  only if you re-run `gate-supply-chain`.
