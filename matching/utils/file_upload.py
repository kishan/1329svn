
import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from django.conf import settings

import boto3


def upload_fileobj_sync(in_mem_file, match_unique_id):

    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        endpoint_url='https://s3.filebase.com'
    )

    bucket_name = '1329svn'
    key = f"{match_unique_id}.gif"

    response = s3_client.upload_fileobj(
        in_mem_file,
        bucket_name,
        key,
        ExtraArgs={
            'ACL': 'public-read'
        }
    )

    s3_resource = boto3.resource('s3')
    url = f"https://1329svn.s3.filebase.com/{key}"
    return url




