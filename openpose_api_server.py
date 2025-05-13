import os
import subprocess
import json
import time
from flask import Flask, request, jsonify
import threading
import numpy as np


DEBUG = True
process_handle = None

app = Flask(__name__)

# Global variables to track processing status
processing_status = {
    "is_processing": False,
    "current_image": None,
    "status_message": "Idle",
    "progress": 0,
}

# Lock for thread safety
status_lock = threading.Lock()


def update_status(message, progress=None, is_processing=None, current_image=None):
    """Update the processing status safely."""
    global processing_status
    with status_lock:
        if message is not None:
            processing_status["status_message"] = message
            if DEBUG:
                print(f"Status update: {message}", flush=True)
        if progress is not None:
            processing_status["progress"] = progress
            if DEBUG:
                print(f"Progress update: {progress}%", flush=True)
        if is_processing is not None:
            processing_status["is_processing"] = is_processing
            if DEBUG:
                print(f"Processing state: {is_processing}", flush=True)
        if current_image is not None:
            processing_status["current_image"] = current_image


def monitor_output(pipe, progress_markers):
    """Monitor output from a pipe and update status accordingly."""
    for line in iter(pipe.readline, ""):
        if not line:
            continue

        update_status(line.strip(), None)

        # More specific progress markers
        if "Starting processing" in line:
            update_status(None, 35)
        elif "Processing" in line:
            update_status(None, 50)
        elif "Finished" in line:
            update_status(None, 75)
        elif "Rendering pose keypoints" in line:
            update_status(None, 60)
        elif "Parsing complete" in line:
            update_status(None, 70)


def has_valid_keypoints(keypoints, threshold=0.1):
    """Check if keypoints array contains valid detections above threshold."""
    if not keypoints:
        return False
    try:
        keypoints_array = np.array(keypoints).reshape(-1, 3)
        # Check if any keypoints have confidence above threshold
        return np.any(keypoints_array[:, 2] > threshold)
    except Exception as e:
        print(e, flush=True)
        return False



