import cv2
import numpy as np
from collections import deque
import time
from src.kalman import KalmanTracker

class ColorTracker:
    def __init__(self, buffer_size=64, real_width=None, min_area_ratio=0.001, max_area_ratio=0.8, max_dist=None):
        """
        Initialize the ColorTracker.
        :param buffer_size: Size of the buffer to store the tracking trail.
        :param real_width: Real-world width of the object (in cm) for distance estimation.
        :param min_area_ratio: Minimum contour area as a ratio of frame size (0.001 = 0.1%).
        :param max_area_ratio: Maximum contour area as a ratio of frame size (0.8 = 80%).
        :param max_dist: Maximum distance (in pixels) to search for the next object position.
        """
        self.buffer_size = buffer_size
        self.pts = deque(maxlen=buffer_size)
        self.current_center = None
        self.radius = 0
        self.last_time = time.time()
        self.velocity = 0.0 # pixels per second
        self.direction = ""
        
        # Kalman Filter
        self.kalman = KalmanTracker()
        self.predicted_center = None
        
        # Distance Estimation
        self.real_width = real_width
        self.focal_length = 600 # Approximate focal length (can be calibrated)
        self.distance = 0.0

        # Area Filtering
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio

        # Distance Restriction
        self.max_dist = max_dist
        self.last_valid_center = None
        self.last_valid_time = 0
        self.search_center = None # For visualization

    def process_frame(self, frame, hsv_lower, hsv_upper):
        """
        Process a single frame to detect objects within the HSV range.
        
        :param frame: The input BGR frame.
        :param hsv_lower: Tuple (h_min, s_min, v_min)
        :param hsv_upper: Tuple (h_max, s_max, v_max)
        :return: Processed mask.
        """
        # Predict next position
        self.predicted_center = self.kalman.predict()
        
        # 1. Blur to reduce noise
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        
        # 2. Convert to HSV
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # 3. Create mask
        mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
        
        # 4. Morphological operations to clean up the mask
        # Erode to remove small blobs, Dilate to fill gaps
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        
        # 5. Find contours
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        
        self.current_center = None
        self.radius = 0
        
        # Calculate Frame Area for relative filtering
        frame_area = frame.shape[0] * frame.shape[1]
        
        # Save search state for visualization before update
        self.search_center = self.last_valid_center

        if len(cnts) > 0:
            # Filter contours by area relative to frame size
            filtered_cnts = []
            for c in cnts:
                area = cv2.contourArea(c)
                if self.min_area_ratio * frame_area < area < self.max_area_ratio * frame_area:
                    filtered_cnts.append(c)

            # Apply Distance Restriction Logic
            candidates = filtered_cnts
            
            if self.max_dist is not None and self.last_valid_center is not None:
                # If we have a previous lock, check timeout
                if time.time() - self.last_valid_time > 1.0:
                     # Timeout expired, reset lock to allow full search
                     self.last_valid_center = None
                     self.search_center = None # Visual update: no restricted search
                else:
                    # Filter candidates by distance from last valid center
                    dist_filtered = []
                    for c in filtered_cnts:
                         M = cv2.moments(c)
                         if M["m00"] > 0:
                             cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                             dist = np.linalg.norm(np.array([cx, cy]) - np.array(self.last_valid_center))
                             if dist <= self.max_dist:
                                 dist_filtered.append(c)
                    
                    if len(dist_filtered) > 0:
                        candidates = dist_filtered
                    else:
                        # No candidate near last position, and timeout hasn't expired.
                        # Do NOT jump to a far object. Treat as lost for now.
                        candidates = []

            if len(candidates) > 0:
                # Find the largest contour from the valid ones
                c = max(candidates, key=cv2.contourArea)
                ((x, y), self.radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                
                if M["m00"] > 0:
                    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                    
                    # Correct Kalman Filter with actual measurement
                    self.current_center = self.kalman.correct(cx, cy)
                    
                    # Update Lock info
                    self.last_valid_center = (cx, cy)
                    self.last_valid_time = time.time()
                    
                    # Update velocity
                    current_time = time.time()
                    dt = current_time - self.last_time
                    if dt > 0 and len(self.pts) > 0 and self.pts[0] is not None:
                        # Calculate distance from last point
                        prev_center = self.pts[0]
                        dx = self.current_center[0] - prev_center[0]
                        dy = self.current_center[1] - prev_center[1]
                        dist = np.sqrt(dx*dx + dy*dy)
                        self.velocity = dist / dt
                        
                        # Determine direction
                        if abs(dx) > abs(dy):
                            self.direction = "East" if dx > 0 else "West"
                        else:
                            self.direction = "South" if dy > 0 else "North"
                    
                    self.last_time = current_time
                    
                    # Calculate Distance
                    if self.real_width is not None and self.radius > 0:
                        # D = (W * F) / P
                        # W = real_width, F = focal_length, P = apparent width (2 * radius)
                        self.distance = (self.real_width * self.focal_length) / (2 * self.radius)

        else:
            # If object lost, check if we should reset lock due to timeout
            if self.max_dist is not None and self.last_valid_center is not None:
                 if time.time() - self.last_valid_time > 1.0:
                     self.last_valid_center = None
                     self.search_center = None

        # Update points deque
        self.pts.appendleft(self.current_center)
        
        return mask

    def draw_annotations(self, frame):
        """
        Draw the tracking trail, bounding circle, and info on the frame.
        """
        # Draw Predicted Position (Blue X)
        if self.predicted_center:
             cv2.drawMarker(frame, self.predicted_center, (255, 0, 0), cv2.MARKER_CROSS, 20, 2)

        # Draw Search Radius
        if self.max_dist is not None and self.search_center is not None:
             cv2.circle(frame, self.search_center, int(self.max_dist), (0, 255, 0), 1)

        # Draw the bounding circle and centroid if tracked
        if self.current_center is not None and self.radius > 10:
            cv2.circle(frame, (int(self.current_center[0]), int(self.current_center[1])), int(self.radius), (0, 255, 255), 2)
            cv2.circle(frame, self.current_center, 5, (0, 0, 255), -1)

        # Draw the trail
        for i in range(1, len(self.pts)):
            if self.pts[i - 1] is None or self.pts[i] is None:
                continue
            
            thickness = int(np.sqrt(self.buffer_size / float(i + 1)) * 2.5)
            cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 0, 255), thickness)

        # Draw Metrics
        info = [
            f"Velocity: {self.velocity:.2f} px/s",
            f"Direction: {self.direction}",
            f"Radius: {self.radius:.1f}"
        ]
        
        if self.real_width is not None:
            info.append(f"Distance: {self.distance:.2f} cm")
            
        if self.max_dist is not None:
            if self.search_center is not None:
                 info.append("State: LOCKED")
            else:
                 info.append("State: SEARCHING")
        
        for i, line in enumerate(info):
            cv2.putText(frame, line, (10, frame.shape[0] - 10 - (i * 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
        return frame
