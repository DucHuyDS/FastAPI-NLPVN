import torch
import torch.nn as nn
import torch.nn.functional as F
import torch

class RNN(nn.Module):
    
    def __init__(self):
        super().__init__()
        num_classes = 7
        hidden_size = 128
        dropout = 0.4
        embedding_dim = 768
        num_layers = 1  # Increase the number of layers to 3
        self.rnn = nn.GRU(embedding_dim, hidden_size, num_layers, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        mean_x = torch.mean(x, dim=1, keepdim=True)
        batch_size, num_models, seq_len, hidden_size = mean_x.shape
        x = mean_x.reshape(batch_size*num_models, seq_len, hidden_size)
        
        x, _ = self.rnn(x)
        
        x = F.relu(x)
        x = F.max_pool1d(x.transpose(1, 2), x.size(1)).squeeze(2)
        
        x = self.dropout(x)
        logit = self.fc1(x)
        return logit
    
class CNN(nn.Module):

    def __init__(self):
        super().__init__()
        num_classes = 7  # number of targets to predict
        output_channel = 32
        dropout = 0.4  # dropout value
        embedding_dim = 768  # length of embedding dim

        ks = 3  # three conv nets here

        input_channel = 4

        # 3 convolutional nets
        self.conv1 = nn.Conv2d(input_channel, output_channel, (3, embedding_dim),  padding=(2, 0), groups=input_channel)
        self.conv2 = nn.Conv2d(input_channel, output_channel, (4, embedding_dim),  padding=(3, 0), groups=input_channel)
        self.conv3 = nn.Conv2d(input_channel, output_channel, (5, embedding_dim),  padding=(4, 0), groups=input_channel)
        # apply dropout
        self.dropout = nn.Dropout(dropout)


        self.fc1 = nn.Linear(ks * output_channel, num_classes)

    def forward(self, x, **kwargs):
        x = [F.relu(self.conv1(x)).squeeze(3), F.relu(self.conv2(x)).squeeze(3), F.relu(self.conv3(x)).squeeze(3)]
        # max-over-time pooling; # (batch, channel_output) * ks
        x = [F.max_pool1d(i, i.size(2)).squeeze(2) for i in x]
        x = torch.cat(x, 1)
        x = self.dropout(x)
        logit = self.fc1(x)
        return logit


def predict_CNN(phobert_model, CNN_model, data):
    b_input_ids = data['input_ids']
    b_input_mask = data['attention_mask']

    # tell pytorch not to bother calculating gradients
    with torch.no_grad():

        # forward propagation (evaluate model on training batch)
        outputs = phobert_model(input_ids=b_input_ids, attention_mask=b_input_mask)
        hidden_layers = outputs['hidden_states']  # get hidden layers

        hidden_layers = torch.stack(hidden_layers, dim=1)  # stack the layers
        hidden_layers = hidden_layers[:,-4:]
        

    logits = CNN_model(hidden_layers)
    _, predicted = torch.max(logits, 1)
    predicted = predicted.detach().cpu()


    return predicted.tolist()


def predict_RNN(phobert_model, RNN_model, data):
    
    b_input_ids = data['input_ids']
    b_input_mask = data['attention_mask']

    # tell pytorch not to bother calculating gradients
    with torch.no_grad():

        # forward propagation (evaluate model on training batch)
        outputs = phobert_model(input_ids=b_input_ids, attention_mask=b_input_mask)
        hidden_layers = outputs['hidden_states']  # get hidden layers

        hidden_layers = torch.stack(hidden_layers, dim=1)  # stack the layers
        hidden_layers = hidden_layers[:,:]
        

    logits = RNN_model(hidden_layers)
    _, predicted = torch.max(logits, 1)
    predicted = predicted.detach().cpu()

    return predicted.tolist()

