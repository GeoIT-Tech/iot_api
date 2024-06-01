import os

from .base_config import BaseConfig

env = os.getenv('ASCEND_ENV', 'dev')
if env == 'local':
    from .local_config import Configuration
if env == 'dev':
    from .dev_config import Configuration