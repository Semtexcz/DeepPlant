import { spawn, spawnSync, type ChildProcess } from 'node:child_process'
import path from 'node:path'
import { setTimeout as delay } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'

/**
 * Real-application lifecycle for the Engineering Editor browser E2E suite.
 *
 * The suite is evidence for the product path users actually receive, so this
 * helper always starts a real application boundary and its own loopback server.
 * It never starts a Vite dev/preview server, a test-only FastAPI app, or
 * `create_editor_api()` directly. Two launchers are supported, and the same
 * browser workflow (the specs) runs against either:
 *
 *     source     `uv run deepplant ui <path> --port 0`   developer checkout
 *     packaged   the standalone Editor launcher          Issue #85 artifact
 *
 * The packaged launcher is selected through the environment:
 *
 *     DEEPLANT_EDITOR_EXECUTABLE   path to the installed/extracted launcher
 *     DEEPLANT_EDITOR_PROJECT      model path, so it can live outside the repo
 *
 * Packaging concerns stop here: the feature specs never mention them.
 *
 * Readiness is the application's own announcement of the loopback URL:
 *
 *     DeepPlant Engineering Editor (read-only Process/PFD)
 *       project: <path>
 *       open:    http://127.0.0.1:<port>/
 *       press Ctrl+C to stop
 *
 * Port allocation stays owned by `--port 0` (the OS picks a free port); this
 * helper only parses the URL the application prints and never re-implements
 * socket allocation. There is no arbitrary readiness sleep.
 */

const SUPPORT_DIR = path.dirname(fileURLToPath(import.meta.url))

/** `apps/editor` - the frontend application directory. */
const EDITOR_DIR = path.resolve(SUPPORT_DIR, '..', '..')

/**
 * Repository root, used as the working directory for the source launcher:
 * `uv run` discovers the project from there. The packaged launcher never uses
 * it - asset resolution does not depend on the working directory (Issue #85).
 */
const REPO_ROOT = path.resolve(EDITOR_DIR, '..', '..')

/** The canonical realistic process fragment, resolved from the repository root. */
export const REALISTIC_PROJECT = path.join(
  REPO_ROOT,
  'examples',
  'realistic-process-fragment',
  'plant.yaml',
)

/** Presentation override the realistic fragment needs for a projectable view. */
export const VESSEL_ROLE_OVERRIDE = ['PS-vessel=vessel'] as const

const ANNOUNCED_URL = /^\s*open:\s+(http:\/\/127\.0\.0\.1:\d+\/)\s*$/
const STARTUP_TIMEOUT_MS = 30_000
const READY_TIMEOUT_MS = 20_000
const POLL_INTERVAL_MS = 100
const SHUTDOWN_GRACE_MS = 5_000
const FORCE_KILL_WAIT_MS = 5_000
const MAX_LOG_CHARS = 32_000

export interface EditorServerOptions {
  /**
   * Repeatable `--symbol-role STEP=ROLE` presentation overrides.
   *
   * The happy path passes `PS-vessel=vessel`; the valid-but-unprojectable error
   * path deliberately omits it.
   */
  readonly symbolRoles?: readonly string[]
}

export interface EditorServer {
  /** Loopback base URL announced by the real application, e.g. `http://127.0.0.1:53421/`. */
  readonly baseUrl: string
  /** Stop the real application process tree: graceful first, forced only when required. */
  stop(): Promise<void>
  /** Captured application stdout/stderr, bounded; for failure diagnostics only. */
  logs(): string
}

/** How to start the application under test. */
interface LaunchSpec {
  /** Human-readable launcher name used in failure messages. */
  readonly label: string
  readonly command: string
  readonly args: readonly string[]
  readonly cwd: string
}

/**
 * Resolve the launcher: the packaged standalone application when
 * `DEEPLANT_EDITOR_EXECUTABLE` is set, otherwise the developer `deepplant ui`.
 *
 * Both produce the identical launch message and the identical HTTP surface, so
 * the specs cannot tell them apart - which is exactly the point.
 */
