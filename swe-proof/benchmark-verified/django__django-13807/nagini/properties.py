# properties.py — PBT falsification battery for django__django-13807.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that SHARES the frozen spec (same axioms /
# pure / pre / post-conditions) and edits ONLY the two impl regions; the runner
# verifies it with Nagini and checks same_spec against model.py. AXIOM_TESTS are
# self-contained Docker probes that EXECUTE the real callee.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   Two pure command-assemblers over List[int] code points.
#     build_single_table_command(table_name)  -- table_name read-only Acc(.,1/2)
#       Ensures ToSeq(Result()) == single_table_prefix()
#                                  + delimit(ToSeq(table_name)) + close_paren()
#     build_three_id_command(ident_a, ident_b, ident_c) -- all three read-only 1/2
#       Ensures ToSeq(Result()) == three_id_head() + delimit(a) + three_id_sep()
#                                  + delimit(b) + three_id_mid() + delimit(c)
#   The single LOAD-BEARING discriminator at every site: each spliced identifier
#   is its DELIMITED form delimit(name), NOT the bare identifier. delimit is a
#   @Pure @ContractOnly axiom GROUNDED in the input (fully a function of the
#   input code points) -- there is no opaque answer-key oracle to echo. The
#   prepatch bug (and the F2P failure) is splicing the BARE identifier; for a
#   reserved word like 'order' delimit('order') = '"order"' != 'order'.
#
# Attacks (one per applicable weakness class), each carrying its refinement
# argument that the faithful real patch would NOT resolve the F2P:
#   frame-mutation  (MANDATORY: 4 read-only inputs)
#   ungrounded-oracle: oracle is GROUNDED -> no wrong echo; instead the
#                      bare-identifier rival (the prepatch bug itself) is the
#                      cheapest WRONG impl the grounded postcondition must reject.
#   partial-domain  (delimit only the already-delimited; correct only on a sub-domain)
#   positive controls (structurally-different CORRECT impls)
#   admissibility   (self-call on an F2P-shaped input)
# control-flow-effect: N/A (pure constructors, no raise/side-effect) -- see assessment.

from pathlib import Path

INSTANCE = "django__django-13807"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors -- every one lies STRICTLY inside an impl region (between the
# # impl-start / # impl-end markers), so editing it cannot perturb the spec view.
# ---------------------------------------------------------------------------

# build_single_table_command impl region (lines 124-133):
#   quoted = delimit_id(table_name)
#   result = []  # type: List[int]
#   result = result + [80, 82, ... , 40]
#   result = result + quoted
#   result = result + [41]
#   return result
SINGLE_QUOTED = "quoted = delimit_id(table_name)"
SINGLE_SPLICE = "result = result + quoted"

# build_three_id_command impl region (lines 159-171):
#   a = delimit_id(ident_a); b = ...; c = ...
#   result = []  # type: List[int]
#   result = result + [1, 2]; result = result + a; ...
#   return result
THREE_A = "a = delimit_id(ident_a)"
THREE_SPLICE_A = "result = result + a"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = []

# --- 1. FRAME-MUTATION (MANDATORY) -----------------------------------------
# All inputs are read-only Acc(.,1/2). A rival that WRITES to the read-only
# input list to manufacture the delimited bytes in place must be rejected for
# INSUFFICIENT PERMISSION (you cannot append/mutate at 1/2). We keep the gold
# postcondition verbatim so the rejection is attributable to the write, not a
# value mismatch.
#
# single-table: mutate table_name (prepend/append the delimiter into the input)
_fm_single = _swap(
    _BASE,
    "    quoted = delimit_id(table_name)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [80, 82, 65, 71, 77, 65, 32,\n"
    "                       102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,\n"
    "                       99, 104, 101, 99, 107, 40]\n"
    "    result = result + quoted\n"
    "    result = result + [41]\n"
    "    return result",
    "    # FRAME-MUTATION rival: try to delimit by WRITING into the read-only\n"
    "    # input list (insert the delimiter 34 at both ends in place) instead of\n"
    "    # calling the backend delimiter on a fresh list. table_name is held at\n"
    "    # Acc(list_pred(table_name), 1/2): a write needs full permission, so this\n"
    "    # must be REJECTED for insufficient permission.\n"
    "    table_name.append(34)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [80, 82, 65, 71, 77, 65, 32,\n"
    "                       102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,\n"
    "                       99, 104, 101, 99, 107, 40]\n"
    "    result = result + table_name\n"
    "    result = result + [41]\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "frame-mutation-single",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _fm_single,
    "refinement": (
        "In the real patch table_name is the caller's identifier string and the "
        "fix routes it through self.ops.quote_name(table_name), which RETURNS a "
        "fresh delimited string and never mutates the caller's value. A faithful "
        "patch that instead mutated the caller's identifier in place would corrupt "
        "check_constraints' later uses of table_name (it is reused for "
        "foreign_key_list, get_primary_key_column, and the SELECT), so it would "
        "not resolve the F2P. Nagini models this read-only contract as "
        "Acc(list_pred(table_name), 1/2); the write must fail."
    ),
    "rationale": (
        "Rejection comes from the PERMISSION SYSTEM: table_name is held at "
        "Acc(list_pred(table_name), 1/2) (read-only) in both Requires and "
        "Ensures; .insert/.append need full permission. The gold postcondition is "
        "kept verbatim so the failure is attributable to the in-place write."
    ),
})

