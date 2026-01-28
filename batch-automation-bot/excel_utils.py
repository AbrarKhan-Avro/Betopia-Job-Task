import pandas as pd

def load_excel(path):
    df = pd.read_excel(path)
    return df

def save_excel(df, path):
    df.to_excel(path, index=False)
