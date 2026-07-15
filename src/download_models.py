import os
import requests
from pathlib import Path
import sys

MODELS_TO_DOWNLOAD = {
    "SwinIR": {
        "url": "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth",
        "path": "models/SwinIR/swinir_realsr_x4.pth"
    },
    "HAT": {
        "url": "https://huggingface.co/AEmotionStudio/ai-upscale-models/resolve/main/Real_HAT_GAN_SRx4.pth",
        "path": "models/HAT/hat_realsr_x4.pth"
    }
}

def download_file(url, target_path):
    target_path = Path(target_path)
    if target_path.exists():
        print(f"[{target_path.parent.name}] File already exists: {target_path.name}")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[{target_path.parent.name}] Downloading {target_path.name}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        with open(target_path, 'wb') as file:
            downloaded = 0
            for data in response.iter_content(chunk_size=1024 * 1024):
                file.write(data)
                downloaded += len(data)
                if total_size > 0:
                    done = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB")
                    sys.stdout.flush()
        print("\nDownload completed!")
    except Exception as e:
        print(f"\nFailed to download {url}: {e}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    for model_name, info in MODELS_TO_DOWNLOAD.items():
        download_file(info["url"], project_root / info["path"])
