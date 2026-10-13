# mapping.md — sphinx-doc__sphinx-7985

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f30284ef926ebaf04b176f21b421e2dffc679792`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled / deeply-modeled callee.

Repo file under change: `sphinx/builders/linkcheck.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `classifyLocalLink (uri : List Char) (fileExists : Bool) (anyIgnore : Bool)` | the non-network arm of `check()` inside `check_thread()` (`sphinx/builders/linkcheck.py:210-222`) — the `elif not uri.startswith(('http:', 'https:')):` block the patch rewrites | the modeled changed function |
| `isUnchecked (uri)` | the guard `len(uri) == 0 or uri.startswith(('#', 'mailto:'))` (`linkcheck.py:213` post-patch) | concrete transliteration of the skip-without-resolution test (identical op) |
| `isHttp (uri)` | the guard `uri.startswith(('http:', 'https:'))` (`linkcheck.py:215`) | concrete transliteration of the web-address test; used only as the method precondition that scopes the model to the non-network arm |
| `hasUriScheme (uri)` *(deep model — A-reference)* | `uri_re.match(uri)` where `uri_re = re.compile('[a-z]+://')` (`linkcheck.py:38` added, used at `linkcheck.py:216` post-patch) | deep model of the access-method detector; validated `hasUriScheme == bool(uri_re.match)` by axiom_check.py (G-AX) |
| `fileExists : Bool` | `path.exists(path.join(self.srcdir, uri))` (`linkcheck.py:219` post-patch) | the file-presence observation; UNCHANGED stdlib callee, observed only as a Bool input (no axiom — its result is a method input) |
| `anyIgnore : Bool` | `any(rex.match(uri) for rex in self.to_ignore)` — the `for rex in self.to_ignore: if rex.match(uri): return 'ignored'` loop (`linkcheck.py:221-223` post-patch) | the skip-pattern observation; UNCHANGED callee, observed only as a Bool input (no axiom — its result is a method input) |
| `classify (uri) (fileExists) (anyIgnore)` | the post-patch control flow of the non-network arm as a whole | pure spec: the verdict of the non-network arm |
| `Status.localLink` | the legacy blanket `return 'local', '', 0` (`linkcheck.py:217` pre-patch) | the verdict the change eliminates for resolvable local links (refinement-audit only; not produced by the post-patch spec) |

The Lean constructor for the unresolved-local-target outcome is named `Status.missing`
(it maps to the real status word `'broken'`, per §2): the constructor name is a
spec-view identifier, kept de-narrated, while the bijection records the true string.

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): the non-network arm returned a single blanket
`return 'local', '', 0` for every non-`http(s)` link without ever testing whether
the named file exists or whether a skip pattern matches; and the
skip-without-resolution guard additionally listed `'ftp:'`. Post-patch, `'ftp:'`
is removed from that guard and instead caught by the access-method detector
(`hasUriScheme`), and a genuine local target is resolved
(`working`/`ignored`/`broken`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `uri` (the link text, a `str`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `s.startswith(p)` ↔ `List.isPrefixOf p.toList l`; empty `str` ↔ `[]`. On the BMP each Python character `ch` ↔ `Char.ofNat (ord ch)`, total and exact |
| `path.exists(path.join(self.srcdir, uri))` result (`bool`) | `Bool` (`fileExists`) | `True ↔ true`, `False ↔ false` |
| `any(rex.match(uri) for rex in self.to_ignore)` result (`bool`) | `Bool` (`anyIgnore`) | `True ↔ true`, `False ↔ false` |
| the `(status, info, code)` 3-tuple `check()` returns | `Status` (the first element) | `'unchecked' ↔ .unchecked`, `'working' ↔ .working`, `'ignored' ↔ .ignored`, `'broken' ↔ .missing`, `'local' ↔ .localLink`. The modeled arm always returns `info = ''` and `code = 0`, so only the status word carries information; the model abstracts the tuple to its `Status` first element |

`info`/`code` are constant (`''`, `0`) on every branch the model covers, so they
carry no behaviour and are abstracted away; the F2P tests distinguish outcomes by
the status word and by whether the link is reported at all (a resolvable local
link's `broken`/`working` vs the legacy non-reporting `local`).

## 3. Modeled scope & callee provenance

### 3.1 `hasUriScheme` deep model ↔ `uri_re.match` (A-reference)
**Callee:** `uri_re.match(uri)` with `uri_re = re.compile('[a-z]+://')`. The patch
adds the module-level `uri_re` and uses it to recognise a link that carries an
explicit access-method marker (an unsupported scheme such as `ftp://…`). Its
behaviour is modeled **deeply** by `hasUriScheme`, so there is **no consumed
axiom** about it.

`re.match` anchors at position 0 and requires one-or-more ASCII lowercase letters
immediately followed by the literal `://`. Because the character after a maximal
lowercase run is non-lowercase and `://` begins with `:` (non-lowercase), the
`://` separator can only occur immediately after the **maximal** front run of
lowercase letters — no shorter prefix can be followed by `:`. Hence
`bool(uri_re.match(uri))` is exactly: "the front maximal lowercase run is
non-empty and is immediately followed by `://`", which is what `hasUriScheme`
encodes (`lowerRun uri ≥ 1` and `"://"` is a prefix of `uri.drop (lowerRun uri)`).

G-AX (`axiom_check.py`) runs the real `re.compile('[a-z]+://').match` over
boundary inputs and ≥20 000 fuzz strings and asserts the boolean agrees with
`hasUriScheme`.

### 3.2 Scope: which arm, and what is held opaque
The modeled `classify` covers the **non-network** arm of `check()`: the link is
not an `http:`/`https:` web address (the `require isHttp uri = false`
precondition; the web-address arm and the `self.good`/`self.broken`/
`self.redirected` caches and the network probe `check_uri()` are the *next* arm,
unchanged by this patch and outside the model). Within the non-network arm the
verdict is a total function of `(uri, fileExists, anyIgnore)`:

- `path.exists(path.join(self.srcdir, uri))` — the file-presence test — is an
  unchanged stdlib callee; its boolean result enters the model as `fileExists`
  (no axiom).
- `any(rex.match(uri) for rex in self.to_ignore)` — the skip-pattern test, the
  same `self.to_ignore` loop used elsewhere in `check()` — is unchanged; its
  boolean result enters the model as `anyIgnore` (no axiom).

Only `uri_re.match` (added by the patch) is modeled, as the A-reference §3.1.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7985`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the entire impl region (`isUnchecked`, `hasUriScheme`, the
nested-`if` control flow — all R/I-tagged ops) to Python and compares against
`patch.diff`'s behaviour, driving a faithful executable copy of the patched
non-network arm with the real `uri_re` and with `path.exists` / the
`self.to_ignore` loop replaced by the supplied `fileExists` / `anyIgnore`
booleans (the unchanged callees enter both sides identically as inputs).
