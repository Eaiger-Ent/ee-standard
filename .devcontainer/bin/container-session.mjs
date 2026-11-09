// Runs this repository's devcontainer on Apple `container`, for a terminal and
// Claude CLI session. ADR 0063 is the decision; docs/20-apple-container-spike.md
// is the evidence for every step below.
//
//   node .devcontainer/bin/container-session.mjs claude     # up, then claude
//   node .devcontainer/bin/container-session.mjs shell      # up, then bash -l
//   node .devcontainer/bin/container-session.mjs up [--rebuild]
//   node .devcontainer/bin/container-session.mjs exec -- <cmd...>
//   node .devcontainer/bin/container-session.mjs stop       # frees host memory
//   node .devcontainer/bin/container-session.mjs down       # stop and delete (volumes kept)
//   node .devcontainer/bin/container-session.mjs check --config <f> [--label <f>] [--calls <f>]
//
// It never reads devcontainer.json. Its inputs are the `devcontainer` CLI's own
// output: `read-configuration`, the `devcontainer.metadata` label the CLI
// writes into the image, and the runtime calls the CLI makes against a stub.
// Anything in those inputs it does not map is refused by name, because a
// setting dropped here is a container that differs from Docker's without
// saying so. tests/test_container_session.py holds the refusals.
//
// Node rather than bash: every input is JSON, macOS ships bash 3.2 and no jq,
// and Node is already on the host to run the CLI.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync, chmodSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const NAME = basename(ROOT);
const IMAGE = `${NAME}-dev:local`;
const CONTAINER = `${NAME}-dev`;
// ADR 0020: the pinned artefact, by the path its lock file owns.
const CLI = join(ROOT, "node_modules", ".bin", "devcontainer");
const KEEP_ALIVE = 'echo Container started; trap "exit 0" TERM; sleep infinity & wait';

// The closed sets. Widening one is a decision about what this launcher can
// reproduce faithfully, so it is made here, in a diff, with a test beside it.
const CONFIG_KEYS = new Set([
  "name", "image", "features", "containerEnv", "initializeCommand", "runArgs",
  "postCreateCommand", "postStartCommand", "remoteUser", "mounts",
  "customizations", "configFilePath",
]);
const LABEL_KEYS = new Set([
  "id", "remoteUser", "mounts", "containerEnv", "postCreateCommand",
  "postStartCommand", "customizations",
]);
// runArgs flags, each taking one value. Both runtimes give them one meaning.
const RUN_ARG_FLAGS = new Set(["--env-file", "--cpus", "--memory"]);
// `docker build` flags the CLI emits that `container build` accepts unchanged.
const BUILD_VALUE_FLAGS = new Set(["-t", "-f", "--build-arg", "--target", "--platform"]);
// Docker-only tokens with no `container build` equivalent (F4). `--load` asks
// for what `container build` does by default: the image lands in the local store.
const BUILD_DROPPED_FLAGS = new Set(["--load"]);
// The keys whose build-time snapshot (the label's last entry) must still match
// devcontainer.json, or the image is stale.
const SNAPSHOT_KEYS = ["remoteUser", "mounts", "containerEnv", "postCreateCommand", "postStartCommand"];
// `container`'s downloads stall without recovering on a network that drops
// connections, and inside a build they stall silently (spike record, "The
// launcher, end to end"). So images are pulled first, where progress shows and
// a stall can be ended: no advance in blobs or bytes for this long is a stall.
const STALL_SECONDS = 120;
const PULL_ATTEMPTS = 3;
// The build argument that carries the base image, as the CLI logs it. The
// build reads the pulled image from the local store (`oci-layout://`).
const BASE_IMAGE_ARG = "_DEV_CONTAINERS_BASE_IMAGE=";

class Refusal extends Error {}

// ---------------------------------------------------------------- validation

function lifecycleErrors(where, key, value) {
  if (value === undefined || typeof value === "string") return [];
  if (Array.isArray(value) && value.every((part) => typeof part === "string")) return [];
  return [`${where}: ${key} is ${JSON.stringify(value)}; only a string or an array of strings is handled`];
}

