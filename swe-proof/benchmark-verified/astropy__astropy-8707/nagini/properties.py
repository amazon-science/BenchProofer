# properties.py — PBT falsification battery for astropy__astropy-8707.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec actually protects — see model.py / refinement.md):
#   build_record_image(raw: List[int], from_bytes: bool) -> List[int]
#     Requires MustTerminate(3)                      <-- TOTAL correctness
#     Requires Acc(list_pred(raw), 1/2)              <-- READ-ONLY input (half perm)
#     Requires all_bytes(ToSeq(raw))
#     Requires Implies(not from_bytes, text_form(raw))  <-- the text-form INPUT form
#     Ensures  Acc(list_pred(raw), 1/2)              <-- frame: caller keeps its half
#     Ensures  Acc(list_pred(Result()))
#     Ensures  ToSeq(Result()) == pad_to_width(reinterpret(ToSeq(raw)))   <-- VALUE
#     Ensures  len(Result()) >= len(raw)
#     Ensures  ToSeq(Result()).take(len(raw)) == ToSeq(raw)               <-- content prefix
#     Ensures  len(Result()) % WIDTH == 0
#     Ensures  text_form(Result())                   <-- TEXT FORM (see below)
#     (NO Exsures  ==  both input forms accepted; never raise)
#
#   TWO INDEPENDENT HALVES, and this is the whole point of the battery.
#
#   (a) VALUE. `reinterpret` is @Pure with Ensures(Result() == x) — it preserves
#   every element, so the value clause is grounded entirely in `raw` (fully
#   unfoldable, not an opaque answer key): any value an impl returns is checked
#   against pad_to_width(ToSeq(raw)) itself. The value-mask and drop-element
#   lanes below attack this half.
#
#   (b) TEXT FORM. Because the correspondence PRESERVES VALUES, it leaves no
#   trace in the value, so (a) alone cannot see whether a byte sequence was ever
#   taken over into textual content: padding `raw` directly produces the very
#   same value. That half is carried by `text_form`, an OPAQUE @Pure
#   @ContractOnly property with NO BODY. Nothing computes it and no impl can
#   assert it of a value of its choosing; `enter_text_form` is its only source,
#   `pad_runtime` DEMANDS it of its argument, and the postcondition demands it of
#   the result. So an impl that hands a byte-form input to the padding step
#   without that step fails pad_runtime's precondition. The text-form lanes below
#   attack this half — it is the load-bearing discriminator, and a spec carrying
#   only (a) admits an impl that skips the correspondence entirely.
#
#   A text-form INPUT (from_bytes false) carries text_form by virtue of its form,
#   so padding it as it stands is admissible — that is the real function's own
#   text path, and the `text-input-padded-directly` accept lane pins it. Nothing
#   beyond element values is assumed of a byte-form input, so the byte domain is
#   not narrowed.
from pathlib import Path

