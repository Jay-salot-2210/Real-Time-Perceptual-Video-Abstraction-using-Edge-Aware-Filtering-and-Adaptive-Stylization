import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import urllib.request

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase1_paper_implementation'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase2_novelty'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase3_deep_semantic'))

from pipeline import abstract_pipeline as p1_pipeline
from enhanced_pipeline import enhanced_pipeline as p2_pipeline
from semantic_pipeline import semantic_pipeline as p3_pipeline

def download_image(url, save_path):
    if not os.path.exists(save_path):
        print(f"Downloading {url}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())

def create_p1_vs_p2_comparison(img_rgb, p1_res, p2_res, save_path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Phase 1 vs Phase 2: From Uniform to Saliency-Guided Abstraction", fontsize=18, fontweight='bold')
    
    axes[0].imshow(img_rgb)
    axes[0].set_title("Original Image", fontsize=14)
    axes[0].axis('off')
    
    axes[1].imshow(cv2.cvtColor(p1_res['final'], cv2.COLOR_BGR2RGB))
    axes[1].set_title("Phase 1 (Paper)\nUniform blur, fixed equidistant color bins\nResult: Cluttered, limited color reduction", fontsize=14)
    axes[1].axis('off')
    
    axes[2].imshow(cv2.cvtColor(p2_res['final'], cv2.COLOR_BGR2RGB))
    axes[2].set_title("Phase 2 (Our Novelty)\nSaliency-guided blur, Lab K-Means (k=8)\nResult: Cleaner posterization, truer colors", fontsize=14)
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

def create_p2_vs_p3_comparison(img_rgb, p2_res, p3_res, save_path):
    fig, axes = plt.subplots(1, 4, figsize=(24, 6))
    fig.suptitle("Phase 2 vs Phase 3: Solving the Texture Problem with Semantic Focal Abstraction", fontsize=18, fontweight='bold')
    
    axes[0].imshow(img_rgb)
    axes[0].set_title("Original Image\nNotice the highly textured background", fontsize=14)
    axes[0].axis('off')
    
    axes[1].imshow(cv2.cvtColor(p2_res['final'], cv2.COLOR_BGR2RGB))
    axes[1].set_title("Phase 2 (Gradient Saliency)\nFails on textures: Grass/crowd has high gradients\nso algorithm mistakenly preserves the background noise", fontsize=14)
    axes[1].axis('off')
    
    axes[2].imshow(p3_res['semantic_mask'], cmap='gray')
    axes[2].set_title("Phase 3 Semantic Mask\nOpenCV Fine-Grained Static Saliency\nIsolates the subject independent of local texture", fontsize=14)
    axes[2].axis('off')
    
    axes[3].imshow(cv2.cvtColor(p3_res['final'], cv2.COLOR_BGR2RGB))
    axes[3].set_title("Phase 3 (Semantic Focal Abstraction)\nBackground heavily blurred (sigma_r=10) & quantized (k=4)\nForeground preserved (sigma_r=2, k=16). Artistic depth-of-field!", fontsize=14)
    axes[3].axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(project_root, "results")
    os.makedirs(output_dir, exist_ok=True)
    
    # We use 'messi5.jpg' because it has a person (foreground) and highly textured grass/crowd (background)
    # This perfectly highlights why Phase 2's gradient-saliency fails and why Phase 3's semantic mask is needed.
    test_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/messi5.jpg"
    test_img_path = os.path.join(output_dir, "test_messi.jpg")
    
    download_image(test_url, test_img_path)
    
    print("Loading image...")
    img_bgr = cv2.imread(test_img_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    print("Running Phase 1...")
    p1_res = p1_pipeline(img_bgr)
    
    print("Running Phase 2...")
    p2_res = p2_pipeline(img_bgr)
    
    print("Running Phase 3...")
    p3_res = p3_pipeline(img_bgr)
    
    print("Generating Phase 1 vs Phase 2 comparison...")
    create_p1_vs_p2_comparison(img_rgb, p1_res, p2_res, os.path.join(output_dir, "comparison_1_P1_vs_P2.png"))
    
    print("Generating Phase 2 vs Phase 3 comparison...")
    create_p2_vs_p3_comparison(img_rgb, p2_res, p3_res, os.path.join(output_dir, "comparison_2_P2_vs_P3.png"))
    
    print("Done! Check the results folder for comparison_1_P1_vs_P2.png and comparison_2_P2_vs_P3.png")
