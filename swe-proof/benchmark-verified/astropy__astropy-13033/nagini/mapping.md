# mapping.md — astropy__astropy-13033

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 298ccb478e6bf092953bca67a3d29dc6c35f6752`, states the type
abstraction, and gives the provenance of the deep-model references (there are
NO consumed axioms).

Repo file under change: `astropy/timeseries/core.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_name_run(run)` | the nested helper `as_scalar_or_list_str(obj)` added inside `BaseTimeSeries._check_required_columns` — `astropy/timeseries/core.py:57` (helper body added at the top of the method by the patch) | modeled changed function: render one run of column names for the message |
| `compose_leading_run_report(cls_name, demanded, found)` | the `raise ValueError(...)` message-assembly in the leading-run-disagreement branch of `_check_required_columns` — `astropy/timeseries/core.py:77-81` (the `elif self.colnames[:len(required_columns)] != required_columns:` branch) | modeled changed function: assemble the full disagreement report |
| `render_run(run)` *(deep model — A-reference)* | the body of the helper `as_scalar_or_list_str` (`core.py:57` post-patch) | pure spec: the rendering of a run (lone name → `'name'`; other length → `str(run)`) |
| `joined(run)` *(deep model — A-reference)* | the comma-space-separated, apostrophe-wrapped element sequence inside Python's `str(list_of_str)` | pure spec: the inner of the textual list form |
| `quoted(t)` | one element's repr inside the textual list form / the `f"'{...}'"` single-name form | pure spec: one name wrapped in apostrophes |
| `report_seq(cls_name, demanded, found)` *(deep model — A-reference)* | the whole `"{} object is invalid - expected {} as the first column{} but found {}".format(...)` message — `core.py:79-81` post-patch | pure spec: the full report string |
| `Requires(MustTerminate(len(run) + 2))` on `render_name_run`; `Invariant(MustTerminate(i + 1))` on its construction loop | the totality of `as_scalar_or_list_str` (`core.py:57` post-patch) | completion obligation (spec clause (3)): rendering a run ends in finitely many steps (that it ends by handing the rendering back is clause (5), below) |
| `Requires(MustTerminate(len(demanded) + len(found) + 6))` on `compose_leading_run_report` | the totality of the `raise ValueError(...)` message assembly (`core.py:77-81` post-patch) | completion obligation (spec clause (3)): assembling the report ends in finitely many steps (that it ends by handing the report back is clause (5), below) |
| `Exsures(Exception, False)` on `render_name_run` | the return-only exit of `as_scalar_or_list_str`: three `return`s of one total expression each and no `raise` anywhere in the body (`core.py:58-64` post-patch) | delivery obligation (spec clause (5)): rendering a run ends by handing the rendering back, never by signalling instead |
| `Exsures(Exception, False)` on `compose_leading_run_report` | the total `.format(...)` message assembly (`core.py:86-89` post-patch), whose VALUE is the report; the enclosing `raise ValueError(...)` at `core.py:86` is how the real code delivers that finished report and is not a way of ending without one | delivery obligation (spec clause (5)): the report is assembled and handed back, never abandoned partway |
| `Ensures(ToSeq(run) == Old(ToSeq(run)))` on `render_name_run` | the read-only use of `obj` by `as_scalar_or_list_str` (`core.py:58-64` post-patch) | preservation obligation (spec clause (4)): the run handed in comes back with the same names in the same order |
| `Ensures(ToSeq(cls_name) == Old(ToSeq(cls_name)))`, and the same for `demanded` and `found`, on `compose_leading_run_report` | the read-only use of the class name, `required_columns` and `self.colnames[:len(required_columns)]` by the `.format(...)` assembly (`core.py:86-89` post-patch) | preservation obligation (spec clause (4)): the report describes the runs AS GIVEN |

The pre-patch repo expressions the change removes (for the refinement audit,
not referenced from the consumer spec view): the message used
`required_columns[0]` and `self.colnames[0]` — only the FIRST name of each run —
inside the template `expected '{}' ... but found '{}'` with literal apostrophes
(`core.py:79-81` pre-patch). The patch routes both runs through the new
`as_scalar_or_list_str` helper and drops the literal apostrophes from the
template (the helper supplies them).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a column name (`str`, e.g. `'time'`) | one distinct token `int >= 0`; in the rendering it is emitted as `encode_name(t) = t + 256` (kept disjoint from the punctuation code points 32/39/44/91/93) | token `t` ↔ the real name string `names[t]`. The rendering of `t` is `[39, encode_name(t), 39]` ↔ the real `'name'`. axiom_check.py expands tokens back to strings and confirms equality to the real output. |
| a run of column names (`list[str]`, e.g. `required_columns`, `self.colnames[:len(required_columns)]`) | `List[int]` (carrier) / `PSeq[int]` (specification) of name tokens | `run[k]` ↔ the k-th name's token; `len(run)` ↔ the run length; list `+` ↔ token-sequence `+`. |
| the rendered message field / full message (`str`) | `List[int]` (carrier) / `PSeq[int]` (specification) over a token-and-punctuation alphabet | punctuation/literal code points are real Unicode code points (apostrophe 39, comma 44, space 32, `[` 91, `]` 93, and the fixed connective text); each name occupies one token position. `expand` (axiom_check.py) substitutes real name strings for tokens to recover the real `str`. |

**Why a name is one token, not its code points.** The behaviour that *changes*
is structural — which names appear in the rendering, in what order, with which
brackets / apostrophes / separators / plural marker. The inner spelling of each
individual name is copied through verbatim by BOTH the pre- and post-patch code
(`required_columns[0]` and the f-string both emit the name as-is), so it is not
where the fix lives. Modelling each name as one token captures the changed
structure exactly while keeping the sequence folds tractable; the
character-level correspondence (token ↔ real string) is declared here and
checked by G-AX.

**Domain note (token bijection).** The bijection token→`'name'` is exact when
the name's `repr` is `'` + the name + `'` — i.e. the name contains no
apostrophe or backslash that Python's `repr`/`str(list)` would escape. Astropy
column names are ordinary identifiers (`'time'`, `'flux'`, `'a'`), so every
tested run is inside this domain; axiom_check.py fuzzes only such identifier
names. A name containing a quote/backslash is outside the token model's clean
domain (and is not exercised by the F2P/P2P tests).

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed axioms**: the proof of `render_name_run` and
`compose_leading_run_report` depends only on the spelled-out pure folds
(`quoted`, `joined`, `render_run`, `report_seq`) and ordinary sequence
concatenation — never on a `@ContractOnly` callee's `Ensures`.

The changed behaviour is modelled DEEPLY; the deep models are validated equal
to the real callees out-of-band:

### 3.1 `render_run` ↔ the helper `as_scalar_or_list_str` (A-reference)
**Real callee (the exact code the fix ships, `core.py:57`):**
```python
def as_scalar_or_list_str(obj):
    if not hasattr(obj, "__len__"):
        return f"'{obj}'"
    elif len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)
