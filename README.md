Prep

keggle instructions

notes for future curls if things change


docker run -it --rm \
  -v $(pwd)/models:/openpose/models \
  -v $(pwd)/images:/images \
  openpose-cpu \
  ./build/examples/openpose/openpose.bin --image_dir /images --write_images /images/output --display 0



  {
  "image_path": "/images/test.jpg",
  "output_dir": "/images/output"
}


{
  "image_path": "/images/test.jpg",           // Required: Path to image within container
  "output_dir": "/images/output",             // Optional: Output directory (default: /images/output)
  
  // Model selection
  "model": "BODY_25",                         // Optional: Model type (BODY_25, COCO, MPI) (default: BODY_25)
  
  // Body part detection options
  "detect_face": false,                       // Optional: Enable face detection (default: false)
  "detect_hands": false,                      // Optional: Enable hand detection (default: false)
  "detect_feet": false,                      // Optional: Enable hand detection (default: false)
  
  // Output types
  "render_on_black": true,                    // Optional: Generate skeleton on black background (default: true)
  "render_on_image": true,                    // Optional: Generate skeleton on original image (default: true)
  "write_json": true,                         // Optional: Generate JSON keypoint data (default: true)
  
  // Detection thresholds
  "render_threshold": 0.05,                   // Optional: Body keypoint confidence threshold (default: 0.05)
  "face_render_threshold": 0.4,               // Optional: Face keypoint confidence threshold (default: 0.4)
  "hand_render_threshold": 0.2,               // Optional: Hand keypoint confidence threshold (default: 0.2)
  
  // Coordinate scaling
  "keypoint_scale": 0                         // Optional: Coordinate scale in JSON output (default: 0)
                                              // 0=original resolution, 3=normalized [0,1], 4=normalized [-1,1]
}


docker-compose down

COMPOSE_BAKE=true docker-compose up --build -d

docker-compose ps
docker ps
logs openpose-api


The keypoint_scale parameter only affects the JSON output, not the rendered images. That's why you're not seeing visual differences.

With keypoint_scale: 0: Coordinates in JSON are in pixel values (e.g., x: 320, y: 240)
With keypoint_scale: 3: Coordinates in JSON are normalized to [0,1] range (e.g., x: 0.33, y: 0.45)


docker exec open_pose_cpu_api_docker-openpose-api-1 /openpose/build/examples/openpose/openpose.bin --help | grep image

Model compatibility notes:
- BODY_25: Supports all features (face, hands, feet)
- COCO: Basic pose detection; face/hand detection may be unstable
- MPI: Basic pose detection; face/hand detection may be unstable