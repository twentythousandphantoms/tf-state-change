"""
Represents and stores information about Terraform Resource

Not used, To be Deleted...
"""
import json
import logging

logger = logging.getLogger(__name__)


class TerraformResource:

    def __init__(self, name, state_dict):
        """
        Init the terraform resource
        :param name: str
        :param state_dict: dict
        """

        self.name = name
        self.state_dict = state_dict

    def __call__(self, name):
        return self

    def print(self):
        print(type(self.get()))
        print(json.dumps(self.get(), indent=2))

    def get(self):
        # nlb_broker_listeners A->B
        # nlb_service_listeners A->B
        #
        print(type(self.state_dict['resources']))
        for resource in self.state_dict['resources']:
            for key, value in resource.items():
                if key == "name" and value == self.name:
                    return resource

    def remove(self, res_name="nlb_service"):
        pass

    def put(self, resource):
        """
        Put a given resource into a state
        :param resource: dict
        :return:
        """
        pass

    def patch_resource(self):
        # modify - listener "nlb_service_listeners" with the B's target groups
        pass
