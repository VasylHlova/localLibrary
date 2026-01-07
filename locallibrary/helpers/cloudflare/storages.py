from storages.backends.s3 import S3Storage

import helpers.storages.mixins as mixins


class CloudflareStorage(S3Storage):
    pass


class StaticFileStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For staticfiles
    """

    location = "static"
    default_acl = "public-read"


class MediaFileStorage(mixins.DefaultACLMixin, CloudflareStorage):
    """
    For general uploads
    """

    location = "media"
    default_acl = "public-read"