```
For a list (`required_columns`, `self.colnames[:len(required_columns)]` are
always lists — both have `__len__`), the scalar branch is never taken; the
relevant behaviour is: length 1 → `f"'{obj[0]}'"` = `'name'`; any other length
→ `str(obj)` = the bracketed, apostrophe-wrapped, comma-space-separated textual
list form. `render_run` (with `joined`/`quoted`) encodes exactly this. G-AX
expands each name token to its real string and asserts the model equals the
real helper output.

### 3.2 `report_seq` ↔ the `ValueError` message format (A-reference)
**Real callee (`core.py:79-81` post-patch):**
```python
"{} object is invalid - expected {} as the first column{} but found {}".format(
    self.__class__.__name__,
    as_scalar_or_list_str(required_columns),
    plural,
    as_scalar_or_list_str(self.colnames[:len(required_columns)]))
```
with `plural = 's' if len(required_columns) > 1 else ''`. `report_seq` encodes
the fixed connective text as literal code points, the plural marker by the same
length test, and the two rendered fields via `render_run`. G-AX asserts the
expanded model equals the real `.format(...)` output, including the exact F2P
scenario (issue #13009: demanded `['time','a']`, found `['time','b']` →
`"... expected ['time', 'a'] as the first columns but found ['time', 'b']"`).

**Soundness check (G-AX).** `axiom_check.py` reproduces the real helper and the
real format string verbatim, runs them on boundary runs (lengths 0/1/2/3, the
F2P scenario, the legacy single-column scenarios) plus 20 000 randomized fuzz
reports over an identifier-name alphabet, and asserts the expanded deep model
equals the real output every time. It imports only the standard library; exit 0
iff sound.

## 4. Completion obligations ↔ the real callees' totality

("Delivering a value" is split across §4 and §4b. Clause (3) here rules out an
execution that never ends; clause (5) in §4b rules out one that ends without an
answer. Read §4's claims as bounded by that split — neither clause alone gets to
"the caller receives a report".)

Spec clause (3) is carried by `Requires(MustTerminate(len(run) + 2))` on
`render_name_run`, `Invariant(MustTerminate(i + 1))` on its construction loop, and
`Requires(MustTerminate(len(demanded) + len(found) + 6))` on
`compose_leading_run_report`. These are
**obligations on the implementation**, not restrictions on the inputs: they are
demanded for every input the other preconditions admit, so the modeled domain is
unchanged (every run length, including 0, 1 and the multi-name runs).

**They are TRUE of the real callees on that whole domain.** The real helper is

```python
def as_scalar_or_list_str(obj):
    if not hasattr(obj, "__len__"):
        return f"'{obj}'"
    elif len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)