export function parseMount(mount) {
  const fields = typeof mount === "string"
    ? Object.fromEntries(mount.split(",").map((pair) => {
      const at = pair.indexOf("=");
      return at < 0 ? [pair, ""] : [pair.slice(0, at), pair.slice(at + 1)];
    }))
    : { ...mount };
  const known = new Set(["type", "source", "target"]);
  const extra = Object.keys(fields).filter((key) => !known.has(key));
  if (extra.length) throw new Refusal(`mount ${JSON.stringify(mount)}: unhandled field(s) ${extra.join(", ")}`);
  if (fields.type !== "volume") {
    throw new Refusal(`mount ${JSON.stringify(mount)}: type ${JSON.stringify(fields.type)} is not handled; only type=volume`);
  }
  if (!fields.source || !fields.target) throw new Refusal(`mount ${JSON.stringify(mount)}: needs source and target`);
  return { source: fields.source, target: fields.target };
}

export function parseRunArgs(runArgs = []) {
  const parsed = {};
  for (let i = 0; i < runArgs.length; i += 1) {
    let flag = runArgs[i];
    let value;
    const at = flag.indexOf("=");
    if (flag.startsWith("--") && at > 0) {
      value = flag.slice(at + 1);
      flag = flag.slice(0, at);
    }
    if (!RUN_ARG_FLAGS.has(flag)) throw new Refusal(`runArgs: ${flag} is not handled`);
    if (value === undefined) {
      i += 1;
      value = runArgs[i];
    }
    if (value === undefined) throw new Refusal(`runArgs: ${flag} has no value`);
    if (flag in parsed) throw new Refusal(`runArgs: ${flag} is given twice`);
    parsed[flag] = value;
  }
  return parsed;
}

function collect(errors, fn) {
  try {
    return fn();
  } catch (error) {
    if (!(error instanceof Refusal)) throw error;
    errors.push(error.message);
    return undefined;
  }
}

export function validateConfig(output) {
  const errors = [];
  const config = output.configuration ?? {};
  for (const key of Object.keys(config)) {
    if (!CONFIG_KEYS.has(key)) errors.push(`devcontainer.json: ${key} is not handled by this launcher`);
  }
  if (config.image === undefined) errors.push("devcontainer.json: only an `image`-based configuration is handled");
  collect(errors, () => parseRunArgs(config.runArgs));
  for (const mount of config.mounts ?? []) collect(errors, () => parseMount(mount));
  for (const key of ["initializeCommand", "postCreateCommand", "postStartCommand"]) {
    errors.push(...lifecycleErrors("devcontainer.json", key, config[key]));
  }
  // The workspace's parent is what gets mounted (F5), so the CLI's workspace
  // folder must be exactly one level below /workspaces.
  const folder = output.workspace?.workspaceFolder ?? "";
  if (!/^\/workspaces\/[^/]+$/.test(folder)) {
    errors.push(`workspace: workspaceFolder ${JSON.stringify(folder)} is not /workspaces/<name>`);
  }
  return errors;
}

export function validateLabel(entries, output) {
  const errors = [];
  if (!Array.isArray(entries) || entries.length === 0) return ["image label: devcontainer.metadata is missing or empty"];
  entries.forEach((entry, index) => {
    const where = `image label entry ${index}${entry.id ? ` (${entry.id})` : ""}`;
    for (const key of Object.keys(entry)) {
      if (!LABEL_KEYS.has(key)) errors.push(`${where}: ${key} is not handled by this launcher`);
    }
    for (const mount of entry.mounts ?? []) collect(errors, () => parseMount(mount));
    for (const key of ["postCreateCommand", "postStartCommand"]) {
      errors.push(...lifecycleErrors(where, key, entry[key]));
    }
  });
  // The last entry is devcontainer.json as it was at build time.
  if (output) {
    const last = entries[entries.length - 1];
    const config = output.configuration ?? {};
    for (const key of SNAPSHOT_KEYS) {
      if (JSON.stringify(last[key]) !== JSON.stringify(config[key])) {
        errors.push(`image label: ${key} differs from devcontainer.json; the image is stale, run \`up --rebuild\``);
      }
    }
  }
  return errors;
}

