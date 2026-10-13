# mapping.md — sphinx-doc__sphinx-7985

## Symbol binding (file:line @ base_commit f30284ef)

- Modeled function: the nested `check()` closure inside
  `CheckExternalLinksBuilder.check_thread` —
  `sphinx/builders/linkcheck.py:211-240 @ base_commit`.
  The patch rewrites its network-free classification prefix
  (`linkcheck.py:213-216` pre-patch) and adds the module-level
  `uri_re = re.compile('[a-z]+://')` (`linkcheck.py:37`).
- Lean triple: `checkLink` —
  `problem_spec_checkLink` / `implementation_checkLink` / `correct_checkLink`
  in `Solution.lean`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | note |
|---|---|---|
| `uri : str` (per-code-point prefix tests) | `uri : List Char` | total/sound indexing; prefix tests are per-char |
| return status `str` ∈ {unchecked, working, broken, ignored, local, redirected} | `LinkStatus` inductive | `'local'` ↔ `.localLink` (Lean keyword-free); 1-1 on the closed status set |
| `path.exists(path.join(self.srcdir, uri))` | `localFileExists : Bool` | filesystem oracle abstracted to its boolean observation (input). Bridged by G-CONF as a provided bit. |
| `any(rex.match(uri) for rex in self.to_ignore)` | `ignoreMatch : Bool` | regex-set membership abstracted to its boolean observation (input) |
| outcome of the `http:`/`https:` branch (caches `self.good`/`self.broken`/`self.redirected` + `check_uri()` network call) | `httpResult : LinkStatus` | UNCHANGED downstream subtree abstracted to its observed status (input); frame-pinned on that branch |
| `uri_re.match(uri)` where `uri_re = re.compile('[a-z]+://')` | `hasUriScheme uri : Bool` (deep model) | `re.match` is anchored at start: one-or-more `[a-z]` then literal `://` |
| `uri.startswith(('#','mailto:'))` | `startsWithHashMailto uri : Bool` (deep model) | prefix test per-char |
| `uri.startswith(('http:','https:'))` | `startsWithHttp uri : Bool` (deep model) | prefix test per-char |

## Callee provenance + flag deps

- `path.exists` / `os.path.join` — stdlib, UNCHANGED by the patch; their composite
  observation is abstracted as the input bit `localFileExists`. Not a consumed
  axiom (no `_prop` needed): the impl branches on the input directly.
- `re.Pattern.match` over `self.to_ignore` — UNCHANGED; abstracted as `ignoreMatch`.
- `re.Pattern.match` over `uri_re` (`[a-z]+://`) — modeled DEEPLY as `hasUriScheme`
  (A-reference; checked equal to the real regex by G-AX over fuzzed URIs).
- The `http:`/`https:` branch (`self.good`/`self.broken`/`self.redirected`
  caches and `check_uri()`) is UNCHANGED; its observed status is the input
  `httpResult`. No flag dependency in the modeled prefix.

## G-CONF fuzz seed

`conf_seed = 20240630` (pinned; see meta.json verifier_pins).
