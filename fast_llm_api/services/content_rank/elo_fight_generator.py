import re
import openai
import random
import json
import asyncio
import aiohttp
import time

from typing import List
from fast_llm_api.services.models import OneStudentEntry
from fast_llm_api.helpers.async_llm_helpers import chatgpt_list_grammar_mistakes, chatgpt_evaluate_creativity, chatgpt_evaluate_coherence, chatgpt_evaluate_depth, chatgpt_compare_grammar, chatgpt_compare_coherence, chatgpt_compare_creativity, chatgpt_compare_depth

def update_elo(entry_a, entry_b, result, score_type):
    k = 32
    expected_a = 1 / (1 + 10 ** ((entry_b[score_type] - entry_a[score_type]) / 400))
    expected_b = 1 / (1 + 10 ** ((entry_a[score_type] - entry_b[score_type]) / 400))
    
    if result == "A":
        entry_a[score_type] += k * (1 - expected_a)
        entry_b[score_type] += k * (0 - expected_b)
    elif result == "B":
        entry_a[score_type] += k * (0 - expected_a)
        entry_b[score_type] += k * (1 - expected_b)
    elif result == "DRAW":
        entry_a[score_type] += k * (0.5 - expected_a)
        entry_b[score_type] += k * (0.5 - expected_b)


async def evaluate_all_entries(student_entries):
    tasks = []
    for entry in student_entries:
        tasks.append(chatgpt_evaluate_creativity(entry['answer']))
        tasks.append(chatgpt_evaluate_depth(entry['answer']))
        tasks.append(chatgpt_evaluate_coherence(entry['answer']))
        tasks.append(chatgpt_list_grammar_mistakes(entry['answer']))

    results = await asyncio.gather(*tasks)

    for i, entry in enumerate(student_entries):
        entry['creativity_score'] = extract_number(results[4 * i])
        entry['depth_score'] = extract_number(results[4 * i + 1])
        entry['coherence_score'] = extract_number(results[4 * i + 2])
        entry['grammar_mistakes'] = results[4 * i + 3]
        entry['grammar_mistake_count'] = len(entry['grammar_mistakes'])
        
        # Initialize Elo scores based on the initial evaluation scores (creativity, depth, coherence, grammar)
        entry['elo_creativity'] = 600 + (entry['creativity_score'] - 1) * 100
        entry['elo_depth'] = 600 + (entry['depth_score'] - 1) * 100
        entry['elo_coherence'] = 600 + (entry['coherence_score'] - 1) * 100
        entry['elo_grammar'] = 600 + (10 - entry['grammar_mistake_count']) * 100  # Assuming fewer grammar mistakes are better
    
    return student_entries

async def elo_fights(student_entries, num_folds):
    for fold in range(num_folds):
        # Sort entries by the average Elo across all factors
        student_entries.sort(key=lambda x: (x['elo_creativity'] + x['elo_depth'] + x['elo_coherence'] + x['elo_grammar']) / 4)
        
        tasks = []
        for entry in student_entries:
            closest_opponent = select_opponent(student_entries, entry)
            if closest_opponent:
                tasks.append(chatgpt_compare_creativity(entry['answer'], closest_opponent['answer']))
                tasks.append(chatgpt_compare_depth(entry['answer'], closest_opponent['answer']))
                tasks.append(chatgpt_compare_coherence(entry['answer'], closest_opponent['answer']))
                tasks.append(chatgpt_compare_grammar(entry['answer'], entry['grammar_mistakes'], closest_opponent['answer'], closest_opponent['grammar_mistakes']))

        results = await asyncio.gather(*tasks)
        
        for j, entry in enumerate(student_entries):
            closest_opponent = select_opponent(student_entries, entry)
            update_elo(entry, closest_opponent, results[4 * j], 'elo_creativity')
            update_elo(entry, closest_opponent, results[4 * j + 1], 'elo_depth')
            update_elo(entry, closest_opponent, results[4 * j + 2], 'elo_coherence')
            update_elo(entry, closest_opponent, results[4 * j + 3], 'elo_grammar')
            
    return student_entries

def select_opponent(student_entries, current_entry):
    current_score = (current_entry['elo_creativity'], current_entry['elo_depth'], current_entry['elo_coherence'], current_entry['elo_grammar'])
    possible_opponents = [entry for entry in student_entries if entry['id'] != current_entry['id']]
    if not possible_opponents:
        return None
    # Sort by the sum of differences in all Elo scores
    opponents_sorted_by_score = sorted(possible_opponents, key=lambda x: abs(x['elo_creativity'] - current_score[0]) + abs(x['elo_depth'] - current_score[1]) + abs(x['elo_coherence'] - current_score[2]) + abs(x['elo_grammar'] - current_score[3]))
    return opponents_sorted_by_score[0]

def extract_number(text):
    try:
        return int(next(s for s in text.split() if s.isdigit()))
    except (ValueError, StopIteration):
        raise ValueError(f"Could not extract a number from the text: {text}")


# Main function to execute the asynchronous process
async def generate_elo_results(student_entries: List[OneStudentEntry], num_folds=20):

    evaluated_entries = await evaluate_all_entries(student_entries)
    elo_results = await elo_fights(evaluated_entries, num_folds)
    
    return elo_results
