# Terraform - Automated Event Driven Security Remediation

The Terraform module and Cloud Function is used to demonstrate the concepts discussed in this [Article](incoming_url). This repo contains all you need to begin automating remediations for [Event Threat Detection](https://cloud.google.com/event-threat-detection/) findings.

## Prerequisites 

Due to changes in the GCP provider, you can only deploy Cloud Functions with Terraform when using a Service Account.  See [Github Issue.](https://github.com/terraform-providers/terraform-provider-google/issues/5388)

The service account running terraform must have the following permissions:

At the organization level:
* Organization Role Administrator
* Logs Configuration Writer
* Organization Administrator


At the project level:
* Pub/Sub Admin
* Cloud Functions Admin
* Storage Admin
* Service Account Admin
* Service Account User

## Usage

1. Clone Repository Locally.
```
git clone git@github.com:ScaleSec/gcp_threat_detection_auto_remediation.git
```
2. Change directory into the newly cloned repository.
```
cd gcp_threat_detection_auto_remediation
```
3. Create a terraform.tfvars file - Replace values before running command.
```
cat > terraform.tfvars <<EOF
  org_id                       = "<<replace with your org id>>"
  project                      = "<<replace with your project id>>"
EOF
```

4. Authenticate your Google Cloud Service Account in one of ways defined in the [Terraform Documentation.](https://www.terraform.io/docs/providers/google/guides/provider_reference.html#full-reference)
```
gcloud auth activate-service-account
```
```
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/yourSAKey.json
```

5. Run the following Terraform commands:

```
terraform init
terraform plan
terraform apply
```

6. To test the Cloud Function:

* Add a @gmail.com IAM member to your project with the role **Project Editor**.
* Refresh the IAM page and the previously added IAM member should be removed.
* Navigate to the [Cloud Functions page](https://console.cloud.google.com/functions/) in the Cloud Console and select the function deployed via terraform.
* Click the 'View Logs' Button to view the outputs of the function.


## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|:----:|:-----:|:-----:|
| org_id | The ID of the Organization to provision resources. | string | - | yes |
| project |The ID of the project where the pub/sub topic will be installed.  | string | - | yes |
| region | The location of resources | string | `us-east1` | no |
| name | Prefix for resource naming | string | `etd` | no |
| org_sink_filter | The Log Filter to apply to the Org Level export. | string | `resource.type:threat_detector resource.labels.detector_name=iam_anomalous_grant` | no |

## Outputs

| Name | Description |
|------|-------------|
| topic_name    | The name of the pub/sub topic where logs are sent to. |
| project       | The Project which hosts the pub/sub topic and subscription resources. |
| organization_sink_writer | The Service Account associated with the organization sink. |
| function_name | The Cloud Function that performs the IAM administration. |


## Limitation of Liability
Please view the [License](LICENSE) for limitations of liability.
