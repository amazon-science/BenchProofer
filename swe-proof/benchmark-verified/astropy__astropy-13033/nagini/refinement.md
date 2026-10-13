# refinement.md — astropy__astropy-13033

The operation-by-operation correspondence between `model.py`'s implementation
(the two modeled functions `render_name_run` and
`compose_leading_run_report`, and the deep folds `quoted`/`joined`/
`render_run`/`report_seq`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-reference** (a deep model validated == the
real callee by axiom_check.py / G-AX — NOT a consumed axiom), **I**
(identical concrete operation), or **T** (a totality/completion obligation).
There are **no A-consumed** rows: the proof consumes no `@ContractOnly` axiom.
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs **and actually produces that behaviour on every admissible input**, so
it resolves.*

**Totality is part of the claim, not an aside.** Nagini's `Ensures` alone gives
PARTIAL correctness: it constrains only executions that REACH a return, and at a
call the callee's contract is ASSUMED. A value correspondence therefore cannot,
by itself, bridge verify ⇒ resolve — an implementation that never reaches a
return discharges every value clause vacuously while producing no message at
all. Totality here needs **two** obligations, because "does not reach a return"
has two shapes and each spec clause reaches only one of them.

*Completion (clause (3), rows A4/B7).* Both modeled functions carry
`Requires(MustTerminate(...))` and the construction loop carries
`Invariant(MustTerminate(i + 1))`. What that establishes, exactly, is that the
computation cannot run forever: every admissible run ends in finitely many steps.
It does **not** establish that it ends by RETURNING. `MustTerminate` is
discharged just as well by an execution that stops promptly and leaves by the
exceptional exit, and every `Ensures` — the value clauses A2/A3/B6 and the
`Old(...)` preservation clauses A5/B8 alike — is silent on such an execution.
So clause (3) alone buys "reaches a return **or** raises".

*Delivery (clause (5), rows A6/B9).* Both modeled functions carry
`Exsures(Exception, False)`, which says the exceptional exit is unreachable: no
admissible input may be answered with a signal instead of a value. That removes
the second disjunct, and only with both clauses in hand does verification
establish that a rendering / a report is ACTUALLY DELIVERED for every input the
preconditions admit. This is not hypothetical: with clause (3) present and clause
(5) absent, a rival that keeps the modeled assembly's shape and exits by raising
verified against this spec while resolving nothing (properties.py case
`nondelivery-signalled-away-report`). §E states the two as Leg 1 and Leg 1b.

**Nor is the value leg about the runs the caller handed over, unless
preservation is stated.** A value clause is read in the POST-state, so
`ToSeq(Result()) == report_seq(ToSeq(demanded), ToSeq(found), ...)` relates the
report to whatever those runs say at the moment of return — not to what they said
on arrival. The half-permissions do not close this, because they may be held on
the SAME object: `demanded` and `found` supplied as one collection give
`Acc(...,1/2)` twice on one receiver, which sums to FULL permission, and an
implementation may then rewrite that collection and report the rewritten names,
satisfying every other clause. Spec clause (4) adds the preservation obligations
`ToSeq(x) == Old(ToSeq(x))` at both sites, which composed with the value clause
pin the report to the runs AS GIVEN. Rows A5 and B8 record this leg; §E states it
as Leg 3.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new helper — `as_scalar_or_list_str` (`core.py:57`)

Gold hunk (added at the top of `_check_required_columns`):
```python
def as_scalar_or_list_str(obj):
    if not hasattr(obj, "__len__"):
        return f"'{obj}'"
    elif len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)
```

| # | model.py impl op (`render_name_run`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `run: List[int]` (name tokens) | `obj` (a `list[str]` of column names) | R | a `list[str]` ↔ `List[int]` of name tokens (mapping.md §2); each `str` element ↔ one token. The scalar (`not hasattr __len__`) branch is unreachable for the two call sites (both pass lists) and is therefore not modeled — the modeled domain is exactly the list inputs the patch's callers supply. |
| A2 | `if len(run) == 1: return [39, encode_name(run[0]), 39]` | `elif len(obj) == 1: return f"'{obj[0]}'"` | R + A-reference | the length-1 branch renders the lone name apostrophe-wrapped. `quoted` encodes `'name'`; G-AX confirms `[39, encode_name(t), 39]` expands to the real `f"'{obj[0]}'"`. |
| A3 | else: build `[91] + joined(run) + [93]` via the backward construction loop | `else: return str(obj)` | R + A-reference | for any other length the rendering is the bracketed textual list form. The deep model `joined`/`quoted` and the verified loop spell out `[` + `'e0', 'e1', ...` + `]`; G-AX confirms the expansion equals the real `str(obj)` (lists of identifier names) over 20 000 fuzz cases. |
| A4 | `Requires(MustTerminate(len(run) + 2))` on `render_name_run`, `Invariant(MustTerminate(i + 1))` on the construction loop | the real helper always returns: the length-1 branch is a single f-string and the else-branch is one `str(obj)` call — neither re-enters `as_scalar_or_list_str` and neither loops | T | the real helper is TOTAL on every list input (mapping.md §4), so the obligation is TRUE of it on the whole modeled domain and constrains no input. It supplies the first half of what makes A2/A3 obligations about a rendering the caller RECEIVES: without it a rival could keep A2's length-1 branch verbatim and never return on the multi-name run, satisfying A2/A3 vacuously on exactly the run the change exists for. It does NOT supply the other half — an execution that stops promptly and leaves by the exceptional exit discharges it — which is row A6. |
| A5 | `Ensures(ToSeq(run) == Old(ToSeq(run)))` on `render_name_run` | the real helper only READS `obj`: `hasattr(obj, "__len__")`, `len(obj)`, `obj[0]`, `str(obj)` — there is no assignment to `obj` or to any element of it in any branch (`core.py:58-64` post-patch) | T | the run handed in comes back with the same names in the same order, so A2/A3 are about the rendering of the run the CALLER passed. TRUE of the real helper on the whole modeled domain, and it constrains no input. It matters because at the demanded-run call site the list passed is `required_columns`, which is `self._required_columns` itself (`core.py:74`) — the container's class-level declared list (`sampled.py:59`), not a copy — so a helper that wrote into `obj` would rewrite what the container demands for the rest of the session. |

| A6 | `Exsures(Exception, False)` on `render_name_run` | every exit of the real helper is a `return` of a single expression and there is no `raise` anywhere in its body: `return f"'{obj}'"` (`core.py:60`), `return f"'{obj[0]}'"` (`core.py:62`), `return str(obj)` (`core.py:64`). Nor can the guarded expressions signal on the modeled domain: `hasattr(obj, "__len__")` (`core.py:59`) returns a bool, `len(obj)` on a list returns an int, the `obj[0]` of `core.py:62` is reached only under the `len(obj) == 1` guard of `core.py:61` so the index is in range, and `str` of a list of name strings is total. The helper has exactly one way to end: handing back a rendering | T | the real helper never signals, so the obligation is TRUE of it on the whole modeled domain, and being demanded of every admissible run it constrains no input. It is the SECOND half of "the caller receives a rendering", and A4 does not contain it: `MustTerminate` is discharged by an execution that stops at once by raising, and every `Ensures` above — A2/A3's value clause and A5's preservation clause — is vacuous on such an execution. Load-bearing at THIS site specifically, not merely at B: before this row existed, a renderer that signalled away was rejected only incidentally, by `compose_leading_run_report`'s own contract at the in-module call site, so the renderer's contract said nothing about a caller outside the model — and the real helper's callers are the two `.format` arguments at `core.py:88-89`, which do consume its value. properties.py cases `nondelivery-signalled-away-render` and `nondelivery-late-after-build` pin it. |

`render_name_run`'s postcondition `ToSeq(Result()) == render_run(ToSeq(run))`
pins the rendering to the full run (every name, in order). The pre-patch had no
such helper — it echoed only the first name — so the prepatch skeleton (site B)
fails this exact full-run obligation.

## B. The report assembly — the `raise ValueError(...)` branch (`core.py:77-81`)

Gold hunk:
```python
- raise ValueError("{} object is invalid - expected '{}' "
-                  "as the first column{} but found '{}'"
-                  .format(self.__class__.__name__, required_columns[0], plural, self.colnames[0]))
+ raise ValueError("{} object is invalid - expected {} "
+                  "as the first column{} but found {}"
+                  .format(self.__class__.__name__, as_scalar_or_list_str(required_columns),
+                             plural, as_scalar_or_list_str(self.colnames[:len(required_columns)])))
```

| # | model.py impl op (`compose_leading_run_report`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `cls_name: List[int]` | `self.__class__.__name__` (a `str`) | R | class name `str` ↔ `List[int]` code points; emitted verbatim (mapping.md §2). |
| B2 | `expected_field = render_name_run(demanded)` | `as_scalar_or_list_str(required_columns)` | R + (calls A) | the demanded run is rendered by the helper of site A (caller uses the callee's spec — both are changed functions, §3 multi-site). `demanded` ↔ `required_columns`. |
| B3 | `found_field = render_name_run(found)` | `as_scalar_or_list_str(self.colnames[:len(required_columns)])` | R + (calls A) | the FOUND run is the leading `len(required_columns)` actual column names, rendered by the same helper. `found` ↔ `self.colnames[:len(required_columns)]`. This is the decisive change: the slice (the whole found run), not `self.colnames[0]`. |
| B4 | `plural = [115] if len(demanded) > 1 else []` | `plural = 's' if len(required_columns) > 1 else ''` (computed at `core.py:69`, used in the message) | I | identical length test and marker; `'s'` ↔ `[115]`, `''` ↔ `[]`. |
| B5 | literal segments `seg1/seg2/seg3` and the concatenation order | the format string `"{} object is invalid - expected {} as the first column{} but found {}"` | I + R | the fixed connective text is identical code points; `.format` positional substitution ↔ list concatenation in the same order. Note the literal apostrophes of the OLD template (`expected '{}'`) are gone — the helper now supplies them, matching the gold's `expected {}`. |
| B6 | postcondition `ToSeq(Result()) == report_seq(...)` | the assembled `ValueError` message | R + A-reference | the whole message is `report_seq`; G-AX confirms `report_seq` (expanded) equals the real `.format(...)` output, including the F2P scenario. |
| B7 | `Requires(MustTerminate(len(demanded) + len(found) + 6))` on `compose_leading_run_report` | the real assembly always completes: it is one `.format(...)` over two total helper calls and a constant plural test, with no loop and no re-entry of `_check_required_columns` | T | the real assembly is TOTAL on every input the branch reaches (mapping.md §4), so the obligation is TRUE of it and restricts no input. The assembly's budget exceeds the renderer's on the same runs, which is exactly the real call structure: the assembly may call the renderer twice and is still obliged to finish. Without this leg the whole message equality B6 is discharged vacuously by an assembly that never *finishes* building a message — the same hole at the second modeled site. It closes only the never-finishes shape of non-delivery, not the finishes-empty-handed shape, which is row B9. |
| B8 | `Ensures(ToSeq(cls_name) == Old(ToSeq(cls_name)))`, and the same for `demanded` and `found`, on `compose_leading_run_report` | the real assembly is one `"...".format(self.__class__.__name__, as_scalar_or_list_str(required_columns), plural, as_scalar_or_list_str(self.colnames[:len(required_columns)]))` (`core.py:86-89` post-patch): `str.format` reads its arguments, and both helper calls only read (A5), so neither `required_columns` nor the found slice nor the class name is mutated | T | the report describes the runs AS GIVEN. Load-bearing beyond the `Acc(...,1/2)` frame clauses: a permission of 1/2 forbids a write, but two of the three inputs may be the SAME object, and then the two halves sum to full permission. B6 alone is read in the post-state, so such an implementation could rewrite the collection, report the rewritten names, and satisfy B1-B7 — the shape properties.py case `aliased-input-rewritten` encodes, which VERIFIED before this row existed. |

| B9 | `Exsures(Exception, False)` on `compose_leading_run_report` | the modeled operation is the ASSEMBLY of the report, i.e. the `"...".format(self.__class__.__name__, as_scalar_or_list_str(required_columns), plural, as_scalar_or_list_str(self.colnames[:len(required_columns)]))` expression at `core.py:86-89`, whose value IS the report (mapping.md §2 — the enclosing `raise ValueError(...)` is how the real code hands that finished report to the user, so the report must exist before it can be delivered). Every part of that expression is total: `str.format` over a template with four positional `{}` fields and exactly four arguments supplied and no conversion specifiers cannot fail; `self.__class__.__name__` is an attribute read; `plural` is the already-computed local from `core.py:76`; and both `as_scalar_or_list_str` calls are exit-by-return-only by A6. The assembly has exactly one way to end: with a finished report | T | the real assembly never signals partway through building the report, so the obligation is TRUE of it and, being demanded of every admissible triple, constrains no input. Do not read it as denying that the real branch raises — it does, at `core.py:86`, and that `raise` is the modeled DELIVERY of the finished report, not a way of ending without one. This row is the one the recorded refutation of this bundle turned on: with B1-B8 in place and no delivery clause, a rival assembly verified against this spec, and refined faithfully it is the patch that leaves `_check_required_columns` with nothing to say — F2P `test_required_columns` and P2P `test_empty_initialization_invalid` both fail on it, because the branch no longer produces the message they assert against. Nagini drops its default no-exceptions check as soon as ANY `Exsures` is declared, and the declaration site is the marker-elided impl region, so nothing but a frozen clause here can reach it; because same-type `Exsures` posts are CONJOINED, a smuggled `Exsures(Exception, ...)` cannot relax this one. properties.py cases `nondelivery-signalled-away-report`, `nondelivery-true-contract-override`, `nondelivery-reraise-from-handler` and `nondelivery-partial-multiname` pin it, and `internal-signal-caught-admitted` pins that it constrains only the EXIT — an assembly that raises internally and handles it before returning the right report still verifies. |

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, A-reference, I, or T. The one operation that genuinely
*changed* — rendering the WHOLE leading run of names (and the matching template
adjustment) instead of only the first name — is modeled **deeply** (the folds
`render_run`/`joined`/`report_seq` and the verified loop), not hidden behind an
axiom about a callee. There is **no `@ContractOnly` axiom** in this bundle: the
proof depends on no opaque callee's `Ensures`. The deep models are instead
validated **== the real helper / real format string** by axiom_check.py (G-AX,
mapping.md §3) as **A-references**.

## D. G-DIFF — which prepatch fails, and on which clause

`model_prepatch.py` keeps the spec byte-identical and reverts ONLY
`compose_leading_run_report`'s impl to the pre-patch assembly: each field is
the apostrophe-wrapped FIRST name of its run (`[39, encode_name(run[0]), 39]`),
regardless of run length — exactly the old `required_columns[0]` /
`self.colnames[0]` behaviour. For a multi-name run this drops every name after
the first, so the assembled `result` differs from `report_seq(...)`, and
verification FAILS on the postcondition clause
`ToSeq(result) == report_seq(ToSeq(cls_name), ToSeq(demanded), ToSeq(found))`
(observed: `model_prepatch.py:236 Assert/postcondition might not hold`). This is
precisely the spec sensing the change: the demanded F2P scenario
(`['time','a']` vs `['time','b']`) renders the full runs post-patch but only
`'time'` vs `'time'` pre-patch — the misleading report the issue reports.

(Only one prepatch is needed: the helper `render_name_run` (gold
`as_scalar_or_list_str`) is a NEW function with no pre-patch counterpart; the
single independently-observable fixed behaviour is the report, whose pre-image
is the first-name-only assembly in `compose_leading_run_report`.)

Note that the prepatch skeleton TERMINATES and RETURNS — it is a straight-line
assembly that raises nothing — so it discharges the completion obligations A4/B7
and the delivery obligations A6/B9, and fails purely on the value clause. The
totality legs therefore do not mask the value leg: the prepatch is still rejected
for encoding the first-name-only report, which is the behaviour the change is
about. (The observed failure is exactly the value clause: `model_prepatch.py:331:
Assert might fail. Assertion (ToSeq(result) == report_seq(ToSeq(cls_name),
ToSeq(demanded), ToSeq(found))) might not hold.`)

## E. verify(model) ⇒ resolved

The argument has four legs, and ALL are needed. No proper subset bridges
verify ⇒ resolved.

**Leg 1 — completion (T; A4, B7).** `render_name_run` carries
`Requires(MustTerminate(len(run) + 2))` and its construction loop carries
`Invariant(MustTerminate(i + 1))`; `compose_leading_run_report` carries
`Requires(MustTerminate(len(demanded) + len(found) + 6))`. A verifying
implementation therefore ENDS in finitely many steps on every input the
preconditions admit — every run length, both boundary lengths, and in particular
the multi-name runs the change exists for. State the consequence precisely: what
this leg excludes is an execution that never gets to the point of answering, so
it leaves "reaches a return **or** leaves by the exceptional exit". This much the
value clauses cannot supply themselves: under partial correctness an `Ensures`
says nothing about an execution that never returns, and at a call the callee's
contract is merely assumed, so without A4/B7 an implementation could be
value-correct on every single-name (legacy) run and simply never finish on the
multi-name run, and still verify. The obligations are TRUE of the real callees — the real helper is one
f-string or one `str(obj)`, the real assembly is one `.format(...)` over two such
calls, none of which loops or re-enters itself (mapping.md §4) — so demanding
them excludes no faithful implementation and narrows no input domain. The budgets are LENGTH-SCALED (`len(run) + 2`; `len(demanded) + len(found) + 6`) rather than constant, so an implementation that works its run down to a strictly shorter one and re-enters itself -- a structurally recursive rendering -- still discharges the obligation; what is excluded is only coming back round on a run no shorter than the current one, i.e. never getting closer to delivering. A constant budget would have banned recursive descent outright and so over-fitted the reference construction's iterative loop; properties.py case `recursive-descent-admitted` pins that a descending implementation must VERIFY.

**Leg 1b — delivery (T; A6, B9).** Both modeled functions carry
`Exsures(Exception, False)`, i.e. the exceptional exit is unreachable on every
admissible input. Composed with Leg 1 this closes the remaining disjunct: a
verifying implementation does not merely stop, it stops by RETURNING, so a
rendering and a report are actually produced and the value clauses below are
obligations about a value the caller receives rather than about a value that would
have been correct had one ever arrived. Leg 1 cannot supply this and neither can
any `Ensures`. `MustTerminate` is discharged by the promptest possible
non-delivery — raise immediately — and an `Ensures` (value clause or `Old(...)`
preservation clause) constrains only the normal-return path, so on an exceptional
exit every one of A2/A3/A5/B1-B8 is vacuous while the caller gets no report at all.
The bundle has this on the record rather than as an argument: with Leg 1, Leg 2 and
Leg 3 all present and Leg 1b absent, a rival assembly VERIFIED against this spec,
and its faithful refinement is the patch on which the branch never builds the
message — F2P `test_required_columns` (1/1) and P2P
`test_empty_initialization_invalid` (1/20) both fail on it, since both assert
against a message that is no longer produced. Two further points on why the clause
must live in the FROZEN spec at BOTH sites. First, Nagini abandons its default
"method raises no exceptions" check the moment any `Exsures` is declared, and the
declaration can be made in the marker-elided impl region, which the frozen-spec
comparison does not see; a frozen `Exsures(Exception, False)` is immune because
same-type exceptional posts are CONJOINED into one obligation each, so a smuggled
duplicate can only add to it. Second, a single site would not do: before A6
existed, a renderer that signalled away was caught only by the in-module caller's
own contract, i.e. incidentally, leaving the renderer's own contract silent about
the delivery its real callers at `core.py:88-89` depend on. The obligations are
TRUE of the real callees — the helper's three exits at `core.py:60,62,64` are each
a `return` of one total expression with no `raise` anywhere in `core.py:58-64`, and
the assembly at `core.py:86-89` is one `str.format` over four supplied positional
arguments, an attribute read, and two calls covered by A6 — so this leg excludes
no faithful implementation and narrows no input domain. It also constrains only
the EXIT, not the internals: an implementation that raises and handles the signal
itself before returning the right report verifies, which properties.py case
`internal-signal-caught-admitted` pins.

**Leg 2 — value (R, A-reference; A2/A3, B1-B6).** Given, from Legs 1 and 1b
together, that a value IS
produced, `compose_leading_run_report` verifies only if its output equals
`report_seq(...)`, i.e. the full report rendering the WHOLE demanded run and the
WHOLE found run with the correct plural marker (B6); `render_name_run` verifies
only if it renders the full run (A2/A3). By R (str ↔ List[int] tokens, the
literal text identities, the identical plural test) the verified functions equal
the gold patch's helper and message on the tested inputs; by G-AX the deep models
equal the real helper and the real format string (A-references).

**Leg 3 — preservation (T; A5, B8).** Both modeled functions carry
`ToSeq(x) == Old(ToSeq(x))` for every run they are handed. A verifying
implementation therefore hands each run back with the same names in the same
order, which composed with Leg 2 makes the delivered report equal
`report_seq` of the runs AS THEY ARRIVED. Without this leg Leg 2 is a statement
about the runs' final contents only, and the aliased supply (`demanded` and
`found` one collection, two halves summing to full permission) lets an
implementation bring the two into agreement by rewriting the collection instead of
by reporting it: the report then names a column the caller never demanded while
every clause of Legs 1 and 2 holds. Refined faithfully that is a helper that
normalises names in place, which rewrites the container's own class-level
`_required_columns` (`core.py:74`, `sampled.py:59`) and so corrupts the successive
message assertions `test_required_columns` makes against that same list. The
obligations are TRUE of the real callees — every branch of the helper is a read
(`core.py:58-64`) and `str.format` reads its arguments (`core.py:86-89`) — so this
leg excludes no faithful implementation and narrows no input domain.

Composing the legs: a model satisfying this spec, refined by the map above,
finishes (Leg 1), finishes by returning rather than by signalling (Leg 1b), and so
delivers — on every admissible input, and leaving the runs it was given as it
found them (Leg 3) — exactly the gold patch's helper output and message (Leg 2), up
to type refinement and audited deep-model references. Dropping any one leg admits a
rival that verifies and does not resolve, and each of the four is exhibited as such
a rival in properties.py: Leg 1 by `non-completion-render-multiname` and
`non-completion-report-assembly`, Leg 1b by `nondelivery-signalled-away-report` and
`nondelivery-signalled-away-render`, Leg 2 by `partial-domain-first-name-only` (the
prepatch shape itself), Leg 3 by `aliased-input-rewritten`. The gold patch
resolves (G-RESOLVE), so the model resolves. The trust points are refinement
fidelity (this document, G-EQ) and the G-AX deep-model validation; there are no
consumed axioms.
