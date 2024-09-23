import re
import openai
import random
import json
import asyncio
import aiohttp
import time

OPENAI_MODEL = "gpt-4o-mini"

MAX_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2

async def async_openai_call(prompt, retries=MAX_RETRIES):
    for attempt in range(retries):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai.api_key}"
            }
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an evaluator."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
                try:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                except KeyError:
                    print(f"Error: {result}")
                    if 'error' in result and 'rate limit' in result['error'].get('message', '').lower():
                        wait_time = RETRY_BACKOFF_FACTOR ** attempt
                        print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    raise
    raise Exception("Max retries exceeded")

async def chatgpt_evaluate_creativity(text):
    prompt = f"""
    Evaluate the creativity of the following text on a scale of 1 to 12, where 1 is very basic or unoriginal and 12 is exceptionally creative and original. Be mindful that these were written by elementary school students. Provide only the number as the response. Use the following rubric:
    - 1-2: Student makes overly simple statements with 2-4 words per sentence.
    - 3-4: Student uses simple adjectives and descriptors to otherwise simple statements with 4-7 words per sentence.
    - 5-6: Student uses somewhat complex adjectives and descriptors to describe otherwise generic events.
    - 7-8: Satisfies 5-6, while explaining some unique experiences with some common elements.
    - 9-10: Satisfies 7-8, but the student portrays a minimal but existing amount of original thought and perspective.
    - 11: Explains unique experiences, unique perspectives, and shows unique character traits of the writer.
    - 12: While satisfying the conditions for an 11, the reader walks away thought-provoked by the writing.
    
    Text: {text}
    """
    return await async_openai_call(prompt)

async def chatgpt_evaluate_depth(text):
    prompt = f"""
    Evaluate the depth of the following text on a scale of 1 to 12, where 1 is very shallow or surface-level and 12 is exceptionally deep, profound, and comprehensive. Be mindful that these were written by elementary school students. Provide only the number as the response. Use the following rubric:
    - 1-2: Student makes overly simple statements with 2-4 words per sentence.
    - 3-4: Student uses simple adjectives and descriptors to otherwise simple statements with 4-7 words per sentence.
    - 5-6: Student uses somewhat complex adjectives and descriptors to describe simple explorations and insight.
    - 7-8: Satisfies 5-6, moderate depth, with some detailed exploration and insight.
    - 9-10: Satisfies 7-8, deep exploration, insightful and well-developed ideas.
    - 11: Explains unique experiences, unique perspectives, and shows unique character traits of the writer.
    - 12: While satisfying the conditions for an 11, the reader walks away thought-provoked by the writing.
    
    Text: {text}
    """
    return await async_openai_call(prompt)

async def chatgpt_evaluate_coherence(text):
    prompt = f"""
    Evaluate the coherence of the following text on a scale of 1 to 5, where 1 means very hard to understand or comprehend and 5 means that the text can be understood easily. We are not evaluating the depth/creativity of the writing, just how comprehensible and coherent the content is. Be mindful that these were written by elementary school students. Provide only the number as the response. Use the following rubric:
    - 1: The reader can understand less than 20% of the information the writer meant to convey.
    - 2: The reader can understand more than 20% but less than 40% of the information the writer meant to convey.
    - 3: The reader can understand more than 40% but less than 60% of the information the writer meant to convey.
    - 4: The reader can understand more than 60% but less than 80% of the information the writer meant to convey.
    - 5: The reader has no trouble understanding what the writer meant to convey.

    Text: {text}
    """
    return await async_openai_call(prompt)

async def chatgpt_list_grammar_mistakes(text):
    prompt = f"""
    List only strict grammatical mistakes in the following text in the form of a JSON array of dictionaries with the keys: start_idx, end_idx, original_text, corrected_text, and mistake_category. Do not correct punctuation or conjugations, or any of these "trivial" mistakes. The mistake_category should be a short note like a teacher would write when grading essays. The input text is a transcription, not an essay, so we must only pick very specific grammar mistakes and do not pick out syntactical, punctuational, etc the technical mistakes. Ensure the output is a valid JSON array. If there are no mistakes, return an empty array "[]".

    Text: {text}
    """
    response = await async_openai_call(prompt)
    try:
        # Preprocess the response to ensure it is a valid JSON array
        cleaned_response = re.sub(r'[^ -~]', '', response)  # Remove non-printable characters
        cleaned_response = cleaned_response.strip().strip('```json').strip('```').strip()
        cleaned_response = cleaned_response.replace(';', ',')  # Replace semicolons with commas
        grammar_mistakes = json.loads(cleaned_response)
        return grammar_mistakes
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Response: {response}")
        print(f"Cleaned Response: {cleaned_response}")
        return []