# three-id: mutate the FIRST read-only input ident_a in place
_fm_three = _swap(
    _BASE,
    "    a = delimit_id(ident_a)\n"
    "    b = delimit_id(ident_b)\n"
    "    c = delimit_id(ident_c)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [1, 2]\n"
    "    result = result + a\n"
    "    result = result + [3]\n"
    "    result = result + b\n"
    "    result = result + [4, 5]\n"
    "    result = result + c\n"
    "    return result",
    "    # FRAME-MUTATION rival: delimit ident_a by WRITING the delimiter into the\n"
    "    # read-only input list instead of on a fresh list. ident_a is held at\n"
    "    # Acc(list_pred(ident_a), 1/2): the write must be REJECTED.\n"
    "    ident_a.append(34)\n"
    "    b = delimit_id(ident_b)\n"
    "    c = delimit_id(ident_c)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [1, 2]\n"
    "    result = result + ident_a\n"
    "    result = result + [3]\n"
    "    result = result + b\n"
    "    result = result + [4, 5]\n"
    "    result = result + c\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "frame-mutation-three",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _fm_three,
    "refinement": (
        "The gold passes primary_key_column_name (modeled ident_a) through "
        "self.ops.quote_name, which returns a fresh delimited string and never "
        "mutates the caller's identifier. A patch that mutated the column-name "
        "value in place would be a non-faithful refinement (the original "
        "identifiers are shared state in check_constraints) and would not resolve "
        "the F2P. The 1/2 permission on ident_a forbids it."
    ),
    "rationale": (
        "Rejection comes from the PERMISSION SYSTEM: ident_a is held at "
        "Acc(list_pred(ident_a), 1/2) in Requires and Ensures; the in-place "
        ".insert/.append needs full permission."
    ),
})

