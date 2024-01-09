# -*- encoding: UTF-8 -*-
import base64
import datetime
import hashlib
import hmac

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import *
import pytz

from imomo import config

"""MONKEY PATCH

This is to make things work in Python >= 2.7.9,

See: https://github.com/boto/boto/issues/2836
"""
import ssl

if hasattr(ssl, 'match_hostname'):
    _old_match_hostname = ssl.match_hostname

    def _new_match_hostname(cert, hostname):
        if hostname.endswith('.s3.amazonaws.com'):
            pos = hostname.find('.s3.amazonaws.com')
            hostname = hostname[:pos].replace('.', '') + hostname[pos:]
        elif hostname.endswith('.s3.eu-central-1.amazonaws.com'):
            pos = hostname.find('.s3.eu-central-1.amazonaws.com')
            hostname = hostname[:pos].replace('.', '') + hostname[pos:]
        return _old_match_hostname(cert, hostname)

    ssl.match_hostname = _new_match_hostname


def get_key_name(source_id, user_id, historical_data_filename):
    return u'{source_id}/{user_id}/{historical_data_filename}'.format(
        source_id=source_id,
        user_id=user_id,
        historical_data_filename=historical_data_filename,
    )


def get_bulk_key(source_id, file_name):
    return u'{source_id}/bulk_data/{file_name}'.format(
        source_id=source_id,
        file_name=file_name,
    )


def get_snow_data_key_name(source_id, user_id, filename):
    return u'{source_id}/snow_data/{user_id}/{filename}'.format(
        source_id=source_id,
        user_id=user_id,
        filename=filename,
    )


def get_forecast_bulletin_key_name(source_id, user_id, filename):
    return u'{source_id}/forecast_bulletins/{user_id}/{filename}'.format(
        source_id=source_id,
        user_id=user_id,
        filename=filename,
    )


def get_forecasting_key_name(source_id, site_id, filename):
    return u'{source_id}/forecasting/{site_id}/{filename}'.format(
        source_id=source_id,
        site_id=site_id,
        filename=filename,
    )


def get_key(key_name, file_object):
    """Retrieve a key from S3 and store it in the given file-like object.

    Note that the configuration of region, bucket and keys is retrieved from
    the standard secrets file.

    Args:
        key_name: The key to retrieve.
        file_object: File-like object where the downloaded file will be loaded.
    """
    secrets = config.get_secrets()
    if secrets.AWS_UPLOAD_REGION == 'eu-central-1':
        s3_conn = S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY,
            host='s3.eu-central-1.amazonaws.com')
    else:
        s3_conn = S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY)
    bucket = s3_conn.get_bucket(secrets.AWS_UPLOAD_BUCKET)
    key = Key(bucket=bucket, name=key_name)
    key.get_contents_to_file(fp=file_object)


def get_signed_url_for_upload(key_name, duration=1800):
    """Proxy method for retrieving a signed URL to use for uploads to an S3
    bucket. The bucket and region are configured through the secrets file.

    This doesn't test the existence of the bucket or attempts to create it
    if it doesn't exist.

    Args:
        key_name: The desired name for the key in the bucket.
        duration: Duration of the link's validity.
    Raises:
        Any AWS error that may occur.
    """
    secrets = config.get_secrets()
    if secrets.AWS_UPLOAD_REGION == 'eu-central-1':
        s3_conn = S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY,
            host='s3.eu-central-1.amazonaws.com')
    else:
        s3_conn = S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY)
    bucket = s3_conn.get_bucket(secrets.AWS_UPLOAD_BUCKET)
    key = Key(bucket=bucket, name=key_name)
    return key.generate_url(expires_in=duration, method='PUT')


def get_form_data_for_upload(key_prefix):
    """Constructs a policy object and signature that can be used for a POST
    upload of files to a S3 bucket owned by the application.

    See these links for details on the construction of the form data:

    * http://goo.gl/y6ttWS
    * http://goo.gl/Cfy8tm

    Args:
        key_prefix: The condition of what should be the prefix of the key.
    """
    date = datetime.date.today()
    datestamp = date.strftime('%Y%m%d')
    long_datestamp = date.strftime('%Y%m%dT000000Z')
    service = 's3'
    secrets = config.get_secrets()
    region = secrets.AWS_UPLOAD_REGION
    bucket = secrets.AWS_UPLOAD_BUCKET
    access_key = secrets.AWS_ACCESS_KEY_ID

    policy_string = build_policy(key_prefix)
    signing_key = calculate_signing_key()
    signature = _sign(signing_key, policy_string, hex=True)
    fields = {
        'acl': 'private',
        'bucket': bucket,
        'x-amz-date': long_datestamp,
        'x-amz-algorithm': 'AWS4-HMAC-SHA256',
        'x-amz-signature': signature,
        'x-amz-credential': '%s/%s/%s/%s/aws4_request' % (access_key,
                                                          datestamp,
                                                          region, service),
        'policy': policy_string,
        'key': key_prefix
    }
    url = 'https://s3.%s.amazonaws.com/%s' % (region, bucket)
    return {'action': url, 'fields': fields}


