import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Path Variables
# TXT_FOLDER_PATH = 'private_datasets/초등부저학년/'
# WRITING_SCORES_PATH = 'private_datasets/writing_elementary_low_final_res.csv'
# SPEAKING_SCORES_PATH = 'private_datasets/speaking_elementary_low_final_res.csv'
# OUTPUT_CSV_PATH = 'elementary_low_student_writing_speaking_scores_sorted.csv'

TXT_FOLDER_PATH = 'private_datasets/중등부/'
WRITING_SCORES_PATH = 'private_datasets/writing_middle_final_res.csv'
SPEAKING_SCORES_PATH = 'private_datasets/speaking_middle_final_res.csv'
OUTPUT_CSV_PATH = 'middle_student_writing_speaking_scores_sorted.csv'



# Column Names
WRITING_TEXT_COLUMN = '학생 글'
WRITING_SUM_SCORE_COLUMN = 'Sum score'
SPEAKING_FILE_PATH_COLUMN = 'file_path'
SPEAKING_SCORE_COLUMN = 'with_stt_toatal_score'

# Parameters
SIMILARITY_THRESHOLD = 0.99
SCORE_RATIO = (0.7, 0.3)  # 7:3 ratio for Speaking:Writing

# Function to extract STUDENT_ID from a file path (without .txt or .wav)
def extract_student_id(file_name):
    return os.path.splitext(file_name)[0]

# Function to read txt files and return a dictionary of {STUDENT_ID: text content}
def read_txt_files(folder_path):
    student_texts = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):
            student_id = extract_student_id(file_name)
            with open(os.path.join(folder_path, file_name), 'r', encoding='utf-8') as f:
                content = f.read().strip()
            student_texts[student_id] = content
    return student_texts

# Function to find the best match for a given text based on similarity
def find_best_match(text, text_dict, threshold=SIMILARITY_THRESHOLD):
    ids = list(text_dict.keys())
    texts = list(text_dict.values())
    
    # Use TF-IDF vectorizer to calculate cosine similarity between the given text and all others
    vectorizer = TfidfVectorizer().fit_transform([text] + texts)
    cosine_sim = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()
    
    # Find the index of the best match if it exceeds the similarity threshold
    best_idx = cosine_sim.argmax()
    if cosine_sim[best_idx] >= threshold:
        return ids[best_idx]
    return None

# Step 1: Load the writing scores from CSV
writing_scores_df = pd.read_csv(WRITING_SCORES_PATH)
writing_scores_df[WRITING_TEXT_COLUMN] = writing_scores_df[WRITING_TEXT_COLUMN].astype(str)  # Ensure all text is treated as string

# Step 2: Load the speaking analysis data
speaking_analysis_df = pd.read_csv(SPEAKING_SCORES_PATH)

# Step 3: Extract STUDENT_ID from file paths in the speaking analysis
speaking_analysis_df['Student ID'] = speaking_analysis_df[SPEAKING_FILE_PATH_COLUMN].apply(extract_student_id)

# Step 4: Read the text files from the txt-datasets/ folder
student_texts = read_txt_files(TXT_FOLDER_PATH)

# Step 5: Match writing scores to student IDs based on text similarity
matched_data = []
for _, row in writing_scores_df.iterrows():
    writing_text = row[WRITING_TEXT_COLUMN]
    
    # Find the best matching student ID for the given writing text
    student_id = find_best_match(writing_text, student_texts)
    
    if student_id:
        # Add all columns from the writing_scores_df, including '학생 글'
        row_data = row.to_dict()
        row_data['Student ID'] = student_id
        matched_data.append(row_data)

# Step 6: Create a DataFrame with the matched writing scores
matched_df = pd.DataFrame(matched_data)

# Step 7: Merge with the speaking analysis data, keeping all columns from both datasets
final_df = pd.merge(matched_df, speaking_analysis_df, on='Student ID', how='inner')

# Step 8: Calculate the composite score based on SCORE_RATIO
final_df['Composite Score'] = (
    final_df[SPEAKING_SCORE_COLUMN] * SCORE_RATIO[0] + final_df[WRITING_SUM_SCORE_COLUMN] * SCORE_RATIO[1]
)

# Step 9: Rename 'Sum score' to 'Writing Sum Score'
final_df = final_df.rename(columns={WRITING_SUM_SCORE_COLUMN: 'Writing Sum Score'})

# Step 10: Reorder the columns as specified
column_order = [
    SPEAKING_FILE_PATH_COLUMN,  # 'file_path'
    WRITING_TEXT_COLUMN,        # '학생 글'
    'with_stt_toatal_score',     # 'without_stt_final_score'
    'Writing Sum Score',         # 'Writing Sum Score'
    # Add the rest of the columns in their existing order
] + [col for col in final_df.columns if col not in ['file_path', '학생 글', 'Writing Sum Score', 'with_stt_toatal_score']]

final_df = final_df[column_order]

# Step 11: Sort the rows by the composite score in descending order
final_df = final_df.sort_values(by='Composite Score', ascending=False)

# Step 12: Save the final result to a CSV with utf-8-sig encoding
final_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')

print(f"Matching completed, scores calculated, and CSV file saved to {OUTPUT_CSV_PATH}.")
