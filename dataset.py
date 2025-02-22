import sqlite3
from pathlib import Path

import pandas as pd

from datasets import Dataset, DatasetDict


def extract_climbs_from_db(db_path):
    try:
        conn = sqlite3.connect(db_path)

        # Check if climbs table exists
        check_table_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='climbs';
        """
        cursor = conn.cursor()
        table_exists = cursor.execute(check_table_query).fetchone()

        if not table_exists:
            print(f"Warning: No 'climbs' table found in {db_path}")
            conn.close()
            return None

        query = """
        SELECT 
            uuid,
            layout_id,
            setter_id,
            setter_username,
            name,
            description,
            hsm,
            edge_left,
            edge_right,
            edge_bottom,
            edge_top,
            angle,
            frames_count,
            frames_pace,
            frames,
            is_draft,
            is_listed,
            created_at
        FROM climbs
        """

        df = pd.read_sql_query(query, conn)

        if len(df) == 0:
            print(f"Warning: No data found in {db_path}")
            conn.close()
            return None

        # Add source database as a column
        df["source_db"] = Path(db_path).stem

        # Keep frames as raw string - no parsing needed

        # Convert boolean columns
        df["is_draft"] = df["is_draft"].astype(bool)
        df["is_listed"] = df["is_listed"].astype(bool)

        # Convert timestamp
        df["created_at"] = pd.to_datetime(df["created_at"])

        conn.close()
        return df
    except sqlite3.Error as e:
        print(f"Error with database {db_path}: {e}")
        return None


def create_hf_dataset():
    db_files = list(Path("./db").glob("*.db"))

    if not db_files:
        raise ValueError("No .db files found in ./db directory")

    all_dfs = []
    for db_file in db_files:
        print(f"Processing {db_file.stem}...")
        df = extract_climbs_from_db(db_file)
        if df is not None:
            all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No valid data found in any database files")

    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Create features dictionary for dataset info
    features = {
        "uuid": "string",
        "layout_id": "int64",
        "setter_id": "int64",
        "setter_username": "string",
        "name": "string",
        "description": "string",
        "hsm": "int64",
        "edge_left": "int64",
        "edge_right": "int64",
        "edge_bottom": "int64",
        "edge_top": "int64",
        "angle": "int64",
        "frames_count": "int64",
        "frames_pace": "int64",
        "frames": "string",  # Raw string
        "is_draft": "bool",
        "is_listed": "bool",
        "created_at": "timestamp[ns]",
        "source_db": "string",
    }

    dataset = Dataset.from_pandas(combined_df)

    # Create train/test/validation splits (80/10/10)
    train_test = dataset.train_test_split(test_size=0.2, seed=42)
    test_valid = train_test["test"].train_test_split(test_size=0.5, seed=42)

    dataset_dict = DatasetDict(
        {
            "train": train_test["train"],
            "test": test_valid["train"],
            "validation": test_valid["test"],
        }
    )

    return dataset_dict


if __name__ == "__main__":
    dataset = create_hf_dataset()

    print("\nDataset Statistics:")
    for split in dataset.keys():
        print(f"{split}: {len(dataset[split])} examples")

    dataset.save_to_disk("datasets/climbs")
    dataset.push_to_hub("mattzcarey/climbs")