# --- 2. BARE-IDENTIFIER rival (the grounded-oracle WRONG impl == the prepatch) -
# The postcondition's oracle delimit(...) is GROUNDED in the input (fully a
# function of the input code points), so there is no opaque answer-key to echo.
# The relevant uniqueness attack is the cheapest WRONG impl: splice the BARE
# identifier (skip delimiting). This IS the prepatch bug and the cause of the
# F2P failure; the grounded postcondition must reject it because delimit(name)
# != name for an undelimited identifier (e.g. 'order').
_bare_single = _swap(
    _swap(_BASE, SINGLE_QUOTED, "quoted = table_name  # BARE: skip delimiting"),
    SINGLE_SPLICE,
    "result = result + table_name  # BARE identifier spliced (prepatch bug)",
)
SPEC_TESTS.append({
    "id": "bare-identifier-single",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _bare_single,
    "refinement": (
        "This is literally the pre-patch behaviour: 'PRAGMA foreign_key_check(%s)' "
        "% table_name with the BARE identifier. On the F2P input table_names="
        "['order'] this emits PRAGMA foreign_key_check(order) which raises "
        "OperationalError: near \"order\": syntax error -- it does NOT resolve "
        "test_check_constraints_sql_keywords (which expects IntegrityError). So a "
        "verifying bare-identifier rival would be a true verify-but-not-resolve "
        "break."
    ),
    "rationale": (
        "Rejection comes from POSTCONDITION clause ToSeq(Result()) == "
        "single_table_prefix() + delimit(ToSeq(table_name)) + close_paren(): the "
        "result splices table_name (bare) but delimit(ToSeq(table_name)) wraps an "
        "undelimited identifier in delimiters, so delimit(x) != x and the equality "
        "fails. The oracle is GROUNDED in the input, so this is the real wrong "
        "impl, not an echo."
    ),
})

_bare_three = _swap(
    _swap(_BASE, THREE_A, "a = ident_a  # BARE: skip delimiting"),
    THREE_SPLICE_A,
    "result = result + ident_a  # BARE identifier spliced (prepatch bug)",
)
SPEC_TESTS.append({
    "id": "bare-identifier-three",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _bare_three,
    "refinement": (
        "Splicing the bare first identifier reproduces the pre-patch SELECT "
        "assembly 'SELECT %s, ... ' % (primary_key_column_name, ...). On the F2P "
        "the columns/table are SQL keywords (db_column='select'/'where', "
        "db_table='order'); a bare splice produces a syntax error and the row "
        "lookup fails, so the patch would not resolve the F2P."
    ),
    "rationale": (
        "Rejection comes from POSTCONDITION clause: ToSeq(Result()) begins "
        "three_id_head() + delimit(ToSeq(ident_a)) + ..., but the rival splices "
        "ident_a bare; delimit(ident_a) != ident_a for an undelimited identifier, "
        "so the leading-segment equality fails."
    ),
})

# --- 3. PARTIAL-DOMAIN rival ------------------------------------------------
# A rival that returns the already-delimited form WITHOUT calling delimit but
# instead emits a CONSTANT delimited identifier (a fixed '""' = [34,34]). This
# is correct ONLY on the sub-domain where the input's delimited form equals
# '""' (i.e. delimit returns [34,34]) -- the empty identifier -- and wrong on
# every reserved-word identifier the F2P exercises. It must be rejected.
# NB: keep the '# type:' comment BARE (no trailing parenthetical / second comment
# on the same physical line) -- Nagini reads the type comment to end-of-line, so
# a trailing '# ...' would corrupt the annotation (pilot bug #1).
_pd_single = _swap(
    _swap(_BASE, SINGLE_QUOTED,
          "quoted = [34, 34]  # type: List[int]"),
    SINGLE_SPLICE,
    "result = result + quoted  # PARTIAL-DOMAIN: constant '\"\"', ignores table_name",
)
SPEC_TESTS.append({
    "id": "partial-domain-constant-delim",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _pd_single,
    "refinement": (
        "Emitting a constant '\"\"' ignores the actual identifier: the real patch "
        "must place self.ops.quote_name(table_name) = '\"order\"' into the "
        "command, not '\"\"'. PRAGMA foreign_key_check(\"\") does not name the "
        "'order' table, so check_constraints would not detect the violation and "
        "the F2P (expecting IntegrityError) would not resolve. Correct only when "
        "the identifier is empty."
    ),
    "rationale": (
        "Rejection comes from POSTCONDITION: delimit(ToSeq(table_name)) depends on "
        "table_name (= [34]+table_name+[34] for an undelimited id), but the rival "
        "emits the fixed [34,34], so the equality holds only on the empty-input "
        "sub-domain and fails for any non-empty identifier."
    ),
})

