import re
import requests


	
def data_for_chart(data):
    x = ["Enjoyment", "Disgust", "Sadness", "Anger", "Fear", 'Surprise', 'Other']
    y_bar = []
    y_pie = []
    for i in x:
        y_bar.append(data.count(i))
    sum_value = sum(y_bar)
    for i in y_bar:
        try:
            y_pie.append(round((i / sum_value), 1) * 100)
        except ZeroDivisionError:
            y_pie.append(0)
    return y_bar, y_pie

def preprocessing(data):
    data = data.lower() 
    with open('dataset/teencode.txt','r',encoding="utf8") as file:
      file = file.read()
      lines = file.split('\n')
      for line in lines:
        elements = line.split('\t')
        data = re.sub(r'\b{}+\b'.format(elements[0]), elements[1], data)   
    alphabet = 'abcdefghijlmnopqrstuvwxyz'
    for c in alphabet:
      data = re.sub(r'{}+'.format(c), c, data)
    data = re.sub(r'\s+', ' ', data)
    return data

def clean_html(sentence):
    text = re.sub(r'\s+', ' ', str(sentence))  # remove white space
    text = re.sub(r'<a.+?</a> ', '', text)
    text = re.sub('<.*?>', '', text)  # remove tag
    text = re.sub(r'http\S+', '', text)  # remove the link
    text = re.sub('&gt;', '>', text)
    text = re.sub('&lt;', '<', text)
    return text
