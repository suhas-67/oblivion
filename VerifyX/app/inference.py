import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from pathlib import Path
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_model():
    model = models.resnet18(weights=None)
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, 1),
        nn.Sigmoid()
    )
    
    model_path = Path("document_fraud_model.pt")
    if model_path.exists():
        try:
            model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
            print(f"Loaded model from {model_path}")
        except Exception as e:
            print(f"Error loading model weights: {e}")
    else:
        print(f"Warning: Model weights not found at {model_path}. Using untrained weights.")
        
    model = model.to(device)
    model.eval()
    return model

model = get_model()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_fraud_score(ela_image_path: str) -> float:
    try:
        image = Image.open(ela_image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            output = model(image_tensor)
            fraud_score = output.item()
            
        return fraud_score
    except Exception as e:
        print(f"Inference Error: {e}")
        return 0.5
