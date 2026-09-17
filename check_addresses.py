import pandas as pd

# قراءة الإكسيل
df = pd.read_excel("donors.xlsx")
df.columns = df.columns.str.strip()

# استخراج كل العناوين وإزالة الفراغات والـ Null
addresses = df['العنوان'].dropna().unique().tolist()

print(addresses)