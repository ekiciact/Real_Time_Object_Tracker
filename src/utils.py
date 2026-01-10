import csv
import time
import os
import cv2
import numpy as np

def initialize_csv(filepath="tracking_data.csv"):
    """
    Initialize the CSV file with headers if it doesn't exist.
    """
    if not os.path.exists(filepath):
        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "X", "Y", "Radius", "Velocity", "Direction", "Distance"])

def log_data(center, radius, velocity, direction, distance=0, filepath="tracking_data.csv"):
    """
    Log tracking data to CSV.
    """
    if center is not None:
        with open(filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([time.time(), center[0], center[1], radius, velocity, direction, distance])

def calculate_hsv_stats(frame, roi):
    """
    Calculate the Mean and Standard Deviation of HSV values in a Region of Interest.
    
    :param frame: The BGR frame.
    :param roi: Tuple (x, y, w, h) of the selected region.
    :return: (lower_hsv, upper_hsv) tuples.
    """
    x, y, w, h = roi
    # Ensure ROI is valid
    if w == 0 or h == 0:
        return None, None
        
    roi_crop = frame[y:y+h, x:x+w]
    hsv_roi = cv2.cvtColor(roi_crop, cv2.COLOR_BGR2HSV)
    
    # Calculate mean and std dev
    mean, std = cv2.meanStdDev(hsv_roi)
    
    # Define thresholds (Mean +/- K * StdDev)
    # K is a multiplier to cover the variance (e.g., 2.5 sigma)
    K = 2.5
    
    lower_hsv = np.array([
        max(0, mean[0][0] - K * std[0][0]),
        max(0, mean[1][0] - K * std[1][0]),
        max(20, mean[2][0] - K * std[2][0]) # Avoid too dark values
    ], dtype=np.uint8)
    
    upper_hsv = np.array([
        min(179, mean[0][0] + K * std[0][0]),
        min(255, mean[1][0] + K * std[1][0]),
        min(255, mean[2][0] + K * std[2][0])
    ], dtype=np.uint8)
    
    return lower_hsv, upper_hsv
