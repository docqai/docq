import * as cdk from "aws-cdk-lib"; //cdk v2
import { Construct } from "constructs";
import path from "path";

import * as iam from 'aws-cdk-lib/aws-iam';
import * as elasticbeanstalk from 'aws-cdk-lib/aws-elasticbeanstalk';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as assets from 'aws-cdk-lib/aws-s3-assets';
import { CfnInstance } from "aws-cdk-lib/aws-ec2";
import { CfnApplication } from "aws-cdk-lib/aws-appconfig";
//import * as ecr from '@aws-cdk/aws-ecr';
//import { SecurityGroup, Vpc } from "aws-cdk-lib/aws-ec2";
//import * as efs from '@aws-cdk/aws-efs';





export type OptionSetting = { namespace: string, optionName: string, value: string };

export type TierType = "Standard" | "SQS/HTTP";
export type TierName = "WebServer" | "Worker";
export type EnvironmentTier = { name: TierName, type: TierType }

export enum EnvironmentType {
  LoadBalanced = "LoadBalanced",
  SingleInstance = "SingleInstance",
}

export enum ProxyServer {
  Nginx = "nginx",
  /**
   * Amazon Linux AM and Docker w/DC only
   */
  None = "none",
}

const webServerTier: EnvironmentTier = { name: "WebServer", type: "Standard" };


const workerTier: EnvironmentTier = { name: "Worker", type: "SQS/HTTP" };

export const environmentTiers = {
  WebServer: webServerTier,
  /**
   * @see https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features-managing-env-tiers.html
   */
  Worker: workerTier,
}



export interface DocqStackProps extends cdk.StackProps {
  /**
   * This name will be used in conventions for naming resources. Will be used in CD pipeline for deployment
   */
  name: string;
  /**
   * Roughly maps to instance sizing (memory and CPU)
   */
  size: "small" | "medium" | "large";
  /**
   * If false runs single instances. Else runs load balanced instances
   */
  resiliant: boolean;

}


//default to the containers in the folder.



export class DocqStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: DocqStackProps) {
    super(scope, id, props);


    const thisAccuntId = cdk.Stack.of(this).account;
    const thisRegion = cdk.Stack.of(this).region;

    const ebS3BucketName = `elasticbeanstalk-${thisRegion}-${thisAccuntId}`;
    const ebS3Bucket = s3.Bucket.fromBucketName(this, 'ebS3Bucket', ebS3BucketName);


    const paramName = new cdk.CfnParameter(this, 'paramName', {
      type: 'String',
      description: 'Give the Docq AI instance a name. It will be used internally to name AWS resources in the stack',
      default: props!.name,
    });

    const name = paramName.valueAsString;

    const { size, resiliant, } = props!;

    const frontendApp = new elasticbeanstalk.CfnApplication(this, 'DocqFrontendApplication', {
      applicationName: name,
      description: 'Docq AI frontend application',
    });


    const rndStr = "GtdoS" //generateRandomAlphanumericString(6)
    const resourceNamePrefix = `docqai-${rndStr}`;


    const frontendAppVersion = createDockerAppVersion(this, "frontend", { appName: resourceNamePrefix, containerConfigFolder: "./dockerrun/docqai", app: frontendApp });

    const instanceProfile = createInstanceProfile(this, rndStr);



    // const bucket = new s3.Bucket(this, 'MyBucket', {
    //   bucketName: `${appName}-eb-deployments`,
    //   blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    //   encryption: s3.BucketEncryption.S3_MANAGED,
    //   enforceSSL: true,
    //   versioned: true,
    //   removalPolicy: cdk.RemovalPolicy.RETAIN,

    // });


    // const asset = new assets.Asset(this, 'DockerRunAwsJsonZip', { // uploads into a CDK assets bucket
    //   path: path.join(__dirname, props?.containerConfigFolder || "dockerrun"),

    // });


    // const appVersionLabel = `${appName}-v1.0.0`;
    // const frontendAppVersion = new elasticbeanstalk.CfnApplicationVersion(this, 'AppVersionFrontend', {
    //   applicationName: frontendApp.ref,
    //   sourceBundle: {
    //     s3Bucket: asset.bucket.bucketName,
    //     //s3Key: `apps/${appName}/Dockerrun.aws.json`,
    //     s3Key: `${asset.s3ObjectKey}`,
    //   },

    // });



    const openai_api_key_arn = "arn:aws:secretsmanager:eu-west-1:246744040432:secret:docq/dev/openai_api_key-ssoE63"

