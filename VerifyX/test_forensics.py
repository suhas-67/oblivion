import sys
from pathlib import Path
from app.forensics import validate_verhoeff, extract_and_validate_id_numbers, analyze_metadata_exif, decode_qr_code, compute_srm_noise_analysis, run_full_forensic_suite

def test_verhoeff():
    print("Testing Verhoeff Checksum...")
    # Known valid Aadhaar numbers and test numbers
    # A valid test Aadhaar number: 3390 6574 1753 -> Let's test
    test_num = "339065741753"
    is_valid = validate_verhoeff(test_num)
    print(f"Number {test_num} valid: {is_valid}")
    
    # Tampered test number (altering single digit: 3390 6574 1754)
    tampered_num = "339065741754"
    is_tampered_valid = validate_verhoeff(tampered_num)
    print(f"Tampered {tampered_num} valid: {is_tampered_valid} (Should be False)")
    assert is_tampered_valid == False, "Tampered number should fail Verhoeff!"

    extracted = extract_and_validate_id_numbers(f"Your Aadhaar No. : {test_num} and modified {tampered_num}")
    print("Extraction & Validation Result:", extracted)
    assert extracted["hard_fail"] == True, "Should flag failure on tampered number in text!"
    print(" Verhoeff tests passed successfully!\n")

def test_on_real_uploads():
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("Uploads dir not found, skipping real file tests.")
        return
        
    sample_files = list(uploads_dir.glob("*.jpeg")) + list(uploads_dir.glob("*.png"))
    sample_files = [f for f in sample_files if not f.name.startswith("ela_")]
    
    print(f"Testing Forensic Suite on {len(sample_files)} uploaded files...")
    for file_path in sample_files[:3]:
        print(f"\n--- Testing file: {file_path.name} ---")
        suite_res = run_full_forensic_suite(file_path, text_content="Sample test 3390 6574 1753")
        print("Metadata:", suite_res["metadata"]["status"], suite_res["metadata"]["detected_software"])
        print("QR Code:", suite_res["qr_code"]["status"], suite_res["qr_code"].get("has_qr"))
        print("SRM Noise:", suite_res["srm_noise"]["status"], suite_res["srm_noise"]["anomaly_score"])
        print("Red Flags:", suite_res["red_flags"])

if __name__ == "__main__":
    test_verhoeff()
    test_on_real_uploads()
    print("\nAll Forensic Suite Tests Completed!")
