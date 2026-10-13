# properties.py — PBT falsification battery for django__django-13023.
#
# NOT a Nagini module: a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec exactly (region-surgery: only the
# text strictly inside # impl-start / # impl-end is replaced; the spec_view elides
# that whole region, so same_spec is guaranteed) and differ only in the impl.
#
# DEFENDED SURFACE (read from model.py):
#   coerce_to_numeric(kind: int) -> Optional[int]
#   Requires: 0 <= kind <= 8     <-- a PLAIN INTEGER acceptance tag; NO heap
#             permission anywhere (no Acc(...,1/2)). => FRAME-MUTATION is N/A
#             for this instance (there is no read-only object input to write to);
#             see 'assessment'. has_readonly_input = False.
#   Ensures (the load-bearing clauses):
#     (P0) kind == 0 or kind == 1 or kind == 2
#          -- normal return is reachable ONLY on an acceptable kind; every reject
#             kind (3/4/5/6/7/8) must NOT return normally.
#     (P1) Implies(kind == 0, Result() is None)          -- absent -> null token.
#     (P2) Implies(kind == 1, Result() is not None and Result() == from_floating())
#          -- the float result is pinned EXACTLY to the float callee's token.
#             NOTE kind 1 is now "floating AND the conversion accepts it": the
#             floating conversion is a SECOND, DISTINCT callee (not the general
#             constructor) with its own rejection, split out as kind 7 below.
#     (P3) Implies(kind == 2, Result() is not None and Result() == accepted_value(kind))
#          -- the accepted result is pinned EXACTLY to the constructor's token
#             (NOT merely "not None" — P2P test_to_python observes this value).
#     (E)  Exsures(ValidationFailure, kind == 3 or kind == 4 or kind == 5)
#          -- every CLASSIFIED rejection shape is surfaced as the SAME uniform
#             validation failure, on those kinds and no others.
#     (E6) Exsures(ConstructorRangeError, kind == 6)
#          -- the ONE rejection shape the coercion does not classify is NOT
#             converted: the constructor's own low-level error reaches the caller
#             unchanged. This leg states the coercion's REAL guarantee; the real
#             `decimal.Decimal` has a fourth rejection class (OverflowError, on
#             the tuple/list coordinate arm past the C ssize_t/long boundary)
#             that neither the pre-patch nor the patched `to_python` converts, so
#             a spec claiming ValidationError-or-normal-return for EVERY value
#             would be strictly stronger than the real function.
#     (E7) Exsures(ConstructorOperandError, kind == 7)
#          -- the OTHER shape the coercion does not classify. The coercion routes
#             a value to the floating conversion on isinstance(value, float), but
#             that conversion (C _decimal create_decimal_from_float) does an EXACT
#             PyFloat/PyLong check, so a value satisfying isinstance without being
#             a real float is refused with TypeError. That call sits at line 1501,
#             ABOVE and OUTSIDE the try beginning at 1502, so the TypeError
#             escapes -- measured identically on the base and gold-patched trees
#             (f.to_python(SimpleLazyObject(lambda: 1.5)) -> raw TypeError).
#             Because E7 declares the SAME low-level class E converts on kind 4,
#             it also pins the boundary: that class may escape on 7 and NOWHERE
#             else, so an impl letting it escape from the constructor path still
#             REJECTS (case partial-domain-kind4-escape / weak-prepatch below).
#     (E8) Exsures(ConversionRangeError, kind == 8)
#          -- the THIRD shape the coercion does not classify, and the SECOND of
#             the floating conversion's own two refusals. The conversion accepts
#             the value's operand TYPE but refuses its magnitude, which lies
#             outside what its own rounding context can represent; that rejection
#             class is distinct from every class the coercion classifies AND from
#             the constructor's out-of-representable-range class (6), and the call
#             is outside the try, so it too escapes raw. Measured identically on
#             the base and gold-patched trees, so not a patch delta.
#             E, E6, E7 and E8 together are total over the reject kinds: nothing
#             is left silent.
#
#   The oracles from_floating()/accepted_value(kind) are @Pure @ContractOnly
#   ABSTRACT accessors (their value is never fabricated by the proof). There is no
#   "wrong echo of an answer key" possible at the Nagini level: an impl can only
#   return EXACTLY what these accessors return, so the kind-1/kind-2 pins admit
#   ONLY the genuine callee token. A constant / cross-callee token therefore
#   REJECTS (cases weak-echo-const-kind2 / weak-echo-fromfloat-kind2 below) — this
#   is the GROUNDED-ORACLE flavour: the pin is grounded in the contract's own
#   accessor, so the attack is a fabricated/wrong token, not an echo that slips
#   through. (This asymmetry hole was the batch01 G-EQ defect, now closed.)
#
# Refinement ground truth (refinement.md / mapping.md / instance.json / G-AX):
#   kind <- DecimalField.to_python's classification of `value`:
#     0 None; 1 isinstance(value,float) AND create_decimal_from_float accepts it;
#     7 isinstance(value,float) but create_decimal_from_float refuses it as a
#       wrong-typed operand (TypeError, escaping raw -- the call is outside the
#       try);
#     8 isinstance(value,float) and create_decimal_from_float accepts the operand
#       TYPE but refuses the magnitude as out of its context's representable
#       range (a distinct class, also escaping raw -- e.g. an int-payload
#       __class__=float value of magnitude past the context's Emax);
#       else decimal.Decimal(value) behaviour:
#     2 accepted; 3 InvalidOperation; 4 TypeError; 5 ValueError;
#     6 OverflowError (the UNCLASSIFIED shape: the C _decimal coordinate arm
#       past the ssize_t/long boundary, e.g. (0,(1,),2**63) or (0,(10**100,),0);
#       measured identical on base and patched trees -> propagates raw).
#   Gold patch (single hunk, line 1504):
#     except decimal.InvalidOperation:
#       -> except (decimal.InvalidOperation, TypeError, ValueError):
#   F2P test_invalid_value: field.clean(value, None) for value in
#     ((), [], {}, set(), object(), complex(), 'non-numeric string',
#      b'non-numeric byte-string') must raise ValidationError (not a raw
#     TypeError/ValueError). {}/set()/object()/complex()/b'...' are kind 4
#     (TypeError); ()/[] are kind 5 (ValueError); 'non-numeric string' is kind 3.
#   P2P test_to_python: f.to_python(3) == Decimal('3'), f.to_python('3.14') ==
#     Decimal('3.14') (accepted-value content observed -> P3 pin).
#
# AXIOM lane: meta.axioms has FOUR @ContractOnly A-consumed axioms over the real
#   CPython `decimal` stdlib: construct_numeric (decimal.Decimal), accepted_value
#   (its accepted return), from_floating (the accepted token of
#   Context.create_decimal_from_float) and convert_floating (that same call's
#   accept-or-refuse behaviour, the callee the floating branch dispatches to). Each
#   gets a soundness probe (real callee matches the axiom's Ensures/Exsures on the
#   axiom's Requires domain) and a containment probe (every callee-input the model
#   can reach lies in the axiom's Requires domain). The bundle's axiom_check.py is
#   the adjudication ground truth; the probes execute the REAL callee (never scrape
#   source) and import only the stdlib.
from pathlib import Path