    const webAppEnv = createDockerEnvironment(this, resourceNamePrefix, {
      name: name,
      app: frontendApp,
      appVersion: frontendAppVersion,
      instanceProfile: instanceProfile,
      type: EnvironmentType.SingleInstance,
      environmentVariables: [
        { "DOCQ_DATA": "./.persisted/" }, 
        { "OPENAI_API_KEY": `$(aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:${thisRegion}:${thisAccuntId}:secret:${openai_api_key_arn} --region ${thisRegion} | jq --raw-output '.SecretString' | jq -r .password)` }],
    });

//https://stackoverflow.com/questions/41283467/is-there-a-way-of-hiding-environment-variables-in-aws-elastic-beanstalk


    new cdk.CfnOutput(this, 'AppEnvEndpoint', {
      value: `http://${webAppEnv.attrEndpointUrl}`,
    });


    new cdk.CfnOutput(this, 'AppEnvCName', {
      value: `http://${webAppEnv.cnamePrefix}`,
    });

    new cdk.CfnOutput(this, 'AppName', {
      value: frontendApp.applicationName!.toString(),
    });


    // const appName2 = `ml-model-huggingface-app`;

    // const huggingfaceAsset = new assets.Asset(this, 'huggingfaceDockerRunAwsJsonZip', { // uploads into a CDK assets bucket
    //   path: path.join(__dirname, "dockerrun-huggingface"),

    // });

    // const mlModelHuggingfaceApp = new elasticbeanstalk.CfnApplication(this, 'MlModelHuggingfaceApplication', {
    //   applicationName: appName2,
    //   description: 'Huggingface ML Model using the HazyResearch Manifest wrapper',
    // });

    // const mlModelHuggingfaceAppVersion = new elasticbeanstalk.CfnApplicationVersion(this, 'MlModelHuggingfaceApplicationVersion', {
    //   applicationName: mlModelHuggingfaceApp.ref,
    //   sourceBundle: {
    //     s3Bucket: huggingfaceAsset.bucket.bucketName,
    //     //s3Key: `apps/${appName}/Dockerrun.aws.json`,
    //     s3Key: `${huggingfaceAsset.s3ObjectKey}`,
    //   },

    // });

    // mlModelHuggingfaceAppVersion.addDependency(mlModelHuggingfaceApp);
    // frontendAppVersion.node.addDependency(huggingfaceAsset);

    // const huggingfaceAppEnv = new elasticbeanstalk.CfnEnvironment(this, "EbEnvironmentHuggingface", {
    //   //solutionStackName: '64bit Amazon Linux 2 v3.4.1 running Docker 19.03.13',
    //   solutionStackName: "64bit Amazon Linux 2 v3.5.7 running Docker", // @see https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html#platforms-supported.docker
    //   //platformVersion: '3.4.1',
    //   environmentName: "ml-model-huggingface-env",
    //   description: "Huggingface ML Model using the HazyResearch Manifest wrapper",
    //   tier: environmentTiers.WebServer,


    //   //instanceType: 't3.small',
    //   applicationName: appName2,
    //   versionLabel: mlModelHuggingfaceAppVersion.ref, // specify the version of the application that you want to deploy
    //   optionSettings: [ // @see https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/command-options-general.html
    //     {
    //       namespace: 'aws:autoscaling:launchconfiguration',
    //       optionName: 'IamInstanceProfile',
    //       value: instanceProfile.instanceProfileName,
    //     },
    //     {
    //       namespace: 'aws:autoscaling:launchconfiguration',
    //       optionName: 'RootVolumeSize',
    //       value: '250', // in GB. with what ever the default is for t3.2xLarge, Docker pull in fails with disk space error
    //     },
    //     {
    //       namespace: 'aws:autoscaling:asg',
    //       optionName: 'MinSize',
    //       value: props!.ebEnvProps?.autoscaleMinSize?.toString() ?? '1',
    //     },
    //     {
    //       namespace: 'aws:autoscaling:asg',
    //       optionName: 'MaxSize',
    //       value: props!.ebEnvProps?.autoscaleMaxSize?.toString() ?? "1",
    //     },
    //     {
    //       namespace: 'aws:ec2:instances',
    //       optionName: 'InstanceTypes',
    //       value: `t3.2xlarge`,
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:environment',
    //       optionName: 'EnvironmentType',
    //       value: EnvironmentType.SingleInstance,
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:environment:proxy',
    //       optionName: 'ProxyServer',
    //       value: ProxyServer.Nginx,
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:application',
    //       optionName: 'Application Healthcheck URL',
    //       value: "/", // valid value ex: `/` (HTTP GET to root path),  `/health`, `HTTPS:443/`, `HTTPS:443/health`
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:application:environment',
    //       optionName: 'RANDOM_VAR',
    //       value: 'hello env var',
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:application:environment',
    //       optionName: 'FLASK_PORT',
    //       value: '80',
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:healthreporting:system',
    //       optionName: 'SystemType',
    //       value: 'enhanced',
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
    //       optionName: 'StreamLogs',
    //       value: 'true',
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
    //       optionName: 'DeleteOnTerminate',
    //       value: 'true',
    //     },
    //     {
    //       namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
    //       optionName: 'RetentionInDays',
    //       value: '1',
    //     },
    //   ],
    // });

