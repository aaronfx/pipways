import pandas as pd
import io


def parse_statement(file_bytes, filename):

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_bytes))

    else:
        raise Exception("Unsupported file format")

    df.columns = [c.lower().strip() for c in df.columns]

    if "profit" not in df.columns:
        raise Exception("Profit column not detected")

    return df
