#!/usr/bin/env python3
# benchmarks.py ---
#
# Filename: benchmarks.py
# Author: Arjun Radhakrishna
# Created: Wed, 01 Jun 2016 11:27:20 -0400
#
#
# Copyright (c) 2015, Arjun Radhakrishna, University of Pennsylvania
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

from bitvectors import BitVector
import parser
import expr_transforms
import random
import verifiers
import termsolvers
import termsolvers_lia
import specifications
import unifiers
import unifiers_lia
import solvers
import exprs
import enumerators
import exprtypes
import semantics_core
import semantics_bv
import semantics_types
import semantics_lia
import semantics_slia
import synthesis_context
import grammars

def get_pbe_valuations(constraints, synth_fun):
    valuations = []
    for constraint in constraints:
        if not exprs.is_application_of(constraint, 'eq') and \
                not exprs.is_application_of(constraint, '='):
            return None
        if len(exprs.get_all_variables(constraint)) > 0:
            return None
        arg_func, arg_other = None, None
        for a in constraint.children:
            if exprs.is_application_of(a, synth_fun):
                arg_func = a
            else:
                arg_other = a
        if arg_func is None or arg_other is None:
            return None
        valuations.append((arg_func.children, arg_other))
    return valuations

def massage_constraints(syn_ctx, macro_instantiator, uf_instantiator, theory, constraints):
    # Instantiate all macro functions
    constraints = [ macro_instantiator.instantiate_all(c)
            for c in constraints ]

    # for c in constraints:
    #     print(exprs.expression_to_string(c))
    # print('Ackermann Reduction')
    constraints = expr_transforms.AckermannReduction.apply(constraints, uf_instantiator, syn_ctx)
    # for c in constraints:
    #     print(exprs.expression_to_string(c))
    # print('let flattener')
    constraints = expr_transforms.LetFlattener.apply(constraints, syn_ctx)
    # for c in constraints:
    #     print(exprs.expression_to_string(c))
    # print('Rewrite ite')
    constraints = expr_transforms.RewriteITE.apply(constraints, syn_ctx)
    # for c in constraints:
    #     print(exprs.expression_to_string(c))
    # constraints, full_constraint_expr = expr_transforms.to_cnf(constraints, theory, syn_ctx)

    # Rewrite ITE?
    return constraints

def rewrite_solution(synth_funs, solution, reverse_mapping):
    # Rewrite any predicates introduced in grammar decomposition
    if reverse_mapping is not None:
        for function_info, cond, orig_expr_template, expr_template in reverse_mapping:
            while True:
                app = exprs.find_application(solution, function_info.function_name)
                if app is None:
                    break
                assert exprs.is_application_of(expr_template, 'ite')

                ite = exprs.parent_of(solution, app)
                ite_without_dummy = exprs.FunctionExpression(ite.function_info, (app.children[0], ite.children[1], ite.children[2]))
                var_mapping = exprs.match(expr_template, ite_without_dummy)
                new_ite = exprs.substitute_all(orig_expr_template, var_mapping.items())
                solution = exprs.substitute(solution, ite, new_ite)

    # Rewrite back into formal parameters
    if len(synth_funs) == 1:
        sols = [solution]
    else:
        sols = solution.children

    rewritten_solutions = []
    for sol, synth_fun in zip(sols, synth_funs):
        variables = exprs.get_all_formal_parameters(sol)
        substitute_pairs = []
        orig_vars = synth_fun.get_named_vars()
        for v in variables:
            substitute_pairs.append((v, orig_vars[v.parameter_position]))
        sol = exprs.substitute_all(sol, substitute_pairs)
        rewritten_solutions.append(sol)

    return rewritten_solutions

def _merge_grammars(sf_grammar_list):
    start = "MergedStart"
    nts = [start]
    nt_type = {}
    rules = {}
    starts = []
    for sf_name, sf_obj, grammar in sf_grammar_list:
        prefix = sf_name
        renamed_grammar = grammar.add_prefix(sf_name)
        nts.extend(renamed_grammar.non_terminals)
        nt_type.update(renamed_grammar.nt_type)
        rules.update(renamed_grammar.rules)
        starts.append(renamed_grammar.start)
    comma_function = semantics_core.CommaFunction([ nt_type[s] for s in starts ])
    rules[start] = [ grammars.FunctionRewrite(comma_function,
            *tuple([ grammars.NTRewrite(s, nt_type[s]) for s in starts ])) ]
    nt_type[start] = None
    merged_grammar = grammars.Grammar(nts, nt_type, rules, start)

    return merged_grammar