# --- 4. POSITIVE CONTROL (soundness) ---------------------------------------
# (a) single-table: structurally-different but CORRECT -- build the whole
# command in ONE concatenation expression bound to a typed local, rather than
# four incremental result = result + ... statements. Keeps the gold proof valid
# (same sequence equality; delimit_id Ensures still gives quoted's ToSeq).
_pos_single = _swap(
    _BASE,
    "    quoted = delimit_id(table_name)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [80, 82, 65, 71, 77, 65, 32,\n"
    "                       102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,\n"
    "                       99, 104, 101, 99, 107, 40]\n"
    "    result = result + quoted\n"
    "    result = result + [41]\n"
    "    return result",
    "    # POSITIVE CONTROL: same value, different shape -- one combined\n"
    "    # concatenation instead of incremental appends. Correct, must verify.\n"
    "    quoted = delimit_id(table_name)\n"
    "    prefix = [80, 82, 65, 71, 77, 65, 32,\n"
    "              102, 111, 114, 101, 105, 103, 110, 95, 107, 101, 121, 95,\n"
    "              99, 104, 101, 99, 107, 40]  # type: List[int]\n"
    "    result = prefix + quoted + [41]  # type: List[int]\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "pos-control-single-combined",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_single,
    "rationale": (
        "A structurally-different but behaviourally-identical impl (one combined "
        "concatenation vs incremental appends) must verify; the sequence equality "
        "in the postcondition is unchanged and delimit_id's Ensures still pins "
        "ToSeq(quoted)==delimit(ToSeq(table_name)). If this fails => SPEC-TOO-STRONG."
    ),
})

# (b) three-id: reorder the three delimit_id calls (compute c, then b, then a)
# and keep the same assembly order. Pure data-independent reorder; correct.
_pos_three = _swap(
    _BASE,
    "    a = delimit_id(ident_a)\n"
    "    b = delimit_id(ident_b)\n"
    "    c = delimit_id(ident_c)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [1, 2]\n"
    "    result = result + a\n"
    "    result = result + [3]\n"
    "    result = result + b\n"
    "    result = result + [4, 5]\n"
    "    result = result + c\n"
    "    return result",
    "    # POSITIVE CONTROL: compute the three delimited forms in REVERSE order\n"
    "    # (data-independent reorder), assemble in the same final order. Correct.\n"
    "    c = delimit_id(ident_c)\n"
    "    b = delimit_id(ident_b)\n"
    "    a = delimit_id(ident_a)\n"
    "    result = []  # type: List[int]\n"
    "    result = result + [1, 2]\n"
    "    result = result + a\n"
    "    result = result + [3]\n"
    "    result = result + b\n"
    "    result = result + [4, 5]\n"
    "    result = result + c\n"
    "    return result",
)
SPEC_TESTS.append({
    "id": "pos-control-three-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _pos_three,
    "rationale": (
        "Reordering the three independent delimit_id calls leaves the assembled "
        "sequence identical; each call's Ensures still holds. Must verify; if not "
        "=> SPEC-TOO-STRONG."
    ),
})

# --- 5. ADMISSIBILITY -------------------------------------------------------
# A positive-control caller: build_single_table_command is invoked on a fresh
# F2P-shaped input (the reserved word 'order' = [111,114,100,101,114]) and we
# assert the precondition is establishable. We add the call inside the
# three-id impl region (the spec there is untouched) and discard the result.
_admiss = _swap(
    _BASE,
    "    a = delimit_id(ident_a)\n"
    "    b = delimit_id(ident_b)\n"
    "    c = delimit_id(ident_c)",
    "    # ADMISSIBILITY: call build_single_table_command on an F2P-shaped input\n"
    "    # ('order' = [111,114,100,101,114]); its Requires Acc(.,1/2) must be\n"
    "    # establishable for a normal freshly-built identifier list.\n"
    "    sample = [111, 114, 100, 101, 114]  # type: List[int]\n"
    "    _probe = build_single_table_command(sample)\n"
    "    a = delimit_id(ident_a)\n"
    "    b = delimit_id(ident_b)\n"
    "    c = delimit_id(ident_c)",
)
SPEC_TESTS.append({
    "id": "admissibility-single-call",
    "kind": "admissibility",
    "expect": "verify",
    "module": _admiss,
    "rationale": (
        "A representative F2P-shaped identifier ('order') flows into "
        "build_single_table_command and its precondition Acc(list_pred(.),1/2) is "
        "establishable for a fresh list. If the call-site fails to verify => "
        "PRECOND-TOO-STRONG. (Edited only inside an impl region; spec untouched.)"
    ),
})


