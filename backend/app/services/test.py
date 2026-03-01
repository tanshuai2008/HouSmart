import pandas as pd

url = "https://huggingface.co/datasets/KJJ231/redfin-data/resolve/main/city_market_tracker.tsv000.gz"

df = pd.read_csv(url, sep="\t", compression="gzip", nrows=5)

print(df.head())