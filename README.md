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

Run:
```
python main.py --states region-cluster-a-main.tfstate region-cluster-b-main.tfstate
```

Example:
```
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate
```

What it does
-
1. Downloads the states from s3
2. Removes NLB from state of cluster_b
3. Copies nlb_broker_listeners, nlb_service_listeners, nlb_certificate and nlb_certificate_validation from the state of cluster_a to the state of cluster_b
4. Uploads the state of cluster_b to s3

_You can customize the behaviour in the main function_

TODO:
-
1. _make s3 object_name and bucket_name customizable to support AWS Prod account_
2. _backup delete resources_