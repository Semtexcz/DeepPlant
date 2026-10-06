# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""The JavaScript probes the packaged desktop self-check runs (Issues #93, #97).

The automated packaged-desktop verification reads the *real rendered page* through
the webview's own JavaScript engine rather than a mock. These scripts and their
bounded settle timings live here, away from the window they are run against: the
window neither defines nor uses them, and ``deepplant.editor.desktop_qt.self_check``
owns running them. ``deepplant.editor.desktop`` (the Qt-free half of the host) owns
the fixture expectations the probes assert, so those values stay checkable in the
fast Python gate.
"""

from __future__ import annotations

from typing import Final

from deepplant.editor.desktop import (
    EMPTY_WORKSPACE_STATUS_TEXT,
    SMOKE_EXPECTED_STEPS,
    SMOKE_EXPECTED_STREAMS,
    SMOKE_PROBE_STEP_ID,
)

__all__ = [
    "CANVAS_PROBE_JS",
    "EMPTY_WORKSPACE_PROBE_JS",
    "EXPECTED_STEPS",
    "EXPECTED_STREAMS",
    "INSPECTOR_PROBE_JS",
    "POST_LOAD_SETTLE_MS",
    "POST_SELECTION_SETTLE_MS",
    "PROBE_STEP_ID",
    "SELF_CHECK_TIMEOUT_MS",
    "canvas_probe_js",
]

#: Give the SPA a moment to render the graph and the Inspector after load and
#: after a synthetic selection. Bounded and explicit; the probe then reads the
#: real DOM rather than guessing that the application is ready.
POST_LOAD_SETTLE_MS: Final[int] = 1500
POST_SELECTION_SETTLE_MS: Final[int] = 600

#: Hard bound on one self-check run. A GUI process must never be able to hang an
#: automated caller: if a stalled webview, a blocking platform dialog, or any
#: other condition prevents the probe from finishing, the application still
#: writes a report and still exits with a non-zero code.
SELF_CHECK_TIMEOUT_MS: Final[int] = 90_000

#: The packaged self-check expectations describe the canonical, self-contained
#: smoke fixture (Issue #98). They are authored once in the Qt-free host module
#: (:mod:`deepplant.editor.desktop`) so the fixture and these values can be checked
#: together in the fast Python gate; the probe step resolves to a symbol role
#: through the ordinary engineering ``function`` -> role policy, so no presentation
#: override is needed.
PROBE_STEP_ID: Final[str] = SMOKE_PROBE_STEP_ID

EXPECTED_STEPS: Final[int] = SMOKE_EXPECTED_STEPS
EXPECTED_STREAMS: Final[int] = SMOKE_EXPECTED_STREAMS

#: The empty-workspace probe (Issue #97). It proves the *shared Vue SPA* rendered
#: with no active document - not a native start page: the ordinary application
#: shell is present, no engineering model was fabricated (zero projected steps),
#: the status is the neutral "no project open" state (never "Invalid"), the empty
#: canvas message is shown, and no projection failure notice appears.
EMPTY_WORKSPACE_PROBE_JS: Final[str] = f"""
(() => {{
  const text = (el) => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null);
  const status = document.querySelector('[role="status"]');
  const steps = document.querySelectorAll('[role="group"][aria-label^="Process step "]');
  const noticePrefix = '[role="note"][aria-label="';
  const notice = document.querySelector(noticePrefix + '{EMPTY_WORKSPACE_STATUS_TEXT}' + '"]');
  const alert = document.querySelector('[role="alert"]');
  return JSON.stringify({{
    statusText: text(status),
    processSteps: steps.length,
    emptyWorkspaceNotice: notice !== null,
    projectionError: text(alert),
    devEntryPoint: document.documentElement.outerHTML.includes('/src/main.ts'),
  }});
}})()
"""


def canvas_probe_js(step_id: str) -> str:
    """Return the canvas probe script that activates one process step by id.

    The probe reads the *rendered* page - the status strip, the projected
    process-step and process-stream counts, and whether the named step node is
    present - then dispatches a synthetic activation on that node so the
    follow-up Inspector probe reads a real selection. The step id is a parameter
    because the packaged project-replacement scenario selects a different step in
    each project.
    """
    return f"""
(() => {{
  const text = (el) => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null);
  const status = document.querySelector('[role="status"]');
  const steps = document.querySelectorAll('[role="group"][aria-label^="Process step "]');
  const streams = document.querySelectorAll('[role="group"][aria-label^="Process stream "]');
  const node = document.querySelector('[role="group"][aria-label="Process step {step_id}"]');
  if (node) {{
    const box = node.getBoundingClientRect();
    const init = {{
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: box.left + box.width / 2,
      clientY: box.top + box.height / 2,
    }};
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
      node.dispatchEvent(new MouseEvent(type, init));
    }}
  }}
  return JSON.stringify({{
    statusText: text(status),
    processSteps: steps.length,
    processStreams: streams.length,
    probeNodeFound: node !== null,
    devEntryPoint: document.documentElement.outerHTML.includes('/src/main.ts'),
  }});
}})()
"""


CANVAS_PROBE_JS: Final[str] = canvas_probe_js(PROBE_STEP_ID)

INSPECTOR_PROBE_JS: Final[str] = """
(() => {
  const text = (el) => (el ? el.textContent.replace(/\\s+/g, ' ').trim() : null);
  const inspector = document.querySelector('aside[aria-label="Inspector"]');
  const fields = {};
  if (inspector) {
    const terms = [...inspector.querySelectorAll('dt')];
    const definitions = [...inspector.querySelectorAll('dd')];
    terms.forEach((term, index) => {
      fields[text(term)] = definitions[index] ? text(definitions[index]) : null;
    });
  }
  return JSON.stringify({
    heading: inspector ? text(inspector.querySelector('h2')) : null,
    fields,
  });
})()
"""
