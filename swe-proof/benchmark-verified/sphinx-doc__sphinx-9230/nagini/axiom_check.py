#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9230.

The changed behaviour is modelled DEEPLY (the structural name=final-element /
type=ordered-prefix parse, with the prefix re-emitted separated by single
spaces), not behind a consumed `@ContractOnly` axiom. There are therefore NO
A-consumed axioms; the single trust point this script validates is the
**A-reference**, and it validates it HONESTLY against the documented modelled
domain rather than only on the abstraction's own image.

  the model's parse of a typed field argument == the REAL `str.rsplit(None, 1)`
  ON SINGLE-SPACE-SEPARATED input, where

    * the parsed NAME is the final element (model:
      PSeq(encode_name(last_token))  ==  one-token rendering of t(n-1));
    * the parsed TYPE is the ordered prefix re-emitted with single spaces
      (model: joined(take(n-1))).

The model abstracts each maximal whitespace-free chunk to one token AND
collapses every inter-token separator to a single space. The modelled domain is
therefore explicitly RESTRICTED to single-space-separated input (mapping.md §2),
the form the F2P/P2P tests use. To avoid the rigged-fuzz trap (generating inputs
only through the abstraction's own `" ".join`), this script fuzzes the REAL
callee's NATIVE input domain — arbitrary whitespace separators, including
multi-space, tabs, and leading/trailing whitespace — and:

  (a) on the modelled single-space sub-domain it ASSERTS the model == the real
      `str.rsplit(None, 1)` (the A-reference it claims);
  (b) on the EXCLUDED multi-whitespace sub-domain it ASSERTS the model is
      genuinely out-of-domain — it documents and demonstrates the divergence
      (the model's single-space rejoin differs from the real verbatim left
      piece) rather than silently never generating such inputs — so the claimed
      restriction is verified, not dodged;
  (c) it confirms that every F2P/P2P test input that reaches this parse IS in
      the single-space sub-domain, so the restriction loses no tested coverage.

It also confirms the modelling domain (n >= 2 tokens) and the unchanged
ValueError path (n < 2 raises identically for BOTH `split` and `rsplit`), and
that the OLD `str.split(None, 1)` disagrees exactly when the type spans more
than one token (n >= 3) — the bug. Imports only the standard library. Exit 0
iff every observation matches.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def model_joined(token_strs):
    """Reference of model.py's `joined`: the ordered prefix re-emitted separated
    by a single space, in order. Returned as the real text (each token
    verbatim), which is exactly what the model's encode_name-tagged sequence
    denotes once the token<->string bijection of mapping.md is applied. NOTE the
    single-space separator: this is the modelled domain restriction."""
    return " ".join(token_strs)


def model_parse(token_strs):
    """Reference of (parsed_argument_type, parsed_argument_name) for a run of
    n >= 2 tokens: the type is the single-space join of the leading n-1 tokens,
    the name is the last token."""
    assert len(token_strs) >= 2
    return model_joined(token_strs[:-1]), token_strs[-1]


# --- domain classification ---------------------------------------------------

def tokens_of(text):
    """The real callee's token view: maximal whitespace-free runs (what
    `str.split()` with sep=None yields). The model carries exactly these."""
    return text.split()


def is_single_space_separated(text):
    """True iff `text` is the canonical single-space-separated form of its
    tokens with no leading/trailing whitespace — the modelled sub-domain. This
    is precisely the form on which the single-space rejoin reproduces the real
    text, and it is the form every tested F2P/P2P input takes."""
    return text == " ".join(tokens_of(text))


# --- the checks --------------------------------------------------------------

def check_rsplit_reference_single_space(text):
    """On SINGLE-SPACE-SEPARATED input the model MUST match the real
    str.rsplit(None, 1) exactly (the A-reference)."""
    assert is_single_space_separated(text), (
        "check_rsplit_reference_single_space called off-domain: %r" % text)
    token_strs = tokens_of(text)
    if len(token_strs) < 2:
        return  # < 2 tokens: not the modelled parse domain (handled separately)
    argtype, argname = text.rsplit(None, 1)            # the REAL gold callee
    exp_type, exp_name = model_parse(token_strs)        # the deep model
    assert argname == exp_name, (
        "name mismatch on single-space input %r: real rsplit name=%r, model=%r"
        % (text, argname, exp_name))
    assert argtype == exp_type, (
        "type mismatch on single-space input %r: real rsplit type=%r, model=%r"
        % (text, argtype, exp_type))


def check_excluded_domain_is_documented(text):
    """On input that is NOT single-space-separated (multi-space / tab / leading
    / trailing whitespace) the model's single-space rejoin is NOT claimed to
    equal the real str.rsplit(None, 1). This asserts the documented restriction
    HONESTLY: the model's name side still equals the real name (rsplit's name
    is the bare last token, which the model captures), but the model's TYPE side
    (a single-space rejoin) can differ from the real verbatim left piece, which
    preserves internal/leading whitespace. We REQUIRE that the only way the
    model could ever differ from the real callee is via this separator collapse
    on excluded input — i.e. whenever the real type text already equals its own
    single-space-collapsed form, the model still matches; otherwise it is
    legitimately out of the modelled domain. This is the check the previous
    rigged harness dodged by never generating such inputs."""
    token_strs = tokens_of(text)
    if len(token_strs) < 2:
        return  # < 2 tokens: ValueError path, checked elsewhere
    argtype, argname = text.rsplit(None, 1)
    exp_type, exp_name = model_parse(token_strs)
    # The name side is whitespace-insensitive (it is the bare final token), so
    # the model must still match the real name even off-domain.
    assert argname == exp_name, (
        "name mismatch off-domain on %r: real rsplit name=%r, model=%r "
        "(the name side must be separator-insensitive)"
        % (text, argname, exp_name))
    # The type side: the model equals the real callee IFF the real left piece is
    # already in single-space-collapsed form. When it is not (genuine
    # multi-whitespace), the model legitimately diverges -> out of modelled
    # domain. We assert this equivalence exactly, so the restriction is verified.
    real_type_is_collapsed = (argtype == model_joined(argtype.split()))
    model_matches_type = (argtype == exp_type)
    assert model_matches_type == real_type_is_collapsed, (
        "off-domain type behaviour not as documented on %r: model_type=%r, "
        "real_type=%r, model_matches=%s, real_is_single_space_collapsed=%s"
        % (text, exp_type, argtype, model_matches_type, real_type_is_collapsed))


def check_old_split_is_the_bug(token_strs):
    """For a multi-token type (n >= 3) the OLD str.split(None, 1) MUST disagree
    with the correct parse — that disagreement is precisely the reported bug."""
    if len(token_strs) < 3:
        return
    text = " ".join(token_strs)
    bug_type, bug_name = text.split(None, 1)           # the pre-patch callee
    good_type, good_name = model_parse(token_strs)
    assert (bug_type, bug_name) != (good_type, good_name), (
        "split(None,1) unexpectedly equals the correct parse on %r" % text)
    # specifically: the bug keeps only the first token as the type
    assert bug_type == token_strs[0], (
        "old split type not the first token on %r" % text)


def check_valueerror_path_unchanged(text):
    """For < 2 whitespace tokens BOTH split and rsplit raise ValueError on the
    2-tuple unpacking, so the gold one-liner leaves that path identical."""
    def unpack(fn):
        try:
            a, b = fn(text, None, 1)
            return ("ok", a, b)
        except ValueError:
            return ("raise",)
    s = unpack(str.split)
    r = unpack(str.rsplit)
    assert s == r, (
        "split/rsplit disagree on the <2-token path for %r: %r vs %r"
        % (text, s, r))
    assert s[0] == "raise", (
        "expected ValueError on <2-token input %r, got %r" % (text, s))


def main():
    # token alphabet: identifier-ish and generic-type chunks containing the
    # awkward characters the issue's `dict(str, str)` type carries (no spaces
    # WITHIN a token — a token is a maximal whitespace-free run).
    token_pool = [
        "dict(str,", "str)", "opc_meta", "params", "Dict[str,", "str]",
        "int", "name", "Tuple[str,", "...]", "List[int]", "foo", "bar",
        "SomeClass", "x", "y", "a(b,", "c)", "value", "Optional[int]",
    ]
    # the REAL callee's whitespace alphabet (sep=None splits on any run of these)
    separators = [" ", "  ", "   ", "\t", " \t ", "\t ", "  \t"]

    # --- (a) A-reference on the MODELLED single-space sub-domain -----------
    # boundary forms, all single-space-separated (the form the tests use).
    boundary_single_space = [
        "int name",                                    # simple 2-token
        "dict(str, str) opc_meta",                     # the issue's case
        "Dict[str, str] params",                       # the F2P case
        "Tuple[str, ...] items",
        "a(b, c) d(e, f) name",                        # long multi-token type
        "List[int] xs",
        "Optional[int] z",
    ]
    for text in boundary_single_space:
        assert is_single_space_separated(text), (
            "boundary input not single-space-separated: %r" % text)
        check_rsplit_reference_single_space(text)
        check_old_split_is_the_bug(tokens_of(text))

    # --- (c) every tested-input shape that reaches this parse is in-domain ---
    # The F2P/P2P field-argument inputs in tests/test_domain_py.py (e.g.
    #   ":param Dict[str, str] params:" -> fieldarg "Dict[str, str] params") are
    # single-space-separated. Assert the representatives are in the sub-domain so
    # the domain restriction loses no tested coverage.
    tested_fieldargs = [
        "Dict[str, str] params",                       # the new F2P line
        "int age", "str name",                         # existing P2P typed params
        "Tuple[str, ...] items",
    ]
    for text in tested_fieldargs:
        assert is_single_space_separated(text), (
            "tested fieldarg unexpectedly NOT in the modelled single-space "
            "sub-domain: %r" % text)
        check_rsplit_reference_single_space(text)

    # --- (a)+(b) randomized fuzz over the REAL callee's NATIVE domain --------
    # Generate inputs with ARBITRARY whitespace separators (NOT only " ".join),
    # plus optional leading/trailing whitespace, so the fuzz exercises the
    # callee's true input domain rather than the abstraction's image. Route each
    # input to the in-domain assertion (a) or the excluded-domain assertion (b).
    rng = random.Random(9230)
    n_in_domain = 0
    n_excluded = 0
    for _ in range(20000):
        n = rng.randint(2, 6)
        run = [rng.choice(token_pool) for _ in range(n)]
        # join with RANDOM (possibly multi-char / tab) separators
        parts = []
        for k, tok in enumerate(run):
            if k:
                parts.append(rng.choice(separators))
            parts.append(tok)
        text = "".join(parts)
        # optional leading / trailing whitespace (real docutils astext can carry
        # it; sep=None strips it, so it is part of the native domain)
        if rng.random() < 0.3:
            text = rng.choice(separators) + text
        if rng.random() < 0.3:
            text = text + rng.choice(separators)

        if is_single_space_separated(text):
            n_in_domain += 1
            check_rsplit_reference_single_space(text)
        else:
            n_excluded += 1
            check_excluded_domain_is_documented(text)
        check_old_split_is_the_bug(tokens_of(text))

    assert n_excluded > 0, (
        "fuzz never produced an excluded (multi-whitespace) input — the "
        "harness would be rigged; separators=%r" % separators)
    assert n_in_domain > 0, "fuzz never produced an in-domain input"

    # --- explicit excluded-domain witnesses (must be demonstrated, not dodged) ---
    # These are realistic docutils-producible inputs that the model does NOT
    # cover; the previous harness avoided generating them. We assert they are
    # off the modelled domain AND that the documented divergence holds, so the
    # restriction is verified rather than hidden.
    excluded_witnesses = [
        "dict(str,  str) opc_meta",                    # internal double space
        "  Dict[str, str] params",                     # leading whitespace
        "Dict[str,\tstr] params",                      # tab inside the type
        "int\t\tname",                                 # tab-run separator
    ]
    saw_real_divergence = False
    for text in excluded_witnesses:
        assert not is_single_space_separated(text), (
            "excluded witness unexpectedly IS single-space-separated: %r" % text)
        check_excluded_domain_is_documented(text)
        token_strs = tokens_of(text)
        if len(token_strs) >= 2:
            argtype, _ = text.rsplit(None, 1)
            exp_type, _ = model_parse(token_strs)
            if argtype != exp_type:
                saw_real_divergence = True
    assert saw_real_divergence, (
        "no excluded witness actually diverged — the divergence the domain "
        "restriction excludes must be demonstrated, not merely asserted")

    # --- unchanged ValueError path (< 2 tokens) ---------------------------
    for text in ["", " ", "   ", "name", "  name  ", "\tonly\t", "single"]:
        check_valueerror_path_unchanged(text)

    print(
        "G-AX OK: on the modelled single-space-separated domain the deep model "
        "(name=final element; type=ordered prefix, single-space rendering) == "
        "real str.rsplit(None,1) over %d boundary + %d tested-fieldarg + %d "
        "in-domain fuzz inputs; the EXCLUDED multi-whitespace/tab/leading "
        "sub-domain (%d fuzz + %d explicit witnesses) is demonstrated "
        "out-of-domain exactly per the documented restriction (real divergence "
        "witnessed); old str.split(None,1) confirmed wrong for multi-token "
        "types; the <2-token ValueError path is identical for split and rsplit."
        % (len(boundary_single_space), len(tested_fieldargs), n_in_domain,
           n_excluded, len(excluded_witnesses)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
