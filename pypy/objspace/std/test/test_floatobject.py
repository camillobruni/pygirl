from pypy.objspace.std import floatobject as fobj
from pypy.objspace.std.objspace import FailedToImplement
import py

class TestW_FloatObject:

    def _unwrap_nonimpl(self, func, *args, **kwds):
        """ make sure that the expected exception occurs, and unwrap it """
        try:
            res = func(*args, **kwds)
            raise Exception, "should have failed but returned '%s'!" %repr(res)
        except FailedToImplement, arg:
            return arg.w_type

    def test_pow_fff(self):
        x = 10.0
        y = 2.0
        z = 13.0
        f1 = fobj.W_FloatObject(x)
        f2 = fobj.W_FloatObject(y)
        f3 = fobj.W_FloatObject(z)
        assert self.space.w_TypeError == (
                          self._unwrap_nonimpl(fobj.pow__Float_Float_ANY,
                                               self.space, f1, f2, f3))

    def test_pow_ffn(self):
        x = 10.0
        y = 2.0
        f1 = fobj.W_FloatObject(x)
        f2 = fobj.W_FloatObject(y)
        v = fobj.pow__Float_Float_ANY(self.space, f1, f2, self.space.w_None)
        assert v.floatval == x ** y
        f1 = fobj.W_FloatObject(-1.23)
        f2 = fobj.W_FloatObject(-4.56)
        assert self.space.w_ValueError == (
                          self._unwrap_nonimpl(fobj.pow__Float_Float_ANY,
                                               self.space, f1, f2,
                                               self.space.w_None))
        x = -10
        y = 2.0
        f1 = fobj.W_FloatObject(x)
        f2 = fobj.W_FloatObject(y)
        v = fobj.pow__Float_Float_ANY(self.space, f1, f2, self.space.w_None)
        assert v.floatval == x**y

class AppTestAppFloatTest:
    def test_negatives(self):
        assert -1.1 < 0
        assert -0.1 < 0

    def test_float_callable(self):
        assert 0.125 == float(0.125)

    def test_float_int(self):
        assert 42.0 == float(42)

    def test_float_hash(self):
        # these are taken from standard Python, which produces
        # the same but for -1.
        import math
        assert hash(42.0) == 42
        assert hash(42.125) == 1413677056
        assert hash(math.ldexp(0.125, 1000)) in (
            32,              # answer on 32-bit machines
            137438953472)    # answer on 64-bit machines
        # testing special overflow values
        assert hash(1e200 * 1e200) == 314159
        assert hash(-1e200 * 1e200) == -271828

    def test_int_float(self):
        assert int(42.1234) == 42
        assert int(4e10) == 40000000000L

    def test_float_string(self):
        assert 42 == float("42")
        assert 42.25 == float("42.25")

    def test_float_unicode(self):
        # u00A0 and u2000 are some kind of spaces
        assert 42.75 == float(unichr(0x00A0)+unicode("42.75")+unichr(0x2000))

    def test_float_long(self):
        assert 42.0 == float(42L)
        assert 10000000000.0 == float(10000000000L)
        raises(OverflowError, float, 10**400)
        
        
    def test_round(self):
        assert 1.0 == round(1.0)
        assert 1.0 == round(1.1)
        assert 2.0 == round(1.9)
        assert 2.0 == round(1.5)
        assert -2.0 == round(-1.5)
        assert -2.0 == round(-1.5)
        assert -2.0 == round(-1.5, 0)
        assert -2.0 == round(-1.5, 0)
        assert 22.2 == round(22.222222, 1)
        assert 20.0 == round(22.22222, -1)
        assert 0.0 == round(22.22222, -2)

    def test_special_float_method(self):
        class a:
            def __float__(self): 
                self.ar = True 
                return None
        inst = a()
        raises(TypeError, float, inst) 
        assert inst.ar 

        class b: 
            pass 
        raises((AttributeError, TypeError), float, b()) 

    def test_getnewargs(self):
        assert  0.0 .__getnewargs__() == (0.0,)


    def test_pow(self):
        def pw(x, y):
            return x ** y
        def espeq(x, y):
            return not abs(x-y) > 1e05
        raises(ZeroDivisionError, pw, 0.0, -1)
        assert pw(0, 0.5) == 0.0
        assert espeq(pw(4.0, 0.5), 2.0)
        assert pw(4.0, 0) == 1.0
        assert pw(-4.0, 0) == 1.0
        raises(ValueError, pw, -1.0, 0.5)
        assert pw(-1.0, 2.0) == 1.0
        assert pw(-1.0, 3.0) == -1.0
        assert pw(-1.0, 1e200) == 1.0

    def test_pow_neg_base(self):
        def pw(x, y):
            return x ** y
        assert pw(-2.0, 2.0) == 4
        
    def test_float_cmp(self):
        assert 12.5 == 12.5
        assert 12.5 != -3.2
        assert 12.5 < 123.4
        assert .25 <= .25
        assert -5744.23 <= -51.2
        assert 4.3 > 2.3
        assert 0.01 >= -0.01
        # float+long
        verylonglong = 10L**400
        infinite = 1e200*1e200
        assert 12.0 == 12L
        assert 1e300 == long(1e300)
        assert 12.1 != 12L
        assert infinite != 123456789L
        assert 12.9 < 13L
        assert -infinite < -13L
        assert 12.9 <= 13L
        assert 13.0 <= 13L
        assert 13.01 > 13L
        assert 13.0 >= 13L
        assert 13.01 >= 13L
        assert infinite > verylonglong
        assert infinite >= verylonglong
        assert 1234.56 < verylonglong
        assert 1234.56 <= verylonglong
        # long+float
        assert 12L == 12.0
        assert long(1e300) == 1e300
        assert 12L != 12.1
        assert 123456789L != infinite
        assert 13L > 12.9
        assert -13L > -infinite
        assert 13L >= 12.9
        assert 13L >= 13.0
        assert 13L < 13.01
        assert 13L <= 13.0
        assert 13L <= 13.01
        assert verylonglong < infinite
        assert verylonglong <= infinite
        assert verylonglong > 1234.56
        assert verylonglong >= 1234.56
