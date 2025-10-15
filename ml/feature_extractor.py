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
        # Using pandas' read_sql for convenience
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
    Takes a DataFrame of logs and converts categorical features into a numerical
    format suitable for machine learning models.

    Args:
        df (pd.DataFrame): The input DataFrame with log data.

    Returns:
        pd.DataFrame: A DataFrame with numerical features only.
        pd.DataFrame: The original DataFrame with original index, for later reference.
    """
    if df.empty:
        return pd.DataFrame(), df

    # --- Feature Engineering ---
    # Convert timestamp to numerical features
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek # Monday=0, Sunday=6

    # Keep original data for reference before dropping columns
    original_df = df.copy()

    # --- Feature Selection and Encoding ---
    # Select features to be used by the model
    features_to_encode = ['user_id', 'action', 'resource', 'status']
    numerical_features = ['hour_of_day', 'day_of_week']

    # Use one-hot encoding for categorical variables
    # This creates new columns for each category (e.g., 'action_login', 'action_logout')
    encoded_df = pd.get_dummies(df[features_to_encode], prefix=features_to_encode)

    # Combine numerical features with the new encoded features
    final_df = pd.concat([df[numerical_features], encoded_df], axis=1)

    # Ensure all column names are strings (required by some ML libraries)
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
        print("\nOriginal Data columns preserved for reference:")
        print(original_data.head())
    else:
        print("No logs found to process.")