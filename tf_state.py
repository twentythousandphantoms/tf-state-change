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

# from tf_resource import TerraformResource

logger = logging.getLogger(__name__)


class TerraformState:

    def __init__(self, filename):
        """
        Init the Terraform State object

        :param name: The secret name
        """

        self.name = filename
        self.s3_resource = boto3.resource('s3', region_name='us-east-1')
        self.s3_bucket = self.s3_resource.Bucket('20210324-jarvis-platform-dev-states')
        self.dl_prefix = 'downloads'
        self.object = 'jarvis-nonprod'
        self.file = os.path.join(self.dl_prefix, self.object, self.name)
        self.dict = None
        self.tmp_file = None
        # self.resource = TerraformResource(name="nlb_service_listeners", state_dict=self.dict)

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

    def from_file(self):
        with(open(self.file, 'r', encoding='ASCII')) as file:
            logger.info(f'Working with the file {self.file}')
            self.dict = json.load(file)
        return self.dict

    def create_tmp_file(self):
        tmp_file = f'{self.file}.tmp.json'
        if not os.path.exists(tmp_file):
            shutil.copyfile(self.file, tmp_file)
            logger.info(f'The file is copied to {tmp_file}')

        with(open(tmp_file, 'r')) as file:
            logger.info(f'Working with the file {tmp_file}')
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
        logger.info(f'The file is copied to {path}')
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
                result.append(resource)
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
                # TODO: save the deleted resources to "deleted" directory. Just in case...
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
            logger.info(f'No resources found by query: {query}')
