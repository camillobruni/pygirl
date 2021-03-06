from pypy.module.marshal import interp_marshal
from pypy.interpreter.error import OperationError
import sys


class AppTestMarshalMore:

    def test_long_0(self):
        import marshal
        z = 0L
        z1 = marshal.loads(marshal.dumps(z))
        assert z == z1

    def test_unmarshal_int64(self):
        # test that we can unmarshal 64-bit ints on 32-bit platforms
        # (of course we only test that if we're running on such a
        # platform :-)
        import marshal
        z = marshal.loads('I\x00\xe4\x0bT\x02\x00\x00\x00')
        assert z == 10000000000
        z = marshal.loads('I\x00\x1c\xf4\xab\xfd\xff\xff\xff')
        assert z == -10000000000
