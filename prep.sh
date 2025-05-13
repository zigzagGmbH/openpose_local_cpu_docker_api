#!/bin/bash

# Reset
Reset='\033[0m'       # Text Reset

# Regular Colors
Black='\033[0;30m'        # Black
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[0;33m'       # Yellow
Blue='\033[0;34m'         # Blue
Purple='\033[0;35m'       # Purple
Cyan='\033[0;36m'         # Cyan
White='\033[0;37m'        # White

# Bold
BBlack='\033[1;30m'       # Black
BRed='\033[1;31m'         # Red
BGreen='\033[1;32m'       # Green
BYellow='\033[1;33m'      # Yellow
BBlue='\033[1;34m'        # Blue
BPurple='\033[1;35m'      # Purple
BCyan='\033[1;36m'        # Cyan
BWhite='\033[1;37m'       # White



# Create all required model directories but first clean-up
echo -e "\n${Red}Removing OLD \"models/\" dir ...${Reset}"
rm -rf models/
sleep 1
echo -e "\n${Yellow}Creating \"models/\" dir and sub directories ...${Reset}"
mkdir -p models/pose/body_25 models/pose/coco models/pose/mpi models/face models/hand
echo -e "${Purple}"
tree
echo -e "${Reset}"
sleep 1


# Download the prototxt files for each model
echo -e "\n${Yellow}Downloading all the necessary prorotext files in necessary sub directories ...${Reset}\n"
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/pose/body_25/pose_deploy.prototxt" -o models/pose/body_25/pose_deploy.prototxt
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/pose/coco/pose_deploy_linevec.prototxt" -o models/pose/coco/pose_deploy_linevec.prototxt
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/pose/mpi/pose_deploy_linevec.prototxt" -o models/pose/mpi/pose_deploy_linevec.prototxt
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/face/pose_deploy.prototxt" -o models/face/pose_deploy.prototxt
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/hand/pose_deploy.prototxt" -o models/hand/pose_deploy.prototxt
# Body model prototxt files
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/pose/body_25/pose_deploy_linevec_faster_4_stages.prototxt" -o models/pose/body_25/pose_deploy_linevec_faster_4_stages.prototxt
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/pose/body_25/pose_deploy_linevec.prototxt" -o models/pose/body_25/pose_deploy_linevec.prototxt
# Face model prototxt files
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/face/pose_deploy.prototxt" -o models/face/pose_deploy.prototxt 
# Hand model prototxt files
curl -L "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/hand/pose_deploy.prototxt" -o models/hand/pose_deploy.prototxt

echo -e "\n"
echo -e "${Purple}"
tree
echo -e "${Reset}"

# Download ALL models
# NOTE:
# The below links are not recheable anymore and I found online that the models are in Kaggle at (https://www.kaggle.com/datasets/changethetuneman/openpose-model).
# So, we have to use Kaggle API to download them

# ==== Not usable ==== #
# curl -L "http://posefs1.perception.cs.cmu.edu/OpenPose/models/pose/body_25/pose_iter_584000.caffemodel" -o models/pose/body_25/pose_iter_584000.caffemodel
# curl -L "http://posefs1.perception.cs.cmu.edu/OpenPose/models/pose/coco/pose_iter_440000.caffemodel" -o models/pose/coco/pose_iter_440000.caffemodel
# curl -L "http://posefs1.perception.cs.cmu.edu/OpenPose/models/pose/mpi/pose_iter_160000.caffemodel" -o models/pose/mpi/pose_iter_160000.caffemodel
# curl -L "http://posefs1.perception.cs.cmu.edu/OpenPose/models/face/pose_iter_116000.caffemodel" -o models/face/pose_iter_116000.caffemodel
# curl -L "http://posefs1.perception.cs.cmu.edu/OpenPose/models/hand/pose_iter_102000.caffemodel" -o models/hand/pose_iter_102000.caffemodel
# =================== #

# 2. Check if Kaggle CLI is installed
if ! command -v kaggle > /dev/null; then
    echo -e "\n${Red}Kaggle CLI not found. Installing ... ${Reset}"
    pip install kaggle
else
    echo -e "\n${Green}Kaggle CLI found!${Reset}"
fi

# 3. Check if Kaggle credentials are configured
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo -e "${Red}Kaggle API credentials not found.${Reset}"
    echo -e "${Cyan}Please visit https://www.kaggle.com/account and create an API token."
    echo -e "Then place the kaggle.json file in ~/.kaggle/"
    echo -e "After that, run this script again.${Reset}"
    exit 1
fi

# 4. Download the dataset
echo -e "${Blue}We will download Open-Pose dataset from ${Yellow}\"changethetuneman/openpose-model\"${Reset}:"
kaggle datasets files changethetuneman/openpose-model
echo ""
sleep 1
echo -e "${Yellow}Downloading the OpenPose dataset...${Reset}"
mkdir -p openpose_models
cd openpose_models
kaggle datasets download changethetuneman/openpose-model --force
unzip openpose-model.zip
ls -l
rm *.zip
echo -e "\n${Green}Downloaded all the OpenPose data!${Reset}"
sleep 1

# 6. Move the model files to their respective directories
echo -e "\n${Yellow}Moving all the OpenPose dataset to respective sub-directories ...${Reset}"
mv pose_iter_116000.caffemodel ../models/face/
mv pose_iter_102000.caffemodel ../models/hand/
mv pose_iter_584000.caffemodel ../models/pose/body_25/
mv pose_iter_440000.caffemodel ../models/pose/coco/
mv pose_iter_160000.caffemodel ../models/pose/mpi/
cd ..
rm -rf openpose_models/
echo -e "\n"
echo -e "${Purple}"
tree
echo -e "${Reset}"
echo -e "\n${Green}Download complete!${Reset} Models are organized!"
sleep 1