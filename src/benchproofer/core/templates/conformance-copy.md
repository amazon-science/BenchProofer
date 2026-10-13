The copy of the implementation sits inside region sentinels, on its own:

```python
def shadow_<name>(<the same parameters>):
    # benchproofer:begin impl
    <the body of the `impl` region, with the checker's annotations taken out, exactly as written>
    # benchproofer:end impl
```

The `def` line stays outside the region, the region holds the body verbatim and nothing else,
and everything else about the comparison lives outside it. Benchproofer checks that it does:
a body that differs compares a second implementation rather than the one the checker
accepted. That is also what lets Benchproofer run the comparison against a different
implementation of the same function, which is how a reviewer's attack on the bundle is
judged. Where the specification models several functions, each body goes in a `shadow_`
function of its own inside the region of the same name (`impl.2` for the second), so every
one of them is compared. A name the body calls keeps its spelling inside the region: where
one modeled body calls another modeled function, or a helper of the file, bind that name at
module level, outside every region, to what the program defines for it -- `serialize_value =
shadow_serialize_value` -- rather than renaming the call inside the region, and reach the
repository's function of that name through its module (`module.serialize_value`). A value
the checker's library supplies and the body still uses, such as `ToSeq`, gets a replacement
of your own outside the regions. Where the body has to be translated all the same, the
translation changes the values it works on and nothing else.
