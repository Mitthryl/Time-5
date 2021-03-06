import cv2
import numpy as np

# Constants for image resizing
CAM_RESOLUTION = (320, 240)

# Create color dictionary
color = dict()

# Color defined from calibration:
# color['name'] = np.array((H_min, S_min, V_min), (H_max, S_max, V_max))
color['red'] = np.array(((0, 67, 140), (15, 207, 255)))
color['green'] = np.array(((40, 67, 52), (86, 202, 255)))
color['blue'] = np.array(((97, 116, 107), (133, 255, 255)))

# Superior interval for red (Defined due to the HSV range of the red color)
RED_SUP_THRESHOLD = np.array(((165, 67, 140), (179, 207, 255)))


def pre_processing(img):
    """Perform noise reduction and format conversion."""

    # Convert to HSV format
    blurred_img = cv2.GaussianBlur(img, (3, 3), 0)
    hsv_img = cv2.cvtColor(blurred_img, cv2.COLOR_BGR2HSV)

    return(hsv_img)


def morpho_operation(img_mask):
    """Reduce noise on color mask with morphology operations."""

    # Perform an opening on the color mask
    kernel = np.ones((11, 11), np.uint8)
    img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_OPEN, kernel)

    return(img_mask)


def find_targets(img_mask, original_img, draw_contours=False):
    """Get borders of mask and calculate the centroid of the biggest target."""

    # Compute the contours of each area of the mask
    image, contours, hierarquy = cv2.findContours(img_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contour lines
    if draw_contours is True:
        cv2.drawContours(original_img, contours, -1, (0, 255, 0), 2)

    # Skip target search if color object was found
    if len(contours) > 0:

        # Find the contour with maximum area
        best_cnt = max(contours, key=cv2.contourArea)

        # Acquire the segmentation centroid
        M = cv2.moments(best_cnt)
        centroid = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        circle_img = cv2.circle(original_img, centroid, 10, (255, 0, 0), 2)

        return(centroid)

    # If no target of the specified color was found
    else:
        return((False, False))


def main():

    # Aquire image from video source
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Camera')

    # Initialize list of visible targets
    target_list = []

    while(True):

        # Capture video frame-by-frame and resize it
        ret, frame = cap.read()
        frame = cv2.resize(frame, CAM_RESOLUTION)

        # Perform pre-processing operations
        proc_img = pre_processing(frame)

        # Do a color detection for each color on the dictionary
        for color_name, color_val in color.items():

            # Create color mask
            if color_name == 'red':
                img_mask_inf = cv2.inRange(proc_img, color_val[0, :], color_val[1, :])
                img_mask_sup = cv2.inRange(proc_img, RED_SUP_THRESHOLD[0, :], RED_SUP_THRESHOLD[1, :])
                img_mask = cv2.bitwise_or(img_mask_inf, img_mask_sup)
            else:
                img_mask = cv2.inRange(proc_img, color_val[0, :], color_val[1, :])

            # Eliminate minor noise
            img_mask = morpho_operation(img_mask)
            # cv2.imshow('Mask for ' + color_name, img_mask)

            # Acquire the biggest color blob centroid
            centroid = find_targets(img_mask, frame, draw_contours=True)

            # Add target info to the list.
            #   Each item is a tuple: ('target label', (x, y))
            #       Ex: ('blue', (10, 50))
            #   If (x, y) = (False, False) no target was found

            # Set the middle of the image as the origin (based on image resolution)
            if centroid[0] is not False:
                centroid_corrected = tuple(np.subtract(centroid, (CAM_RESOLUTION[0] / 2, CAM_RESOLUTION[1] / 2)))

                # Store the new target
                target_list.append((color_name, centroid_corrected))

            else:
                # Store the new target
                target_list.append((color_name, centroid))

            # cv2.putText(frame, color_name, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, str(centroid_corrected), centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Display image
        cv2.imshow('Camera', frame)

        # Output the target label and centroid
        for target in target_list:
            print(target)

        target_list.clear()

        # Wait for exit command
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release capture and handle exit
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
