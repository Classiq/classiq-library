#!/bin/bash
set -e

export SECRET_ARN=$M2M_SECRET_ARN
if [ "$IS_DEV" = "true" ]; then
    aws codeartifact login --tool pip --domain classiq-cadmium --repository Pypi-Classiq-Non-Prod
fi

aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" | \
jq '{"classiqTokenAccount": .SecretString | fromjson | .access_token }' > "${HOME}/.classiq-credentials"
