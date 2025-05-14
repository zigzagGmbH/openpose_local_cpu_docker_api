# README

## Inspiration & Reason

- I wanted to have a separte effort to see if I can run openpose loaclly on my __mac__.
- I was inspired by the [online openposeai viz](https://openposeai.com/?lng=en) but wanted something where I can use a webcam to take a snapshot and get opnepose skeleton back - a humble wish.
- But after spending a full day almost to try to compile `openpose` on my `mac M3` chip and dealing with outdated instructions and code base I was almost about to give up.
- But then I thought probably someone ported it via `docker` and for `ubuntu` (where it's supposed to compile easily) and even better, for `cpu` and not ~~`CUDA`~~

## What It Tries to Solve

- This project creates a `cpu` only openpose image in `Ubuntu 18` so that we can run it form `macOS`.
- This then exposes 3 API end points:
  - `/process` (`POST` req): Takes an image (and few other parameters - more on those below) processes it using one of the 3 openpose models (`BODY_25`, `COCO`, `MPI`) and gives us `openpose` skeleton data (images and json)
  - `/stop` (`POST`): Stops a running job
  - `/status` (`GET`): Gives us some ongoing staus
- This way we __do not have to deal with__ the aforementioned issues on `macOS`, especially.
- And any language agnostic client, capable of `HTTP` can send image and recveive openpose data

## What It Doesn't Do

- This project currently doesn't support realtime video streams as `x11` forwarding on `macOS` was bit of an issue.
- This project currently doesn't support video file (from disk) analysis. Although if needed we can think about it. But I wanted a simple solution first.
- 

Note: there are other projects ...

---

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

---

## LICENSE

[MIT](LICENSE)

## Attribution

- [openpose (original)](https://github.com/CMU-Perceptual-Computing-Lab/openpose)
- [docker-openpose-cpu](https://github.com/seancook/docker-openpose-cpu/)