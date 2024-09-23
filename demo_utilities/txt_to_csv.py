import os
import csv

# Directory and CSV file paths
# directory = 'private_datasets/중등부'
# csv_file_name = 'private_datasets/input_processed/middle_school.csv'

directory = 'private_datasets/초등부저학년'
csv_file_name = 'private_datasets/input_processed/elementary_school.csv'

# List to store the contents of all .txt files along with their IDs
texts_with_ids = []

# Iterate through all files in the specified directory
for filename in os.listdir(directory):
    if filename.endswith('.txt'):
        # Extract the ID from the filename (assuming format is {ID}.txt)
        student_id = filename.split('.')[0]  # Gets the part before '.txt'
        
        # Open and read the file
        with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
            content = file.read()
            texts_with_ids.append({'id': student_id, 'Student Text': content})

# Write the contents to a CSV file
with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['id', 'Student Text'])
    
    # Write the header
    writer.writeheader()
    
    # Write the contents
    for entry in texts_with_ids:
        writer.writerow(entry)

print(f"Texts with IDs have been successfully written to {csv_file_name}.")