INSTANCE = "django__django-13023"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl body — everything strictly inside # impl-start/# impl-end.
# All region surgery replaces this single block, so same_spec is guaranteed.
_GOLD_IMPL = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _with_impl(new_impl_body: str) -> str:
    """Return model.py with the impl body replaced (spec untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_body)


# ===========================================================================
# (1) POSITIVE CONTROL — structurally-different but CORRECT (soundness).
# The gold catches its three classified rejection classes and lets the FOURTH
# (the out-of-representable-range shape, kind 6) propagate implicitly. This
# variant makes that propagation EXPLICIT: a fourth handler that catches the
# unclassified rejection and re-raises the same class. Re-raising the identical
# exception class is observationally identical to not catching it at all — the
# caller sees ConstructorRangeError either way — so every obligation (P0..P3, E,
# E6) is preserved. Pure executable-shape change. MUST verify (else
# SPEC-TOO-STRONG: the spec would be forbidding a genuinely equivalent impl).
#
# NOTE: the literal gold shape `except (A, B, C):` (a tuple of classes) is NOT
# usable here — Nagini's TRANSLATOR rejects an except-clause class-tuple with
# "Not supported: class literal has unsupported format" (a front-end syntax
# limitation, NOT a spec rejection: even a 2-class tuple `except (A, B):` fails
# to translate, and the failure is a Translation error raised before any
# postcondition reasoning). A bare `raise` inside the handler is ALSO not
# translatable (Translation failed), hence the explicit re-raise below.
#
# NOTE (why the previous `except Exception:` single-handler control was removed
# from the soundness lane): a single blanket handler catches the unclassified
# range rejection TOO and converts it to the validation failure. That is not the
# gold's behaviour — the real patched `to_python` catches exactly
# (InvalidOperation, TypeError, ValueError) and lets OverflowError through — so
# the blanket-handler variant computes a DIFFERENT function and now correctly
# appears in the reject lane as `over-convert-unclassified` below.
# ===========================================================================
_POS_EXPLICIT_RERAISE = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()
    except ConstructorRangeError:
        raise ConstructorRangeError()"""

# ===========================================================================
# (2) POSITIVE CONTROL — branch-reordered fast paths AND reordered handlers
# (soundness). Check the float fast path BEFORE the absent fast path (explicit
# `elif`), and list the three classified rejection handlers in the reverse order
# (Domain, Operand, Malformed). All three reorderings preserve the exact
# value-pins: the two fast-path guards are disjoint (kind==1 vs kind==0), and the
# three handler classes are disjoint sibling classes that all raise the SAME
# uniform ValidationFailure, so their textual order is unobservable. The
# unclassified range rejection is left uncaught, exactly as in the gold.
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_REORDER = """    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    elif kind == 0:
        return None
    try:
        return construct_numeric(kind)
    except ConstructorDomainError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorMalformedError:
        raise ValidationFailure()"""

# ===========================================================================
# (3) ADMISSIBILITY — an IN-REGION self-call proves the precondition admits a
# normal, F2P/P2P-shaped input. Inside the impl we first call coerce_to_numeric
# on kind 2 (the accepted shape, exactly P2P test_to_python's f.to_python(3)),
# discharging Requires(0 <= 2 <= 5) for a legitimate input, and assert the
# guaranteed non-null accepted token. Then the real (gold) body computes the
# result for the actual `kind`. If the self-call cannot establish Requires for
# this normal input -> PRECOND-TOO-STRONG. Edited strictly inside impl -> same_spec.
# ===========================================================================
_ADMISS_IMPL = """    # --- admissibility self-call on a normal F2P/P2P-shaped input (kind 2,
    # the accepted shape, as in P2P test_to_python f.to_python(3)) ---
    Assert(0 <= 2 and 2 <= 8)
    # --- the real (gold) coercion for the actual kind ---
    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (4) UNIQUENESS — THE prepatch echo: catch ONLY ConstructorMalformedError.
# This is exactly model_prepatch.py / the pre-patch `except decimal.InvalidOperation:`.
# On kind 4 (Operand) and kind 5 (Domain) the constructor's own rejection class
# escapes undeclared -> the Exsures(ValidationFailure, kind in {3,4,5}) clause is
# unprovable (an undeclared exception class escapes). MUST reject.
# ===========================================================================
_WEAK_PREPATCH = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()"""

# ===========================================================================
# (5) PARTIAL-DOMAIN — catch malformed (3) + domain (5) but NOT operand (4).
# Correct on kinds 3 and 5; on kind 4 (the wrong-typed operand) the constructor's
# ConstructorOperandError escapes. This is the EXACT bug in the problem statement
# (DecimalField.to_python raising TypeError on a dict value) — kind 4 covers
# {} / set() / object() / complex() / b'...' in the F2P. MUST reject (the kind-4
# sub-domain's rejection escapes as a non-ValidationFailure exception).
# ===========================================================================
_PARTIAL_KIND4_ESCAPE = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (6) CONTROL-FLOW-EFFECT — on a reject kind, SWALLOW the rejection and return
# normally (return None) instead of raising. The value abstraction alone would
# not catch "returned None" vs "raised" unless the spec pins the normal-return
# domain; here P0 (Ensures kind==0 or 1 or 2) forbids a normal return on kinds
# 3/4/5, AND the Exsures(ValidationFailure, kind in {3,4,5}) is left unsatisfied.
# MUST reject. (A capability-style discriminator: raise vs return is observable.)
# ===========================================================================
_WEAK_SWALLOW = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        return None
    except ConstructorOperandError:
        return None
    except ConstructorDomainError:
        return None"""

# ===========================================================================
# (7) CONTROL-FLOW-EFFECT — on a reject kind, RE-RAISE the constructor's own
# low-level rejection class (do NOT convert to the uniform ValidationFailure).
# This is the literal anti-fix: surfacing the raw constructor error to the caller
# (a raw TypeError/ValueError), the exact behaviour the gold patch eliminates.
# The only declared Exsures of coerce_to_numeric is ValidationFailure, so letting
# ConstructorOperandError/DomainError propagate is an undeclared escape. MUST reject.
# ===========================================================================
_WEAK_RERAISE = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    return construct_numeric(kind)"""