function resolveLaunchSpec(symbolRoles: readonly string[]): LaunchSpec {
  const project = process.env['DEEPLANT_EDITOR_PROJECT'] ?? REALISTIC_PROJECT
  const executable = process.env['DEEPLANT_EDITOR_EXECUTABLE']
  const roleArgs = symbolRoles.flatMap((entry) => ['--symbol-role', entry])
  if (executable !== undefined && executable !== '') {
    return {
      label: 'the packaged DeepPlant Editor',
      command: executable,
      args: [project, '--port', '0', '--no-browser', ...roleArgs],
      // A packaged application is self-contained, so it runs from wherever the
      // model lives - outside the checkout.
      cwd: path.dirname(project),
    }
  }
  return {
    label: '`deepplant ui`',
    command: 'uv',
    args: ['run', 'deepplant', 'ui', project, '--port', '0', ...roleArgs],
    cwd: REPO_ROOT,
  }
}

interface LogBuffer {
  push(chunk: string): void
  text(): string
}

interface ExitTracker {
  done: Promise<void>
  spawnError: Error | null
  code: number | null
  signal: NodeJS.Signals | null
}

/**
 * Process-group ids started by this helper.
 *
 * Used only as a last-resort safety net so an interrupted worker cannot leak a
 * Uvicorn process. Cleanup never signals anything but these groups.
 */
const liveGroups = new Set<number>()
let safetyNetInstalled = false

function installSafetyNet(): void {
  if (safetyNetInstalled) {
    return
  }
  safetyNetInstalled = true
  process.on('exit', () => {
    for (const pid of liveGroups) {
      try {
        process.kill(-pid, 'SIGKILL')
      } catch {
        // The process group is already gone; there is nothing left to clean up.
      }
    }
  })
}

function createLogBuffer(): LogBuffer {
  let text = ''
  return {
    push(chunk: string): void {
      text += chunk
      if (text.length > MAX_LOG_CHARS) {
        text = text.slice(-MAX_LOG_CHARS)
      }
    },
    text(): string {
      return text
    },
  }
}

function createExitTracker(child: ChildProcess): ExitTracker {
  const tracker: ExitTracker = {
    done: Promise.resolve(),
    spawnError: null,
    code: null,
    signal: null,
  }
  tracker.done = new Promise<void>((resolve) => {
    child.once('exit', (code, signal) => {
      tracker.code = code
      tracker.signal = signal
      resolve()
    })
    child.once('error', (error: Error) => {
      tracker.spawnError = error
      resolve()
    })
  })
  return tracker
}

function findAnnouncedUrl(logText: string): string | null {
  for (const line of logText.split('\n')) {
    const match = ANNOUNCED_URL.exec(line)
    if (match?.[1] !== undefined) {
      return match[1]
    }
  }
  return null
}

/** Fail clearly when the application died or could not be spawned before it was ready. */
function assertStillStarting(tracker: ExitTracker, log: LogBuffer, label: string): void {
  if (tracker.spawnError !== null) {
    throw new Error(`could not start ${label}: ${tracker.spawnError.message}\n${log.text()}`)
  }
  if (tracker.code !== null || tracker.signal !== null) {
    throw new Error(
      `${label} exited before the editor became ready ` +
        `(code ${tracker.code ?? 'null'}, signal ${tracker.signal ?? 'none'}).\n${log.text()}`,
    )
  }
}

async function waitForAnnouncedUrl(
  tracker: ExitTracker,
  log: LogBuffer,
  label: string,
): Promise<string> {
  const deadline = Date.now() + STARTUP_TIMEOUT_MS
  while (Date.now() < deadline) {
    const url = findAnnouncedUrl(log.text())
    if (url !== null) {
      return url
    }
    assertStillStarting(tracker, log, label)
    await delay(POLL_INTERVAL_MS)
  }
  throw new Error(
    `${label} did not announce a loopback URL within ${STARTUP_TIMEOUT_MS} ms.\n${log.text()}`,
  )
}

