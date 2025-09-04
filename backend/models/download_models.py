# download_models.py: Tải models từ HuggingFace (chạy một lần khi có internet)

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Tải embedding model
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
embedding_model.save("./models/multilingual_e5_large")
AutoTokenizer.from_pretrained("intfloat/multilingual-e5-large").save_pretrained("./models/multilingual_e5_large")

# Tải LLM vinallama
tokenizer = AutoTokenizer.from_pretrained("vinai/vinallama-2.7b-chat")
tokenizer.save_pretrained("./models/vinallama-2.7b-chat")
model = AutoModelForCausalLM.from_pretrained("vinai/vinallama-2.7b-chat", torch_dtype=torch.float16)
model.save_pretrained("./models/vinallama-2.7b-chat")

print("🎉 Models đã tải về local thành công!")