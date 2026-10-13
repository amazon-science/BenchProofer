# refinement.md — sphinx-doc__sphinx-7985

Maps every op in `implementation_checkLink` (Solution.lean) to its `patch.diff`
counterpart. Tags: **R** type-refinement, **A-consumed** axiom used by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical
concrete op.

Modeled function: the network-free classification prefix of the nested `check()`
closure in `CheckExternalLinksBuilder.check_thread`
(`sphinx/builders/linkcheck.py:211-216 @ base_commit`, patched lines). The
unchanged downstream `http:`/`https:` subtree (cache lookups + `check_uri()`) is
abstracted to its observed status `httpResult` and frame-pinned.

| # | Lean impl op | patch.diff / repo counterpart | tag | note |
|---|---|---|---|---|
| 1 | `if uri.isEmpty \|\| startsWithHashMailto uri then return .unchecked` | `if len(uri) == 0 or uri.startswith(('#', 'mailto:')): return 'unchecked', '', 0` | R | `uri : List Char` ↔ `str`; `startsWithHashMailto` deeply models the per-char prefix test. The patch DROPS `'ftp:'` from this tuple — the Lean op omits it (modeled by omission); the dropped `ftp:` case is now handled by op 3. |
| 2 | `if !startsWithHttp uri then …` | `elif not uri.startswith(('http:', 'https:')): …` | R | `startsWithHttp` deeply models the prefix test. Guards the rewritten local-classification block. |
| 3 | `if hasUriScheme uri then return .unchecked` | `if uri_re.match(uri): return 'unchecked', '', 0` (`uri_re = re.compile('[a-z]+://')`) | A-reference | `hasUriScheme` deeply models the anchored regex `[a-z]+://`; validated == real regex by G-AX over fuzzed URIs. This is the NEW branch (a transfer scheme other than web → unchecked). |
| 4 | `else if localFileExists then return .working` | `else: if path.exists(path.join(self.srcdir, uri)): return 'working', '', 0` | R | `path.exists(path.join(srcdir, uri))` is the unchanged stdlib observation, abstracted to the input bit `localFileExists` (bridged by G-CONF). NEW branch: a present source-relative path → working. |
| 5 | `else if ignoreMatch then return .ignored` | `else: for rex in self.to_ignore: if rex.match(uri): return 'ignored', '', 0` | R | the regex-set membership over the (unchanged) `self.to_ignore` list abstracted to the input bit `ignoreMatch`. NEW branch. |
| 6 | `else return .broken` | `else: return 'broken', '', 0` (the `for…else` clause) | I | NEW branch: an absent, non-ignored local path → broken. This is the central behavior the issue + F2P (`path/to/notfound`) demand. |
| 7 | `return httpResult` (web branch) | the unchanged `elif uri in self.good … elif … check_uri()` subtree | R | the entire UNCHANGED web-resolution subtree abstracted to its observed status `httpResult`; frame-pinned in the spec (`result = httpResult`). |

Result projection: Python `check()` returns `(status, message, code)`. Every
changed return in the modeled prefix is `(status, '', 0)` — the message and code
are uniform (`''`, `0`) across all of branches #1, #3-#6, so they carry no
discriminating information for this change and are projected away; the entire
behavioral change is in the status component, modeled as `LinkStatus`. (The web
branch's message/code live in the unchanged subtree abstracted by `httpResult`.)

No changed op is inexpressible. The only A-tagged row is #3 (A-reference,
G-AX-checked); there is no consumed `_prop` axiom, so the impl region is NOT
all-A-tagged ⇒ `conf_skip = false` and G-CONF runs the R/I differential.

## Prepatch correspondence (G-DIFF)

`Solution_prepatch.lean` carries the real pre-patch `check()`: `'ftp:'` is folded
back into the skip-prefix set (→ `.unchecked`), and the ENTIRE non-web branch
returns a single catch-all outcome (`.localLink`) — exactly
`return 'local', '', 0`. This contradicts the frozen spec on every discriminating
input, e.g. `uri="conf.py", localFileExists=true` (spec demands `.working`,
prepatch yields `.localLink`) and `uri="path/to/notfound", localFileExists=false,
ignoreMatch=false` (spec demands `.broken`, prepatch yields `.localLink`). The
carried gold proof body therefore fails to typecheck ⇒ fails G-VERIFY. This is
the bug the F2P tests `test_defaults` / `test_anchors_ignored` exercise.
