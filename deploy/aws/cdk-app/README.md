# Infra to deploy DocqAI on AWS

This CDK project deploys an instance of DocqAI to AWS.

This CDK project is design to also generate a CloudFormation template that we can use with a LaunchStack URL.

TypeScript rather than Python so we can easily create a FABR CDF package in the future

## LaunchStack URL 

- `cdk synth`
- 

## CD - Trigger just an app deploy for an environment

- publish updated container image. See Makefile in root of repo
- `aws elasticbeanstalk update-environment --application-name <app-name> --environment-name <env-name> --version-label <version label from console> --profile fabrexp`
  - Example: `aws elasticbeanstalk update-environment --application-name docqai --environment-name docqai --version-label docqappstack-appversion-240nebwgnt2z --profile fabrexp`
  - note: that we can use the same AppVersion if the Dockerrun.aws.json is pointing at the tag `latest` and the updated image is also tagged `latest`



## Publishing containers

The GH action `publish-container.yml` handles publishing to GCR ( Github Container Registry)

## /dockerrun/<app-name>

Container config files go in these folders. This is our folder convension. All the files in the folder our bundled and uploaded to S3 for deployment.

The dockerrun.aws.json (has to be v1) is how the EB HostManager know which image to pull for an environment and config the container on start up.

Dockerrun.aws.json v1 ref

<https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/single-container-docker-configuration.html#docker-configuration.no-compose>

## Notes

- EB bucket - EB creates a bucket in an account that launches EB. This is used for assets and logs. The bucket name follows the following convention "elasticbeanstalk-<region>-<account id>"
