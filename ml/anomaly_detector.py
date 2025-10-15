import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from datetime import datetime

from db.database import get_db_connection
from ml.feature_extractor import fetch_logs_as_dataframe, preprocess_features

MODEL_PATH = "ml/isolation_forest_model.joblib"
COLUMNS_PATH = "ml/model_columns.joblib"

class AnomalyDetector:
    """
    A class to handle training, prediction, and persistence of the Isolation Forest model.
    """
    def __init__(self, contamination=0.05):
        """
        Initializes the AnomalyDetector.

        Args:
            contamination (float): The expected proportion of anomalies in the dataset.
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.model_columns = []

    def train(self, data):
        """
        Trains the Isolation Forest model on the given data.

        Args:
            data (pd.DataFrame): The preprocessed numerical data for training.
        """
        if data.empty:
            print("Training data is empty. Skipping training.")
            return

        print("Training Isolation Forest model...")
        self.model.fit(data)
        self.model_columns = data.columns.tolist() # Store the column order
        print("Model training complete.")

    def predict(self, data):
        """
        Predicts anomalies using the trained model.

        Args:
            data (pd.DataFrame): The preprocessed numerical data for prediction.

        Returns:
            np.ndarray: An array of predictions (-1 for anomalies, 1 for normal).
            np.ndarray: The anomaly scores for each data point.
        """
        if not self.model_columns:
            print("Model has not been trained or loaded. Cannot predict.")
            return None, None

        # Ensure the prediction data has the same columns as the training data
        data = data.reindex(columns=self.model_columns, fill_value=0)

        print("Predicting anomalies...")
        predictions = self.model.predict(data)
        scores = self.model.decision_function(data)
        print("Prediction complete.")
        return predictions, scores

    def save_model(self):
        """Saves the trained model and its columns to disk."""
        print(f"Saving model to {MODEL_PATH}")
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.model_columns, COLUMNS_PATH)

    def load_model(self):
        """Loads a pre-trained model and its columns from disk."""
        try:
            print(f"Loading model from {MODEL_PATH}")
            self.model = joblib.load(MODEL_PATH)
            self.model_columns = joblib.load(COLUMNS_PATH)
            print("Model loaded successfully.")
            return True
        except FileNotFoundError:
            print("No pre-trained model found.")
            return False

def run_anomaly_detection():
    """
    Full pipeline: Fetches data, trains model, predicts anomalies, and saves results.
    """
    print("--- Starting Anomaly Detection Pipeline ---")

    # 1. Fetch and preprocess data
    logs_df = fetch_logs_as_dataframe()
    if logs_df.empty:
        print("Pipeline stopped: No logs to process.")
        return

    processed_data, original_data = preprocess_features(logs_df)

    # 2. Train or load model
    detector = AnomalyDetector()
    if not detector.load_model():
        detector.train(processed_data)
        detector.save_model()

    # 3. Predict anomalies
    predictions, scores = detector.predict(processed_data)

    if predictions is None:
        print("Pipeline stopped: Prediction failed.")
        return

    # 4. Identify and save anomalies to the database
    anomaly_indices = original_data.index[predictions == -1]
    anomalous_logs = original_data.loc[anomaly_indices]
    anomaly_scores = scores[predictions == -1]

    print(f"\nFound {len(anomalous_logs)} potential anomalies.")

    conn = get_db_connection()
    if not conn:
        print("Could not connect to DB to save anomalies.")
        return

    try:
        with conn.cursor() as cur:
            # Clear previous anomalies
            cur.execute("DELETE FROM anomalies")
            print("Cleared previous anomaly records.")

            for index, row in anomalous_logs.iterrows():
                log_id = row['id']
                score = anomaly_scores[anomalous_logs.index.get_loc(index)]
                timestamp = datetime.now()
                details = f"Anomaly detected for user '{row['user_id']}' performing action '{row['action']}' on resource '{row['resource']}'"

                cur.execute(
                    """
                    INSERT INTO anomalies (log_id, timestamp, score, details)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (log_id, timestamp, score, details)
                )
            conn.commit()
        print(f"Successfully saved {len(anomalous_logs)} new anomalies to the database.")
    except Exception as e:
        print(f"Error saving anomalies to database: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_anomalies():
    """Retrieves all anomalies from the database, joined with log details."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.timestamp, l.user_id, l.action, l.resource, a.score, a.details
                FROM anomalies a
                JOIN logs l ON a.log_id = l.id
                ORDER BY a.score ASC -- Show most anomalous first
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Error fetching anomalies: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    run_anomaly_detection()

    print("\n--- Fetching Detected Anomalies ---")
    anomalies = get_anomalies()
    if anomalies:
        for anomaly in anomalies:
            print(anomaly)
    else:
        print("No anomalies found in the database.")