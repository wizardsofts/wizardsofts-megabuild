#!/usr/bin/env python3
"""
Security Camera Feed Display

This script connects to a local security camera feed and displays it in a window.
It uses OpenCV to capture and display the video stream.
Support for EZVIZ cameras has been added.
"""

import cv2
import argparse
import logging
import sys
import time
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('../logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'../logs/camera_feed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('security_camera')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Display video feed from a security camera')
    parser.add_argument('--source', '-s', type=str, default='0',
                      help='Camera source (0 for default webcam, or RTSP/HTTP URL for IP camera)')
    parser.add_argument('--width', '-w', type=int, default=640,
                      help='Display width')
    parser.add_argument('--height', '-ht', type=int, default=480,
                      help='Display height')
    parser.add_argument('--fps', '-f', type=int, default=30,
                      help='Frames per second to capture')
    parser.add_argument('--ezviz', '-ez', action='store_true',
                      help='Specify if using an EZVIZ camera')
    parser.add_argument('--camera-serial', type=str,
                      help='EZVIZ camera serial number (required for EZVIZ cameras)')
    parser.add_argument('--verification-code', type=str,
                      help='EZVIZ camera verification code (required for EZVIZ cameras)')
    parser.add_argument('--ip', type=str,
                      help='EZVIZ camera IP address (for local network connection)')
    parser.add_argument('--cloud', action='store_true',
                      help='Connect to EZVIZ camera via cloud instead of local network')
    parser.add_argument('--username', type=str,
                      help='EZVIZ account username (for cloud connection)')
    parser.add_argument('--password', type=str,
                      help='EZVIZ account password (for cloud connection)')
    parser.add_argument('--channel', type=int, default=1,
                      help='EZVIZ camera channel number (default: 1)')
    parser.add_argument('--stream-type', type=str, default='main', choices=['main', 'sub'],
                      help='EZVIZ stream type: main (HD) or sub (SD) (default: main)')
    parser.add_argument('--protocol', type=str, default='rtsp', choices=['rtsp', 'http'],
                      help='Protocol to use for connecting to the camera (default: rtsp)')
    return parser.parse_args()

def get_ezviz_url(args):
    """
    Generate the appropriate URL for EZVIZ camera based on connection method.

    EZVIZ cameras support several connection methods:
    1. Direct local connection (if camera is on same network)
    2. Cloud connection through EZVIZ servers

    Args:
        args: Command line arguments containing EZVIZ connection details

    Returns:
        URL string for the EZVIZ camera stream
    """
    # Check if we're connecting locally or through cloud
    if args.cloud:
        # Cloud connection requires username and password
        if not args.username or not args.password:
            logger.error("Cloud connection requires username and password")
            return None

        if not args.camera_serial:
            logger.error("Camera serial number is required")
            return None

        # Cloud EZVIZ URL format
        # Note: This is a simplified example, actual cloud implementation might require EZVIZ SDK
        logger.warning("Direct cloud connection not fully supported. Consider using local connection.")
        return None
    else:
        # Local connection - two methods:
        # 1. Using camera IP address (easier)
        # 2. Using camera serial and verification code (more secure)

        if args.ip:
            # Method 1: Using IP address
            stream_type = "0" if args.stream_type == "main" else "1"
            protocol = args.protocol.lower()

            if protocol == "rtsp":
                # RTSP URL format for EZVIZ cameras with IP
                url = f"rtsp://{args.ip}:554/h264/{args.channel}/{stream_type}/"

                # Add verification code as password if provided
                if args.verification_code:
                    url = f"rtsp://admin:{args.verification_code}@{args.ip}:554/h264/{args.channel}/{stream_type}/"

                logger.info(f"Using direct IP RTSP connection: {url}")
                return url
            else:
                # HTTP URL format for EZVIZ cameras with IP
                url = f"http://{args.ip}:80/httpHD/{args.channel}"
                if args.stream_type == "sub":
                    url = f"http://{args.ip}:80/httpSD/{args.channel}"

                # Add verification code as password if provided
                if args.verification_code:
                    url = url.replace("http://", f"http://admin:{args.verification_code}@")

                logger.info(f"Using direct IP HTTP connection: {url}")
                return url
        elif args.camera_serial and args.verification_code:
            # Method 2: Using serial number and verification code
            # This typically requires the EZVIZ app or SDK to properly implement
            logger.warning("Direct connection via serial number requires EZVIZ SDK integration.")
            logger.info("Consider using the IP address method instead.")

            # Example format for some EZVIZ models (may not work with all models)
            stream_type = "0" if args.stream_type == "main" else "1"
            url = f"rtsp://admin:{args.verification_code}@{args.camera_serial}.lscamera.ezvizlife.com:554/h264/{args.channel}/{stream_type}/"

            logger.info(f"Attempting connection with serial number: {url}")
            return url
        else:
            logger.error("For local connection, either IP address or camera serial + verification code are required")
            return None

def connect_to_camera(source, is_ezviz=False, ezviz_args=None):
    """
    Connect to the camera source.

    Args:
        source: Camera source (0 for default webcam, or URL for IP camera)
        is_ezviz: Boolean indicating if this is an EZVIZ camera
        ezviz_args: Command line arguments containing EZVIZ connection details

    Returns:
        VideoCapture object if successful, None otherwise
    """
    # Handle EZVIZ camera specifically
    if is_ezviz:
        source = get_ezviz_url(ezviz_args)
        if not source:
            return None
    # Convert numeric string to integer for webcam index
    elif source.isdigit():
        source = int(source)

    logger.info(f"Attempting to connect to camera source: {source}")
    cap = cv2.VideoCapture(source)

    # Check if camera opened successfully
    if not cap.isOpened():
        logger.error("Error: Could not open camera.")
        return None

    logger.info("Successfully connected to camera.")
    return cap

def configure_camera(cap, width, height, fps):
    """Configure camera parameters."""
    # Set the resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Set the FPS
    cap.set(cv2.CAP_PROP_FPS, fps)

    # Get actual parameters (might differ from requested)
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    logger.info(f"Camera configured with resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")

def display_camera_feed(args):
    """
    Connect to camera and display feed in a window.

    Args:
        args: Command line arguments containing camera configuration
    """
    # Connect to camera
    cap = connect_to_camera(args.source, args.ezviz, args)
    if cap is None:
        return

    # Configure camera
    configure_camera(cap, args.width, args.height, args.fps)

    # Create window
    window_name = "Security Camera Feed"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    frame_count = 0
    start_time = time.time()
    actual_fps = 0

    try:
        logger.info("Starting video display. Press 'q' to quit.")
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()

            # If frame is read correctly ret is True
            if not ret:
                logger.error("Error: Can't receive frame (stream end?). Exiting...")
                break

            # Calculate and display FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                actual_fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()

            # Add FPS text to the frame
            cv2.putText(frame, f"FPS: {actual_fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, args.height - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Display the resulting frame
            cv2.imshow(window_name, frame)

            # Exit if 'q' is pressed
            if cv2.waitKey(1) == ord('q'):
                logger.info("User requested to quit")
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # When everything done, release the capture and destroy windows
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Camera feed stopped and resources released")

def main():
    """Main function."""
    args = parse_arguments()

    logger.info(f"Starting security camera feed with source: {args.source}, "
               f"resolution: {args.width}x{args.height}, FPS: {args.fps}")

    # Pass full args object to support EZVIZ parameters
    a = {}
    a['source']='10.0.0.3:8000'
    a['username']='wizardsofts@gmail.com'
    a['password']='Austr@li@2#25'
    display_camera_feed(a)

if __name__ == "__main__":
    main()
