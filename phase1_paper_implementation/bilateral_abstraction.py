"""
Phase 1: Paper Implementation
Bilateral Filter-based Image Abstraction
Based on: Winnemoller et al. "Real-Time Video Abstraction" SIGGRAPH 2006

This module implements the core bilateral filtering pipeline described in the paper.
"""

import cv2
import numpy as np


def rgb_to_lab(image_bgr):
    """Convert BGR image to CIELab color space (as recommended in paper)."""
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)


def lab_to_rgb(image_lab):
    """Convert CIELab back to BGR."""
    lab_uint8 = np.clip(image_lab, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lab_uint8, cv2.COLOR_LAB2BGR)


def bilateral_filter_pass(image_lab, sigma_d=3.0, sigma_r=4.25):
    """
    Single pass of bilateral filter in Lab color space.
    
    Paper Eq. (1): H(x_hat, sigma_d, sigma_r) - the bilateral filter
    
    sigma_d: spatial domain sigma (blur radius) — paper uses 3
    sigma_r: range sigma (contrast preservation) — paper uses 4.25
    
    Small sigma_r  → preserve nearly all edges (less smoothing)
    Large sigma_r  → approaches Gaussian blur (more smoothing)
    """
    # diameter = 2 * ceil(2*sigma_d) + 1  (approximate support)
    d = int(2 * np.ceil(2 * sigma_d) + 1)
    
    # OpenCV bilateral filter works per-channel; apply to each Lab channel
    result = np.zeros_like(image_lab)
    for ch in range(3):
        channel = image_lab[:, :, ch]
        # sigmaColor maps to sigma_r, sigmaSpace maps to sigma_d
        filtered = cv2.bilateralFilter(
            channel.astype(np.float32),
            d=d,
            sigmaColor=sigma_r,
            sigmaSpace=sigma_d
        )
        result[:, :, ch] = filtered
    return result


def iterative_bilateral_filter(image_bgr, n_iterations=4, sigma_d=3.0, sigma_r=4.25):
    """
    Iterative bilateral filtering — approximates anisotropic diffusion.
    
    Paper Section 3.1: "iterated bilateral filters as one special case"
    Paper uses nb ∈ {3,4} iterations typically.
    
    Returns both the abstracted Lab image and the intermediate result 
    (after ne iterations) used for edge detection.
    """
    lab = rgb_to_lab(image_bgr)
    
    ne = min(2, n_iterations - 1)  # edge extraction iteration (paper: ne ∈ {1,2})
    lab_for_edges = None
    
    for i in range(n_iterations):
        lab = bilateral_filter_pass(lab, sigma_d, sigma_r)
        if i == ne - 1:
            lab_for_edges = lab.copy()
    
    if lab_for_edges is None:
        lab_for_edges = lab.copy()
    
    return lab, lab_for_edges


def abstract_image(image_bgr, n_iterations=4, sigma_d=3.0, sigma_r=4.25):
    """
    Full abstraction pipeline without stylization (Phase 1 core).
    Returns abstracted BGR image.
    """
    lab_abstract, lab_edges = iterative_bilateral_filter(
        image_bgr, n_iterations, sigma_d, sigma_r
    )
    return lab_to_rgb(lab_abstract), lab_edges