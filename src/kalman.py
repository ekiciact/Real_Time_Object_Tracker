import cv2
import numpy as np

class KalmanTracker:
    def __init__(self):
        # Initialize Kalman Filter
        # 4 dynamic params (x, y, dx, dy), 2 measured params (x, y)
        self.kf = cv2.KalmanFilter(4, 2)
        
        # Measurement Matrix (H) - we only measure position (x, y)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0]], np.float32)
        
        # Transition Matrix (F) - defines how state evolves
        # x = x + dx*dt, y = y + dy*dt
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                             [0, 1, 0, 1],
                                             [0, 0, 1, 0],
                                             [0, 0, 0, 1]], np.float32)
        
        # Process Noise Covariance (Q) - Uncertainty in system evolution
        self.kf.processNoiseCov = np.array([[1, 0, 0, 0],
                                            [0, 1, 0, 0],
                                            [0, 0, 1, 0],
                                            [0, 0, 0, 1]], np.float32) * 0.03

        # Measurement Noise Covariance (R) - Uncertainty in measurement
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1 # Low noise trust measurement

        self.prediction = np.zeros((2, 1), np.float32)

    def predict(self):
        """Predict the next state."""
        self.prediction = self.kf.predict()
        return (int(self.prediction[0]), int(self.prediction[1]))

    def correct(self, x, y):
        """Correct the state with actual measurement."""
        measurement = np.array([[np.float32(x)], [np.float32(y)]])
        self.kf.correct(measurement)
        return (int(self.prediction[0]), int(self.prediction[1]))
