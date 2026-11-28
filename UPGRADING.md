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

### Moving past register contract 38: the Apple `container` files

Register contract 39 makes Apple `container` a first-class container engine
([ADR 0066](docs/adr/0066-apple-container-is-a-first-class-engine.md)). Its register
pins the `devcontainer` CLI the engine runs, in
`tools.devcontainer-cli`, by `.devcontainer/package-lock.json`. A repository
without that file fails `tool_versions_match_register` in step 6. So if your
diff in step 2 adds `devcontainer-cli`, add the files the template now carries.
This applies whichever engine you run: adding them changes nothing on Docker.

Copy them from the tag you are moving to, in the shell where step 2 set `$base`
and `$new`. The first line stops if you already have a `.devcontainer/package.json`,
because that file is yours and this step must not overwrite it. Merge the
`@devcontainers/cli` pin into it by hand instead:

```bash
[ ! -e .devcontainer/package.json ] || { echo ".devcontainer/package.json exists: merge by hand"; false; }
tmpl="$base/$new/plugins/control-register/templates/devcontainer"
mkdir -p .devcontainer/bin
curl -fsSL "$tmpl/bin/container-session.mjs" -o .devcontainer/bin/container-session.mjs
curl -fsSL "$tmpl/package.json" -o .devcontainer/package.json
curl -fsSL "$tmpl/package-lock.json" -o .devcontainer/package-lock.json
grep -qx 'node_modules/' .devcontainer/.gitignore || printf '\n# The pinned devcontainer CLI, installed by npm ci.\nnode_modules/\n' >> .devcontainer/.gitignore
git add .devcontainer/bin/container-session.mjs .devcontainer/package.json .devcontainer/package-lock.json .devcontainer/.gitignore
```

To run on Apple `container` as well, also give the container a resource floor.
The template's `runArgs` now ends `"--cpus", "4", "--memory", "4g"`. Without
those flags an Apple container gets 1 GiB. Add the same four values to your
`runArgs`. Then, **on the Mac rather than in the container**, start a session as
[`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md) § 1 does:

```bash
container system start
npm ci --prefix .devcontainer --no-audit --no-fund
node .devcontainer/bin/container-session.mjs up
```

If the launcher **refuses**, it names the `devcontainer.json` setting it cannot
reproduce. Stay on Docker and keep the refusal: it is the record of why. The
files you added still satisfy contract 39.

**Done when** `git status --short .devcontainer` lists the files above and
nothing else, and, if you ran the launcher, `up` ended with `check-auth.sh`'s
table, every line ✓. Step 6 confirms the register agrees.

### Moving past register contract 39: an update entry per lockfile directory

Register contract 40 makes SUP-002 require a Dependabot entry for **every
directory holding a tracked lockfile**, not one entry per ecosystem anywhere.
The case it was found on is yours if you took contract 39's step above:
`.devcontainer/package-lock.json` sits outside the root, and an `npm` entry at
`/`, or none, proposes it nothing. Step 6 fails it as *no update entry for: node
at /.devcontainer*.

Step 5 re-runs `/gate-supply-chain`, which writes the entry. To add it by hand
instead, append to `.github/dependabot.yml`:

```yaml
  - package-ecosystem: npm
    directory: /.devcontainer
    schedule:
      interval: weekly
```

A lockfile nothing should update, such as a test fixture's, goes in SUP-002's
`exclude_directories:` as a Dependabot `directories` glob. That is a loosening,
recorded in your register where a reviewer sees it. A Renovate configuration
that covers every ecosystem is unaffected: Renovate finds nested lockfiles
itself.

**Done when** `uv run register-check run --control SUP-002` passes.

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

Every gate you owe a run carries a line beginning `→` that names its command,
such as `/gate-secrets`. A gate is a Claude Code skill, so run that command in a
Claude Code session in this repository, not in the shell. Go by the `→` lines
rather than the state column: a gate reading `STACK UNWIRED` has current stamps
but has not wired a stack that now applies, and it is owed a run all the same.
Lines under *Pinned, and no bot will ever propose moving it* are information,
not actions. The table of states, and what each one asks of you, is
[`docs/08-adopting.md`](docs/08-adopting.md) § 4.4.

**Then deploy the controls no gate in `control-register` deploys.** They are
listed under *Deployed by a skill this plugin does not ship*. The list comes from
`deployed_by` in the register you moved in step 3, not from what has been
deployed, so a control appears there even if nothing ever deployed it. `0 owed`
in the summary line does not include them. Each row shows the skill version its
stamps record and the version you have installed, and a `→` line when the
installed version is newer. `UNRECORDED` means no stamp names the control, and
that is normal: neither skill writes a stamp, so the report cannot tell whether
it has run.

Each skill named there is a plugin of its own: `lint-md` deploys DOC-001 and
`lint-yaml` deploys YML-001. For each one, `claude plugin list` shows whether it
is installed, and from which marketplace.

Install any that are missing, with `claude plugin install <name>@ee-standard`
(or `@ee-skills`), and update any that are present, as step 1 did for
`control-register`. Then run each one in Claude Code as `/<name>`, whether it is
new or was there before: a release that adds a control to the register adds
work for that skill to do. [`docs/08-adopting.md`](docs/08-adopting.md) § 3 is
the full route, including what each skill leaves for you.

**Done when** the summary line reads `0 owed a deployment`, and
`uv run register-check run --control <ID>` passes for each control those skills
deploy. A release whose notes say no contract moved should already read that
after step 4. If it does not, the gate was already owed before this upgrade.

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
  now; `gate-build` pins it but never re-copies it. The one exception is the
  Apple `container` files in step 3, which register contract 39 requires and you
  copy by hand. `register-check deployments` says whether your launcher is
  still the plugin's copy. To take a template change,
  compare `plugins/control-register/templates/devcontainer/` between the two
  tags and apply it by hand.
- **Decisions you recorded.** Your `deployment-decisions.yaml` entries stay as
  they are. If one names a version the release moved past, step 5 reports it
  as a **stale record**, which is how you find it.
- **The bots.** Dependabot and Renovate keep their configuration. It changes
  only if you re-run `gate-supply-chain`.