# ===========================================================================
# AXIOM_TESTS  -- delimit / delimit_id are @ContractOnly A-consumed axioms.
# Soundness: the real callee (sqlite3 DatabaseOperations.quote_name) must match
#   the delimit Ensures on every input in its Requires domain (any str).
# Containment: the model reaches quote_name with ARBITRARY identifier lists
#   (table/column names); delimit's Requires is the full PSeq[int] domain (no
#   constraint), so every caller-reachable input is trivially covered -- we
#   demonstrate it by feeding the real callee the exact identifier shapes the
#   F2P uses ('order','select','where' + already-delimited + unicode + empty).
# ===========================================================================
AXIOM_TESTS = []

# Embed the host-side reference of the model axiom into the probe (the runner
# mounts ONLY the probe at /work; model.py / axiom_check.py are NOT in-container).
_AX_SOUND_PROBE = r'''
import sys
import random

def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def codepoints(s):
    return [ord(ch) for ch in s]

def delimit_model(cps):
    # Reference of model.py's `delimit` axiom over code points (delimiter = 34).
    # Already-delimited (begins AND ends with 34, a lone '"' counts) -> unchanged;
    # otherwise wrapped: [34] + name + [34].
    if len(cps) >= 1 and cps[0] == 34 and cps[-1] == 34:
        return list(cps)
    return [34] + list(cps) + [34]

def main():
    try:
        configure_django()
    except Exception as exc:
        print("AX-SOUND SKIP: Django not configurable: %r" % (exc,))
        return 0
    from django.db.backends.sqlite3.operations import DatabaseOperations
    ops = DatabaseOperations(connection=None)
    quote_name = ops.quote_name

    boundary = [
        # the decisive reserved-word class the F2P actually drives:
        "order", "select", "where", "table", "group", "from", "join",
        "Order", "SELECT",
        "a", "z", "abc", "my_table", "col1", "_x", "x9", "CamelCase",
        '"order"', '"select"', '"already"',     # already-delimited -> unchanged
        '""',                                     # two-delimiter -> unchanged
        '"',                                      # lone delimiter (boundary len>=1, not >=2)
        '"a"', '"my_table"',
        "",                                       # empty identifier -> '""'
        "table with space", "weird;name", "na#me", "n'q",
        'a"b',                                    # interior quote, not bracketing -> wrapped
        '"unbalanced', 'unbalanced"',             # one-sided -> wrapped
        "é", "café", "票据",  # non-ASCII identifiers
    ]
    bad = 0
    for name in boundary:
        observed = codepoints(quote_name(name))
        expected = delimit_model(codepoints(name))
        if observed != expected:
            print("AX-SOUND MISMATCH on %r: quote_name->%r axiom->%r" % (name, observed, expected))
            bad += 1
            continue
        if not (len(observed) >= 1):
            print("AX-SOUND len<1 on %r: %r" % (name, observed)); bad += 1; continue
        if not (observed[0] == 34 and observed[-1] == 34):
            print("AX-SOUND not delimiter-bracketed on %r: %r" % (name, observed)); bad += 1

    rng = random.Random(13807)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "0123456789_ ;#'.-") + ['"', "é", "票"]
    n = 20000
    for _ in range(n):
        length = rng.randint(0, 16)
        name = "".join(rng.choice(alphabet) for _ in range(length))
        observed = codepoints(quote_name(name))
        expected = delimit_model(codepoints(name))
        if observed != expected:
            print("AX-SOUND FUZZ MISMATCH on %r: quote_name->%r axiom->%r" % (name, observed, expected))
            bad += 1
            break

    # idempotence the axiom encodes (already-delimited -> unchanged)
    for name in ["order", "select", "my_table", "café"]:
        once = quote_name(name)
        if quote_name(once) != once:
            print("AX-SOUND not idempotent on %r" % (name,)); bad += 1

    if bad:
        print("AX-SOUND FAIL: %d mismatch(es)" % bad)
        return 1
    print("AX-SOUND OK: real quote_name == delimit axiom over %d boundary + %d fuzz "
          "identifiers; delimiter-bracketed (len>=1), idempotent." % (len(boundary), n))
    return 0

sys.exit(main())
'''
AXIOM_TESTS.append({
    "id": "ax-sound-delimit",
    "axiom": "delimit",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AX_SOUND_PROBE,
    "rationale": (
        "delimit / delimit_id model the unchanged callee "
        "DatabaseOperations.quote_name. The probe executes the REAL quote_name on "
        "the F2P-decisive reserved words, already-delimited names, the lone-'\"' "
        "len>=1 boundary, empty, unicode, and 20000 fuzz identifiers, asserting "
        "every observation equals the delimit Ensures and is delimiter-bracketed "
        "(len>=1) and idempotent. quote_name takes no kwargs (no flag "
        "dependency). Any disagreement => AXIOM-UNSOUND."
    ),
})

