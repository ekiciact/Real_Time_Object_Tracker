I will implement 5 major features to enhance the Object Tracker:

### 1. **Auto-Color Calibration ("Click-to-Track")**
- **Feature**: Allow users to select an object in the video stream (using `cv2.selectROI`) to automatically calculate the optimal HSV thresholds.
- **Implementation**:
    - Add a "Select Object" mode in `main.py` triggered by a keypress (e.g., 's').
    - Calculate the Mean and Standard Deviation of the Hue/Saturation/Value in the selected region.
    - Set `lower_hsv = mean - (std_dev * threshold)` and `upper_hsv = mean + (std_dev * threshold)`.

### 2. **Target Image Upload**
- **Feature**: Users can provide a static image path (via command line `--image`) to set the tracking color before the webcam starts.
- **Implementation**:
    - Add `--image` argument to `main.py`.
    - If provided, load the image, compute the dominant color (or center ROI color), and set initial HSV values.

### 3. **Video File Support**
- **Feature**: Process a pre-recorded video file instead of the webcam feed.
- **Implementation**:
    - Add `--video` argument.
    - Modify `cv2.VideoCapture` initialization to accept the file path.
    - Add playback controls: 'p' to pause/resume, 'r' to restart.

### 4. **Occlusion Handling with Kalman Filter**
- **Feature**: Smooth tracking and predict the object's position even when it is momentarily hidden or detection fails.
- **Implementation**:
    - Integrate `cv2.KalmanFilter` into `src/tracker.py`.
    - **Predict**: Estimate next position based on velocity.
    - **Correct**: Update with actual measurement when contour is found.
    - Draw a "Predicted" path (blue) vs "Actual" path (red).

### 5. **Distance Estimation**
- **Feature**: Estimate and display the real-world distance of the object from the camera.
- **Implementation**:
    - Add `--width` argument (real-world object width in cm).
    - Use the Triangle Similarity principle: `Distance = (KnownWidth * FocalLength) / ApparentWidth`.
    - Requires a calibration step (or default focal length assumption) to be reasonably accurate.

### **Refactored Workflow**
1.  **Startup**: Check for `--video` or `--image` args.
2.  **Calibration**:
    - If `--image`: Auto-tune immediately.
    - If Webcam/Video: Wait for user to press 's' to select ROI or use manual sliders.
3.  **Tracking Loop**:
    - Apply Kalman Prediction.
    - Find Contours (Measurement).
    - Kalman Correction.
    - Calculate Distance (if width provided).
    - Render Annotations.

I will update `src/tracker.py` for logic and `main.py` for the interface.