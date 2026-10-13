# mapping.md — astropy__astropy-13033

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 298ccb478e6bf092953bca67a3d29dc6c35f6752`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance.

Repo file under change: `astropy/timeseries/core.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `requiredColumnsError (className required present)` | the `raise ValueError(...)` message built in the mismatch branch of `BaseTimeSeries._check_required_columns` — `astropy/timeseries/core.py:55` (method), message at body lines 78–82 (the `elif self.colnames[:len(required_columns)] != required_columns:` arm) | the modeled changed behaviour: the invalidity message |
| `renderColumnList (xs : List (List Char))` | the post-patch local that renders a name collection for display (single → quoted scalar, otherwise → the list's `str(...)`), `core.py` post-patch lines 58–64 | pure spec: display rendering of a name collection |
| `quoted (s : List Char)` | the `f"'{x}'"` single-quoting used for a scalar name (plain interpolation, NO escaping) | pure spec: one name wrapped verbatim in apostrophes |
| `renderedName` (**opaque**, axioms region) | Python `repr` of one `str` — the per-element rendering `str(list_of_str)` applies to each element (quote-delimited, with CPython's escaping rules: delimiter switches to double quotes when the value embeds a single quote and no double quote; backslash/control/non-printable escapes per the Unicode tables) | A-reference: the platform's canonical per-element rendering, an UNCHANGED builtin; binding validated executably by G-AX (`axiom_check.py`) |
| `joinRendered` / `bracketList` | Python `str(list_of_str)` — `repr` of a `list[str]`: `[` + `, `-joined per-element `repr` + `]` | pure spec: the `[...]` rendering of a name collection, per-element via `renderedName` |
| `errorMessage (className required present)` | the full `"{} object is invalid - expected {} as the first column{} but found {}".format(...)` string of the post-patch mismatch arm | pure spec: the whole message |

The pre-patch repo construct the change supersedes (refinement audit only, not in
the consumer spec view): the old mismatch-arm message
`"{} object is invalid - expected '{}' as the first column{} but found '{}'"`
`.format(self.__class__.__name__, required_columns[0], plural, self.colnames[0])`
— which names only `required_columns[0]` and `self.colnames[0]`, each as a quoted
scalar. The post-patch local helper that does the rendering is `core.py` lines
58–64 (a nested `def`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a column name `str` (an element of `required_columns` / `self.colnames`, and `self.__class__.__name__`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`; on the BMP `Char.ofNat (ord ch)` ↔ `ch` is total and exact |
| a sequence of column names `list[str]` (`required_columns`, `self.colnames`) | `List (List Char)` | element-wise the name bijection above; `len(xs)` ↔ `xs.length`; `xs[:k]` ↔ `xs.take k`; `xs[0]` ↔ `xs.head?.getD []`; the empty list ↔ `[]` |
| the built `str` message (`ValueError`'s first arg) | `List Char` | char-sequence identity; the F2P test compares `exc.value.args[0]` to a literal `str`, i.e. its character content |
| `repr` of one `str` (the per-element rendering `str(list)` applies) | `renderedName` (**opaque**) | left ABSTRACT in the model: committing to a concrete Lean approximation of the platform's per-character escaping rules would diverge from the real behaviour on names embedding quote/backslash/control characters. G-AX (`axiom_check.py`) validates the binding executably against the real builtin over adversarial names (embedded single/double quotes, backslashes, control chars, non-ASCII, empty), byte-for-byte through the `str(list)` composition — so the bijection is exact for EVERY name, not only simple identifiers. |
| `str(list_of_str)` (`repr` of a `list[str]`) | `bracketList` | `[` + (`, `-joined `renderedName` tokens) + `]`, exactly CPython's `list.__str__` composition; per-element fidelity delegated to the `renderedName` binding above (exact for all names) |
| `f"'{x}'"` single-quoting of one name | `quoted x` | `'` ++ x ++ `'`, VERBATIM plain interpolation with no escaping — this is precisely what the real single-name arm does (an f-string, not `repr`), for pathological names too. For a 1-element collection Python returns `f"'{obj[0]}'"`, modeled by `renderColumnList [x] = quoted x`. |

`required_columns` in the mismatch arm is `self._required_columns` (when not
relaxed) — a Python `list[str]`; `self.colnames[:len(required_columns)]` is the
present-names prefix. The model carries both as `List (List Char)` and slices the
present names with `present.take required.length` exactly as the patch slices
`self.colnames[:len(required_columns)]`.

## 3. Callee provenance (kind-A)

**One A-reference; no consumed `axiom`.** The message construction is built
from concrete string operations (`quoted`, `joinRendered`/`bracketList`, `++`,
`take`, `length`, the plural `if`) over the three inputs, modeled DEEPLY in
`Solution.lean`'s `pure` region — EXCEPT the per-element rendering used inside
a rendered sequence, which is the platform's unchanged builtin (`repr` of a
`str`, as applied by `str(list)`) and is left `opaque` (`renderedName`,
axioms region). The patch's changed operation — WHICH collections are
rendered, and WHEN the single-name vs whole-sequence form is used — is fully
under the spec (directive 7: never axiomatize the operation the patch
changes); only the pre-existing per-character escaping rules of the platform
are abstracted. No `axiom` about `renderedName` is consumed: the proof never
inspects its behaviour.

G-AX (`axiom_check.py`) validates the `renderedName ↔ repr` binding
executably in-container: the `bracketList` composition against the real
`str(list)` byte-for-byte, plus a round-trip sanity leg, over adversarial and
fuzzed names (pinned seed 13033, 50k+ cases).

The surrounding control flow that decides WHICH branch raises (the
`_required_columns_enabled` early return, the `_required_columns is not None`
guard, the relax handling, the empty-`colnames` branch, the prefix-mismatch
comparison) is **unchanged** by the patch and is not modeled: the patch touches
only the message string of the already-selected mismatch arm. See refinement.md
§C.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13033`** so the
consumer-side verdict is reproducible. The fuzz alphabet for column names mixes
the simple-name alphabet (ASCII letters, digits, underscore; length ≥ 1) with
ADVERSARIAL names (embedded single/double quotes, backslashes, control
characters, non-ASCII) — the `renderedName := repr` binding makes the
`str([...])`/`f"'{x}'"` ↔ `bracketList`/`quoted` bijection (§2) exact on every
input, pathological names included. The shadow transliterates
`errorMessage`/`renderColumnList` (R/I ops plus the A-reference leaf bound to
`repr`) to Python; the oracle drives the **real patched**
`BaseTimeSeries._check_required_columns` in-container via a minimal stand-in
object (only the attributes the method reads: `_required_columns_enabled`,
`_required_columns`, `_required_columns_relax`, `colnames`, `__class__.__name__`),
catching the `ValueError` and comparing `args[0]`.
