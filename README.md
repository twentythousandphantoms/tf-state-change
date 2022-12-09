# tf-state-change

Install
-
```
cd tf-state-change
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Usage
-
First, get the aws credentials via aws-saml-auth or awsmyid tools so that they are stored in the ~/.aws/credentials
```commandline
aws-saml-auth
or
awsmyid --login
```

Usage:
```
(venv) ab@ANDREIs-MacBook-Pro tf-state-change % python main.py -h
usage: main.py [-h] --states STATES [STATES ...] [--dry-run]

optional arguments:
  -h, --help            show this help message and exit
  --states STATES [STATES ...]
                        List of state files to work with
  --dry-run             Run without uploading state back to S3. The changes will be saved to a new "modified" directory

```

Example:
```
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate --dry-run
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate
```

What it does
-
1. Downloads the states from s3
2. Removes NLB from state of cluster_b
3. Copies nlb_broker_listeners, nlb_service_listeners, nlb_certificate and nlb_certificate_validation from the state of cluster_a to the state of cluster_b
4. Uploads the state of cluster_b to s3

_ tested on this pipeline: https://gitlab.disney.com/dtci-ep-swe/dtci-ep-swe-integration/jarvis/jarvis-platform-provision/-/jobs/17068191 _
_You can customize the behaviour in the main function_



TODO:
-
1. _make s3 object_name and bucket_name customizable to support AWS Prod account_
2. _backup delete resources_
