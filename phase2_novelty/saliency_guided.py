"""
Phase 2: Saliency-Guided Abstraction (Novelty Contribution)
Problem with Paper: Uses only luminance + color opponency for saliency.
Our Improvement: Add gradient magnitude map as explicit, steerable saliency
                 that controls WHERE the bilateral filter is more/less aggressive.

In the paper, m(·) in Eq. (2) is mentioned but never used in the automatic case.
We activate it here with a proper saliency map.
"""

import cv2
import numpy as np


def compute_gradient_saliency(image_bgr, blur_sigma=2.0):
    """
    Compute gradient-magnitude saliency map.
    
    High gradient → visually important → preserve more detail (less smoothing)
    Low gradient  → visually unimportant → smooth more aggressively
    
    Returns normalized saliency map in [0, 1].
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Smooth first to reduce noise
    if blur_sigma > 0:
        ksize = int(2 * np.ceil(2 * blur_sigma) + 1)
        gray = cv2.GaussianBlur(gray, (ksize, ksize), blur_sigma)
    
    # Gradient magnitude using Sobel
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    
    # Normalize to [0, 1]
    if mag.max() > 1e-6:
        mag = mag / mag.max()
    
    return mag.astype(np.float32)


def compute_color_opponency_saliency(image_bgr):
    """
    Compute color opponency saliency (RG and BY channels).
    More faithful to the paper's mention of color opponency contrast.
    
    Returns normalized saliency map in [0, 1].
    """
    img_float = image_bgr.astype(np.float32) / 255.0
    B, G, R = img_float[:, :, 0], img_float[:, :, 1], img_float[:, :, 2]
    
    # Red-Green opponency
    RG = np.abs(R - G)
    # Blue-Yellow opponency
    BY = np.abs(B - 0.5 * (R + G))
    
    # Combine
    saliency = (RG + BY) / 2.0
    if saliency.max() > 1e-6:
        saliency = saliency / saliency.max()
    
    return saliency.astype(np.float32)


def combine_saliency_maps(gradient_sal, color_sal, w_gradient=0.6, w_color=0.4,
                           smooth_sigma=5.0):
    """
    Combine gradient and color opponency saliency maps.
    Smooth the combined map to avoid sharp saliency transitions.
    """
    combined = w_gradient * gradient_sal + w_color * color_sal
    
    # Smooth saliency map (prevents harsh boundaries in filtering)
    ksize = int(2 * np.ceil(2 * smooth_sigma) + 1)
    combined = cv2.GaussianBlur(combined, (ksize, ksize), smooth_sigma)
    
    # Re-normalize
    if combined.max() > 1e-6:
        combined = combined / combined.max()
    
    return combined.astype(np.float32)


def saliency_adaptive_bilateral_pass(image_lab, saliency_map, 
                                      sigma_d=3.0,
                                      sigma_r_high=2.0,   # for high-saliency (preserve)
                                      sigma_r_low=8.0):   # for low-saliency (smooth more)
    """
    Saliency-adaptive bilateral filtering.
    
    Key idea: Vary sigma_r based on saliency.
    - High saliency (edges, faces) → small sigma_r → preserve contrasts
    - Low saliency (backgrounds) → large sigma_r → smooth aggressively
    
    This implements the m(·) ≠ 0 case from paper Eq. (2).
    We blend two bilateral filter responses weighted by saliency.
    """
    d = int(2 * np.ceil(2 * sigma_d) + 1)
    
    result_high = np.zeros_like(image_lab)  # detail-preserving pass
    result_low = np.zeros_like(image_lab)   # smoothing pass
    
    for ch in range(3):
        channel = image_lab[:, :, ch].astype(np.float32)
        result_high[:, :, ch] = cv2.bilateralFilter(
            channel, d=d, sigmaColor=sigma_r_high, sigmaSpace=sigma_d
        )
        result_low[:, :, ch] = cv2.bilateralFilter(
            channel, d=d, sigmaColor=sigma_r_low, sigmaSpace=sigma_d
        )
    
    # Blend: saliency=1 → keep detail (result_high), saliency=0 → smooth more (result_low)
    sal = saliency_map[:, :, np.newaxis]  # (H, W, 1)
    blended = sal * result_high + (1.0 - sal) * result_low
    
    return blended.astype(np.float32)


def saliency_guided_abstraction(image_bgr, n_iterations=4,
                                 sigma_d=3.0,
                                 sigma_r_high=2.0,
                                 sigma_r_low=8.0,
                                 w_gradient=0.6, w_color=0.4):
    """
    Phase 2 core: Saliency-guided iterative bilateral abstraction.
    
    Improvements over paper:
    1. Explicit saliency map (gradient + color opponency combined)
    2. Per-pixel adaptive sigma_r controlled by saliency
    3. Background suppressed more aggressively, foreground preserved better
    
    Returns abstracted Lab image, saliency map, and intermediate result.
    """
    from bilateral_abstraction import rgb_to_lab
    
    # Compute saliency before filtering
    grad_sal = compute_gradient_saliency(image_bgr)
    color_sal = compute_color_opponency_saliency(image_bgr)
    saliency = combine_saliency_maps(grad_sal, color_sal, w_gradient, w_color)
    
    lab = rgb_to_lab(image_bgr)
    
    ne = min(2, n_iterations - 1)
    lab_for_edges = None
    
    for i in range(n_iterations):
        lab = saliency_adaptive_bilateral_pass(
            lab, saliency, sigma_d, sigma_r_high, sigma_r_low
        )
        if i == ne - 1:
            lab_for_edges = lab.copy()
    
    if lab_for_edges is None:
        lab_for_edges = lab.copy()
    
    return lab, lab_for_edges, saliency