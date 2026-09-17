import pandas as pd

df = pd.read_excel("new_data.xlsx")
print("العواميد اللي بايثون شايفها بالظبط هي:")
print(df.columns.tolist())