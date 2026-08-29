import os
import glob
import zipfile
import tarfile
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageChops
from skimage.feature import local_binary_pattern
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import lmdb
from io import BytesIO

# --- 1. SMART DATASET UNPACKER ---
def deep_unpack_and_locate():
    print("--- LOCATING & UNPACKING DATASETS ---")
    
    # 1. Recursively unpack any hidden .tar or .zip files inside dataset/
    unpacked_any = True
    while unpacked_any:
        unpacked_any = False
        for root, dirs, files in os.walk("dataset"):
            for file in files:
                filepath = os.path.join(root, file)
                
                # Unpack Zips
                if filepath.endswith('.zip'):
                    print(f"Unzipping trapped archive: {file}...")
                    try:
                        with zipfile.ZipFile(filepath, 'r') as zf:
                            zf.extractall(root)
                        os.remove(filepath)  # Clean up to save space
                        unpacked_any = True
                    except Exception as e:
                        print(f"Skipping {file}: {e}")
                        
                # Unpack Tars
                elif filepath.endswith(('.tar', '.tar.gz', '.tgz')):
                    print(f"Untarring trapped archive: {file}...")
                    try:
                        with tarfile.open(filepath, 'r:*') as tf:
                            tf.extractall(root)
                        os.remove(filepath)
                        unpacked_any = True
                    except Exception as e:
                        print(f"Skipping {file}: {e}")

    # 2. Broadly locate the extracted files
    authentic_files = glob.glob("dataset/**/*.tif", recursive=True)
    lmdb_paths = glob.glob("dataset/**/data.mdb", recursive=True)
    
    if not authentic_files:
        raise FileNotFoundError("Could not find Authentic (.tif) images. Extraction may have failed.")
    if not lmdb_paths:
        raise FileNotFoundError("Could not find DocTamper data.mdb even after deep unpack.")
        
    # Grab the folder containing the training LMDB
    train_lmdb_dir = next((os.path.dirname(p) for p in lmdb_paths if "training" in p.lower()), os.path.dirname(lmdb_paths[0]))
    
    return authentic_files, train_lmdb_dir

# --- 2. FORENSIC FEATURE EXTRACTION ---
def get_ela_features(img, quality=90):
    try:
        temp_filename = "temp_ela.jpg"
        img.save(temp_filename, 'JPEG', quality=quality)
        recompressed = Image.open(temp_filename)
        
        diff = ImageChops.difference(img, recompressed)
        diff_np = np.array(diff)
        
        ela_mean, ela_std, ela_max = np.mean(diff_np), np.std(diff_np), np.max(diff_np)
        os.remove(temp_filename)
        return [ela_mean, ela_std, ela_max]
    except Exception:
        return [0, 0, 0]

def get_texture_features(img):
    try:
        img_gray = np.array(img.convert('L'))
        img_resized = cv2.resize(img_gray, (300, 300))
        
        lbp = local_binary_pattern(img_resized, 8, 1, method='uniform')
        n_bins = int(lbp.max() + 1)
        hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
        
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        return hist.tolist()
    except Exception:
        return [0] * 10

def process_image(img):
    img = img.convert('RGB')
    ela = get_ela_features(img)
    tex = get_texture_features(img)
    return ela + tex

# --- 3. DATASET BUILDING ---
def build_dataset(authentic_files, train_lmdb_dir, max_samples_per_class=500):
    print(f"\n--- EXTRACTING FEATURES ({max_samples_per_class} images per class) ---")
    data = []
    labels = []
    
    # Process Authentic Documents (Class 0)
    auth_count = 0
    print("Processing Authentic documents (this takes a minute)...")
    for filepath in authentic_files:
        if auth_count >= max_samples_per_class: break
        try:
            img = Image.open(filepath)
            features = process_image(img)
            data.append(features)
            labels.append(0)
            auth_count += 1
        except Exception:
            pass

    # Process Tampered Documents from LMDB (Class 1)
    tamp_count = 0
    print("Processing Tampered documents from LMDB (this takes a minute)...")
    env = lmdb.open(train_lmdb_dir, readonly=True, lock=False)
    with env.begin(write=False) as txn:
        cursor = txn.cursor()
        for key, value in cursor:
            if tamp_count >= max_samples_per_class: break
            if b'image' in key:
                try:
                    img = Image.open(BytesIO(value))
                    features = process_image(img)
                    data.append(features)
                    labels.append(1)
                    tamp_count += 1
                except Exception:
                    pass
    env.close()
            
    return np.array(data), np.array(labels)

# --- 4. EXECUTION & TRAINING ---
if __name__ == "__main__":
    # 1. Extract and find paths safely
    authentic_files, train_lmdb_dir = deep_unpack_and_locate()
    
    # 2. Build dataset matrix (Adjust to 1000 if you want a stronger model, but 500 is faster)
    X, y = build_dataset(authentic_files, train_lmdb_dir, max_samples_per_class=500)
    print(f"\nDataset Built: {X.shape[0]} total images, {X.shape[1]} features per image.")

    # 3. Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Model
    print("\nTraining Random Forest Model...")
    clf = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = clf.predict(X_test)
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, target_names=["Authentic", "Tampered"]))

    # 6. Save Model
    model_filename = "document_fraud_ml_model.joblib"
    joblib.dump(clf, model_filename)
    print(f"\nSUCCESS! Model saved as '{model_filename}' in your VerifyX folder.")