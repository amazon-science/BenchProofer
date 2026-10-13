"""properties.py — PBT falsification manifest for psf__requests-1142.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    announce_body_size(headers: Dict[int,int], method: int,
                        seekable: bool, stream_len: int,
                        body_present: bool, body_len: int) -> None

modeling the gold-patched `PreparedRequest.prepare_content_length`. Its
load-bearing contract:

    Requires(dict_pred(headers))                       # FULL permission (mutated)
    Requires(size_header() not in headers)             # header absent on entry
    Requires(Implies(seekable, body_present))          # a seekable stream IS a body
    Ensures (dict_pred(headers))
    Ensures (Implies(seekable,
                     size_header() in headers and headers[size_header()] == stream_len))          # (1)
    Ensures (Implies(not seekable and body_present,
                     size_header() in headers and headers[size_header()] == body_len))            # (2)
    Ensures (Implies(not seekable and not body_present,
                     (size_header() in headers) ==
                     (method != method_get() and method != method_head())))                       # (3) DISCRIMINATOR
    Ensures (Implies(not seekable and not body_present and method != GET and method != HEAD,
                     headers[size_header()] == 0))                                                 # (4)
    Ensures (Forall(int, k: Implies(k != size_header(),
                     (k in headers) == Old(k in headers))))                                        # (F1) frame
    Ensures (Forall(int, k: Implies(k != size_header() and k in headers and Old(k in headers),
                     headers[k] == Old(headers[k]))))                                              # (F2) frame
    Ensures (method == Old(method))                                                                # (5)

What the spec actually defends, and the attacks it must survive:

  * The behaviour is a small GROUNDED decision table over the args. There is NO
    axiomatised callee (meta.axioms == []) and NO @Pure answer-key oracle to
    echo: the @Pure helpers `size_header()`, `method_get()`, `method_head()` are
    constant identity TOKENS (0 / 1 / 2), not functions of the input. Every
    output the postcondition pins is a function of `stream_len` / `body_len` /
    `method` / the booleans, fully spelled out. So there is no "echo a wrong
    oracle" shortcut; the cheapest impl that satisfies the pins is the gold
    decision table itself (case `echo-honest` confirms this with an inline
    assertion). AXIOM_TESTS is therefore empty (no @ContractOnly axiom, no
    A-reference deep model) — see the assessment.

  * NO read-only (Acc(.,1/2)) input exists. The only heap input is `headers`,
    held at FULL permission precisely because it is mutated in place; `method`
    and the four lifted observations are pass-by-value primitives (immutable
    ints/bools), so there is no half-permission heap reference to overwrite. The
    classic frame-mutation probe (write to a 1/2 input to satisfy the pin
    vacuously) does not apply here; clause (5) `method == Old(method)` is
    nonetheless unbreakable because `method` is an immutable int. This is
    documented in the assessment rather than faked with an inapplicable probe.

  * The DISCRIMINATING content of the gold patch — a bodyless GET/HEAD must
    carry NO size header, while any other bodyless method announces zero — lives
    in clause (3). Every uniqueness rival targets exactly the clause it would
    have to break, with a refinement argument tying it to a real patch that
    would NOT resolve the F2P (`test_no_content_length`: bodyless GET and
    bodyless HEAD ⇒ 'Content-Length' not in headers).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION catching wrong behaviour
(or, for clause 5, the unchanged-method pin), never from a tampered spec.
"""
from pathlib import Path