    // new cdk.CfnOutput(this, 'huggingfaceAppEnvEndpoint', {
    //   value: `http://${huggingfaceAppEnv.attrEndpointUrl}`,
    // });


    // new cdk.CfnOutput(this, 'huggingfaceAppEnvCName', {
    //   value: `http://${huggingfaceAppEnv.cnamePrefix}`,
    // });

    // new cdk.CfnOutput(this, 'huggingfaceAppEnvName', {
    //   value: huggingfaceAppEnv.applicationName!.toString(),
    // });



  }
}

function generateRandomAlphanumericString(length: number) {
  const alphaChar = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  const numericChar = '0123456789';

  let result = '';
  for (let i = 0; i < length; i++) {
    result += alphaChar.charAt(Math.floor(Math.random() * alphaChar.length));
  }
  return result;
}


// aws ecr-public get-login-password --region us-east-1 --profile <your fabr profile name here> | docker login --username AWS --password-stdin public.ecr.aws/q0o2r1k7
// docker tag docqai/docq-rs:latest public.ecr.aws/q0o2r1k7/docqai/docq-rs:latest
// docker push public.ecr.aws/q0o2r1k7/docqai/docq-rs:latest


export interface AppVersionProps {
  appName: string;
  /**
   * The CfnApplication that this verison belongs to.
   */
  app: elasticbeanstalk.CfnApplication;
  /**
   * folder that contains the Dockerrun.aws.json v1 config file.
   */
  containerConfigFolder: string;
}

function createDockerAppVersion(scope: Construct, name: string, props: AppVersionProps): elasticbeanstalk.CfnApplicationVersion {

  const asset = new assets.Asset(scope, 'DockerRunAwsJsonZip', { // uploads into a CDK assets bucket
    //path: path.join(__dirname, props?.containerConfigFolder || "dockerrun"),
    path: path.join(props?.containerConfigFolder || "dockerrun/dockerrun"),
  });

  const appVersion = new elasticbeanstalk.CfnApplicationVersion(scope, `AppVersion-${name}`, {
    applicationName: props.app.ref,
    sourceBundle: {
      s3Bucket: asset.bucket.bucketName,
      //s3Key: `apps/${appName}/Dockerrun.aws.json`,
      s3Key: `${asset.s3ObjectKey}`,
    },

  });

  appVersion.addDependency(props.app);
  appVersion.node.addDependency(asset);
  return appVersion;
}


/**
 * 
 * @param scope 
 * @param name used to name resources. suffixed with '-aws-elasticbeanstalk-ec2-role'
 * @param props if no managed policy names are provided AWSElasticBeanstalkWebTier is used as the default. Import a managed policy from one of the policies that AWS manages.
  
    For this managed policy, you only need to know the name to be able to use it.

    Some managed policy names start with "service-role/", some start with "job-function/", and some don't start with anything. Include the prefix when constructing this object.
 */
function createInstanceProfile(scope: Construct, name: string, props?: { awsManagedPolicyNames?: string[] }): iam.CfnInstanceProfile {
  const role = new iam.Role(scope, `${name}-aws-elasticbeanstalk-ec2-role`, {
    assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
  });

  if (props && props.awsManagedPolicyNames && props.awsManagedPolicyNames.length > 0) {
    props.awsManagedPolicyNames.forEach(policyName => {
      role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName(policyName))
    });
  } else {
    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName("AWSElasticBeanstalkWebTier"));
  }

  const profileName = `${name}-InstanceProfile`

  const instanceProfile = new iam.CfnInstanceProfile(scope, profileName, {
    instanceProfileName: profileName,
    roles: [
      role.roleName
    ]
  });

  return instanceProfile;
}


export interface EnvironmentProps {
  /**
   * The name of the Elastic Beanstalk environment
   */
  name: string;
  description?: string;

