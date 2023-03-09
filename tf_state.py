"""
Represents and stores information about Terraform State
"""
import json
import os
import shutil
from collections.abc import Mapping
from typing import Dict, Any, List, Callable

import boto3
import botocore

import logging

from state_errors import SchemaError, DataNotFoundError

logger = logging.getLogger(__name__)


class TerraformState:

    def __init__(self, filename, region, env="nonprod"):
        """
        Init the Terraform State object

        :param name: The secret name
        """

        self.name = filename
        self.s3_resource = boto3.resource('s3', region_name='us-east-1')
        self.dl_prefix = 'downloads'
        self.file = os.path.join(self.dl_prefix, self.object, self.name)
        self.dict = None
        self.tmp_file = None

        if env == "nonprod":
            self.s3_bucket = self.s3_resource.Bucket('20210324-jarvis-platform-dev-states')
            self.object = 'jarvis-nonprod'
        elif env == "prod":
            self.s3_bucket = self.s3_resource.Bucket('20210517-jarvis-platform-prod-states')
            self.object = 'jarvis-prod'

    def create_folder(self, name: str) -> True:
        """
        Prepares a folder to where the files are being downloaded to.
        The folder name is same is the S3 object name

        :return: None
        """

        full_path = os.path.join(name, self.object)
        if not os.path.exists(full_path):
            try:
                os.mkdir(name)
                os.mkdir(full_path)
                logger.info(f'The directory {full_path} is created')
            except OSError:
                raise
        else:
            logger.info(f'The directory {full_path} exists')
        return name

    def load(self):
        self.dict = self.from_file()

    def from_file(self):
        with(open(self.file, 'r', encoding='ASCII')) as file:
            logger.debug(f'Working with the file {self.file}')
            self.dict = json.load(file)
        return self.dict

    def create_tmp_file(self):
        tmp_file = f'{self.file}.tmp.json'
        if not os.path.exists(tmp_file):
            shutil.copyfile(self.file, tmp_file)
            logger.info(f'The file is copied to {tmp_file}')

        with(open(tmp_file, 'r')) as file:
            logger.debug(f'Working with the file {tmp_file}')
            self.dict = json.load(file)

        return tmp_file

    def download(self):
        """
        Downloads the files from an S3. Saves the downloaded file into the specified folder ("downloads") or raises error

        :return: Path to the downloaded file

        """
        prefix = self.create_folder(name=self.dl_prefix)  # create a folder where to store the Terraform State
        try:
            path = f'{self.object}/{self.name}'
            self.s3_bucket.download_file(Key=path, Filename=f'{prefix}/{path}')
            self.file = os.path.join(prefix, path)
            logger.info(f'{path}: Downloaded')
            return path
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                logger.error(self.name + ": The object does not exist.")
            elif e.response['Error']['Code'] == "400":
                logger.error(f'Unauthorized')
                exit(1)
            else:
                raise

    def upload(self, source='modified'):
        """Upload a file to an S3 bucket

        :param source: The folder from where upload to
        :return: True if file was uploaded, else False
        """
        try:
            path = f'{self.object}/{self.name}'
            self.s3_bucket.upload_file(Filename=f'{source}/{path}', Key=path)
            logger.info(f'{path}: Uploaded')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "400":
                logger.error(f'Unauthorized')
                return False
            else:
                logger.error(e.response['Error'])
                raise
        return True

    def save(self, dst='modified', rm_tmp=True):
        """Copies the tmp_file to the destination directory and
        If dst already exists, it will be replaced.
        :param rm_tmp: removes the tmp_file (<state_file>.tmp.json). Default: True
        :param dst: The folder where save the sate file to
        :return: True if file was saved
        """

        prefix = self.create_folder(dst)
        path = os.path.join(prefix, self.object, self.name)
        shutil.copyfile(src=self.tmp_file, dst=path)
        logger.info(f'The state is saved to {path}')
        if rm_tmp:
            os.remove(self.tmp_file)
        return True

    @staticmethod
    def inplace_change(state_file):
        with open(state_file) as f:
            s = f.read()

        with open(state_file, 'w') as f:
            s = s.replace("<", "\\u003c")
            s = s.replace(">", "\\u003e")
            s = s.replace("&", "\\u0026")
            f.write(s)

    def getByQuery(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.dict = self.from_file()
        result = []
        for resource in self.dict['resources']:
            if all(x in resource and resource[x] == query[x] for x in query):
                logger.info(f'Found the {query} in {self.name}')
                result.append(resource)

        if not result:
            raise DataNotFoundError(query)
        return result

    def addResource(self, new_data: Dict[str, Any]) -> dict:
        self.tmp_file = self.create_tmp_file()
        with open(self.tmp_file, "w", encoding='utf-8') as state_file:
            logger.info("Append new data; {0}".format(new_data))
            self.dict["resources"].append(new_data)
            json.dump(self.dict, state_file, indent=2)
        self.inplace_change(self.tmp_file)
        return self.dict

    def deleteByQuery(self, query: Dict[str, Any]) -> list:
        self.dict = self.from_file()
        found, result = [], []
        for resource in self.dict["resources"]:
            if all(x in resource and resource[x] == query[x] for x in query):
                found.append(resource)
            else:
                result.append(resource)

        if len(found) > 0:
            self.tmp_file = self.create_tmp_file()
            with open(self.tmp_file, "w", encoding='utf-8') as state_file:
                logger.info(f'Delete resources: \n {found}')
                self.dict["resources"] = result
                json.dump(self.dict, state_file, indent=2)
            return found
        else:
            raise DataNotFoundError(query)

    def getResourceInstances(self, query: Dict[str, Any]) -> list:
        result = []
        # self.printDict(self.dict['resources'])
        logger.debug(f'Query: {query}')
        logger.debug(dir(self.dict['resources']))
        logger.debug(type(self.dict['resources']))
        counter = 0
        for resource in self.dict['resources']:
            counter = counter + 1
            logger.debug(f"test {counter}")
            if all(x in resource and resource[x] == query[x] for x in query):
                logger.debug(f"found the {query}!")
                result.append(resource["instances"])
        if len(result[0]) < 1:
            logger.error(f'Did not found such a resource: {query}')
        return result[0]

    @staticmethod
    def printDict(d: Dict):
        print(json.dumps(d, indent=2))

    @staticmethod
    def getInstanceAttrValue(instance: Dict[str, Any], attribute_key: str):
        attr_value = instance["attributes"].get(attribute_key)
        return attr_value

    @staticmethod
    def rmInstanceAttr(instance: Dict[str, Any], attribute_key: str) -> Dict[str, Any]:
        attr_dict = instance.get("attributes")

        if attribute_key in attr_dict.keys():
            attr_dict.pop(attribute_key)
            logger.debug(f'Instance: {instance.get("index_key")} - Delete attribute by key: {attribute_key}')
        else:
            logger.info(f'No attributes found by attribute_key: {attribute_key} in instance {instance}')

        instance.pop("attributes")
        instance["attributes"] = attr_dict

        return instance

    @staticmethod
    def addInstanceAttr(instance: Dict[str, Any], attribute_key: str, attribute_value):
        instance["attributes"].update({attribute_key: attribute_value})
        logger.debug(f'Instance: {instance.get("index_key")} - Add new attribute {attribute_key}')
        return instance

    def updateInstanceAttr(self, instance: Dict[str, Any], attribute_key: str, attribute_value: Dict[str, Any]) -> \
            Dict[str, Any]:
        instance_after_attr_removal = self.rmInstanceAttr(instance=instance,
                                                          attribute_key=attribute_key)

        instance_with_attr_updated = self.addInstanceAttr(instance=instance_after_attr_removal,
                                                          attribute_key=attribute_key,
                                                          attribute_value=attribute_value)
        return instance_with_attr_updated

    def updateByQuery(self, query: Dict[str, Any], new_resource=None, new_instances=None) -> bool:
        result = []
        found = False

        for resource in self.dict["resources"]:
            if all(x in resource and resource[x] == query[x] for x in query):
                found = True
                if new_resource:
                    if set(new_resource.keys()).issubset(resource.keys()):
                        result.append(new_resource)
                        logger.info(f'The resource {query} is replaced in {self.name}')
                        logger.debug(f'The resource {query} is replaced in {self.name} by: {new_resource}')
                    else:
                        raise SchemaError(
                            "original resource keys: " + ",".join(sorted(list(resource.keys()))),
                            "new_resource keys: "
                            + ",".join(sorted(list(new_resource.keys()))),
                        )
                if new_instances:
                    resource["instances"] = new_instances
                    result.append(resource)
                    logger.info(f'The resource {query} is updated with the instances: {new_instances}')
            else:
                result.append(resource)
        if not found:
            logger.error(
                f'There is no resource matching the given filter {query} in the state {self.name},'
                f' hence it is not updated')
            exit(1)
        else:
            self.tmp_file = self.create_tmp_file()
            with open(self.tmp_file, "w", encoding='utf-8') as state_file:
                self.dict["resources"] = result
                json.dump(self.dict, state_file, indent=2)
            self.inplace_change(self.tmp_file)
        return found
