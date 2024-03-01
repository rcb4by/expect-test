# expect-test
A new paradigm of unit testing

## Tutorial
### Basic Example
To test the best, we should keep tests in the easiest place to keep them updated - alongside the code itself.
With Expect Test, this is simple:
```python
@expect(2).toBe(4)
def squared(x: int) -> int:
    return x ** 2
```
To write more tests, simply include more decorators:
```python
@expect(2).toBe(4)
@expect(0).toBe(0)
@expect(-3).toBe(9)
def squared(x: int) -> int:
    return x ** 2
```
Tests, along with docstrings, are visually separated from code, while providing necessary context about the intended behavior of the function:
```python
@expect(2).toBe(4)
@expect(0).toBe(0)
@expect(-3).toBe(9)
def squared(x: int) -> int:
    """
    Return the square of the input number
    Inputs:
        `x`: the number to square
    Returns: the squared number
    """
    return x ** 2
```
Arguments to `@expect` will be passed to the function under test, while args to `toBe` will be interpreted as a tuple:
```python
@expect(6, 3, mod=4).toBe(4, 2)
def mult_then_div_mod(x: int, y: int, /, *, mod: int) -> int:
    return divmod(x * y, mod)
```
For classes, `@init` will construct an instance before running the tests:
```python
class Multiply:
    def __init__(self, x: int):
        self.x = x

    @init(3)
    @expect(5).toBe(15)
    @expect(0).toBe(0)
    def multiply(y: int) -> int:
        return self.x * y
```
### Advanced Features
#### Setup
Use `@mock` to patch out sub-calls and remove side effects:
```python
@mock(request.get, return_value='SUCCESS')
@expect('test body').toBe('SUCCESS')
def make_request(body: str) -> Response:
    return request.get(URL, body)
```
Or `@env` to patch an environment variable:
```python
@env('URL', 'test-url.com')
@mock(request.get, return_value='SUCCESS')
@expect('test body').toBe('SUCCESS')
def make_request(body: str) -> Response:
    return request.get(os.getenv('URL'), body)
```
`mock`, `env`, and `init` can also be used in-line to create per-test environments:
```python
@mock(request.get, return_value='SUCCESS')
@expect('test body').toBe('SUCCESS')
@mock(request.get, return_value='FAILURE').expect('test body').toBe('FAILURE')
def make_request(body: str) -> Response:
    return request.get(os.getenv('URL'), body)
```
#### Verification
`toBe` can be replaced with `toRaise`, or ommitted entirely:
```python
@expect(True)     # passes if no exception is thrown
@expect(False).toRaise(AssertionError)
def assert_value(value):
    assert value
```
Expect Test provides a variety of helper functions for verifying the behavior of mocks:
```python
@env('URL', 'test-url.com')
@mock(request.get, return_value='SUCCESS')
@expect('test body').toBe('SUCCESS').withCall('test-url.com', 'test body')  # Asserts passed args against most recent call
@expect('test body').toBe('SUCCESS').withCalls([(['test-url.com', 'test body'], {})])  # List of tuple([*args], {**kwargs}) 
@expect('test body').withCallCount(1)  # There is no `withoutCalls`, use `withCallCount(0)` instead
def make_request(body: str) -> Response:
    return request.get(os.getenv('URL'), body)
```
Multiple mocks can be verified by chaining or by id:
```python
@mock(request.get, id='get', return_value='SUCCESS')
@mock(json.dump, id='dump')
@expect('test-url.com', None).withCall('test-url.com').withCall(None, 'SUCCESS')
@expect('test-url.com', None).withDumpCall(None, 'SUCCESS').withGetCall('test-url.com')  # `id` will be stripped of non-alphanum and capitalized
def get_and_write(url: str, f: file):
    response = request.get(url)
    json.dump(f, data)
```
Expect Test de facto encourages functional programming, but when testing class methods, the `withState` directive receives kwargs which will be compared against properties of the same name.
Remember that class construction is treated as a function and thus receives the `@expect` directive:
```python
class StoredMultiple:
    @expect(5).withState(x=5)
    def __init__(self, x: int):
        self.x = x

    @init(3).expect(5).withState(x=15)
    def multiply(y: int) -> int:
        self.x *= y
```
### Full Example
```python

class SafeRequest:
    @expect(2).withState(max_retries=2)
    @env('ENV', 'prod').expect(2).withState(url='prod.url')
    @env('ENV', 'qa').expect(2).withState(url='qa.url')
    def __init__(self, max_retries: int):
        self.max_retries = max_retries
        if os.getenv('ENV') == 'prod':
            self.url = 'prod.url'
        else:
            self.url = 'qa.url'

    @env('ENV', 'qa')
    @init(2)
    @mock(request.get, 'get', status_code=200, text='SUCCESS')
    @mock(request.post, 'post', status_code=200, text='SUCCESS')
    @expect('GET', 'test').toBe('SUCCESS').withGetCall(ANY, 'test').withPostCallCount(0)
    @expect('POST', 'test').toBe('SUCCESS').withPostCall(ANY, 'test').withGetCallCount(0)
    @expect('INVALID', 'test').toRaise(InvalidMethodError)
    @mock(request.get, status_code=400).expect('GET', 'test').toRaise(MaxRetriesExceededError).withCallCount(2)
    def request(self, method: str, body: str) -> str:
        retries = 0
        while retries < self.max_retries:
            if method == 'GET':
                response = request.get(self.url, body)
            elif method == 'POST':
                response = request.post(self.url, body)
            else:
                raise InvalidMethodError(method)
            if response.status_code == 200:
                return response.text
            retries += 1
        raise MaxRetriesExceededError()
```