INSTANCE = "astropy__astropy-8707"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (lines between # impl-start and # impl-end).
# Editing only these keeps spec_view (hence same_spec) byte-identical.
# ---------------------------------------------------------------------------

# The whole gold impl body (verbatim from model.py impl region).
_IMPL_GOLD = """    # The code-point correspondence, spelled out step by step: every element of
    # the input is carried across unchanged (byte value b -> code point b), for
    # either input form.
    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(all_bytes(ToSeq(raw)))
        Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
        # invariants-end
        c = raw[i - 1]
        Assert(ToSeq(raw).drop(i - 1)[0] == c)
        Assert(ToSeq(raw).drop(i - 1).drop(1) == ToSeq(raw).drop(i))
        image = [c] + image
        i = i - 1
    Assert(ToSeq(image) == reinterpret(ToSeq(raw)))
    # Carrying the elements across is what makes the value textual content, so
    # the outcome is taken over into text form; the padding step, defined on
    # textual content, then applies for either input form.
    text = enter_text_form(image)
    Assert(ToSeq(text) == reinterpret(ToSeq(raw)))
    res = pad_runtime(text)
    return res"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: gold impl body not found verbatim"


# === (1) POSITIVE CONTROL — structurally different but CORRECT (expect verify) =
# Keep the backward loop (the front-recursive reinterpret needs the front unfold;
# a forward-append variant would be a PROOF gap, not a spec defect — PLAN caveat).
# Reshape LOCALLY: hoist `c` via two locals, reorder the two in-loop Asserts, and
# stage the prepend through a temp list. Same observable behaviour, gold proof
# still discharges. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
_IMPL_POS = """    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(all_bytes(ToSeq(raw)))
        Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
        # invariants-end
        j = i - 1
        c = raw[j]
        # reordered (vs gold) but equivalent unfold facts for reinterpret:
        Assert(ToSeq(raw).drop(j).drop(1) == ToSeq(raw).drop(i))
        Assert(ToSeq(raw).drop(j)[0] == c)
        head = [c]  # type: List[int]
        image = head + image
        i = j
    Assert(ToSeq(image) == reinterpret(ToSeq(raw)))
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (2) ACCEPT — a text-form input may be padded as it stands (expect verify) ==
# This is the real function's own TEXT path: an input supplied already in text
# form IS textual content, so the padding step applies to it directly, while a
# byte-form input is taken over into text form first. Both branches must be
# admissible or the spec would be demanding work the real function does not do on
# its text path (SPEC-TOO-STRONG), and it would also prove the precondition had
# narrowed the byte domain. Pins that the discriminator is the INPUT FORM, not a
# blanket "always call the step" requirement.
_IMPL_TEXT_DIRECT = """    if from_bytes:
        # a byte sequence is taken over into textual content first
        image = []  # type: List[int]
        i = len(raw)
        while i > 0:
            # invariants-start
            Invariant(MustTerminate(i + 1))
            Invariant(Acc(list_pred(raw), 1 / 2))
            Invariant(Acc(list_pred(image)))
            Invariant(0 <= i and i <= len(raw))
            Invariant(all_bytes(ToSeq(raw)))
            Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
            # invariants-end
            c = raw[i - 1]
            Assert(ToSeq(raw).drop(i - 1)[0] == c)
            Assert(ToSeq(raw).drop(i - 1).drop(1) == ToSeq(raw).drop(i))
            image = [c] + image
            i = i - 1
        text = enter_text_form(image)
        res = pad_runtime(text)
        return res
    # an input already in text form is textual content: pad it as it stands
    res = pad_runtime(raw)
    return res"""

# === (3) ADMISSIBILITY — precondition admits a normal F2P-shaped input (verify) =
# Cannot add a top-level caller (that would leave the impl region and break
# same_spec). Instead, in-region: re-derive the precondition consequences and
# confirm a NORMAL return is reachable (no Exsures path forced). If the Requires
# were vacuous/over-strong the impl could not both use these facts and return.
_IMPL_ADMISS = """    # admissibility: the precondition facts are usable and non-vacuous, and a
    # normal (non-raising) return is reachable for an in-domain input.
    Assert(all_bytes(ToSeq(raw)))          # from Requires; usable
    Assert(len(raw) >= 0)                  # list length is well-defined
    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(all_bytes(ToSeq(raw)))
        Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
        # invariants-end
        c = raw[i - 1]
        Assert(ToSeq(raw).drop(i - 1)[0] == c)
        Assert(ToSeq(raw).drop(i - 1).drop(1) == ToSeq(raw).drop(i))
        image = [c] + image
        i = i - 1
    Assert(ToSeq(image) == reinterpret(ToSeq(raw)))
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (4) FRAME-MUTATION — write to the read-only input (expect reject) =========
# raw is Requires(Acc(list_pred(raw), 1/2)): the function holds only HALF the
# permission, so any WRITE to raw must fail for INSUFFICIENT PERMISSION. The gold
# postcondition invariants are kept VERBATIM so the rejection is attributable to
# the write, not to a spec change. A faithful real patch that overwrites its input
# `image` argument (Card.fromstring) would mutate caller-shared state — the F2P
# test reuses the literal and asserts keyword/value, and mutating the caller's
# bytes is not what the gold does (gold rebinds a local) — so it would NOT
# faithfully resolve. This is the #1 weakness class a byte-fuzzer never finds.
_IMPL_FRAME = """    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw)))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(all_bytes(ToSeq(raw)))
        Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
        # invariants-end
        c = raw[i - 1]
        Assert(ToSeq(raw).drop(i - 1)[0] == c)
        Assert(ToSeq(raw).drop(i - 1).drop(1) == ToSeq(raw).drop(i))
        # FRAME MUTATION: write back to the read-only half-permission input.
        raw[i - 1] = c
        image = [c] + image
        i = i - 1
    Assert(ToSeq(image) == reinterpret(ToSeq(raw)))
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (5) TEXT-FORM / the original defect — no correspondence at all (reject) ====
# THE load-bearing lane. The impl hands the input STRAIGHT to the padding step,
# performing no code-point correspondence whatsoever. Note this satisfies every
# VALUE clause: the correspondence preserves values, so
# pad_to_width(reinterpret(ToSeq(raw))) == pad_to_width(ToSeq(raw)). Only the
# text-form half rejects it — pad_runtime DEMANDS text_form of its argument, and
# a byte-form input (from_bytes true) has no such property, since
# `enter_text_form` is text_form's only source. A faithful real patch leaving
# Card.fromstring untouched hands raw bytes to _pad, which raises TypeError
# instead of returning keyword='ABC'/value='abc', so test_card_from_bytes FAILS.
# A spec whose only content were the value clauses would ADMIT this impl.
_IMPL_NO_STEP = """    # no correspondence applied: hand the input straight to the padding step
    res = pad_runtime(raw)
    return res"""

