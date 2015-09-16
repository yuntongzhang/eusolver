#!/usr/bin/env python3
# expr_transforms.py ---
#
# Filename: expr_transforms.py
# Author: Abhishek Udupa
# Created: Wed Sep  2 18:19:39 2015 (-0400)
#
#
# Copyright (c) 2015, Abhishek Udupa, University of Pennsylvania
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by The University of Pennsylvania
# 4. Neither the name of the University of Pennsylvania nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

# Code:

import utils
import exprs
import exprtypes
import semantics_types
import itertools
import functools

# if __name__ == '__main__':
#     utils.print_module_misuse_and_exit()

class ExprTransformerBase(object):
    def __init__(self, transform_name):
        self.transform_name = transform_name
        self.expr_stack = []

    def _matches_expression(self, expr_object, fun_name):
        return (expr_object.expr_kind == exprs.ExpressionKinds.function_expression and
                expr_object.function_info.function_name == fun_name)

    def _matches_expression_any(self, expr_object, *fun_names):
        fun_name_set = set(fun_names)
        if (expr_object.expr_kind != exprs.ExpressionKinds.function_expression):
            return False
        return (expr_object.function_info.function_name in fun_name_set)


class NNFConverter(ExprTransformerBase):
    def __init__(self):
        super().__init__('NNFConverter')

    def _eliminate_complex(self, expr_object, syn_ctx):
        kind = expr_object.expr_kind
        if (kind != exprs.ExpressionKinds.function_expression):
            return expr_object
        elif (not self._matches_expression_any(expr_object, 'and', 'or',
                                               'implies', 'iff', 'xor',
                                               'not')):
            return expr_object
        else:
            function_info = expr_object.function_info
            function_name = function_info.function_name
            transformed_children = [self._eliminate_complex(x, syn_ctx)
                                    for x in expr_object.children]
            if (function_name == 'implies'):
                c1 = syn_ctx.make_function_expr('not', transformed_children[0])
                return syn_ctx.make_ac_function_expr('or', c1, transformed_children[1])
            elif (function_name == 'iff'):
                c1 = transformed_children[0]
                c2 = transformed_children[1]
                not_c1 = syn_ctx.make_function_expr('not', c1)
                not_c2 = syn_ctx.make_function_expr('not', c2)
                c1_implies_c2 = syn_ctx.make_ac_function_expr('or', not_c1, c2)
                c2_implies_c1 = syn_ctx.make_ac_function_expr('or', not_c2, c1)
                return syn_ctx.make_ac_function_expr('and', c1_implies_c2, c2_implies_c1)
            elif (function_name == 'xor'):
                c1 = transformed_children[0]
                c2 = transformed_children[1]
                not_c1 = syn_ctx.make_function_expr('not', c1)
                not_c2 = syn_ctx.make_function_expr('not', c2)
                c1_and_not_c2 = syn_ctx.make_ac_function_expr('and', c1, not_c2)
                c2_and_not_c1 = syn_ctx.make_ac_function_expr('and', c2, not_c1)
                return syn_ctx.make_ac_function_expr('or', c1_and_not_c2, c2_and_not_c1)
            else:
                return syn_ctx.make_function_expr(function_name, *transformed_children)


    def _do_transform(self, expr_object, syn_ctx, polarity):
        kind = expr_object.expr_kind
        if (kind != exprs.ExpressionKinds.function_expression):
            return expr_object

        elif (not self._matches_expression_any(expr_object, 'and', 'or', 'not')):
            if (polarity):
                return expr_object
            else:
                return syn_ctx.make_function_expr('not', expr_object)

        else:
            function_info = expr_object.function_info
            function_name = function_info.function_name
            if (function_name == 'not'):
                child_polarity = (not polarity)
            else:
                child_polarity = polarity

            transformed_children = [self._eliminate_complex(x, syn_ctx)
                                    for x in expr_object.children]

            if (function_name == 'and'):
                if (polarity):
                    return syn_ctx.make_ac_function_expr('and', *transformed_children)
                else:
                    return syn_ctx.make_ac_function_expr('or', *transformed_children)
            elif (function_name == 'or'):
                if (polarity):
                    return syn_ctx.make_ac_function_expr('or', *transformed_children)
                else:
                    return syn_ctx.make_ac_function_expr('and', *transformed_children)
            elif (function_name == 'not'):
                return transformed_children[0]
            else:
                assert False


    def apply(self, *args):
        if (len(args) != 2):
            raise basetypes.ArgumentError('NNFConverter.apply() must be called with an ' +
                                          'expression object and a synthesis context object')
        simple_expr = self._eliminate_complex(args[0], args[1])
        return self._do_transform(simple_expr, args[1], True)

