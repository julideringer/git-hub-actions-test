#! /bin/sh

ACCOUNT_ID="416737519422"
REGION="eu-west-1"
REPOSITORY="user_profile_images"
IMAGE_NAME="profile_lambda_update_user"
IMAGE_VERSION="latest"
IMAGE=$IMAGE_NAME":"$IMAGE_VERSION

#aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 416737519422.dkr.ecr.eu-west-1.amazonaws.com
aws ecr create-repository --repository-name $REPOSITORY --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE
docker tag $IMAGE $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY:$IMAGE_VERSION
