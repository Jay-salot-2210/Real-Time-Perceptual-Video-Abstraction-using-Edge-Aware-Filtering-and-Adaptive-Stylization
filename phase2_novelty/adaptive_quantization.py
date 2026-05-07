"""
Phase 2: Adaptive K-Means Color Quantization (Novelty Contribution)

Problem with Paper: Fixed equidistant bin boundaries for quantization.
Paper acknowledges: "Our fixed equidistant quantization boundaries are arbitrary,
                    making it difficult to control results for artistic purposes."

Our Solution: Use k-means clustering in Lab color space to find
              data-driven, perceptually uniform bin boundaries.
              
This produces better color posterization because it:
1. Places bins where actual pixel colors cluster (data-driven)
2. Works in perceptually uniform Lab space
3. Preserves important color distinctions that fixed bins may split arbitrarily
"""

import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans


def adaptive_kmeans_quantize(image_lab, n_colors=8, use_ab=True):
    """
    K-means quantization in Lab color space.
    
    Improvement over paper: Instead of fixed equidistant bins on L only,
    we cluster the full Lab color space to find natural color groups.
    
    image_lab : Lab image (H, W, 3), L ∈ [0,100], a,b ∈ [-127,127]
    n_colors  : number of color clusters (analogous to n_bins in paper)
    use_ab    : if True, cluster in full Lab; if False, cluster L only
    
    Returns quantized Lab image with same shape.
    """
    h, w = image_lab.shape[:2]
    
    if use_ab:
        # Normalize Lab to similar scales for clustering
        # L: [0,100] → [0,1], a,b: [-127,127] → [-1,1]
        pixels = image_lab.reshape(-1, 3).astype(np.float32)
        pixels_norm = pixels.copy()
        pixels_norm[:, 0] /= 100.0
        pixels_norm[:, 1] /= 127.0
        pixels_norm[:, 2] /= 127.0
    else:
        # Cluster only L channel
        pixels = image_lab.reshape(-1, 3).astype(np.float32)
        pixels_norm = pixels[:, 0:1] / 100.0
    
    # MiniBatchKMeans is faster than KMeans for images
    kmeans = MiniBatchKMeans(
        n_clusters=n_colors,
        random_state=42,
        batch_size=min(1000, pixels_norm.shape[0]),
        n_init=3
    )
    labels = kmeans.fit_predict(pixels_norm)
    
    # Replace each pixel with its cluster center
    if use_ab:
        centers = kmeans.cluster_centers_  # (n_colors, 3), normalized
        # Denormalize
        centers_lab = centers.copy()
        centers_lab[:, 0] *= 100.0
        centers_lab[:, 1] *= 127.0
        centers_lab[:, 2] *= 127.0
        quantized_pixels = centers_lab[labels]
    else:
        centers = kmeans.cluster_centers_  # (n_colors, 1)
        centers_L = centers[:, 0] * 100.0
        quantized_L = centers_L[labels]
        quantized_pixels = pixels.copy()
        quantized_pixels[:, 0] = quantized_L
    
    quantized = quantized_pixels.reshape(h, w, 3).astype(np.float32)
    return quantized


def smooth_quantization_boundary(image_lab, quantized_lab, 
                                  edge_map, blend_strength=0.3):
    """
    Blend quantized and non-quantized results near edges to avoid
    harsh color transitions at boundaries.
    
    Near edges: keep more of the original abstracted image detail.
    In flat regions: apply full quantization.
    
    edge_map: [0,1] where 0 = edge, 1 = no edge
    """
    # edge_map: 0 near edges, 1 away from edges
    # We want: near edges → keep abstracted (less quantized)
    #          away from edges → apply quantization
    mask = edge_map[:, :, np.newaxis]  # (H, W, 1)
    
    # Invert: 1 = edge, 0 = flat
    edge_weight = (1.0 - mask) * blend_strength
    
    # Blend: more quantized in flat areas, less at edges
    blended = (1.0 - edge_weight) * quantized_lab + edge_weight * image_lab
    return blended.astype(np.float32)