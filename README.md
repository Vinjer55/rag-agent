# RAG Agent

## Development
#### To install the required dependencies, run the following command:
```
pip install -r requirements.txt
```

#### To start the API, run the following command:
```
uvicorn src.main:app
```

#### and then you can open http://127.0.0.1:8000/api/docs to view it using Swagger UI in the browser.

### Initialize Redis in Docker
```
docker run -d --name redis-local -p 6379:6379 redis
```

### Run Redis
```
docker start redis-local
```