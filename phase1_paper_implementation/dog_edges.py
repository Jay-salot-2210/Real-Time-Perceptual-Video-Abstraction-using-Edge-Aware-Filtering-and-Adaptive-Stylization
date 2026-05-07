"""
Phase 1: DoG Edge Detection
Based on: Winnemoller et al. "Real-Time Video Abstraction" SIGGRAPH 2006

Implements Equations (4) and (5) from the paper exactly.
"""

import cv2
import numpy as np


def gaussian_blur_channel(channel, sigma):
    """
    S(x_hat, sigma_e) — Eq. (5) in paper.
    Gaussian blur of a single-channel float image.
    """
    ksize = int(2 * np.ceil(2 * sigma) + 1)
    return cv2.GaussianBlur(channel, (ksize, ksize), sigma)


def dog_edges(image_lab, sigma_e=1.0, tau=0.98, phi_e=2.0):
    """
    Difference-of-Gaussians edge detection — Eq. (4) in paper.

    D(x_hat, sigma_e, tau, phi_e):
        = 1                              if (S_sigma_e - tau * S_sigma_r) > 0
        = 1 + tanh(phi_e * (S_sigma_e - tau * S_sigma_r))   otherwise

    sigma_e : spatial scale for edge detection (paper: σe; coarser = larger value)
    tau     : threshold sensitivity (paper: τ = 0.98 throughout)
    phi_e   : sharpness of edge activation falloff (paper: φe ∈ [0.75, 5.0])

    Returns edge map in [0, 1], where values near 1 = edge present.
    """
    # Work on L (luminance) channel only, normalized to [0, 1]
    L = image_lab[:, :, 0] / 100.0  # L ∈ [0, 100] → [0, 1]

    # Two scales: sigma_e and sqrt(1.6) * sigma_e (paper: factor of 1.6)
    sigma_r = np.sqrt(1.6) * sigma_e

    S_sigma_e = gaussian_blur_channel(L.astype(np.float32), sigma_e)
    S_sigma_r = gaussian_blur_channel(L.astype(np.float32), sigma_r)

    # DoG response
    dog = S_sigma_e - tau * S_sigma_r

    # Smoothed step function (Eq. 4)
    edge_map = np.where(
        dog > 0,
        np.ones_like(dog),                              # bright regions = no edge
        1.0 + np.tanh(phi_e * dog)                      # edge = value drops toward 0
    )

    return edge_map.astype(np.float32)


def overlay_edges_on_image(image_bgr, edge_map, edge_color=(0, 0, 0)):
    """
    Overlay DoG edges onto abstracted image.
    edge_map ∈ [0,1]: values < 1 indicate edges (darken those pixels).
    """
    result = image_bgr.astype(np.float32).copy()
    # Expand edge_map to 3 channels and multiply
    alpha = edge_map[:, :, np.newaxis]  # (H, W, 1)
    ec = np.array(edge_color, dtype=np.float32)
    result = result * alpha + ec * (1.0 - alpha)
    return np.clip(result, 0, 255).astype(np.uint8)