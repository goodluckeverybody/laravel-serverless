from aws_cdk import (
    Duration,
    CfnOutput,
    aws_iam as iam,
    App,
)
from constructs import Construct

class GithubConnection(Construct):

    def __init__(self, scope: Construct, construct_id: str, github_org: str, github_repo: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        oidc_arn = f"arn:aws:iam::982195495700:oidc-provider/token.actions.githubusercontent.com"

        provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self, 
            'GithubProvider', 
            oidc_arn
        )

        principle = iam.OpenIdConnectPrincipal(provider).with_conditions(
            conditions={
                "StringLike": {
                    'token.actions.githubusercontent.com:sub':
                        f'repo:{github_org}/{github_repo}:*'
                }
            }
        )

        principle.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRoleWithWebIdentity"],
                resources=["*"]
            )
        )

        iam.Role(self, "deployment_role",
            assumed_by=principle,
            role_name=f"{github_org}-{github_repo}-deploy",
            max_session_duration=Duration.seconds(3600),
            inline_policies={
                "DeploymentPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=['sts:AssumeRole'],
                            resources=[f'arn:aws:iam::982195495700:role/cdk-*'],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            }
        )

        CfnOutput(self, "DeploymentRoleArn", value=f"arn:aws:iam::982195495700:role/{github_org}-{github_repo}-deploy")