import pandas as pd
from db.database import get_db_connection

def fetch_logs_as_dataframe():
    """
    Fetches all logs from the database and returns them as a pandas DataFrame.
    """
    conn = get_db_connection()
    if not conn:
        print("Could not connect to the database to fetch logs.")
        return pd.DataFrame()

    try:
        df = pd.read_sql("SELECT * FROM logs ORDER BY timestamp", conn)
        return df
    except Exception as e:
        print(f"Error fetching logs into DataFrame: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def preprocess_features(df):
    """
    Takes a DataFrame of logs and converts categorical and timestamp features
    into a numerical format suitable for machine learning models.
    """
    if df.empty:
        return pd.DataFrame(), df

    # --- Feature Engineering ---
    # Convert timestamp to numerical features
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    # Keep original data for reference
    original_df = df.copy()

    # --- Feature Selection and Encoding ---
    features_to_encode = ['user_id', 'action', 'resource', 'status']
    numerical_features = ['hour_of_day', 'day_of_week']

    # One-hot encode categorical variables
    encoded_df = pd.get_dummies(df[features_to_encode], prefix=features_to_encode, dtype=float)

    # Combine numerical features with encoded features
    final_df = pd.concat([df[numerical_features], encoded_df], axis=1)

    # THE FIX IS HERE: Ensure all columns are of a standard float type
    final_df = final_df.astype(float)

    final_df.columns = final_df.columns.astype(str)

    print(f"Feature extraction complete. Shape of processed data: {final_df.shape}")

    return final_df, original_df

if __name__ == '__main__':
    print("Fetching logs and running feature extraction...")
    logs_df = fetch_logs_as_dataframe()
    if not logs_df.empty:
        processed_data, original_data = preprocess_features(logs_df)
        print("\nProcessed Data Head:")
        print(processed_data.head())
        print("\nData Types:")
        print(processed_data.dtypes)
    else:
        print("No logs found to process.")