export function translateBuild(argv) {
  let rest;
  if (argv[0] === "buildx" && argv[1] === "build") rest = argv.slice(2);
  else if (argv[0] === "build") rest = argv.slice(1);
  else throw new Refusal(`runtime call ${JSON.stringify(argv)} is not a build`);
  const out = ["build"];
  let context;
  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (BUILD_DROPPED_FLAGS.has(token)) continue;
    if (BUILD_VALUE_FLAGS.has(token)) {
      if (rest[i + 1] === undefined) throw new Refusal(`build: ${token} has no value`);
      out.push(token, rest[i + 1]);
      i += 1;
    } else if (token.startsWith("-")) {
      throw new Refusal(`build: ${token} is not handled`);
    } else if (context === undefined) {
      context = token;
    } else {
      throw new Refusal(`build: a second positional argument ${JSON.stringify(token)}`);
    }
  }
  if (context === undefined) throw new Refusal("build: no context directory");
  out.push(context);
  return out;
}

// The calls the CLI makes to learn about a runtime, which the stub answers
// with nothing. With --platform the CLI reads the image from the registry, so
// an empty answer is harmless (F2).
function isProbe(argv) {
  const [first, second] = argv;
  if (first === "-v" || first === "version") return true;
  if (first === "buildx" && second === "version") return true;
  if (first === "inspect" && second === "--type" && argv[2] === "image") return true;
  return first === "pull";
}

export function planBuilds(calls) {
  const errors = [];
  const builds = [];
  for (const argv of calls) {
    if (isProbe(argv)) continue;
    const translated = collect(errors, () => translateBuild(argv));
    if (translated) builds.push(translated);
  }
  if (!errors.length && builds.length === 0) errors.push("the CLI made no build call");
  return { builds, errors };
}

export function imagesToPull(builds) {
  const images = [];
  for (const argv of builds) {
    argv.forEach((token, i) => {
      if (argv[i - 1] === "--build-arg" && token.startsWith(BASE_IMAGE_ARG)) images.push(token.slice(BASE_IMAGE_ARG.length));
    });
  }
  return [...new Set(images)];
}

// What a `container image pull --progress plain` line says has been done: the
// phase, the blobs fetched and the bytes fetched. The elapsed-time counter is
// deliberately not part of it, because a stalled pull keeps counting.
export function progressMark(line) {
  const phase = line.match(/^\[(\d+)\/\d+\]/);
  const blobs = line.match(/(\d+) of \d+ blobs/);
  // "3.6/108.7 MB": the unit is written once, after the total.
  const bytes = line.match(/([\d.]+)(?: ?[KMGT]?B)?\/[\d.]+ ?[KMGT]?B/);
  if (!phase && !blobs && !bytes) return undefined;
  return [phase?.[1], blobs?.[1], bytes?.[1]].join("|");
}

export function merge(output, entries) {
  const config = output.configuration;
  const merged = { remoteUser: config.remoteUser, mounts: [], containerEnv: {}, postCreate: [], postStart: [] };
  const byTarget = new Map();
  for (const entry of entries) {
    if (entry.remoteUser) merged.remoteUser = entry.remoteUser;
    Object.assign(merged.containerEnv, entry.containerEnv ?? {});
    for (const mount of entry.mounts ?? []) {
      const parsed = parseMount(mount);
      byTarget.set(parsed.target, parsed);
    }
    if (entry.postCreateCommand !== undefined) merged.postCreate.push(entry.postCreateCommand);
    if (entry.postStartCommand !== undefined) merged.postStart.push(entry.postStartCommand);
  }
  merged.mounts = [...byTarget.values()];
  if (!merged.remoteUser) throw new Refusal("no remoteUser; BLD-001 requires one, and this launcher never runs a session as root");
  return merged;
}

