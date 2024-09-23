# Fast LLM API

Quick repo to ship LLM APIs via FastAPI, ECS, ECR

## a. Docker -> ECR

### 1. Install AWS CLI

Ensure you have the AWS CLI installed and configured. If not, install it by following this guide.

Configure the AWS CLI with your credentials:

```bash
aws configure
```

You'll need your AWS Access Key ID, Secret Access Key, and region.

### 2. Authenticate Docker to AWS ECR
Use the AWS CLI to authenticate Docker to your ECR registry. Replace aws-region with your region:

```bash
aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com
```

Replace:

```
<aws-region> with your AWS region (e.g., us-east-1)
<aws-account-id> with your 12-digit AWS account ID
```

### 3. Build & Tag Your Docker Image
```bash
sudo docker build --platform linux/amd64 -t fast_llm_api .  
```

The `--platform linux/amd64` is necessary especailly for mac users. Without this command, the docker image gets built in, let's say, a Mac environment, the results of which will not run in a typical AWS server environment.

Tag Docker image:

```bash
docker tag <local-image-name>:<tag> <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/<your-repo-name>:<tag>

```

```bash
docker tag fast_llm_api:latest 696651694142.dkr.ecr.ap-northeast-2.amazonaws.com/theta-one/fast-llm:latest
```

### 4. Build & Tag Your Docker Image

```bash
docker push <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/<your-repo-name>:<tag>
```

```bash
docker push 696651694142.dkr.ecr.ap-northeast-2.amazonaws.com/theta-one/fast-llm
```