class CNFConverter(ExprTransformerBase):
    def __init__(self):
        super().__init__('CNFConverter')

    def _do_transform(self, expr_object, syn_ctx):
        """Requires: expression is in NNF."""

        kind = expr_object.expr_kind
        if (kind != exprs.ExpressionKinds.function_expression):
            return [expr_object]
        elif (not self._matches_expression_any(expr_object, 'and', 'or')):
            return [expr_object]
        else:
            function_info = expr_object.function_info
            num_children = len(expr_object.children)
            if (function_info.function_name == 'and'):
                clauses = []
                for i in range(num_children):
                    child = expr_object.children[i]
                    clauses.extend(self._do_transform(child, syn_ctx))
                return clauses
            elif (function_info.function_name == 'or'):
                transformed_children = []
                for i in range(num_children):
                    child = expr_object.children[i]
                    transformed_children.append(self._do_transform(child, syn_ctx))

                clauses = []
                for prod_tuple in itertools.product(*transformed_children):
                    clauses.append(syn_ctx.make_ac_function_expr('or', *prod_tuple))
                return clauses

    def apply(self, *args):
        if (len(args) != 2):
            raise basetypes.ArgumentError('CNFConverter.apply() must be called with ' +
                                          'an expression and a synthesis context object')
        nnf_converter = NNFConverter()
        nnf_expr = nnf_converter.apply(args[0], args[1])
        clauses = self._do_transform(nnf_expr, args[1])
        return (clauses, args[1].make_ac_function_expr('and', *clauses))

def check_expr_binding_to_context(expr, syn_ctx):
    kind = expr.expr_kind
    if (kind == exprs.ExpressionKinds.variable_expression):
        if (not syn_ctx.validate_variable(expr.variable_info)):
            raise TypeError(('Expression %s was not formed using the given ' +
                             'context!') % exprs.expression_to_string(expr))
    elif (kind == exprs.ExpressionKinds.function_expression):
        if (not syn_ctx.validate_function(expr.function_info)):
            raise TypeError(('Expression %s was not formed using the given ' +
                             'context!') % exprs.expression_to_string(expr))
        for child in expr.children:
            check_expr_binding_to_context(child, syn_ctx)
    elif (kind == exprs.ExpressionKinds.formal_parameter_expression):
        raise TypeError(('Expression %s contains a formal parameter! Specifications ' +
                         'are not allowed to contain formal ' +
                         'parameters!') % (exprs.expression_to_string(expr)))
    else:
        return

def _get_unknown_function_invocation_args(expr):
    kind = expr.expr_kind
    retval = set()
    if (kind == exprs.ExpressionKinds.function_expression):
        if (expr.function_info.function_kind == semantics_types.FunctionKinds.unknown_function):
            retval.add(expr.children)
        for child in expr.children:
            retval = retval | _get_unknown_function_invocation_args(child)
    return retval

def check_single_invocation_property(expr, syn_ctx = None):
    """Checks if the expression has only one unknown function, and also
    that the expression satisfies the single invocation property, i.e.,
    the unknown function appears only in one syntactic form in the expression."""
    if (not isinstance(expr, list)):
        unknown_function_set = gather_unknown_functions(expr)
    else:
        unknown_function_set = set()
        for clause in expr:
            unknown_function_set = unknown_function_set | gather_unknown_functions(clause)

    if (len(unknown_function_set) > 1):
        return False

    if (not isinstance(expr, list)):
        cnf_converter = CNFConverter()
        (clauses, cnf_expr) = cnf_converter.apply(expr, syn_ctx)
    else:
        clauses = expr

    for clause in clauses:
        fun_arg_tuples = _get_unknown_function_invocation_args(clause)
        if (len(fun_arg_tuples) > 1):
            return False
    return True

def _gather_variables(expr, accumulator):
    kind = expr.expr_kind
    if (kind == exprs.ExpressionKinds.variable_expression):
        accumulator.add(expr)
    elif (kind == exprs.ExpressionKinds.function_expression):
        for child in expr.children:
            _gather_variables(child, accumulator)

def gather_variables(expr):
    """Gets the set of variable expressions present in the expr."""
    var_set = set()
    _gather_variables(expr, var_set)
    return var_set

def _gather_unknown_functions(expr, fun_set):
    kind = expr.expr_kind
    if (kind == exprs.ExpressionKinds.function_expression):
        if (isinstance(expr.function_info, semantics_types.UnknownFunctionBase)):
            fun_set.add(expr.function_info)
        for child in expr.children:
            _gather_unknown_functions(child, fun_set)

