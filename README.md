# tf-state-change

*The script performs the following*: 
1. Downloads the states from s3
2. Copies `nlb` from state_a to state_b 
3. Copies `nlb_domain` from state_a to state_b
4. Copies `nlb_service` from state_a to state_b
5. Copies `nlb_certificate` from state_a to state_b
6. Copies `nlb_certificate_validation (route53_record)` from state_a to state_b
7. Copies `nlb_certificate_validation (acm_certificate_validation)` from state_a to state_b
8. Copies `nlb_broker_listeners` from state_a to state_b **keeping target_groups of state_b**
9. Copies `nlb_service_listeners` from state_a to state_b **keeping target_groups of state_b**
10. Uploads the state of cluster_b to s3

If you set the `--prometheus` parameter, is performs the following actions additionally:
1. Copies `nlb` (from prometheus module) from state_a to state_b 
2. Copies `internal_record_set` (from prometheus module) from state_a to state_b
3. Copies `nlb_service` (from prometheus module) from state_a to state_b
4. Copies `nlb_listeners` (from prometheus module) from state_a to state_b **keeping target_groups of state_b**

_*You can customize the behaviour in the main function_

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
usage: main.py [-h] --states STATES STATES --env ENV [--dry-run] [--prometheus]                                                                                                                                                                                                                                                                                              ─╯

optional arguments:
  -h, --help            show this help message and exit
  --states STATES STATES
                        List of state files to work with
  --env ENV             nonprod or prod
  --dry-run             Run without uploading state back to S3. The changes will be saved to a new "modified" directory
  --prometheus          Set this parameter if prometheus ingress enabled in target clusters
```

Example:
```
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate --env nonprod --dry-run
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate --env nonprod

python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate --env nonprod --prometheus --dry-run
python main.py --states us-east-1-plygnd-ab-main.tfstate us-east-1-plygnd-ab2-main.tfstate --env nonprod --prometheus

```

TODO:
-
2. _backup delete resources_
