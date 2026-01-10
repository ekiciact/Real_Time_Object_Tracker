I will implement "Project 1: Real-Time Object Tracker (Color-Based)" with a robust, modular architecture and a user-friendly interface for dynamic color tuning.

### 1. Environment Configuration
- Create `environment.yml` to define a reproducible Anaconda environment named `cv-tracker`.
- **Dependencies**: Python 3.9, OpenCV (headless or full), NumPy.

### 2. Core Implementation (`src/`)
- **`src/tracker.py`**:
  - Implement `ColorTracker` class.
  - **Features**:
    - HSV Color Space Conversion.
    - Morphological operations (Erosion/Dilation) to remove noise.
    - Contour detection to find the largest object.
    - Centroid tracking with a `deque` to draw the movement trail.
    - Velocity calculation (pixels/frame).
- **`src/utils.py`**:
  - Helper functions for text overlays and CSV logging.
- **`main.py`**:
  - Entry point of the application.
  - **GUI**: Implement OpenCV Trackbars for real-time HSV (Hue, Saturation, Value) calibration.
  - **Loop**: Webcam capture -> Track -> Render -> User Input handling.

### 3. Documentation
- **`README.md`**: Quick start guide, installation instructions.
- **`docs/USER_GUIDE.md`**:
  - Detailed workflow: How to create the Conda env, how to launch the tracker.
  - **Calibration Guide**: Step-by-step instructions on using the sliders to isolate a specific color.
  - **Troubleshooting**: Common lighting and camera issues.

### 4. Verification
- I will verify the code by attempting to run the help/usage command (since I cannot see a webcam stream, I will ensure the code initializes correctly and handles video files/streams logic without syntax errors).
