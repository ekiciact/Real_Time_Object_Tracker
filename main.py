import cv2
import numpy as np
from src.tracker import ColorTracker
from src.utils import initialize_csv, log_data, calculate_hsv_stats
import argparse
import sys
import os

def nothing(x):
    pass

def initialize_trackbars(window_name="Settings"):
    """Create trackbars for HSV tuning."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Hue Min", window_name, 0, 179, nothing)
    cv2.createTrackbar("Hue Max", window_name, 179, 179, nothing)
    cv2.createTrackbar("Sat Min", window_name, 0, 255, nothing)
    cv2.createTrackbar("Sat Max", window_name, 255, 255, nothing)
    cv2.createTrackbar("Val Min", window_name, 0, 255, nothing)
    cv2.createTrackbar("Val Max", window_name, 255, 255, nothing)

    # Default values
    cv2.setTrackbarPos("Hue Min", window_name, 0)
    cv2.setTrackbarPos("Hue Max", window_name, 179)
    cv2.setTrackbarPos("Sat Min", window_name, 0)
    cv2.setTrackbarPos("Sat Max", window_name, 255)
    cv2.setTrackbarPos("Val Min", window_name, 0)
    cv2.setTrackbarPos("Val Max", window_name, 255)

def set_trackbar_values(window_name, lower_hsv, upper_hsv):
    """Update trackbar positions."""
    cv2.setTrackbarPos("Hue Min", window_name, lower_hsv[0])
    cv2.setTrackbarPos("Sat Min", window_name, lower_hsv[1])
    cv2.setTrackbarPos("Val Min", window_name, lower_hsv[2])
    cv2.setTrackbarPos("Hue Max", window_name, upper_hsv[0])
    cv2.setTrackbarPos("Sat Max", window_name, upper_hsv[1])
    cv2.setTrackbarPos("Val Max", window_name, upper_hsv[2])

def get_trackbar_values(window_name="Settings"):
    """Read current values from trackbars."""
    h_min = cv2.getTrackbarPos("Hue Min", window_name)
    h_max = cv2.getTrackbarPos("Hue Max", window_name)
    s_min = cv2.getTrackbarPos("Sat Min", window_name)
    s_max = cv2.getTrackbarPos("Sat Max", window_name)
    v_min = cv2.getTrackbarPos("Val Min", window_name)
    v_max = cv2.getTrackbarPos("Val Max", window_name)
    
    return (h_min, s_min, v_min), (h_max, s_max, v_max)

def main():
    parser = argparse.ArgumentParser(description="Advanced Real-Time Color Object Tracker")
    parser.add_argument("--source", type=int, default=0, help="Webcam source index (default: 0)")
    parser.add_argument("--video", type=str, help="Path to video file (overrides --source)")
    parser.add_argument("--image", type=str, help="Path to target object image for auto-calibration")
    parser.add_argument("--width", type=float, help="Real-world width of the object in cm (for distance estimation)")
    
    # New arguments for area filtering
    parser.add_argument("--min_area", type=float, default=0.001, help="Minimum contour area as ratio of frame size (default: 0.001)")
    parser.add_argument("--max_area", type=float, default=0.8, help="Maximum contour area as ratio of frame size (default: 0.8)")
    parser.add_argument("--max_dist", type=float, help="Maximum distance (in pixels) to search for the next object position")
    
    parser.add_argument("--log", action="store_true", help="Enable CSV logging")
    args = parser.parse_args()

    # Initialize Tracker with area limits
    tracker = ColorTracker(real_width=args.width, min_area_ratio=args.min_area, max_area_ratio=args.max_area, max_dist=args.max_dist)
    
    # Initialize Logging
    if args.log:
        initialize_csv()
        print("[INFO] Logging enabled. Data will be saved to tracking_data.csv")

    # Determine Input Source
    source = args.source
    if args.video:
        if not os.path.exists(args.video):
            print(f"[ERROR] Video file not found: {args.video}")
            return
        source = args.video
        print(f"[INFO] Processing video: {args.video}")

    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open source {source}")
        return

    # Setup UI
    settings_window = "Settings"
    initialize_trackbars(settings_window)

    # Auto-Calibration from Image
    if args.image:
        if os.path.exists(args.image):
            print(f"[INFO] Loading target image: {args.image}")
            target_img = cv2.imread(args.image)
            # Use center 50% of image as ROI
            h, w = target_img.shape[:2]
            roi = (int(w*0.25), int(h*0.25), int(w*0.5), int(h*0.5))
            lower, upper = calculate_hsv_stats(target_img, roi)
            set_trackbar_values(settings_window, lower, upper)
            print("[INFO] Auto-calibrated from image.")
        else:
            print(f"[ERROR] Image file not found: {args.image}")

    print("[INFO] Tracker started.")
    print("[INFO] Controls:")
    print(" - 's': Select ROI to track (Click-to-Track)")
    print(" - 'p': Pause/Resume")
    print(" - 'q': Quit")

    # Initialize variables to ensure scope validity
    paused = False
    annotated_frame = None
    mask = None

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                # Loop video if it ends
                if args.video:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print("[INFO] Frame capture failed.")
                    break
            
            # Resize large frames for better performance
            if frame.shape[1] > 1280:
                frame = cv2.resize(frame, (1280, int(1280 * frame.shape[0] / frame.shape[1])))

            # Flip if using webcam
            if args.video is None:
                frame = cv2.flip(frame, 1)

            # Get HSV values from UI
            lower_hsv, upper_hsv = get_trackbar_values(settings_window)

            # Process Frame
            mask = tracker.process_frame(frame, lower_hsv, upper_hsv)
            
            # Log data
            if args.log:
                log_data(tracker.current_center, tracker.radius, tracker.velocity, tracker.direction, tracker.distance)

            # Draw Annotations
            annotated_frame = tracker.draw_annotations(frame.copy())

        # Show Results (Even when paused)
        if annotated_frame is not None and mask is not None:
            # Create windows with WINDOW_NORMAL flag to allow resizing
            if cv2.getWindowProperty("Original Frame", cv2.WND_PROP_VISIBLE) < 1:
                cv2.namedWindow("Original Frame", cv2.WINDOW_NORMAL)
            if cv2.getWindowProperty("Mask", cv2.WND_PROP_VISIBLE) < 1:
                cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)
                
            cv2.imshow("Original Frame", annotated_frame)
            cv2.imshow("Mask", mask)

        # Keyboard Controls
        key = cv2.waitKey(30 if args.video else 1) & 0xFF
        
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord("p") or key == ord("P"):
            paused = not paused
        elif key == ord("s") or key == ord("S"):
            # Select ROI
            # Need to pause to select
            paused = True
            
            # Check if frame exists before selecting
            if frame is not None:
                print("[INFO] Select a ROI and then press SPACE or ENTER button!")
                print("[INFO] Cancel the selection process by pressing c button!")
                roi = cv2.selectROI("Original Frame", frame, fromCenter=False, showCrosshair=True)
                if roi != (0, 0, 0, 0):
                    lower, upper = calculate_hsv_stats(frame, roi)
                    if lower is not None:
                        set_trackbar_values(settings_window, lower, upper)
                        print(f"[INFO] New Thresholds: Lower={lower}, Upper={upper}")
                    
                    # Auto-Calculate Area Filters
                    # roi = (x, y, w, h)
                    roi_area = roi[2] * roi[3]
                    frame_area = frame.shape[0] * frame.shape[1]
                    ratio = roi_area / frame_area
                    
                    # Set dynamic limits: 
                    # - Allow object to get ~40% smaller (0.6x)
                    # - Allow object to get ~100% bigger (2.0x)
                    tracker.min_area_ratio = ratio * 0.6
                    tracker.max_area_ratio = ratio * 2.0
                    print(f"[INFO] Auto-Size Tuned: ROI Ratio={ratio:.4f}, Min={tracker.min_area_ratio:.4f}, Max={tracker.max_area_ratio:.4f}")
            else:
                print("[WARN] No frame to select ROI from.")
            
            # Note: We use the existing "Original Frame" window, so no new window to destroy.
            paused = False

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
