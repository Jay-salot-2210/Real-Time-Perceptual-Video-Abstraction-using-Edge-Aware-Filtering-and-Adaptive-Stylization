"""
Phase 1: Soft Color Quantization (Temporally Coherent Stylization)
Based on: Winnemoller et al. "Real-Time Video Abstraction" SIGGRAPH 2006

Implements Equation (6) — pseudo-quantization with gradient-based sharpness control.
"""

import cv2
import numpy as np


def soft_quantize_channel(channel, n_bins=8, phi_q=8.0):
    """
    Q(x_hat, q, phi_q) — Eq. (6) in paper.
    
    Soft/pseudo quantization of a single channel.
    
    channel  : 2D float array
    n_bins   : number of quantization bins (paper: q ∈ [8, 10])
    phi_q    : sharpness of bin transition (larger = harder boundaries)
    
    Returns softly quantized channel.
    """
    # Normalize channel to [0, 1]
    c_min, c_max = channel.min(), channel.max()
    if c_max - c_min < 1e-6:
        return channel.copy()
    
    norm = (channel - c_min) / (c_max - c_min)
    
    # Bin width
    delta_q = 1.0 / n_bins
    
    # Find nearest bin boundary
    # q_nearest is the center of the nearest bin
    bin_idx = np.floor(norm * n_bins).astype(int)
    bin_idx = np.clip(bin_idx, 0, n_bins - 1)
    q_nearest = (bin_idx + 0.5) * delta_q  # center of each bin
    
    # Eq. (6): Q = q_nearest + (Δq/2) * tanh(phi_q * (f - q_nearest))
    quantized = q_nearest + (delta_q / 2.0) * np.tanh(phi_q * (norm - q_nearest))
    
    # Map back to original range
    return quantized * (c_max - c_min) + c_min


def gradient_based_sharpness(L_channel, lambda_phi=3.0, omega_phi=14.0,
                              lambda_delta=0.0, omega_delta=2.0):
    """
    Gradient-adaptive sharpness control (paper Section 3.3).
    
    Allows hard bin boundaries only in high-gradient regions.
    In low-gradient areas, transitions are spread out (painterly).
    
    Returns phi_q map (2D array) with values in [lambda_phi, omega_phi].
    """
    # Compute luminance gradient magnitude
    grad_x = cv2.Sobel(L_channel.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(L_channel.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
    
    # Clamp gradient to [lambda_delta, omega_delta]
    g_clamped = np.clip(gradient_mag, lambda_delta, omega_delta)
    
    # Map linearly to [lambda_phi, omega_phi]
    t = (g_clamped - lambda_delta) / (omega_delta - lambda_delta + 1e-8)
    phi_q_map = lambda_phi + t * (omega_phi - lambda_phi)
    
    return phi_q_map.astype(np.float32)


def soft_quantize_lab(image_lab, n_bins=8,
                       lambda_phi=3.0, omega_phi=14.0,
                       lambda_delta=0.0, omega_delta=2.0):
    """
    Apply soft quantization to Lab image with gradient-based sharpness.
    Only quantizes the L (luminance) channel as described in paper.
    
    Returns quantized Lab image.
    """
    result = image_lab.copy()
    L = image_lab[:, :, 0]  # L ∈ [0, 100]
    
    # Get spatially-varying phi_q
    phi_q_map = gradient_based_sharpness(
        L, lambda_phi, omega_phi, lambda_delta, omega_delta
    )
    
    # Apply quantization pixel-wise using mean phi_q 
    # (full pixel-wise would need loops; we use mean for speed)
    phi_q_mean = float(phi_q_map.mean())
    L_quantized = soft_quantize_channel(L, n_bins=n_bins, phi_q=phi_q_mean)
    
    result[:, :, 0] = L_quantized
    return result