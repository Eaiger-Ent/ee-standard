# A template is written below its marker, indented to where it goes

Read by every skill in this plugin that writes a YAML template into the target
repository. It is held here, once, rather than repeated in each of them
(ADR 0036, in the standard's own repository).

**A YAML template has two parts, and only the second is written.** The comment
block at the top explains the template to whoever runs the gate. It ends at a
marker line beginning `# ---`, which names the file the payload goes into and
the list it joins. Everything below the marker is the payload. Neither the
comments above it nor the marker line itself are ever written.

**The payload starts at column 0.** It is a YAML document in its own right, so
it parses and lints as shipped (ADR 0059). That means it is not yet at the depth
it is written at. A hook goes into a `hooks:` list and a step into a `steps:`
list, and both lists are nested.

So, after substituting the placeholders:

1. **Find the column of the list it joins.** Read it from the file, never assume
   it. The column of the existing items' `-` is the column of yours: an existing
   `- id:` under the `repo: local` entry's `hooks:`, or an existing `- name:` or
   `- uses:` under the job's `steps:`.
2. **Indent every non-blank line of the payload by that many spaces.** Leave
   blank lines empty. Trailing whitespace on a blank line is a finding in every
   linter that reads the file.
3. **In a file you are creating, use six spaces.** That is the column pre-commit
   and GitHub's own examples put these lists at:

   ```yaml
   repos:
     - repo: local
       hooks:
         - id: example
   ```

   ```yaml
   jobs:
     example:
       steps:
         - name: example
   ```

A payload written at the wrong depth is a different document, not a badly
formatted one: a hook at column 0 becomes a top-level sequence that pre-commit
rejects, and one at the depth of `hooks:` ends the list.

A template whose payload is a whole file, as `.github/dependabot.yml` is, is
written at column 0, as shipped.