# === (6) TEXT-FORM / inverted input form (expect reject) =======================
# The pre-patch behaviour reached by branching the OTHER way: the byte-form input
# is padded as it stands and only a text-form input is taken over into text form.
# Wrong on exactly the byte sub-domain the change is about, and it is a DIFFERENT
# path to the same defect than (5) — (5) skips the step for both forms, this one
# skips it precisely where it is required. Rejected on the byte branch:
# pad_runtime's text_form precondition cannot be met for a byte-form input.
# A faithful real patch of this shape decodes the str (a no-op) and passes bytes
# through raw, so test_card_from_bytes still FAILS.
_IMPL_INVERTED = """    if from_bytes:
        # byte-sequence input handed to the padding step as it stands
        res = pad_runtime(raw)
        return res
    text = enter_text_form(raw)
    res = pad_runtime(text)
    return res"""

# === (7) LAUNDERED TEXT FORM — right property, wrong value (expect reject) =====
# Attacks the seam between the two halves: this impl DOES call the step, so
# text_form(Result()) holds honestly — but it applies it to a fabricated value
# (all spaces, correct length) rather than to the input's elements. It shows the
# text-form half is not a loophole that excuses the value half: the value clause
# ToSeq(Result()) == pad_to_width(reinterpret(ToSeq(raw))) fails on any input
# with a non-space element. Ungrounded-oracle-echo class.
_IMPL_LAUNDER = """    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(len(image) == len(raw) - i)
        # invariants-end
        # fabricated content: the input's elements are never carried across
        image = [32] + image
        i = i - 1
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (8) PARTIAL-DOMAIN — correct except it drops the LAST byte (expect reject) =
# Loop `while i > 1` instead of `> 0`: every byte but the FIRST (index 0) is
# carried across; the first byte is dropped. On a non-empty input the image is one
# short and its content prefix no longer equals raw, violating BOTH the
# value equality ToSeq(Result()) == pad_to_width(reinterpret(...)) AND
# ToSeq(Result()).take(len(raw)) == ToSeq(raw). A faithful real patch that drops
# the first byte of `image` decodes "BC     = 'abc'" — Card.fromstring then parses
# a wrong keyword/value, so test_card_from_bytes FAILS. The loop invariant
# `ToSeq(image)==reinterpret(ToSeq(raw).drop(i))` would no longer close to
# `drop(0)` at exit, so the spec must reject it.
_IMPL_PARTIAL = """    image = []  # type: List[int]
    i = len(raw)
    while i > 1:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(ToSeq(image) == reinterpret(ToSeq(raw).drop(i)))
        # invariants-end
        c = raw[i - 1]
        Assert(ToSeq(raw).drop(i - 1)[0] == c)
        Assert(ToSeq(raw).drop(i - 1).drop(1) == ToSeq(raw).drop(i))
        image = [c] + image
        i = i - 1
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (9) VALUE-MASK — ASCII-mask the byte value (expect reject) ================
# Replace the value-preserving correspondence with c & 0x7f (ascii mask):
# identical to gold on bytes 0..127 but DIFFERENT on 128..255. raw can reach those
# values (Requires all_bytes => 0..255), so the value equality with reinterpret
# (the IDENTITY) and the content-prefix clause both fail on the high-byte
# sub-domain. This is the latin-1-vs-ascii distinction the change turns on: a real
# patch using .decode('ascii') (or masking) would corrupt any byte > 127 (mojibake
# / the very malformatted-FITS bytes the change keeps), so it would not faithfully
# reproduce gold (and would raise on non-ascii bytes).
# Modeled here as the bitmask; same_spec is preserved (impl-region only).
_IMPL_MASK = """    image = []  # type: List[int]
    i = len(raw)
    while i > 0:
        # invariants-start
        Invariant(MustTerminate(i + 1))
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(Acc(list_pred(image)))
        Invariant(0 <= i and i <= len(raw))
        Invariant(all_bytes(ToSeq(raw)))
        Invariant(len(image) == len(raw) - i)
        # invariants-end
        c = raw[i - 1] % 128   # ASCII-MASK: identity on 0..127, wrong on 128..255
        image = [c] + image
        i = i - 1
    text = enter_text_form(image)
    res = pad_runtime(text)
    return res"""

