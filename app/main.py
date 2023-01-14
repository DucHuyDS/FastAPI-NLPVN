from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .crawler import preprocessing, parse_comment
import random
from selenium.common.exceptions import InvalidArgumentException
import pickle
from tensorflow import keras
from keras.utils import pad_sequences
import pathlib

base_dir = pathlib.Path(__file__).parent.parent.resolve()


class Link(BaseModel):
    link: str


class Comment(BaseModel):
    comment: str | None = None


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



from ctypes import *
lib8 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcublas.so.11')
lib1 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcudart.so.11.0')
lib2 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcublasLt.so.11')
lib3 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcufft.so.10')
lib4 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcurand.so.10')
lib5 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcusolver.so.10')
lib6 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcusparse.so.11')
lib7 = cdll.LoadLibrary('/data/users/CHDHPC/2017902628/cuda/lib64/libcudnn.so.8')


mapping = {0: "Anger", 1: "Disgust", 2: "Enjoyment", 3: "Fear", 4: "Other", 5: "Sadness", 6: "Surprise"}
model_phobert = AutoModelForSequenceClassification.from_pretrained(
                    "NDHuy3008/phobert-base-sentiment",
                    num_labels=7,
                    label2id={"Anger": 0, "Disgust": 1, "Enjoyment": 2, "Fear": 3, "Other": 4, "Sadness": 5,
                              "Surprise": 6},
                    id2label=mapping,
                )
tokenizer_phobert = AutoTokenizer.from_pretrained("NDHuy3008/phobert-base-sentiment",
                                                          do_lower_case=True)

model_roberta = AutoModelForSequenceClassification.from_pretrained(
                    "NDHuy3008/xlm-roberta-sentiment",
                    num_labels=7,
                    label2id={"Anger": 0, "Disgust": 1, "Enjoyment": 2, "Fear": 3, "Other": 4, "Sadness": 5,
                              "Surprise": 6},
                    id2label=mapping,
                )
tokenizer_roberta = AutoTokenizer.from_pretrained("NDHuy3008/xlm-roberta-sentiment",
                                                          do_lower_case=True)





@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    num_for_socket = random.randint(0, 20)
    context = {
        'request': request,
        'number': num_for_socket,
    }
    return templates.TemplateResponse("main.html", context)


def data_for_chart(data):
    x = ["Enjoyment", "Disgust", "Sadness", "Anger", "Fear", 'Surprise', 'Other']
    y_bar = []
    y_pie = []
    for i in x:
        y_bar.append(data.count(i))
    sum_value = sum(y_bar)
    for i in y_bar:
        y_pie.append(round((i / sum_value), 1) * 100)
    return y_bar, y_pie


@app.websocket("/ws/{number}")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_json()
        if data['type'] == 'link':
            try:
                list_comments = await parse_comment(data['link'], websocket)
            except (InvalidArgumentException, IndexError):
                await websocket.send_json({'type': 'error.!'})
            else:
                await websocket.send_json({'type': 'done.!', 'list_comments': list_comments})
        elif data['type'] == 'model':
            value_list = []
            
            if data['model'] == 'phobert' or data['model'] == 'roberta':
                if data['model'] == 'phobert':
                    model = model_phobert
                    tokenizer = tokenizer_phobert
                else:
                    model = model_roberta
                    tokenizer = tokenizer_roberta
                pipe = TextClassificationPipeline(model=model, tokenizer=tokenizer)
                for comment in data['list_comments']:
                    prediction = pipe(comment)[0]
                    label = prediction['label']
                    text = f'[{label}]{comment}'
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"], 'comment': text})
            elif data['model'] == 'cnn':
                model = keras.models.load_model(f'{base_dir}/model/model_cnn.h5')
                with open(f'{base_dir}/model/tokenizer_cnn.pickle', 'rb') as handle:
                    tokenizer = pickle.load(handle)

                comments = list(data['list_comments'])
                length_comments = len(comments)

                for i in range(length_comments):
                    texts = [comments[i]]
                    texts = tokenizer.texts_to_sequences(texts)
                    texts = pad_sequences(texts, maxlen=1000)
                    prediction = model.predict(texts, batch_size=1024, verbose=1)
                    label = mapping[prediction.argmax(-1)[0]]
                    text = f"[{label}]{comments[i]}"
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"], 'comment': text})
            y_bar, y_pie = data_for_chart(value_list)
            await websocket.send_json({'type': 'draw', 'model': data['model'], 'y_bar': y_bar, 'y_pie': y_pie})
