import os
import json
import logging
import asyncio
import requests
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.logger import logger as fastapi_logger
from fastapi import FastAPI, Request, Response, status

# log handling - not getting anything in docker logs
# https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/issues/19#issuecomment-620810957
gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_logger = logging.getLogger("gunicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers = gunicorn_error_logger.handlers
fastapi_logger.setLevel(logging.INFO)
fastapi_logger.handlers = gunicorn_error_logger.handlers

OLLAMA_BASE_URL="http://localhost:11434"
# background_tasks = BackgroundTasks()
# https://github.com/ollama/ollama/blob/main/docs/api.md


def pull_ollama_model(modelName):
    fastapi_logger.info(f'Pulling model {modelName}')
    os.system(f'ollama pull {modelName} &')
    fastapi_logger.info(f'Pulling model {modelName} complete')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Get a default model 
    ollamaModel = os.environ.get('OLLAMA_MODEL')
    if ollamaModel:
        fastapi_logger.info(f'Env set. Default model is {ollamaModel}')
        pull_ollama_model(ollamaModel)
    else:
        fastapi_logger.info(f'Env not set. Pulling default model gemma:2b')
        pull_ollama_model('gemma:2b')
    yield
 
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=['*'],
    allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.get('/ping')
async def ping_get():
    headers = {'access-control-allow-origin': '*', 'vary':'origin, access-control-request-method, access-control-request-headers'}
    return Response(status_code=status.HTTP_200_OK, headers=headers)


async def post_ollama_generation_handler(request_body_dict):
    infer_url=f"{OLLAMA_BASE_URL}/api/generate"
    # Don't stream response
    request_body_dict['stream']=False
    request_body = json.dumps(request_body_dict).encode('utf-8')
    response = requests.post(infer_url, data=request_body)
    return response.json()

async def post_ollama_completion_handler(request_body_dict):
    infer_url=f"{OLLAMA_BASE_URL}/v1/chat/completions"
    request_body = json.dumps(request_body_dict).encode('utf-8')
    response = requests.post(infer_url, data=request_body, headers={"Content-Type":"application/json"})
    return response.json()

async def post_ollama_pullmodel_handler(request_body_dict):
    # {'model_source':'ollama','model_name':'phi'}
    if request_body_dict['model_source'] == 'ollama':
       pull_ollama_model(request_body_dict["model_name"])
    return {
        "message": "The model pull has started please wait for a while before using it"
        }

async def post_ollama_getlist_handler():
    infer_url=f"{OLLAMA_BASE_URL}/api/tags"
    response = requests.get(infer_url, headers={"Content-Type":"application/json"})
    return response.json()


@app.post('/invocations')
async def invocations(request: Request):
    request_body = await request.body()
    try:
        request_body_dict = json.loads(request_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    action = request_body_dict['action']
    data = request_body_dict['data']
    if action == 'generate':
        return (await post_ollama_generation_handler(data))
    elif action == 'chat-completion':
        return (await post_ollama_completion_handler(data))
    elif action == 'pullmodel':
        return (await post_ollama_pullmodel_handler(data))
    elif action == 'list':
        return (await post_ollama_getlist_handler())
    return {
        "message": "You must add an action the following actions are supported: generate, chat-completion, pullmodel, list",
        "actions":[
                "generate",
                "chat-completion",
                "list",
                "pullmodel"
            ]
    }
