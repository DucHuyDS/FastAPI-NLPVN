from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
from fastapi import FastAPI, Request, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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
origins = [
    os.getenv('domain'),
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



phobert = "phobert-large-sentiment"
roberta = "xlm-roberta-sentiment"



def query(data, model):
    API_URL = f'https://api-inference.huggingface.co/models/NDHuy3008/{model}' 
    headers = {"Authorization": f"Bearer {os.getenv('token')}"}
    response = requests.post(API_URL, headers=headers,
	 json={
		"inputs": data,
		"options":{
			"wait_for_model":True
			}
		}
	)
    return response.json()

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

@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request, background_tasks: BackgroundTasks):
    # load api before run
    background_tasks.add_task(query, '',roberta)
    background_tasks.add_task(query, '',phobert)
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
                list_comments = await parse_comment(data['link'], websocket)
            except (InvalidArgumentException, IndexError):
                await websocket.send_json({'type': 'error.!'})
            else:
                await websocket.send_json({'type': 'done.!', 'list_comments': list_comments})
        elif data['type'] == 'model':
            value_list = []
            sentences = list(data['list_comments'])
            length_comments = len(sentences)
            if data['model'] == 'phobert' or data['model'] == 'roberta':
                if data['model'] == 'phobert':
                    model = phobert
                elif data['model'] == 'roberta':
                    model = roberta
                    
                output = query(sentences,model)

                for i in range(length_comments):
                    label = output[i][0]['label']
                    sentence = sentences[i]
                    # text = data['list_comments'][i]
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"],'label':label ,'sentence': sentence})
            elif data['model'] == 'cnn':
                model = keras.models.load_model(f'{base_dir}/model/model_cnn.h5')
                with open(f'{base_dir}/model/tokenizer_cnn.pickle', 'rb') as handle:
                    tokenizer = pickle.load(handle)

                # comments = list(data['list_comments'])
                # length_comments = len(comments)

                for i in range(length_comments):
                    texts = [sentences[i]]
                    texts = tokenizer.texts_to_sequences(texts)
                    texts = pad_sequences(texts, maxlen=1000)
                    prediction = model.predict(texts, batch_size=1024, verbose=1)
                    label = mapping[prediction.argmax(-1)[0]]
                    sentence = sentences[i]
                    # text = f"[{label}]{comments[i]}"
                    value_list.append(label)
                    await websocket.send_json({'type': data["model"], 'label':label, 'sentence': sentence})
            y_bar, y_pie = data_for_chart(value_list)
            await websocket.send_json({'type': 'draw', 'model': data['model'], 'y_bar': y_bar, 'y_pie': y_pie})