// ------------------------------------------------------------------- running

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, { stdio: "inherit", ...options });
  if (result.error) throw result.error;
  return result;
}

function must(cmd, args, options = {}) {
  const result = run(cmd, args, options);
  if (result.status !== 0) {
    throw new Error(`${cmd} ${args[0] ?? ""} exited ${result.status}`);
  }
  return result;
}

function capture(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], ...options });
  if (result.error) throw result.error;
  return result;
}

function arch() {
  if (process.arch === "arm64") return "arm64";
  if (process.arch === "x64") return "amd64";
  throw new Refusal(`host architecture ${process.arch} is not handled`);
}

function preflight() {
  if (process.platform !== "darwin") throw new Refusal("Apple `container` runs on macOS; use Docker elsewhere");
  if (!existsSync(CLI)) throw new Refusal(`${CLI} is missing; run \`npm ci\` in ${ROOT} on the host`);
  const status = capture("container", ["system", "status"]);
  if (status.status !== 0) throw new Refusal("`container` services are not running; run `container system start`");
}

function makeStub() {
  const dir = mkdtempSync(join(tmpdir(), "container-session-"));
  const log = join(dir, "calls");
  const stub = join(dir, "docker");
  // NUL-separated arguments, one record-separator token per call, so no
  // argument can be mistaken for a boundary.
  writeFileSync(stub, `#!/bin/sh\nprintf '%s\\0' "$@" >> '${log}'\nprintf '\\036\\0' >> '${log}'\nexit 0\n`);
  chmodSync(stub, 0o755);
  return { dir, stub, calls: () => readCalls(log) };
}

function withStub(fn) {
  const context = makeStub();
  try {
    return fn(context);
  } finally {
    rmSync(context.dir, { recursive: true, force: true });
  }
}

async function withStubAsync(fn) {
  const context = makeStub();
  try {
    return await fn(context);
  } finally {
    rmSync(context.dir, { recursive: true, force: true });
  }
}

function readCalls(log) {
  if (!existsSync(log)) return [];
  const calls = [];
  let current = [];
  for (const token of readFileSync(log, "utf8").split("\0").slice(0, -1)) {
    if (token === "\x1e") {
      calls.push(current);
      current = [];
    } else {
      current.push(token);
    }
  }
  return calls;
}

function readConfiguration() {
  return withStub(({ stub }) => {
    const result = capture(CLI, ["read-configuration", "--workspace-folder", ROOT, "--docker-path", stub]);
    if (result.status !== 0) throw new Error(`devcontainer read-configuration exited ${result.status}\n${result.stderr}`);
    return JSON.parse(result.stdout);
  });
}

function readLabel() {
  const result = capture("container", ["image", "inspect", IMAGE]);
  if (result.status !== 0) return undefined;
  const platform = arch();
  for (const image of JSON.parse(result.stdout)) {
    for (const variant of image.variants ?? []) {
      if (variant.platform?.os !== "linux" || variant.platform?.architecture !== platform) continue;
      const label = variant.config?.config?.Labels?.["devcontainer.metadata"];
      if (label) return JSON.parse(label);
    }
  }
  return [];
}

function refuseAll(errors) {
  if (errors.length) throw new Refusal(errors.join("\n  "));
}

function builderImage() {
  const result = capture("container", ["system", "property", "list"]);
  if (result.status !== 0) return undefined;
  const section = result.stdout.split(/^\[build\]\s*$/m)[1]?.split(/^\[/m)[0] ?? "";
  return section.match(/^image\s*=\s*"([^"]+)"/m)?.[1];
}