def process_image(
    image_path,
    output_dir,
    model="BODY_25",
    detect_face=False,
    detect_hands=False,
    detect_feet=False,
    write_json=True,
    render_on_black=True,
    render_on_image=True,
    render_threshold=0.05,
    face_render_threshold=0.4,
    hand_render_threshold=0.2,
    feet_render_threshold=0.03,
    keypoint_scale=0,
):
    """Process an image with OpenPose with multiple visualization options."""

    global process_handle

    update_status(f"Starting to process image: {image_path}", 0, True, image_path)

    # Get the directory of the image
    image_dir = os.path.dirname(image_path)
    image_filename = os.path.basename(image_path)
    name_without_ext = os.path.splitext(image_filename)[0]

    # Create output subdirectories
    black_bg_dir = os.path.join(output_dir, "black_bg")
    src_img_dir = os.path.join(output_dir, "on_image")

    json_dir = os.path.join(output_dir, "json")

    # Create directories if they don't exist
    for directory in [
        black_bg_dir,
        src_img_dir,
        json_dir,
    ]:
        os.makedirs(directory, exist_ok=True)

    outputs = {
        "rendered_on_black": [],
        "rendered_on_image": [],
        "json": [],
    }

    # Process options
    process_options = []

    # 1. Render on black background if requested
    if render_on_black:
        process_options.append(
            {"output_dir": black_bg_dir, "disable_blending": True, "name": "black_bg"}
        )

    # 2. Render on original image if requested
    if render_on_image:
        process_options.append(
            {"output_dir": src_img_dir, "disable_blending": False, "name": "on_image"}
        )

    # Execute OpenPose for each rendering option
    for option in process_options:
        # Prepare the OpenPose command
        cmd = [
            "./build/examples/openpose/openpose.bin",
            "--image_dir",
            image_dir,
            "--model_pose",
            model,
            "--write_images",
            option["output_dir"],
            "--write_json",
            json_dir,
            "--display",
            "0",
            "--render_threshold",
            str(render_threshold),
            "--render_pose",
            "1",
            "--part_to_show",
            "0",
        ]

        # Model-specific adjustments
        if model == "COCO":
            # COCO model uses a specific prototxt file
            cmd.extend(["--prototxt_path", "pose/coco/pose_deploy_linevec.prototxt"])
        elif model == "MPI":
            # MPI model uses its own prototxt file
            cmd.extend(["--prototxt_path", "pose/mpi/pose_deploy_linevec.prototxt"])
        elif model == "BODY_25":
            # Default BODY_25 model
            # (no additional flags needed as this is the default)
            pass

        # Add black background if specified
        if option["disable_blending"]:
            cmd.append("--disable_blending")

        # Add facial keypoint detection if requested
        if detect_face:
            cmd.append("--face")
            cmd.extend(["--face_render_threshold", str(face_render_threshold)])

        # Add hand keypoint detection if requested
        if detect_hands:
            cmd.append("--hand")
            cmd.extend(["--hand_render_threshold", str(hand_render_threshold)])

        # Add feet-specific parameters if requested
        # ** NOTE: Only available for model BODY_25
        if detect_feet and model == "BODY_25":
            cmd.append("--maximize_positives")  # Helps with harder-to-detect keypoints
            update_status(
                f"Feet detection enabled with threshold: {feet_render_threshold}", None
            )
            # Optionally, adjust the render threshold for this run if it helps feet detection
            cmd[cmd.index("--render_threshold") + 1] = str(
                min(render_threshold, feet_render_threshold)
            )
        elif detect_feet and model != "BODY_25":
            update_status(
                "Error: Feet detection only available with BODY_25 model", 100, False
            )
            return False, outputs

        # Set keypoint scale
        cmd.extend(["--keypoint_scale", str(keypoint_scale)])

        # Run the OpenPose command
        # try:
        #     update_status(f"Running OpenPose for {option['name']} rendering...", 25)
        #     update_status(f"Command: {' '.join(cmd)}", 30)

        #     # process = subprocess.Popen(
        #     #     cmd,
        #     #     stdout=subprocess.PIPE,
        #     #     stderr=subprocess.PIPE,
        #     #     universal_newlines=True,
        #     # )
        #     process = subprocess.Popen(
        #         cmd,
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #         universal_newlines=True,
        #         bufsize=1
        #     )

        #     # Monitor the process output
        #     for line in process.stdout:
        #         update_status(line.strip(), None)

        #     # Wait for the process to complete
        #     process.wait()

        try:
            update_status(f"Running OpenPose for {option['name']} rendering...", 25)
            update_status(f"Command: {' '.join(cmd)}", 30)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,  # Line buffered
            )

            process_handle = process
            print(f"Setting process_handle to {process_handle}", flush=True)

            # Start monitoring in separate threads to avoid blocking
            stdout_thread = threading.Thread(
                target=monitor_output,
                args=(
                    process.stdout,
                    {"Starting": 35, "Keypoints": 50, "Finished": 75},
                ),
            )
            stderr_thread = threading.Thread(
                target=monitor_output, args=(process.stderr, {})
            )

            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Wait for process to finish
            process.wait()
            stdout_thread.join(timeout=60)
            stderr_thread.join(timeout=60)

            if process.returncode == 0:
                # Check for rendered image output
                for ext in [".jpg", ".png"]:
                    rendered_path = os.path.join(
                        option["output_dir"], f"{name_without_ext}_rendered{ext}"
                    )
                    if os.path.exists(rendered_path):
                        if option["disable_blending"]:
                            outputs["rendered_on_black"].append(rendered_path)
                        else:
                            outputs["rendered_on_image"].append(rendered_path)
                # Check for JSON output
                json_path = os.path.join(json_dir, f"{name_without_ext}_keypoints.json")
                if os.path.exists(json_path) and json_path not in outputs["json"]:
                    outputs["json"].append(json_path)
            elif process.returncode != 0:
                stderr_output = (
                    process.stderr.read() if process.stderr else "No error output"
                )
                update_status(
                    f"OpenPose process failed (code {process.returncode}): {stderr_output}",
                    100,
                    False,
                )
                print(f"ERROR WITH MODEL {model}: {stderr_output}", flush=True)
                return False, outputs
            else:
                stderr = process.stderr.read()
                update_status(f"Error during processing: {stderr}", 100, False)
                return False, outputs

        except Exception as e:
            print(f"EXCEPTION WITH MODEL {model}: {str(e)}", flush=True)
            update_status(f"Exception during processing: {str(e)}", 100, False)
            return False, outputs

    update_status("Processing completed successfully", 100, False)
    return True, outputs


