"""properties.py — G-PBT falsification battery for django__django-13551 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct makeHashInput`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  makeHashInput (u : UserState) (timestamp : String) return (out : String)
    ensures out = hashInput u timestamp

The method builds the single-use token-invalidation input from the user's
durable state and the request timestamp. The pure region pins the whole outcome
as a total function of the method's own inputs:

  hashInput u timestamp
    = u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u
  emailValue u = u.emailRaw.getD ""

So the sole ensures pins ONE structural clause with several independent parts:

  * (ORD) the EXACT in-order 5-part concatenation — primary key, password,
          last-login string, timestamp, then the email contribution LAST. A
          rival that permutes the parts violates the ensures wherever two
          permuted parts differ. Probed at BOTH the leading pair
          (weak-reorder-pk-password) and the middle pair
          (weak-reorder-login-timestamp), so no region of the ordering is left
          unattacked.
  NOTE (audit): the ORD clause is pinned up to GROUPING only — ``++`` is
          associative, so the SAME string admits differently-parenthesised terms.
          The frozen ``a ++ b ++ c ++ d ++ e`` parses left-associated; a
          right-associated impl is a different term that is NOT definitionally
          equal to it and needs ``String.append_assoc`` as a real rewrite. That
          the spec still accepts it is the pos-right-assoc-group control.

  * (EMAIL) the trailing part is ``emailValue u`` — the stored address when the
          account has one (``some e ↦ e``) and the empty string when it does not
          (``none ↦ ""``). Folding the address in is the discriminating fix: two
          states differing only in the address produce different inputs, because
          the address is appended after a common prefix (concatenation is
          left-cancellative). A rival that (a) drops this part, (b) truncates it,
          or (c) contributes a non-empty string when the account has no address
          violates the ensures.

Every INPUT binder of ``hashInput`` must hold for EVERY value:
  * ``u.pk`` / ``u.password`` — the leading durable parts; the ORD clause pins
    their order (the reorder rival abuses exactly these two).
  * ``u.loginTimestamp`` / ``timestamp`` — the middle parts, carried through
    unchanged; varied across the reject witnesses so a rival mishandling either
    would be caught.
  * ``u.emailRaw`` — drives ``emailValue`` and the whole EMAIL clause; the three
    EMAIL rivals attack its present / absent branches.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):

  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    MANDATORY frame-mutation rivals keep the gold body verbatim then WRITE back
    into a read-only input (the primary-key sequence, the optional address) held
    only at a fractional heap permission, and are rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every parameter
    is an immutable value, this bundle declares no ``mut`` binder, there is no
    heap and no aliasing. There is no read-only input to overwrite and no
    permission system to trip, so the class is vacuous. No substitute is
    fabricated.

  * TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``hashInput u timestamp``; ``hashInput`` / ``emailValue`` are concrete
    ``def``s in the ``pure`` region computing the input from the method's own
    arguments (the ``axioms`` region is empty; there is no opaque answer key to
    echo). The unique satisfier IS the grounded concatenation, so there is no
    wrong echo to build; the honest controls are the cheapest faithful reshapes
    (the ``pos-*`` cases).

  * PARTIAL-DOMAIN / VALUE — heavily exercised. Every EMAIL rival is correct on a
    sub-domain and wrong on its complement: drop-email is correct only when the
    account has no address; truncated-tail is correct only on the empty address;
    none-email-sentinel is correct only when the account HAS an address. The
    reorder rival is correct whenever the two leading parts happen to coincide
    and wrong otherwise.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide`` on concrete ``String``
inputs. Each reject rival carries a machine-checked refutation ``witness`` — a
Velvet tester statement ``makeHashInputTester <u> <timestamp> = false`` at ONE
concrete input, checked in a file whose ``prove_correct`` block has been stripped
so no tactic script can mask the verdict. No ``axiom`` / ``sorry`` /
``native_decide`` is involved; the return carrier is ``String`` (already has
``DecidableEq``), so the tester derivation needs no extra instance. Both halves
were checked out-of-band with ``scripts/lean_verify.sh``: every witness
ELABORATES against its rival (exit 0) and FAILS (``decide`` proves the
proposition false, exit 1) against the frozen solution, so each rejection is a
genuine spec refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; ``hashInput`` / ``emailValue`` are I/R-ops (modeled directly),
refinement-checked by ``conformance_check.py`` (G-CONF), not axiomatized.
Nothing in the proof rests on an axiom, and this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13551"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end` (marker lines included). Every rival and
# reshape edits ONLY this block (and, for reshapes/admissibility, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    -- The email folded into the input: the stored address when present,\n"
    "    -- otherwise the empty string (an account with no/blank email).\n"
    '    let email := u.emailRaw.getD ""\n'
    "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); reject rivals leave it as-is
# (the rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct makeHashInput by\n  loom_solve\n  simp [hashInput, emailValue]"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `makeHashInputTester <u> <timestamp> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. The method has
# ---- NO precondition, and the `String` return carrier is already decidable, so
# ---- the tester derives with no extra instance. Checked in a file whose
# ---- `prove_correct` block has been stripped.
_TESTER = (
    "extract_program_for makeHashInput\n"
    "prove_precondition_decidable_for makeHashInput\n"
    "prove_postcondition_decidable_for makeHashInput\n"
    "derive_tester_for makeHashInput\n\n"
)


def _user(pk, password, login, email):
    """A concrete `UserState` literal. `email` is None (`emailRaw := none`) or a
    string (`emailRaw := some "..."`)."""
    e = "none" if email is None else f'some "{email}"'
    return ('{ pk := "%s", password := "%s", loginTimestamp := "%s", '
            "emailRaw := %s }" % (pk, password, login, e))


def _witness(user, timestamp):
    return (_TESTER +
            f'example : makeHashInputTester {user} "{timestamp}" = false := by\n'
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the concatenated value identical and only
    # reshapes the executable surface; the reproof stays close to the frozen
    # `loom_solve; simp` script.
    # =====================================================================
    {
        "id": "pos-match-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the email contribution with an explicit `match` on the
        # optional address instead of `getD ""`. Definitionally the same value on
        # both branches (`some e ↦ e`, `none ↦ ""`), so `out = hashInput u
        # timestamp` still holds. The reproof case-splits the option so both arms
        # reduce to the frozen `emailValue`.
        "module": _impl_reproved(
            "    let email := match u.emailRaw with\n"
            "      | some e => e\n"
            '      | none => ""\n'
            "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email",
            "prove_correct makeHashInput by\n"
            "  loom_solve\n"
            "  cases h : u.emailRaw <;> simp [hashInput, emailValue, h]"),
        "rationale": "computing the email contribution by an explicit match on the "
                     "optional address (`some e ↦ e`, `none ↦ \"\"`) is definitionally "
                     "`emailValue u`, so the assembled input equals `hashInput u "
                     "timestamp` on the whole domain; a correct reshape must verify, "
                     "else SPEC-TOO-STRONG on how the email branch is spelled. "
                     "Mirrors the sibling's control-flow-reshape positive.",
    },
    {
        "id": "pos-right-assoc-group",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: assemble the five parts RIGHT-associated. `++` is notated
        # left-associative in Lean, so the frozen `a ++ b ++ c ++ d ++ e` parses
        # as `(((a ++ b) ++ c) ++ d) ++ e` and this rival's
        # `a ++ (b ++ (c ++ (d ++ e)))` is a GENUINELY different term — not the
        # same parse tree, and NOT definitionally equal (checked: `rfl` fails on
        # the two sides, exit 1). Equality needs associativity of `String.append`
        # as a real rewrite, so the reproof adds `String.append_assoc`; the frozen
        # `simp [hashInput, emailValue]` alone does NOT close it (checked, exit 1
        # with the two groupings as unsolved goals). That is what makes this a
        # load-bearing grouping control rather than a re-spelling.
        #
        # It REPLACES an earlier `pos-prefix-bind` case that bound the four
        # leading parts to a local and returned `pre ++ email`. That case's
        # rationale claimed associativity of `++` was what made it correct, but
        # `(a ++ b ++ c ++ d) ++ e` is the frozen term SYNTACTICALLY (left
        # associativity again) — `rfl` closes the two sides directly (checked,
        # exit 0). Introducing a `let` for a sub-expression is a re-spelling the
        # elaborator erases, so the case exercised no grouping obligation at all
        # and its stated reason was false. Re-aimed at the grouping the spec can
        # actually be too strong about.
        "module": _impl_reproved(
            '    let email := u.emailRaw.getD ""\n'
            "    return u.pk ++ (u.password ++ (u.loginTimestamp ++ (timestamp ++ email)))",
            "prove_correct makeHashInput by\n"
            "  loom_solve\n"
            "  simp [hashInput, emailValue, String.append_assoc]"),
        "rationale": "assembling the five parts right-associated produces the same "
                     "STRING as the frozen left-associated concatenation but a "
                     "different TERM: the two are not definitionally equal (`rfl` "
                     "fails) and the frozen tactic script does not close the "
                     "reshaped goal, so associativity of `String.append` is a real "
                     "rewrite the reproof must supply. A faithful correct impl that "
                     "merely groups the concatenation differently must still verify, "
                     "else the spec is SPEC-TOO-STRONG on grouping. Carries the "
                     "sibling's local-rebind positive's SPIRIT (structurally "
                     "different, behaviourally identical) at a point where the "
                     "restructuring is not erased by the elaborator.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the EMAIL clause
    # is DEGENERATE at the interesting point — a fold that never actually let the
    # address change the input would read like a live one. This case discharges
    # an in-region assert pinning that two states differing ONLY in the email
    # (present vs absent, every other part fixed) produce DIFFERENT inputs — i.e.
    # the folded email genuinely forks the outcome, which is exactly the property
    # the F2P relies on. The rest of the impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned only to also close the
    # assert.
    # =====================================================================
    {
        "id": "admiss-email-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            '      (hashInput { pk := "1", password := "p", loginTimestamp := "", '
            'emailRaw := some "A" } "t"\n'
            '         ≠ hashInput { pk := "1", password := "p", loginTimestamp := "", '
            'emailRaw := none } "t"))\n'
            '    let email := u.emailRaw.getD ""\n'
            "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email",
            "prove_correct makeHashInput by\n"
            "  loom_solve <;> simp [hashInput, emailValue] <;> decide"),
        "rationale": "the EMAIL clause is non-degenerate at an F2P-shaped point: "
                     "two states identical except for the email (`some \"A\"` vs "
                     "`none`, all other parts fixed) map to DIFFERENT inputs, so "
                     "folding the address in genuinely changes the outcome — the "
                     "behaviour the F2P exercises. The in-region assert must "
                     "discharge (else the fold would be vacuous / the obligation "
                     "degenerate); the impl is kept verbatim so the ensures still "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-drop-email",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, the bug-delta / pre-patch: assemble ONLY the four
        # leading parts and never fold the email in. Correct on every account
        # with no address; wrong whenever the account HAS an address.
        "module": _impl(
            "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp"),
        "refinement": "this is the pre-patch behaviour: the input omits the email "
                      "contribution entirely. The assembled input is then "
                      "invariant under an address change, so an outstanding "
                      "single-use token minted before the change still matches "
                      "afterwards — precisely the defect the fix removes. The F2P "
                      "asserts the token IS invalidated once the address changes, "
                      "so the faithful real patch (no email folded in) FAILS the "
                      "F2P and does NOT resolve (= the pre-patch skeleton, G-DIFF).",
        "rationale": "REJECT from `out = hashInput u timestamp` on the EMAIL "
                     "clause: the post-image appends `emailValue u`, but the rival "
                     "omits it, so on any account WITH an address (`emailRaw = some "
                     "e`, `e` non-empty) the two inputs differ by the trailing "
                     "`e`. Refuted at a user whose address is present (`some "
                     "\"A\"`) — the sub-domain where this rival is wrong, and the "
                     "one the sentinel/absent-address witnesses do not cover.",
        "witness": _witness(_user("1", "p", "L", "A"), "t"),
    },
    {
        "id": "weak-reorder-pk-password",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival: swap the two leading parts (password before primary key)
        # while still appending the email last. The multiset of characters can
        # match gold, but the ensures pins the EXACT in-order concatenation, so
        # any input where the two parts differ is refuted.
        "module": _impl(
            '    let email := u.emailRaw.getD ""\n'
            "    return u.password ++ u.pk ++ u.loginTimestamp ++ timestamp ++ email"),
        "refinement": "swapping the two leading parts assembles them in the wrong "
                      "order. For any user whose primary key and password differ — "
                      "the overwhelming common case — the assembled input differs "
                      "from the intended one, so the derived single-use token "
                      "differs and the token round-trip / make-token behaviour "
                      "diverges from the reference. It fails the token generation "
                      "and check behaviour the P2P tests pin, so the faithful real "
                      "patch does NOT resolve.",
        "rationale": "REJECT from `out = hashInput u timestamp` on the ORD clause: "
                     "the post-image is `pk ++ password ++ …` but the rival emits "
                     "`password ++ pk ++ …`; wherever the two parts differ the "
                     "strings differ. Refuted at a user with `pk = \"1\"`, "
                     "`password = \"2\"` (and NO address, `emailRaw = none`) — this "
                     "varies the `u.pk` / `u.password` binders AND the `emailRaw` "
                     "binder (absent here, present in weak-drop-email) so the two "
                     "rivals carry distinct separating inputs.",
        "witness": _witness(_user("1", "2", "c", None), "d"),
    },
    {
        "id": "weak-none-email-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the ABSENT-email branch: contribute a non-empty
        # sentinel for accounts with NO address (`getD "X"`) instead of the empty
        # string. Correct on every account that HAS an address; wrong when the
        # account has none.
        "module": _impl(
            '    let email := u.emailRaw.getD "X"\n'
            "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email"),
        "refinement": "contributing a fixed non-empty sentinel for accounts with "
                      "no address makes the assembled input differ from the "
                      "reference for every address-less account (whose contribution "
                      "must be empty). Such accounts' single-use tokens would no "
                      "longer round-trip against the reference construction, so the "
                      "token generation / check behaviour the P2P tests pin fails; "
                      "the faithful real patch does NOT resolve.",
        "rationale": "REJECT from `out = hashInput u timestamp` on the EMAIL "
                     "clause's ABSENT branch: `emailValue` maps `none` to `\"\"`, so "
                     "the input must end in the four leading parts with nothing "
                     "appended, but the rival appends `\"X\"`. Refuted at a user "
                     "with NO address (`emailRaw = none`) — the branch weak-drop-"
                     "email (present address) and weak-truncated-tail (present "
                     "address) do not exercise; also varies `pk`/`timestamp`.",
        "witness": _witness(_user("9", "q", "", None), "z"),
    },
    {
        "id": "weak-reorder-login-timestamp",
        "kind": "uniqueness",
        "expect": "reject",
        # ORDER rival on the two MIDDLE parts: emit the request timestamp BEFORE
        # the last-login string. Added by audit: the ORD clause was previously
        # attacked only on the two LEADING parts, so a rival that permuted the
        # middle of the concatenation was unprobed even though the ensures pins
        # all five positions. Correct only when the two middle parts coincide.
        "module": _impl(
            '    let email := u.emailRaw.getD ""\n'
            "    return u.pk ++ u.password ++ timestamp ++ u.loginTimestamp ++ email"),
        "refinement": "this assembles the last-login string and the request "
                      "timestamp in the wrong order. For any account whose "
                      "last-login string differs from the request timestamp — the "
                      "normal case, since the two are distinct instants — the "
                      "assembled input differs from the intended one, so the "
                      "derived single-use token differs and the token "
                      "generation / round-trip behaviour the P2P tests pin "
                      "diverges from the reference. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = hashInput u timestamp` on the ORD clause "
                     "at the MIDDLE positions: the post-image is `… ++ "
                     "loginTimestamp ++ timestamp ++ …` but the rival emits `… ++ "
                     "timestamp ++ loginTimestamp ++ …`; wherever the two differ "
                     "the strings differ. Refuted at a user with `loginTimestamp "
                     "= \"L\"` and `timestamp = \"t\"`. Complements weak-reorder-"
                     "pk-password, which attacks ORD only at the two LEADING "
                     "positions and so leaves the middle of the concatenation "
                     "unprobed.",
        "witness": _witness(_user("1", "p", "L", "A"), "t"),
    },
    {
        "id": "weak-truncated-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, off-by-one tail: fold the email in but DROP its last
        # character. Correct only on the empty address; wrong on every non-empty
        # address, one character short at the tail.
        "module": _impl(
            '    let email := (u.emailRaw.getD "").dropRight 1\n'
            "    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email"),
        "refinement": "dropping the final character of the address from the input "
                      "means two addresses sharing a prefix collide, and a normal "
                      "address change generally leaves the truncated tail differing "
                      "from the reference. The assembled input no longer matches "
                      "the reference construction on any account with a non-empty "
                      "address, so the token behaviour the F2P / P2P tests pin "
                      "diverges; the faithful real patch does NOT resolve.",
        "rationale": "REJECT from `out = hashInput u timestamp` on the EMAIL "
                     "clause: the trailing part must be the WHOLE `emailValue u`, "
                     "but the rival appends it with its last character removed, so "
                     "on any account with a non-empty address the inputs differ by "
                     "that character. Refuted at a user with a two-character "
                     "address (`some \"AB\"`) — distinguishes it from weak-drop-"
                     "email (which is wrong even at a one-character address) and "
                     "varies `loginTimestamp`/`timestamp`.",
        "witness": _witness(_user("1", "p", "k", "AB"), "w"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness — two of which are the mandatory
# frame-mutation rivals). The sibling has NO divergence/non-termination case.
# The sibling models the same fingerprint over a rich `user` whose fields carry
# fractional heap permissions, building the concatenation with verified `while`
# loops over `List[int]` code points; this backend models the same input
# STRAIGHT-LINE over `String`, with the concatenation as the pure `hashInput` and
# the email contribution as `emailValue`. The concatenation surface carries
# across intact; the permission surface, the loops and the invariants do not
# exist here.
#
#   sibling case                  -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-empty-addr-guard  -> pos-match-fold                PORTED (reshaped
#                                                                   straight-line)
#   pos-control-rename-reshape    -> pos-right-assoc-group         PORTED (reshaped;
#                                                                   RE-AIMED by audit)
#   admiss-self-call              -> admiss-email-nondegenerate    RE-AIMED
#   frame-mutate-pk               -> (none)                        VACUOUS
#   frame-mutate-address          -> (none)                        VACUOUS
#   weak-drop-email               -> weak-drop-email               PORTED
#   weak-email-truncated-tail     -> weak-truncated-tail           PORTED
#   weak-reorder-pk-password      -> weak-reorder-pk-password      PORTED
#   weak-none-address-sentinel    -> weak-none-email-sentinel      PORTED
#   (no sibling case)             -> weak-reorder-login-timestamp  ADDED by audit
#
# 6 ported, 1 re-aimed, 2 vacuous, 1 added. No divergence case exists in the
# sibling, so none is ported and none is fabricated.
#
# AUDIT REPAIRS (independent re-derivation of the port, machine-checked):
#   * pos-prefix-bind was DROPPED and replaced by pos-right-assoc-group. It bound
#     the four leading parts to a local and returned `pre ++ email`, claiming
#     associativity of `++` as the reason it was still correct. That reason is
#     FALSE: `++` is left-associative, so `(a ++ b ++ c ++ d) ++ e` IS the frozen
#     term syntactically — `rfl` closes the two sides (checked, exit 0) — and a
#     `let` binding a sub-expression is erased by the elaborator. The case
#     verified honestly but exercised no grouping obligation, and the frozen proof
#     closed it UNCHANGED, which is the tell. The replacement groups
#     right-associated: not definitionally equal (`rfl` fails, exit 1), not closed
#     by the frozen script (exit 1), closed by adding `String.append_assoc`
#     (exit 0) — a grouping control that can actually detect SPEC-TOO-STRONG.
#   * weak-reorder-login-timestamp was ADDED. The ORD clause pins all five
#     positions but was probed only at the two LEADING parts, leaving the middle
#     pair (last-login string vs request timestamp) unattacked. Built and checked
#     out-of-band: the rival does not verify, its witness elaborates against the
#     rival (exit 0) and FAILS on gold with `decide` proving the tester
#     proposition false at the named input (exit 1) — a semantic refutation.
#
# VACUOUS (frame-mutate-pk / frame-mutate-address): the sibling's two MANDATORY
#   frame-mutation rivals keep the gold body verbatim then write back into a
#   read-only input (the primary-key sequence, the optional address) held only at
#   half permission, and must be rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent: every parameter is an immutable value,
#   the method declares no `mut` binder, there is no heap and no aliasing. There
#   is no read-only input to overwrite and no permission system to trip, so the
#   class is vacuous. No substitute is fabricated.
# RE-AIMED (admissibility): the sibling's self-call probe establishes that the
#   fractional-permission precondition admits a normal F2P-shaped input. This
#   backend's method has NO precondition and no permission surface, so that probe
#   is degenerate (every input is in-domain). It is re-aimed at the residual
#   total-domain risk — that the folded email is DEGENERATE at the interesting
#   point — via an in-region assert that two states differing only in the email
#   (present vs absent) map to DIFFERENT inputs, so the fold genuinely forks the
#   outcome (the F2P property).
# PORTED-RESHAPED (pos-match-fold / pos-right-assoc-group): the sibling's two
#   positive controls reshape the executable surface (an explicit non-empty guard
#   on the address loop; a loop-index rename) while keeping every invariant and
#   the concatenated value. This backend's frozen impl is straight-line (no loop),
#   so the exact loop reshapes do not exist; the reshape SPIRIT — "structurally
#   different, behaviourally identical" — is carried by (a) computing the email
#   contribution with an explicit `match` instead of `getD`, and (b) grouping the
#   concatenation right-associated instead of left. BOTH are real reshapes on this
#   carrier, each confirmed by the same two checks: the reshaped term is NOT
#   definitionally equal to the frozen one (`rfl` fails, exit 1) and the FROZEN
#   tactic script does not close it (exit 1), so each genuinely re-proves the
#   obligation for a new impl shape rather than re-spelling it. Reproofs stay a
#   `loom_solve` + `simp`/`cases` away (`cases h : u.emailRaw` for the match fold,
#   `String.append_assoc` for the grouping).
#
# TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the input binders of the
#   sole ensures (5 reject cases; 4 distinct input points, since the added
#   middle-reorder rival is refuted at the same point as weak-drop-email — the
#   two rivals differ in WHICH clause fails there, not in the point):
#     u.pk            — "1" / "1" / "9" / "1" / "1"      (varied: 1 vs 9)
#     u.password      — "p" / "2" / "q" / "p" / "p"      (varied)
#     u.loginTimestamp— "L" / "c" / ""  / "k" / "L"      (varied, incl. empty)
#     timestamp       — "t" / "d" / "z" / "w" / "t"      (varied)
#     u.emailRaw      — some "A" / none / none / some "AB" / some "A"
#                                                   (present AND absent)
#   Every independent part of the post-image is attacked: the ORD clause at BOTH
#   the leading pair (weak-reorder-pk-password) and the middle pair
#   (weak-reorder-login-timestamp), and the EMAIL clause on all three of its
#   failure modes — dropped (weak-drop-email), non-empty-on-absent
#   (weak-none-email-sentinel), and truncated (weak-truncated-tail). No binder is
#   held fixed across the whole witness set, so a rival mishandling any single
#   binder would be caught.
#
# AUDIT SPEC-TOO-WEAK PROBES (attack D) — NEW wrong impls beyond the shipped
#   rivals, built and run against the frozen spec out-of-band. NONE verified;
#   each was rejected AND carried a witness that elaborated against it (exit 0)
#   while `decide` proved the tester proposition FALSE on gold (exit 1):
#     * drop the last-login part entirely (4-part concatenation, login omitted);
#     * fold the email contribution in TWICE (`… ++ email ++ email`);
#     * fold the email in FIRST rather than last (ORD on the email position);
#     * map a PRESENT-but-empty address to a non-empty sentinel while keeping the
#       absent branch empty — the near-miss the `Option`/`getD` carrier makes
#       reachable, since `some ""` and `none` are DISTINCT here even though the
#       repo's `or ''` collapses them.
#   No spec hole was found: the sole ensures pins the outcome as a total function
#   of the method's own inputs, so it admits exactly one behaviour.
#
# AUDIT SPEC-TOO-STRONG PROBES (attack E) — NEW correct reshapes, all of which
#   VERIFY once the elided tactic body is retuned (so no soundness hole):
#     * return the pure oracle directly (`return hashInput u timestamp`) —
#       `loom_solve` alone closes it;
#     * right-associated grouping — needs `String.append_assoc` (now SHIPPED as
#       pos-right-assoc-group);
#     * a control-flow SPLIT with one `return` per option branch — closed by
#       `loom_solve <;> simp_all [hashInput, emailValue]`;
#     * staged accumulation through three intermediate locals — closed by the
#       FROZEN script unchanged (which is why it is not shipped as a control: it
#       is a re-spelling the elaborator erases, the same defect the dropped
#       pos-prefix-bind had).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (`hashInput` / `emailValue` are I/R-ops
# checked by G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