async def chatgpt_compare_creativity(text_a, text_b):
    prompt = f"""
    Compare the following two texts and determine which one is more creative. 
    
    Just as reference, here is a rubric for an absolute measure:
    ```Evaluate the creativity of the following text on a scale of 1 to 12, where 1 is very basic or unoriginal and 12 is exceptionally creative and original. Be mindful that these were written by elementary school students. Provide only the number as the response. Use the following rubric:
    - 1-2: Student makes overly simple statements with 2-4 words per sentence.
    - 3-4: Student uses simple adjectives and descriptors to otherwise simple statements with 4-7 words per sentence.
    - 5-6: Student uses somewhat complex adjectives and descriptors to describe otherwise generic events.
    - 7-8: Satisfies 5-6, while explaining some unique experiences with some common elements.
    - 9-10: Satisfies 7-8, but the student portrays a minimal but existing amount of original thought and perspective.
    - 11: Explains unique experiences, unique perspectives, and shows unique character traits of the writer.
    - 12: While satisfying the conditions for an 11, the reader walks away thought-provoked by the writing.```

    Compare the following two texts and determine which one is more creative. 
    Provide "A", "B", or "DRAW" only as the response. Choose "DRAW" only if the texts are truly indistinguishable:
    Text A: {text_a}
    Text B: {text_b}
    """
    return await async_openai_call(prompt)

async def chatgpt_compare_depth(text_a, text_b):
    prompt = f"""
    Compare the following two texts and determine which one has more depth. 
    
    Just as reference, here is a rubric for an absolute measure:
    ```Evaluate the depth of the following text on a scale of 1 to 12, where 1 is very shallow or surface-level and 12 is exceptionally deep, profound, and comprehensive. Be mindful that these were written by elementary school students. Provide only the number as the response. Use the following rubric:
    - 1-2: Student makes overly simple statements with 2-4 words per sentence.
    - 3-4: Student uses simple adjectives and descriptors to otherwise simple statements with 4-7 words per sentence.
    - 5-6: Student uses somewhat complex adjectives and descriptors to describe simple explorations and insight.
    - 7-8: Satisfies 5-6, moderate depth, with some detailed exploration and insight.
    - 9-10: Satisfies 7-8, deep exploration, insightful and well-developed ideas.
    - 11: Explains unique experiences, unique perspectives, and shows unique character traits of the writer.
    - 12: While satisfying the conditions for an 11, the reader walks away thought-provoked by the writing.```
    
    Compare the following two texts and determine which one has more depth. 
    Provide "A", "B", or "DRAW" only as the response. Choose "DRAW" only if the texts are truly indistinguishable:
    Text A: {text_a}
    Text B: {text_b}
    """
    return await async_openai_call(prompt)

async def chatgpt_compare_coherence(text_a, text_b):
    prompt = f"""
    Compare the following two texts and determine which one is more coherent. 
    
    Just as reference, here is a rubric for an absolute measure:
    ```Evaluate the coherence of the following text on a scale of 1 to 5, where 1 means very hard to understand or comprehend and 5 means that the text can be understood easily. Provide only the number as the response. Use the following rubric:
    - 1: The reader can understand less than 20% of the information the writer meant to convey.
    - 2: The reader can understand more than 20% but less than 40% of the information the writer meant to convey.
    - 3: The reader can understand more than 40% but less than 60% of the information the writer meant to convey.
    - 4: The reader can understand more than 60% but less than 80% of the information the writer meant to convey.
    - 5: The reader has no trouble understanding what the writer meant to convey.```

    Compare the following two texts and determine which one is more coherent. 
    Provide "A", "B", or "DRAW" only as the response. Choose "DRAW" only if the texts are truly indistinguishable:
    Text A: {text_a}
    Text B: {text_b}
    """
    return await async_openai_call(prompt)

async def chatgpt_compare_grammar(text_a, text_a_mistakes, text_b, text_b_mistakes):
    prompt = f"""
    Compare the grammar skills of the following two texts and determine which one has better grammar skills. Consider the number and types of mistakes listed for each text, as well as the overall complexity and correctness of the grammar used.

    Text A: {text_a}
    Mistakes A: {json.dumps(text_a_mistakes)}

    Text B: {text_b}
    Mistakes B: {json.dumps(text_b_mistakes)}

    Provide "A", "B", or "DRAW" only as the response. Choose "DRAW" only if the texts are truly indistinguishable.
    """
    return await async_openai_call(prompt)
