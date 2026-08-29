"""
VerifyX - Classical Machine Learning (ML) Document Fraud Model
Extracts statistical forensic features (ELA statistics, Laplacian variance, noise gradients, color inconsistencies)
and trains an Ensemble Random Forest / Gradient Boosting Classifier.

Usage:
    python train_ml_fraud_model.py --data_dir ./dataset --output document_fraud_model.joblib
"""

import os
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import cv2
from scipy.stats import skew, kurtosis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
import joblib

# ---------------------------------------------------------
# FORENSIC FEATURE EXTRACTION
# ---------------------------------------------------------
def compute_ela_array(image_path: str, quality: int = 90) -> np.ndarray:
    """Compute ELA difference array."""
    try:
        original = Image.open(image_path).convert('RGB')
        temp_path = f"_temp_feat_{os.getpid()}_{Path(image_path).stem}.jpg"
        original.save(temp_path, 'JPEG', quality=quality)
        temporary = Image.open(temp_path)
        
        diff = ImageChops.difference(original, temporary)
        ela_arr = np.array(diff, dtype=np.float32)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return ela_arr
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return np.zeros((224, 224, 3), dtype=np.float32)

def extract_forensic_features(image_path: str) -> np.ndarray:
    """
    Extracts a 24-dimensional handcrafted forensic feature vector:
    - ELA statistical moments (mean, std, skew, kurtosis, percentiles)
    - Laplacian edge sharpness & noise gradient inconsistencies
    - Color balance & saturation variance
    """
    features = []
    
    # 1. ELA Features
    ela_arr = compute_ela_array(image_path)
    ela_gray = cv2.cvtColor(ela_arr.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    
    features.append(np.mean(ela_arr))
    features.append(np.std(ela_arr))
    features.append(np.max(ela_arr))
    features.append(float(skew(ela_gray.ravel())))
    features.append(float(kurtosis(ela_gray.ravel())))
    features.append(np.percentile(ela_gray, 75))
    features.append(np.percentile(ela_gray, 90))
    features.append(np.percentile(ela_gray, 99))
    
    # Ratio of high-error pixels (> 15 diff)
    high_error_ratio = np.sum(ela_gray > 15) / (ela_gray.size + 1e-6)
    features.append(high_error_ratio)
    
    # 2. Laplacian Blur & Edge Noise Inconsistency
    try:
        orig_img = cv2.imread(image_path)
        if orig_img is None:
            orig_img = np.zeros((224, 224, 3), dtype=np.uint8)
        gray = cv2.cvtColor(orig_img, cv2.COLOR_BGR2GRAY)
        
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        features.append(lap_var)
        
        # Sobel gradient standard deviation
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        features.append(np.std(sobelx))
        features.append(np.std(sobely))
        
        # 3. HSV Saturation & Value Inconsistencies (for cut & paste photos)
        hsv = cv2.cvtColor(orig_img, cv2.COLOR_BGR2HSV)
        features.append(np.mean(hsv[:, :, 1])) # Saturation mean
        features.append(np.std(hsv[:, :, 1]))  # Saturation std
        features.append(np.mean(hsv[:, :, 2])) # Value mean
        features.append(np.std(hsv[:, :, 2]))  # Value std
        
        # Color channel standard deviations
        features.append(np.std(orig_img[:, :, 0]))
        features.append(np.std(orig_img[:, :, 1]))
        features.append(np.std(orig_img[:, :, 2]))
    except Exception:
        features.extend([0.0] * 10)
        
    return np.array(features, dtype=np.float32)

# ---------------------------------------------------------
# DATASET LOADER & TRAINER
# ---------------------------------------------------------
def load_dataset(data_dir: str):
    X, y = [], []
    data_path = Path(data_dir)
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    
    # Authentic (0)
    for auth_dir in ["authentic", "genuine", "real", "0"]:
        p = data_path / auth_dir
        if p.exists() and p.is_dir():
            for f in p.rglob("*"):
                if f.suffix.lower() in valid_exts:
                    feat = extract_forensic_features(str(f))
                    X.append(feat)
                    y.append(0)
                    
    # Tampered (1)
    for tamp_dir in ["tampered", "forged", "fake", "1"]:
        p = data_path / tamp_dir
        if p.exists() and p.is_dir():
            for f in p.rglob("*"):
                if f.suffix.lower() in valid_exts:
                    feat = extract_forensic_features(str(f))
                    X.append(feat)
                    y.append(1)
                    
    return np.array(X), np.array(y)

def train_ml(data_dir: str, output_path: str = "document_fraud_model.joblib"):
    print(f"Extracting forensic features from dataset: {data_dir}...")
    X, y = load_dataset(data_dir)
    
    if len(X) == 0:
        print("Error: No valid document images found in dataset folder.")
        return
        
    print(f"Loaded {len(X)} samples: {np.sum(y == 0)} Authentic, {np.sum(y == 1)} Tampered.")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("\nTraining Ensemble Classifier (Random Forest + Gradient Boosting)...")
    rf = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
    
    ensemble = VotingClassifier(estimators=[('rf', rf), ('gb', gb)], voting='soft')
    ensemble.fit(X_train, y_train)
    
    # Evaluation
    y_pred = ensemble.predict(X_test)
    y_prob = ensemble.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    try:
        auc = roc_auc_score(y_test, y_prob)
    except Exception:
        auc = 0.0
        
    print(f"\n================ MODEL EVALUATION ================")
    print(f"Accuracy : {acc * 100:.2f}%")
    print(f"ROC-AUC  : {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Authentic", "Tampered"]))
    
    # Save Pipeline
    joblib.dump(ensemble, output_path)
    print(f"Model saved successfully to: {Path(output_path).resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ML Document Fraud Model")
    parser.add_argument("--data_dir", type=str, default="./dataset", help="Path to dataset directory")
    parser.add_argument("--output", type=str, default="document_fraud_model.joblib", help="Output model path")
    args = parser.parse_args()
    train_ml(args.data_dir, args.output)
