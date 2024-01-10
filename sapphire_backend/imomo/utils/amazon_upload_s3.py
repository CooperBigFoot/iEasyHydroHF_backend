import os

import boto
from boto import s3


def main():
    conn = boto.connect_s3()
    bucket = conn.get_bucket("kg.imomo")
    bucket_location = bucket.get_location()
    conn = boto.s3.connect_to_region(bucket_location)
    bucket = conn.get_bucket("kg.imomo")
    path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir, "webapp", "dist", "ru"))
    for root, dirs, files in os.walk(path):
        for file_name in files:
            key = s3.key.Key(bucket)
            key.key = os.path.relpath(os.path.join(root, file_name), path)
            key.set_contents_from_filename(os.path.join(root, file_name))


if __name__ == "__main__":
    main()
