## The port in `conformance.py`

`conformance.py` cannot contain the implementation as `$solution` writes it -- $why -- so it
compares the repository with a port of it into Python, and no gate checks that the port
does what the implementation does: a comparison against a wrong port says nothing about the
implementation. Check the port line by line against the implementation, each line against
the line of `$solution` it ports. A line that does not do what that line does -- another
operation, a branch taken on another condition, a step left out or added, a value converted
otherwise than `correspondence.md` maps it -- is a finding: quote both lines, and name an
input on which the two differ.
