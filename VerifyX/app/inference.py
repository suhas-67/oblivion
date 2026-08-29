from io import BytesIO
from pathlib import Path
from typing import Optional
from PIL import Image, ImageChops
import numpy as np
import cv2
from scipy.stats import skew, kurtosis
from app.config import BASE_DIR

class MLInferenceEngine:
    """Inference engine for the 11-feature RVL-CDIP Document Forgery Model."""
    
    def __init__(self):
        self.ml_model = None
        self.torch_model = None
        self.device = None
        self.transform = None
        self._load_models()

    def _load_models(self):
        # 1. Load Classical ML VotingClassifier Pipeline (RandomForest + GradientBoosting)
        joblib_path = BASE_DIR / "document_fraud_model.joblib"
        pkl_path = BASE_DIR / "document_fraud_model.pkl"
        
        target_path = joblib_path if joblib_path.exists() else (pkl_path if pkl_path.exists() else None)
        if target_path:
            try:
                import joblib
                self.ml_model = joblib.load(target_path)
                print(f"[InferenceEngine] Loaded RVL-CDIP ML Model from {target_path.name}")
            except Exception as e:
                print(f"[InferenceEngine] Failed to load joblib model: {e}")

        # 2. PyTorch Fallback (if ML model absent)
        pt_path = BASE_DIR / "document_fraud_model.pt"
        if pt_path.exists() and self.ml_model is None:
            try:
                import torch
                import torch.nn as nn
                from torchvision import models, transforms

                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = models.resnet18(weights=None)
                model.fc = nn.Sequential(
                    nn.Linear(model.fc.in_features, 1),
                    nn.Sigmoid()
                )
                model.load_state_dict(torch.load(pt_path, map_location=self.device, weights_only=True))
                model = model.to(self.device)
                model.eval()
                self.torch_model = model

                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                print(f"[InferenceEngine] Loaded PyTorch model from {pt_path.name}")
            except Exception as e:
                print(f"[InferenceEngine] PyTorch initialization note: {e}")

    @staticmethod
    def compute_ela_features(img: Image.Image, quality: int = 90, error_threshold: int = 20) -> list:
        """Computes 9 statistical features from on-the-fly Error Level Analysis."""
        try:
            buffer = BytesIO()
            img.save(buffer, 'JPEG', quality=quality)
            buffer.seek(0)
            recompressed = Image.open(buffer)
            
            diff = ImageChops.difference(img, recompressed)
            diff_np = np.array(diff).flatten()
            
            ela_mean = float(np.mean(diff_np))
            ela_std = float(np.std(diff_np))
            ela_max = float(np.max(diff_np))
            ela_skew = float(skew(diff_np))
            ela_kurt = float(kurtosis(diff_np))
            p75, p90, p99 = [float(p) for p in np.percentile(diff_np, [75, 90, 99])]
            high_error_ratio = float(np.sum(diff_np > error_threshold) / (len(diff_np) + 1e-7))
            
            return [ela_mean, ela_std, ela_max, ela_skew, ela_kurt, p75, p90, p99, high_error_ratio]
        except Exception as e:
            print(f"[InferenceEngine] ELA feature extraction error: {e}")
            return [0.0] * 9

    @staticmethod
    def compute_edge_and_blur_features(img: Image.Image) -> list:
        """Computes 2 edge and blur variance features using Laplacian and Sobel gradients."""
        try:
            cv_img = np.array(img.convert('L'))
            laplacian_var = float(cv2.Laplacian(cv_img, cv2.CV_64F).var())
            sobelx = cv2.Sobel(cv_img, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(cv_img, cv2.CV_64F, 0, 1, ksize=3)
            sobel_var = float(np.var(np.sqrt(sobelx**2 + sobely**2)))
            return [laplacian_var, sobel_var]
        except Exception as e:
            print(f"[InferenceEngine] Edge/blur feature extraction error: {e}")
            return [0.0, 0.0]

    def extract_11_features(self, image_path: str | Path) -> np.ndarray:
        """Extracts the exact 11 features matching the Google Colab training code."""
        try:
            img = Image.open(image_path).convert('RGB')
            feats = self.compute_ela_features(img) + self.compute_edge_and_blur_features(img)
            return np.nan_to_num(np.array(feats, dtype=np.float32))
        except Exception as e:
            print(f"[InferenceEngine] Feature extraction error: {e}")
            return np.zeros(11, dtype=np.float32)

    def predict_fraud_score(self, image_path: str | Path) -> float:
        """Runs ML pipeline inference and returns Fraud Probability Score [0.0, 1.0]."""
        # 1. Classical ML Voting Classifier
        if self.ml_model is not None:
            try:
                feats = self.extract_11_features(image_path)
                probs = self.ml_model.predict_proba([feats])[0]
                score = float(probs[1])
                print(f"[ML Model Inference] Fraud Probability: {score * 100:.2f}%")
                return score
            except Exception as e:
                print(f"[InferenceEngine] ML Inference Error: {e}")

        # 2. PyTorch ResNet Fallback
        if self.torch_model is not None:
            try:
                import torch
                image = Image.open(image_path).convert('RGB')
                image_tensor = self.transform(image).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    output = self.torch_model(image_tensor)
                    score = float(output.item())
                    print(f"[DL Model Inference] Fraud Probability: {score * 100:.2f}%")
                    return score
            except Exception as e:
                print(f"[InferenceEngine] PyTorch Inference Error: {e}")
                
        return 0.15

# Global singleton
engine = MLInferenceEngine()

def predict_fraud_score(image_path: str | Path) -> float:
    return engine.predict_fraud_score(image_path)
