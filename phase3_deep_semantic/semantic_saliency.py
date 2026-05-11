"""
Phase 3: Deep Saliency (Novelty Contribution)

This uses OpenCV's advanced Static Saliency (Spectral Residual / Fine Grained) 
to identify the main subject in the image. This saliency mask replaces the 
low-level gradient/color saliency from Phase 2, allowing the abstraction pipeline 
to focus on the semantic foreground and heavily abstract the background.
"""

import cv2
import numpy as np

def get_advanced_saliency(image_bgr):
    """
    Use OpenCV's Static Saliency (Fine Grained) to get a mask of the main subject.
    Returns a normalized mask in [0, 1] where 1 is the subject and 0 is the background.
    """
    # Create the saliency object
    saliency = cv2.saliency.StaticSaliencyFineGrained_create()
    
    # Compute the saliency map
    success, saliency_map = saliency.computeSaliency(image_bgr)
    
    if success:
        # Normalize to [0, 1]
        saliency_map = (saliency_map * 255).astype(np.uint8)
        
        # Threshold to create a stronger foreground mask
        # We use Otsu's binarization to automatically find the best threshold
        _, thresholded = cv2.threshold(saliency_map, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Smooth the binary mask to make it continuous
        mask = thresholded.astype(np.float32) / 255.0
    else:
        # Fallback to all ones (treat whole image as foreground) if it fails
        mask = np.ones(image_bgr.shape[:2], dtype=np.float32)
            
    return mask

def refine_semantic_mask(mask, smooth_sigma=10.0):
    """
    Refine the binary mask to ensure smooth transitions
    during the abstraction blending process.
    """
    # Smooth the mask to prevent harsh artifact lines at the subject boundary
    if smooth_sigma > 0:
        ksize = int(2 * np.ceil(2 * smooth_sigma) + 1)
        mask = cv2.GaussianBlur(mask, (ksize, ksize), smooth_sigma)
        
    return np.clip(mask, 0.0, 1.0)

def compute_semantic_saliency(image_bgr, smooth_sigma=10.0):
    """
    Computes the advanced saliency map.
    """
    raw_mask = get_advanced_saliency(image_bgr)
    refined_mask = refine_semantic_mask(raw_mask, smooth_sigma)
    return refined_mask
