from fastapi import FastAPI,Depends,HTTPException,Request
import time
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()


@app.middleware('http')
async def loggin_middle_ware(request:Request,call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time()-start_time
    print(f"{request.method} {request.url} took {duration:.4f}secs")
    return response 


@app.get("/")
def greeting_msg():
    return {"message":"Hey its working Bro😭😭"}