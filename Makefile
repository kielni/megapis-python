build:
	docker build --platform linux/amd64 -t megapis:local .

# 	--env max_sources=10 \

run:
	aws sts get-session-token | jq -r '.Credentials | ["AWS_ACCESS_KEY_ID=" + .AccessKeyId, "AWS_SECRET_ACCESS_KEY=" + .SecretAccessKey, "AWS_SESSION_TOKEN=" + .SessionToken] | .[]' > session.env
	docker run -p 9000:8080 --platform linux/amd64 \
	--name megapis \
	--rm \
	--env bucket=megapis \
	--env base_url=http://megapis.s3.amazonaws.com \
	--env keys=kimberly \
	--env transform=json \
	--env LAMBDA_TIMEOUT_MS=600000 \
	--env LAMBDA_TIMEOUT_MS=600000 \
	--env-file session.env \
	megapis:local "lambda.rss_refresh"

test:
	curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

push:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com
	docker tag megapis:local $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/megapis:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/megapis:latest