```

Every branch is a single expression that returns; the helper contains no loop and
never re-enters itself, so it terminates on every input — in particular on both
call sites' lists (`required_columns` and the `self.colnames[:len(...)]` slice) of
any length. The real assembly is one
`"...".format(self.__class__.__name__, as_scalar_or_list_str(...), plural, as_scalar_or_list_str(...))`
over two such calls plus the constant `plural` test; it likewise contains no loop
and does not re-enter `_check_required_columns`. So demanding completion excludes
no faithful implementation. The budgets are ORDERED (the assembly's exceeds the
renderer's on the same runs) precisely because the real assembly calls the real
renderer twice: a caller with the larger budget may invoke the smaller-budget
callee and is still obliged to finish. The budgets are LENGTH-SCALED (`len(run) + 2`; `len(demanded) + len(found) + 6`) rather than constant, so an implementation that works its run down to a strictly shorter one and re-enters itself -- a structurally recursive rendering -- still discharges the obligation; what is excluded is only coming back round on a run no shorter than the current one, i.e. never getting closer to delivering. A constant budget would have banned recursive descent outright and so over-fitted the reference construction's iterative loop; properties.py case `recursive-descent-admitted` pins that a descending implementation must VERIFY.

**Why the obligations are load-bearing rather than decorative.** Nagini proves
PARTIAL correctness: an `Ensures` constrains only executions that reach a return,
and at a call site the callee's contract is ASSUMED rather than re-established.
Without clause (3), then, the value clauses of §3.1/§3.2 are satisfied vacuously
by any implementation that never reaches a return — including one that keeps the
length-1 branch exactly right (so every legacy single-required-column scenario
renders correctly) and never finishes on the multi-name run, which is exactly the
run the disagreement report exists to describe. Refined faithfully, such an
implementation raises `RecursionError` (or hangs) where the tests expect the
`ValueError` message, so it does not resolve. Clause (3) is one of the two things
that make §3.1/§3.2 statements about output the caller ACTUALLY RECEIVES; §4b is
the other, and clause (3) does not subsume it — `MustTerminate` is discharged by
an execution that stops at once by signalling, which reaches no return and so
satisfies every `Ensures` vacuously.

**Scope note.** Completion is about ending, not about how fast: no
step count, iteration order, or measure value is claimed to match the real code.
The measures are internal proof budgets, and any faithful implementation that
finishes can be given a measure satisfying them (the positive control in
properties.py re-derives the report with the site-B locals reordered and the two
renders swapped, and verifies).

## 4b. Delivery obligations ↔ the real callees' return-only exit

Spec clause (5) is carried by `Exsures(Exception, False)` on **both** modeled
functions. Like the completion obligations these are **obligations on the
implementation**, not restrictions on the inputs: they are demanded for every input
the other preconditions admit, so the modeled domain is unchanged (every run
length, including 0, 1, the multi-name runs, and the aliased triple).

**They are TRUE of the real callees on that whole domain.** The helper
(`core.py:58-64` post-patch) has exactly three exits, each a `return` of one
expression — `f"'{obj}'"` (`core.py:60`), `f"'{obj[0]}'"` (`core.py:62`),
`str(obj)` (`core.py:64`) — with no `raise` anywhere in its body, and none of those
expressions can signal on the modeled domain: `hasattr(obj, "__len__")` yields a
bool, `len` of a list an int, the `obj[0]` at `core.py:62` sits under the
`len(obj) == 1` guard at `core.py:61` so the index is in range, and `str` of a list
of names is total. The modeled assembly is the `.format(...)` expression at
`core.py:86-89`: a template with four positional `{}` fields and no conversion
specifiers, given exactly four arguments — an attribute read, the `plural` local
already computed at `core.py:76`, and two calls that exit only by returning — so it
too cannot fail. So demanding delivery excludes no faithful implementation.

**Read the assembly row correctly.** The real branch DOES raise, at `core.py:86`.
What is modeled at site B is the assembly of the report, i.e. the `.format(...)`
subexpression whose value is the message (§1, §3.2); the `raise ValueError(...)`
wrapped round it is how the real code hands the finished report to the user, and it
presupposes that the report was built. Clause (5) denies the assembly the option of
ending WITHOUT a report, which is a different thing from denying the surrounding
method its delivery mechanism.

**Why the obligations are load-bearing rather than decorative.** Nagini's default
"this method raises no exceptions" check is DROPPED as soon as any `Exsures` is
declared, and such a declaration can be made inside the `impl` region, which the
frozen-spec comparison elides and therefore cannot see. So an implementation was
free to declare its way out of the exceptional exit and then take it: it ends
promptly (clause (3) satisfied), rewrites nothing (clause (4) satisfied — it does
nothing), and reaches no return, so every value clause of §3.1/§3.2 and every
`Old(...)` clause of §5 is vacuous, while the reader is told nothing about which
names were demanded or which were found. Refined faithfully that is the change on
which the disagreement branch never produces its message: F2P
`test_required_columns` and P2P `test_empty_initialization_invalid` both assert
against that message and both fail. Freezing the clause in the spec view closes it,
and it cannot be relaxed from the impl region: Nagini CONJOINS the exceptional posts
declared for the same exception type, so a smuggled `Exsures(Exception, True)` adds
an obligation beside this one instead of replacing it, and the accompanying
`error ==> OR(declared types)` post blocks leaving by any other type.
properties.py cases `nondelivery-signalled-away-report`,
`nondelivery-signalled-away-render`, `nondelivery-true-contract-override`,
`nondelivery-reraise-from-handler`, `nondelivery-partial-multiname` and
`nondelivery-late-after-build` are those rivals, and the first VERIFIED before
clause (5) existed.

**Why BOTH sites and not just the assembly.** Before clause (5), a renderer that
signalled away was rejected only because `compose_leading_run_report`'s own
contract required its call to return — an incidental protection from the in-module
caller, leaving `render_name_run`'s contract silent about delivery to any other
caller. The real helper's callers are the two `.format` arguments at
`core.py:88-89`, which consume its value, so the renderer owes delivery in its own
right.

**Scope note.** Clause (5) constrains only how the modeled functions END. It says
nothing about their internals: an implementation may raise and handle a signal
itself, provided it goes on to return the right rendering / report. properties.py
case `internal-signal-caught-admitted` pins that such an implementation must
VERIFY, so the clause is not a ban on exception machinery.

## 5. Preservation obligations ↔ the real callees' read-only use of their inputs

Spec clause (4) is carried by `Ensures(ToSeq(run) == Old(ToSeq(run)))` on
`render_name_run` and by the three `Ensures(ToSeq(x) == Old(ToSeq(x)))` on
`compose_leading_run_report`. Like the completion obligations these are
**obligations on the implementation**, demanded for every input the other
preconditions admit, so the modeled domain is unchanged.

**They are TRUE of the real callees.** Every branch of the real helper
(`core.py:58-64` post-patch) only reads its argument —
`hasattr(obj, "__len__")`, `len(obj)`, `obj[0]`, `str(obj)` — and contains no
assignment to `obj` or to an element of it. The real assembly
(`core.py:86-89` post-patch) is a single
`"...".format(self.__class__.__name__, as_scalar_or_list_str(required_columns), plural, as_scalar_or_list_str(self.colnames[:len(required_columns)]))`;
`str.format` reads its arguments, and both helper calls only read, so neither the
class name, nor `required_columns`, nor the found slice is mutated. So demanding
preservation excludes no faithful implementation.

**Why they are load-bearing rather than implied by the half-permissions.** An
`Acc(list_pred(x), 1 / 2)` forbids a write to `x` only while it is the whole share
held on that object. At the report-assembly site the three half-permissions may be
held on the SAME object: hand the demanded run and the found run over as one
collection and the two halves sum to FULL permission. The value clauses are read
in the POST-state, so an implementation may then rewrite that collection and
report the rewritten names — the report equals `report_seq` of what the runs say
at return, every other clause holds, and the caller's own declared list of names
has been changed underneath it. Refined faithfully that is a helper that
normalises the names in place, and because the demanded run passed at
`core.py:88` is `required_columns` — i.e. `self._required_columns` itself
(`core.py:74`), the class-level list declared at `sampled.py:59`, not a copy — the
rewrite outlives the message and corrupts the successive assertions
`test_required_columns` makes against that same list. Clause (4) composed with the
value clauses pins the report to the runs AS GIVEN; properties.py case
`aliased-input-rewritten` is that rival, and it VERIFIED before clause (4)
existed.

**Scope note.** Preservation is about the names and their order, which is all the
model carries. Nothing is claimed about identity, capacity, or any other
representation detail of the collections, and nothing forbids an implementation
from building whatever fresh lists it likes.