@app.route("/process", methods=["POST"])
def process_request():
    """API endpoint to process an image with multiple visualization options."""
    # Check if already processing
    with status_lock:
        if processing_status["is_processing"]:
            return jsonify(
                {
                    "success": False,
                    "message": "Already processing an image",
                    "status": processing_status,
                }
            )

    try:
        # Get the image path from the request
        data = request.json
        if not data or "image_path" not in data:
            return jsonify({"success": False, "message": "Image path not provided"})

        # Required parameters
        image_path = data["image_path"]
        output_dir = data.get("output_dir", "/images/output")

        # Optional visualization parameters
        model = data.get("model", "BODY_25")

        detect_face = data.get("detect_face", False)
        detect_hands = data.get("detect_hands", False)
        detect_feet = data.get("detect_feet", False)

        # Build a warnings array for any potential issues
        warnings = []
        # Add model-specific validation warnings
        if model != "BODY_25" and (detect_face or detect_hands):
            warning_msg = f"Face and hand detection with {model} model may be unstable. For best results, use BODY_25 model."
            warnings.append(warning_msg)
            print(f"WARNING: {warning_msg}", flush=True)

        # Still reject feet detection with non-BODY_25 models (since this is a technical limitation)
        if detect_feet and model != "BODY_25":
            return jsonify(
                {
                    "success": False,
                    "message": "Feet detection is only available with BODY_25 model",
                }
            )

        render_on_black = data.get("render_on_black", True)
        render_on_image = data.get("render_on_image", True)
        write_json = data.get("write_json", True)

        # Rendering thresholds
        render_threshold = float(data.get("render_threshold", 0.05))
        face_render_threshold = float(data.get("face_render_threshold", 0.4))
        hand_render_threshold = float(data.get("hand_render_threshold", 0.2))
        feet_render_threshold = float(data.get("feet_render_threshold", 0.03))
        keypoint_scale = int(data.get("keypoint_scale", 0))

        # Validate model selection
        if model not in ["BODY_25", "COCO", "MPI"]:
            return jsonify(
                {
                    "success": False,
                    "message": f"Invalid model: {model}. Must be one of: BODY_25, COCO, MPI",
                }
            )

        # Check if model files exist
        model_dir = f"/openpose/models/pose/{model.lower()}"
        if not os.path.exists(model_dir):
            return jsonify(
                {"success": False, "message": f"Model directory not found: {model_dir}"}
            )

        # For COCO specifically, we need to use the correct prototxt file
        if model == "COCO":
            if not os.path.exists(f"{model_dir}/pose_deploy_linevec.prototxt"):
                return jsonify(
                    {
                        "success": False,
                        "message": f"Required prototxt file for {model} not found",
                    }
                )

        # Validate the paths
        if not os.path.exists(image_path):
            return jsonify(
                {"success": False, "message": f"Image not found: {image_path}"}
            )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Check for model+feet compatibility BEFORE starting the thread
        if detect_feet and model != "BODY_25":
            return jsonify(
                {
                    "success": False,
                    "message": "Feet detection is only available with BODY_25 model",
                }
            )

        # Process the image in a separate thread
        threading.Thread(
            target=process_image,
            args=(
                image_path,
                output_dir,
                model,
                detect_face,
                detect_hands,
                detect_feet,
                write_json,
                render_on_black,
                render_on_image,
                render_threshold,
                face_render_threshold,
                hand_render_threshold,
                feet_render_threshold,
                keypoint_scale,
            ),
        ).start()

        response = {
            "success": True,
            "message": "Image processing started",
            "status": processing_status,
            "options": {
                "model": model,
                "detect_face": detect_face,
                "detect_hands": detect_hands,
                "detect_feet": detect_feet,
                "render_on_black": render_on_black,
                "render_on_image": render_on_image,
                "write_json": write_json,
                "render_threshold": render_threshold,
                "face_render_threshold": face_render_threshold,
                "hand_render_threshold": hand_render_threshold,
                "feet_render_threshold": feet_render_threshold,
                "keypoint_scale": keypoint_scale,
            },
        }

        if warnings:
            response["warnings"] = warnings

        return jsonify(response)
    except Exception as e:
        update_status(f"API error: {str(e)}", None, False)
        return jsonify({"success": False, "message": str(e)})


