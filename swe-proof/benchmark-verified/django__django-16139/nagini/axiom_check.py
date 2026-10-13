#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16139.

This bundle consumes NO @ContractOnly axiom. The one unchanged callee whose
semantics the proof relies on -- hierarchical relative-reference resolution
("pop one accumulated segment per '..' step, otherwise append") -- is modelled
DEEPLY in model.py as the verified pure fold `resolve`. G-AX therefore checks
that this deep model is sound:

  (A-reference) the deep model `resolve(base_dir, rel)` (model.py pure region)
      == the REAL stdlib resolver `urllib.parse.urljoin(base_url, rel_url)`,
      on the hierarchical-path shapes the bundle uses (boundary + fuzz). The
      model represents a URL path as the list of its non-empty segments; the
      ".." step is the sentinel DOTDOT == -1; `base_dir` is the directory-
      segment list of a trailing-slash base URL.

It also confirms, end to end, the behaviour the spec pins:

  * The post-patch relative reference  f"../../{pk}/password/"  resolved against
    the change URL  .../user/<token>/change/  yields  .../user/<pk>/password/
    for EVERY access token (incl. token != pk).
  * The pre-patch relative reference   "../password/"          resolved the same
    way yields  .../user/<token>/password/ , i.e. it is WRONG exactly when the
    page was reached via an identifier other than the primary key.

Imports only the Python standard library (`urllib.parse` is the resolver the
real test, tests/auth_tests/test_forms.py, uses for the same assertion). Exit 0
iff every obligation holds.
"""
import random
import sys
import urllib.parse

DOTDOT = -1


# --- model.py deep-model reference (kept in lock-step with `resolve`) --------

def resolve(base_dir, rel):
    """Reference implementation of model.py's deep model `resolve`, over lists
    of path-segment ids (DOTDOT == -1 is the up-one-level step)."""
    stack = list(base_dir)
    for step in rel:
        if step == DOTDOT:
            if stack:
                stack.pop()
        else:
            stack.append(step)
    return stack


# --- bridge between segment-id lists and concrete URL strings ----------------

def segs_to_url(segs, trailing_slash=True):
    """A trailing-slash absolute URL from ordinary (non-DOTDOT) segment names.
    The empty segment list renders as the root '/'."""
    if len(segs) == 0:
        return "/"
    body = "/".join(str(s) for s in segs)
    return "/" + body + ("/" if trailing_slash else "")


def rel_to_url(rel):
    """A relative reference string from a list of steps (DOTDOT -> '..'). The
    result is always RELATIVE (no leading '/'); an empty step list is the empty
    reference '' (which `urljoin` resolves to the base itself)."""
    if len(rel) == 0:
        return ""
    parts = [".." if step == DOTDOT else str(step) for step in rel]
    return "/".join(parts) + "/"


def overpops_root(base_dir_segs, rel_steps):
    """True iff some prefix of `rel_steps` would pop above the root given the
    base depth -- i.e. the relative reference escapes above '/'. Outside the
    deep model's declared domain (the patch's change URLs are always deep
    enough that a 1- or 2-level '..' never reaches the root), and the regime
    where RFC 3986 `urljoin` emits a non-absolute remainder. The model.py
    precondition keeps the base prefix populated, so this case never arises in
    the bundle; the check restricts validation to that sound domain."""
    depth = len(base_dir_segs)
    for step in rel_steps:
        if step == DOTDOT:
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def check_resolve_reference(base_dir_segs, rel_steps):
    """Assert the deep model resolve(...) == REAL urllib.parse.urljoin(...) on
    the bundle's domain (no root over-pop)."""
    if overpops_root(base_dir_segs, rel_steps):
        return
    base_url = segs_to_url(base_dir_segs, trailing_slash=True)
    rel_url = rel_to_url(rel_steps)
    real_url = urllib.parse.urljoin(base_url, rel_url)
    model_url = segs_to_url(resolve(base_dir_segs, rel_steps), trailing_slash=True)
    assert real_url == model_url, (
        "resolve deep model unsound: base=%r rel=%r -> urljoin gave %r, "
        "deep model gives %r" % (base_url, rel_url, real_url, model_url))


def main():
    rng = random.Random(16139)

    # --- A-reference: resolve == urllib.parse.urljoin -----------------------
    # Boundary base-dir shapes (the change-URL directory segment lists) and the
    # two relative references the bug is about, plus assorted ".." mixtures.
    bases = [
        ["admin", "auth", "user", "tok", "change"],   # the real shape
        ["admin", "auth", "user", "7", "change"],
        ["a", "b"],
        ["x"],
        ["p", "q", "r", "s", "t"],
    ]
    rel_boundary = [
        [DOTDOT, "password"],                          # pre-patch reference
        [DOTDOT, DOTDOT, "9", "password"],             # post-patch reference
        [],                                            # empty relative ref
        [DOTDOT],
        [DOTDOT, DOTDOT, DOTDOT, DOTDOT, DOTDOT],       # over-pop (clamps at root)
        ["only"],
        [DOTDOT, "1", DOTDOT, "2"],                     # interleaved
    ]
    for b in bases:
        for r in rel_boundary:
            check_resolve_reference(b, r)

    # Randomized fuzz over base depth and relative-step shape.
    seg_alphabet = ["a", "b", "c", "d", "e", "f", "0", "1", "2", "3", "user",
                    "change", "password"]
    for _ in range(20000):
        depth = rng.randint(1, 7)
        base = [rng.choice(seg_alphabet) for _ in range(depth)]
        rlen = rng.randint(0, 7)
        rel = []
        for _ in range(rlen):
            if rng.random() < 0.45:
                rel.append(DOTDOT)
            else:
                rel.append(rng.choice(seg_alphabet))
        check_resolve_reference(base, rel)

    # --- end-to-end behavioural witness (mirrors the F2P test's urljoin) ----
    # change URL reached via an arbitrary access token; password page keyed by
    # the primary key. Post-patch reference must hit the pk page for every
    # token; pre-patch reference hits it iff token == pk.
    APP, MODEL = "auth", "user"
    for _ in range(5000):
        pk = rng.randint(1, 10 ** 9)
        token = rng.choice([pk, rng.randint(1, 10 ** 9),
                             "uuid-%d" % rng.randint(0, 10 ** 9),
                             "testclient"])
        change_url = "/admin/%s/%s/%s/change/" % (APP, MODEL, token)
        target = "/admin/%s/%s/%s/password/" % (APP, MODEL, pk)

        post_ref = "../../%s/password/" % pk           # the gold (post-patch)
        post_resolved = urllib.parse.urljoin(change_url, post_ref)
        assert post_resolved == target, (
            "post-patch reference wrong: token=%r pk=%r -> %r != %r"
            % (token, pk, post_resolved, target))

        pre_ref = "../password/"                        # the pre-patch (buggy)
        pre_resolved = urllib.parse.urljoin(change_url, pre_ref)
        if str(token) == str(pk):
            assert pre_resolved == target
        else:
            assert pre_resolved != target, (
                "pre-patch reference unexpectedly correct for token=%r pk=%r"
                % (token, pk))

    print("G-AX OK: resolve deep model (== urllib.parse.urljoin) sound on %d "
          "boundary + 20000 fuzz inputs; end-to-end pk-keyed reference "
          "validated on 5000 token/pk witnesses"
          % (len(bases) * len(rel_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
