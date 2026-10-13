import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behavior under specification is the rendering of a
--  stand-in placeholder symbol's reference from the data the placeholder carries;
--  it is modeled DEEPLY in the `pure` region below as a total function of its
--  inputs. Nothing outside the modeled rendering is consulted, so there is no
--  `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- A stand-in placeholder symbol is created to stand for a name that could not
   be resolved. It carries two pieces of textual data:
     * `modulePath`  — the dotted module path it lives under;
     * `createdName` — the simple name it was created to stand for.

   The reported simple name of such a placeholder is exactly the name it was
   created to stand for: a placeholder created for a name reports that name, and
   a placeholder created with no name (the bare root placeholder) reports the
   empty name. -/
def reportedName (createdName : List Char) : List Char := createdName

/- The renderer that turns a symbol into a cross-reference does not treat every
   module path alike. Three module paths are reserved by it, and a placeholder
   living under one of them is rendered by a different rule than the general one.
   These are the reserved paths, and the one reserved simple name. -/
def coreNamespaceA : List Char :=
  ['_', '_', 'b', 'u', 'i', 'l', 't', 'i', 'n', '_', '_']
def coreNamespaceB : List Char := ['b', 'u', 'i', 'l', 't', 'i', 'n', 's']
def abbreviatedNamespace : List Char := ['t', 'y', 'p', 'i', 'n', 'g']
def aliasFactoryName : List Char :=
  ['N', 'e', 'w', 'T', 'y', 'p', 'e', '.', '<', 'l', 'o', 'c', 'a', 'l', 's',
   '>', '.', 'n', 'e', 'w', '_', 't', 'y', 'p', 'e']

/- The constant decorations the renderer places around the symbol text: the role
   marker it opens with, the mark it closes with, the element-list tail it adds
   for a path under a reserved core namespace, and the mark that abbreviates a
   path under the reserved abbreviated namespace. -/
def openMark : List Char := [':', 'p', 'y', ':', 'c', 'l', 'a', 's', 's', ':', '`']
def closeMark : List Char := ['`']
def elementListTail : List Char := ['\\', ' ', '[', ']']
def abbreviationMark : List Char := ['~']

/- The reference the renderer produces for a placeholder, as a function of the
   two pieces of data the placeholder carries. Four rules, tried in this order —
   the renderer consults the module path FIRST and only reaches the general
   dotted rule when the path is none of the reserved ones:

     1. the reserved abbreviated namespace together with the reserved simple
        name: the module path is dropped and only the reported simple name is
        rendered;
     2. a reserved core namespace: the module path is dropped, the reported
        simple name is rendered, and the element-list tail is appended;
     3. the reserved abbreviated namespace with any other simple name: the
        dotted path is rendered behind the abbreviation mark;
     4. any other module path: the dotted path is rendered plainly.

   In every one of the four rules the trailing segment is the reported simple
   name — the name the placeholder was created to stand for — so no rule drops
   it. -/
def renderedReference (modulePath createdName : List Char) : List Char :=
  if modulePath = abbreviatedNamespace ∧ reportedName createdName = aliasFactoryName then
    openMark ++ reportedName createdName ++ closeMark
  else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
    openMark ++ reportedName createdName ++ closeMark ++ elementListTail
  else if modulePath = abbreviatedNamespace then
    openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark
  else
    openMark ++ modulePath ++ ['.'] ++ reportedName createdName ++ closeMark

@[grind] lemma reportedName_eq (createdName : List Char) :
    reportedName createdName = createdName := rfl

@[grind] lemma renderedReference_general (modulePath createdName : List Char)
    (hA : modulePath ≠ coreNamespaceA) (hB : modulePath ≠ coreNamespaceB)
    (hT : modulePath ≠ abbreviatedNamespace) :
    renderedReference modulePath createdName
      = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark := by
  simp [renderedReference, reportedName, hA, hB, hT]

@[grind] lemma renderedReference_core (modulePath createdName : List Char)
    (h : modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) :
    renderedReference modulePath createdName
      = openMark ++ createdName ++ closeMark ++ elementListTail := by
  rcases h with h | h <;> subst h <;>
    simp [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
          abbreviatedNamespace, aliasFactoryName]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the reference for a stand-in placeholder symbol. The rendering reads
   the placeholder's module path and the name it was created to stand for, and
   follows whichever of the renderer's four rules the module path selects; in
   every rule the trailing segment is the reported simple name, which is exactly
   the name the placeholder was created to stand for. Both inputs are read-only —
   neither is declared `mut` (directive 5): the rendering only reads the module
   path and the creation name and mutates nothing. -/
method renderReference (modulePath : List Char) (createdName : List Char)
    return (out : List Char)
  ensures out = renderedReference modulePath createdName
  ensures modulePath = abbreviatedNamespace → createdName = aliasFactoryName →
      out = openMark ++ createdName ++ closeMark
  ensures (modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) →
      out = openMark ++ createdName ++ closeMark ++ elementListTail
  ensures modulePath = abbreviatedNamespace → createdName ≠ aliasFactoryName →
      out = openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ createdName
              ++ closeMark
  ensures modulePath ≠ coreNamespaceA → modulePath ≠ coreNamespaceB →
      modulePath ≠ abbreviatedNamespace →
      out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark
  do
    -- impl-start
    -- The placeholder's reported simple name is the name it was created to stand
    -- for; the rendered reference places that name in the trailing position of
    -- whichever of the renderer's four rules the module path selects.
    let simpleName := createdName
    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
      return openMark ++ simpleName ++ closeMark
    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
      return openMark ++ simpleName ++ closeMark ++ elementListTail
    else if modulePath = abbreviatedNamespace then
      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
               ++ closeMark
    else
      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
    -- impl-end

prove_correct renderReference by
  loom_solve
  <;> intros
  <;> subst_vars
  <;> simp_all [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,
                abbreviatedNamespace, aliasFactoryName]
