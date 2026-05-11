"""
Phase 3: Deep Semantic Pipeline (Deep Learning Guided Abstraction)

This pipeline integrates the semantic saliency from MediaPipe into the abstraction process.
Instead of relying on low-level gradients, the model understands the semantic meaning (e.g., person vs background)
and abstracts them differently to create a depth-of-field, focal-point artistic effect.
"""

import cv2
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Add necessary paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'phase1_paper_implementation'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'phase2_novelty'))

from semantic_saliency import compute_semantic_saliency
from bilateral_abstraction import rgb_to_lab, lab_to_rgb
from saliency_guided import saliency_adaptive_bilateral_pass
from adaptive_quantization import adaptive_kmeans_quantize
from dog_edges import dog_edges
from enhanced_pipeline import compute_metrics


def semantic_guided_abstraction(image_bgr, n_iterations=4,
                                 sigma_d=3.0,
                                 sigma_r_high=2.0, # Foreground (preserve)
                                 sigma_r_low=10.0, # Background (heavy blur)
                                 smooth_sigma=5.0):
    """
    Phase 3: Semantic-guided iterative bilateral abstraction.
    """
    semantic_saliency = compute_semantic_saliency(image_bgr, smooth_sigma)
    
    lab = rgb_to_lab(image_bgr)
    
    ne = min(2, n_iterations - 1)
    lab_for_edges = None
    
    for i in range(n_iterations):
        lab = saliency_adaptive_bilateral_pass(
            lab, semantic_saliency, sigma_d, sigma_r_high, sigma_r_low
        )
        if i == ne - 1:
            lab_for_edges = lab.copy()
            
    if lab_for_edges is None:
        lab_for_edges = lab.copy()
        
    return lab, lab_for_edges, semantic_saliency

def semantic_quantization(lab_image, semantic_mask, k_foreground=16, k_background=4):
    """
    Apply different quantization levels to foreground and background.
    Foreground retains more colors (higher fidelity for faces/skin).
    Background is heavily posterized (k=4) for artistic effect.
    """
    # Quantize foreground
    quant_fg = adaptive_kmeans_quantize(lab_image, n_colors=k_foreground, use_ab=True)
    # Quantize background
    quant_bg = adaptive_kmeans_quantize(lab_image, n_colors=k_background, use_ab=True)
    
    # Blend using semantic mask
    mask = semantic_mask[:, :, np.newaxis]
    quant_blended = mask * quant_fg + (1.0 - mask) * quant_bg
    
    return quant_blended.astype(np.float32)

def semantic_overlay_edges(image_bgr, edge_map, semantic_mask, fg_strength=1.0, bg_strength=0.2, edge_color=(0, 0, 0)):
    """
    Overlay DoG edges onto the image, but adjust the edge strength based on semantics.
    Foreground edges are strong, background edges are faded out.
    """
    result = image_bgr.astype(np.float32).copy()
    
    # Base edge alpha (edge_map < 1 indicates edge)
    alpha_base = edge_map[:, :, np.newaxis]
    
    # Modulate alpha based on semantic mask
    # We want edge_map=0 to remain 0 in FG, but become closer to 1 in BG
    mask = semantic_mask[:, :, np.newaxis]
    strength_map = mask * fg_strength + (1.0 - mask) * bg_strength
    
    # Apply strength: alpha = 1.0 - (1.0 - alpha_base) * strength
    alpha_modulated = 1.0 - (1.0 - alpha_base) * strength_map
    
    ec = np.array(edge_color, dtype=np.float32)
    result = result * alpha_modulated + ec * (1.0 - alpha_modulated)
    
    return np.clip(result, 0, 255).astype(np.uint8)


def semantic_pipeline(
    image_bgr,
    # Bilateral params
    n_bilateral=4,
    sigma_d=3.0,
    sigma_r_fg=2.0,
    sigma_r_bg=10.0,
    # Quantization params
    use_quantization=True,
    k_fg=16,
    k_bg=4,
    # Edge params
    sigma_e=1.0,
    fg_edge_str=1.0,
    bg_edge_str=0.2
):
    """
    Phase 3 full semantic pipeline.
    """
    results = {'original': image_bgr.copy()}
    
    # Step 1: Semantic Saliency & Filtering
    lab_abstract, lab_for_edges, semantic_mask = semantic_guided_abstraction(
        image_bgr, n_bilateral, sigma_d, sigma_r_fg, sigma_r_bg
    )
    results['semantic_mask'] = semantic_mask
    results['abstracted'] = lab_to_rgb(lab_abstract)
    
    # Step 2: Semantic Quantization
    if use_quantization:
        lab_quantized = semantic_quantization(lab_abstract, semantic_mask, k_fg, k_bg)
        results['quantized'] = lab_to_rgb(lab_quantized)
        lab_final = lab_quantized
    else:
        lab_final = lab_abstract
        
    # Step 3: DoG Edges with semantic weighting
    edge_map = dog_edges(lab_for_edges, sigma_e=sigma_e)
    results['edge_map'] = edge_map
    
    final_bgr = lab_to_rgb(lab_final)
    final_with_edges = semantic_overlay_edges(
        final_bgr, edge_map, semantic_mask, 
        fg_strength=fg_edge_str, bg_strength=bg_edge_str
    )
    
    results['final'] = final_with_edges
    results['metrics'] = compute_metrics(image_bgr, final_with_edges)
    
    return results

if __name__ == "__main__":
    import urllib.request
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "results")
    os.makedirs(output_dir, exist_ok=True)
    
    test_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
    test_img_path = os.path.join(output_dir, "test_input.jpg")
    
    print("Downloading test image...")
    try:
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(test_img_path, 'wb') as out_file:
            out_file.write(response.read())
        print("Downloaded.")
    except Exception as e:
        print(f"Download failed ({e})")
        sys.exit(1)
        
    img = cv2.imread(test_img_path)
    
    print("Running Phase 3 Semantic Pipeline...")
    p3_results = semantic_pipeline(img)
    
    cv2.imwrite(os.path.join(output_dir, "phase3_semantic_mask.png"), (p3_results['semantic_mask'] * 255).astype(np.uint8))
    cv2.imwrite(os.path.join(output_dir, "phase3_final.png"), p3_results['final'])
    
    print("Phase 3 complete! Check the results folder.")