def gather_unknown_functions(expr):
    fun_set = set()
    _gather_unknown_functions(expr, fun_set)
    return fun_set

def canonicalize_specification(expr, syn_ctx):
    """Performs a bunch of operations:
    1. Checks that the expr is "well-bound" to the syn_ctx object.
    2. Checks that the specification has the single-invocation property.
    3. Gathers the set of unknown functions (should be only one).
    4. Gathers the variables used in the specification.
    5. Converts the specification to CNF (as part of the single-invocation test)
    6. For each clause, returns a mapping from the formal arguments to terms
    Returns a tuple containing:
    1. A list of 'variable_info' objects corresponding to the variables used in the spec
    2. A list of unknown functions (should be a singleton list)
    3. A list of clauses corresponding to the CNF specification
    4. A list of NEGATED clauses
    5. A list of lists, one list for each clause, mapping the formal parameters
       to terms.
    """
    check_expr_binding_to_context(expr, syn_ctx)
    unknown_function_set = gather_unknown_functions(expr)
    variable_set = gather_variables(expr)

    unknown_function_list = list(unknown_function_set)
    variable_list = [expr.variable_info for expr in variable_set]
    variable_list.sort(key=lambda x: x.variable_name)
    num_vars = len(variable_list)
    num_funs = len(unknown_function_list)
    for i in range(num_vars):
        variable_list[i].variable_eval_offset = i
    for i in range(num_funs):
        unknown_function_list[i].unknown_function_id = i

    cnf_converter = CNFConverter()
    clauses, cnf_expr = cnf_converter.apply(expr, syn_ctx)
    neg_clauses = [syn_ctx.make_function_expr('not', clause) for clause in clauses]
    if (not check_single_invocation_property(clauses)):
        raise basetypes.ArgumentError('Spec:\n%s\nis not single-invocation!' %
                                      exprs.expression_to_string(expr))
    mapping_list = []
    for clause in clauses:
        arg_tuples = list(_get_unknown_function_invocation_args(clause))
        assert (len(arg_tuples) <= 1)
        if (len(arg_tuples) == 0):
            mapping_list.append([])
        else:
            mapping_list.append(list(arg_tuples[0]))

    return (variable_list, unknown_function_list, clauses, neg_clauses, mapping_list)

#######################################################################
# TEST CASES
#######################################################################

def test_cnf_conversion():
    import synthesis_context
    import semantics_core
    import semantics_lia
    syn_ctx = synthesis_context.SynthesisContext(semantics_core.CoreInstantiator(),
                                                 semantics_lia.LIAInstantiator())
    var_exprs = [syn_ctx.make_variable_expr(exprtypes.IntType(), 'x%d' % i) for i in range(10)]
    max_fun = syn_ctx.make_unknown_function('max', [exprtypes.IntType()] * 10,
                                            exprtypes.IntType())
    max_app = syn_ctx.make_function_expr(max_fun, *var_exprs)
    max_ge_vars = [syn_ctx.make_function_expr('ge', max_app, var_expr) for var_expr in var_exprs]
    max_eq_vars = [syn_ctx.make_function_expr('eq', max_app, var_expr) for var_expr in var_exprs]
    formula1 = syn_ctx.make_ac_function_expr('or', *max_eq_vars)
    formula2 = syn_ctx.make_ac_function_expr('and', *max_ge_vars)
    formula = syn_ctx.make_ac_function_expr('and', formula1, formula2)

    cnf_converter = CNFConverter()
    cnf_clauses, cnf_expr = cnf_converter.apply(formula, syn_ctx)
    print(exprs.expression_to_string(cnf_expr))
    print([exprs.expression_to_string(cnf_clause) for cnf_clause in cnf_clauses])

    print(check_single_invocation_property(formula, syn_ctx))
    binary_max = syn_ctx.make_unknown_function('max2', [exprtypes.IntType(),
                                                        exprtypes.IntType()],
                                               exprtypes.IntType())
    binary_max_app = syn_ctx.make_function_expr(binary_max, var_exprs[0], var_exprs[1])
    binary_max_app_rev = syn_ctx.make_function_expr(binary_max, var_exprs[1], var_exprs[0])
    non_separable = syn_ctx.make_function_expr('eq', binary_max_app, binary_max_app_rev)
    print(check_single_invocation_property(non_separable, syn_ctx))

    max_rec = syn_ctx.make_function_expr(binary_max, binary_max_app, binary_max_app)
    non_separable2 = syn_ctx.make_function_expr('eq', max_rec, binary_max_app)
    print(check_single_invocation_property(non_separable2, syn_ctx))

if __name__ == '__main__':
    test_cnf_conversion()

#
# expr_transforms.py ends here