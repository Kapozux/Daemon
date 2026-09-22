"""A simple calculator module."""


class Calculator:
    """A basic calculator."""

    def add(self, a, b):
        """Return a + b."""
        return a + b

    def sub(self, a, b):
        """Return a - b."""
        return a - b

    def mul(self, a, b):
        """Return a * b."""
        return a * b

    def div(self, a, b):
        """Return a / b. Raise ValueError if b is zero."""
        if b == 0:
            raise ValueError('division by zero')
        return a / b

    def pow(self, a, b):
        """Return a ** b."""
        return a ** b

    def mod(self, a, b):
        """Return a % b. Raise ValueError if b is zero."""
        if b == 0:
            raise ValueError('modulo by zero')
        return a % b

    def sqrt(self, a):
        """Return the square root of a. Raise ValueError if a is negative."""
        if a < 0:
            raise ValueError('sqrt of negative number')
        return a ** 0.5


if __name__ == '__main__':
    c = Calculator()
    print('add(3, 2) =', c.add(3, 2))
    print('sub(3, 2) =', c.sub(3, 2))
    print('mul(3, 2) =', c.mul(3, 2))
    print('div(3, 2) =', c.div(3, 2))
    print('pow(2, 3) =', c.pow(2, 3))
    print('mod(7, 3) =', c.mod(7, 3))
    print('sqrt(9)   =', c.sqrt(9))
    try:
        c.div(1, 0)
    except ValueError as e:
        print('div(1, 0) raises ValueError:', e)
    try:
        c.mod(1, 0)
    except ValueError as e:
        print('mod(1, 0) raises ValueError:', e)
    try:
        c.sqrt(-1)
    except ValueError as e:
        print('sqrt(-1) raises ValueError:', e)
