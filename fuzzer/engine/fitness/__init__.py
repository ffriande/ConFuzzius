#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def fitness_function(indv, env):
    block_coverage_fitness = compute_branch_coverage_fitness(env.individual_branches[indv.hash], env.code_coverage)
    if env.args.data_dependency:
        data_dependency_fitness = compute_data_dependency_fitness(indv, env.data_dependencies)
        return block_coverage_fitness + data_dependency_fitness
    return block_coverage_fitness

def compute_branch_coverage_fitness(branches, pcs):
    non_visited_branches = 0.0

    for jumpi in branches:
        for destination in branches[jumpi]:
            if not branches[jumpi][destination] and destination not in pcs:
                non_visited_branches += 1

    return non_visited_branches

def compute_data_dependency_fitness(indv, data_dependencies):
    data_dependency_fitness = 0.0
    all_reads = set()

    for d in data_dependencies:
        all_reads.update(data_dependencies[d]["read"])

    for i in indv.chromosome:
        _function_hash = i["arguments"][0]
        if _function_hash in data_dependencies:
            for i in data_dependencies[_function_hash]["write"]:
                if i in all_reads:
                    data_dependency_fitness += 1

    return data_dependency_fitness

def fitness_function_ddu(indv, env):
    if indv.hash in env.spectrum.gen_indvs_ddu_scores:
        ddu_fit = env.spectrum.gen_indvs_ddu_scores[indv.hash]
    else:
        print("FAIL DDU FETCH = ", ddu_fit)
        ddu_fit = 0.0

    if env.args.data_dependency:
        data_dependency_fit = compute_data_dependency_fitness(indv, env.data_dependencies)
        
        if len(env.data_dependencies) == 0:
            data_dependency_fit_normalized = 0
        else:
            data_dependency_fit_normalized = data_dependency_fit / (len(env.data_dependencies))

        return ddu_fit + data_dependency_fit_normalized

    return ddu_fit