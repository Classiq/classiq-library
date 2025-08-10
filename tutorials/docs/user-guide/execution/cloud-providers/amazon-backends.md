# Execution on Amazon Braket Cloud

The Classiq executor supports execution on Amazon Braket's cloud simulators and hardware.

<!-- prettier-ignore-start -->
!!! tip
    Backends may sometimes be unavailable. Check the availability windows with Amazon Braket.
<!-- prettier-ignore-end -->

## Usage

Execution on Amazon Braket requires an AWS account, and a role that Classiq can assume for execution.

=== "SDK"

    [comment]: DO_NOT_TEST

    ```python
    from classiq import AwsBackendPreferences

    preferences = AwsBackendPreferences(
        backend_name="Name of requested simulator or hardware",
        aws_role_arn="ARN of the CrossAccountRoleForBraket role",
        s3_bucket_name="S3 bucket name to save the results",
        s3_folder="The folder path within the S3 bucket, where the results will be saved",
        job_timeout="Timeout for execution (Optional)",
    )
    ```

=== "IDE"

     ![Opening info tab](../../../resources/excution_aws_login.png)

### Initial Account Setup

Before first use, the Classiq platform needs your permission to connect to your
AWS account. This is done by creating a cross-account role.

Classiq provides with the attached CloudFormation `AssumeRole.cf.yaml` file. It only has the permissions needed for Braket.

To create the cross-account role that only Classiq can use, deploy the CloudFormation file to your account:

1. Download the [AssumeRole.cf.yaml](../cloud-providers/resources/AssumeRole.cf.yaml) file.
2. Install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
3. Contact [Classiq support](mailto:support@classiq.io) to obtain these parameters:
    1. `CORRECT_TRUSTED_ACCOUNT`
    2. `CORRECT_EXTERNAL_ID_VALUE`
4. Execute this command:
    ```
    aws cloudformation create-stack --stack-name ClassiqBraketRole --template-body file://AssumeRole.cf.yaml --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=TrustedAccount,ParameterValue=${CORRECT_TRUSTED_ACCOUNT} ParameterKey=ExternalId,ParameterValue=${CORRECT_EXTERNAL_ID_VALUE}
    ```

<!-- prettier-ignore-start -->
!!! warning
    The required parameters may differ between users.
    Contacting Classiq support is required!
<!-- prettier-ignore-end -->

To learn more about IAM roles, refer to the [AWS documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html).

### Required Credentials

When executing via the Classiq platform using AWS Cloud, there are several
required credentials:

1. `aws_role_arn`
    1. Make sure the [initial setup](../cloud-providers/amazon-backends.md#initial-account-setup)
       step is completed.
    2. Go to the AWS Identity and Access Management (IAM) service.
    3. Under `Roles`, search for the `CrossAccountRoleForBraket` role.
    4. Copy this role's `ARN` and use it as the `aws_role_arn`.
2. `s3_bucket_name`
    1. Create a new bucket. Its name must start with `amazon-braket-`.
    2. Use the bucket name as the `s3_bucket_name`.
       This is the bucket that saves the execution results.
3. `s3_folder`
    1. Enter the path to the folder in the `S3 bucket`.
       This is the path in the bucket where the execution results are
       saved.

For further support, contact [Classiq support](mailto:support@classiq.io).

## Supported Backends

The Classiq executor supports any available gate-based Amazon Braket simulator and quantum hardware.

Included hardware:

-   "IonQ device"
-   "Lucy"
-   "Aspen-11"
-   "Aspen-M-1"

Included simulators:

-   "SV1"
-   "TN1"
-   "dm1"
