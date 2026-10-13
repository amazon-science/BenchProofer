The port of the implementation into Python sits inside region sentinels, on its own:

```python
def shadow_<name>(<the same parameters>):
    # benchproofer:begin impl
    <the `impl` region, ported into Python line by line>
    # benchproofer:end impl
```

Port it line by line and keep its structure -- the same cases in the same order, the same
recursion or loop, a call to the same helper where the code calls one -- so that a reviewer
can read each line of the port against the line of the model it ports, and end each line of
the port with a comment naming that line. Where an operation of the model has no Python
operation of the same meaning, write what the model's operation computes, not the nearest
Python builtin: a `Char.toLower` defined on ASCII letters alone is not `str.lower`. The `def`
line stays outside the region; the region holds the port and nothing else, and everything
else about the comparison lives outside it. Where the specification models several
functions, each port goes in a `shadow_` function of its own inside the region of the same
name (`impl.2` for the second), so every one of them is compared. A name the code calls
keeps its spelling in the port: where one modeled function calls another, or a helper of the
file, port that one as well and bind its name at module level, outside every region, to the
port -- `serializeValue = shadow_serializeValue` -- rather than renaming the call inside the
region, and reach the repository's function through its module.