function pullOnce(image) {
  return new Promise((done) => {
    const child = spawn("container", ["image", "pull", "--progress", "plain", "--platform", `linux/${arch()}`, image], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let mark;
    let advanced = Date.now();
    let tail = "";
    let shown = "";
    let stalled = false;
    const read = (chunk) => {
      for (const line of chunk.toString().split(/[\r\n]+/)) {
        if (!line.trim()) continue;
        tail = line.trim();
        const next = progressMark(line);
        if (next !== undefined && next !== mark) {
          mark = next;
          advanced = Date.now();
        }
      }
    };
    child.stdout.on("data", read);
    child.stderr.on("data", read);
    const timer = setInterval(() => {
      if (tail && tail !== shown) {
        process.stderr.write(`  ${tail}\n`);
        shown = tail;
      }
      if (Date.now() - advanced > STALL_SECONDS * 1000) {
        stalled = true;
        child.kill("SIGTERM");
      }
    }, 10000);
    child.on("close", (code) => {
      clearInterval(timer);
      done({ ok: code === 0 && !stalled, stalled, tail });
    });
  });
}

async function ensureImage(image) {
  if (capture("container", ["image", "inspect", image]).status === 0) return;
  let last = {};
  for (let attempt = 1; attempt <= PULL_ATTEMPTS; attempt += 1) {
    process.stderr.write(`container-session: pulling ${image} (attempt ${attempt} of ${PULL_ATTEMPTS})\n`);
    last = await pullOnce(image);
    if (last.ok) return;
    process.stderr.write(last.stalled
      ? `container-session: no progress for ${STALL_SECONDS}s; stopping that pull\n`
      : `container-session: pull failed: ${last.tail}\n`);
  }
  throw new Error(`could not pull ${image} after ${PULL_ATTEMPTS} attempts (last: ${last.tail}). `
    + "The network is dropping or stalling connections; run `up` again later.");
}

async function build(resources) {
  await withStubAsync(async ({ dir, stub, calls }) => {
    const result = run(CLI, [
      "build", "--workspace-folder", ROOT, "--frozen-lockfile",
      "--platform", `linux/${arch()}`, "--image-name", IMAGE, "--docker-path", stub,
    ], { env: { ...process.env, TMPDIR: dir }, stdio: ["ignore", "ignore", "inherit"] });
    if (result.status !== 0) throw new Error(`devcontainer build exited ${result.status}`);
    const { builds, errors } = planBuilds(calls());
    refuseAll(errors);
    for (const image of [builderImage(), ...imagesToPull(builds)].filter(Boolean)) await ensureImage(image);
    const sizing = [];
    if (resources["--cpus"]) sizing.push("--cpus", resources["--cpus"]);
    if (resources["--memory"]) sizing.push("--memory", resources["--memory"]);
    try {
      for (const argv of builds) must("container", [argv[0], ...sizing, "--progress", "plain", ...argv.slice(1)]);
    } finally {
      // The builder holds its own allocation until stopped (F8).
      run("container", ["builder", "stop"], { stdio: "ignore" });
    }
  });
}

function containerState() {
  const result = capture("container", ["list", "--all", "--format", "json"]);
  if (result.status !== 0) throw new Error("container list failed");
  const found = JSON.parse(result.stdout).find((c) => c.configuration?.id === CONTAINER);
  return found ? found.status?.state ?? "unknown" : "missing";
}

function shellCommand(command) {
  return typeof command === "string" ? ["/bin/sh", "-c", command] : command;
}

function execArgs(merged, folder, interactive) {
  const user = merged.remoteUser;
  const args = ["exec"];
  if (interactive) args.push("-i", ...(process.stdin.isTTY ? ["-t"] : []));
  // F6: `container exec -u` sets HOME but not USER or LOGNAME. Neither is a
  // secret; secrets reach the container only through --env-file on `run` (F7).
  args.push("-u", user, "-e", `USER=${user}`, "-e", `LOGNAME=${user}`, "-w", folder, CONTAINER);
  return args;
}

async function up({ rebuild = false } = {}) {
  preflight();
  const output = readConfiguration();
  refuseAll(validateConfig(output));
  const config = output.configuration;
  const resources = parseRunArgs(config.runArgs);
  if (rebuild && containerState() !== "missing") down();
  if (rebuild || readLabel() === undefined) await build(resources);
  const entries = readLabel();
  refuseAll(validateLabel(entries, output));
  const merged = merge(output, entries);
  const folder = output.workspace.workspaceFolder;

  if (config.initializeCommand !== undefined) {
    const [cmd, ...args] = shellCommand(config.initializeCommand);
    must(cmd, args, { cwd: ROOT });
  }

  const state = containerState();
  if (state === "missing") {
    const args = ["run", "-d", "--name", CONTAINER];
    if (resources["--cpus"]) args.push("--cpus", resources["--cpus"]);
    if (resources["--memory"]) args.push("--memory", resources["--memory"]);
    if (resources["--env-file"]) {
      const file = resources["--env-file"];
      args.push("--env-file", isAbsolute(file) ? file : join(ROOT, file));
    }
    // containerEnv is committed configuration, never a secret.
    for (const [key, value] of Object.entries(merged.containerEnv)) args.push("-e", `${key}=${value}`);
    for (const { source, target } of merged.mounts) {
      args.push("--mount", `type=volume,source=${source},target=${target}`);
    }
    // F5: the parent, so the checkout is not the mount point git distrusts.
    args.push("-v", `${dirname(ROOT)}:/workspaces`, "-w", folder);
    args.push("--entrypoint", "/bin/sh", IMAGE, "-c", KEEP_ALIVE);
    must("container", args, { stdio: ["ignore", "ignore", "inherit"] });
    for (const command of merged.postCreate) must("container", [...execArgs(merged, folder, false), ...shellCommand(command)]);
  } else if (state === "stopped") {
    must("container", ["start", CONTAINER], { stdio: ["ignore", "ignore", "inherit"] });
  } else if (state !== "running") {
    throw new Refusal(`container ${CONTAINER} is ${state}; run \`down\` and try again`);
  }
  if (state !== "running") {
    for (const command of merged.postStart) must("container", [...execArgs(merged, folder, false), ...shellCommand(command)]);
  }
  return { merged, folder };
}

function down() {
  run("container", ["stop", CONTAINER], { stdio: "ignore" });
  run("container", ["delete", CONTAINER], { stdio: "ignore" });
}

async function attach(command) {
  const { merged, folder } = await up();
  const result = run("container", [...execArgs(merged, folder, true), ...command]);
  return result.status ?? 1;
}

function check(argv) {
  const files = {};
  for (let i = 0; i < argv.length; i += 2) files[argv[i].replace(/^--/, "")] = argv[i + 1];
  if (!files.config) throw new Refusal("check needs --config <read-configuration output>");
  const output = JSON.parse(readFileSync(files.config, "utf8"));
  const errors = validateConfig(output);
  let builds = [];
  if (files.label) errors.push(...validateLabel(JSON.parse(readFileSync(files.label, "utf8")), output));
  if (files.calls) {
    const plan = planBuilds(JSON.parse(readFileSync(files.calls, "utf8")));
    errors.push(...plan.errors);
    builds = plan.builds;
  }
  refuseAll(errors);
  process.stdout.write(`${JSON.stringify({ builds, pulls: imagesToPull(builds) })}\n`);
  return 0;
}

async function main(argv) {
  const [command, ...rest] = argv;
  switch (command) {
    case "up": await up({ rebuild: rest.includes("--rebuild") }); return 0;
    case "claude": return attach(["claude", ...rest]);
    case "shell": return attach(["bash", "-l"]);
    case "exec": return attach(rest[0] === "--" ? rest.slice(1) : rest);
    case "stop": run("container", ["stop", CONTAINER]); return 0;
    case "down": down(); return 0;
    case "check": return check(rest);
    default:
      process.stderr.write("usage: container-session.mjs up [--rebuild] | claude [args] | shell | exec -- <cmd> | stop | down | check --config <f> [--label <f>] [--calls <f>]\n");
      return 2;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).then((code) => {
    process.exitCode = code;
  }, (error) => {
    if (error instanceof Refusal) {
      process.stderr.write(`container-session: refused:\n  ${error.message}\n`);
      process.exitCode = 2;
    } else {
      process.stderr.write(`container-session: ${error.message}\n`);
      process.exitCode = 1;
    }
  });
}
