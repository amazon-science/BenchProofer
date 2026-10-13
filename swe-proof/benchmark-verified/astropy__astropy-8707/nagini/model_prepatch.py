"""Twin-artifact model for astropy__astropy-8707.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Building a single record image from raw input. The input arrives in one of
      two forms: either it is already in TEXT form (it is textual content), or it
      is a RAW BYTE sequence (each element a byte value in 0..255). BOTH forms
      must be ACCEPTED and must yield a record image.

      The record image is the input's textual content padded out with spaces
      (code point 32) to a whole multiple of the constant record width.

      How textual content is reached differs by form. An input already in text
      form IS textual content and may be used as it stands. A raw byte sequence
      is NOT yet textual content: it becomes textual content by being taken code
      point for code point, byte value b yielding code point b. That
      correspondence preserves every element's value, so the image built from a
      byte sequence equals the image built from the value-equal text-form input
      -- the same keyword and the same value are recovered from either form.

      The padding step is defined on TEXTUAL CONTENT, and it yields textual
      content again. Being in text form is a property OF A VALUE, conferred by
      the step that takes a byte sequence over into textual content; it is not
      something a caller may simply assert of a raw byte sequence it happens to
      hold. So the value that reaches the padding step has to be one that is
      genuinely textual content -- for a byte-sequence input, that means the
      code-point correspondence must have been applied to it beforehand -- and
      the record image handed back is itself textual content.

  (2) Building the list of record images from a whole raw input. A raw byte
      input must be ACCEPTED here too: it yields the record images the input
      contains rather than a failure. Each record image handed back is textual
      content reached as in (1) -- its code points are the values of the input
      elements that record was built from, so from either form of one record the
      same keyword and the same value are recovered. How a whole input divides
      into records is NOT part of the behaviour specified here, and nothing is
      claimed about a byte input and the value-equal text-form input dividing
      alike.

Two things are therefore pinned, and neither implies the other: the VALUE of the
image (the padded, value-preserving textual content of the input, the same for
both input forms), and the TEXT FORM of the value that is padded (for a byte
sequence, attained only by applying the correspondence to it). A correspondence
that preserves values cannot be detected in the value it produces, which is why
the value clauses alone cannot express the second point; text form is carried as
a property of a value, conferred only by that step and demanded by the padding
step, which is what makes it observable.

Strings/bytes are modelled as `List[int]` (Nagini bans `str`/`bytes` indexing);
specifications are carried by `PSeq[int]`. The constant record width is modelled
as the small constant 4 (the real width is 80; only multiplicity matters and the
refinement is width-agnostic -- see refinement.md). The value half of the
correspondence is spelled out DEEPLY as `reinterpret` and matched by the
implementation step for step. Its other half -- that the outcome is textual
content, which a sequence-of-code-points carrier cannot express as a value -- is
carried by the opaque property `text_form`: it has no body, so no computation
conjures it, `enter_text_form` is its only source, and the padding step demands
it. An input supplied in text form carries it by virtue of that form (the two
forms are told apart by `from_bytes`). Termination is demanded at the method
level, so every guarantee is claimed of runs that finish.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

WIDTH = 4  # modelled constant record width (real value 80; see refinement.md)


# axioms-start
@Pure
@ContractOnly
def pad_to_width(image: PSeq[int]) -> PSeq[int]:
    """The padding helper, as a pure specification function: it appends space
    code points (32) to the TEXTUAL CONTENT `image` until its length is a whole
    multiple of the constant record width, leaving the existing content
    untouched. The runtime form is `pad_runtime`. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(len(image) >= 0)
    Ensures(len(Result()) >= len(image))
    Ensures(Result().take(len(image)) == image)              # content preserved
    Ensures(len(Result()) % WIDTH == 0)                      # whole multiple
    Ensures(len(Result()) <= len(image) + WIDTH)             # at most WIDTH added
    Ensures(Forall(int, lambda k: (Implies(len(image) <= k and k < len(Result()),
                                            Result()[k] == 32))))  # spaces