# [BASIC]
# @app.route("/status", methods=["GET"])
# def get_status():
#     """API endpoint to get the current processing status."""
#     with status_lock:
#         status_copy = dict(processing_status)
#     return jsonify(status_copy)


@app.route("/status", methods=["GET"])
def get_status():
    """API endpoint to get the current processing status and comprehensive output files."""
    # Optional check to verify if process is still running
    check_process = request.args.get("check_process", "false").lower() == "true"
    feet_render_threshold = 0.03  # Define here for feet detection checks

    with status_lock:
        status_copy = dict(processing_status)

    # If requested and processing is ongoing, check if process is still alive
    if check_process and status_copy.get("is_processing", False):
        try:
            # Check if any OpenPose processes are running
            result = subprocess.run(
                ["pgrep", "-f", "openpose.bin"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if result.returncode != 0:
                # No OpenPose processes found, but status says still processing
                # This means the process might have crashed
                with status_lock:
                    processing_status["is_processing"] = False
                    processing_status["status_message"] = (
                        "Process may have crashed or completed without updating status"
                    )
                    processing_status["progress"] = 100
                status_copy = dict(processing_status)
        except Exception as e:
            status_copy["status_error"] = str(e)

    # Always check for outputs, whether processing is complete or not
    if status_copy.get("current_image"):
        image_path = status_copy["current_image"]
        base_output_dir = "/images/output"  # Base output directory

        image_basename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(image_basename)[0]

        # Define output directories
        output_dirs = {
            "black_bg": os.path.join(base_output_dir, "black_bg"),
            "on_image": os.path.join(base_output_dir, "on_image"),
            "json": os.path.join(base_output_dir, "json"),
        }

        # Initialize outputs collection
        outputs = {
            "rendered_on_black": [],
            "rendered_on_image": [],
            "json": [],
        }

        # Check for rendered images on black background
        for ext in [".jpg", ".png"]:
            img_path = os.path.join(
                output_dirs["black_bg"], f"{name_without_ext}_rendered{ext}"
            )
            if os.path.exists(img_path):
                outputs["rendered_on_black"].append(img_path)

        # Check for rendered images on original image
        for ext in [".jpg", ".png"]:
            img_path = os.path.join(
                output_dirs["on_image"], f"{name_without_ext}_rendered{ext}"
            )
            if os.path.exists(img_path):
                outputs["rendered_on_image"].append(img_path)

        # Check for JSON keypoints
        json_path = os.path.join(
            output_dirs["json"], f"{name_without_ext}_keypoints.json"
        )
        if os.path.exists(json_path):
            outputs["json"].append(json_path)

        # Add outputs to status - even if they're partial
        if any(len(v) > 0 for v in outputs.values()):
            status_copy["outputs"] = outputs

        # Add processing information if JSON is available
        if len(outputs["json"]) > 0:
            try:
                with open(outputs["json"][0], "r") as f:
                    keypoints_data = json.load(f)

                # Extract basic info
                num_people = len(keypoints_data.get("people", []))

                # Add keypoint statistics to status
                keypoint_stats = {
                    "num_people_detected": num_people,
                    "has_face_keypoints": False,
                    "has_hand_keypoints": False,
                    "has_feet_keypoints": False,
                    "model_used": "unknown",
                }

                # Check if any people were detected and extract more detailed info
                if num_people > 0:
                    person = keypoints_data["people"][0]
                    keypoint_stats["has_face_keypoints"] = "face_keypoints_2d" in person
                    keypoint_stats["has_hand_keypoints"] = (
                        has_valid_keypoints(person.get("hand_left_keypoints_2d", [])) or
                        has_valid_keypoints(person.get("hand_right_keypoints_2d", []))
                    )

                    if "pose_keypoints_2d" in person:
                        body_keypoints = np.array(person["pose_keypoints_2d"]).reshape(
                            -1, 3
                        )
                        # Check if any foot keypoints (19-24) have confidence > threshold
                        if len(body_keypoints) >= 25:  # BODY_25 model
                            foot_indices = [19, 20, 21, 22, 23, 24]
                            keypoint_stats["has_feet_keypoints"] = any(
                                body_keypoints[idx, 2] > feet_render_threshold
                                for idx in foot_indices
                                if idx < len(body_keypoints)
                            )

                    # Determine model based on number of body keypoints
                    body_keypoints = np.array(
                        person.get("pose_keypoints_2d", [])
                    ).reshape(-1, 3)
                    num_keypoints = len(body_keypoints)

                    if num_keypoints == 25:
                        keypoint_stats["model_used"] = "BODY_25"
                    elif num_keypoints == 18:
                        keypoint_stats["model_used"] = "COCO"
                    elif num_keypoints == 15:
                        keypoint_stats["model_used"] = "MPI"

                    # Add model-specific keypoint information
                    if keypoint_stats["model_used"] == "BODY_25":
                        # Body_25 specific processing
                        # (feet detection already handled above)
                        pass
                    elif keypoint_stats["model_used"] == "COCO":
                        # COCO specific keypoint mappings/processing
                        keypoint_stats["coco_specific_info"] = (
                            "COCO model has 18 keypoints"
                        )
                    elif keypoint_stats["model_used"] == "MPI":
                        # MPI specific keypoint mappings/processing
                        keypoint_stats["mpi_specific_info"] = (
                            "MPI model has 15 keypoints"
                        )

                status_copy["keypoint_stats"] = keypoint_stats

            except Exception as e:
                status_copy["keypoint_stats_error"] = str(e)

    # Add additional status information
    if status_copy.get("is_processing", False):
        status_copy["estimated_completion"] = "Checking for output files..."
        if "outputs" in status_copy:
            if status_copy["outputs"]["json"]:
                status_copy["estimated_completion"] = (
                    "JSON output complete, finalizing processing..."
                )
            elif (
                status_copy["outputs"]["rendered_on_black"]
                or status_copy["outputs"]["rendered_on_image"]
            ):
                status_copy["estimated_completion"] = (
                    "Renderings complete, generating JSON output..."
                )
            else:
                status_copy["estimated_completion"] = (
                    "Processing image, no outputs yet..."
                )

    return jsonify(status_copy)


@app.route("/stop", methods=["POST"])
def stop_processing():
    """API endpoint to stop the current image processing."""
    global process_handle

    print(
        f"STOP requested. Current process_handle: {process_handle}, is_processing: {processing_status['is_processing']}",
        flush=True,
    )

    # First check if we're processing anything
    with status_lock:
        is_processing = processing_status["is_processing"]
        if not is_processing:
            return jsonify(
                {"success": False, "message": "No active processing to stop"}
            )

    # Get local reference to the process handle outside the lock
    local_process = process_handle

    # If we have no process to stop
    if local_process is None:
        update_status("No process found to stop", 100, False)
        return jsonify(
            {"success": False, "message": "Process information missing, cannot stop"}
        )

    # Try to terminate the process
    try:
        update_status("Stopping process...", None, None)

        # Terminate and wait briefly outside the lock
        local_process.terminate()
        time.sleep(1)

        # Force kill if still running
        if local_process.poll() is None:
            local_process.kill()

        # Reset the process handle
        process_handle = None

        # Update the status
        update_status("Processing stopped by user", 100, False)

        return jsonify(
            {
                "success": True,
                "message": "Processing stopped",
                "status": processing_status,
            }
        )

    except Exception as e:
        # Make sure we release the process even on error
        process_handle = None
        update_status(f"Error while stopping: {str(e)}", 100, False)

        return jsonify(
            {"success": False, "message": f"Error stopping process: {str(e)}"}
        )


if __name__ == "__main__":
    print("Starting OpenPose API Server...", flush=True)
    app.run(host="0.0.0.0", port=2500)
