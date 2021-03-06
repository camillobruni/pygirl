
import _rawffi
import sys

keepalive_key = str # XXX fix this when provided with test

def store_reference(where, base_key, target):
    #self.__dict__['_objects'][key] = value._objects
    if '_objects' in where.__dict__:
        # shortcut
        where.__dict__['_objects'][str(base_key)] = target
        return
    key = [base_key]
    while not '_objects' in where.__dict__:
        key.append(where.__dict__['_index'])
        where = where.__dict__['_base']
    real_key = ":".join([str(i) for i in key])
    where.__dict__['_objects'][real_key] = target

class ArgumentError(Exception):
    pass

class _CDataMeta(type):
    def from_param(self, value):
        if isinstance(value, self):
            return value
        try:
            as_parameter = value._as_parameter_
        except AttributeError:
            raise TypeError("expected %s instance instead of %s" % (
                self.__name__, type(value).__name__))
        else:
            return self.from_param(as_parameter)

    def _CData_input(self, value):
        """Used when data enters into ctypes from user code.  'value' is
        some user-specified Python object, which is converted into a _rawffi
        array of length 1 containing the same value according to the
        type 'self'.
        """
        cobj = self.from_param(value)
        return cobj, cobj._get_buffer_for_param()

    def _CData_value(self, value):
        cobj = self.from_param(value)
        # we don't care here if this stuff will live afterwards, as we're
        # interested only in value anyway
        return cobj._get_buffer_value()

    def _CData_output(self, resbuffer, base=None, index=-1, needs_free=False):
        assert isinstance(resbuffer, _rawffi.ArrayInstance)
        """Used when data exits ctypes and goes into user code.
        'resbuffer' is a _rawffi array of length 1 containing the value,
        and this returns a general Python object that corresponds.
        """
        res = self.__new__(self)
        res.__dict__['_buffer'] = resbuffer
        res.__dict__['_base'] = base
        res.__dict__['_index'] = index
        res.__dict__['_needs_free'] = needs_free
        return res.__ctypes_from_outparam__()

    def _CData_retval(self, resbuffer):
        return self._CData_output(resbuffer, needs_free=True)

    def __mul__(self, other):
        from _ctypes.array import create_array_type
        return create_array_type(self, other)

    def _is_pointer_like(self):
        return False

    def in_dll(self, dll, name):
        buffer = dll._handle.getprimitive(self._ffishape, name)
        val = self.__new__(self)
        val._buffer = buffer
        return val

class CArgObject(object):
    """ simple wrapper around buffer, just for the case of freeing
    it afterwards
    """
    def __init__(self, buffer):
        self._buffer = buffer

    def __del__(self):
        self._buffer.free()
        self._buffer = None

class _CData(object):
    """ The most basic object for all ctypes types
    """
    __metaclass__ = _CDataMeta
    _objects = None

    def __init__(self, *args, **kwds):
        raise TypeError("%s has no type" % (type(self),))

    def __ctypes_from_outparam__(self):
        return self

    def _get_buffer_for_param(self):
        return self

    def _get_buffer_value(self):
        return self._buffer[0]

def sizeof(tp):
    if not isinstance(tp, _CDataMeta):
        if isinstance(tp, _CData):
            tp = type(tp)
        else:
            raise TypeError("ctypes type or instance expected, got %r" % (
                type(tp).__name__,))
    return tp._sizeofinstances()

def alignment(tp):
    if not isinstance(tp, _CDataMeta):
        if isinstance(tp, _CData):
            tp = type(tp)
        else:
            raise TypeError("ctypes type or instance expected, got %r" % (
                type(tp).__name__,))
    return tp._alignmentofinstances()

def byref(cdata):
    from ctypes import pointer
    return pointer(cdata)

def cdata_from_address(self, address):
    # fix the address, in case it's unsigned
    address = address & (sys.maxint * 2 + 1)
    instance = self.__new__(self)
    lgt = getattr(self, '_length_', 1)
    instance._buffer = self._ffiarray.fromaddress(address, lgt)
    return instance

def addressof(tp):
    return tp._buffer.buffer
