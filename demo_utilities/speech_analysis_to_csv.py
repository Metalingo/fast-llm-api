import json
import pandas as pd

# speech_json_file = "private_datasets_2nd/elementary_low_final_res_transcribed.json"
speech_json_file = "private_datasets_2nd/middle_final_res_transcribed.json"

speech_dataset = json.load(open(speech_json_file, "r"))


df = pd.DataFrame.from_dict(speech_dataset, orient='index')

# Reset index to move the keys into a column named 'id'
df.reset_index(inplace=True)

# Rename the index column to 'id'
df.rename(columns={'index': 'id'}, inplace=True)

# Apply the replacement in the 'id' column
df['id'] = df['id'].str.replace('.wav', '')

# Output the DataFrame
print(df)

# Save as CSV (optional)
df.to_csv(speech_json_file.replace(".json", ".csv"), index=False, encoding='utf-8-sig')