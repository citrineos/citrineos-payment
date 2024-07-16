import os
from typing import get_type_hints, Union
from dotenv import load_dotenv

class AppConfigError(Exception):
    pass

def _parse_bool(val: Union[str, bool]) -> bool:  # pylint: disable=E1136 
    return val if type(val) == bool else val.lower() in ['true', 'yes', '1']

# AppConfig class with required fields, default values, type checking, and typecasting for int and bool values
class AppConfig:
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    OPENAPI_TITLE: str = "Stackbox Payment API"
    MESSAGE_BROKER_SSL_ACTIVE: bool
    MESSAGE_BROKER_HOST: str
    MESSAGE_BROKER_PORT: int    
    MESSAGE_BROKER_USER: str
    MESSAGE_BROKER_PASSWORD: str 
    MESSAGE_BROKER_VHOST: str
    MESSAGE_BROKER_EXCHANGE_TYPE: str = "topic"
    MESSAGE_BROKER_EXCHANGE_NAME: str
    MESSAGE_BROKER_EVENT_CONSUMER_QUEUE_NAME: str
    WEBSERVER_HOST: str
    WEBSERVER_PORT: int
    WEBSERVER_PATH: str
    DB_HOST: str
    DB_PORT: int
    DB_DATABASE: str
    DB_USER: str
    DB_PASSWORD: str
    DB_TABLE_PREFIX: str
    STRIPE_API_KEY: str
    STRIPE_ENDPOINT_SECRET_ACCOUNT: str
    STRIPE_ENDPOINT_SECRET_CONNECT: str
    AMPAY_DEFAULT_FEE: float
    AMPAY_COUNTRY_CODE_FOR_ADDING_TAX: str
    AMPAY_ADDING_TAX_RATE: int
    MESSAGE_BROKER_OCPP_QUEUE_PREFIX: str
    OCPP_REMOTESTART_IDTAG_PREFIX: str
    AMPAY_RECEIPT_BASE_URL: str
    CITRINEOS_MESSAGE_API_URL: str
    CITRINEOS_DATA_API_URL: str
    CITRINEOS_SCAN_AND_CHARGE: bool
    CITRINEOS_DIRECTUS_URL: str
    CITRINEOS_DIRECTUS_LOGIN_EMAIL: str
    CITRINEOS_DIRECTUS_LOGIN_PASSWORD: str
    CITRINEOS_DIRECTUS_QR_CODE_FOLDER: str
    CLIENT_URL: str


    """
    Map environment variables to class fields according to these rules:
      - Field won't be parsed unless it has a type annotation
      - Field will be skipped if not in all caps
      - Class field and environment variable name are the same
    """
    def __init__(self, env):
        ENV_FILE = ".env"
        if(env.get('CONFIG_PATH') is not None):
            ENV_FILE = env.get('CONFIG_PATH')
        load_dotenv(dotenv_path=ENV_FILE)

        for field in self.__annotations__:
            if not field.isupper():
                continue

            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError('The {} field is required'.format(field))

            # Cast env var value to expected type and raise AppConfigError on failure
            try:
                var_type = get_type_hints(AppConfig)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise AppConfigError('Unable to cast value of "{}" to type "{}" for "{}" field'.format(
                    env[field],
                    var_type,
                    field
                )
            )

    def __repr__(self):
        return str(self.__dict__)

# Expose Config object for app to import


Config = AppConfig(os.environ)
