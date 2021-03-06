"""
Reviewed 03-06-22
Sequence-iteration is correctly implemented, thoroughly
tested, and complete. The only missing feature is support
for function-iteration.
"""
from pypy.objspace.std.objspace import *


class W_AbstractSeqIterObject(W_Object):
    from pypy.objspace.std.itertype import iter_typedef as typedef
    
    def __init__(w_self, w_seq, index=0):
        if index < 0:
            index = 0
        w_self.w_seq = w_seq
        w_self.index = index

class W_SeqIterObject(W_AbstractSeqIterObject):
    """Sequence iterator implementation for general sequences."""

class W_FastSeqIterObject(W_AbstractSeqIterObject):
    """Sequence iterator specialized for lists or tuples, accessing
    directly their RPython-level list of wrapped objects.
    """
    def __init__(w_self, w_seq, wrappeditems):
        W_AbstractSeqIterObject.__init__(w_self, w_seq)
        w_self.wrappeditems = wrappeditems

class W_ReverseSeqIterObject(W_Object):
    from pypy.objspace.std.itertype import reverse_iter_typedef as typedef
    
    def __init__(w_self, space, w_seq, index=-1):
        w_self.w_seq = w_seq
        w_self.w_len = space.len(w_seq)
        w_self.index = space.int_w(w_self.w_len) + index


registerimplementation(W_SeqIterObject)
registerimplementation(W_FastSeqIterObject)
registerimplementation(W_ReverseSeqIterObject)

def iter__SeqIter(space, w_seqiter):
    return w_seqiter

def next__SeqIter(space, w_seqiter):
    if w_seqiter.w_seq is None:
        raise OperationError(space.w_StopIteration, space.w_None) 
    try:
        w_item = space.getitem(w_seqiter.w_seq, space.wrap(w_seqiter.index))
    except OperationError, e:
        w_seqiter.w_seq = None
        if not e.match(space, space.w_IndexError):
            raise
        raise OperationError(space.w_StopIteration, space.w_None) 
    w_seqiter.index += 1 
    return w_item

def len__SeqIter(space,  w_seqiter):
    if w_seqiter.w_seq is None:
        return space.wrap(0)
    index = w_seqiter.index
    w_length = space.len(w_seqiter.w_seq)
    w_len = space.sub(w_length, space.wrap(index))
    if space.is_true(space.lt(w_len,space.wrap(0))):
        w_len = space.wrap(0)
    return w_len


def iter__FastSeqIter(space, w_seqiter):
    return w_seqiter

def next__FastSeqIter(space, w_seqiter):
    if w_seqiter.wrappeditems is None:
        raise OperationError(space.w_StopIteration, space.w_None)
    index = w_seqiter.index
    try:
        w_item = w_seqiter.wrappeditems[index]
    except IndexError:
        w_seqiter.wrappeditems = None
        w_seqiter.w_seq = None
        raise OperationError(space.w_StopIteration, space.w_None) 
    w_seqiter.index = index + 1
    return w_item

def len__FastSeqIter(space, w_seqiter):
    if w_seqiter.wrappeditems is None:
        return space.wrap(0)
    totallength = len(w_seqiter.wrappeditems)
    remaining = totallength - w_seqiter.index
    if remaining < 0:
        remaining = 0
    return space.wrap(remaining)


def iter__ReverseSeqIter(space, w_seqiter):
    return w_seqiter

def next__ReverseSeqIter(space, w_seqiter):
    if w_seqiter.w_seq is None or w_seqiter.index < 0:
        raise OperationError(space.w_StopIteration, space.w_None) 
    try:
        w_item = space.getitem(w_seqiter.w_seq, space.wrap(w_seqiter.index))
        w_seqiter.index -= 1 
    except OperationError, e:
        w_seqiter.w_seq = None
        if not e.match(space, space.w_IndexError):
            raise
        raise OperationError(space.w_StopIteration, space.w_None) 
    return w_item

def len__ReverseSeqIter(space, w_seqiter):
    if w_seqiter.w_seq is None:
        return space.wrap(0)
    index = w_seqiter.index+1
    w_length = space.len(w_seqiter.w_seq)
    # if length of sequence is less than index :exhaust iterator
    if space.is_true(space.gt(space.wrap(w_seqiter.index), w_length)):
        w_len = space.wrap(0)
        w_seqiter.w_seq = None
    else:
        w_len =space.wrap(index)
    if space.is_true(space.lt(w_len,space.wrap(0))):
        w_len = space.wrap(0)
    return w_len

register_all(vars())