# === (10) SKIP THE PADDING STEP on an aligned input (expect reject) ============
# Boundary lane: when the input length is already a whole multiple of the width,
# return the textual content WITHOUT the padding step. text_form(Result()) still
# holds (the step conferred it), so this too probes the seam — but the EMPTY input
# is the boundary that refutes it: the real padding helper pads an empty input up
# to a FULL record (adding exactly WIDTH), so returning it unpadded breaks
# len(Result()) % WIDTH == 0's companion value clause. A real patch skipping _pad
# on aligned input would leave a 0-length image where the real code produces a
# full blank record.
_IMPL_SKIP_PAD = """    text = enter_text_form(raw)
    if len(raw) % WIDTH == 0:
        # already a whole multiple: hand it back without the padding step
        return text
    res = pad_runtime(text)
    return res"""

# === (11) DIVERGENCE — never reach the return (expect reject) ==================
# Under PARTIAL correctness every Ensures holds vacuously of a run that never
# returns, so a diverging impl verifies and its faithful patch HANGS the test it
# was meant to fix. Requires(MustTerminate(3)) at the method level plus the
# per-loop Invariant(MustTerminate(_)) is what rejects it; this lane is the
# control proving the obligation is load-bearing rather than decorative.
_IMPL_DIVERGE = """    i = 0
    while i >= 0:
        # invariants-start
        Invariant(Acc(list_pred(raw), 1 / 2))
        Invariant(i >= 0)
        # invariants-end
        i = i + 1
    text = enter_text_form(raw)
    res = pad_runtime(text)
    return res"""


