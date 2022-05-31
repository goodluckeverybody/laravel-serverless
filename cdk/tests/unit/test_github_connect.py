from aws_cdk import (
    App,
    Stack,
    assertions
)
from cdk.github_connection import GithubConnection

def test_github_connection_construct():
    org = "test"
    repo = "repo"

    stack = Stack()

    GithubConnection(
        stack,
        "TestGithubConnection",
        github_org=org,
        github_repo=repo
    )

    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::IAM::Role", {
        "RoleName": f"{org}-{repo}-deploy"
    })

    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{org}/{repo}:*"
                        }
                    },
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": f"arn:aws:iam::{App.account}:oidc-provider/token.actions.githubusercontent.com"
                    }
                }
            ],
        }
    })

    template.has_resource_properties("AWS::IAM::Role", {
        "Policies": [
            {
                "PolicyDocument": {
                "Statement": [
                    {
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Resource": f"arn:aws:iam::{App.account}:role/cdk-*"
                    }
                ],
                "Version": "2012-10-17"
                },
                "PolicyName": "DeploymentPolicy"
            }
        ]
    })