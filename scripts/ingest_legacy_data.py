import os
import pandas as pd

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
 
# Create Supabase client
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# CSV file
CSV_FILE = r"D:\AgneticAI_Learning\FDE\Logistic_SupplyChain\data\raw\dynamic_supply_chain_logistics_dataset.csv"

# Supabase table
TABLE_NAME = "logistics_data"

# Read CSV
df = pd.read_csv(CSV_FILE)

print("CSV Shape:", df.shape)
print("Columns:", df.columns.tolist())

# Convert timestamp
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
).dt.strftime("%Y-%m-%dT%H:%M:%S")

# Replace NaN with None
df = df.where(pd.notnull(df), None)

# Convert to dictionary records
records = df.to_dict(orient="records")

# Batch size
BATCH_SIZE = 500

# Upload in batches
for i in range(0, len(records), BATCH_SIZE):

    batch = records[i:i + BATCH_SIZE]

    try:

        response = (
            supabase
            .table(TABLE_NAME)
            .insert(batch)
            .execute()
        )

        print(
            f"Uploaded: "
            f"{min(i + BATCH_SIZE, len(records))}"
            f"/{len(records)}"
        )

    except Exception as e:

        print(f"Upload failed at batch {i}: {e}")

print("CSV upload completed!")