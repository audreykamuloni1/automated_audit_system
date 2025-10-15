import pytest
import pandas as pd
import os
from unittest.mock import patch

from ml.feature_extractor import fetch_logs_as_dataframe, preprocess_features
from ml.anomaly_detector import AnomalyDetector, run_anomaly_detection, get_anomalies
from db.database import setup_database, get_db_connection
from ingestion.log_ingester import ingest_logs

@pytest.fixture(scope="module")
def db_with_logs():
    """Fixture to set up a clean DB and ingest logs for ML tests."""
    setup_database()
    ingest_logs('data/sample_logs.csv')
    yield
    # Teardown is handled by setup_database on next run

def test_fetch_logs_as_dataframe(db_with_logs):
    """Tests that logs are fetched correctly into a pandas DataFrame."""
    df = fetch_logs_as_dataframe()
    assert not df.empty
    assert len(df) == 20 # Based on sample_logs.csv
    assert 'user_id' in df.columns
    assert 'action' in df.columns

def test_preprocess_features(db_with_logs):
    """Tests the feature extraction and preprocessing pipeline."""
    df = fetch_logs_as_dataframe()
    processed_df, original_df = preprocess_features(df)

    assert not processed_df.empty
    assert 'hour_of_day' in processed_df.columns
    assert 'day_of_week' in processed_df.columns
    assert 'user_id_admin-01' in processed_df.columns # Check one-hot encoding
    assert 'action_login' in processed_df.columns

    # Check that no object types remain (all numerical)
    assert all(dtype.kind in 'if' for dtype in processed_df.dtypes) # int or float

@patch('ml.anomaly_detector.joblib.dump') # Mock saving to avoid creating files
def test_anomaly_detector_class(mock_dump):
    """Tests the AnomalyDetector class's train and predict methods."""
    detector = AnomalyDetector()

    # Create sample preprocessed data
    sample_data = pd.DataFrame({
        'feature1': [1, 2, 1, 10, 2, 1],
        'feature2': [0, 0, 1, 5, 0, 1]
    })

    # Test training
    detector.train(sample_data)
    assert detector.model is not None
    assert len(detector.model_columns) == 2

    # Test prediction
    predictions, scores = detector.predict(sample_data)
    assert predictions is not None
    assert scores is not None
    assert len(predictions) == len(sample_data)

    # With contamination=0.05, one point should be an anomaly
    assert sum(predictions == -1) > 0

@patch('ml.anomaly_detector.joblib.dump')
def test_full_anomaly_detection_pipeline(mock_dump, db_with_logs):
    """
    Tests the end-to-end anomaly detection pipeline, from fetching data
    to storing results in the database.
    """
    # Ensure the anomalies table is empty before the run
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM anomalies")
    conn.commit()
    conn.close()

    # Run the full pipeline
    run_anomaly_detection()

    # Check that anomalies were saved to the database
    anomalies = get_anomalies()
    assert isinstance(anomalies, list)
    # The exact number depends on the model's behavior, but it should find some
    assert len(anomalies) > 0

    # Check the structure of the first anomaly record
    first_anomaly = anomalies[0]
    assert len(first_anomaly) == 7 # id, timestamp, user_id, action, resource, score, details
    assert isinstance(first_anomaly[5], float) # Score should be a float (decimal is read as float)