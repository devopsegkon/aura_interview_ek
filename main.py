from constructs import Construct
from cdktf import App, TerraformStack, S3Backend, TerraformVariable, TerraformAsset, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.instance import Instance
from cdktf_cdktf_provider_aws import s3_bucket
import os
import datetime
from cdktf_cdktf_provider_aws import s3_bucket_website_configuration
from cdktf_cdktf_provider_aws import s3_bucket_policy
from cdktf_cdktf_provider_aws import s3_bucket_public_access_block
from cdktf_cdktf_provider_aws import cloudfront_distribution
from cdktf_cdktf_provider_aws import cloudfront_origin_access_control
from cdktf_cdktf_provider_aws import s3_bucket_public_access_block
from cdktf_cdktf_provider_aws import wafv2_ip_set
from cdktf_cdktf_provider_aws import wafv2_rule_group
from cdktf_cdktf_provider_aws import wafv2_web_acl
from cdktf_cdktf_provider_aws import s3_object

def create_index_file():
    file = open("index.html", "w")
    file.write('<html xmlns="http://www.w3.org/1999/xhtml" >\n')
    file.write("<head>\n")
    file.write("    <title>Hello Aura</title>\n")
    file.write("</head>\n")
    file.write("<body>\n")
    file.write("    <h1>Hello, World!</h1>\n")
    file.write("    <p>My deployment time was:</p>\n")
    file.write("    <p>")
    # Get the current date and time
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    file.write(current_time)
    file.write("    </p>\n")
    file.write("</body>\n")
    file.write("</html>\n")
    file.close()

create_index_file()

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        AwsProvider(self, 'Aws', region='us-east-1')

        S3Backend(self,
            bucket="terraform-state-aura-ek",
            key="aura",
            encrypt=True,
            region="us-east-1"
        )

        website_bucket_name = TerraformVariable(self, "website_bucket_name",
                    type = "string",
                    default = "aura-interview-ek-website",
                    description = "Bucket for public static website"
        )

        my_ip_address = TerraformVariable(self, "my_ip_address",
                    type = "string",
                    default = "76.130.240.10/32",
                    description = "My IP Address"
        )

        website_bucket = s3_bucket.S3Bucket(
            self,
            "s3_bucket_static_website",
            bucket=website_bucket_name.string_value
        )

        s3_bucket_public_access_block.S3BucketPublicAccessBlock(
            self,
            "restrict_access",
            bucket=website_bucket_name.string_value,
            block_public_acls       = True,
            block_public_policy     = True,
            ignore_public_acls      = True,
            restrict_public_buckets = True
        )
        

        asset = TerraformAsset(self, "index.html",
                    path=os.path.join(os.path.dirname(__file__), 'index.html')
                )


        access_control = cloudfront_origin_access_control.CloudfrontOriginAccessControl(
            self,
            "access_control",
            name = "accesscontrol",
            origin_access_control_origin_type = "s3",
            signing_behavior                  = "always",
            signing_protocol                  = "sigv4"
        )


        wafIpSet = wafv2_ip_set.Wafv2IpSet(
            self,
            "wafv2IpSet",
            name = "allowed-ip-set",
            scope = "CLOUDFRONT",
            ip_address_version = "IPV4",
            addresses          = [my_ip_address.string_value]
        )

        wafexample = wafv2_web_acl.Wafv2WebAcl(
            self,
            "wafexample",
            name = "cloudfront-acl",
            scope = "CLOUDFRONT",
            default_action = {
                "block": {

                },
            },
            visibility_config = {
                "cloudwatch_metrics_enabled":  False,
                "metric_name":                "friendly-metric-name",
                "sampled_requests_enabled":   False
            },
            rule = [{
                "name": "rule1",
                "action": {
                    "allow": {

                    },
                },
                "priority": 1,
                "statement": {
                    "ip_set_reference_statement": {
                        "arn": wafIpSet.arn
                    },
                },
                "visibilityConfig": {
                    "cloudwatchMetricsEnabled":  False,
                    "metricName":                "friendly-metric-name",
                    "sampledRequestsEnabled":   False
                }
            }]
        )

        cloudf_dist_ek = cloudfront_distribution.CloudfrontDistribution(
            self,
            "cloudf_dist_ek",
            enabled=True,
            web_acl_id=wafexample.arn,
            depends_on=[website_bucket,access_control],
            default_root_object = "index.html",
            origin= [{
                "domainName": website_bucket.bucket_regional_domain_name,
                "originId": website_bucket.bucket,
                "originAccessControlId": access_control.id,
                "custom_origin_config": {
                    "http_port":               80,
                    "https_port":              443,
                    "origin_keepalive_timeout":  5,
                    "origin_protocol_policy":   "http-only",
                    "origin_read_timeout":      30,
                    "origin_ssl_protocols":  [
                        "TLSv1.2"
                    ]
                }
            }],
            default_cache_behavior = {
                "cache_policy_id":         "658327ea-f89d-4fab-a63d-7e88639e58f6",
                "viewer_protocol_policy":  "redirect-to-https",
                "compress":               True,
                "allowed_methods":         ["GET", "HEAD", "OPTIONS"],
                "cached_methods":          ["GET", "HEAD", "OPTIONS"],
                "target_origin_id":        website_bucket.bucket
            },
            restrictions = {
                "geo_restriction": {
                    "restriction_type": "none",
                    "locations":         []
                }
            },
            viewer_certificate = {
                "cloudfront_default_certificate":  True
            }
        )


        bucket_policy = s3_bucket_policy.S3BucketPolicy(self, "my_policy",
                                      depends_on=[website_bucket],
                                      bucket=website_bucket_name.string_value,
                                      policy="""{
                                 "Version": "2012-10-17",
                                 "Statement": [
                                     {
                                         "Effect": "Allow",
                                         "Principal": {
                                             "Service": "cloudfront.amazonaws.com"
                                         },
                                         "Action": [
                                             "s3:GetObject"
                                         ],
                                         "Resource": "arn:aws:s3:::%s/*",
                                         "Condition": {
                                            "StringEquals": {
                                                "AWS:SourceArn": "%s"
                                            }
                                        }
                                     }
                                 ]
                                 }
                                 """ % (website_bucket_name.string_value, cloudf_dist_ek.arn)
        )

        bucket_object = s3_object.S3Object(
            self,
            "s3_indexhtml_datetime",
            depends_on=[bucket_policy],
            bucket=website_bucket.bucket,
            key="index.html",
            source=asset.path,
            content_type= "text/html",
            metadata= {
                "content-type" : "text/html"
            }
        )

        TerraformOutput(self, "out_s3_bucket_website_url", value=website_bucket.bucket_regional_domain_name)
        TerraformOutput(self, "out_cloudfront_distribution_domain_name", value=cloudf_dist_ek.domain_name)
        

app = App()
MyStack(app, "python-aws")

app.synth()

