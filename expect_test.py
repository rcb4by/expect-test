
class Setup: pass
class Assertion: pass
class ToBe(Assertion):
  def __init__(self, *args):
    self.expected = tuple(args)

  def assert_stmt(self, result):
    assert self.expected == result



class init(Setup):
  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs

  def expect(self, *args, **kwargs):
    _expect = expect(*args, **kwargs)
    _expect.setups.append(self)
    return _expect





class expect:

  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    self.setups = []
    self.assertions = []

  def __call__(self, func):
    result = func(*self.args, **self.kwargs)
    for stmt in assertions:
      stmt.assert_stmt(result)
  
  def toBe(self, *args):
    self.assertions.append(ToBe(args))
    return self
