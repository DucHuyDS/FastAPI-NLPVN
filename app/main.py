import asyncio
import random
import torch
import uvicorn
from fastapi import FastAPI, Request, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crawler import get_comments
from selenium.common.exceptions import InvalidArgumentException
from dotenv import load_dotenv
from predict_model import CNN,RNN, predict_CNN, predict_RNN
from transformers import AutoModel, pipeline, AutoTokenizer
from utils import  data_for_chart, preprocessing

class Link(BaseModel):
    link: str


class Comment(BaseModel):
    comment: str | None = None


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

tokenizer = AutoTokenizer.from_pretrained('vinai/phobert-base')

cnn_model = CNN()
cnn_model.load_state_dict(torch.load('model/cnn-model.pt',map_location=torch.device('cpu')))
phobert_cnn = AutoModel.from_pretrained('NDHuy3008/cnn-phobert-base')

rnn_model = RNN()
rnn_model.load_state_dict(torch.load('model/rnn-model.pt',map_location=torch.device('cpu')))
phobert_rnn = AutoModel.from_pretrained('NDHuy3008/rnn-phobert-base')

pipe = pipeline("text-classification", model="NDHuy3008/phobert-base-sentiment")


@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request, background_tasks: BackgroundTasks):
    num_for_socket = random.randint(0, 20)
    context = {
        'request': request,
        'number': num_for_socket,
    } 
    return templates.TemplateResponse("main.html", context)




@app.websocket("/ws/{number}")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    mapping = {0: "Anger", 1: "Disgust", 2: "Enjoyment", 3: "Fear", 4: "Other", 5: "Sadness",6: "Surprise"}
    while True:
        data = await websocket.receive_json()
        if data['type'] == 'link':         
            try:
                list_comments = await get_comments(data['link'], websocket)
            except (InvalidArgumentException, IndexError):
                await websocket.send_json({'type': 'error.!'})
            else:
                length_comments = len(list_comments)
                sentences_for_predict= []
                for i in range(length_comments):
                    sentences_for_predict.append(preprocessing(list_comments[i]))
                await websocket.send_json({'type': 'done.!', 'list_comments': list_comments,'list_predict':sentences_for_predict})
        elif data['type'] == 'model':
            value_list = []
            sentences = list(data['list_comments'])
            list_predict = list(data['list_predict'])
            length_comments = len(sentences)
            if data['model'] == 'tf':
                for i in range(length_comments):
                    output = pipe(list_predict[i])
                    label = output[0]['label']
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"],'label':label ,'sentence': sentences[i]})
                    await asyncio.sleep(0.01)
                await websocket.send_json({'type': data["model"],'label':'done'})
            elif data['model'] == 'cnn':
                for i in range(length_comments):
                    encodings = tokenizer(list_predict[i], truncation=True, padding=True, max_length=256,return_tensors='pt')
                    predict = predict_CNN(phobert_cnn,cnn_model, encodings)
                    label =mapping[predict[0]]
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"],'label':label ,'sentence': sentences[i]})
                    await asyncio.sleep(0.01)
                    
            elif data['model'] == 'rnn':
                for i in range(length_comments):
                    encodings = tokenizer(list_predict[i], truncation=True, padding=True, max_length=256,return_tensors='pt')
                    predict = predict_RNN(phobert_rnn,rnn_model, encodings)
                    label =mapping[predict[0]]
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"],'label':label ,'sentence': sentences[i]})
                    await asyncio.sleep(0.01)
            y_bar, y_pie = data_for_chart(value_list)
            # await websocket.send_json({'type': data["model"],'label':'done'}) draw
            await websocket.send_json({'type': "draw", 'model': data['model'], 'label':'done', 'y_bar': y_bar, 'y_pie': y_pie})



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
