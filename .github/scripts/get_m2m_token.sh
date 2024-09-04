set -e

export SECRET_ARN=$PROD_M2M_SECRET_ARN
if [ "$IS_DEV" = "true" ]; then
    SECRET_ARN=$NIGHTLY_M2M_SECRET_ARN
    aws codeartifact login --tool pip --domain classiq-cadmium --repository Pypi-Classiq-Non-Prod
fi

aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" | \
jq '{"classiqTokenAccount": .SecretString | fromjson | .access_token }' > "${HOME}/.classiq-credentials"
