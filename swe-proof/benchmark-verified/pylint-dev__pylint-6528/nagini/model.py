"""Twin-artifact model for pylint-dev__pylint-6528.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A single ignore decision for a discovered path. A path is ignored exactly
      when ANY of three independently-configured rules fires: its final path
      component (its "name") is one of the configured ignore names; OR some
      configured name-pattern matches that final component; OR some configured
      full-path pattern matches the whole path. The decision is the disjunction
      of the three rules — none of them is dropped.

  (2) Recursive discovery must respect that decision *for whole subtrees*. A
      directory tree is walked top-down, one root at a time, to collect the
      paths that will be examined. When the ignore decision of (1) holds for a
      walked root, that root is dropped AND it starts suppressing descent, so
      every root reached LATER in the walk that lies within it is dropped too —
      even one whose own name matches no ignore rule. A root therefore survives
      only when it is not itself ignored and lies within no directory that an
      EARLIER step of the same walk had already started suppressing descent
      past; being reached by recursion is not enough to keep a path inside a
      suppressed directory.

      Suppressing descent has a SECOND source, and it is observable too. Some
      walked directories the walk accounts for AS A WHOLE: it answers for such a
      directory itself and examines nothing inside it separately, so that
      directory likewise suppresses every later root that lies within it. Such a
      directory SURVIVES — the walk does answer for it — while the roots beneath
      it do not. The two sources are independent and neither may be dropped: a
      walked directory suppresses descent exactly when the ignore decision of
      (1) fires on it OR it is one the walk accounts for as a whole. Which
      directories are of that second kind is an observable of the tree being
      walked, not a choice open to an implementation, so it is pinned as such —
      dropping it would keep roots the walk does not answer for separately, and
      inventing it would drop roots the walk does.

      Two things follow from "earlier in the same walk", and both are observable.
      A root is only ever suppressed by a directory the walk had ALREADY
      reached: a directory that starts suppressing descent only at a later step
      of the walk suppresses nothing behind it. And the containment test that
      does the suppressing is the plain path-prefix relation of the walk itself,
      not a component-boundary test — so a walked root is suppressed by an
      earlier suppressing directory exactly when that directory's path is a
      prefix of it.

  (3) Both answers must actually be DELIVERED. The ignore decision of (1) is
      settled in finitely many steps and returned; the surviving-root sequence
      of (2) is likewise produced in finitely many steps — a bounded number per
      walked root — and returned. A computation that never gets there has
      answered nothing, so (1) and (2) are claims about a value that comes back,
      not merely about runs that happen to come back. This is demanded of every
      input the domain admits: it is an obligation on the computation, not a
      restriction on the inputs.

Filesystem paths are modelled as opaque `int` tokens (path ids); the only
operations performed on a path are taking its name component, testing the
name/path patterns, asking whether the walk accounts for a directory as a whole,
the path-prefix ("lies within") relation between two paths, and list membership
— never character inspection (Nagini bans `str` indexing). The name component,
the two pattern tests, the accounted-for-as-a-whole observable and the prefix
relation are unchanged callees, axiomatized as `@Pure @ContractOnly` and
validated against the real callees out-of-band (axiom_check.py / G-AX). The
ignore decision itself and the subtree-aware discovery filter are modelled
deeply and verified.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def name_of(element: int) -> int:
    """Final path component (the "name") of a path id — the unchanged stdlib
    callee that reduces a path to the token the ignore-names list is matched
    against. A deterministic pure function of the path id.
    Provenance + executable soundness check: mapping.md §3.1 / axiom_check.py.
    """


@Pure
@ContractOnly
def basename_matches(element: int) -> bool:
    """Whether some configured name-pattern matches this path's name component
    (the unchanged regex callee applied to the path's name). A deterministic
    pure predicate of the path id.
    Provenance + executable soundness check: mapping.md §3.2 / axiom_check.py.
    """


@Pure
@ContractOnly
def path_matches(element: int) -> bool:
    """Whether some configured full-path pattern matches this whole path (the
    unchanged regex callee applied to the path itself). A deterministic pure
    predicate of the path id.
    Provenance + executable soundness check: mapping.md §3.3 / axiom_check.py.
    """


@Pure
@ContractOnly
def covers_own_subtree(element: int) -> bool:
    """Whether the walk accounts for this directory AS A WHOLE — it answers for
    the directory itself and examines nothing inside it separately. An
    observable of the walked tree, read off the directory the walk has reached;
    a deterministic pure predicate of the path id, and an unchanged callee of
    the walk. It is the SECOND reason a walked directory starts suppressing
    descent (the first is the ignore decision), so the roots beneath such a
    directory are not examined even though no ignore rule fires on them.
    Provenance + executable soundness check: mapping.md §3.5 / axiom_check.py.
    """


@Pure
@ContractOnly
def under(child: int, ancestor: int) -> bool:
    """Whether `child` lies within `ancestor` under the unchanged path-prefix
    relation the walk uses to suppress descent past an already-suppressing
    directory: `ancestor`'s path is a prefix of `child`'s. This is the plain
    prefix test, NOT a component-boundary ("separator") test — a directory whose
    path is a textual prefix of a sibling's path does suppress that sibling, and
    the relation holds of a path and itself. A deterministic pure relation
    between two path ids.
    Provenance + executable soundness check: mapping.md §3.4 / axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def name_ignored(name: int, ignore_names: PSeq[int]) -> bool:
    """Whether a name token occurs in the configured ignore-names sequence.
    Front-recursive so a single membership unfold is available per step."""
    if len(ignore_names) == 0:
        return False
    return name == ignore_names[0] or name_ignored(name, ignore_names.drop(1))


@Pure
def ignored(element: int, ignore_names: PSeq[int]) -> bool:
    """The ignore decision for one path: the disjunction of the three rules —
    name in the ignore-names list, a name-pattern match, or a full-path match.
    None of the three is dropped."""
    return (
        name_ignored(name_of(element), ignore_names)
        or basename_matches(element)
        or path_matches(element)
    )


@Pure
def suppresses_descent(directory: int, ignore_names: PSeq[int]) -> bool:
    """Whether a walked directory, once the walk has reached it, starts
    suppressing descent — so every later root that lies within it is dropped.
    Exactly two independent reasons do that and BOTH are kept: the ignore
    decision of (1) fires on the directory, OR the walk accounts for that
    directory as a whole and therefore examines nothing inside it separately.
    Neither disjunct may be omitted and neither may be strengthened away."""
    return ignored(directory, ignore_names) or covers_own_subtree(directory)


@Pure
def suppressed_by_earlier(element: int, walked_before: PSeq[int],
                          ignore_names: PSeq[int]) -> bool:
    """Whether `element` is suppressed by the walk steps that came before it:
    some root in `walked_before` — the roots the top-down walk reached STRICTLY
    EARLIER, in order — suppresses descent AND `element` lies within it. The
    quantification is over the already-walked prefix only, never over the whole
    walked set: a directory that starts suppressing descent only at a later step
    suppresses nothing behind it. Front-recursive so a single unfold is
    available per step."""
    if len(walked_before) == 0:
        return False
    return (
        (suppresses_descent(walked_before[0], ignore_names)
         and under(element, walked_before[0]))
        or suppressed_by_earlier(element, walked_before.drop(1), ignore_names)
    )


@Pure
def pruned(element: int, walked_before: PSeq[int],
           ignore_names: PSeq[int]) -> bool:
    """A walked root is dropped from discovery when it is itself ignored OR it
    is suppressed by an earlier-walked directory that suppresses descent. This
    is the subtree-aware decision: a path inside an ignored directory is dropped
    even when its own name matches no ignore rule, and so is a path inside a
    directory the walk already accounts for as a whole. Note the asymmetry: a
    directory that only accounts for its own subtree is itself KEPT (it is not a
    disjunct of the drop decision) while everything strictly within it goes."""
    return (ignored(element, ignore_names)
            or suppressed_by_earlier(element, walked_before, ignore_names))


@Pure
def kept(rest: PSeq[int], walked_before: PSeq[int],
         ignore_names: PSeq[int]) -> PSeq[int]:
    """The walk-order subsequence of `rest` that survives subtree-aware
    pruning, given that `walked_before` are the roots already walked. Each step
    decides the head against the prefix walked before it and then extends that
    prefix by the head — so every root is judged against exactly the roots that
    preceded it, whether or not it survived. Front-recursive so a single unfold
    is available per loop step."""
    if len(rest) == 0:
        return rest
    if pruned(rest[0], walked_before, ignore_names):
        return kept(rest.drop(1), walked_before + PSeq(rest[0]), ignore_names)
    return (PSeq(rest[0])
            + kept(rest.drop(1), walked_before + PSeq(rest[0]), ignore_names))
# pure-end


def kept_none_ignored(rest: PSeq[int], walked_before: PSeq[int],
                      ignore_names: PSeq[int]) -> None:
    """Lemma: no element of kept(rest, walked_before) is itself ignored (the
    per-path safety half of the discovery filter), proven by induction over the
    front-recursion of kept."""
    # The induction is finite: one step per remaining element of `rest`, which
    # the recursive step strictly shortens, so the lemma is DELIVERED and not
    # merely promised of a derivation that runs on forever.
    Requires(MustTerminate(len(rest) + 1))
    Ensures(Forall(int, lambda k: (Implies(
        0 <= k and k < len(kept(rest, walked_before, ignore_names)),
        not ignored(kept(rest, walked_before, ignore_names)[k],
                    ignore_names)))))
    if len(rest) > 0:
        kept_none_ignored(rest.drop(1), walked_before + PSeq(rest[0]),
                          ignore_names)
        if pruned(rest[0], walked_before, ignore_names):
            # head dropped: kept(rest) == kept(rest.drop(1))
            Assert(kept(rest, walked_before, ignore_names) ==
                   kept(rest.drop(1), walked_before + PSeq(rest[0]),
                        ignore_names))
        else:
            # head retained at index 0 (not pruned); tail shifted by one
            Assert(kept(rest, walked_before, ignore_names) ==
                   PSeq(rest[0]) + kept(rest.drop(1),
                                        walked_before + PSeq(rest[0]),
                                        ignore_names))
            Assert(kept(rest, walked_before, ignore_names)[0] == rest[0])
            Assert(Forall(int, lambda k: (Implies(
                1 <= k and k < len(kept(rest, walked_before, ignore_names)),
                kept(rest, walked_before, ignore_names)[k] ==
                kept(rest.drop(1), walked_before + PSeq(rest[0]),
                     ignore_names)[k - 1]))))


def subtree_prune_drops(all_roots: PSeq[int], k: int,
                        ignore_names: PSeq[int]) -> None:
    """Lemma (the subtree half of safety): a walked root that is suppressed by
    an earlier-walked directory that suppresses descent contributes NOTHING to
    the surviving sequence — the discovery filter behaves at that step exactly
    as if the root were absent. So a path inside an ignored directory never
    survives, even where its own name matches no ignore rule; and neither does a
    path inside a directory the walk already accounts for as a whole. Both
    suppression sources get this treatment, because `suppresses_descent` is the
    disjunction of the two."""
    Requires(0 <= k and k < len(all_roots))
    Requires(suppressed_by_earlier(all_roots[k], all_roots.take(k),
                                   ignore_names))
    # A single step, so this too is a delivered conclusion.
    Requires(MustTerminate(1))
    Ensures(kept(all_roots.drop(k), all_roots.take(k), ignore_names) ==
            kept(all_roots.drop(k + 1), all_roots.take(k + 1), ignore_names))
    Assert(all_roots.drop(k)[0] == all_roots[k])
    Assert(all_roots.drop(k).drop(1) == all_roots.drop(k + 1))
    Assert(all_roots.take(k) + PSeq(all_roots[k]) == all_roots.take(k + 1))
    Assert(pruned(all_roots[k], all_roots.take(k), ignore_names))


def kept_step(all_roots: PSeq[int], i: int, ignore_names: PSeq[int]) -> None:
    """Lemma: ONE step of the walk-order fold, at walk position i-1. Unfolding
    `kept` at the front of the not-yet-judged suffix: the root at that position
    is judged against exactly the roots walked before it, and the prefix the
    remaining roots are judged against is that prefix extended by it."""
    Requires(0 < i and i <= len(all_roots))
    # A single unfold, so this too is a delivered conclusion.
    Requires(MustTerminate(1))
    Ensures(kept(all_roots.drop(i - 1), all_roots.take(i - 1), ignore_names) ==
            (kept(all_roots.drop(i), all_roots.take(i), ignore_names)
             if pruned(all_roots[i - 1], all_roots.take(i - 1), ignore_names)
             else PSeq(all_roots[i - 1])
             + kept(all_roots.drop(i), all_roots.take(i), ignore_names)))
    Assert(all_roots.drop(i - 1)[0] == all_roots[i - 1])
    Assert(all_roots.drop(i - 1).drop(1) == all_roots.drop(i))
    Assert(all_roots.take(i - 1) + PSeq(all_roots[i - 1]) == all_roots.take(i))


def is_ignored(element: int, ignore_names: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(ignore_names), 1 / 2))
    # The decision must be REACHED for every input the domain admits: it is
    # settled in finitely many steps — a bounded number per configured ignore
    # name — and returned. A computation that runs on forever never decides
    # anything, so the value clause below is owed on every admissible input
    # rather than only on the runs that happen to reach the end. An obligation
    # on the computation, not a restriction on the inputs.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ignore_names), 1 / 2))
    # The decision is exactly the disjunction of the three independent rules.
    Ensures(Result() == ignored(element, ToSeq(ignore_names)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def discover(roots: List[int], ignore_names: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(roots), 1 / 2))
    Requires(Acc(list_pred(ignore_names), 1 / 2))
    # Discovery must COMPLETE for every input the domain admits: the surviving
    # sequence is produced in finitely many steps — a bounded number per walked
    # root, so the walk itself is the bound — and returned. A walk that never
    # ends discovers nothing, so the two value clauses below are owed on every
    # admissible input rather than only on the runs that happen to reach the
    # end. An obligation on the computation, not a restriction on the inputs.
    # The bound is stated one above the number of walked roots so that the
    # per-position walk-order reasoning discovery needs sits strictly beneath
    # it.
    Requires(MustTerminate(len(roots) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(roots), 1 / 2))
    Ensures(Acc(list_pred(ignore_names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the walk-order subsequence of roots that survive
    # subtree-aware pruning, each root judged against the roots walked strictly
    # before it: kept drops every root that is itself ignored OR is suppressed
    # by an earlier-walked directory that suppresses descent — for either of the
    # two reasons a directory does that, the ignore decision or the walk
    # accounting for it as a whole — and retains the rest in order.
    Ensures(ToSeq(Result()) ==
            kept(ToSeq(roots), ToSeq(roots).take(0), ToSeq(ignore_names)))
    # Soundness of discovery, per-path half: NO surviving path is one the ignore
    # decision fires on. (The subtree half — a path suppressed by an
    # earlier-walked suppressing directory contributes nothing — is the lemma
    # `subtree_prune_drops`, which the fold above pins for every walk position.)
    Ensures(Forall(int, lambda k: (Implies(
        0 <= k and k < len(Result()),
        not ignored(Result()[k], ToSeq(ignore_names))))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