@Pure
@ContractOnly
def text_form(v: List[int]) -> bool:
    """Holds of a value that is TEXTUAL CONTENT, as opposed to a raw byte
    sequence that has not been taken over into textual content.

    Deliberately OPAQUE -- it has no body. Nothing computes it, and no caller can
    assert it of a value of its own choosing: its only source is
    `enter_text_form`, and the padding step demands it. That is what makes "the
    value being padded really is textual content" checkable rather than merely
    claimable, which matters precisely because the code-point correspondence
    preserves values and so leaves no trace in the value itself. A value supplied
    in text form has this property by virtue of its form. Provenance + executable
    soundness check: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(v), 1 / 2))


@ContractOnly
def enter_text_form(v: List[int]) -> List[int]:
    """Take a value over into TEXT form, leaving its content exactly as it is.
    This is the half of the code-point correspondence that a
    sequence-of-code-points carrier cannot express as a value: the elements are
    carried across unchanged (the value half is spelled out deeply as
    `reinterpret`), and what the step adds is that the outcome IS textual
    content, which is what the padding step requires of its argument. Provenance
    + executable soundness check: mapping.md / axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(v), 1 / 2))
    Ensures(Acc(list_pred(v), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(v))                     # content unchanged
    Ensures(text_form(Result()))                             # outcome is textual


@ContractOnly
def pad_runtime(text: List[int]) -> List[int]:
    """Runtime form of the padding helper. It is defined on TEXTUAL CONTENT: its
    argument must be in text form, which a raw byte sequence attains only by
    being taken over into textual content first. It returns the padded value (the
    value level of `pad_to_width`), itself textual content. Soundness check:
    axiom_check.py."""
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(text_form(text))
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == pad_to_width(ToSeq(text)))
    Ensures(text_form(Result()))
# axioms-end


# pure-start
@Pure
def reinterpret(x: PSeq[int]) -> PSeq[int]:
    """The value half of the code-point correspondence for a raw byte sequence
    (byte value b -> code point b), spelled out deeply: every element is carried
    across unchanged. Front-recursive so a single unfold is available per step."""
    Ensures(Result() == x)
    if len(x) == 0:
        return PSeq(0).take(0)
    return PSeq(x[0]) + reinterpret(x.drop(1))


@Pure
def all_bytes(x: PSeq[int]) -> bool:
    """Every element is a byte value (0..255): true of any genuine byte input
    and of the text these record images use."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(x),
                                          0 <= x[k] and x[k] <= 255)))
# pure-end


def build_record_image(raw: List[int], from_bytes: bool) -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(3))
    Requires(Acc(list_pred(raw), 1 / 2))
    Requires(all_bytes(ToSeq(raw)))
    # The two input forms. `from_bytes` false says the input is supplied ALREADY
    # in text form, and such an input is textual content by virtue of its form,
    # so it may be padded as it stands. A byte-sequence input (`from_bytes` true)
    # carries no such property: nothing beyond its element values is assumed of
    # it, so the byte-input domain is exactly as wide as it is without this
    # clause -- which is the domain on which both forms must be accepted.
    Requires(Implies(not from_bytes, text_form(raw)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(raw), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # ACCEPT-BOTH-FORMS: the function returns normally for a byte-sequence input
    # (from_bytes == True) just as for a text-form input (from_bytes == False).
    # (The absence of an Exsures clause is that guarantee.)
    #
    # VALUE: the image is the padded, value-preserving textual content of the
    # input. Because the correspondence preserves every element's value, a byte
    # input yields the same image as the value-equal text-form input.
    Ensures(ToSeq(Result()) == pad_to_width(reinterpret(ToSeq(raw))))
    Ensures(len(Result()) >= len(raw))
    Ensures(ToSeq(Result()).take(len(raw)) == ToSeq(raw))
    Ensures(len(Result()) % WIDTH == 0)
    # TEXT FORM: the image handed back is itself textual content. Text form has
    # no source but the step that takes a value over into it, and the padding
    # step demands it of its argument, so this can hold only if what was padded
    # was genuinely textual content -- for a byte-sequence input, only if that
    # step was applied to it first. This is the half of the behaviour the value
    # clauses above cannot express, the correspondence being value-preserving.
    Ensures(text_form(Result()))
    # post-conditions-end
    # impl-start
    # The code-point correspondence, spelled out step by step.
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
    # PRE-PATCH: only an input supplied already in text form is treated as
    # textual content. A byte sequence is handed to the padding step without
    # first being taken over into text form, so on the byte-input form the
    # padding step receives a value that is not textual content.
    if not from_bytes:
        res = pad_runtime(raw)
        return res
    res = pad_runtime(image)
    return res
    # impl-end
