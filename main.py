"""
Main TFStateResourceSwapper script.
"""
import sys
import argparse

from tf_state import TerraformState


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--states', nargs='+', help='List of state files to work with', required=True)
    parser.add_argument('--dry-run', help='Run without uploading state back to S3. The changes will be saved to a new '
                                          '"modified" directory',
                        required=False, action="store_true", dest="dry_run")
    args = parser.parse_args()
    return args.states, args.dry_run


def download_states(states):
    for name in states:
        state = TerraformState(name)
        state.download()


def upload_states(states):
    for name in states:
        state = TerraformState(name)
        state.upload(source='modified')


def replaceResourceInstancesAttributes(state_a,
                                       state_b,
                                       resource_filter,
                                       attribute_name,
                                       match_instances_by="index_key"):
    instances_a = state_a.getResourceInstances(query=resource_filter)
    instances_b = state_b.getResourceInstances(query=resource_filter)
    instances_b_updated = []

    if len(instances_a) == len(instances_b):
        for instance_a in instances_a:

            attribute_value_a = state_a.getInstanceAttrValue(instance=instance_a,
                                                             attribute_key=attribute_name)

            for instance_b in instances_b:
                if instance_b["attributes"][match_instances_by] == instance_a["attributes"][match_instances_by]:
                    instance_b_updated = state_b.updateInstanceAttr(instance=instance_b,
                                                                    attribute_key=attribute_name,
                                                                    attribute_value=attribute_value_a)
                    instances_b_updated.append(instance_b_updated)
    return instances_b_updated


def main() -> None:
    """
    This function performs the Terraform resources swapping between Terraform states
    :return: None
    """

    states, dry_run = arg_parser()
    download_states(states)

    ###############
    state_a = TerraformState(filename=states[0])
    state_b = TerraformState(filename=states[1])

    a_broker_listeners = state_a.getByQuery({"name": "nlb_broker_listeners"})
    a_service_listeners = state_a.getByQuery({"name": "nlb_service_listeners"})
    a_broker_certificate = state_a.getByQuery({"name": "nlb_certificate"})
    a_acm_certificate_validation = state_a.getByQuery(
        query={"name": "nlb_certificate_validation", "type": "aws_acm_certificate_validation"})
    a_route53_certificate_validation = state_a.getByQuery(
        query={"name": "nlb_certificate_validation", "type": "aws_route53_record"})
    a_nlb_domain = state_a.getByQuery({"name": "nlb_domain"})
    a_nlb_service = state_a.getByQuery({"name": "nlb_service"})
    a_nlb = state_a.getByQuery({"name": "nlb"})

    state_b.deleteByQuery({"name": "nlb_broker_listeners"})
    state_b.deleteByQuery({"name": "nlb_service_listeners"})
    state_b.deleteByQuery({"name": "nlb_certificate"})
    state_b.deleteByQuery(query={"name": "nlb_certificate_validation", "type": "aws_acm_certificate_validation"})
    state_b.deleteByQuery(query={"name": "nlb_certificate_validation", "type": "aws_route53_record"})
    state_b.deleteByQuery({"name": "nlb_domain"})
    state_b.deleteByQuery({"name": "nlb_service"})
    state_b.deleteByQuery({"name": "nlb"})

    state_b.addResource(a_broker_listeners[0])
    state_b.addResource(a_service_listeners[0])
    state_b.addResource(a_broker_certificate[0])
    state_b.addResource(a_acm_certificate_validation[0])
    state_b.addResource(a_route53_certificate_validation[0])
    state_b.addResource(a_nlb_domain[0])
    state_b.addResource(a_nlb_service[0])
    state_b.addResource(a_nlb[0])

    state_b.save(dst="modified")
    if not dry_run:
        state_b.upload(source="modified")


if __name__ == '__main__':
    import logging.config

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
