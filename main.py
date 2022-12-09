"""
Main TFStateResourceSwapper script.
"""
import sys
import argparse

# from tf_resource import TerraformResource
from tf_state import TerraformState


# bucket_name = 20210324-jarvis-platform-dev-states
# object_name = jarvis-nonprod

def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--states', nargs='+', help='List of state files to work with', required=True)
    args = parser.parse_args()
    return args.states


def download_states(states):
    for name in states:
        state = TerraformState(name)
        state.download()


def upload_states(states):
    for name in states:
        state = TerraformState(name)
        state.upload(source='modified')


def main() -> None:
    """
    This function performs the Terraform resources swapping between Terraform states
    :return: None
    """

    states = arg_parser()
    download_states(states)

    ###############
    state_a = TerraformState(filename=states[0])
    state_b = TerraformState(filename=states[1])

    a_broker_listeners = state_a.getByQuery({"name": "nlb_broker_listeners"})
    a_service_listeners = state_a.getByQuery({"name": "nlb_service_listeners"})
    a_broker_certificate = state_a.getByQuery({"name": "nlb_certificate"})
    a_acm_certificate_validation = state_a.getByQuery(query={"name": "nlb_certificate_validation", "type": "aws_acm_certificate_validation"})
    a_route53_certificate_validation = state_a.getByQuery(query={"name": "nlb_certificate_validation", "type": "aws_route53_record"})
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
    # state_b.upload(source="modified")
    ############

    ## tests:
    # state.create_tmp_file()
    # resource = TerraformResource(name="nlb", state_dict=state.load_file())
    # nlb_a = resource.get()
    # resource = state.TerraformResource(name="nlb", state_dict=state.dict)

    # resource = state.getByQuery({"name": "cruisecontrol_configmap"})
    # print(resource)
    # state.create_tmp_file()
    # state.addResource(new_data=resource[0])

    # resource = state.getByQuery({"name": "nlb"})
    # print(resource)

    # resource.print()
    # resource.remove()

    # state = resource.remove()
    # state.resource(name="nlb").print()
    # state.resource.print()


if __name__ == '__main__':
    import logging.config

    # Setting up Logger

    # logging.config.fileConfig('/path/to/logging.conf')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
