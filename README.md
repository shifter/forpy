# forpy
Generic network traffic forwarding and manipulation tool implemented with [asyncio](https://docs.python.org/3/library/asyncio.html).

## Compatibility
`asyncio` is available for Python 3.3 and newer. Users of Python 3.3 must install `asyncio` from [PyPI](https://pypi.python.org/pypi), Python 3.4 ships it in the standard library by default. Therefore forpy requires Python 3.3 or any newer.

## Dependencies
[uvloop](http://magic.io/blog/uvloop-make-python-networking-great-again/) can be used as a drop in replacement for the `asyncio` event loop for better performance. Just install it via `pip`:

```
pip install uvloop
```