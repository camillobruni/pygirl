from pypy.objspace.flow.model import Block, Variable, Constant
from pypy.rpython.lltypesystem.lltype import Void
from pypy.translator.backendopt.support import log
from pypy.translator import simplify
from pypy import conftest

def remove_unaryops(graph, opnames):
    """Removes unary low-level ops with a name appearing in the opnames list.
    """
    positions = []
    for block in graph.iterblocks():
        for i, op in enumerate(block.operations):
            if op.opname in opnames:
                positions.append((block, i))
    while positions:
        block, index = positions.pop()
        op_result = block.operations[index].result
        op_arg = block.operations[index].args[0]
        # replace the new variable (op_result) with the old variable
        # (from all subsequent positions)
        for op in block.operations[index:]:
            if op is not None:
                for i in range(len(op.args)):
                    if op.args[i] == op_result:
                        op.args[i] = op_arg
                if (op.opname == "indirect_call"
                    and isinstance(op.args[0], Constant)):
                    op.opname = "direct_call"
                    op.args = op.args[:-1]
        for link in block.exits:
            for i in range(len(link.args)):
                if link.args[i] == op_result:
                    link.args[i] = op_arg
        if block.exitswitch == op_result:
            if isinstance(op_arg, Variable):
                block.exitswitch = op_arg
            else:
                simplify.replace_exitswitch_by_constant(block, op_arg)
        block.operations[index] = None
       
    # remove all operations
    for block in graph.iterblocks():
        if block.operations:
            block.operations[:] = filter(None, block.operations)

def remove_same_as(graph):
    remove_unaryops(graph, ["same_as"])

def remove_duplicate_casts(graph, translator):
    simplify.join_blocks(graph)
    num_removed = 0
    # remove chains of casts
    for block in graph.iterblocks():
        comes_from = {}
        for op in block.operations:
            if op.opname == "cast_pointer":
                if op.args[0] in comes_from:
                    from_var = comes_from[op.args[0]]
                    comes_from[op.result] = from_var
                    if from_var.concretetype == op.result.concretetype:
                        op.opname = "same_as"
                        op.args = [from_var]
                        num_removed += 1
                    else:
                        op.args = [from_var]
                else:
                    comes_from[op.result] = op.args[0]
    if num_removed:
        remove_same_as(graph)
    # remove duplicate casts
    for block in graph.iterblocks():
        available = {}
        for op in block.operations:
            if op.opname == "cast_pointer":
                key = (op.args[0], op.result.concretetype)
                if key in available:
                    op.opname = "same_as"
                    op.args = [available[key]]
                    num_removed += 1
                else:
                    available[key] = op.result
            elif op.opname == 'resume_point':
                available.clear()
    if num_removed:
        remove_same_as(graph)
        # remove casts with unused results
        for block in graph.iterblocks():
            used = {}
            for link in block.exits:
                for arg in link.args:
                    used[arg] = True
            for i, op in list(enumerate(block.operations))[::-1]:
                if op.opname == "cast_pointer" and op.result not in used:
                    del block.operations[i]
                    num_removed += 1
                else:
                    for arg in op.args:
                        used[arg] = True
        if translator.config.translation.verbose:
            log.removecasts(
                "removed %s cast_pointers in %s" % (num_removed, graph.name))
    return num_removed

def remove_superfluous_keep_alive(graph):
    for block in graph.iterblocks():
        used = {}
        for i, op in list(enumerate(block.operations))[::-1]:
            if op.opname == "keepalive":
                if op.args[0] in used:
                    del block.operations[i]
                else:
                    used[op.args[0]] = True
 

