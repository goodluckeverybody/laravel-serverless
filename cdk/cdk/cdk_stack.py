from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretmanager
)
from constructs import Construct
from aws_cdk.aws_apigatewayv2_integrations_alpha import HttpLambdaIntegration
from aws_cdk.aws_apigatewayv2_alpha import HttpApi
from cdk.github_connection import GithubConnection

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "Vpc", max_azs=3, nat_gateways=1)

        ## Credentials
        secret = secretmanager.Secret.from_secret_name_v2(self, "RdsCredendtials", "rds")
        credents = rds.Credentials.from_secret(secret)

        ## Security Groups
        db_connection_group = ec2.SecurityGroup(self, "Proxy to RDS Connection", vpc=vpc)
        db_connection_group.add_ingress_rule(db_connection_group,ec2.Port.tcp(3306))

        lambda_to_proxy_group = ec2.SecurityGroup(self, "Lambda to RDS Proxy", vpc=vpc)
        db_connection_group.add_ingress_rule(lambda_to_proxy_group, ec2.Port.tcp(3306))

        ## RDS
        db = rds.DatabaseInstance(self, "Db",
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            vpc=vpc,
            credentials=credents,
            security_groups=[db_connection_group],
            database_name="laravel_serverless"
        )

        ## Proxy Lambda <-> RDS
        proxy = db.add_proxy("Proxy",
            borrow_timeout=Duration.seconds(30),
            secrets=[db.secret],
            vpc=vpc,
            security_groups=[db_connection_group],
            require_tls=False
        )

        laravel_web = _lambda.DockerImageFunction(self, "LaravelWeb",
            code=_lambda.DockerImageCode.from_image_asset("../codebase"),
            memory_size=1024,
            timeout=Duration.seconds(120),
            vpc=vpc,
            security_groups=[lambda_to_proxy_group],
            environment={
                "DB_HOST": proxy.endpoint,
                "DB_USERNAME": "admin",
                "DB_PASSWORD": "password"
            }
        )

        web_integration = HttpLambdaIntegration("laravel_web_integration", laravel_web)

        endpoint = HttpApi(self, "api_gateway",
            default_integration=web_integration
        )

        GithubConnection(
            self, 
            'GithubDeploymentRole', 
            github_org='goodluckeverybody', 
            github_repo='laravel-serverless'
        )

        CfnOutput(self, "api_url", value=endpoint.url)