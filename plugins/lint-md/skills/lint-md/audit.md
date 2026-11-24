# Audit the install

Read from Step 1 of `SKILL.md`, after `markdownlint-cli2` is installed and
`<CLI2_INVOCATION> --version` succeeds.

`markdownlint-cli2` pins `markdownlint` exactly, so a fix to anything underneath it (a
transitive dependency such as `re2js` or `katex`) does not reach the project until
`markdownlint-cli2` itself releases. `npm audit fix` can only offer a downgrade. Check, and
where a published fix exists, override it.

## 1. Find what has an advisory of its own

```bash
npm audit --json 2>/dev/null | node -e 'const a=JSON.parse(require("fs").readFileSync(0));for(const [n,v] of Object.entries(a.vulnerabilities||{}))if((v.via||[]).some(x=>typeof x==="object"))console.log(n)'
```

Each name printed is a package with an advisory of its own, not one that is only flagged
through another. No output means nothing to do: say so and return to Step 1b.

## 2. Override each to its newest published version

For each name, find the newest version (`npm view <name> version`) and add it to
`overrides` in `package.json`, keeping any `overrides` already there. Then re-resolve and
re-check:

```bash
npm install && npm audit
```

## 3. Report, and keep it reversible

Tell the user what was overridden and why. Do not carry a fixed version in this skill: the
versions that are safe today are not the ones that will be safe next month.

If `npm audit` still reports a finding, or an override breaks `<CLI2_INVOCATION> --version`,
remove the override you added and tell the user which advisory remains. An audit that
cannot be cleared is the user's decision, not a reason to abort the install.
