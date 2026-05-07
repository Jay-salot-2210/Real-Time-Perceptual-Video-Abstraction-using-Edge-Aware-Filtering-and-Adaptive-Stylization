"""
Phase 1: Complete Abstraction Pipeline
Based on: Winnemoller et al. "Real-Time Video Abstraction" SIGGRAPH 2006

Full pipeline: Bilateral Filter → DoG Edges → Soft Quantization
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bilateral_abstraction import rgb_to_lab, lab_to_rgb, iterative_bilateral_filter
from dog_edges import dog_edges, overlay_edges_on_image
from soft_quantization import soft_quantize_lab


def abstract_pipeline(
    image_bgr,
    # Bilateral filter params
    n_bilateral=4,
    sigma_d=3.0,
    sigma_r=4.25,
    # DoG edge params
    sigma_e=1.0,
    tau=0.98,
    phi_e=2.0,
    # Quantization params
    use_quantization=True,
    n_bins=8,
    lambda_phi=3.0,
    omega_phi=14.0,
    # Edge overlay params
    use_edges=True,
    edge_color=(0, 0, 0)
):
    """
    Full paper pipeline (Figure 2 in the paper):
    1. RGB → Lab
    2. Iterative bilateral filtering (anisotropic diffusion approx.)
    3. DoG edge detection (on intermediate filtered image)
    4. Optional soft color quantization
    5. Edge overlay
    6. Lab → RGB
    
    Returns dict with intermediate and final results for visualization.
    """
    results = {}
    results['original'] = image_bgr.copy()
    
    # Step 1: Iterative bilateral filtering
    lab_abstract, lab_for_edges = iterative_bilateral_filter(
        image_bgr, n_bilateral, sigma_d, sigma_r
    )
    results['abstracted_no_edges'] = lab_to_rgb(lab_abstract)
    
    # Step 2: Optional soft quantization on L channel
    if use_quantization:
        lab_quantized = soft_quantize_lab(
            lab_abstract, n_bins=n_bins,
            lambda_phi=lambda_phi, omega_phi=omega_phi
        )
        results['quantized_no_edges'] = lab_to_rgb(lab_quantized)
        lab_final = lab_quantized
    else:
        lab_final = lab_abstract
    
    # Step 3: DoG edge detection (from intermediate filtered image)
    if use_edges:
        edge_map = dog_edges(lab_for_edges, sigma_e=sigma_e, tau=tau, phi_e=phi_e)
        results['edge_map'] = edge_map
        
        # Overlay edges on final image
        final_bgr = lab_to_rgb(lab_final)
        final_with_edges = overlay_edges_on_image(final_bgr, edge_map, edge_color)
        results['final'] = final_with_edges
    else:
        results['final'] = lab_to_rgb(lab_final)
    
    return results


def visualize_pipeline(results, title="Phase 1: Paper Implementation", save_path=None):
    """Create a comprehensive visualization of the pipeline steps."""
    keys_to_show = []
    titles_map = {
        'original': 'Original',
        'abstracted_no_edges': 'After Bilateral Filter',
        'quantized_no_edges': 'After Quantization',
        'edge_map': 'DoG Edge Map',
        'final': 'Final Output'
    }
    
    for k in titles_map:
        if k in results:
            keys_to_show.append(k)
    
    n = len(keys_to_show)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if n == 1:
        axes = [axes]
    
    for ax, key in zip(axes, keys_to_show):
        img = results[key]
        if key == 'edge_map':
            ax.imshow(img, cmap='gray', vmin=0, vmax=1)
        else:
            ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(titles_map[key], fontsize=10)
        ax.axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    plt.close()
    return fig


def run_phase1_on_image(image_path, output_dir, params=None):
    """
    Run the full Phase 1 pipeline on a single image and save results.
    """
    if params is None:
        params = {}
    
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    
    # Resize for consistency
    h, w = img.shape[:2]
    max_dim = 512
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    # Run pipeline
    results = abstract_pipeline(img, **params)
    
    # Save individual outputs
    base = os.path.splitext(os.path.basename(image_path))[0]
    
    for key, val in results.items():
        if key == 'edge_map':
            save_p = os.path.join(output_dir, f"{base}_p1_{key}.png")
            cv2.imwrite(save_p, (val * 255).astype(np.uint8))
        else:
            save_p = os.path.join(output_dir, f"{base}_p1_{key}.png")
            cv2.imwrite(save_p, val)
    
    # Save comparison figure
    fig_path = os.path.join(output_dir, f"{base}_p1_pipeline.png")
    visualize_pipeline(results, title=f"Phase 1 — {base}", save_path=fig_path)
    
    return results, fig_path


if __name__ == "__main__":
    import urllib.request
    
    # Download a test image (public domain)
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bikesg.jpg/640px-Bikesg.jpg"
    test_img_path = "/home/claude/project/results/test_input.jpg"
    output_dir = "/home/claude/project/results"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Downloading test image...")
    try:
        urllib.request.urlretrieve(test_url, test_img_path)
        print("Downloaded test image.")
    except Exception as e:
        print(f"Download failed: {e}")
        # Create a synthetic test image
        test_img = np.zeros((256, 256, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (50, 50), (200, 200), (100, 150, 200), -1)
        cv2.circle(test_img, (128, 128), 60, (200, 100, 50), -1)
        cv2.imwrite(test_img_path, test_img)
        print("Created synthetic test image.")
    
    print("Running Phase 1 pipeline...")
    results, fig_path = run_phase1_on_image(test_img_path, output_dir)
    print(f"Phase 1 complete! Pipeline figure saved to: {fig_path}")
    print("Keys in results:", list(results.keys()))