def make_specification(synth_funs, theory, syn_ctx, constraints):
    if not expr_transforms.is_single_invocation(constraints, theory, syn_ctx):
        specification = specifications.MultiPointSpec(syn_ctx.make_function_expr('and', *constraints),
                syn_ctx, synth_funs)
        syn_ctx.assert_spec(specification, synth_funs)
        verifier = verifiers.MultiPointVerifier(syn_ctx)
    elif len(synth_funs) == 1 and get_pbe_valuations(constraints, synth_funs[0]) is not None:
        synth_fun = synth_funs[0]
        valuations = get_pbe_valuations(constraints, synth_fun)
            # print("Using PBE specifications")
        specification = specifications.PBESpec(valuations, synth_fun, theory)
        syn_ctx.assert_spec(specification, synth_funs)
        verifier = verifiers.PBEVerifier(syn_ctx)
    else:
        # print("Using standard specifications")
        spec_expr = constraints[0] if len(constraints) == 1 \
                else syn_ctx.make_function_expr('and', *constraints)
        specification = specifications.StandardSpec(spec_expr, syn_ctx, synth_funs, theory)
        syn_ctx.assert_spec(specification, synth_funs)
        verifier = verifiers.StdVerifier(syn_ctx)
    return specification, verifier

def full_lia_grammars(grammar_map):
    for grammar in grammar_map.values():
        if not grammar.from_default:
            return False
    return True

def make_unification_solver(theory, syn_ctx, synth_funs, grammar_map, specification, verifier):
    if theory == 'LIA' and full_lia_grammars(grammar_map) and all([sf.range_type == exprtypes.IntType() for sf in synth_funs ]):
        term_solver = termsolvers_lia.SpecAwareLIATermSolver(specification.term_signature, specification)
        unifier = unifiers_lia.SpecAwareLIAUnifier(None, term_solver, synth_funs, syn_ctx, specification)
        solver = solvers.Solver(syn_ctx)
        solutions = solver.solve(
                enumerators.NullGeneratorFactory(),
                term_solver,
                unifier,
                verifier,
                verify_term_solve=True
                )
        solution = next(solutions)
        final_solution = rewrite_solution(synth_funs, solution, reverse_mapping=None)
    else:
        if len(synth_funs) > 1:
            print("Using memoryless esolver: Multi fun Single invocation")
            return esolver(syn_ctx, synth_funs, grammar_map, specification, verifier, mode='Classic')
        synth_fun = synth_funs[0]
        grammar = grammar_map[synth_fun]

        ans = grammar.decompose(syn_ctx.macro_instantiator)
        if ans == None:
            print("Using classic esolver: Grammar not decomposable")
            return esolver(syn_ctx, [synth_fun], {synth_fun:grammar}, specification, verifier, mode='Classic')

        term_grammar, pred_grammar, reverse_mapping = ans
        generator_factory = enumerators.RecursiveGeneratorFactory()
        term_generator = term_grammar.to_generator(generator_factory)
        pred_generator = pred_grammar.to_generator(generator_factory)
        solver = solvers.Solver(syn_ctx)
        term_solver = termsolvers.PointlessTermSolver(specification.term_signature, term_generator)
        unifier = unifiers.PointlessEnumDTUnifier(pred_generator, term_solver, synth_fun, syn_ctx)
        solver = solvers.Solver(syn_ctx)
        # solution = solvers._do_solve(solver, generator_factory, term_solver, unifier, verifier, False)
        solutions = solver.solve(
                generator_factory,
                term_solver,
                unifier,
                verifier,
                verify_term_solve=True
                )
        solution = next(solutions)
        final_solution = rewrite_solution([synth_fun], solution, reverse_mapping)
    return final_solution

