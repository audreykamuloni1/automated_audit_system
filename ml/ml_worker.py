from PyQt5.QtCore import QObject, QThread, pyqtSignal
from ml.anomaly_detector import run_anomaly_detection, get_anomalies

class MLWorker(QObject):
    """
    A worker object that runs the ML pipeline in a separate thread.
    Communicates with the GUI via signals.
    """
    # Signals to communicate with the main GUI thread
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    results_ready = pyqtSignal(list)

    def run(self):
        """
        The main entry point for the worker's task.
        This method will be executed in a separate thread.
        """
        try:
            self.progress.emit("Starting anomaly detection pipeline...")

            # This function encapsulates the entire ML process
            run_anomaly_detection()

            self.progress.emit("Fetching results from database...")

            # After the pipeline runs, fetch the results to display
            anomalies_data = get_anomalies()
            self.results_ready.emit(anomalies_data)

        except Exception as e:
            # Report any errors back to the user via the progress signal
            self.progress.emit(f"An error occurred: {e}")
        finally:
            # Signal that the worker has finished its job
            self.finished.emit()