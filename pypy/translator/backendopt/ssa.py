from pypy.objspace.flow.model import Variable, mkentrymap, flatten, Block
from pypy.tool.algo.unionfind import UnionFind

class DataFlowFamilyBuilder:
    """Follow the flow of the data in the graph.  Builds a UnionFind grouping
    all the variables by families: each family contains exactly one variable
    where a value is stored into -- either by an operation or a merge -- and
    all following variables where the value is just passed unmerged into the
    next block.
    """

    def __init__(self, graph):
        # Build a list of "unification opportunities": for each block and each
        # 'n', an "opportunity" groups the block's nth input variable with
        # the nth output variable from each of the incoming links, in a list:
        # [Block, blockvar, linkvar, linkvar, linkvar...]
        opportunities = []
        opportunities_with_const = []
        for block, links in mkinsideentrymap(graph).items():
            assert links
            for n, inputvar in enumerate(block.inputargs):
                vars = [block, inputvar]
                put_in = opportunities
                for link in links:
                    var = link.args[n]
                    if not isinstance(var, Variable):
                        put_in = opportunities_with_const
                    vars.append(var)
                # if any link provides a Constant, record this in
                # the opportunities_with_const list instead
                put_in.append(vars)
        self.opportunities = opportunities
        self.opportunities_with_const = opportunities_with_const
        self.variable_families = UnionFind()

    def complete(self):
        # An "opportunitiy" that lists exactly two distinct variables means that
        # the two variables can be unified.  We maintain the unification status
        # in 'variable_families'.  When variables are unified, it might reduce
        # the number of distinct variables and thus open other "opportunities"
        # for unification.
        variable_families = self.variable_families
        any_progress_at_all = False
        progress = True
        while progress:
            progress = False
            pending_opportunities = []
            for vars in self.opportunities:
                repvars = [variable_families.find_rep(v1) for v1 in vars[1:]]
                repvars_without_duplicates = dict.fromkeys(repvars)
                count = len(repvars_without_duplicates)
                if count > 2:
                    # cannot unify now, but maybe later?
                    pending_opportunities.append(vars[:1] + repvars)
                elif count == 2:
                    # unify!
                    variable_families.union(*repvars_without_duplicates)
                    progress = True
            self.opportunities = pending_opportunities
            any_progress_at_all |= progress
        return any_progress_at_all

    def merge_identical_phi_nodes(self):
        variable_families = self.variable_families
        any_progress_at_all = False
        progress = True
        while progress:
            progress = False
            block_phi_nodes = {}   # in the SSA sense
            for vars in self.opportunities + self.opportunities_with_const:
                block, blockvar = vars[:2]
                linksvars = vars[2:]   # from the incoming links (vars+consts)
                linksvars = [variable_families.find_rep(v) for v in linksvars]
                phi_node = (block,) + tuple(linksvars) # ignoring n and blockvar
                if phi_node in block_phi_nodes:
                    # already seen: we have two phi nodes in the same block that
                    # get exactly the same incoming vars.  Identify the results.
                    blockvar1 = block_phi_nodes[phi_node]
                    if variable_families.union(blockvar1, blockvar)[0]:
                        progress = True
                else:
                    block_phi_nodes[phi_node] = blockvar
            any_progress_at_all |= progress
        return any_progress_at_all

    def get_variable_families(self):
        self.complete()
        return self.variable_families


def SSI_to_SSA(graph):
    """Rename the variables in a flow graph as much as possible without
    violating the SSA rule.  'SSI' means that each Variable in a flow graph is
    defined only once in the whole graph; all our graphs are SSI.  This
    function does not break that rule, but changes the 'name' of some
    Variables to give them the same 'name' as other Variables.  The result
    looks like an SSA graph.  'SSA' means that each var name appears as the
    result of an operation only once in the whole graph, but it can be
    passed to other blocks across links.
    """
    variable_families = DataFlowFamilyBuilder(graph).get_variable_families()
    # rename variables to give them the name of their familiy representant
    for v in variable_families.keys():
        v1 = variable_families.find_rep(v)
        if v1 != v:
            v.set_name_from(v1)

    # sanity-check that the same name is never used several times in a block
    variables_by_name = {}
    for block in flatten(graph):
        if not isinstance(block, Block):
            continue
        vars = [op.result for op in block.operations]
        for link in block.exits:
            vars += link.getextravars()
        assert len(dict.fromkeys([v.name for v in vars])) == len(vars), (
            "duplicate variable name in %r" % (block,))
        for v in vars:
            variables_by_name.setdefault(v.name, []).append(v)
    # sanity-check that variables with the same name have the same concretetype
    for vname, vlist in variables_by_name.items():
        vct = [getattr(v, 'concretetype', None) for v in vlist]
        assert vct == vct[:1] * len(vct), (
            "variables called %s have mixed concretetypes: %r" % (vname, vct))

# ____________________________________________________________

def mkinsideentrymap(graph_or_blocks):
    # graph_or_blocks can be a full FunctionGraph, or a mapping
    # {block: reachable-from-outside-flag}.
    if isinstance(graph_or_blocks, dict):
        blocks = graph_or_blocks
        entrymap = {}
        for block in blocks:
            for link in block.exits:
                if link.target in blocks and not blocks[link.target]:
                    entrymap.setdefault(link.target, []).append(link)
        return entrymap
    else:
        graph = graph_or_blocks
        entrymap = mkentrymap(graph)
        del entrymap[graph.startblock]
        return entrymap

def variables_created_in(block):
    result = {}
    for v in block.inputargs:
        result[v] = True
    for op in block.operations:
        result[op.result] = True
    return result


def SSA_to_SSI(graph_or_blocks, annotator=None):
    """Turn a number of blocks belonging to a flow graph into valid (i.e. SSI)
    form, assuming that they are only in SSA form (i.e. they can use each
    other's variables directly, without having to pass and rename them along
    links).

    'graph_or_blocks' can be a graph, or just a dict that lists some blocks
    from a graph, as follows: {block: reachable-from-outside-flag}.
    """
    from pypy.translator.unsimplify import copyvar

    entrymap = mkinsideentrymap(graph_or_blocks)
    builder = DataFlowFamilyBuilder(graph_or_blocks)
    variable_families = builder.get_variable_families()
    del builder

    pending = []     # list of (block, var-used-but-not-defined)

    for block in entrymap:
        variables_created = variables_created_in(block)
        variables_used = {}
        for op in block.operations:
            for v in op.args:
                variables_used[v] = True
        variables_used[block.exitswitch] = True
        for link in block.exits:
            for v in link.args:
                variables_used[v] = True

        for v in variables_used:
            if isinstance(v, Variable):
                if v not in variables_created:
                    pending.append((block, v))

    while pending:
        block, v = pending.pop()
        v_rep = variable_families.find_rep(v)
        variables_created = variables_created_in(block)
        if v in variables_created:
            continue     # already ok
        for w in variables_created:
            w_rep = variable_families.find_rep(w)
            if v_rep is w_rep:
                # 'w' is in the same family as 'v', so we can simply
                # reuse its value for 'v'
                block.renamevariables({v: w})
                break
        else:
            # didn't find it.  Add it to all incoming links.
            try:
                links = entrymap[block]
            except KeyError:
                raise Exception("SSA_to_SSI failed: no way to give a value to"
                                " %r in %r" % (v, block))
            w = copyvar(annotator, v)
            variable_families.union(v, w)
            block.renamevariables({v: w})
            block.inputargs.append(w)
            for link in links:
                link.args.append(v)
                pending.append((link.prevblock, v))