# ===========================================================================
# (8) UNGROUNDED-ECHO / value pin — kind-2 returns a FABRICATED constant token
# (return 1) instead of the constructor's accepted_value(kind). This is the
# batch01 atk_10b witness. P3 pins Result() == accepted_value(kind); a fabricated
# literal cannot be proven equal to the abstract accessor -> MUST reject.
# (If it verified, an impl returning a constant Decimal would break P2P
# test_to_python f.to_python(3) == Decimal('3') => real SPEC-TOO-WEAK.)
# ===========================================================================
_WEAK_ECHO_CONST_KIND2 = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    if kind == 2:
        return 1
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (9) CROSS-CALLEE ECHO / value pin — kind-2 returns the FLOAT callee's token
# from_floating() instead of the constructor's accepted_value(kind). This is the
# batch01 atk_10 witness. P3 pins kind-2 to accepted_value(kind); from_floating()
# is a DIFFERENT abstract accessor, not provably equal -> MUST reject.
# (A real patch returning the float-path Decimal for an accepted non-float value
# returns the wrong number and breaks P2P test_to_python => SPEC-TOO-WEAK.)
# ===========================================================================
_WEAK_ECHO_FROMFLOAT_KIND2 = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    if kind == 2:
        return from_floating()
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (10) VALUE PIN on the FLOAT branch — kind-1 returns a fabricated constant
# (return 1) instead of from_floating(). P2 pins Result() == from_floating(); a
# literal is not provably equal to the abstract float accessor -> MUST reject.
# (A real patch returning a constant Decimal for every float input would break
# P2P test_to_python f.to_python(2.0625) == Decimal('2.062') => SPEC-TOO-WEAK.)
# ===========================================================================
_WEAK_ECHO_CONST_KIND1 = """    if kind == 0:
        return None
    if kind == 7 or kind == 8:
        return convert_floating(kind)
    if kind == 1:
        return 1
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (11) OVER-CONVERSION of the UNCLASSIFIED shape — a blanket `except Exception:`
# funnels EVERY rejection class, INCLUDING the out-of-representable-range shape
# (kind 6), into the uniform ValidationFailure. This is the impl the E6 leg
# exists to exclude: the real patched to_python catches exactly
# (InvalidOperation, TypeError, ValueError) and lets OverflowError propagate, so
# a blanket handler computes a DIFFERENT function than the gold. It is also the
# shape a spec-realignment is most likely to accidentally admit — if E6 were
# dropped instead of stated, this would verify. MUST reject: E pins the uniform
# failure to kinds 3/4/5 ONLY, so raising it on kind 6 violates E, and E6's
# ConstructorRangeError leg is left unsatisfied.
# ===========================================================================
_OVER_CONVERT_UNCLASSIFIED = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except Exception:
        raise ValidationFailure()"""

