"""Unit tests for calculator.Calculator."""

import unittest

from calculator import Calculator


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.c = Calculator()

    def test_add(self):
        self.assertEqual(self.c.add(2, 3), 5)

    def test_add_negative(self):
        self.assertEqual(self.c.add(-1, -1), -2)

    def test_sub(self):
        self.assertEqual(self.c.sub(5, 3), 2)

    def test_sub_negative(self):
        self.assertEqual(self.c.sub(0, 4), -4)

    def test_mul(self):
        self.assertEqual(self.c.mul(3, 4), 12)

    def test_mul_negative(self):
        self.assertEqual(self.c.mul(-2, 3), -6)

    def test_div(self):
        self.assertEqual(self.c.div(10, 2), 5)

    def test_div_float(self):
        self.assertEqual(self.c.div(1, 4), 0.25)

    def test_div_by_zero(self):
        with self.assertRaises(ValueError) as ctx:
            self.c.div(1, 0)
        self.assertEqual(str(ctx.exception), 'division by zero')

    def test_pow(self):
        self.assertEqual(self.c.pow(2, 3), 8)

    def test_pow_zero_exp(self):
        self.assertEqual(self.c.pow(2, 0), 1)

    def test_pow_negative_exp(self):
        self.assertEqual(self.c.pow(2, -1), 0.5)

    def test_mod(self):
        self.assertEqual(self.c.mod(7, 3), 1)

    def test_mod_negative(self):
        self.assertEqual(self.c.mod(-7, 3), 2)

    def test_mod_by_zero(self):
        with self.assertRaises(ValueError) as ctx:
            self.c.mod(1, 0)
        self.assertEqual(str(ctx.exception), 'modulo by zero')

    def test_sqrt(self):
        self.assertEqual(self.c.sqrt(9), 3.0)

    def test_sqrt_zero(self):
        self.assertEqual(self.c.sqrt(0), 0.0)

    def test_sqrt_float(self):
        self.assertEqual(self.c.sqrt(2.25), 1.5)

    def test_sqrt_negative(self):
        with self.assertRaises(ValueError) as ctx:
            self.c.sqrt(-1)
        self.assertEqual(str(ctx.exception), 'sqrt of negative number')


if __name__ == '__main__':
    unittest.main()