INSTANCE = "psf__requests-1142"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The whole gold impl body (between # impl-start and # impl-end), used as a
# single replaceable block for structural rewrites.
_GOLD_IMPL = """    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0"""

# single-branch landmarks (impl region; the assignment form, distinct from the
# postcondition's `==` comparisons).
_SEEK_ASSIGN = "        headers[size_header()] = stream_len"
_METHOD_GUARD = "    elif method != method_get() and method != method_head():"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT: same decision table, branches
# REORDERED (bodyless-method case FIRST, then the seekable/body cases), the two
# token disequalities SWAPPED (method_head before method_get), and the
# body-present case reached via a plain `else` (sound because the precondition
# Implies(seekable, body_present) makes the only remaining case body_present).
# Semantically identical to gold, different source shape. No induction lemma is
# needed (straight-line guarded assignment), so a verify failure here would be a
# genuine SPEC-TOO-STRONG (over-fit to one branch order), not a proof gap.
_REORDERED_IMPL = """    if not seekable and not body_present:
        if method != method_head() and method != method_get():
            headers[size_header()] = 0
    elif seekable:
        headers[size_header()] = stream_len
    else:
        headers[size_header()] = body_len"""
_POS_REORDERED = _swap(_BASE, _GOLD_IMPL, _REORDERED_IMPL)

# (P2) ECHO-HONEST cheapest impl. There is no @Pure answer-key to echo (the
# helpers are constant tokens), so the cheapest impl satisfying the pins IS the
# gold decision table. This control keeps the gold impl verbatim and adds, right
# after it, an Assert that the post-state matches the spec decision table
# exactly — redundant with the gold proof, so it MUST verify. Its purpose is to
# demonstrate the spec is NOT echo-vulnerable: there is no WRONG echo that
# verifies (if one existed, this would instead be a SPEC-TOO-WEAK reject case).
_ECHO_ASSERT = """    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0
    Assert(Implies(seekable, headers[size_header()] == stream_len))
    Assert(Implies(not seekable and body_present, headers[size_header()] == body_len))
    Assert(Implies(not seekable and not body_present,
                   (size_header() in headers) ==
                   (method != method_get() and method != method_head())))"""
_POS_ECHO = _swap(_BASE, _GOLD_IMPL, _ECHO_ASSERT)

# (P3) ADMISSIBILITY. A self-call on an F2P-shaped input — a bodyless GET
# (not seekable, not body_present, method == method_get()) — must establish the
# precondition: dict_pred on a fresh empty header map, size_header() absent, and
# Implies(seekable, body_present) (vacuously true, seekable False). If the
# self-call fails to verify the precondition for this normal F2P input =>
# PRECOND-TOO-STRONG. The fresh dict literal `{}` carries dict_pred and has no
# keys, so size_header() not in it holds.
#
# TERMINATION BOOKKEEPING (added with the MustTerminate obligation): the
# self-call is GUARDED by `if body_present:` solely to discharge the obligation.
# The probe is a bodyless call, which sits at level 2, so the caller must sit
# strictly above it; inside this guard body_present holds, so the caller is at
# level 3. Measured: with the self-call UNGUARDED, Nagini reports "Obligation
# leak check failed. Callee announce_body_size might not take all unsatisfied
# obligations from the caller" — and raising the method's own level does NOT
# help (level 10 leaks identically), because a constant level moves both sides
# of the comparison together and can never satisfy n > n against itself. So the
# guard is what makes the obligation dischargeable, NOT a weakening of the
# probe: the precondition conjuncts are still checked at a real call site on the
# same F2P-shaped bodyless-GET input. That rejection was about the CALL SITE's
# level, not about the precondition, so leaving it unguarded would report
# PRECOND-TOO-STRONG for a domain fact that is perfectly establishable — a false
# finding against the spec. NON-VACUITY CONTROL (measured): replacing the guard
# body with `Assert(False)` FAILS to verify, so the guarded branch is genuinely
# reachable and the self-call still proves something.
_ADMISS_IMPL = """    if body_present:
        probe = {}  # type: Dict[int, int]
        announce_body_size(probe, method_get(), False, 0, False, 0)
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0"""
_POS_ADMISS = _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) THE DISCRIMINATING BUG — the pre-patch behaviour (model_prepatch.py):
# unconditionally announce zero FIRST, with no method guard. For a bodyless
# GET/HEAD this leaves the size header present (== 0) but clause (3) requires it
# ABSENT. Its faithful real patch is exactly the pre-patch code
# (`self.headers['Content-Length'] = '0'` before the branches, no method guard),
# which FAILS the F2P test_no_content_length (bodyless GET/HEAD must carry no
# Content-Length) — so it would NOT resolve.
_PREPATCH_IMPL = """    headers[size_header()] = 0
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_IMPL, _PREPATCH_IMPL)

# (U2) DROP THE METHOD GUARD entirely: announce zero for EVERY bodyless request
# regardless of method. Differs from U1 in shape (no leading write; the zero is
# in the final branch reached unconditionally for the bodyless case) but has the
# same observable defect: bodyless GET/HEAD now carries Content-Length == 0,
# violating clause (3). Faithful real patch: `elif body is None: ...='0'` with no
# method test — the pre-#957-fix-style code that still sets Content-Length on
# bodyless GET/HEAD and so FAILS test_no_content_length. Would NOT resolve.
_NO_GUARD_IMPL = """    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    else:
        headers[size_header()] = 0"""
_RIVAL_NO_GUARD = _swap(_BASE, _GOLD_IMPL, _NO_GUARD_IMPL)

# (U3) PARTIAL-DOMAIN: guard only excludes GET, not HEAD. Correct on bodyless GET
# (no header) and on every payload-carrying method (zero), but WRONG on bodyless
# HEAD: it still announces zero. A faithful real patch of this shape
# (`self.method not in ('GET',)` — forgetting HEAD) passes the GET half of the
# F2P but FAILS the HEAD half (head_req: 'Content-Length' not in headers), so it
# would NOT resolve. Rejection source: clause (3) for method == method_head() in
# the bodyless case: (size_header() in headers) == (method != GET and method !=
# HEAD) becomes True == (True and False) == False — contradiction.
_HEAD_ONLY_GUARD = "    elif method != method_get():"
_RIVAL_PARTIAL_HEAD = _swap(_BASE, _METHOD_GUARD, _HEAD_ONLY_GUARD)

# (U4) WRONG STREAM VALUE (value-divergence on the seekable branch): announce the
# non-stream body length `body_len` instead of the measured stream length
# `stream_len`. A faithful real patch using `len(body)` instead of
# `str(body.tell())` for a seekable stream would announce the wrong size whenever
# the stream's measured length differs from len(body) (e.g. a file opened
# mid-way, or any stream where len() is unavailable / wrong) and would FAIL the
# size-correctness behaviour that P2P test_basic_building and the gold contract
# pin. Rejection source: clause (1) headers[size_header()] == stream_len, which
# is violated whenever stream_len != body_len.
_RIVAL_WRONG_STREAM = _swap(_BASE, _SEEK_ASSIGN,
                            "        headers[size_header()] = body_len")

# (U5) EXTRA-HEADER SMUGGLE (frame violation): behave correctly on the size
# header but ALSO write an unrelated header key (token 42) into the map. This
# is the G-PANEL-1 audit's winning attack against the frame-less spec: clauses
# (1)-(4) only pin size_header(), so without a whole-map frame the spec admits
# an impl whose faithful real patch injects a spurious header (e.g.
# `self.headers['X-Content-Probe'] = '12345'`) into every prepared request —
# observably different wire behaviour from the gold patch. Rejection source:
# frame clause (F1): 42 in headers post-state, but Old(42 in headers) is not
# guaranteed, so (42 in headers) == Old(42 in headers) fails.
_EXTRA_KEY_IMPL = """    headers[42] = 12345
    if seekable:
        headers[size_header()] = stream_len
    elif body_present:
        headers[size_header()] = body_len
    elif method != method_get() and method != method_head():
        headers[size_header()] = 0"""
_RIVAL_EXTRA_KEY = _swap(_BASE, _GOLD_IMPL, _EXTRA_KEY_IMPL)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different but CORRECT impl (bodyless-method branch first, "
                  "token disequalities swapped, body case via plain else justified by the "
                  "Implies(seekable, body_present) precondition). Straight-line guarded "
                  "assignment, no induction needed. If it fails to verify the postcondition "
                  "is over-fit to the gold branch order => SPEC-TOO-STRONG."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _POS_ECHO,
     "rationale": "the oracle is GROUNDED (constant @Pure tokens, outputs are functions of "
                  "the args), so there is no wrong echo. The cheapest impl satisfying the "
                  "pins is the gold table; asserting the decision table after it is redundant "
                  "with the gold proof and MUST verify. Demonstrates the spec is NOT "
                  "echo-vulnerable (else this would be a SPEC-TOO-WEAK reject case)."},
    {"id": "admiss-bodyless-get", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on an F2P-shaped input (bodyless GET: not seekable, not "
                  "body_present, method_get()) on a fresh empty header map must establish the "
                  "precondition (dict_pred, size_header() absent, Implies(seekable, "
                  "body_present) vacuous). If not => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-prepatch-unconditional", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this is the pre-patch behaviour (model_prepatch.py): unconditionally set "
                   "Content-Length = '0' first, no method guard. Its faithful real patch is "
                   "exactly the pre-gold prepare_content_length, which leaves Content-Length "
                   "present (=0) on a bodyless GET/HEAD and so FAILS the F2P "
                   "test_no_content_length — it would NOT resolve.",
     "rationale": "the discriminating bug. Rejection source: postcondition clause (3) "
                  "Implies(not seekable and not body_present, (size_header() in headers) == "
                  "(method != GET and method != HEAD)) — for a bodyless GET/HEAD the header "
                  "is present (True) but the RHS is False. If it verified => SPEC-TOO-WEAK "
                  "(admits the pre-patch bug; this is exactly the G-DIFF discriminator)."},
    {"id": "rival-drop-method-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_GUARD,
     "refinement": "announces zero for EVERY bodyless request (else branch, no method test). "
                   "A faithful real patch dropping the `self.method not in ('GET','HEAD')` "
                   "condition still sets Content-Length on bodyless GET/HEAD and FAILS "
                   "test_no_content_length — it would NOT resolve.",
     "rationale": "same observable defect as U1 via a different impl shape. Rejection source: "
                  "clause (3) — bodyless GET/HEAD carries the header (True) while the RHS is "
                  "False. If it verified => SPEC-TOO-WEAK (the method guard is unenforced)."},
    {"id": "partial-domain-head-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_HEAD,
     "refinement": "guards only GET (`method != method_get()`), forgetting HEAD — correct on "
                   "bodyless GET and on payload-carrying methods, WRONG on bodyless HEAD "
                   "(announces zero). A faithful real patch `self.method not in ('GET',)` "
                   "passes the GET half of the F2P but FAILS the HEAD half (head_req: "
                   "'Content-Length' not in headers) — it would NOT resolve.",
     "rationale": "partial-domain: pins the GET sub-domain but diverges on bodyless HEAD. "
                  "Rejection source: clause (3) for method == method_head() in the bodyless "
                  "case — (size_header() in headers) == (method != GET and method != HEAD) "
                  "becomes True == (True and False) == False. If it verified => SPEC-TOO-WEAK "
                  "(HEAD sub-domain uncovered)."},
    {"id": "rival-wrong-stream-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_STREAM,
     "refinement": "the seekable-stream branch announces body_len instead of the measured "
                   "stream_len. A faithful real patch using `str(len(body))` instead of "
                   "`str(body.tell())` for a seekable stream announces the wrong size whenever "
                   "the stream's measured length differs from len(body), violating the "
                   "size-correctness behaviour the gold contract and P2P pin — it would NOT "
                   "resolve (and len() is undefined on many seekable streams).",
     "rationale": "value-divergence on the seekable branch. Rejection source: clause (1) "
                  "headers[size_header()] == stream_len, violated whenever stream_len != "
                  "body_len. If it verified => SPEC-TOO-WEAK (stream size unpinned)."},
    {"id": "rival-extra-header-smuggle", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_KEY,
     "refinement": "correct on the size header but ALSO injects an unrelated header (key 42). "
                   "Its faithful real patch adds e.g. `self.headers['X-Content-Probe'] = "
                   "'12345'` to prepare_content_length — every prepared request then carries "
                   "a spurious header the gold patch never sends, observably different wire "
                   "behaviour (and the exact impl the G-PANEL-1 audit exhibited against the "
                   "frame-less spec).",
     "rationale": "frame violation. Rejection source: frame clause (F1) Forall k != "
                  "size_header(): (k in headers) == Old(k in headers) — key 42 becomes "
                  "present though it need not have been on entry. If it verified => "
                  "SPEC-TOO-WEAK (map frame unenforced; extra headers smuggleable)."},
]

# ===========================================================================
# AXIOM LANE — empty for this instance.
# ===========================================================================
# meta.axioms == [], deep_model_references == []: the changed operation (the
# guarded body-size announcement) is modeled DEEPLY in the impl region, with no
# @ContractOnly axiom and no A-reference deep model. There is therefore no
# real-callee soundness obligation and no caller-domain containment obligation to
# probe in Docker. (axiom_check.py separately runs a stdlib-only deep-model
# self-consistency oracle for G-AX; it is not an axiom probe.)
AXIOM_TESTS = []
