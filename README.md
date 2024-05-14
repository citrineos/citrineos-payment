# Configuration
Main important config keys which can be set via ENV Variables:

## CitrineOS REST API URL
CITRINEOS_REST_API_REMOTE_START="http://localhost:8080/ocpp/evdriver/requestStartTransaction"

## API URL which will be used by the frontend application
CLIENT_API_URL="http://localhost:9010/api"

# Message Broker (RabbitMQ)
## Protocol of the Message Broker [amqp / amqps] (required)
MESSAGE_BROKER_SSL_ACTIVE=False

## Host of the Message Broker (required)
MESSAGE_BROKER_HOST="127.0.0.1"

## Port of the Message Broker (required)
MESSAGE_BROKER_PORT=5672

## User of the Message Broker (required)
MESSAGE_BROKER_USER="guest"

## Password of the Message Broker (required)
MESSAGE_BROKER_PASSWORD="guest"

## Vhost of the Message Broker (required)
MESSAGE_BROKER_VHOST="/"

## Exchange type to be used for the Message Broker (deafult: topic)
MESSAGE_BROKER_EXCHANGE_TYPE="headers"

## Exchange name to be used for the Message Broker (required)
MESSAGE_BROKER_EXCHANGE_NAME="citrineos"

## The name of the queue where this service will listen for events to be processed, e.g. when a TransactionEvent was received. (required)
MESSAGE_BROKER_EVENT_CONSUMER_QUEUE_NAME="paymentService"

# Webserver Settings (api used by the frontend)
## Host of the web server (required)
WEBSERVER_HOST="0.0.0.0"

## Port of the web server (required)
WEBSERVER_PORT=9010

## Path which will be used as web routes prefix (e.g. "/path") [""]
WEBSERVER_PATH="/api"

## Database settings (required)
DB_HOST="127.0.0.1"
DB_PORT=5432
DB_DATABASE="citrine"
DB_USER="citrine"
DB_PASSWORD="citrine"
DB_TABLE_PREFIX="payment_"

# Stripe settings
## Stripe API Key (required)
(container contains Stackbox' test api key)
STRIPE_API_KEY="sk_test_some-stripe-api-key"

## Stripe endpoint secrect for receiving webhooks from Stripe for endpoint-type "Account" (required)
(Webhook needs to be configured with stripe and given secret needs to be used)
STRIPE_ENDPOINT_SECRET_ACCOUNT="whsec_some-stripe-signing-secret"

## Stripe endpoint secrect for receiving webhooks from Stripe for endpoint-type "Connect" (required)
(Webhook needs to be configured with stripe and given secret needs to be used)
STRIPE_ENDPOINT_SECRET_CONNECT="whsec_some-stripe-signing-secret"
