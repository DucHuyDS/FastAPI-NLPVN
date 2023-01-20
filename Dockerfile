FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD uvicorn --host 0.0.0.0 --port $PORT app.main:app
