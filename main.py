from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(title='MeNeM', version='1.0.0')       # mention title and version of project in the space respectively

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def root():
    return { 'status' : 'alive' }


app.include_router(router, prefix='/api/v1')