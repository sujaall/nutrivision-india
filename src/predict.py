import torch
import torchvision.transforms as transforms
from torchvision import models
import torch.nn as nn
from PIL import Image

def load_model(model_path):
    checkpoint = torch.load(model_path, map_location="cpu")
    class_names = checkpoint['class_names']
    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(
        model.last_channel, len(class_names))
    model.load_state_dict(checkpoint['model_state'])
    model.eval()
    return model, class_names

def predict_food(image_path, model, class_names, top_k=3):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485,0.456,0.406],
            [0.229,0.224,0.225])
    ])
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = model(tensor)
        probs = torch.softmax(out, dim=1)
        top_p, top_i = probs.topk(top_k)
    return [
        {"food": class_names[top_i[0][i]],
         "confidence": f"{top_p[0][i]*100:.1f}%"}
        for i in range(top_k)
    ]