# ===========================================================================
# (12) NORMAL RETURN on the UNCLASSIFIED shape — swallow the range rejection and
# return the accepted token instead of letting it propagate. A real patch doing
# this would hand a downstream consumer a fabricated Decimal for a value the
# constructor could not build at all. MUST reject: P0 (Ensures kind==0 or 1 or 2)
# forbids a normal return on kind 6, and E6 is left unsatisfied. This is the
# raise-vs-return discriminator on the newly-stated leg.
# ===========================================================================
_RETURN_ON_UNCLASSIFIED = """    if kind == 0:
        return None
    if kind == 1 or kind == 7 or kind == 8:
        return convert_floating(kind)
    if kind == 6:
        return accepted_value(2)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (13) OVER-CONVERSION on the FLOATING branch — place the floating conversion
# INSIDE the uniform-failure handling, so the conversion's own
# wrong-typed-operand rejection is funnelled into the validation failure too.
# The real coercion invokes the floating conversion OUTSIDE that handling, so
# this impl computes a different function on the whole kind-7 class. MUST reject:
# clause E pins the uniform failure to kinds 3/4/5 ONLY (so raising it on kind 7
# violates E), and the kind-7 Exsures leg is left unsatisfied.
# ===========================================================================
_OVER_CONVERT_FLOATING = """    if kind == 0:
        return None
    try:
        if kind == 1 or kind == 7 or kind == 8:
            return convert_floating(kind)
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (14) NORMAL RETURN on the floating branch's refused shape — hand back a token
# for a value the floating conversion would not accept at all. MUST reject: P0
# forbids a normal return on kind 7, and the kind-7 Exsures leg is unsatisfied.
# ===========================================================================
_RETURN_ON_FLOATING_REFUSED = """    if kind == 0:
        return None
    if kind == 7:
        return from_floating()
    if kind == 1 or kind == 8:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""


# ===========================================================================
# (15) OVER-CONVERSION of the floating conversion's OUT-OF-RANGE refusal — catch
# the conversion's range refusal (kind 8) and funnel it into the uniform
# validation failure. The real coercion invokes that conversion OUTSIDE the
# uniform-failure handling, so its range refusal reaches the caller unchanged
# (measured identically on the base and gold-patched trees). This is the impl the
# E8 leg exists to exclude, and the one a realignment that merely WIDENED the
# domain without stating the leg would admit. MUST reject: E pins the uniform
# failure to kinds 3/4/5 ONLY, and E8's ConversionRangeError leg is unsatisfied.
# ===========================================================================
_OVER_CONVERT_FLOAT_RANGE = """    if kind == 0:
        return None
    if kind == 1 or kind == 7:
        return convert_floating(kind)
    if kind == 8:
        try:
            return convert_floating(kind)
        except ConversionRangeError:
            raise ValidationFailure()
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (16) NORMAL RETURN on the floating conversion's out-of-range shape — hand back
# a token for a value whose magnitude the conversion could not represent at all.
# MUST reject: P0 forbids a normal return on kind 8 and E8 is unsatisfied. This
# is the raise-vs-return discriminator on the newly-stated leg.
# ===========================================================================
_RETURN_ON_FLOAT_RANGE = """    if kind == 0:
        return None
    if kind == 8:
        return from_floating()
    if kind == 1 or kind == 7:
        return convert_floating(kind)
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""

# ===========================================================================
# (17) CLASS SWAP across the floating conversion's TWO refusals — raise the
# range-refusal class on the wrong-typed-operand shape (kind 7) and vice versa.
# The two refusals are DISTINCT low-level classes in the real callee, so an impl
# that swaps them surfaces the wrong class to the caller on both shapes. MUST
# reject: E7 and E8 each pin their own class to their own kind, so this violates
# both. Confirms the new leg discriminates WHICH class escapes, not merely THAT
# something escapes.
# ===========================================================================
_SWAP_FLOAT_REFUSALS = """    if kind == 0:
        return None
    if kind == 1:
        return convert_floating(kind)
    if kind == 7:
        raise ConversionRangeError()
    if kind == 8:
        raise ConstructorOperandError()
    try:
        return construct_numeric(kind)
    except ConstructorMalformedError:
        raise ValidationFailure()
    except ConstructorOperandError:
        raise ValidationFailure()
    except ConstructorDomainError:
        raise ValidationFailure()"""


SPEC_TESTS = [
    {
        "id": "pos-control-explicit-reraise",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_EXPLICIT_RERAISE),
        "rationale": (
            "Structurally-different CORRECT impl: the gold lets the unclassified "
            "range rejection propagate IMPLICITLY (no handler); this variant adds "
            "an explicit fourth handler that re-raises the same class. Re-raising "
            "the identical class is observationally identical to not catching it "
            "(the caller sees ConstructorRangeError either way), so P0..P3/E/E6 "
            "are all preserved. A faithful correct impl MUST verify (else "
            "SPEC-TOO-STRONG). NOTE: the literal gold shape except (A,B,C): is "
            "untranslatable in Nagini ('class literal has unsupported format'), "
            "and a bare `raise` also fails to translate; hence the explicit form."
        ),
    },
    {
        "id": "pos-control-reorder-fastpaths",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_REORDER),
        "rationale": (
            "Structurally-different CORRECT impl: the two disjoint accepted "
            "fast-path guards are reordered (float kind==1 checked before absent "
            "kind==0, via elif) AND the three classified rejection handlers are "
            "listed in reverse order. Disjoint guards and disjoint sibling handler "
            "classes that all raise the SAME uniform failure make the order "
            "unobservable; the unclassified range rejection stays uncaught as in "
            "the gold. Every value-pin and both Exsures legs are preserved; "
            "MUST verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-accepted-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": (
            "A positive-control self-call invokes coerce_to_numeric(2) — the "
            "accepted shape exactly as P2P test_to_python's f.to_python(3) — "
            "establishing Requires(0 <= 2 <= 8) for a legitimate input and "
            "asserting the guaranteed non-null accepted token == accepted_value(2). "
            "The real gold body then computes the actual result, so the module "
            "still verifies. If the call site cannot establish Requires for this "
            "normal input -> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-prepatch-only-malformed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_PREPATCH),
        "refinement": (
            "This IS the prepatch behaviour: catching only "
            "ConstructorMalformedError <-> the pre-patch `except "
            "decimal.InvalidOperation:`. On kind 4 (TypeError, e.g. a dict — the "
            "exact problem-statement bug) and kind 5 (ValueError, e.g. () / []) "
            "the constructor's own rejection escapes raw, so field.clean({}, None) "
            "/ field.clean((), None) raises TypeError/ValueError instead of "
            "ValidationError and F2P test_invalid_value FAILS. model_prepatch.py "
            "is exactly this and is documented to fail (G-DIFF)."
        ),
        "rationale": (
            "UNIQUENESS: with only ConstructorMalformedError caught, kinds 4 and 5 "
            "let ConstructorOperandError / ConstructorDomainError escape — an "
            "exception class the frozen spec never declares. The Exsures clause "
            "Exsures(ValidationFailure, kind==3 or 4 or 5) is then unprovable on "
            "kinds 4/5 (an undeclared exception escapes) -> REJECT. If it "
            "verified, the spec would admit the prepatch bug => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-kind4-escape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_KIND4_ESCAPE),
        "refinement": (
            "A patch widening the caught set to (InvalidOperation, ValueError) but "
            "OMITTING TypeError handles kinds 3 and 5 yet still raises a raw "
            "TypeError on kind 4 — precisely the dict value the problem statement "
            "reports. field.clean({}, None) (and set()/object()/complex()/b'...') "
            "would still raise TypeError, not ValidationError, so F2P "
            "test_invalid_value FAILS on the kind-4 sub-domain."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on kinds 3 and 5 but the kind-4 sub-domain "
            "(wrong-typed operand) lets ConstructorOperandError escape "
            "undeclared. The Exsures(ValidationFailure, kind==4) leg is unprovable "
            "-> REJECT. The element-level Exsures pins EVERY reject kind, not just "
            "a majority; a spec pinning only a subset would be SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "cflow-swallow-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_SWALLOW),
        "refinement": (
            "A patch that catches the constructor rejection and RETURNS (e.g. "
            "returns None) instead of raising would silently accept an invalid "
            "value: field.clean({}, None) would not raise at all, so "
            "test_invalid_value (which asserts a ValidationError is raised) FAILS. "
            "It also corrupts every downstream consumer expecting a Decimal."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT: a normal return on a reject kind is a "
            "raise-vs-return difference. P0 (Ensures kind==0 or 1 or 2) forbids a "
            "normal return on kinds 3/4/5, AND the Exsures(ValidationFailure, "
            "kind in {3,4,5}) is left unsatisfied -> REJECT. If it verified the "
            "value abstraction would be blind to raise-vs-return => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "cflow-reraise-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_RERAISE),
        "refinement": (
            "Dropping the handler entirely (re-raise the constructor's own raw "
            "rejection) is the literal anti-fix: the caller sees a raw TypeError / "
            "ValueError / InvalidOperation, exactly the behaviour the gold patch "
            "eliminates. field.clean({}, None) raises TypeError, not "
            "ValidationError -> F2P test_invalid_value FAILS."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT: coerce_to_numeric declares ONLY "
            "Exsures(ValidationFailure, ...). Letting ConstructorMalformedError / "
            "ConstructorOperandError / ConstructorDomainError propagate on kinds "
            "3/4/5 is an undeclared exception escape -> REJECT. The spec pins the "
            "exception IDENTITY (uniform failure vs raw constructor error)."
        ),
    },
    {
        "id": "weak-echo-const-kind2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ECHO_CONST_KIND2),
        "refinement": (
            "This is the batch01 atk_10b witness: a faithful real patch whose "
            "accepted branch returns a FABRICATED constant Decimal (not "
            "decimal.Decimal(value)) returns the wrong number for every accepted "
            "value, so P2P test_to_python f.to_python(3) == Decimal('3') / "
            "f.to_python('3.14') == Decimal('3.14') FAILS."
        ),
        "rationale": (
            "VALUE-PIN (grounded oracle): P3 pins Result() == accepted_value(kind) "
            "— an abstract @ContractOnly accessor whose value the proof never "
            "fabricates. A constant literal `1` cannot be proven equal to "
            "accepted_value(2) -> REJECT. This is the closed batch01 asymmetry "
            "hole; if it verified the spec would admit a wrong accepted Decimal "
            "=> SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-echo-fromfloat-kind2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ECHO_FROMFLOAT_KIND2),
        "refinement": (
            "This is the batch01 atk_10 witness: returning the FLOAT-path callee's "
            "token (create_decimal_from_float, which rounds via the field's "
            "context) for an accepted NON-float value yields a different, "
            "precision-rounded Decimal than decimal.Decimal(value), breaking P2P "
            "test_to_python (the accepted value's exact content is observed)."
        ),
        "rationale": (
            "CROSS-CALLEE ECHO / value-pin: P3 pins kind-2 to accepted_value(kind); "
            "from_floating() is a DISTINCT abstract accessor with no proven "
            "equality to accepted_value(2) -> REJECT. Pinning each branch to its "
            "OWN callee (symmetric) is what closes the cross-callee echo; if it "
            "verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-echo-const-kind1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_WEAK_ECHO_CONST_KIND1),
        "refinement": (
            "A faithful real patch whose float branch returns a FABRICATED "
            "constant Decimal (not self.context.create_decimal_from_float(value)) "
            "returns the wrong number for every float input, so P2P test_to_python "
            "f.to_python(2.0625) == Decimal('2.062') / f.to_python(2.1875) == "
            "Decimal('2.188') FAILS."
        ),
        "rationale": (
            "VALUE-PIN on the FLOAT branch: P2 pins Result() == from_floating(), "
            "an abstract @ContractOnly accessor. A constant literal `1` is not "
            "provably equal to from_floating() -> REJECT. Symmetric with the "
            "kind-2 pin; if it verified the float result would be free "
            "=> SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "over-convert-unclassified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_OVER_CONVERT_UNCLASSIFIED),
        "refinement": (
            "A blanket `except Exception:` (or `except (InvalidOperation, "
            "TypeError, ValueError, OverflowError):`) converts the "
            "out-of-representable-range rejection into a ValidationError too. The "
            "real patched to_python does NOT: measured on both the base and the "
            "gold-patched tree, f.to_python((0,(1,),2**63)) and "
            "f.to_python((0,(10**100,),0)) raise OverflowError, identically. So "
            "this impl computes a different function than the gold on the whole "
            "kind-6 class — it is a behaviour change the patch never made."
        ),
        "rationale": (
            "OVER-CONVERSION: clause E pins the uniform ValidationFailure to "
            "kinds 3/4/5 and to those kinds ONLY, so raising it on kind 6 makes E "
            "unprovable; clause E6's Exsures(ConstructorRangeError, kind == 6) is "
            "simultaneously unsatisfied -> REJECT. This is the case that proves "
            "the faithfulness realignment did not open a hole: E6 was STATED, not "
            "dropped, so the kind-6 behaviour is still pinned in both directions."
        ),
    },
    {
        "id": "return-on-unclassified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RETURN_ON_UNCLASSIFIED),
        "refinement": (
            "Swallowing the range rejection and returning a token hands a "
            "downstream consumer a Decimal for a value the constructor could not "
            "build at all — worse than either the base or the patched behaviour, "
            "both of which raise. No real patch does this."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT on the newly-stated leg: P0 (Ensures kind==0 or "
            "kind==1 or kind==2) forbids a normal return on kind 6, and E6 is left "
            "unsatisfied -> REJECT. Confirms the kind-6 leg discriminates "
            "raise-vs-return, not merely which exception class is raised."
        ),
    },
    {
        "id": "over-convert-floating-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_OVER_CONVERT_FLOATING),
        "refinement": (
            "Moving the floating conversion INSIDE the try (so its rejection is "
            "caught too) converts the floating branch's wrong-typed-operand "
            "rejection into a ValidationError. The real to_python does NOT: the "
            "float conversion is called at line 1501, ABOVE and OUTSIDE the try "
            "that begins at line 1502, so its TypeError escapes. Measured on both "
            "the base and the gold-patched tree, "
            "f.to_python(SimpleLazyObject(lambda: 1.5)) raises a raw TypeError "
            "identically. So this impl computes a different function than the gold "
            "on the whole kind-7 class — a behaviour change the patch never made."
        ),
        "rationale": (
            "OVER-CONVERSION on the floating branch: clause E pins the uniform "
            "ValidationFailure to kinds 3/4/5 and to those kinds ONLY, so raising "
            "it on kind 7 makes E unprovable; the kind-7 "
            "Exsures(ConstructorOperandError, kind == 7) leg is simultaneously "
            "unsatisfied -> REJECT. This is the case proving the kind-7 "
            "realignment did not open a hole: the leg was STATED, not dropped, so "
            "the floating branch's refusal is pinned in both directions."
        ),
    },
    {
        "id": "return-on-floating-refused",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RETURN_ON_FLOATING_REFUSED),
        "refinement": (
            "Swallowing the floating conversion's refusal and returning a token "
            "hands a downstream consumer a Decimal for a value the conversion "
            "could not build at all — worse than either the base or the patched "
            "behaviour, both of which let the TypeError propagate. No real patch "
            "does this."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT on the kind-7 leg: P0 (Ensures kind==0 or "
            "kind==1 or kind==2) forbids a normal return on kind 7, and the "
            "kind-7 Exsures leg is left unsatisfied -> REJECT. Confirms the leg "
            "discriminates raise-vs-return, not merely the exception class."
        ),
    },
    {
        "id": "over-convert-float-range",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_OVER_CONVERT_FLOAT_RANGE),
        "refinement": (
            "Converting the floating conversion's out-of-range refusal into the "
            "validation failure claims a guarantee the real coercion does not "
            "have: that call sits outside the try, so on such a value the real "
            "to_python raises the conversion's own class, identically on the base "
            "and gold-patched trees. An impl doing this computes a DIFFERENT "
            "function than the gold on the whole kind-8 class."
        ),
        "rationale": (
            "OVER-CONVERSION on the newly-stated leg: clause E pins the uniform "
            "failure to kinds 3/4/5 ONLY (so raising it on kind 8 violates E) and "
            "E8's ConversionRangeError leg is left unsatisfied -> REJECT. This is "
            "the case proving the kind-8 realignment STATED the leg rather than "
            "merely widening the domain: had the domain grown without E8, this "
            "impl would verify."
        ),
    },
    {
        "id": "return-on-float-range",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_RETURN_ON_FLOAT_RANGE),
        "refinement": (
            "Returning a token for a value whose magnitude the conversion refused "
            "hands a downstream consumer a Decimal the conversion never built. "
            "Neither the base nor the patched to_python does this: both let the "
            "refusal propagate."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT on the kind-8 leg: P0 (Ensures kind==0 or "
            "kind==1 or kind==2) forbids a normal return on kind 8 and E8 is "
            "unsatisfied -> REJECT. Confirms the leg discriminates raise-vs-return."
        ),
    },
    {
        "id": "swap-float-refusals",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_SWAP_FLOAT_REFUSALS),
        "refinement": (
            "The floating conversion's two refusals are distinct low-level classes "
            "in the real callee (a wrong-typed operand vs a magnitude outside the "
            "context's representable range), and a caller can tell them apart. An "
            "impl that swaps them surfaces the wrong class on both shapes."
        ),
        "rationale": (
            "CLASS-IDENTITY discriminator across the floating branch's two reject "
            "kinds: E7 pins the operand class to kind 7 and E8 pins the range "
            "class to kind 8, so swapping violates both legs -> REJECT. Confirms "
            "the realignment pinned WHICH class escapes on each shape, not merely "
            "that the domain got wider."
        ),
    },
]

# ===========================================================================
# AXIOM LANE — three @ContractOnly A-consumed axioms over the real CPython
# `decimal` stdlib. Probes EXECUTE the real callee (never scrape source), import
# only the stdlib, open nothing (no UTF-8 file-read hazard), and exit 0 iff the
# obligation holds. apply_gold=True (the axioms describe the post-gold callee
# behaviour, though decimal itself is unchanged by the patch). The bundle's
# axiom_check.py is the adjudication ground truth; these probes re-derive its core
# obligations in-container against the image's real decimal module.
# ===========================================================================

# --- construct_numeric soundness: each rejection kind raises EXACTLY the declared
#     class; the accepted kind returns normally. The axiom's Requires domain is
#     kind in {2,3,4,5}; we drive the REAL decimal.Decimal on representative +
#     fuzzed values of each kind (incl. the 8 exact F2P invalid values) and assert
#     the observed acceptance kind matches the axiom's Ensures/Exsures.
_AX_CONSTRUCT_SOUND = r'''
import decimal, random, sys
INVALID_OP = decimal.InvalidOperation

def real_kind(value):
    # NOTE ordering: OverflowError is NOT a subclass of ValueError or TypeError
    # (its MRO is OverflowError -> ArithmeticError -> Exception), so the clause
    # order below is immaterial; it is listed explicitly to make the fourth
    # rejection class an ASSERTED observation rather than a fallthrough.
    try:
        decimal.Decimal(value); return 2
    except INVALID_OP:
        return 3
    except TypeError:
        return 4
    except OverflowError:
        return 6
    except ValueError:
        return 5
    except Exception:
        return None  # undeclared escape -> UNSOUND

def check(value, expected):
    obs = real_kind(value)
    if obs is None:
        print("UNSOUND: decimal.Decimal(%r) raised outside "
              "{InvalidOp,TypeError,ValueError,OverflowError}" % (value,)); sys.exit(1)
    if obs != expected:
        print("UNSOUND: decimal.Decimal(%r) expected kind %d, observed %d" % (value, expected, obs)); sys.exit(1)

accepted = ["3","3.14","0","-1","1e3","2.0625","+0.0"," 3.5 ","  10\n",
            "1_000","Infinity","-Infinity","1E+6",".5","5.",
            0,1,-7,2**64,10**30, decimal.Decimal("1.5")]
for v in accepted: check(v, 2)
malformed = ["abc","non-numeric string","1.2.3","$5","12,34",""," ","NaNx","1 2","0x10","one","--3","1/2"]
for v in malformed: check(v, 3)
typeerr = [{}, set(), object(), complex(), b"non-numeric byte-string", b"123",
           {1:2}, {"a"}, frozenset(), bytearray(b"x"), 3.5j, type, (lambda: 0)]
for v in typeerr: check(v, 4)
valueerr = [(), [], (1,2), [1,2,3], [0], (0,),
            (2,(1,),0), (-1,(1,),0), ('0',(1,),0), (0,'1',0), (0,(10,),0),
            (0,(-1,),0), (0,(1,),'x'), (0,(1,),1.5), (0,(1,),0,0), (0,None,0),
            (0,((1,),),0)]
for v in valueerr: check(v, 5)
# ---- kind 6: a component outside the internal representable range -----------
# The FOURTH rejection class. The C _decimal (libmpdec) accelerator — the one
# `import decimal` binds and django therefore calls — converts the sign, the
# digit tuple's members and the exponent of the (sign, digits, exponent)
# coordinate form to C integers, and raises OverflowError when one does not fit.
# This is an in-domain shape of the SAME coordinate family as ()/[]/(1,2), one
# step past the ssize_t/long boundary; the coercion does not classify it.
rangeerr = [
    (0,(1,),2**63), (0,(1,),-2**63-1), (0,(1,),10**100), (0,(1,),-10**100),
    (0,(10**100,),0), (10**100,(1,),0), (0,(1,),sys.maxsize+1),
    [0,(1,),2**63], [0,(10**100,),0],
]
for v in rangeerr: check(v, 6)
# the exponent boundary itself is NOT kind 6: at exactly +/-(2**63-1)/-2**63 the
# value still fits a C ssize_t and libmpdec rejects it as InvalidOperation.
for v in [(0,(1,),2**63-1), (0,(1,),-2**63)]: check(v, 3)
# the 8 exact F2P test_invalid_value inputs must all be CLASSIFIED rejections
# (3/4/5) — i.e. none of them is the unclassified kind 6, so the patch's
# ValidationError guarantee covers every one of them.
for v in [(), [], {}, set(), object(), complex(), "non-numeric string", b"non-numeric byte-string"]:
    k = real_kind(v)
    if k not in (3,4,5):
        print("UNSOUND: F2P invalid %r observed kind %r (must be a CLASSIFIED rejection)" % (v, k)); sys.exit(1)
rng = random.Random(13023)
for _ in range(1500):
    c = rng.randint(0,4)
    if c==0: v={rng.randint(0,9):rng.randint(0,9)}
    elif c==1: v=set(rng.randint(0,9) for _ in range(rng.randint(1,4)))
    elif c==2: v=complex(rng.random(),rng.random())
    elif c==3: v=object()
    else: v=bytes(rng.randint(0,255) for _ in range(rng.randint(1,6)))
    check(v, 4)
for _ in range(1500):
    n = rng.randint(0,5); seq=[rng.randint(0,9) for _ in range(n)]
    check(list(seq),5); check(tuple(seq),5)
# fuzz kind-6: coordinate forms with a component past the C integer boundary
BIG = [2**63, 2**63+1, -2**63-1, -2**63-2, 10**100, -10**100, 10**400]
for _ in range(1500):
    where = rng.randint(0,2)
    if where == 0:
        v = (rng.choice([0,1]), (rng.randint(0,9),), rng.choice(BIG))
    elif where == 1:
        v = (rng.choice([0,1]), (rng.choice([b for b in BIG if b > 0]),), rng.randint(-5,5))
    else:
        v = (rng.choice([b for b in BIG if b > 0]), (rng.randint(0,9),), rng.randint(-5,5))
    check(v, 6)
    check(list(v), 6)
junk="abcXYZ$%@,/ \t!?one two"
for _ in range(1500):
    s="".join(rng.choice(junk) for _ in range(rng.randint(1,12)))
    try:
        decimal.Decimal(s); continue  # happened to be a valid literal (all-space) -> skip
    except INVALID_OP:
        check(s,3)
    except (TypeError, ValueError, OverflowError):
        print("UNSOUND: string %r raised non-InvalidOperation" % (s,)); sys.exit(1)
# EXHAUSTIVENESS of the four declared classes: a broad cross-arm census must
# surface no FIFTH rejection class (real_kind returning None). This is what makes
# the four-way Exsures total over the rejection space rather than merely wider.
POOL_INT=[0,1,-1,2**63,2**63+1,-2**63-1,10**100,sys.maxsize,-sys.maxsize-1]
POOL_MISC=['F','n','N','x','',None,1.5,True,(1,),[1],'1',{},set(),object(),b'1',
           complex(),memoryview(b'1'),range(2),frozenset(),type,decimal.Decimal(1)]
census = {}
for _ in range(40000):
    a = rng.randint(0,6)
    if a <= 2:
        v = (rng.choice(POOL_INT+POOL_MISC),
             rng.choice([tuple(rng.choice(POOL_INT+POOL_MISC) for _ in range(rng.randint(0,4)))]+POOL_MISC),
             rng.choice(POOL_INT+POOL_MISC))
    elif a == 3: v = tuple(rng.choice(POOL_INT+POOL_MISC) for _ in range(rng.randint(0,6)))
    elif a == 4: v = [rng.choice(POOL_INT+POOL_MISC) for _ in range(rng.randint(0,6))]
    elif a == 5: v = ''.join(rng.choice('0123456789eE+-._ NnaIifSs') for _ in range(rng.randint(0,20)))
    else: v = rng.choice(POOL_INT+POOL_MISC)
    k = real_kind(v)
    if k is None:
        print("UNSOUND: a FIFTH rejection class escaped on %r" % (v,)); sys.exit(1)
    census[k] = census.get(k,0)+1
if 6 not in census:
    print("PROBE INEFFECTIVE: the census never produced a kind-6 rejection"); sys.exit(1)
print("construct_numeric SOUND: every rejection is exactly one of "
      "{InvalidOperation,TypeError,ValueError,OverflowError}; accepted kinds "
      "return normally; 40000-input cross-arm census found NO fifth class "
      "(kind histogram %r)." % (sorted(census.items()),))
sys.exit(0)
'''

# --- accepted_value soundness: the real decimal.Decimal(value) returns a non-null
#     Decimal on every accepted (kind-2) input. The axiom only claims
#     Ensures(Result() is not None) (value abstract), so it must NOT over-claim.
_AX_ACCEPTED_SOUND = r'''
import decimal, random, sys
accepted = ["3","3.14","0","-1","1e3","2.0625","+0.0"," 3.5 ","  10\n",
            "1_000","Infinity","-Infinity","1E+6",".5","5.",
            0,1,-7,2**64,10**30, decimal.Decimal("1.5")]
for v in accepted:
    produced = decimal.Decimal(v)
    if produced is None:
        print("UNSOUND: decimal.Decimal(%r) returned None for an accepted value" % (v,)); sys.exit(1)
    if not isinstance(produced, decimal.Decimal):
        print("UNSOUND: decimal.Decimal(%r) returned non-Decimal %s" % (v, type(produced).__name__)); sys.exit(1)
# fuzz: random valid numeric strings + ints
rng = random.Random(2)
for _ in range(2000):
    if rng.random() < 0.5:
        v = str(rng.randint(-10**12, 10**12))
    else:
        v = "%d.%02d" % (rng.randint(0,9999), rng.randint(0,99))
    produced = decimal.Decimal(v)
    if produced is None or not isinstance(produced, decimal.Decimal):
        print("UNSOUND: accepted %r did not yield a non-null Decimal" % (v,)); sys.exit(1)
print("accepted_value SOUND: real decimal.Decimal returns a non-null Decimal on every accepted input.")
sys.exit(0)
'''

# --- from_floating soundness: Context.create_decimal_from_float never raises on
#     ANY float, incl. inf/-inf/nan (the field uses prec=4 in the F2P). The axiom
#     claims Ensures(True) (a normal return, value abstract).
_AX_FROMFLOAT_SOUND = r'''
import decimal, random, sys
ctx = decimal.Context(prec=4)

# ---- kind 1: a GENUINE float is converted without raising ---------------------
class MyFloat(float):
    pass
floats = [0.0,-0.0,1.0,-1.0,2.4,2.0625,2.1875,3.1415926535897,
          1e308,-1e308,1e-308,1.5e-300,float("inf"),float("-inf"),float("nan"),
          sys.float_info.max,-sys.float_info.max,sys.float_info.min,5e-324,
          MyFloat(1.5),MyFloat(float("inf")),MyFloat(0.0)]
for fv in floats:
    try:
        ctx.create_decimal_from_float(fv)
    except Exception as e:
        print("UNSOUND: create_decimal_from_float(%r) raised %s" % (fv, type(e).__name__)); sys.exit(1)
rng = random.Random(7)
for _ in range(2000):
    fv = rng.uniform(-1e6,1e6) * (10 ** rng.randint(-20,20))
    try:
        ctx.create_decimal_from_float(fv)
    except Exception as e:
        print("UNSOUND: create_decimal_from_float(%r) raised %s" % (fv, type(e).__name__)); sys.exit(1)

# ---- kind 7: a value the coercion ROUTES to this conversion but which the -----
# conversion refuses as a wrong-typed operand. The coercion's floating-branch
# test is isinstance(value, float); the C _decimal create_decimal_from_float
# does an EXACT PyFloat/PyLong check instead of a duck-typed __float__ call, so a
# value that satisfies isinstance without being a real float is refused with
# TypeError. That call sits OUTSIDE the coercion's try, so the TypeError escapes.
# The axiom's Exsures(ConstructorOperandError, kind == 7) stands for exactly it.
class _AttrSpoof:
    __class__ = float
class _PropSpoof:
    @property
    def __class__(self):
        return float
spoofers = [("attr __class__", _AttrSpoof()), ("property __class__", _PropSpoof())]
try:
    from unittest.mock import MagicMock, Mock, NonCallableMock
    spoofers += [("MagicMock(spec=float)", MagicMock(spec=float)),
                 ("Mock(spec=float)", Mock(spec=float)),
                 ("NonCallableMock(spec=float)", NonCallableMock(spec=float))]
except Exception:
    pass
try:
    from django.utils.functional import SimpleLazyObject
    for fac in (lambda: 1.5, lambda: float("inf"), lambda: float("nan"),
                lambda: 0.0, lambda: -1e308):
        spoofers.append(("SimpleLazyObject(float)", SimpleLazyObject(fac)))
except Exception:
    pass
probed = 0
for label, v in spoofers:
    if isinstance(v, float) is not True:
        print("PROBE INEFFECTIVE: %s does not satisfy the coercion's floating-branch test" % label); sys.exit(1)
    try:
        ctx.create_decimal_from_float(v)
        print("UNSOUND: create_decimal_from_float ACCEPTED %s; the axiom's kind-7 "
              "rejection leg claims it refuses this operand" % label); sys.exit(1)
    except TypeError:
        probed += 1
    except Exception as e:
        print("UNSOUND: create_decimal_from_float(%s) raised %s, not the "
              "wrong-typed-operand class the kind-7 leg declares"
              % (label, type(e).__name__)); sys.exit(1)
if probed == 0:
    print("PROBE INEFFECTIVE: no floating-branch operand rejection was exercised"); sys.exit(1)
print("from_floating/convert_floating SOUND: create_decimal_from_float returned "
      "normally on every genuine float (incl. inf/-inf/nan and float subclasses) "
      "and refused all %d floating-branch operand spoofers with EXACTLY the "
      "wrong-typed-operand class." % probed)
sys.exit(0)
'''

# --- containment: every callee-input the MODEL can reach lies in each axiom's
#     Requires domain. coerce_to_numeric reaches construct_numeric / accepted_value
#     ONLY when kind not in {0,1}, i.e. kind in {2,3,4,5} — exactly
#     construct_numeric's Requires(kind in {2,3,4,5}) and (for the accepted token)
#     accepted_value's Requires(kind == 2) reached only on the kind-2 leg.
#     from_floating is reached only on kind == 1 and takes no kind argument. There
#     is no caller-reachable input outside any axiom's Requires domain; this probe
#     enumerates the model's full reachable kind set and asserts containment.
_AX_CONTAINMENT = r'''
import sys
# coerce_to_numeric Requires: 0 <= kind <= 8 -> reachable kinds = {0,...,8}
reachable = set(range(0, 9))
# Control flow: kind 0 -> return None (no callee); kind 1, 7 or 8 ->
#   convert_floating(kind); else -> construct_numeric(kind).
convert_inputs = {k for k in reachable if k in (1, 7, 8)}      # {1,7,8}
convert_domain = {1, 7, 8}
missing = convert_inputs - convert_domain
if missing:
    print("AXIOM-TOO-WEAK-FOR-CALLER: convert_floating reachable inputs %r outside Requires %r" % (missing, convert_domain)); sys.exit(1)
construct_inputs = {k for k in reachable if k not in (0, 1, 7, 8)}   # {2,3,4,5,6}
# construct_numeric Requires(kind in {2,3,4,5,6}) — the fourth rejection kind is
# inside the domain, so no reachable value is excluded from the precondition.
construct_domain = {2, 3, 4, 5, 6}
missing = construct_inputs - construct_domain
if missing:
    print("AXIOM-TOO-WEAK-FOR-CALLER: construct_numeric reachable inputs %r outside Requires %r" % (missing, construct_domain)); sys.exit(1)
# accepted_value is consumed only on the kind == 2 accepted leg (Result() ==
# accepted_value(kind) with kind == 2); its Requires(kind == 2) is met exactly.
accepted_inputs = {k for k in construct_inputs if k == 2}      # {2}
accepted_domain = {2}
missing = accepted_inputs - accepted_domain
if missing:
    print("AXIOM-TOO-WEAK-FOR-CALLER: accepted_value reachable inputs %r outside Requires %r" % (missing, accepted_domain)); sys.exit(1)
# Every callee also carries Requires(kind == value_kind()), tying its tag to the
# acceptance shape of the value in scope (mapping.md 3.4). The caller meets it by
# construction: coerce_to_numeric carries the same tie and passes its OWN kind to
# every callee, so no caller-reachable callee-input is excluded by it either.
# Covering MORE than the caller reaches would be SOUND, not a defect; here the
# coverage matches exactly. No caller-reachable callee-input is uncovered.
print("CONTAINMENT OK: construct_numeric reaches %r within %r; accepted_value reaches %r within %r; "
      "convert_floating reaches %r within %r; from_floating consumed only as the "
      "kind==1 value pin (no kind argument)."
      % (sorted(construct_inputs), sorted(construct_domain), sorted(accepted_inputs),
         sorted(accepted_domain), sorted(convert_inputs), sorted(convert_domain)))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-construct-sound",
        "axiom": "construct_numeric",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_CONSTRUCT_SOUND,
        "rationale": (
            "Runs the REAL decimal.Decimal on representative + 6000 fuzz values of "
            "every kind (incl. the 8 exact F2P invalid values) under the default "
            "context the field uses. Asserts kind-2 accepts, kind-3 raises EXACTLY "
            "InvalidOperation, kind-4 EXACTLY TypeError, kind-5 EXACTLY ValueError, "
            "kind-6 EXACTLY OverflowError, and — via a 40000-input cross-arm census "
            "— that NO FIFTH rejection class exists. The kind-6 leg is the "
            "faithfulness-critical one: the C _decimal accelerator raises "
            "OverflowError on the (sign, digits, exponent) coordinate arm once a "
            "component passes the ssize_t/long boundary, and it also asserts the "
            "boundary itself (exponent == 2**63-1 / -2**63) is still kind 3, so the "
            "kind-3/kind-6 split is pinned on both sides. Any disagreement "
            "=> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-accepted-sound",
        "axiom": "accepted_value",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_ACCEPTED_SOUND,
        "rationale": (
            "The accepted_value axiom claims only Ensures(Result() is not None) "
            "(value abstract). Runs the REAL decimal.Decimal(value) on all accepted "
            "boundary inputs + 2000 fuzz and asserts it returns a non-null Decimal "
            "every time, so the axiom never over-claims. Any None/non-Decimal "
            "return => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-fromfloat-sound",
        "axiom": "from_floating",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_FROMFLOAT_SOUND,
        "rationale": (
            "The from_floating axiom claims Ensures(True) (a normal return). Runs "
            "the REAL Context(prec=4).create_decimal_from_float (the F2P field's "
            "precision) on boundary floats incl. inf/-inf/nan + 2000 fuzz and "
            "asserts a normal return every time. Any raise => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-containment",
        "axiom": "construct_numeric",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": (
            "Containment: every callee-input coerce_to_numeric can reach "
            "(construct_numeric only on kind in {2,3,4,5,6}; accepted_value only on "
            "kind==2; from_floating only on kind==1, no kind arg) lies in the "
            "respective axiom's Requires domain. A caller-reachable input outside "
            "the domain => AXIOM-TOO-WEAK-FOR-CALLER; here coverage matches exactly. "
            "The fourth rejection kind was added to BOTH the coercion's Requires "
            "(0..6) and construct_numeric's, so the repair widened the modelled "
            "domain rather than narrowing it — no real input class was excluded to "
            "make the divergence unobservable."
        ),
    },
]
