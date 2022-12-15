"""
Main TFStateResourceSwapper script.
"""
import sys
import argparse

from tf_state import TerraformState


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--states', nargs=2, help='List of state files to work with', required=True)
    parser.add_argument('--region', nargs=1, help='AWS Region', required=True)
    parser.add_argument('--dry-run', help='Run without uploading state back to S3. The changes will be saved to a new '
                                          '"modified" directory',
                        required=False, action="store_true", dest="dry_run")
    args = parser.parse_args()
    return args.states, args.region[0], args.dry_run


def download_states(states, region):
    for name in states:
        state = TerraformState(filename=name, region=region)
        state.download()


def replaceResourceInstancesAttributes(state_a,
                                       state_b,
                                       resource_filter,
                                       attribute_name,
                                       match_instances_by="index_key"):
    """
    Extracts attribute <attribute_name> from state_b
    Applies this attribute to instances of state_a resource

    :param state_a:
    :param state_b:
    :param resource_filter: (dict) The query on which the resource to select, e.g. {"name": "nlb_broker_listeners"}
    :param attribute_name: (str) The attribute name to replace, e.g. "default_action"
    :param match_instances_by: (str) The attribute for match instances from state_a and state_b
    :return: Returns the updated state_a instances
    :rtype: List[Dict]
    """
    logger.info(f'Replacing {resource_filter} instances attribute: "{attribute_name}"')
    instances_a = state_a.getResourceInstances(query=resource_filter)
    logger.debug(f'Got the instances_a: {instances_a}')
    instances_b = state_b.getResourceInstances(query=resource_filter)
    logger.debug(f'Got the instances_b: {instances_b}')
    instances_a_updated = []

    if len(instances_a) == len(instances_b):
        logger.info('So far so good')
        for instance_b in instances_b:

            attribute_value_b = state_b.getInstanceAttrValue(instance=instance_b,
                                                             attribute_key=attribute_name)
            for instance_a in instances_a:
                if instance_a["attributes"][match_instances_by] == instance_b["attributes"][match_instances_by]:
                    instance_a_updated = state_a.updateInstanceAttr(instance=instance_a,
                                                                    attribute_key=attribute_name,
                                                                    attribute_value=attribute_value_b)
                    instances_a_updated.append(instance_a_updated)
    return instances_a_updated


def main() -> None:
    """
    This function performs the Terraform resources swapping between Terraform states
    :return: None
    """

    states, region, dry_run = arg_parser()
    download_states(states=states, region=region)

    ###############
    state_a = TerraformState(filename=states[0], region=region)
    state_a.load()
    logger.info(f'The state_a is loaded.')
    logger.info(f'The state_a resources len: {len(state_a.dict["resources"])}.')
    state_b = TerraformState(filename=states[1], region=region)
    state_b.load()
    logger.info(f'The state_b is loaded.')
    logger.info(f'The state_b resources len: {len(state_b.dict["resources"])}.')

    # Get resources from state_a
    a_nlb = state_a.getByQuery({"name": "nlb"})
    a_nlb_domain = state_a.getByQuery({"name": "nlb_domain"})
    a_nlb_service = state_a.getByQuery({"name": "nlb_service"})
    a_broker_certificate = state_a.getByQuery({"name": "nlb_certificate"})
    a_route53_certificate_validation = state_a.getByQuery(
        query={"name": "nlb_certificate_validation", "type": "aws_route53_record"})
    a_acm_certificate_validation = state_a.getByQuery(
        query={"name": "nlb_certificate_validation", "type": "aws_acm_certificate_validation"})

    a_broker_listeners = state_a.getByQuery({"name": "nlb_broker_listeners"})
    a_service_listeners = state_a.getByQuery({"name": "nlb_service_listeners"})

    # Update listeners with target groups of cluster b
    a_broker_listeners[0]["instances"] = replaceResourceInstancesAttributes(state_a=state_a,
                                                                            state_b=state_b,
                                                                            resource_filter={
                                                                                "name": "nlb_broker_listeners"},
                                                                            attribute_name="default_action",
                                                                            match_instances_by="port")
    a_service_listeners[0]["instances"] = replaceResourceInstancesAttributes(state_a=state_a,
                                                                             state_b=state_b,
                                                                             resource_filter={
                                                                                 "name": "nlb_service_listeners"},
                                                                             attribute_name="default_action",
                                                                             match_instances_by="port")
    # Update resources in state_b
    state_b.updateByQuery(query={"name": "nlb"}, new_resource=a_nlb[0])
    state_b.updateByQuery(query={"name": "nlb_domain"}, new_resource=a_nlb_domain[0])
    state_b.updateByQuery(query={"name": "nlb_service"}, new_resource=a_nlb_service[0])
    state_b.updateByQuery(query={"name": "nlb_certificate"}, new_resource=a_broker_certificate[0])
    state_b.updateByQuery(query={"name": "nlb_certificate_validation", "type": "aws_route53_record"},
                          new_resource=a_route53_certificate_validation[0])
    state_b.updateByQuery(query={"name": "nlb_certificate_validation", "type": "aws_acm_certificate_validation"},
                          new_resource=a_acm_certificate_validation[0])

    state_b.updateByQuery(query={"name": "nlb_broker_listeners"},
                          new_resource=a_broker_listeners[0])
    state_b.updateByQuery(query={"name": "nlb_service_listeners"},
                          new_resource=a_service_listeners[0])

    # Apply the updated state_b
    state_b.save(dst="modified")
    if not dry_run:
        state_b.upload(source="modified")


if __name__ == '__main__':
    import logging.config

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
