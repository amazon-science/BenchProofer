"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-11510.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    forward_with_source_read(t_pre: Place, lines: List[int]) -> List[int]

i.e. the gathered-include-content forwarding step the gold patch installs as the
``_insert_input`` closure inside ``Include.run``. Load-bearing contract (stated
under IOExists1(Place)(lambda t_post: ...)):

    Requires(Acc(list_pred(lines), 1/2))      # READ-ONLY input (1/2 share)
    Requires(len(lines) >= 2)                  # at least the two framing markers
    Requires(token(t_pre, 3) and
             hook_offer_io(t_pre, ToSeq(lines).take(len-2), t_post))  # ONE licensed offer
    Requires(MustTerminate(3))
    Ensures (token(t_post))                                          # the offer HAPPENED
    Ensures (Acc(list_pred(lines), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (ToSeq(Result()) == transformed(ToSeq(lines)))            # THE pin
    Ensures (len(Result()) >= 2)
    Ensures (ToSeq(Result()).drop(len-2) == ToSeq(lines).drop(len-2)) # markers verbatim
    Ensures (ToSeq(Result()).take(len-2) == hook(ToSeq(lines).take(len-2)))  # body = offered region

with
    transformed(lines) = hook(lines.take(len-2)) + lines.drop(len-2)
    hook  : @Pure @ContractOnly UNINTERPRETED (no Ensures)
    hook_offer_io(t_pre, region, t_post): @IOOperation, Terminates(True) — the
                            EFFECT of showing `region` to the hook once
    emit_and_collect(t_pre, body): @ContractOnly, Acc(list_pred(body),1/2),
                            Requires token(t_pre,2) and
                                     hook_offer_io(t_pre, ToSeq(body), t_post),
                            Ensures token(t_post) and
                                    ToSeq(Result()) == hook(ToSeq(body))

What the spec defends, and the attacks it must survive:

  * The output pin is GROUNDED in the input, not pinned to an oracle answer-key.
    `hook` is an UNINTERPRETED @Pure symbol with NO Ensures; the only way to make
    `ToSeq(Result())` contain `hook(ToSeq(lines).take(n-2))` is to call
    `emit_and_collect` on a body whose `ToSeq` is provably `ToSeq(lines).take(n-2)`
    — i.e. to actually offer the markers-excluded body region to the dispatcher.
    There is NO executable materialization of the @Pure `hook` PSeq into a
    list_pred list, so there is no "echo a wrong answer" shortcut. Because hook is
    a congruent function of its argument and Viper cannot prove
    `hook(A) == hook(B)` for A != B (as PSeq), any rival that offers a DIFFERENT
    region (full lines / one marker dropped / forwarded verbatim / empty-body
    sub-domain) cannot discharge the pin. Hence the value-side uniqueness rivals
    target WHICH region is offered and how the markers are framed (the exact gold
    discriminator, see G-LEAK semantic note: offering the markers to source-read
    yields a wrong F2P parse), and the effect-side rivals below target HOW MANY
    offers happen — the one thing no clause about the returned value can see.

  * The OFFER IS AN EFFECT, and the effect discipline is what the value pin
    cannot see. Two impls can return the same sequence while having shown the
    registered transformers different content, or content twice, or nothing at
    all — a discarded offer is invisible to every value clause, because the value
    clauses quantify only over what is returned. So the number of offers and the
    region each offer shows are carried as an IO obligation: the step is handed
    `token(t_pre, 3)` plus ONE instance of `hook_offer_io(t_pre, body_region,
    t_post)`, `emit_and_collect` spends exactly that instance (its Requires names
    the region it shows, `ToSeq(body)`) and yields `token(t_post)`, and the step
    must hand `token(t_post)` back. Neither a token nor an operation instance can
    be created by an implementation, so:
      - forwarding without offering cannot produce `token(t_post)`  (the token is
        obtainable only by making the offer) — `rival-forward-verbatim`,
        `rival-partial-skip-offer`;
      - an offer of any other region has no matching instance —
        `rival-offer-full-lines`, `rival-one-marker`, `rival-alias-empty-body`;
      - a SECOND offer of anything has no instance left, and a fabricated place
        carries no token — `rival-extra-offer-full-lines`,
        `rival-forge-place-second-offer`, `rival-duplicate-offer`.
    These are the rivals the value clauses alone admitted: an impl that forwards
    the correct sequence and ALSO shows the transformers the whole gathered
    sequence satisfies every value clause, and its faithful real counterpart
    (a second dispatch of the full `include_lines`) fails F2P.

  * `lines` is held read-only (1/2). The mandatory attack is FRAME MUTATION
    (`frame-mutate-lines`): a rival that WRITES to `lines` to satisfy the pin
    vacuously must fail for INSUFFICIENT PERMISSION (the gold scaffolding is kept
    verbatim around the write so the rejection is attributable to the store).

  * No deep-model / A-reference axiom whose Ensures is consumed numerically; the
    one A-consumed axiom (`emit_and_collect`) wraps the REAL
    `EventManager.emit('source-read', ...)` + the line<->text round trip, checked
    by axiom_check.py / G-AX. The AXIOM_TESTS lane re-runs that real callee in
    Docker (apply_gold=True) for soundness (the marker frame holds on the real
    dispatcher) and caller-domain containment.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`) that
edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION (or the permission
system), never from a tampered spec. For rivals that change WHICH region is
offered, the now-false gold asserts inside the impl region are dropped together
with the body line, so the rejection lands on the `transformed`/body
postcondition clause rather than on a stale assert. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11510"
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
# Region landmarks — all strictly INSIDE the impl region of model.py.
# ---------------------------------------------------------------------------

# The whole gold impl body (between # impl-start and # impl-end). Used as a
# single replaceable block for the region-changing rivals so that no stale
# (now-false) assert survives to mask the postcondition rejection.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    # Split off the authored body (all but the final two framing markers) and\n"
    "    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.\n"
    "    body = lines[:n - 2]\n"
    "    markers = lines[n - 2:]\n"
    "    Assert(ToSeq(body) == ToSeq(lines).take(n - 2))\n"
    "    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))\n"
    "    # Offer the body to the content-transformation hook, spending the step's one\n"
    "    # licence; its (possibly rewritten) result replaces the body region.\n"
    "    new_body = emit_and_collect(t_pre, body)\n"
    "    Assert(ToSeq(new_body) == hook(ToSeq(lines).take(n - 2)))\n"
    "    # Re-attach the framing markers, in their original positions, after the\n"
    "    # transformed body, and forward the result.\n"
    "    result = new_body + markers\n"
    "    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))\n"
    "    return result\n"
    "    # impl-end"
)

# sanity: the reconstructed gold impl block must be present, exactly once.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block landmark drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (4) Structurally-different but CORRECT. Same operation, but the statement
# order is reshaped: compute `markers` FIRST, give the body a different local
# name (`auth`), splice as `markers`-tail after the hooked body. Semantically
# identical to gold; different source. If this fails to verify the postcondition
# is over-fit to one statement order / local layout => SPEC-TOO-STRONG.
_POS_REORDER_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    markers = lines[n - 2:]\n"
    "    auth = lines[:n - 2]\n"
    "    Assert(ToSeq(markers) == ToSeq(lines).drop(n - 2))\n"
    "    Assert(ToSeq(auth) == ToSeq(lines).take(n - 2))\n"
    "    hooked = emit_and_collect(t_pre, auth)\n"
    "    Assert(ToSeq(hooked) == hook(ToSeq(lines).take(n - 2)))\n"
    "    out = hooked + markers\n"
    "    Assert(ToSeq(out) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))\n"
    "    return out\n"
    "    # impl-end"
)
_POS_REORDER = _swap(_BASE, _GOLD_IMPL, _POS_REORDER_IMPL)

# (2 / honest positive control for the GROUNDED oracle) The hook is grounded:
# there is no executable materialization of the @Pure `hook` to echo, so the
# cheapest impl still has to offer the body region to `emit_and_collect`. This
# control is the gold impl with an extra assertion, right before the return,
# that the value it built equals the spec function `transformed(ToSeq(lines))`.
# It is CORRECT (expect="verify"); its purpose is to demonstrate there is no
# wrong oracle-echo that verifies (the result must be PRODUCED by the modeled
# dispatch on the modeled region, not equated to an opaque marker). If you could
# echo a wrong answer and still verify, this would instead be a reject case;
# here no such echo exists.
_ECHO_RETURN = (
    "    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))\n"
    "    return result\n"
)
_ECHO_RETURN_NEW = (
    "    Assert(ToSeq(result) == hook(ToSeq(lines).take(n - 2)) + ToSeq(lines).drop(n - 2))\n"
    "    Assert(ToSeq(result) == transformed(ToSeq(lines)))\n"
    "    return result\n"
)
_ECHO_HONEST = _swap(_BASE, _ECHO_RETURN, _ECHO_RETURN_NEW)

# (6) ADMISSIBILITY. An F2P-shaped probe input — the
# `test_include_source_read_event` start-line shape ["", body, marker_a, marker_b]
# modeled as four opaque line identities [0,1,2,3] (len 4 >= 2) — must establish
# the VALUE half of the precondition, Acc(list_pred(.),1/2) & len>=2. If it fails
# to verify for a normal F2P input => PRECOND-TOO-STRONG. The probe list is
# created locally (full perm) so holding it at 1/2 is admissible. The effect half
# of the precondition (token + one `hook_offer_io` licence) is a RESOURCE, not a
# constraint on the input value: it restricts no line sequence, and it is
# non-contradictory — were it contradictory the impl would prove anything and
# `rival-vacuous-precondition` (which asserts False under it) would verify. So
# the two halves together admit exactly the F2P line shapes.
_ADMISS_HEAD = "    # impl-start\n    n = len(lines)\n"
_ADMISS_HEAD_NEW = (
    "    # impl-start\n"
    "    probe = [0, 1, 2, 3]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(len(probe) >= 2)\n"
    "    n = len(lines)\n"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `lines` is read-only
# (1/2). This rival WRITES `lines[0] = 0` before the gold body. The gold
# scaffolding is kept verbatim around it, so the failure is attributable solely
# to the store. Under Acc(list_pred(lines),1/2) a store to `lines` requires FULL
# permission, so it MUST fail for INSUFFICIENT PERMISSION (not a value mismatch).
_FRAME_IMPL = _swap(
    _GOLD_IMPL,
    "    # impl-start\n    n = len(lines)\n",
    "    # impl-start\n    lines[0] = 0\n    n = len(lines)\n",
)
_RIVAL_FRAME = _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL)

# (2) FORWARD-VERBATIM — the actual pre-patch BUG (== model_prepatch.py). The
# gathered lines are forwarded WITHOUT being offered to the hook:
# `result = lines[:n]` (a fresh full-perm copy, same elements, no event). Then
# ToSeq(Result()) == ToSeq(lines), but the pin needs hook(take(n-2)) + drop(n-2);
# since `hook` is uninterpreted, ToSeq(lines).take(n-2) is not provably equal to
# hook(ToSeq(lines).take(n-2)), so the `transformed` postcondition fails.
_VERBATIM_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    result = lines[:n]\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_VERBATIM = _swap(_BASE, _GOLD_IMPL, _VERBATIM_IMPL)

# (3) OFFER-FULL-LINES — the markers-not-excluded bug. The FULL gathered lines
# (markers included) are offered to the hook: body = lines[:n] (everything),
# markers = lines[n:] (empty). Rejected twice over: the step holds a licence for
# an offer of `ToSeq(lines).take(n-2)` only, so showing the hook `ToSeq(lines)`
# has no matching `hook_offer_io` instance (insufficient permission at the
# emit_and_collect call); and even granted the offer, ToSeq(result) ==
# hook(ToSeq(lines)) cannot discharge the pin hook(take(n-2)) ++ drop(n-2) with
# `hook` uninterpreted, nor the marker-preservation clause.
_FULL_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    body = lines[:n]\n"
    "    markers = lines[n:]\n"
    "    new_body = emit_and_collect(t_pre, body)\n"
    "    result = new_body + markers\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_FULL = _swap(_BASE, _GOLD_IMPL, _FULL_IMPL)

# (4) ONE-MARKER — only the LAST line is held out of the hook instead of the
# final two: body = lines[:n-1], markers = lines[n-1:]. Rejected on the offered
# region (the licence names take(n-2), not take(n-1), so the offer of
# ToSeq(lines).take(n-1) has no instance) and, granted the offer, on the pin
# (hook(take(n-1)) ++ drop(n-1) cannot discharge hook(take(n-2)) ++ drop(n-2)
# with `hook` uninterpreted) and on the body clause.
_ONE_MARKER_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    body = lines[:n - 1]\n"
    "    markers = lines[n - 1:]\n"
    "    new_body = emit_and_collect(t_pre, body)\n"
    "    result = new_body + markers\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_ONE_MARKER = _swap(_BASE, _GOLD_IMPL, _ONE_MARKER_IMPL)

# (5) PARTIAL-DOMAIN — correct on every input with a non-empty body (n > 2) but
# forwards VERBATIM when the body is empty (n == 2, the two-markers-only shape,
# the boundary the precondition admits: len>=2). On that sub-domain it makes no
# offer at all, so it cannot hand back token(t_post) (the token is obtainable
# only by making the licensed offer); and the pin needs hook(take(0)) ++ drop(0)
# = hook(empty) ++ lines while the rival returns ToSeq(lines), which with `hook`
# uninterpreted is not provably that. A faithful real patch of this shape (skip
# the source-read event when the included file is empty) would NOT emit the event
# for an empty include and so diverge from gold on empty bodies.
_PARTIAL_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    body = lines[:n - 2]\n"
    "    markers = lines[n - 2:]\n"
    "    if n == 2:\n"
    "        result = lines[:n]\n"
    "        return result\n"
    "    new_body = emit_and_collect(t_pre, body)\n"
    "    result = new_body + markers\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_PARTIAL = _swap(_BASE, _GOLD_IMPL, _PARTIAL_IMPL)

# (6) EXTRA-OFFER-FULL-LINES — the counterexample family the value clauses
# admitted: the gold computation VERBATIM (so every value clause holds, the
# returned sequence is bit-identical to gold's) plus one MORE offer, showing the
# hook the whole gathered sequence and discarding what comes back. A discarded
# offer is invisible to every clause about the returned value; it is visible to
# the transformers, which is what the behaviour is about. Rejected because the
# step holds ONE `hook_offer_io` instance and the gold offer already spent it (and
# the token with it), so the second emit_and_collect call has neither.
_EXTRA_FULL_IMPL = _swap(
    _GOLD_IMPL,
    "    result = new_body + markers\n",
    "    whole = lines[:n]\n"
    "    ignored = emit_and_collect(t_pre, whole)\n"
    "    result = new_body + markers\n",
)
_RIVAL_EXTRA_FULL = _swap(_BASE, _GOLD_IMPL, _EXTRA_FULL_IMPL)

# (7) FORGE-PLACE-SECOND-OFFER — the same extra offer, but reaching for a place
# of its own (`Place()`) so as not to spend the step's own token. Places are not
# a source of tokens or licences: `token(Place(), 2)` is not held by anyone and
# cannot be folded, so the fabricated offer has no permission. This is the
# effect-side twin of `frame-mutate-lines`: it exists to test whether the
# one-offer discipline can be subverted by minting the resource it rations.
_FORGE_IMPL = _swap(
    _GOLD_IMPL,
    "    result = new_body + markers\n",
    "    p = Place()\n"
    "    whole = lines[:n]\n"
    "    ignored = emit_and_collect(p, whole)\n"
    "    result = new_body + markers\n",
)
_RIVAL_FORGE = _swap(_BASE, _GOLD_IMPL, _FORGE_IMPL)

# (8) DUPLICATE-OFFER — shows the hook the RIGHT region, twice, forwarding the
# second result. Every value clause still holds (both results are hook(body)), so
# only the effect discipline separates it from gold: there is one licence, and the
# first offer spent it.
_DUP_IMPL = _swap(
    _GOLD_IMPL,
    "    result = new_body + markers\n",
    "    again = emit_and_collect(t_pre, body)\n"
    "    result = again + markers\n",
)
_RIVAL_DUP = _swap(_BASE, _GOLD_IMPL, _DUP_IMPL)

# (9) ALIAS/BOUNDARY — at the empty-body boundary (n == 2) it offers the input
# list ITSELF (the alias case: body and the gathered sequence are the same
# object, markers empty), and is gold elsewhere. The licensed region there is
# take(0) = the empty sequence, so showing the hook ToSeq(lines) has no matching
# instance; the pin fails too (hook(lines) ++ empty vs hook(empty) ++ lines).
_ALIAS_IMPL = (
    "    # impl-start\n"
    "    n = len(lines)\n"
    "    if n == 2:\n"
    "        whole = emit_and_collect(t_pre, lines)\n"
    "        return whole\n"
    "    body = lines[:n - 2]\n"
    "    markers = lines[n - 2:]\n"
    "    new_body = emit_and_collect(t_pre, body)\n"
    "    result = new_body + markers\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_ALIAS = _swap(_BASE, _GOLD_IMPL, _ALIAS_IMPL)

# (10) VACUITY CONTROL — the strengthened precondition carries RESOURCES (a token
# and one operation instance). A resource precondition that is contradictory
# would make every implementation verify, i.e. the strongest possible weakness,
# and it would not show up as a value-clause failure anywhere. So assert False
# under it: this must be REJECTED. If it verifies the precondition is infeasible
# and the whole cell proves nothing.
_VACUITY_IMPL = _swap(
    _GOLD_IMPL,
    "    # impl-start\n    n = len(lines)\n",
    "    # impl-start\n    Assert(False)\n    n = len(lines)\n",
)
_RIVAL_VACUITY = _swap(_BASE, _GOLD_IMPL, _VACUITY_IMPL)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT: markers computed first, body "
                  "given a different local name, same hooked-body ++ markers splice. "
                  "Keeps the gold proof obligations (the take/drop asserts) valid, so it "
                  "is not a proof-gap case. If it fails to verify the postcondition is "
                  "over-fit to one statement order/local layout => SPEC-TOO-STRONG."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the output pin is GROUNDED in the input (hook is an uninterpreted "
                  "@Pure symbol applied to the modeled body region; no executable "
                  "materialization to echo). The cheapest impl still offers the body to "
                  "emit_and_collect. Asserting result == transformed(ToSeq(lines)) before "
                  "return is redundant with the gold proof and must verify. Demonstrates "
                  "the spec is NOT echo-vulnerable: there is no wrong oracle-echo that "
                  "verifies (else this would be a reject case)."},
    {"id": "admiss-f2p-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "an F2P-shaped probe input [0,1,2,3] (the start-line shape "
                  "['', body, marker_a, marker_b], len 4 >= 2) must establish the VALUE half "
                  "of the precondition, Acc(list_pred(.),1/2) & len>=2; if not, "
                  "PRECOND-TOO-STRONG. The probe is a locally-created full-perm list, so "
                  "holding it at 1/2 is admissible. The effect half (token + one offer "
                  "licence) constrains no line sequence and is feasible — see "
                  "rival-vacuous-precondition, which asserts False under it and must be "
                  "rejected."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-lines", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: the gold `_insert_input` "
                   "never mutates its `include_lines` argument (it builds `text` and a new "
                   "list `text.splitlines() + include_lines[-2:]`). The rival exists only "
                   "to test whether the read-only (1/2) precondition can be subverted by "
                   "writing to `lines`. There is no resolving patch that overwrites its "
                   "gathered-lines input, so a verifying rival here would be a pure "
                   "verify⇏resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `lines[0] = 0` writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION. "
                  "Rejection source: the PERMISSION SYSTEM (a store needs full perm), not a "
                  "value mismatch; the gold scaffolding is kept verbatim. If it verified => "
                  "SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "rival-forward-verbatim", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_VERBATIM,
     "refinement": "this is the PRE-PATCH behaviour (== model_prepatch.py): the gathered "
                   "lines reach the parser without being offered to the source-read hook. "
                   "Its faithful real patch is precisely the un-patched `Include.run` that "
                   "FAILS both F2P tests (test_include_source_read_event never sees "
                   "'baz/baz' in sources_reported; the nested-include rewrite #magical-> "
                   "amazing never reaches the parsed body). So it would NOT resolve.",
     "rationale": "the discriminating bug the patch fixes. Rejection source: it makes no "
                  "offer, so it can neither hand back token(t_post) (reachable only through "
                  "the licensed offer) nor discharge the pin ToSeq(Result()) == "
                  "transformed(ToSeq(lines)) = hook(take(n-2)) ++ drop(n-2), since "
                  "forwarding verbatim gives ToSeq(lines) and the uninterpreted `hook` makes "
                  "take(n-2) != hook(take(n-2)) unprovable. If it verified => SPEC-TOO-WEAK "
                  "(admits the un-patched code)."},
    {"id": "rival-offer-full-lines", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FULL,
     "refinement": "offers the FULL gathered lines (the two docutils-0.18 framing markers "
                   "INCLUDED) to the source-read event instead of `include_lines[:-2]`. "
                   "This is the exact semantic discriminator (G-LEAK note): the panel "
                   "proved that offering the markers to source-read yields a WRONG F2P "
                   "parse (the markers get rewritten/parsed as authored content). A "
                   "faithful real patch dropping the `[:-2]` slice would FAIL the F2P tests "
                   "(the offered text != '\\nBaz was here.'), so it would NOT resolve.",
     "rationale": "marker-not-excluded bug. Rejection source: the licence names the region "
                  "take(n-2), so an offer of ToSeq(lines) has no matching hook_offer_io "
                  "instance; and granted the offer, the pin / the marker clause "
                  "ToSeq(Result()).drop(len-2) == ToSeq(lines).drop(len-2) and the body "
                  "clause take(len-2) == hook(take(len-2)) still fail, since hook(full) "
                  "cannot discharge hook(take(n-2)) ++ drop(n-2) (uninterpreted hook). If it "
                  "verified => SPEC-TOO-WEAK (marker frame hollow)."},
    {"id": "rival-one-marker", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ONE_MARKER,
     "refinement": "holds out only the LAST line from the hook (`include_lines[:-1]`) "
                   "instead of the final TWO. A faithful real patch using `[:-1]`/`[-1:]` "
                   "would offer the blank-line marker (include_lines[-2]) to source-read "
                   "and reattach only the trailing comment marker — diverging from the gold "
                   "two-marker frame and parsing the blank-line marker as body, FAILING the "
                   "F2P marker-exclusion assertion. So it would NOT resolve.",
     "rationale": "off-by-one on the marker count. Rejection source: the licensed region is "
                  "take(n-2), not take(n-1), so the offer has no matching hook_offer_io "
                  "instance; and the pin needs hook(take(n-2)) ++ drop(n-2) while the rival "
                  "produces hook(take(n-1)) ++ drop(n-1), with the body clause "
                  "take(len-2)==hook(take(len-2)) failing too (uninterpreted hook => "
                  "unprovable). If it verified => SPEC-TOO-WEAK (marker count unpinned)."},
    {"id": "partial-domain-empty-body", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "correct whenever the body is non-empty (n > 2) but forwards VERBATIM "
                   "when the body is empty (n == 2, the two-markers-only include, which the "
                   "precondition len>=2 admits). A faithful real patch of this shape (skip "
                   "the source-read event for an empty include body) would NOT emit the "
                   "event for an empty included file, diverging from gold (which always "
                   "emits) — observable to a source-read handler that records every "
                   "docname, so it would NOT resolve.",
     "rationale": "partial-domain: pins only the n>2 sub-domain. Rejection source: on n==2 "
                  "the branch makes no offer, so it cannot hand back token(t_post) (the "
                  "token is reachable only through the licensed offer), and the pin "
                  "ToSeq(Result()) == transformed(ToSeq(lines)) needs hook(take(0)) ++ "
                  "drop(0) while the rival returns ToSeq(lines) with hook uninterpreted. If "
                  "it verified => SPEC-TOO-WEAK (empty-body sub-domain unpinned)."},
    {"id": "rival-extra-offer-full-lines", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_FULL,
     "refinement": "the gold computation VERBATIM plus a second dispatch showing the hook "
                   "the whole gathered sequence and discarding the result. Its faithful real "
                   "patch is the gold `_insert_input` with one extra "
                   "`events.emit('source-read', docname, [\"\\n\".join(include_lines)])` whose "
                   "return value is thrown away. Measured: that patch FAILS F2P "
                   "(test_include_source_read_event) — the second dispatch shows every "
                   "registered listener the marker-bearing text, and the test's listener "
                   "records what it was shown, so it records the wrong content. Same "
                   "forwarded sequence as gold, so every value clause holds: this is exactly "
                   "the verify-but-not-resolve shape the effect discipline exists to reject.",
     "rationale": "control-flow-effect: right value, extra effect. Rejection source: the "
                  "PERMISSION SYSTEM on the effect resource — the step holds one "
                  "hook_offer_io instance and the gold offer already spent it together with "
                  "token(t_pre), so the second emit_and_collect call has neither ('There "
                  "might be insufficient permission to access hook_offer_io(...)'). If it "
                  "verified => SPEC-TOO-WEAK (offer COUNT unpinned: a discarded dispatch is "
                  "invisible to every clause about the returned value)."},
    {"id": "rival-forge-place-second-offer", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGE,
     "refinement": "no faithful real patch corresponds to fabricating a licence; like "
                   "frame-mutate-lines this rival exists to test whether the resource the "
                   "spec rations can be minted by the implementation. If it verified, the "
                   "one-offer obligation would be decorative and the extra-dispatch patch "
                   "above (which does NOT resolve) would be admitted through this door.",
     "rationale": "resource forgery, the effect-side twin of the frame-mutation probe. "
                  "Rejection source: the PERMISSION SYSTEM — a freshly constructed Place "
                  "carries no token and no operation instance, and neither is foldable, so "
                  "token(p, 2) is not held ('There might be insufficient permission to "
                  "access token(p, 2)'). If it verified => SPEC-TOO-WEAK (the offer budget "
                  "could be minted at will)."},
    {"id": "rival-duplicate-offer", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DUP,
     "refinement": "shows the hook the correct region twice and forwards the second result. "
                   "Its faithful real patch dispatches 'source-read' twice on the same body "
                   "text; the real patched step dispatches exactly once per invocation "
                   "(conformance_check.py asserts the real closure's dispatch list is "
                   "one-element), and a listener that is not idempotent — a counter, an "
                   "accumulator, a listener that appends — observes the difference. So the "
                   "rival is not the specified behaviour even where the forwarded value "
                   "agrees.",
     "rationale": "duplicate effect, right value. Rejection source: the PERMISSION SYSTEM on "
                  "the effect resource (one licence, spent by the first offer). Both results "
                  "are hook(body), so NO value clause separates this from gold — it is the "
                  "purest test that the offer count is pinned. If it verified => "
                  "SPEC-TOO-WEAK."},
    {"id": "rival-alias-empty-body", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALIAS,
     "refinement": "at the empty-body boundary (n == 2) it offers the gathered list ITSELF "
                   "(body aliases the input, no markers held out) and returns what comes "
                   "back. Its faithful real patch offers the full `include_lines` — markers "
                   "included — for an empty included file, showing listeners the docutils "
                   "framing markers as authored content and forwarding the rewritten markers "
                   "to the parser. Diverges from gold on that sub-domain, so it would NOT "
                   "resolve.",
     "rationale": "boundary + aliasing: the input list is passed as the offered body at "
                  "n==2. Rejection source: the licensed region there is take(0) (the empty "
                  "sequence), so an offer of ToSeq(lines) has no matching hook_offer_io "
                  "instance; and the pin needs hook(empty) ++ lines while the rival produces "
                  "hook(lines). If it verified => SPEC-TOO-WEAK (offered region unpinned at "
                  "the boundary)."},
    {"id": "rival-vacuous-precondition", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_VACUITY,
     "refinement": "not a candidate patch: the control for the strengthened precondition "
                   "itself. The added conjunct is a RESOURCE (a token plus one operation "
                   "instance), and an infeasible resource precondition would let EVERY "
                   "implementation verify — the maximal spec weakness, and one no value "
                   "clause would reveal. Asserting False under the precondition is the "
                   "standard control: it must be rejected.",
     "rationale": "vacuity control. Rejection source: the assertion itself ('Assert might "
                  "fail. Assertion False might not hold'), which is only reportable if the "
                  "precondition is satisfiable. If it verified => SPEC-TOO-WEAK in the "
                  "strongest sense (precondition infeasible => the cell proves nothing)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real callee) — emit_and_collect wraps the REAL
# EventManager('source-read') + the line<->text round trip. apply_gold=True
# because the axiom describes the post-gold _insert_input behaviour.
# ===========================================================================

# (1) axiom-soundness for emit_and_collect. Drives the REAL
# sphinx.events.EventManager('source-read') through the patch's _insert_input
# text logic (byte-for-byte) and asserts the axiom's promise on the marker frame:
#   * the invocation offers the hook content EXACTLY ONCE (the effect the
#     hook_offer_io licence rations: one instance spent per call);
#   * the body offered to the event is EXACTLY "\n".join(lines[:-2]) (markers
#     excluded);
#   * the two framing markers are re-attached VERBATIM, in their original
#     positions, at the end (markers bypass the hook);
#   * under the identity hook the forwarded sequence reconstructs the input
#     (the line<->text round trip is the identity at line granularity);
#   * a rewriting hook's effect lands ONLY in the body region, never the markers
#     (so hook(body) replaces exactly the body region — the axiom's
#     ToSeq(Result())==hook(ToSeq(body)) decomposition).
# Fuzz boundary shapes (incl. the two F2P shapes + the issue's &REPLACE_ME; case)
# + randomized line sets. Any disagreement of the REAL dispatcher with the axiom
# on an in-domain (len>=2, non-raising listener) input => AXIOM-UNSOUND.
_AX_EMIT_SOUND = r'''
import random, sys
from sphinx.events import EventManager
from sphinx.util.osutil import os_path


class _FakeApp:
    pdb = False


def make_events(handler):
    ev = EventManager(_FakeApp())
    if "source-read" not in ev.events:
        ev.add("source-read")
    if handler is not None:
        ev.connect("source-read", handler, priority=500)
    return ev


def patched_insert_input(events, docname, include_lines):
    # byte-for-byte replica of the gold _insert_input text/marker logic.
    text = "\n".join(include_lines[:-2])
    arg = [text]
    events.emit("source-read", docname, arg)
    text = arg[0]
    return text.splitlines() + include_lines[-2:]


def check_one(lines):
    assert len(lines) >= 2
    body = lines[:-2]
    markers = lines[-2:]

    # one-offer + body-is-offered: record EVERY offer the invocation makes, then
    # assert there was exactly ONE and it showed exactly join(lines[:-2]).
    seen = []
    ev = make_events(lambda app, doc, src: seen.append(src[0]))
    fwd = patched_insert_input(ev, "index", list(lines))
    if len(seen) != 1:
        print("AXIOM-UNSOUND: offers per invocation != 1:", len(seen)); sys.exit(1)
    if seen[0] != "\n".join(body):
        print("AXIOM-UNSOUND: offered text != join(body):", repr(seen[0]),
              "vs", repr("\n".join(body))); sys.exit(1)

    # marker reattachment: the two framing markers returned verbatim, last.
    if fwd[-2:] != markers:
        print("AXIOM-UNSOUND: markers not preserved verbatim:", fwd[-2:], "vs", markers)
        sys.exit(1)

    # round-trip identity under the identity hook (no listener rewrite).
    if "\n".join(body).splitlines() == body and fwd != list(lines):
        print("AXIOM-UNSOUND: identity round trip broke:", fwd, "vs", lines); sys.exit(1)


def check_rewriting(lines, needle, repl):
    body = lines[:-2]
    markers = lines[-2:]
    offers = []

    def rewrite(app, doc, src):
        offers.append(src[0])
        src.__setitem__(0, src[0].replace(needle, repl))

    ev = make_events(rewrite)
    fwd = patched_insert_input(ev, "index", list(lines))
    if len(offers) != 1:
        print("AXIOM-UNSOUND: offers per invocation != 1:", len(offers)); sys.exit(1)
    # hook effect lands only in the body region, never the markers.
    if fwd[-2:] != markers:
        print("AXIOM-UNSOUND: rewrite leaked into markers:", fwd[-2:], "vs", markers)
        sys.exit(1)
    expected_body = "\n".join(body).replace(needle, repl).splitlines()
    if fwd[:-2] != expected_body:
        print("AXIOM-UNSOUND: rewritten body region wrong:", fwd[:-2], "vs", expected_body)
        sys.exit(1)


marker_a = ""
marker_b = '.. end of inclusion from "foo.rst"'
boundary = [
    ["The #magical foo.", marker_a, marker_b],          # F2P nested-include shape
    ["", "Baz was here.", marker_a, marker_b],          # F2P start-line shape
    ["a", "b", "c", marker_a, marker_b],
    ["only", "two"],                                    # exactly the two markers (empty body)
    ["one body line", marker_a, marker_b],
    ["x", "", "y", "", "z", marker_a, marker_b],        # interior blank lines
    ["&REPLACE_ME;", "text", marker_a, marker_b],       # issue's substitution case
    ["line with spaces   ", "\ttabbed", marker_a, marker_b],
]
for L in boundary:
    check_one(L)
check_rewriting(["The #magical foo.", marker_a, marker_b], "#magical", "amazing")
check_rewriting(["&REPLACE_ME;", "more", marker_a, marker_b], "&REPLACE_ME;", "REPLACED")

rng = random.Random(11510)
words = ["foo", "bar", "baz", "REPLACE_ME", "#magical", "qux", "", "  ",
         "&amp;", "section", "===", "---", "a b c", "1", "2"]
for _ in range(20000):
    nbody = rng.randint(0, 8)
    bd = [rng.choice(words) for _ in range(nbody)]
    L = bd + [rng.choice(["", "  ", "x"]),
              '.. end of inclusion from "%s.rst"' % rng.choice(words or ["d"])]
    check_one(L)
    if bd:
        check_rewriting(L, rng.choice(["foo", "REPLACE_ME", "#magical", "z"]), "REPLACED")

# the docname routing the helper uses (path2doc(os_path(path))): os_path is the
# identity on '/'-separated paths on POSIX; exercise the real callee.
assert os_path("baz/baz.rst").endswith("baz.rst")
print("emit_and_collect SOUND: real EventManager('source-read') marker frame holds "
      "over %d boundary + 20000 fuzz line sets (ONE offer per invocation, "
      "body-offered, markers verbatim, round-trip identity, hook propagation "
      "body-only)." % len(boundary))
sys.exit(0)
'''

# (2) axiom-containment for emit_and_collect. The model reaches emit_and_collect
# with EXACTLY one argument: `body = lines[:n-2]`, the markers-excluded prefix of
# a line sequence with len>=2. So the reachable callee-inputs are precisely the
# line sequences `lines[:-2]` for any include with at least the two framing
# markers — i.e. any list of zero or more body lines. The axiom's Requires is
# `Acc(list_pred(body),1/2)` (a read-only list of ints, no length/value bound), so
# EVERY reachable body lies in the domain (including the empty body when n==2).
# This probe asserts the real callee (the patch's text logic) accepts every
# reachable body shape (0..k body lines) without error and that the empty-body
# boundary (n==2) is handled. Covering more (any list) than the caller reaches is
# SOUND, not a defect.
_AX_CONTAINMENT = r'''
import sys
from sphinx.events import EventManager


class _FakeApp:
    pdb = False


def make_events():
    ev = EventManager(_FakeApp())
    if "source-read" not in ev.events:
        ev.add("source-read")
    ev.connect("source-read", lambda app, doc, src: None, priority=500)
    return ev


def offer(events, body_lines):
    # the patch offers exactly "\n".join(include_lines[:-2]); body_lines IS that
    # markers-excluded prefix. Accept any number of body lines (incl. zero).
    text = "\n".join(body_lines)
    arg = [text]
    events.emit("source-read", "index", arg)
    return arg[0]


# the model reaches emit_and_collect only with body = lines[:n-2]; for len>=2
# inputs that is a body of 0..k lines. Enumerate the reachable body shapes.
ev = make_events()
reachable_lengths = list(range(0, 12))  # 0 (empty body, n==2) .. 11
for k in reachable_lengths:
    body = ["line%d" % i for i in range(k)]
    out = offer(ev, body)   # must accept without error
    if not isinstance(out, str):
        print("containment: real callee returned non-str for body len", k); sys.exit(1)

# the axiom's Requires (Acc(list_pred(body),1/2)) places NO length/value bound,
# so every reachable body (any markers-excluded prefix, incl. empty) is covered.
# There is no reachable callee-input outside the axiom's domain.
print("containment OK: model reaches emit_and_collect only with body = lines[:-2] "
      "(0..k body lines, incl. empty when n==2); axiom domain Acc(list_pred,1/2) "
      "covers every reachable body — no caller-reachable input outside the domain.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-emit-sound", "axiom": "emit_and_collect", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_EMIT_SOUND,
     "rationale": "the REAL EventManager('source-read') driven through the patch's "
                  "_insert_input text logic must satisfy the emit_and_collect axiom's marker "
                  "frame on every in-domain (len>=2, non-raising) input: exactly ONE offer "
                  "per invocation (the axiom spends exactly one hook_offer_io licence), body "
                  "offered == join(lines[:-2]), markers reattached verbatim, identity round "
                  "trip, hook effect body-only. Any disagreement => AXIOM-UNSOUND."},
    {"id": "ax-emit-containment", "axiom": "emit_and_collect", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "the model reaches emit_and_collect only with body = lines[:n-2] (a "
                  "0..k-line markers-excluded prefix), and only once, at the place its one "
                  "hook_offer_io licence names. The axiom Requires Acc(list_pred,1/2) plus "
                  "that licence, placing no length/value bound, so every reachable body "
                  "(incl. the empty body at n==2) lies in the domain, and the effect the "
                  "real callee performs per call is the single dispatch the licence buys "
                  "(counted by ax-emit-sound). A reachable callee-input outside the axiom "
                  "domain => AXIOM-TOO-WEAK-FOR-CALLER."},
]