/**
 * Close the small bind-then-serve window after the URL announcement.
 *
 * The CLI binds the loopback socket before it prints, so the URL remains the
 * readiness boundary; this only confirms Uvicorn is accepting connections.
 */
async function waitForServing(
  baseUrl: string,
  tracker: ExitTracker,
  log: LogBuffer,
  label: string,
): Promise<void> {
  const deadline = Date.now() + READY_TIMEOUT_MS
  let lastFailure = 'no response yet'
  while (Date.now() < deadline) {
    assertStillStarting(tracker, log, label)
    try {
      const response = await fetch(baseUrl, { redirect: 'manual' })
      if (response.ok) {
        return
      }
      lastFailure = `HTTP ${response.status}`
    } catch (error) {
      lastFailure = error instanceof Error ? error.message : String(error)
    }
    await delay(POLL_INTERVAL_MS)
  }
  throw new Error(
    `the editor server at ${baseUrl} did not become ready (${lastFailure}).\n${log.text()}`,
  )
}

/** End the process this helper started, using platform-appropriate semantics. */
function signalProcess(child: ChildProcess, force: boolean): void {
  const pid = child.pid
  if (pid === undefined) {
    return
  }
  if (process.platform === 'win32') {
    // Windows has no POSIX process groups. `taskkill` is the platform-native way
    // to end the process and anything it started, so no Unix-only negative-PID
    // assumption is copied into the Windows path.
    const args = ['/PID', String(pid), '/T', ...(force ? ['/F'] : [])]
    spawnSync('taskkill', args, { stdio: 'ignore' })
    return
  }
  try {
    // `detached: true` makes the child a process-group leader, so a negative pid
    // signals the whole `uv` -> python -> uvicorn tree and nothing else.
    process.kill(-pid, force ? 'SIGKILL' : 'SIGTERM')
  } catch {
    // The process group is already gone; there is nothing left to clean up.
  }
}

async function settlesWithin(work: Promise<unknown>, ms: number): Promise<boolean> {
  return Promise.race([work.then(() => true), delay(ms).then(() => false)])
}

async function stopProcessTree(child: ChildProcess, tracker: ExitTracker): Promise<void> {
  if (tracker.code !== null || tracker.signal !== null) {
    return
  }
  signalProcess(child, false)
  if (await settlesWithin(tracker.done, SHUTDOWN_GRACE_MS)) {
    return
  }
  signalProcess(child, true)
  await settlesWithin(tracker.done, FORCE_KILL_WAIT_MS)
}

/**
 * Start the real application under test: the packaged standalone Editor when
 * `DEEPLANT_EDITOR_EXECUTABLE` is set, otherwise `deepplant ui` over the
 * production build.
 *
 * Resolves once the application has announced its loopback URL and the server
 * answers. Rejects with the captured application log when startup fails for any
 * reason.
 */
export async function startEditorServer(options: EditorServerOptions = {}): Promise<EditorServer> {
  installSafetyNet()
  const spec = resolveLaunchSpec(options.symbolRoles ?? [])
  const child = spawn(spec.command, [...spec.args], {
    cwd: spec.cwd,
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  const log = createLogBuffer()
  child.stdout?.setEncoding('utf8')
  child.stderr?.setEncoding('utf8')
  child.stdout?.on('data', (chunk: string) => log.push(chunk))
  child.stderr?.on('data', (chunk: string) => log.push(chunk))

  const tracker = createExitTracker(child)
  const pid = child.pid
  if (pid !== undefined) {
    liveGroups.add(pid)
    void tracker.done.then(() => liveGroups.delete(pid))
  }

  try {
    const baseUrl = await waitForAnnouncedUrl(tracker, log, spec.label)
    await waitForServing(baseUrl, tracker, log, spec.label)
    return {
      baseUrl,
      stop: () => stopProcessTree(child, tracker),
      logs: () => log.text(),
    }
  } catch (error) {
    await stopProcessTree(child, tracker)
    throw error
  }
}