  app: elasticbeanstalk.CfnApplication;


  appVersion?: elasticbeanstalk.CfnApplicationVersion;

  instanceProfile: iam.CfnInstanceProfile;

  /**
   * Examples: `/` (HTTP GET to root path),  `/health`, `HTTPS:443/`, `HTTPS:443/health`
   * Defaults to `/`
   */
  healthCheckUrl?: string;

  environmentVariables?: { [key: string]: string }[];

  /**
   * folder name with a Dockerrun.aws.json v1 file. Relative to the 'lib' folder. This folder can only contain this single file. If no provided deploys the EB default app
   */
  containerConfigFolder?: string;

  /**
   * Comma-separated list of EC2 instance types to be used. The first in the list is the default.
   * Default value is `t3.medium`
   */
  ec2InstanceTypes?: string;

  /**
   * LoadBalanced or SingleInstance environment. SingleInstance has no ALB. 
   */
  type: EnvironmentType;

  /**
   * when type is LoadBalanced, the minimum number of instances
   * Default value is 1
   */
  autoscaleMinSize?: number;

  /**
   * when type is LoadBalanced, the maximum number of instances
   * Default value is 1
   */
  autoscaleMaxSize?: number;

}


function createDockerEnvironment(scope: Construct, name: string, props: EnvironmentProps): elasticbeanstalk.CfnEnvironment {



  const optionSettings1: elasticbeanstalk.CfnEnvironment.OptionSettingProperty[] = [
    {
      namespace: 'aws:autoscaling:launchconfiguration',
      optionName: 'IamInstanceProfile',
      value: props.instanceProfile.instanceProfileName,
    },
    {
      namespace: 'aws:autoscaling:asg',
      optionName: 'MinSize',
      value: props.autoscaleMinSize?.toString() ?? '1',
    },
    {
      namespace: 'aws:autoscaling:asg',
      optionName: 'MaxSize',
      value: props.autoscaleMaxSize?.toString() ?? "1",
    },
    {
      namespace: 'aws:autoscaling:launchconfiguration',
      optionName: 'RootVolumeSize',
      value: '250', // in GB. with what ever the default is for t3.2xLarge, Docker pull in fails with disk space error
    },
    {
      namespace: 'aws:ec2:instances',
      optionName: 'InstanceTypes',
      value: props.ec2InstanceTypes ? props.ec2InstanceTypes : 't3.medium',
    },
    {
      namespace: 'aws:elasticbeanstalk:environment',
      optionName: 'EnvironmentType',
      value: EnvironmentType.SingleInstance,
    },
    {
      namespace: 'aws:elasticbeanstalk:environment:proxy',
      optionName: 'ProxyServer',
      value: ProxyServer.Nginx,
    },
    {
      namespace: 'aws:elasticbeanstalk:application',
      optionName: 'Application Healthcheck URL',
      value: props.healthCheckUrl ?? "/",
    },
    {
      namespace: 'aws:elasticbeanstalk:healthreporting:system',
      optionName: 'SystemType',
      value: 'enhanced',
    },
    {
      namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
      optionName: 'StreamLogs',
      value: 'true',
    },
    {
      namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
      optionName: 'DeleteOnTerminate',
      value: 'true',
    },
    {
      namespace: 'aws:elasticbeanstalk:cloudwatch:logs',
      optionName: 'RetentionInDays',
      value: '1',
    },
  ];


  props.environmentVariables?.forEach(envVar => {
    console.log(`key: ${Object.keys(envVar)[0]}, value: ${Object.values(envVar)[0]}`);
    optionSettings1.push({
      namespace: 'aws:elasticbeanstalk:application:environment',
      optionName: Object.keys(envVar)[0],
      value: Object.values(envVar)[0],
    });
  });





  // Create an Elastic Beanstalk environment.
  const appEnv = new elasticbeanstalk.CfnEnvironment(scope, `${name}`, {

    solutionStackName: "64bit Amazon Linux 2 v3.5.7 running Docker", // @see https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html#platforms-supported.docker

    environmentName: props.name,
    description: props.description ?? `Environment for ${props.name}`,
    tier: environmentTiers.WebServer,


    //instanceType: 't3.small',
    applicationName: props.app.applicationName ?? `${name}`,
    versionLabel: props.appVersion?.ref, // specify the version of the application that you want to deploy
    // @see https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/command-options-general.html
    optionSettings: optionSettings1,



  });



  appEnv.addDependency(props.app);



  return appEnv;
}