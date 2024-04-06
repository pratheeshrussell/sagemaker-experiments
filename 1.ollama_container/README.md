# Ollama in Sagemaker

> Refer: [Deploying custom models on AWS Sagemaker using FastAPI](https://sii.pl/blog/en/deploying-custom-models-on-aws-sagemaker-using-fastapi/)

## Local Testing
Build the model
```
docker build . -t ollama-sagemaker
docker run -d --name ollamaDeployTest ollama-sagemaker 
```

Use curl to test the endpoints
For example  
```
curl http://localhost:8080/invocations \
    -H "Content-Type: application/json" \
    -d '{
        "action":"chat-completion",
        "data":{
            "model": "gemma:2b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        }
    }'
```

```
curl http://localhost:8080/invocations -d '{
    "action":"generate",
    "data":{
        "model": "gemma:2b",
        "prompt": "Why is the sky blue?"
    }
    }'
```
```
curl http://localhost:8080/invocations -d '{
    "action":"pullmodel",
    "data":{
        "model_source":"ollama",
        "model_name":"phi"
        }
    }'
```
```
curl http://localhost:8080/invocations -d '{
    "action":"list",
    "data":{}
}'

```

## Running on AWS Sagemaker
### Push the image to ECR
* Create the registry in ECR  
I will be calling it **ollama-sagemaker**   
You will get a name like xxxxxxxxxxxx.dkr.ecr.ap-south-1.amazonaws.com/ollama-sagemaker

* Set access key details in aws cli(This is a one time process)  
```
aws configure
```

* login to ecr repo with docker(this expires frequently you may have to relogin again after a while)
```
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin xxxxxxxxxxxx.dkr.ecr.ap-south-1.amazonaws.com
```
* Build the image  
```
docker build -t ollama-sagemaker .

docker tag ollama-sagemaker:latest xxxxxxxxxxxx.dkr.ecr.ap-south-1.amazonaws.com/ollama-sagemaker:latest
```

* Push the image to ECR repo  

```
docker push XXXXXXXXXX.dkr.ecr.ap-south-1.amazonaws.com/ollama-sagemaker:latest
```

### Create Sagemaker Model
* goto sagemaker service --> Inference --> Models  
* click on "Create Model"   
* paste the ECR Image URI under "Location of inference code image"   
* You can optionally set the environment variable **OLLAMA_MODEL** and set it to any value that can be directly pulled with the *ollama pull* command. If this is not set the gemma:2b will be pulled by default  
* Finally click on 'Create Model' button  

### Create Sagemaker Endpoint Configurations
* goto sagemaker service --> Inference --> Endpoint configurations  
* click on button to create endpoint config  
* Under Variants click on "Create Production Variant". select the model we created  
* you can edit the variant if you need to change instance type  
* finally create the configuration  

### Create Sagemaker Endpoint
* goto sagemaker service --> Inference --> Endpoints  
* click on button to create endpoint  
* Select the endpoint configuration from list and click on the button to select that config  
* create the endpoint  

## Allowed Env Vars
```
OLLAMA_MODEL=phi
```

## Inferencing
```
import boto3
import sagemaker

import json

sagemaker_runtime = boto3.client('sagemaker-runtime',
    region_name = aws_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key)

test_input = {
        "action":"chat-completion",
        "data":{
            "model": "gemma:2b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        }
    }


payload = json.dumps(test_input)

response = sagemaker_runtime.invoke_endpoint(EndpointName=endpoint_name,
                                         ContentType='application/json',
                                         Body=payload)

result = json.loads(response["Body"].read().decode())
print(result)
```


## REFER:
1. https://sii.pl/blog/en/deploying-custom-models-on-aws-sagemaker-using-fastapi/   
2. https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html#your-algorithms-inference-algo-ping-requests  