def esolver(syn_ctx, synth_funs, grammar_map, specification, verifier, mode):
    assert mode in [ 'Classic', 'Memoryless' ]

    if mode == 'Classic':
        generator_factory = enumerators.PointDistinctGeneratorFactory()
        TermSolver = termsolvers.PointDistinctTermSolver
    else:
        generator_factory = enumerators.RecursiveGeneratorFactory()
        TermSolver = termsolvers.PointlessTermSolver

    # Grammars and generators
    if len(synth_funs) > 1:
        sf_list = [ (synth_fun.function_name, synth_fun, grammar_map[synth_fun])
            for synth_fun in synth_funs ]
        grammar = _merge_grammars(sf_list)
    else:
        grammar = grammar_map[synth_funs[0]]
    term_generator = grammar.to_generator(generator_factory)

    # Term solver, unifier, and verifiers
    term_solver = TermSolver(specification.term_signature, term_generator)
    term_solver.one_term_coverage = True
    unifier = unifiers.NullUnifier(None, term_solver, synth_funs, syn_ctx, specification)

    solver = solvers.Solver(syn_ctx)
    solutions = solver.solve(
            generator_factory,
            term_solver,
            unifier,
            verifier,
            verify_term_solve=False
            )
    solution = next(solutions)
    rewritten_solutions = rewrite_solution(synth_funs, solution, reverse_mapping=None)
    return rewritten_solutions

def make_solver(file_sexp):
    benchmark_tuple = parser.extract_benchmark(file_sexp)
    (
            theories,
            syn_ctx,
            synth_instantiator,
            macro_instantiator,
            uf_instantiator,
            constraints,
            grammar_map,
            forall_vars_map
            ) = benchmark_tuple

    assert len(theories) == 1
    theory = theories[0]

    constraints = massage_constraints(syn_ctx, macro_instantiator, uf_instantiator, theory, constraints)
    synth_funs = list(synth_instantiator.get_functions().values())

    specification, verifier = make_specification(synth_funs, theory, syn_ctx, constraints)

    if expr_transforms.is_single_invocation(constraints, theory, syn_ctx):
        final_solutions = make_unification_solver(theory, syn_ctx, synth_funs, grammar_map, specification, verifier)
    else:
        if len(synth_funs) > 1:
            print("Using memoryless esolver: Multi fun Multi invocation")
        else:
            print("Using memoryless esolver: Not single invocation")
        spec_expr = syn_ctx.make_function_expr('and', *constraints)
        synth_funs = list(synth_instantiator.get_functions().values())
        final_solutions = esolver(syn_ctx, synth_funs, grammar_map, specification, verifier, mode='Memoryless')
    for sf, sol in zip(synth_funs, final_solutions):
        fp_string = ' '.join([ '(%s %s)' % 
            (v.variable_info.variable_name, v.variable_info.variable_type.print_string()) 
            for v in sf.get_named_vars() ])
        print('(define-fun %s (%s) %s\n     %s)' % (sf.function_name, fp_string, sf.range_type.print_string(), exprs.expression_to_string(sol)))

# Tests:

def test_make_solver(benchmark_files):
    import parser

    # for benchmark_file in [ "../benchmarks/max/max_2.sl", "../benchmarks/max/max_3.sl" ]:
    # for benchmark_file in [ "../benchmarks/SyGuS-COMP15/GENERAL-Track/qm_max3.sl" ]:
    # for benchmark_file in [ "../benchmarks/SyGuS-COMP15/INV-Track/inv-benchmarks-temp/sum1.sl" ]:
    # for benchmark_file in [ "../benchmarks/icfp/icfp_105_1000.sl" ]:
    # for benchmark_file in [ "../benchmarks/one_off/max_plus_1.sl" ]:
    for benchmark_file in benchmark_files:
        print("Doing", benchmark_file)
        file_sexp = parser.sexpFromFile(benchmark_file)
        make_solver(file_sexp)

def find_grammar_anamolies():
    import os
    for folder, subs, files in os.walk('../benchmarks/SyGuS-COMP15/'):
        for filename in files:
            if not filename.endswith('.sl'):
                continue
            benchmark_file = os.path.join(folder, filename)
            # print("Doing", benchmark_file)
            try:
            # if True:
                file_sexp = parser.sexpFromFile(benchmark_file)
                benchmark_tuple = parser.extract_benchmark(file_sexp)
            except Exception:
                print('Failed', benchmark_file)


if __name__ == "__main__":
    import sys
    benchmark_files = sys.argv[1:]
    test_make_solver(benchmark_files)
    # find_grammar_anamolies()
