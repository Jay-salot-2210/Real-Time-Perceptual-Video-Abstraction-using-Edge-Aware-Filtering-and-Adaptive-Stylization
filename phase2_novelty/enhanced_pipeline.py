"""
Phase 2: Enhanced Pipeline with Quantitative Metrics
Combines saliency-guided abstraction + adaptive quantization + evaluation metrics.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'phase1'))

from saliency_guided import saliency_guided_abstraction, compute_gradient_saliency, compute_color_opponency_saliency
from adaptive_quantization import adaptive_kmeans_quantize, smooth_quantization_boundary
from bilateral_abstraction import lab_to_rgb, rgb_to_lab
from dog_edges import dog_edges, overlay_edges_on_image
from soft_quantization import soft_quantize_lab


def compute_metrics(original_bgr, abstracted_bgr):
    """
    Quantitative evaluation metrics (improvement over paper which only had user study).
    
    Returns dict with:
    - PSNR: Peak Signal-to-Noise Ratio (higher = more faithful)
    - SSIM-approx: Structural similarity (higher = more structurally similar)
    - color_reduction: Ratio of unique colors in original vs abstracted
    - edge_preservation: How well edges are preserved
    """
    orig_f = original_bgr.astype(np.float32)
    abst_f = abstracted_bgr.astype(np.float32)
    
    # PSNR
    mse = np.mean((orig_f - abst_f) ** 2)
    if mse < 1e-10:
        psnr = 100.0
    else:
        psnr = 20 * np.log10(255.0 / np.sqrt(mse))
    
    # Approximate SSIM (luminance + contrast + structure)
    orig_gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    abst_gray = cv2.cvtColor(abstracted_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    
    mu1, mu2 = orig_gray.mean(), abst_gray.mean()
    sig1 = orig_gray.std()
    sig2 = abst_gray.std()
    sig12 = ((orig_gray - mu1) * (abst_gray - mu2)).mean()
    
    C1, C2 = 6.5025, 58.5225
    ssim = (2*mu1*mu2 + C1) * (2*sig12 + C2) / \
           ((mu1**2 + mu2**2 + C1) * (sig1**2 + sig2**2 + C2))
    
    # Color reduction ratio
    h, w = original_bgr.shape[:2]
    orig_pixels = original_bgr.reshape(-1, 3)
    abst_pixels = abstracted_bgr.reshape(-1, 3)
    
    # Quantize to reduce color space for counting
    orig_reduced = (orig_pixels // 8).astype(np.int32)
    abst_reduced = (abst_pixels // 8).astype(np.int32)
    
    n_orig = len(set(map(tuple, orig_reduced)))
    n_abst = len(set(map(tuple, abst_reduced)))
    color_reduction = 1.0 - (n_abst / max(n_orig, 1))
    
    # Edge preservation: compare edge maps
    orig_edges = cv2.Canny(cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY), 50, 150)
    abst_edges = cv2.Canny(cv2.cvtColor(abstracted_bgr, cv2.COLOR_BGR2GRAY), 50, 150)
    
    # Dilate original edges for some tolerance
    kernel = np.ones((3, 3), np.uint8)
    orig_edges_dilated = cv2.dilate(orig_edges, kernel, iterations=1)
    
    # What fraction of abstracted edges fall within original edge regions?
    if abst_edges.sum() > 0:
        edge_preservation = float(np.logical_and(abst_edges > 0, orig_edges_dilated > 0).sum()) / \
                           float((abst_edges > 0).sum())
    else:
        edge_preservation = 0.0
    
    return {
        'PSNR (dB)': round(psnr, 2),
        'SSIM': round(float(ssim), 4),
        'Color Reduction (%)': round(color_reduction * 100, 1),
        'Edge Preservation': round(edge_preservation, 4)
    }


def enhanced_pipeline(
    image_bgr,
    # Bilateral params
    n_bilateral=4,
    sigma_d=3.0,
    sigma_r_high=2.0,
    sigma_r_low=8.0,
    # Saliency params
    w_gradient=0.6,
    w_color=0.4,
    # DoG params
    sigma_e=1.0,
    tau=0.98,
    phi_e=2.0,
    # Adaptive quantization params
    use_quantization=True,
    n_colors=8,
):
    """
    Phase 2 enhanced pipeline:
    1. Compute explicit saliency map (gradient + color opponency)
    2. Saliency-adaptive bilateral filtering (variable sigma_r per region)
    3. Adaptive k-means quantization in Lab space
    4. DoG edge detection + overlay
    """
    results = {'original': image_bgr.copy()}
    
    # Step 1+2: Saliency-guided bilateral filtering
    lab_abstract, lab_for_edges, saliency = saliency_guided_abstraction(
        image_bgr, n_bilateral, sigma_d, sigma_r_high, sigma_r_low,
        w_gradient, w_color
    )
    results['saliency_map'] = saliency
    results['abstracted'] = lab_to_rgb(lab_abstract)
    
    # Step 3: Adaptive quantization
    if use_quantization:
        lab_quantized = adaptive_kmeans_quantize(lab_abstract, n_colors=n_colors, use_ab=True)
        results['quantized'] = lab_to_rgb(lab_quantized.astype(np.float32))
        lab_final = lab_quantized.astype(np.float32)
    else:
        lab_final = lab_abstract
    
    # Step 4: DoG edges
    edge_map = dog_edges(lab_for_edges, sigma_e=sigma_e, tau=tau, phi_e=phi_e)
    results['edge_map'] = edge_map
    
    final_bgr = lab_to_rgb(lab_final)
    final_with_edges = overlay_edges_on_image(final_bgr, edge_map)
    results['final'] = final_with_edges
    
    # Metrics
    results['metrics'] = compute_metrics(image_bgr, final_with_edges)
    
    return results


def visualize_comparison(p1_results, p2_results, save_path=None):
    """
    Create a side-by-side comparison: Phase 1 (paper) vs Phase 2 (ours).
    """
    fig = plt.figure(figsize=(16, 9))
    
    # Title
    fig.suptitle("Real-Time Image Abstraction: Paper vs. Enhanced Method", 
                 fontsize=15, fontweight='bold', y=0.98)
    
    gs = gridspec.GridSpec(3, 5, figure=fig, hspace=0.4, wspace=0.3)
    
    rows_config = [
        # (row, col, key_p1_or_p2, title, is_phase2)
        (0, 0, 'original', 'Original Input', None),
        (0, 1, 'abstracted_no_edges', 'P1: After Bilateral', 'phase1'),
        (0, 2, 'quantized_no_edges', 'P1: Quantized', 'phase1'),
        (0, 3, 'edge_map', 'P1: DoG Edges', 'phase1'),
        (0, 4, 'final', 'P1: Final Output', 'phase1'),
        
        (1, 0, 'original', 'Original Input', None),
        (1, 1, 'saliency_map', 'P2: Saliency Map', 'phase2'),
        (1, 2, 'abstracted', 'P2: Adaptive Filter', 'phase2'),
        (1, 3, 'quantized', 'P2: K-Means Quant.', 'phase2'),
        (1, 4, 'final', 'P2: Final Output', 'phase2'),
    ]
    
    for row, col, key, title, source in rows_config:
        ax = fig.add_subplot(gs[row, col])
        
        if source == 'phase1':
            data = p1_results.get(key)
        elif source == 'phase2':
            data = p2_results.get(key)
        else:
            data = p1_results.get(key, p2_results.get(key))
        
        if data is None:
            ax.set_visible(False)
            continue
        
        if key in ('edge_map', 'saliency_map'):
            ax.imshow(data, cmap='hot' if key == 'saliency_map' else 'gray', vmin=0, vmax=1)
        else:
            ax.imshow(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
        
        label_color = '#1a6fb5' if source == 'phase1' else '#b51a1a'
        ax.set_title(title, fontsize=8, color=label_color, fontweight='bold')
        ax.axis('off')
    
    # Metrics comparison table
    ax_metrics = fig.add_subplot(gs[2, :])
    ax_metrics.axis('off')
    
    p1_metrics = p1_results.get('metrics', {})
    p2_metrics = p2_results.get('metrics', {})
    
    if p1_metrics and p2_metrics:
        metric_keys = list(p1_metrics.keys())
        col_labels = ['Metric', 'Phase 1 (Paper)', 'Phase 2 (Ours)', 'Better?']
        table_data = []
        for k in metric_keys:
            v1 = p1_metrics[k]
            v2 = p2_metrics[k]
            # Determine which is better
            if k in ('PSNR (dB)', 'SSIM', 'Edge Preservation'):
                better = 'P2 ✓' if v2 >= v1 else 'P1 ✓'
            else:  # Color Reduction: higher = more abstraction
                better = 'P2 ✓' if v2 >= v1 else 'P1 ✓'
            table_data.append([k, str(v1), str(v2), better])
        
        table = ax_metrics.table(
            cellText=table_data,
            colLabels=col_labels,
            cellLoc='center',
            loc='center',
            bbox=[0.1, 0.0, 0.8, 1.0]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        ax_metrics.set_title("Quantitative Comparison", fontsize=11, fontweight='bold', pad=10)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved comparison: {save_path}")
    
    plt.close()


if __name__ == "__main__":
    import urllib.request
    
    # Ensure phase1 is accessible
    phase1_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'phase1')
    sys.path.insert(0, phase1_dir)
    
    from pipeline import abstract_pipeline, visualize_pipeline, run_phase1_on_image
    
    output_dir = "/home/claude/project/results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Download test image
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bikesg.jpg/640px-Bikesg.jpg"
    test_img_path = "/home/claude/project/results/test_input.jpg"
    
    print("Downloading test image...")
    try:
        urllib.request.urlretrieve(test_url, test_img_path)
        print("Downloaded.")
    except Exception as e:
        print(f"Download failed ({e}), using synthetic image.")
        test_img = np.random.randint(100, 200, (256, 256, 3), dtype=np.uint8)
        for i in range(5):
            x1, y1 = np.random.randint(0, 200, 2)
            color = tuple(np.random.randint(0, 255, 3).tolist())
            cv2.rectangle(test_img, (x1, y1), (x1+50, y1+50), color, -1)
        cv2.imwrite(test_img_path, test_img)
    
    img = cv2.imread(test_img_path)
    h, w = img.shape[:2]
    max_dim = 512
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    
    print("Running Phase 1...")
    p1_results = abstract_pipeline(img, n_bilateral=4, use_quantization=True)
    p1_results['metrics'] = compute_metrics(img, p1_results['final'])
    visualize_pipeline(
        p1_results, 
        title="Phase 1: Paper Implementation",
        save_path=os.path.join(output_dir, "phase1_result.png")
    )
    
    print("Running Phase 2...")
    p2_results = enhanced_pipeline(img, n_bilateral=4, use_quantization=True)
    
    print("Creating comparison visualization...")
    visualize_comparison(
        p1_results, p2_results,
        save_path=os.path.join(output_dir, "comparison.png")
    )
    
    print("\n=== METRICS COMPARISON ===")
    print(f"{'Metric':<25} {'Phase 1':>15} {'Phase 2':>15}")
    print("-" * 55)
    for k in p1_results['metrics']:
        v1 = p1_results['metrics'][k]
        v2 = p2_results['metrics'][k]
        print(f"{k:<25} {str(v1):>15} {str(v2):>15}")
    
    print(f"\nResults saved to: {output_dir}")