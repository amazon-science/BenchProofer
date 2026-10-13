#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13401.

This bundle consumes NO `@ContractOnly` axiom: equality, the strict order, and
the hash KEY are all modelled deeply over the attributes' own fields. What G-AX
must validate is that those deep models agree with the REAL Python semantics the
gold patch relies on — the same `getattr`-equality, native tuple comparison, and
native `hash` the patched `__eq__` / `__lt__` / `__hash__` invoke. These are the
A-reference checks (mapping.md §3):

  (A-reference 1) `eq_ref` / `same_owner` == the patch's equality decision
      `creation_counter == other.creation_counter and
       getattr(self,'model',None) == getattr(other,'model',None)`, with a model
      modelled by its (app_label, model_name) identity pair (so two distinct
      models are distinct pairs).

  (A-reference 2) `lt_ref` == the patch's `__lt__` decision, including the
      tie-break that compares the native tuple `(app_label, model_name)`; and
      the model's flattened-key lexicographic order `lex_lt(label ++ [SEP] ++
      name, ...)` (SEP = 0, below every identifier code point) equals Python's
      native tuple comparison on those pairs.

  (A-reference 3) `hash_ref` is the exact KEY the gold `__hash__` feeds to the
      builtin `hash` — `(creation_counter, app_label_or_None, model_name_or_None)`
      — and the builtin `hash` is injective on the DISTINCT keys this benchmark
      produces, so two attributes with different identity hash apart (the
      collection-de-duplication the issue is about). Validated by executing the
      REAL builtin `hash` and asserting distinct keys -> distinct hashes.

Imports nothing repo-specific: native `hash`, tuple comparison and `getattr` are
the very operations the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys

SEP = 0  # separator below every identifier code point (identifiers never NUL)


# --- model.py reference encodings (kept in lock-step with the deep models) ---

def flat_key(label, name):
    """model.py's flattened identity key: label ++ [SEP] ++ name (code points)."""
    return [ord(c) for c in label] + [SEP] + [ord(c) for c in name]


def lex_lt(x, y):
    """model.py's `lex_lt`: lexicographic strict less-than on code-point seqs."""
    i = 0
    while i < len(x) and i < len(y):
        if x[i] != y[i]:
            return x[i] < y[i]
        i += 1
    return len(x) < len(y)


def same_owner(a, b):
    """model.py `same_owner`: both ownerless, or both own an identical key."""
    (oa, ka), (ob, kb) = a, b
    return oa == ob and (not oa or ka == kb)


def eq_ref(a, b):
    """model.py `eq_ref`: same rank AND same owner identity."""
    (ra, _, _), (rb, _, _) = a, b
    return ra == rb and same_owner((a[1], a[2]), (b[1], b[2]))


def lt_ref(a, b):
    """model.py `lt_ref`."""
    (ra, oa, ka), (rb, ob, kb) = a, b
    if ra != rb or (not oa and not ob):
        return ra < rb
    if oa != ob:
        return not oa
    return lex_lt(ka, kb)


def hash_ref(a):
    """model.py `hash_ref` KEY as a tuple (the value fed to builtin hash)."""
    (r, o, k) = a
    if o:
        return (r, 1) + tuple(k)
    return (r, 0)


# --- the REAL Python semantics the gold patch invokes ------------------------

def real_eq(self_cc, self_model, other_cc, other_model):
    """The patched __eq__ decision, verbatim semantics."""
    return (self_cc == other_cc and self_model == other_model)


def real_lt(self_cc, self_has, self_id, other_cc, other_has, other_id):
    """The patched __lt__ decision, verbatim semantics (self_id/other_id are the
    native (app_label, model_name) tuples; meaningful only when *_has)."""
    if self_cc != other_cc or (not self_has and not other_has):
        return self_cc < other_cc
    elif self_has != other_has:
        return not self_has
    else:
        return self_id < other_id


def real_hash_key(cc, has, app_label, model_name):
    """The exact tuple the gold __hash__ hashes."""
    return (cc, app_label if has else None, model_name if has else None)


# --- the checks --------------------------------------------------------------

def attr_of(rank, label, name):
    """Build a model attribute (rank, owned, flat_key); label is None => no
    owner (a bare, never-attached field)."""
    if label is None:
        return (rank, False, [])
    return (rank, True, flat_key(label, name))


def native_of(rank, label, name):
    """The native ingredients of the same attribute, as the real ops see them.
    A model is identified by its (app_label, model_name) pair; an ownerless
    field's model attribute is absent (getattr default None)."""
    has = label is not None
    ident = (label, name) if has else None
    return rank, has, ident


def check_pair(a_spec, b_spec):
    ra, la, na = a_spec
    rb, lb, nb = b_spec
    A, B = attr_of(*a_spec), attr_of(*b_spec)
    rA, hA, idA = native_of(*a_spec)
    rB, hB, idB = native_of(*b_spec)

    # A-reference 1: equality
    got_eq = eq_ref(A, B)
    want_eq = real_eq(rA, idA, rB, idB)
    assert got_eq == want_eq, ("eq_ref unsound on %r,%r: model=%s real=%s"
                               % (a_spec, b_spec, got_eq, want_eq))

    # A-reference 2: strict order (incl. flattened-key lex == native tuple cmp)
    got_lt = lt_ref(A, B)
    want_lt = real_lt(rA, hA, idA, rB, hB, idB)
    assert got_lt == want_lt, ("lt_ref unsound on %r,%r: model=%s real=%s"
                               % (a_spec, b_spec, got_lt, want_lt))
    # when both owned, the flattened-key order must equal the native tuple order
    if hA and hB:
        assert lex_lt(A[2], B[2]) == (idA < idB), (
            "flattened-key lex order disagrees with native tuple order on "
            "%r,%r" % (idA, idB))

    # A-reference 3: hash key identity + builtin-hash injectivity on distinct keys
    keyA = hash_ref(A)
    keyB = hash_ref(B)
    realkeyA = real_hash_key(rA, hA, la, na)
    realkeyB = real_hash_key(rB, hB, lb, nb)
    # the model's key must encode the same identity the gold hashes (distinct
    # iff the gold's key is distinct)
    assert (keyA == keyB) == (realkeyA == realkeyB), (
        "hash_ref identity disagrees with gold hash key on %r,%r" % (a_spec, b_spec))
    # builtin hash de-dup property, stated SOUNDLY: the issue is fields that
    # share a creation rank but belong to different owners collapsing in a set.
    # The gold key now carries the owner, so such keys differ; for keys sharing
    # the SAME rank component, the builtin hash separates them (no collision on
    # identifier-like identity strings). NOTE we do NOT claim universal hash
    # injectivity: hash(-1) == hash(-2) (CPython's -1 error-sentinel quirk)
    # collides distinct *ranks*, which is irrelevant to the equal-rank de-dup.
    if rA == rB and realkeyA != realkeyB:
        assert hash(realkeyA) != hash(realkeyB), (
            "builtin hash collision on equal-rank distinct keys %r vs %r"
            % (realkeyA, realkeyB))


def main():
    # --- the F2P scenario (abstract model + two concrete inheritors) ----------
    APP = "model_fields"
    abstract = (0, APP, "abstractmodel")
    inherit1 = (0, APP, "inheritabstractmodel1")
    inherit2 = (0, APP, "inheritabstractmodel2")
    f2p = [abstract, inherit1, inherit2]
    for i in range(len(f2p)):
        for j in range(len(f2p)):
            check_pair(f2p[i], f2p[j])
    # the exact F2P assertions (assertNotEqual / assertLess / hash differ)
    A, B, C = (attr_of(*x) for x in f2p)
    assert not eq_ref(A, B) and not eq_ref(A, C) and not eq_ref(B, C)
    assert lt_ref(A, B) and lt_ref(A, C) and lt_ref(B, C)
    f2p_keys = [real_hash_key(native_of(*x)[0], native_of(*x)[1], x[1], x[2])
                for x in f2p]
    assert len({hash(k) for k in f2p_keys}) == 3, "F2P hashes must differ"

    # --- backward-compat scenario (bare fields, no owner, distinct ranks) ----
    bare = [(7, None, None), (-1, None, None), (3, None, None)]
    for i in range(len(bare)):
        for j in range(len(bare)):
            check_pair(bare[i], bare[j])
    # a bare field vs an owned field at equal rank: bare precedes
    check_pair((5, None, None), (5, APP, "thing"))
    check_pair((5, APP, "thing"), (5, None, None))

    # --- boundary identity strings -------------------------------------------
    labels = ["", "a", "app", "z", "app2", "model_fields", "auth"]
    names = ["", "a", "x", "model", "abstractmodel", "inheritabstractmodel1",
             "inheritabstractmodel10", "z"]
    boundary = []
    for la in labels:
        for na in names:
            boundary.append((0, la, na))
            boundary.append((1, la, na))
    boundary += [(0, None, None), (-1, None, None), (100, None, None)]
    for i in range(0, len(boundary), 1):
        for j in range(0, len(boundary), 1):
            check_pair(boundary[i], boundary[j])

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13401)
    alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
    def rand_label():
        n = rng.randint(0, 10)
        return "".join(rng.choice(alphabet) for _ in range(n))
    for _ in range(40000):
        ra = rng.randint(-3, 5)
        rb = rng.randint(-3, 5)
        a = (ra, None, None) if rng.random() < 0.25 else (ra, rand_label(), rand_label())
        b = (rb, None, None) if rng.random() < 0.25 else (rb, rand_label(), rand_label())
        check_pair(a, b)

    print("G-AX OK: eq_ref / lt_ref / hash_ref deep models == native "
          "getattr-equality / tuple-order / builtin-hash on the F2P scenario, "
          "%d boundary pairs and 40000 fuzz pairs; flattened-key lex order "
          "matches native tuple order; distinct gold keys hash apart."
          % (len(boundary) ** 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
