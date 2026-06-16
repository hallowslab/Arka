FROM rabbitmq:4

# Copy your production config
COPY docker/rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

RUN rabbitmq-plugins enable --offline \
    rabbitmq_prometheus

# Optional: load definitions
#COPY docker/rabbitmq/definitions.json /etc/rabbitmq/definitions.json