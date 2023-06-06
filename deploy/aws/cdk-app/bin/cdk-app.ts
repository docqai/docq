#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DocqStack } from '../library/cdk-app-stack';

const app = new cdk.App();



new DocqStack(app, 'DocqAppStack', {
  name: "docqai",
  description: 'Docq AI application',
  size: "small",
  resiliant: false

  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
  
});

// const cftemplateUri = "https://cdk-hnb659fds-assets-246744040432-eu-west-1.s3.eu-west-1.amazonaws.com/cb650bc664b488ef57c3e5ff8bb37f61d3c5d52d9757a758f432079953ff2da8.json"
// new cdk.CfnOutput(app, 'LaunchStackUrl eu-west-1', {
//   value: `https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=DocqAI&templateURL=https://cdk-hnb659fds-assets-246744040432-eu-west-1.s3.eu-west-1.amazonaws.com/cf2cad040c0869ad181c5938f4adb6632d0017416246d4563d0dbcf3e34344a8.json`,
// });


//TODO: add a second stack to upload the template to s3 or do it on the CLI


