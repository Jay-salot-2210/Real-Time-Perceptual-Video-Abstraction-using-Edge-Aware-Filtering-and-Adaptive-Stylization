"""
Hyperparameter Tuning & Experimentation Script

This script runs Phase 1, Phase 2, and Phase 3 with different parameter sets,
saves the output images, and logs the metrics for analysis.
"""

import cv2
import os
import urllib.request
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase1_paper_implementation'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase2_novelty'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase3_deep_semantic'))

from pipeline import abstract_pipeline as p1_pipeline
from enhanced_pipeline import enhanced_pipeline as p2_pipeline
from semantic_pipeline import semantic_pipeline as p3_pipeline

def run_experiments():
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(project_root, "results", "experiments")
    os.makedirs(output_dir, exist_ok=True)
    
    test_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/messi5.jpg"
    test_img_path = os.path.join(output_dir, "test_input.jpg")
    
    if not os.path.exists(test_img_path):
        print("Downloading test image...")
        req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(test_img_path, 'wb') as out_file:
            out_file.write(response.read())
            
    img = cv2.imread(test_img_path)
    
    print("=== Phase 1: Tuning Bilateral Filter Iterations & Quantization Bins ===")
    p1_params = [
        {"n_bilateral": 2, "n_bins": 8},   # Under-abstracted
        {"n_bilateral": 4, "n_bins": 8},   # Paper default
        {"n_bilateral": 8, "n_bins": 4}    # Over-abstracted
    ]
    for idx, params in enumerate(p1_params):
        print(f"Running P1 Exp {idx+1}: {params}")
        res = p1_pipeline(img, n_bilateral=params["n_bilateral"], n_bins=params["n_bins"])
        cv2.imwrite(os.path.join(output_dir, f"p1_exp{idx+1}_b{params['n_bilateral']}_q{params['n_bins']}.png"), res['final'])
        
    print("\n=== Phase 2: Tuning K-Means Colors & Saliency Weights ===")
    p2_params = [
        {"n_colors": 4, "w_gradient": 0.8, "w_color": 0.2}, # Extreme posterization, gradient focused
        {"n_colors": 8, "w_gradient": 0.6, "w_color": 0.4}, # Balanced (Default)
        {"n_colors": 16, "w_gradient": 0.2, "w_color": 0.8} # High color fidelity, color focused
    ]
    for idx, params in enumerate(p2_params):
        print(f"Running P2 Exp {idx+1}: {params}")
        res = p2_pipeline(img, n_colors=params["n_colors"], w_gradient=params["w_gradient"], w_color=params["w_color"])
        cv2.imwrite(os.path.join(output_dir, f"p2_exp{idx+1}_k{params['n_colors']}.png"), res['final'])
        
    print("\n=== Phase 3: Tuning Semantic Guided Focal Abstraction ===")
    p3_params = [
        # Exp 1: Mild depth-of-field effect
        {"sigma_r_bg": 6.0, "k_fg": 16, "k_bg": 8, "bg_edge_str": 0.5},
        # Exp 2: Strong depth-of-field (Default)
        {"sigma_r_bg": 10.0, "k_fg": 16, "k_bg": 4, "bg_edge_str": 0.2},
        # Exp 3: Extreme isolation (BG completely washed out)
        {"sigma_r_bg": 20.0, "k_fg": 32, "k_bg": 2, "bg_edge_str": 0.0}
    ]
    for idx, params in enumerate(p3_params):
        print(f"Running P3 Exp {idx+1}: {params}")
        res = p3_pipeline(img, 
                          sigma_r_bg=params["sigma_r_bg"], 
                          k_fg=params["k_fg"], 
                          k_bg=params["k_bg"], 
                          bg_edge_str=params["bg_edge_str"])
        cv2.imwrite(os.path.join(output_dir, f"p3_exp{idx+1}_bgblur{params['sigma_r_bg']}_kfg{params['k_fg']}.png"), res['final'])

    print("\nExperiments complete. Check results/experiments/ folder.")

if __name__ == "__main__":
    run_experiments()