SPEC_TESTS = [
    {
        "id": "pos-control-reshaped-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: backward loop kept "
                     "(front-recursive reinterpret needs the front unfold), but "
                     "locals hoisted (j, head), the two in-loop unfold Asserts "
                     "reordered, and the trailing Assert dropped. Same behaviour; "
                     "gold proof still discharges. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "accept-text-input-padded-directly",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_TEXT_DIRECT),
        "rationale": "The real function's own TEXT path: an input supplied "
                     "already in text form IS textual content, so the padding "
                     "step applies to it directly, while a byte-form input is "
                     "taken over into text form first. Must verify — otherwise "
                     "the spec demands work the real function does not do on its "
                     "text path (SPEC-TOO-STRONG). Also demonstrates the "
                     "byte-input domain was NOT narrowed: the discriminator is "
                     "the input form, not a blanket 'always call the step'.",
    },
    {
        "id": "admissibility-indomain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives the precondition consequences (all_bytes, "
                     "len>=0) in-region and reaches a normal (non-raising) "
                     "return for an in-domain input. If the Requires were vacuous "
                     "or over-strong this could not both use the facts and return "
                     "=> PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "Faithful real patch: Card.fromstring overwriting its input "
                      "`image` (e.g. image[i]=...) would mutate caller-shared "
                      "bytes; gold only rebinds a local (image = image.decode). "
                      "Mutating the caller's buffer is observably different and not "
                      "what gold does, so the refined patch would not faithfully "
                      "resolve test_card_from_bytes' contract on the shared input.",
        "rationale": "raw is Acc(list_pred(raw), 1/2) — only half permission. The "
                     "write raw[i-1]=c needs FULL permission => Nagini rejects for "
                     "insufficient permission. Source: the permission system + the "
                     "Acc(...,1/2) Requires. Gold invariants kept verbatim so the "
                     "rejection is attributable to the write.",
    },
    {
        "id": "text-form-no-correspondence-at-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NO_STEP),
        "refinement": "This is Card.fromstring left as it stands: raw bytes go "
                      "straight to _pad, which raises TypeError 'can't concat str "
                      "to bytes' instead of returning keyword='ABC'/value='abc', "
                      "so test_card_from_bytes FAILS — the faithful patch does not "
                      "resolve.",
        "rationale": "THE load-bearing lane. Satisfies every VALUE clause — the "
                     "correspondence preserves values, so "
                     "pad_to_width(reinterpret(ToSeq(raw))) == "
                     "pad_to_width(ToSeq(raw)) — and is rejected ONLY by the "
                     "text-form half: pad_runtime Requires(text_form(text)) and a "
                     "byte-form input has no such property, `enter_text_form` "
                     "being text_form's only source. A spec carrying only the "
                     "value clauses would ADMIT this impl.",
    },
    {
        "id": "text-form-inverted-input-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_INVERTED),
        "refinement": "A faithful real patch of this shape decodes the str input "
                      "(a no-op) and passes a bytes input through unchanged to "
                      "_pad, which raises TypeError — test_card_from_bytes still "
                      "FAILS.",
        "rationale": "A DIFFERENT path to the same defect than the lane above: "
                     "that one omits the step for both forms, this one omits it "
                     "precisely where it is required (the byte form) while "
                     "applying it where it is not needed. Rejected on the byte "
                     "branch by pad_runtime's text_form precondition.",
    },
    {
        "id": "laundered-text-form-fabricated-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_LAUNDER),
        "refinement": "A faithful real patch returning a blank record of the "
                      "right length instead of the decoded input gives "
                      "keyword='' — test_card_from_bytes FAILS.",
        "rationale": "Probes the SEAM between the two halves: the step IS called, "
                     "so text_form(Result()) holds honestly, but it is applied to "
                     "a fabricated all-spaces value. Rejected by the VALUE clause "
                     "ToSeq(Result()) == pad_to_width(reinterpret(ToSeq(raw))) on "
                     "any input with a non-space element. Proves the text-form "
                     "half is not a loophole excusing the value half.",
    },
    {
        "id": "partial-domain-drop-first-byte",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_PARTIAL),
        "refinement": "Faithful real patch dropping the first byte of `image` "
                      "(image = image.decode('latin1')[1:]) decodes \"BC     = "
                      "'abc'\" — Card.fromstring then parses a wrong keyword, so "
                      "test_card_from_bytes (assert c.keyword=='ABC') FAILS.",
        "rationale": "Loop `while i > 1` drops index 0. At exit "
                     "ToSeq(image)==reinterpret(ToSeq(raw).drop(1)) != "
                     "reinterpret(ToSeq(raw)), so the value equality "
                     "ToSeq(Result())==pad_to_width(reinterpret(ToSeq(raw))) and "
                     "ToSeq(Result()).take(len(raw))==ToSeq(raw) both fail (on any "
                     "non-empty input). Source: the value postcondition + the "
                     "content-prefix clause.",
    },
    {
        "id": "value-mask-ascii-7bit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_MASK),
        "refinement": "Faithful real patch using .decode('ascii') / a 7-bit mask "
                      "agrees with gold on bytes 0..127 but corrupts (or raises on) "
                      "bytes 128..255 — exactly the malformatted/non-ASCII bytes the "
                      "latin-1 gold deliberately retains. A header carrying such a "
                      "byte would mojibake or error, so the refined patch does not "
                      "faithfully reproduce gold on its declared domain.",
        "rationale": "c = raw[i-1] % 128 equals the identity (reinterpret) only on "
                     "0..127; all_bytes admits 0..255, so on a high byte "
                     "ToSeq(image) != reinterpret(ToSeq(raw)) and the value "
                     "equality fails. Source: reinterpret's Ensures(Result()==x) "
                     "(identity) consumed by the value postcondition.",
    },
    {
        "id": "boundary-skip-padding-when-aligned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_SKIP_PAD),
        "refinement": "A faithful real patch skipping _pad when len(image) is "
                      "already a multiple of 80 leaves an EMPTY image where the "
                      "real code produces a full blank record, so the card image "
                      "is not a well-formed record and the F2P assertions on "
                      "keyword/value do not hold.",
        "rationale": "Boundary lane on the EMPTY input: the real padding helper "
                     "pads an empty input up to a FULL record (adding exactly "
                     "WIDTH), so returning it unpadded breaks the value clause "
                     "ToSeq(Result()) == pad_to_width(reinterpret(ToSeq(raw))). "
                     "text_form(Result()) still holds here, so this lane also "
                     "confirms the text-form half does not excuse the value half.",
    },
    {
        "id": "divergence-never-returns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DIVERGE),
        "refinement": "A faithful real patch that spins before padding hangs "
                      "test_card_from_bytes rather than resolving it: the test "
                      "never completes, so the instance is not resolved.",
        "rationale": "Under PARTIAL correctness every Ensures holds vacuously of a "
                     "run that never returns, so without a termination obligation "
                     "this impl VERIFIES. Requires(MustTerminate(3)) at the method "
                     "level plus the per-loop Invariant(MustTerminate(_)) rejects "
                     "it (obligation leak / measure not decreasing). Control "
                     "proving the obligation is load-bearing, not decorative.",
    },
]

# No @ContractOnly axiom soundness/containment probes are scheduled here as
# Docker AXIOM_TESTS because the bundle already carries axiom_check.py (the G-AX
# real-callee check): it runs bytes.decode('latin1') over 0..255 + all 65536
# pairs + 20000 fuzz (the value half of the correspondence == the real decode) and
# the real astropy _pad over 245 lengths incl. the empty=full-record boundary plus
# the text-only TypeError-on-raw-bytes property that grounds text_form /
# pad_runtime. That established check IS the axiom lane for this instance;
# re-encoding it here would duplicate, not strengthen, it. See 'assessment' in the
# structured return.
AXIOM_TESTS = []
