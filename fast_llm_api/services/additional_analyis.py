import asyncio
import numpy as np
from typing import List
from fast_llm_api.services.models import OneStudentEntry
from fast_llm_api.helpers.async_llm_helpers import async_openai_call
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



async def chatgpt_evaluate_plagiarism_probability(text):
    prompt_plagiarism = f"""
        Consider the following text and make an informed guess on whether this reads as a plagiarized text. We understand that you don't have access to all kinds of databases, but answer with both your confidence (in LOW, MEDIUM, HIGH) in that the text sounds plagiarized and what you think it reads very similarly too.

        Consider the following text, and determine its probability of plagiarism.
        Output "LOW" if you think there is a low chance / zero chance it was plagiarized.
        Output "MEDIUM: <Source Text Name>" or "HIGH: <Source Text Name>" if you think it is plagiarized, and add "Source Text Name" accordingly to the source that the given text sounds a lot like.
        Keep in mind that students are completely allowed to quote real references, and that direct quotations do NOT constitute plagiarism. But pretending that it's their own work without proper quoting is what does.
        Do NOT explain your reasoning, only output "LOW", "MEDIUM: <Source Text Name>", OR "HIGH: <Source Text Name>", and no other texrt.

        Input Text: {text}
        """
    return await async_openai_call(prompt_plagiarism)

async def chatgpt_evaluate_story_probability(text):
    prompt_story = f"""
        Consider the following text and make an informed guess on whether this reads as a story, rather than an essay. We are trying to give a score for how story-like this text is, and we're expecting to receive mainly essays, so we're trying to filter out texts that are essays without theses.
        Please generate a score from 0 to 100 in 10 intervals, where:
        - 0 means it's a typical essay that is not a story (though it might have some small story-like elements), 
        - 50 if it's an essay driven mainly by a story, and 
        - 100 if this is just a story of a character going through a certain set of actions.
        
        Do NOT explain your reasoning, only output one of "0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100". Do not explain, only one of the eleven numbers, please.
        
        Input Text: {text}
        """
        
    return await async_openai_call(prompt_story)


async def evaluate_all_entries_story_plagiarism(student_entries):
    num_type_tasks = 2

    tasks = []
    for entry in student_entries:
        tasks.append(chatgpt_evaluate_plagiarism_probability(entry['answer']))
        tasks.append(chatgpt_evaluate_story_probability(entry['answer']))

    results = await asyncio.gather(*tasks)

    for i, entry in enumerate(student_entries):
        entry['plagiarism_score'] = results[num_type_tasks * i]
        entry['story_score'] = results[num_type_tasks * i + 1]

    return student_entries

async def cross_check_similarity(student_entries, similarity_threshold):
    
    ids = list([item["id"] for item in student_entries])
    texts = list([item["answer"] for item in student_entries])

    text_vectors = TfidfVectorizer().fit_transform(texts)
    for text_index, _ in enumerate(texts):
        reference_vector = text_vectors[text_index:text_index+1]
        
        cosine_sim = cosine_similarity(reference_vector, text_vectors).flatten()

        cosine_sim[text_index] = -np.inf # mask the vector itself
        best_idx = cosine_sim.argmax()
        # if cosine_sim[best_idx] >= similarity_threshold:
        #     similarity_text = f"ID: {ids[best_idx]} / 유사도: {cosine_sim[best_idx]}"
        # else:
        #     similarity_text = f"없음 / 1위 유사도: {ids[best_idx]}, 유사도 {cosine_sim[best_idx]}"
        
        student_entries[text_index]["best_similarity_id"] = ids[best_idx]
        student_entries[text_index]["best_similarity_score"] = cosine_sim[best_idx]


    return student_entries


# Main function to execute the asynchronous process
async def generate_function(student_entries: List[OneStudentEntry], similarity_threshold):
    evaluated_entries = await evaluate_all_entries_story_plagiarism(student_entries)
    final_results = await cross_check_similarity(evaluated_entries, similarity_threshold)
    
    return final_results


