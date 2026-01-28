import os
import torch
import pickle
import numpy as np
from PIL import Image
from torchvision import models, transforms
from torchvision.models import ResNet18_Weights
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------------
# Load saved embeddings database
# -------------------------------
with open("embeddings.pkl", "rb") as f:
    saved_embeddings, image_names = pickle.load(f)

saved_embeddings = np.array(saved_embeddings)

# -------------------------------
# Load pretrained ResNet18 model
# -------------------------------
model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
model = torch.nn.Sequential(*list(model.children())[:-1])
model.eval()

# -------------------------------
# Image preprocessing
# -------------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])


def recognize_captcha(image_path):
    """
    Recognize captcha image and return predicted text
    (filename without extension)
    """
    if not os.path.exists(image_path):
        return None

    try:
        img = Image.open(image_path).convert("RGB")
        img = transform(img).unsqueeze(0)

        with torch.no_grad():
            embedding = model(img).squeeze().numpy()

        similarities = cosine_similarity([embedding], saved_embeddings)
        best_match_index = similarities.argmax()

        filename = image_names[best_match_index]
        return os.path.splitext(filename)[0]

    except Exception:
        return None
