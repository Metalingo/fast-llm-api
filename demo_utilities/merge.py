

import pandas as pd

# Load the three CSV files into separate DataFrames
# common_filename = "private_datasets_2nd/elementary_low"
common_filename = "private_datasets_2nd/middle"


df1 = pd.read_csv(f'{common_filename}_content_ranking.csv')
df2 = pd.read_csv(f'{common_filename}_additional_analysis.csv')
df3 = pd.read_csv(f'{common_filename}_final_res_transcribed.csv')

# Merge the DataFrames on the 'id' column
combined_df = df1.merge(df2, on='id').merge(df3, on='id')

# Save the combined DataFrame to a new CSV file
combined_df.to_csv(f'{common_filename}_combined.csv', index=False, encoding='utf-8-sig')

# Display the combined DataFrame
print(combined_df)