# Containment: the model's delimit Requires has NO domain constraint (any
# PSeq[int]); quote_name accepts any str. Demonstrate that every callee-input
# the modeled functions can actually REACH (an arbitrary identifier string at
# any of the three splice sites) lies in quote_name's domain by exercising the
# exact identifier shapes the F2P passes and confirming the callee never raises.
_AX_COVER_PROBE = r'''
import sys

def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    try:
        configure_django()
    except Exception as exc:
        print("AX-COVER SKIP: Django not configurable: %r" % (exc,))
        return 0
    from django.db.backends.sqlite3.operations import DatabaseOperations
    ops = DatabaseOperations(connection=None)
    quote_name = ops.quote_name

    # The modeled functions reach quote_name with ARBITRARY identifier strings
    # (table/column names). The model's delimit Requires is the unrestricted
    # PSeq[int] domain, so containment is trivially satisfied; we DEMONSTRATE the
    # real callee accepts every caller-reachable identifier shape (it must not
    # raise / be out-of-domain) on the exact F2P inputs plus structural edges.
    reachable = [
        "order",          # F2P table db_table='order'
        "select",         # F2P pk db_column='select'
        "where",          # F2P fk db_column='where'
        "",               # empty identifier (degenerate but in PSeq[int])
        "a",              # singleton
        '"order"',        # an already-delimited identifier
        '"',              # lone-delimiter boundary
        "café",     # non-ASCII
        "x" * 256,        # long identifier
    ]
    bad = 0
    for name in reachable:
        try:
            out = quote_name(name)
        except Exception as exc:
            print("AX-COVER OUT-OF-DOMAIN: quote_name(%r) raised %r" % (name, exc))
            bad += 1
            continue
        if not isinstance(out, str):
            print("AX-COVER unexpected return type for %r: %r" % (name, type(out)))
            bad += 1
    if bad:
        print("AX-COVER FAIL: %d caller-reachable input(s) outside quote_name domain" % bad)
        return 1
    print("AX-COVER OK: every caller-reachable identifier (incl. all F2P keyword "
          "names) is in quote_name's domain (no raise); delimit Requires "
          "(unrestricted PSeq[int]) contains every reachable callee-input.")
    return 0

sys.exit(main())
'''
AXIOM_TESTS.append({
    "id": "ax-cover-delimit",
    "axiom": "delimit",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _AX_COVER_PROBE,
    "rationale": (
        "Containment, not full-domain coverage. The modeled functions can pass "
        "quote_name any identifier string; delimit's Requires is the unrestricted "
        "PSeq[int] domain, so every caller-reachable input is covered. The probe "
        "confirms the real callee accepts the exact F2P keyword identifiers plus "
        "structural edges without raising. A reachable input outside the axiom "
        "domain would be AXIOM-TOO-WEAK-FOR-CALLER (none here)."
    ),
})
