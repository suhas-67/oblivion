"""
VerifyX - Document Fraud Model Training Script
Train a custom PyTorch ResNet-18 model on your own dataset of Authentic vs Tampered documents.

Usage:
    1. Organize your dataset into:
       dataset/
         ├── authentic/   (or 0/) -> genuine, untampered documents
         └── tampered/    (or 1/) -> forged, edited, photoshopped documents

    2. Run training:
       python train_fraud_model.py --data_dir ./dataset --epochs 15 --batch_size 16 --lr 0.0001
"""

import os
import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import models, transforms

# ---------------------------------------------------------
# ELA PREPROCESSING UTILITY
# ---------------------------------------------------------
def generate_ela_image(image_path: str, quality: int = 90) -> Image.Image:
    """Compute in-memory Error Level Analysis for training."""
    try:
        original = Image.open(image_path).convert('RGB')
        temp_path = f"_temp_train_{os.getpid()}_{Path(image_path).stem}.jpg"
        original.save(temp_path, 'JPEG', quality=quality)
        temporary = Image.open(temp_path)
        
        diff = ImageChops.difference(original, temporary)
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        scale = 255.0 / max_diff
        ela_img = ImageEnhance.Brightness(diff).enhance(scale)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return ela_img
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return Image.new('RGB', (224, 224))

# ---------------------------------------------------------
# CUSTOM DOCUMENT FRAUD DATASET
# ---------------------------------------------------------
class DocumentFraudDataset(Dataset):
    def __init__(self, data_dir: str, transform=None, use_ela: bool = True):
        self.samples = []
        self.transform = transform
        self.use_ela = use_ela
        
        data_path = Path(data_dir)
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        
        # Load Authentic (Label 0)
        for auth_dir in ["authentic", "genuine", "real", "0"]:
            p = data_path / auth_dir
            if p.exists() and p.is_dir():
                for f in p.rglob("*"):
                    if f.suffix.lower() in valid_extensions:
                        self.samples.append((str(f), 0.0))
                        
        # Load Tampered (Label 1)
        for tamp_dir in ["tampered", "forged", "fake", "1"]:
            p = data_path / tamp_dir
            if p.exists() and p.is_dir():
                for f in p.rglob("*"):
                    if f.suffix.lower() in valid_extensions:
                        self.samples.append((str(f), 1.0))
                        
        print(f"Loaded {len(self.samples)} total images ({sum(1 for _, l in self.samples if l == 0.0)} authentic, {sum(1 for _, l in self.samples if l == 1.0)} tampered).")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        if self.use_ela:
            image = generate_ela_image(img_path)
        else:
            image = Image.open(img_path).convert('RGB')
            
        if self.transform:
            image = self.transform(image)
            
        return image, torch.tensor([label], dtype=torch.float32)

# ---------------------------------------------------------
# MODEL DEFINITION
# ---------------------------------------------------------
def create_model():
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, 1),
        nn.Sigmoid()
    )
    return model

# ---------------------------------------------------------
# TRAINING LOOP
# ---------------------------------------------------------
def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    transform_train = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomRotation(degrees=5),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    transform_val = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    full_dataset = DocumentFraudDataset(args.data_dir, transform=transform_train, use_ela=True)
    if len(full_dataset) == 0:
        print("Error: No images found. Ensure your data directory has 'authentic' and 'tampered' folders.")
        return
        
    val_size = max(1, int(len(full_dataset) * 0.2))
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    model = create_model().to(device)
    criterion = nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=2, factor=0.5)
    
    best_val_loss = float('inf')
    output_path = Path(args.output)
    
    print("\nStarting Training...")
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss, train_correct = 0.0, 0
        
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * images.size(0)
            preds = (outputs >= 0.5).float()
            train_correct += (preds == labels).sum().item()
            
        train_loss = train_loss / len(train_dataset)
        train_acc = (train_correct / len(train_dataset)) * 100
        
        # Validation
        model.eval()
        val_loss, val_correct = 0.0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                preds = (outputs >= 0.5).float()
                val_correct += (preds == labels).sum().item()
                
        val_loss = val_loss / len(val_dataset)
        val_acc = (val_correct / len(val_dataset)) * 100
        scheduler.step(val_loss)
        
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] | Train Loss: {train_loss:.4f}, Acc: {train_acc:.1f}% | Val Loss: {val_loss:.4f}, Acc: {val_acc:.1f}%")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), output_path)
            print(f"  --> Saved improved model checkpoint to {output_path}")
            
    print(f"\nTraining Complete! Best model saved to: {output_path.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Document Fraud Detection Model")
    parser.add_argument("--data_dir", type=str, default="./dataset", help="Path to dataset root")
    parser.add_argument("--epochs", type=int, default=15, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--output", type=str, default="document_fraud_model.pt", help="Output .pt model path")
    args = parser.parse_args()
    train(args)