def build_policy(key_prefix, service='s3',
                 expires_in=3600, max_content_length=None,
                 acl='private', content_type_prefix=''):
    """Build a policy string according to the Amazon AWS guidelines.

    The details are available in: http://goo.gl/2hDBJG

    Args:
        key_prefix: The prefix for the key which will be uploaded.
        access_key: The access key ID.
        service: The service to be used, defaults to s3.
        expires_in: Expiration period for the security policy, in seconds.
        max_content_length: Limit to the upload size.
        acl: The access control level.
        content_type_prefix: Prefix for the admitted content types.
    """
    date = datetime.date.today()
    datestamp = date.strftime('%Y%m%d')
    long_datestamp = date.strftime('%Y%m%dT000000Z')
    expires_absolute = (datetime.datetime.now(tz=pytz.utc) +
                        datetime.timedelta(seconds=expires_in)).strftime(
                        '%Y-%m-%dT%H:%M:%S.%fZ')

    secrets = config.get_secrets()
    region = secrets.AWS_UPLOAD_REGION
    access_key = secrets.AWS_ACCESS_KEY_ID
    bucket = secrets.AWS_UPLOAD_BUCKET

    conditions = []
    key = '["starts-with", "$key", "%s"]'
    conditions.append(key % key_prefix)
    bucket_cond = '{"bucket": "%s"}'
    conditions.append(bucket_cond % bucket)
    acl_cond = '{"acl": "%s"}'
    conditions.append(acl_cond % acl)
    if content_type_prefix:
        content_type = '["starts-with", "$Content-Type", "%s"]'
        conditions.append(content_type % content_type_prefix)
    if max_content_length:
        content_length = '["content-length-range", 0, %s]'
        conditions.append(content_length % max_content_length)

    x_amz_algorithm = '{"x-amz-algorithm": "AWS4-HMAC-SHA256"}'
    conditions.append(x_amz_algorithm)
    x_amz_credential = '{"x-amz-credential": "%s/%s/%s/%s/aws4_request"}'
    conditions.append(x_amz_credential % (access_key, datestamp,
                                          region, service))
    x_amz_date = '{"x-amz-date": "%s"}'
    conditions.append(x_amz_date % long_datestamp)
    conditions_string = ','.join(conditions)

    policy = """{"expiration": "%s",\n"conditions": [%s]}""" % (
        expires_absolute, conditions_string)
    return base64.b64encode(policy.encode('utf-8'))


def _sign(key, msg, hex=False):
    """Sign a message with a key according to Amazon AWS SigV4.

    See: http://goo.gl/Cnjyhf

    Args:
        key: The signing key.
        msg: The message to sign.
        hex: Indicates whether to return an hex-encoded value.
    Returns:
        The signed value.
    """
    if hex:
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def calculate_signing_key():
    """Calculate the signing key according to the AWS documentation.

    See documentation in:

    http://goo.gl/vyPmaI

    Args:
        secret_key: The AWS key to generate the signing key.
        datestamp: The date when the signature was generated,
            format is yyyymmdd.
        region: The region for which the signature is valid.
        service: The service for which the signature is valid.
    Returns:
        String to use when signing a policy encoded string.
    """
    secrets = config.get_secrets()
    secret_key = secrets.AWS_SECRET_ACCESS_KEY
    region = secrets.AWS_UPLOAD_REGION
    datestamp = datetime.date.today().strftime('%Y%m%d')
    service = 's3'

    date_key = _sign(('AWS4' + secret_key).encode('utf-8'),
                     datestamp)
    date_region_key = _sign(date_key, region)
    date_region_service_key = _sign(date_region_key, service)
    signing_key = _sign(date_region_service_key, 'aws4_request')
    return signing_key


def get_tmp_url(aws_path, expires_in=3600):
    secrets = config.get_secrets()
    s3_conn = get_s3_conn()
    bucket = s3_conn.get_bucket(secrets.AWS_UPLOAD_BUCKET)
    key = Key(bucket=bucket, name=aws_path)
    return key.generate_url(expires_in=expires_in)


def store_file(contents, filename, public=False, file_type='xlsx'):
    """Stores a file in the configured AWS bucket, the file's ACL is set to
    private but a temporary signed URL is generated to retrieve it.

    Args:
        contents: A file-like object with the contents to store, this object
            is rewound before the upload starts.
        filename: The full path of the key to store.
    Returns:
        A signed url that can be used to retrieve the file during the next
        hour.
    """
    secrets = config.get_secrets()
    s3_conn = get_s3_conn()
    bucket = s3_conn.get_bucket(secrets.AWS_UPLOAD_BUCKET)
    key = Key(bucket=bucket, name=filename)

    if file_type == 'xlsx':
        headers = {
            'Content-Type': 'application/vnd.openxmlformats-'
                            'officedocument.spreadsheetml.sheet'
        }
    else:
        headers = None

    key.set_contents_from_file(contents, rewind=True, headers=headers)

    if not public:
        return key.generate_url(expires_in=3600)
    else:
        key.make_public()
        return 'https://{host}/{bucket}/{key}'.format(
            host=s3_conn.server_name(),
            bucket=secrets.AWS_UPLOAD_BUCKET,
            key=key.key
        )


def get_s3_conn():
    secrets = config.get_secrets()
    if secrets.AWS_UPLOAD_REGION == 'eu-central-1':
        return S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY,
            host='s3.eu-central-1.amazonaws.com')
    else:
        return S3Connection(
            aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY)
