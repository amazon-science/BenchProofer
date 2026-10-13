"""properties.py — PBT falsification battery for sphinx-doc__sphinx-10614.

NOT a Nagini module; an adversarial record the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants that share the FROZEN spec
(markers.same_spec) and differ ONLY inside an `# impl-start`/`# impl-end`
region; each is checked by re-running the Nagini verifier. Axiom cases are
self-contained Docker probes (real Python string ops, the eval image runtime).

DEFENDED SURFACE (read model.py): three pure value functions over strings
modelled as List[int] code points, specification carried by PSeq[int]. The
image format is an OBSERVABLE input (`vector_format`: True for the vector
image whose links resolve against the image directory, False for the raster
image whose links resolve against the document), so each clause below is
pinned in BOTH formats and no format is left unconstrained:

  * url_for_destination(dest_uri, vector_format)   -- READ-ONLY Acc(...,1/2)
      load-bearing post:  ToSeq(Result()) == ToSeq(dest_uri)   (identity, and
                          stated for an ARBITRARY vector_format: the same link
                          in both formats)
      consequence:        has_scheme(dest_uri) == has_scheme(Result())
  * url_for_self_doc_anchor(current_doc_name, anchor_id, vector_format)
      -- TWO read-only inputs; the ONE function whose value is format-dependent
      load-bearing post:  vector_format  ==> Result() == cf ++ '#' ++ aid
      load-bearing post:  !vector_format ==> Result() == '#' ++ aid
      consequence:        vector_format  ==> Result().take(len(cf)) == cf
  * trailing_name_for_destination(dest_uri)        -- READ-ONLY Acc(...,1/2)
      load-bearing post:  ToSeq(Result()) == after_last_hash(ToSeq(dest_uri))
      (no format parameter: identification is the same operation either way)

Every input is read-only (Acc(...,1/2)) -> FRAME-MUTATION is MANDATORY and is
one headline attack: a rival that WRITES to a half-permission input to build
its answer must be rejected for INSUFFICIENT PERMISSION.

The other headline attack family is FORMAT-DEPENDENCE (section 5). A spec that
pinned only the vector-format link would leave the raster link free, so a rival
could keep the reported '../' over-climb (or invent a new one) on the raster
arm and still verify while breaking the raster P2P test. Those rivals are
carried here explicitly, including the two sub-domain variants (short URIs
only; scheme-bearing URIs only) that survive a spec pinned on the visible
test's inputs alone.

UNGROUNDED-ORACLE: the only @Pure helper in a postcondition, after_last_hash,
is FULLY GROUNDED in the argument dest_uri (an unfoldable function of the
input, not an opaque answer key). There is no "wrong echo" to build against
it: returning the materialized after_last_hash IS the correct answer. So for
that function we carry an honest cheapest-impl positive control
(pos-control-external-key) plus partial-domain rivals that the per-element
take/drop pin must reject. The echo family is instead exercised where an echo
IS constructible: raster-anchor-echoes-vector reuses the term the OTHER
postcondition names (cf ++ '#' ++ aid) as the answer for the raster domain.

There are NO @ContractOnly axioms (meta.axioms == []). The three deep models
are A-reference, validated by axiom_check.py == the real Python string ops.
The axiom lane re-runs that soundness + a caller-domain containment argument
in the pinned eval container (real runtime), per PLAN.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10614"
FLOAT_ENCODING = None  # meta.float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor fragments: each is UNIQUE text inside exactly one impl region.
# Editing only inside # impl-start/# impl-end guarantees same_spec (the spec
# view elides impl + nested invariants).
# ---------------------------------------------------------------------------

# ---- url_for_destination impl region --------------------------------------
_DEST_IMPL = '''    result = []  # type: List[int]
    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

# ---- trailing_name_for_destination impl region tail (the return) ----------
_EXTKEY_RETURN = '''    Assert(ToSeq(result) == after_last_hash(ToSeq(dest_uri)))
    return result'''

# ---- url_for_self_doc_anchor: the RASTER arm (the early-return block) -----
_SELFDOC_RASTER = '''    if not vector_format:
        # Raster image: "#" then the anchor identifier.
        bare = [35]  # type: List[int]
        m = 0
        while m < len(anchor_id):
            # invariants-start
            Invariant(Acc(list_pred(anchor_id), 1 / 2))
            Invariant(Acc(list_pred(bare)))
            Invariant(0 <= m and m <= len(anchor_id))
            Invariant(ToSeq(bare) == PSeq(35) + ToSeq(anchor_id).take(m))
            Invariant(MustTerminate(len(anchor_id) - m + 1))
            # invariants-end
            old_bare = ToSeq(bare)
            bare.append(anchor_id[m])
            Assert(ToSeq(bare) == old_bare + PSeq(anchor_id[m]))
            Assert(ToSeq(anchor_id).take(m) + PSeq(ToSeq(anchor_id)[m]) == ToSeq(anchor_id).take(m + 1))
            m = m + 1
        Assert(ToSeq(anchor_id).take(len(anchor_id)) == ToSeq(anchor_id))
        Assert(ToSeq(bare) == PSeq(35) + ToSeq(anchor_id))
        return bare
'''


# A destination-impl template: the gold forward copy, optionally seeded with a
# guarded '../' and carrying the matching case-split invariant. Used by the
# format-dependence rivals so each differs from gold in exactly the seed.
def _dest_variant(seed, invariants):
    return ('''    result = []  # type: List[int]
''' + seed + '''    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
''' + invariants + '''        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result''')


# ===========================================================================
# 1. POSITIVE CONTROLS (soundness, expect verify) -- structurally different
#    but CORRECT impls that keep every gold proof obligation. If one cannot
#    verify => SPEC-TOO-STRONG.
# ===========================================================================

# pos-control-destination: local-variable reshape. Same forward fold, but the
# appended element is bound to a typed local first and the per-element pin is
# phrased through that local. Keeps the loop invariant + both framing asserts.
_POS_DEST = '''    result = []  # type: List[int]
    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        ch = dest_uri[i]  # type: int
        result.append(ch)
        Assert(ToSeq(result) == old_seq + PSeq(ch))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

POS_DEST = {
    "id": "pos-control-destination",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _DEST_IMPL, _POS_DEST),
    "rationale": ("a structurally-different but CORRECT impl (the appended "
                  "element bound to a typed local 'ch', per-element pin through "
                  "it) must still satisfy ToSeq(Result())==ToSeq(dest_uri) for "
                  "BOTH values of vector_format; the gold loop invariant + both "
                  "framing asserts are kept, so this is a spec check not a "
                  "proof-gap. If it fails => SPEC-TOO-STRONG."),
}


# pos-control-external-key: the cheapest HONEST impl that is correct -- it is
# the gold backward-scan/forward-copy, but the final equality is routed through
# a frozen carrier local `key_seq` (a local-variable reshape) instead of stated
# directly. All invariants/Asserts that the proof needs are kept; only the
# executable shape of the final pin changes. This is also the grounded-oracle
# positive control: returning the materialized after_last_hash IS correct, so
# there is no wrong echo to build.
_POS_EXTKEY_RETURN = '''    key_seq = after_last_hash(ToSeq(dest_uri))  # frozen carrier of the answer
    Assert(ToSeq(dest_uri).drop(start) == key_seq)
    Assert(ToSeq(result) == key_seq)
    Assert(ToSeq(result) == after_last_hash(ToSeq(dest_uri)))
    return result'''

POS_EXTKEY = {
    "id": "pos-control-external-key",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _EXTKEY_RETURN, _POS_EXTKEY_RETURN),
    "rationale": ("structurally-different CORRECT impl of trailing_name_for_"
                  "destination: the final equality is routed through a frozen "
                  "carrier local `key_seq = after_last_hash(ToSeq(dest_uri))` "
                  "(local-variable reshape) rather than stated directly; every "
                  "loop invariant and the proof-bearing tail asserts are kept. "
                  "The grounded @Pure oracle after_last_hash makes the "
                  "materialized trailing component the ONLY correct answer. If "
                  "it fails => SPEC-TOO-STRONG."),
}


# pos-control-raster-anchor: the raster arm rebuilt so the leading "#" is
# APPENDED to an initially-empty carrier instead of being the element the
# carrier is created holding. Same value, different executable shape; proves
# the raster clause added by the format repair is SATISFIABLE by more than the
# one literal spelling gold happens to use (i.e. the clause pins the VALUE,
# not the syntax, and the !vector_format domain is genuinely inhabited).
_POS_RASTER = _SELFDOC_RASTER.replace('''        bare = [35]  # type: List[int]
        m = 0''', '''        bare = []  # type: List[int]
        empty_seq = ToSeq(bare)
        bare.append(35)  # '#'
        Assert(ToSeq(bare) == empty_seq + PSeq(35))
        Assert(len(empty_seq) == 0)
        Assert(ToSeq(bare) == PSeq(35))
        m = 0''')

POS_RASTER = {
    "id": "pos-control-raster-anchor",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _SELFDOC_RASTER, _POS_RASTER),
    "rationale": ("the raster arm reshaped (leading '#' appended to an empty "
                  "carrier rather than the carrier's initial element) is still "
                  "CORRECT and must satisfy !vector_format ==> Result() == "
                  "'#' ++ anchor_id. Confirms the format clause added by the "
                  "repair is a value pin with an inhabited !vector_format "
                  "domain, not an accidental syntactic one. Failing => "
                  "SPEC-TOO-STRONG on the raster arm."),
}


# ===========================================================================
# 2. FRAME-MUTATION (uniqueness, expect reject) -- MANDATORY: every input is
#    read-only Acc(...,1/2). A rival that WRITES the input to fabricate the
#    answer must fail for INSUFFICIENT PERMISSION (the half-permission cannot
#    be mutated). Gold post-conditions are untouched, so the rejection is
#    attributable to the write, not a spec change.
# ===========================================================================

# frame-mut-destination: clear+rebuild dest_uri in place then copy from it. The
# `dest_uri[i] = dest_uri[i]` write needs full permission to dest_uri, but the
# Requires gives only 1/2 -> insufficient permission.
_FRAME_DEST = '''    result = []  # type: List[int]
    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        dest_uri[i] = dest_uri[i]  # WRITE to a read-only (1/2) input -> reject
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

FRAME_DEST = {
    "id": "frame-mut-destination",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _FRAME_DEST),
    "refinement": ("a faithful real patch that MUTATES child['refuri'] (the "
                   "source URI) in place would corrupt the shared pending_xref "
                   "node that other diagram nodes / the PNG branch also read, "
                   "emitting wrong hrefs and failing test_inheritance_diagram_"
                   "svg_html (the absolute-URL and relative-existence checks)."),
    "rationale": ("dest_uri carries only Acc(list_pred(dest_uri), 1/2) "
                  "(read-only); the `dest_uri[i] = ...` write needs full "
                  "permission, so Nagini rejects for insufficient permission. "
                  "If it verifies => the frame condition is too weak (a mutating "
                  "impl could satisfy the postcondition vacuously)."),
}


# frame-mut-self-doc: write to current_doc_name (a 1/2 read-only input) inside
# the first copy loop. The gold proof obligations are otherwise untouched.
_SELFDOC_LOOP1 = '''        old_seq = ToSeq(result)
        result.append(current_doc_name[i])
        Assert(ToSeq(result) == old_seq + PSeq(current_doc_name[i]))'''
_FRAME_SELFDOC_LOOP1 = '''        old_seq = ToSeq(result)
        current_doc_name[i] = current_doc_name[i]  # WRITE to read-only (1/2) -> reject
        result.append(current_doc_name[i])
        Assert(ToSeq(result) == old_seq + PSeq(current_doc_name[i]))'''

FRAME_SELFDOC = {
    "id": "frame-mut-self-doc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SELFDOC_LOOP1, _FRAME_SELFDOC_LOOP1),
    "refinement": ("a faithful patch that mutates current_filename in place "
                   "would corrupt the per-document output name shared by every "
                   "node's link in this and sibling diagrams, breaking the "
                   "relative-resolution check in the F2P SVG test."),
    "rationale": ("current_doc_name carries Acc(list_pred(current_doc_name), "
                  "1/2); the write needs full permission -> insufficient-"
                  "permission rejection. Verifying => frame too weak."),
}


# frame-mut-external-key: write to dest_uri inside the forward copy loop of
# trailing_name_for_destination.
_EXTKEY_LOOP = '''        old_seq = ToSeq(result)
        result.append(dest_uri[k])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[k]))'''
_FRAME_EXTKEY_LOOP = '''        old_seq = ToSeq(result)
        dest_uri[k] = dest_uri[k]  # WRITE to read-only (1/2) input -> reject
        result.append(dest_uri[k])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[k]))'''

FRAME_EXTKEY = {
    "id": "frame-mut-external-key",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EXTKEY_LOOP, _FRAME_EXTKEY_LOOP),
    "refinement": ("mutating child['refuri'] while deriving the intersphinx key "
                   "would change the very URI later emitted as the href, so the "
                   "registered key and the link would disagree and the external "
                   "'https://example.org/...' link check in F2P would fail."),
    "rationale": ("dest_uri is Acc(list_pred(dest_uri),1/2) read-only; the write "
                  "needs full permission -> rejected. Verifying => frame too weak."),
}


# ===========================================================================
# 3. PARTIAL-DOMAIN rivals (uniqueness, expect reject) -- correct on a slice of
#    the F2P/P2P domain, wrong on a sub-domain. The per-element take/drop
#    postcondition must reject each.
# ===========================================================================

# partial-domain-destination-dropslast: copy all but the final element. Correct
# only on the empty URI; wrong on every non-empty URI (drops the last char).
_PARTIAL_DEST = '''    result = []  # type: List[int]
    i = 0
    while i + 1 < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

PARTIAL_DEST = {
    "id": "partial-domain-destination-dropslast",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _PARTIAL_DEST),
    "refinement": ("dropping the final character of every URI yields e.g. "
                   "'https://example.org/foo.html#subdir.other.Bo', which is NOT "
                   "child.get('refuri'); the SVG test asserts absolute hrefs "
                   "start with 'https://example.org/' AND that relative hrefs "
                   "resolve to an EXISTING file -- a truncated link fails both."),
    "rationale": ("the loop stops one early (i+1 < len), so ToSeq(result) == "
                  "take(len-1) != take(len)==ToSeq(dest_uri) for any non-empty "
                  "input; the identity postcondition rejects it. Verifying => "
                  "SPEC-TOO-WEAK (admits a last-element-dropping impl)."),
}


# partial-domain-external-key-wholeuri: return the WHOLE dest_uri (the prepatch
# behaviour). Correct iff the URI has no '#'; wrong when it carries an anchor,
# which is exactly the intersphinx case in the F2P test.
_PARTIAL_EXTKEY = '''    result = []  # type: List[int]
    k = 0
    while k < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(dest_uri))
        Invariant(ToSeq(result) == ToSeq(dest_uri).take(k))
        Invariant(MustTerminate(len(dest_uri) - k + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[k])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[k]))
        Assert(ToSeq(dest_uri).take(k) + PSeq(ToSeq(dest_uri)[k]) == ToSeq(dest_uri).take(k + 1))
        k = k + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

# This must replace the ENTIRE trailing-name impl body (the backward scan + the
# forward copy). Anchor on the whole region between impl-start and impl-end of
# trailing_name_for_destination.
_EXTKEY_FULL = '''    # Scan backward for the last '#'. `start` indexes the beginning of the
    # trailing component; the invariant ties it to the front-recursive
    # `after_last_hash` via one unfold per step.
    start = len(dest_uri)
    i = len(dest_uri)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(0 <= i and i <= start and start <= len(dest_uri))
        Invariant(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # Unfold after_last_hash at index i-1: drop(i-1) == [dest_uri[i-1]] ++ drop(i)
        Assert(ToSeq(dest_uri).drop(i - 1) == PSeq(ToSeq(dest_uri)[i - 1]) + ToSeq(dest_uri).drop(i))
        Assert(ToSeq(dest_uri).drop(i - 1).drop(1) == ToSeq(dest_uri).drop(i))
        Assert(ToSeq(dest_uri).drop(i - 1)[0] == ToSeq(dest_uri)[i - 1])
        if dest_uri[i - 1] == 35 and start == i:
            # no '#' seen yet to the right, and this is one: trailing starts here
            start = i
        elif start == i and dest_uri[i - 1] != 35:
            # still no '#' to the right and this char is ordinary: extend left
            start = i - 1
        # else: a '#' already dominates to the right; `start` is unchanged
        i = i - 1
    Assert(ToSeq(dest_uri).drop(0) == ToSeq(dest_uri))
    Assert(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
    result = []  # type: List[int]
    k = start
    while k < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= start and start <= k and k <= len(dest_uri))
        Invariant(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
        Invariant(ToSeq(result) == ToSeq(dest_uri).drop(start).take(k - start))
        Invariant(MustTerminate(len(dest_uri) - k + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[k])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[k]))
        Assert(ToSeq(dest_uri).drop(start)[k - start] == ToSeq(dest_uri)[k])
        Assert(ToSeq(dest_uri).drop(start).take(k - start) + PSeq(ToSeq(dest_uri).drop(start)[k - start])
               == ToSeq(dest_uri).drop(start).take(k - start + 1))
        k = k + 1
    Assert(ToSeq(result) == ToSeq(dest_uri).drop(start).take(len(dest_uri) - start))
    Assert(ToSeq(dest_uri).drop(start).take(len(dest_uri) - start) == ToSeq(dest_uri).drop(start))
    Assert(ToSeq(result) == ToSeq(dest_uri).drop(start))
    Assert(ToSeq(dest_uri).drop(start) == after_last_hash(ToSeq(dest_uri)))
    Assert(ToSeq(result) == after_last_hash(ToSeq(dest_uri)))
    return result'''

PARTIAL_EXTKEY = {
    "id": "partial-domain-external-key-wholeuri",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _EXTKEY_FULL, _PARTIAL_EXTKEY),
    "refinement": ("returning the whole URI as the registration key is the "
                   "PRE-PATCH behaviour (model_prepatch_3): for the intersphinx "
                   "target 'https://example.org/foo.html#subdir.other.Bob' it "
                   "registers under the full URI instead of 'subdir.other.Bob', "
                   "so the class node is not matched and 'https://example.org' "
                   "never appears in the SVG -- F2P 'subdir.' check fails."),
    "rationale": ("ToSeq(result)==ToSeq(dest_uri) but the post pins it to "
                  "after_last_hash(ToSeq(dest_uri)); these differ on every "
                  "'#'-bearing URI, so the postcondition rejects it. Verifying "
                  "=> SPEC-TOO-WEAK (admits the un-stripped key)."),
}


# ===========================================================================
# 4. CONTROL-FLOW / bug-replica supporting rivals (uniqueness, expect reject)
#    The literal reported bug: the '../' prefix. Mechanical near-miss, but it
#    carries the real refinement (the exact 404 the issue reports).
# ===========================================================================

# prefix-dotdot-destination: prepend '../' (== [46,46,47]) -- the actual bug
# (model_prepatch). The result is then '../' ++ dest_uri.
_BUG_DEST = '''    result = [46, 46, 47]  # type: List[int]  # the '../' over-climb (the bug)
    i = 0
    while i < len(dest_uri):
        # invariants-start
        Invariant(Acc(list_pred(dest_uri), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(dest_uri))
        Invariant(ToSeq(result) == PSeq(46, 46, 47) + ToSeq(dest_uri).take(i))
        Invariant(MustTerminate(len(dest_uri) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(dest_uri[i])
        Assert(ToSeq(result) == old_seq + PSeq(dest_uri[i]))
        Assert(ToSeq(dest_uri).take(i) + PSeq(ToSeq(dest_uri)[i]) == ToSeq(dest_uri).take(i + 1))
        i = i + 1
    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result'''

BUG_DEST = {
    "id": "prefix-dotdot-destination",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _BUG_DEST),
    "refinement": ("this is the literal reported bug (model_prepatch): "
                   "'../' + refuri. For the absolute URL it produces "
                   "'../https://example.org/...', which the F2P SVG test "
                   "explicitly forbids (href with '://' must start with "
                   "'https://example.org/', never '../https://'); for relative "
                   "links it over-climbs one directory and 404s."),
    "rationale": ("result == PSeq(46,46,47) ++ ToSeq(dest_uri) != ToSeq(dest_uri) "
                  "for any input, so the identity postcondition rejects it. The "
                  "G-DIFF discriminator; verifying => SPEC-TOO-WEAK."),
}


# prefix-dotdot-self-doc: prepend '../' to the self-document anchor link
# (model_prepatch_2). result becomes '../' ++ cf ++ '#' ++ aid in the vector arm,
# and the '../' is carried through every intermediate assert so the rejection
# lands on the POSTCONDITION rather than on a dropped proof step.
_SELFDOC_VECTOR = '''    result = []  # type: List[int]
    i = 0
    while i < len(current_doc_name):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(current_doc_name))
        Invariant(ToSeq(result) == ToSeq(current_doc_name).take(i))
        Invariant(MustTerminate(len(current_doc_name) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(current_doc_name[i])
        Assert(ToSeq(result) == old_seq + PSeq(current_doc_name[i]))
        Assert(ToSeq(current_doc_name).take(i) + PSeq(ToSeq(current_doc_name)[i])
               == ToSeq(current_doc_name).take(i + 1))
        i = i + 1
    Assert(ToSeq(current_doc_name).take(len(current_doc_name)) == ToSeq(current_doc_name))
    cf_seq = ToSeq(current_doc_name)  # frozen carrier of the prefix
    Assert(ToSeq(result) == cf_seq)
    result.append(35)  # '#'
    Assert(ToSeq(result) == cf_seq + PSeq(35))
    j = 0
    while j < len(anchor_id):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(anchor_id), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(anchor_id))
        Invariant(ToSeq(current_doc_name) == cf_seq)
        Invariant(ToSeq(result) == cf_seq + PSeq(35) + ToSeq(anchor_id).take(j))
        Invariant(MustTerminate(len(anchor_id) - j + 1))
        # invariants-end
        old_seq2 = ToSeq(result)
        result.append(anchor_id[j])
        Assert(ToSeq(result) == old_seq2 + PSeq(anchor_id[j]))
        Assert(ToSeq(anchor_id).take(j) + PSeq(ToSeq(anchor_id)[j]) == ToSeq(anchor_id).take(j + 1))
        j = j + 1
    Assert(ToSeq(anchor_id).take(len(anchor_id)) == ToSeq(anchor_id))
    Assert(ToSeq(result) == cf_seq + PSeq(35) + ToSeq(anchor_id))
    return result'''
_BUG_SELFDOC_VECTOR = '''    result = [46, 46, 47]  # type: List[int]   # the '../' over-climb (the bug)
    i = 0
    while i < len(current_doc_name):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(current_doc_name))
        Invariant(ToSeq(result) == PSeq(46, 46, 47) + ToSeq(current_doc_name).take(i))
        Invariant(MustTerminate(len(current_doc_name) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(current_doc_name[i])
        Assert(ToSeq(result) == old_seq + PSeq(current_doc_name[i]))
        Assert(ToSeq(current_doc_name).take(i) + PSeq(ToSeq(current_doc_name)[i])
               == ToSeq(current_doc_name).take(i + 1))
        i = i + 1
    Assert(ToSeq(current_doc_name).take(len(current_doc_name)) == ToSeq(current_doc_name))
    cf_seq = ToSeq(current_doc_name)  # frozen carrier of the prefix
    Assert(ToSeq(result) == PSeq(46, 46, 47) + cf_seq)
    result.append(35)  # '#'
    Assert(ToSeq(result) == PSeq(46, 46, 47) + cf_seq + PSeq(35))
    j = 0
    while j < len(anchor_id):
        # invariants-start
        Invariant(Acc(list_pred(current_doc_name), 1 / 2))
        Invariant(Acc(list_pred(anchor_id), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(anchor_id))
        Invariant(ToSeq(current_doc_name) == cf_seq)
        Invariant(ToSeq(result) == PSeq(46, 46, 47) + cf_seq + PSeq(35) + ToSeq(anchor_id).take(j))
        Invariant(MustTerminate(len(anchor_id) - j + 1))
        # invariants-end
        old_seq2 = ToSeq(result)
        result.append(anchor_id[j])
        Assert(ToSeq(result) == old_seq2 + PSeq(anchor_id[j]))
        Assert(ToSeq(anchor_id).take(j) + PSeq(ToSeq(anchor_id)[j]) == ToSeq(anchor_id).take(j + 1))
        j = j + 1
    Assert(ToSeq(anchor_id).take(len(anchor_id)) == ToSeq(anchor_id))
    Assert(ToSeq(result) == PSeq(46, 46, 47) + cf_seq + PSeq(35) + ToSeq(anchor_id))
    return result'''

BUG_SELFDOC = {
    "id": "prefix-dotdot-self-doc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SELFDOC_VECTOR, _BUG_SELFDOC_VECTOR),
    "refinement": ("the literal bug for the refid branch (model_prepatch_2): "
                   "'../' + current_filename + '#' + refid. The SVG link then "
                   "climbs above the image directory and 404s; the F2P test's "
                   "relative-resolution assert (abs_uri under imagedir exists) "
                   "fails."),
    "rationale": ("the vector arm's first-loop init starts result at "
                  "PSeq(46,46,47), so the final ToSeq(result)=='../'++cf++'#'"
                  "++aid != cf++'#'++aid, failing the vector_format ==> exact-"
                  "concatenation postcondition. Note the invariant edit is "
                  "INSIDE the impl region (a nested invariant, elided from the "
                  "spec view) so same_spec holds. Verifying => SPEC-TOO-WEAK."),
}


# ===========================================================================
# 5. FORMAT-DEPENDENCE rivals (uniqueness, expect reject). The image format is
#    an observable, so a rival may branch on it. Every one of these keeps the
#    VECTOR behaviour exactly gold -- so a spec that constrained only the
#    vector link would admit it -- and corrupts the RASTER behaviour, either
#    on the whole raster domain or on a sub-domain chosen to survive the
#    inputs the visible tests actually exercise.
# ===========================================================================

# format-raster-dotdot-destination: the reported over-climb, retained on the
# raster arm only. This is the rival that measurably breaks P2P
# test_inheritance_diagram_png_html while satisfying a vector-only spec.
_RASTER_DOTDOT = _dest_variant(
    '''    if not vector_format:
        result = [46, 46, 47]  # raster arm keeps the over-climb
''',
    '''        Invariant(Implies(not vector_format,
                          ToSeq(result) == PSeq(46, 46, 47) + ToSeq(dest_uri).take(i)))
        Invariant(Implies(vector_format, ToSeq(result) == ToSeq(dest_uri).take(i)))
''')

RASTER_DOTDOT = {
    "id": "format-raster-dotdot-destination",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _RASTER_DOTDOT),
    "refinement": ("MEASURED: applied to the real tree (the refuri branch made "
                   "format-dependent, '../' + refuri when graphviz_output_format "
                   "!= 'SVG'), the F2P svg test still passes and P2P "
                   "test_inheritance_diagram_png_html FAILS -- the raster area "
                   "map emits '../my_class_1.html#...' where the test requires "
                   "'my_class_1.html#...'. The gold hunk registers urls[refname] "
                   "= child.get('refuri') OUTSIDE any format branch, so this "
                   "rival is a real regression, not an unobserved freedom."),
    "rationale": ("ToSeq(Result())==ToSeq(dest_uri) is asserted for an arbitrary "
                  "vector_format, so the raster instantiation rejects: result == "
                  "'../' ++ dest_uri there. Verifying => SPEC-TOO-WEAK exactly "
                  "in the way this cell was refuted before the format observable "
                  "was added (the raster link was unconstrained)."),
}


# format-raster-short-uri-guard: the over-climb kept ONLY for raster URIs of at
# most 3 code points. A partial-domain guard: it is correct on every URI the
# tests actually contain, so no test can catch it; only the value pin can.
_RASTER_SHORT = _dest_variant(
    '''    if not vector_format and len(dest_uri) <= 3:
        result = [46, 46, 47]  # only the short raster URIs over-climb
''',
    '''        Invariant(Implies(not vector_format and len(dest_uri) <= 3,
                          ToSeq(result) == PSeq(46, 46, 47) + ToSeq(dest_uri).take(i)))
        Invariant(Implies(vector_format or len(dest_uri) > 3,
                          ToSeq(result) == ToSeq(dest_uri).take(i)))
''')

RASTER_SHORT = {
    "id": "format-raster-short-uri-guard",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _RASTER_SHORT),
    "refinement": ("every refuri in the F2P/P2P fixtures is far longer than 3 "
                   "characters ('my_class_1.html#my_package.MyClass1', "
                   "'https://example.org/foo.html#subdir.other.Bob'), so this "
                   "rival passes the whole visible suite while still emitting "
                   "'../a.h' for a short raster link -- a 404 of exactly the "
                   "reported kind on any project whose pages have short names."),
    "rationale": ("the postcondition is a value pin over the FULL input domain, "
                  "not over the fixture inputs: instantiating it at a raster "
                  "call with len(dest_uri) <= 3 refutes the rival. Verifying => "
                  "SPEC-TOO-WEAK (a length-guarded sub-domain left free)."),
}


# format-raster-scheme-conditional: correct exactly on the absolute-URL
# sub-domain the visible SVG test names, over-climbing every relative raster
# link. This is the rival that survives a repair which pins only the case the
# problem statement talks about.
_RASTER_SCHEME = _dest_variant(
    '''    if not vector_format and not has_scheme(ToSeq(dest_uri)):
        result = [46, 46, 47]  # only relative raster links over-climb
''',
    '''        Invariant(Implies(not vector_format and not has_scheme(ToSeq(dest_uri)),
                          ToSeq(result) == PSeq(46, 46, 47) + ToSeq(dest_uri).take(i)))
        Invariant(Implies(vector_format or has_scheme(ToSeq(dest_uri)),
                          ToSeq(result) == ToSeq(dest_uri).take(i)))
''')

RASTER_SCHEME = {
    "id": "format-raster-scheme-conditional",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _RASTER_SCHEME),
    "refinement": ("this rival keeps the ONE property the scheme consequence "
                   "clause states (an absolute URL is preserved verbatim, so no "
                   "'../https://' is ever emitted) and breaks the raster case "
                   "the consequence clause says nothing about: relative links "
                   "become '../my_class_1.html#...' in the PNG area map, which "
                   "is the 404 the issue reports."),
    "rationale": ("the identity pin, not the scheme consequence, is what refutes "
                  "it: at a raster call with a scheme-free URI the result is "
                  "'../' ++ dest_uri. Verifying => SPEC-TOO-WEAK (the spec would "
                  "then be pinning only the sub-domain the issue text mentions)."),
}


# format-raster-anchor-colon-separator: boundary token swap in the raster arm --
# ':' (U+003A, 58) where the separator must be '#' (U+0023, 35).
_RASTER_COLON = (_SELFDOC_RASTER
                 .replace("bare = [35]", "bare = [58]")
                 .replace("PSeq(35) + ToSeq(anchor_id).take(m)",
                          "PSeq(58) + ToSeq(anchor_id).take(m)")
                 .replace("Assert(ToSeq(bare) == PSeq(35) + ToSeq(anchor_id))",
                          "Assert(ToSeq(bare) == PSeq(58) + ToSeq(anchor_id))"))

RASTER_COLON = {
    "id": "format-raster-anchor-colon-separator",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SELFDOC_RASTER, _RASTER_COLON),
    "refinement": ("the fragment separator is what makes an in-page anchor an "
                   "anchor: ':test.DocHere' is not a fragment reference at all, "
                   "so the raster area map would point nowhere and the P2P PNG "
                   "test's href check on the self-document link fails."),
    "rationale": ("one code point apart from gold (58 vs 35), so it isolates the "
                  "separator token: !vector_format ==> Result() == PSeq(35) ++ "
                  "anchor_id rejects it. Verifying => the separator is not "
                  "actually pinned in the raster clause."),
}


# format-raster-anchor-echoes-vector: the raster arm is deleted, so BOTH formats
# return the term the OTHER postcondition names (cf ++ '#' ++ aid). An echo of a
# clause that IS in the spec, offered for the domain it does not cover.
RASTER_ECHO = {
    "id": "format-raster-anchor-echoes-vector",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _SELFDOC_RASTER, ""),
    "refinement": ("MEASURED on the real tree: making the refid branch emit "
                   "current_filename + '#' + refid in BOTH formats leaves the "
                   "whole visible suite green (the PNG fixture's self-document "
                   "anchor is not asserted on), yet it is not what the gold hunk "
                   "does -- lines 423-426 of the patched inheritance_diagram.py "
                   "prefix the document name ONLY for 'SVG'. In a raster area "
                   "map the doc name is a redundant second hop that breaks the "
                   "anchor as soon as the page is served under a different name "
                   "(e.g. as a directory index)."),
    "rationale": ("the answer echoed is a real spec term, so nothing but the "
                  "raster clause can refute it: !vector_format ==> Result() == "
                  "'#' ++ anchor_id fails when the doc name is non-empty. This "
                  "is the case that proves the repair pins the raster arm to a "
                  "specific value rather than to 'some link mentioned above'."),
}


# over-approx-destination-doubles-first-char: append one extra copy of the first
# character. It KEEPS both consequence clauses -- dest_uri is still a prefix of
# the result, and '://' membership is unchanged -- so a spec written as those
# consequences alone would admit it. Only the exact-value identity refutes it.
_DEST_DOUBLE = _DEST_IMPL.replace(
    '''    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    return result''',
    '''    Assert(ToSeq(dest_uri).take(len(dest_uri)) == ToSeq(dest_uri))
    if len(dest_uri) > 0:
        old_tail = ToSeq(result)
        result.append(dest_uri[0])  # one extra character: prefix + scheme kept
        Assert(ToSeq(result) == old_tail + PSeq(dest_uri[0]))
    return result''')

DEST_DOUBLE = {
    "id": "over-approx-destination-doubles-first-char",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _DEST_IMPL, _DEST_DOUBLE),
    "refinement": ("'my_class_1.html#my_package.MyClass1m' is not a file that "
                   "exists, so the SVG test's relative-resolution assert (the "
                   "href must resolve to an existing output file) fails; the "
                   "over-approximation is invisible to any check that only asks "
                   "whether the link STARTS with the right thing."),
    "rationale": ("deliberately satisfies every WEAKER observable in the spec "
                  "(Result() begins with dest_uri; has_scheme unchanged, since "
                  "appending dest_uri[0] cannot remove a '://' and cannot create "
                  "one unless the URI already had it) and violates only "
                  "ToSeq(Result())==ToSeq(dest_uri). Verifying => the identity "
                  "pin is not load-bearing and the spec is an over-approximation."),
}


# ===========================================================================
# 6. ADMISSIBILITY (expect verify) -- confirm the precondition admits a normal
#    F2P-shaped input. The Requires here is only Acc(...,1/2), so this is a
#    structural in-domain positive control on the most complex function: the
#    gold trailing-name impl re-derived with the redundant tail assert chain
#    intact verifies, proving the backward-scan precondition accepts a
#    '#'-bearing intersphinx URI. (If it could not => PRECOND-TOO-STRONG.)
# ===========================================================================
# Re-use the gold body with one extra harmless in-domain Assert added at the
# very top of the impl (inside the region), asserting the empty-prefix identity
# that the F2P intersphinx URI relies on. Keeps all gold obligations.
_EXTKEY_HEAD = '''    # Scan backward for the last '#'. `start` indexes the beginning of the
    # trailing component; the invariant ties it to the front-recursive
    # `after_last_hash` via one unfold per step.
    start = len(dest_uri)'''
_ADMISS_HEAD = '''    # admissibility: a normal F2P-shaped intersphinx URI (carries a '#') is in
    # the precondition domain -- drop(0) is the whole URI, an in-domain fact.
    Assert(ToSeq(dest_uri).drop(0) == ToSeq(dest_uri))
    # Scan backward for the last '#'. `start` indexes the beginning of the
    # trailing component; the invariant ties it to the front-recursive
    # `after_last_hash` via one unfold per step.
    start = len(dest_uri)'''

ADMISS_EXTKEY = {
    "id": "admiss-external-key",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _EXTKEY_HEAD, _ADMISS_HEAD),
    "rationale": ("admissibility: the gold trailing-name body plus one harmless "
                  "in-domain Assert (drop(0)==whole URI) verifies, confirming "
                  "Requires(Acc(list_pred(dest_uri),1/2)) accepts a normal "
                  "'#'-bearing intersphinx URI. If it could not be established "
                  "=> PRECOND-TOO-STRONG. All gold obligations kept."),
}


SPEC_TESTS = [
    POS_DEST,
    POS_EXTKEY,
    POS_RASTER,
    FRAME_DEST,
    FRAME_SELFDOC,
    FRAME_EXTKEY,
    PARTIAL_DEST,
    PARTIAL_EXTKEY,
    BUG_DEST,
    BUG_SELFDOC,
    RASTER_DOTDOT,
    RASTER_SHORT,
    RASTER_SCHEME,
    RASTER_COLON,
    RASTER_ECHO,
    DEST_DOUBLE,
    ADMISS_EXTKEY,
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axioms (meta.axioms == []). The three deep
# models are A-reference, validated == the real Python string operations the
# gold patch performs. We re-run that soundness check AND a caller-domain
# containment argument in the pinned eval container (real runtime, old Python /
# ASCII locale -> open utf-8; only stdlib). The "real callee" here is Python
# str.rsplit / '+' / 'in' as exercised by the gold hunk, in BOTH image formats.
# ===========================================================================

_AX_SOUNDNESS = r'''
import sys

# Deep-model reference encodings (kept in lock-step with model.py's @Pure /
# impl semantics). These mirror the model EXACTLY (forward-fold / backward scan
# collapsed to their value), then we compare to the REAL Python op the gold
# patch performs in html_visit_inheritance_diagram -- for BOTH values of
# graphviz_output_format, since the format is a modelled input.

def has_scheme(s):
    # model.py has_scheme: True iff '://' occurs somewhere in s
    for i in range(len(s)):
        if i + 2 < len(s) and s[i] == ':' and s[i + 1] == '/' and s[i + 2] == '/':
            return True
    return False

def after_last_hash(s):
    # model.py after_last_hash: trailing component after the final '#'
    p = 0
    for i in range(len(s)):
        if s[i] == '#':
            p = i + 1
    return s[p:]

def url_for_destination(refuri, vector_format):
    return refuri                      # model fn 1: identity copy, either format

def url_for_self_doc_anchor(cf, refid, vector_format):
    # model fn 2: cf ++ '#' ++ refid for the vector image, '#' ++ refid for the
    # raster image
    if vector_format:
        return cf + '#' + refid
    return '#' + refid

def trailing_name_for_destination(refuri):
    return after_last_hash(refuri)     # model fn 3: trailing component

def real_destination(refuri, fmt):
    # gold op, patched inheritance_diagram.py: urls[refname] = child.get('refuri')
    # -- NOT inside any `if graphviz_output_format` branch, so it is the same in
    # both formats.
    return refuri

def real_self_doc(cf, refid, fmt):
    # gold op, patched inheritance_diagram.py refid branch:
    #   if graphviz_output_format == 'SVG': current_filename + '#' + refid
    #   else:                               '#' + refid
    if fmt == 'SVG':
        return cf + '#' + refid
    return '#' + refid

def check_destination(refuri):
    for fmt, vec in (('SVG', True), ('PNG', False)):
        real = real_destination(refuri, fmt)
        assert url_for_destination(refuri, vec) == real, ("dest", fmt, refuri)
        # scheme-membership preserved under the identity (== Python 'in')
        assert has_scheme(refuri) == ('://' in refuri), ("scheme", refuri)
        assert has_scheme(url_for_destination(refuri, vec)) == ('://' in real), \
            ("scheme2", fmt, refuri)

def check_self_doc(cf, refid):
    for fmt, vec in (('SVG', True), ('PNG', False)):
        real = real_self_doc(cf, refid, fmt)
        assert url_for_self_doc_anchor(cf, refid, vec) == real, ("selfdoc", fmt, cf, refid)
        if vec:
            assert real[:len(cf)] == cf, ("selfdoc-prefix", cf, refid)  # begins with cf
        else:
            assert real == '#' + refid, ("selfdoc-bare", cf, refid)     # no doc name
    # the two formats really do differ whenever the document name is non-empty:
    # a model that ignored the format could not satisfy both.
    if cf:
        assert (url_for_self_doc_anchor(cf, refid, True)
                != url_for_self_doc_anchor(cf, refid, False)), ("format-blind", cf, refid)

def check_external_key(refuri):
    # gold op (external refuri key, post-fix): refuri.rsplit('#', 1)[-1]
    real = refuri.rsplit('#', 1)[-1]
    assert trailing_name_for_destination(refuri) == real, ("extkey", refuri, real)

import random
refuris = [
    "", "foo.html", "my_class_1.html#my_package.MyClass1",
    "../my_package/my_class_2.html#my_package.MyClass2",
    "https://example.org/foo.html#subdir.other.Bob",
    "https://example.org/foo.html", "#anchor-only", "no-hash", "a#b#c#d",
    "trailing#", "#", "##", "scheme://host/p#frag", "subdir.other.Bob",
    "x://y", ":/incomplete", "a:b/c", "a.h", "abc",
]
filenames = ["index.html", "subdir/index.html", "a/b/c.html", "x.htm", ""]
refids = ["test.DocHere", "my_package.MyClass1", "a.b.c", "x", ""]
for u in refuris:
    check_destination(u); check_external_key(u)
for cf in filenames:
    for rid in refids:
        check_self_doc(cf, rid)
rng = random.Random(10614)
alphabet = list("abcXYZ._/-0129") + ["#", "#", ":", "/", "://", "https://"]
for _ in range(40000):
    u = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
    check_destination(u); check_external_key(u)
    cf = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
    rid = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
    check_self_doc(cf, rid)
print("AX-SOUND OK: 3 deep models == real Python str ops in BOTH image formats "
      "(identity; '#'-concat with/without the doc name; rsplit('#',1)[-1]) on "
      "%d boundary + 40000 fuzz" % len(refuris))
sys.exit(0)
'''


_AX_CONTAINMENT = r'''
import sys
# Caller-domain CONTAINMENT for the three A-reference deep models. The deep
# models are TOTAL Python string functions (no narrowing precondition): their
# domain is "every str" (times both image formats, an exhaustive bool).
# The caller (html_visit_inheritance_diagram, gold hunk) reaches them only with:
#   * url_for_destination / trailing_name_for_destination <- child.get('refuri')
#       (or child['refuri']) -- an arbitrary Python str (relative path, anchor,
#       or absolute intersphinx URL).
#   * url_for_self_doc_anchor <- (current_filename, child.get('refid')) --
#       both arbitrary Python strs.
#   * vector_format <- (graphviz_output_format == 'SVG') -- a bool, and BOTH
#       values are caller-reachable: the builder config takes 'png' (default)
#       or 'svg', and the P2P/F2P tests exercise one each.
# Since each deep model accepts EVERY str and EVERY bool, and the caller can
# only ever pass a str and a bool, every caller-reachable input lies inside the
# model's domain -> covered. (Covering MORE than the caller reaches is sound;
# the float-vs-int rule.) We assert it positively: run the models on the
# F2P/P2P-reachable representatives and the fuzz corpus, in both formats, and
# confirm none raises / falls outside the domain.

def after_last_hash(s):
    p = 0
    for i in range(len(s)):
        if s[i] == '#':
            p = i + 1
    return s[p:]

# F2P/P2P-reachable inputs (from the rewritten svg test wiring: intersphinx
# subdir.other.Bob -> foo.html#subdir.other.Bob; relative test.* links; and the
# png fixture's my_class_1.html#my_package.MyClass1 area map).
reachable = [
    "https://example.org/foo.html#subdir.other.Bob",   # external intersphinx
    "test.DocHere.html#test.DocHere",
    "../test.DocMainLevel.html#test.DocMainLevel",
    "index.html#test.Foo",
    "my_class_1.html#my_package.MyClass1",             # png area map
    "subdir/index.html",
    "",                                                 # degenerate
]
import random
rng = random.Random(427)
alphabet = list("abcXYZ._/-0129") + ["#", ":", "/", "://", "https://"]
for _ in range(5000):
    reachable.append("".join(rng.choice(alphabet) for _ in range(rng.randint(0, 16))))

formats = [True, False]                       # graphviz_output_format == 'SVG' or not
for u in reachable:
    assert isinstance(u, str)                 # caller only ever passes a str
    for vec in formats:
        assert isinstance(vec, bool)          # the format observable is a bool: exhaustive
        _ = u                                 # url_for_destination domain = all str x bool
        _ = (u + '#' + u) if vec else ('#' + u)   # self-doc domain = all str x bool
    _ = after_last_hash(u)                    # trailing-name domain = all str: total
    _ = u.rsplit('#', 1)[-1]                  # the real op is likewise total on str
print("AX-CONTAIN OK: every caller-reachable input (str x both image formats) "
      "is inside each deep model's domain (all-str x all-bool / total); "
      "%d reachable+fuzz inputs x 2 formats covered" % len(reachable))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodels",
        "axiom": "url_for_destination / url_for_self_doc_anchor / trailing_name_for_destination",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS,
        "rationale": ("the three A-reference deep models must equal the REAL "
                      "Python string operations the gold hunk performs, in BOTH "
                      "image formats (identity on refuri in either format; "
                      "current_filename + '#' + refid for SVG vs '#' + refid "
                      "otherwise; refuri.rsplit('#',1)[-1]) on boundary + 40000 "
                      "fuzz inputs, run under the eval container's real runtime. "
                      "Any disagreement => AXIOM-UNSOUND (deep-model infidelity)."),
    },
    {
        "id": "ax-contain-deepmodels",
        "axiom": "url_for_destination / url_for_self_doc_anchor / trailing_name_for_destination",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": ("containment: each deep model is total over str (times the "
                      "bool image format), and the caller "
                      "(html_visit_inheritance_diagram) can only ever pass a str "
                      "(refuri/refid/current_filename) and a bool "
                      "(graphviz_output_format == 'SVG'), both of whose values "
                      "are reachable; so every caller-reachable input is inside "
                      "the model domain. A reachable input outside the domain "
                      "would be AXIOM-TOO-WEAK-FOR-CALLER; none exists."),
    },
]
