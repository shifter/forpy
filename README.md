# forpy
Generic network traffic forwarding and manipulation tool implemented with [asyncio](https://docs.python.org/3/library/asyncio.html).

## Compatibility
`asyncio` is available for Python 3.3 and newer. Users of Python 3.3 must install `asyncio` from [PyPI](https://pypi.python.org/pypi), Python 3.4 ships it in the standard library by default. Therefore forpy requires Python 3.3 or any newer.

## Dependencies
[uvloop](http://magic.io/blog/uvloop-make-python-networking-great-again/) can be used as a drop in replacement for the `asyncio` event loop for better performance. Just install it via `pip`:

```
pip install uvloop
```

## Manipulate Traffic
forpy implements two functions for traffic manipulations: `request_hook()` for manipulating requests before they will be sent to the target server and `response_hook()` for manipulating responses before they will be sent back to the client.

If e.g. a rquest would contain a string `username=anonymous`, changing the username would be as easy as:

```python
def request_hook(data):
    data = data.replace(b'username=anonymous', b'username=admin')
    return data
```