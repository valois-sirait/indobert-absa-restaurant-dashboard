import torch
import torch.nn as nn
from transformers import AutoModel


class MultiHeadIndoBERT(nn.Module):
    def __init__(self, bert_model, dropout=0.1):
        super().__init__()

        self.bert = bert_model
        hidden_size = self.bert.config.hidden_size

        self.dropout = nn.Dropout(dropout)

        # SESUAI TRAINING KAMU
        self.aspect_head = nn.Linear(hidden_size, 1)   # ✔ BINARY (BCE)
        self.sentiment_head = nn.Linear(hidden_size, 3) # ✔ 3 CLASS

    def forward(self, input_ids=None, attention_mask=None, inputs_embeds=None):

        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            inputs_embeds=inputs_embeds
        )

        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)

        aspect_logits = self.aspect_head(pooled_output)
        sentiment_logits = self.sentiment_head(pooled_output)

        return aspect_logits, sentiment_logits