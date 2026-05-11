import cv2
import matplotlib.pyplot as plt
import os

def stitch_images(img_paths, titles, super_title, save_path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(super_title, fontsize=18, fontweight='bold')
    
    for ax, path, title in zip(axes, img_paths, titles):
        img = cv2.imread(path)
        if img is not None:
            ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            print(f"Warning: Could not read {path}")
        ax.set_title(title, fontsize=14)
        ax.axis('off')
        
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved {save_path}")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    exp_dir = os.path.join(project_root, "results", "experiments")
    report_dir = os.path.join(project_root, "report")
    
    os.makedirs(report_dir, exist_ok=True)
    
    # Phase 1
    p1_paths = [
        os.path.join(exp_dir, "p1_exp1_b2_q8.png"),
        os.path.join(exp_dir, "p1_exp2_b4_q8.png"),
        os.path.join(exp_dir, "p1_exp3_b8_q4.png")
    ]
    p1_titles = [
        "Under-Abstracted\n(2 Iterations, 8 Bins)\nToo photorealistic",
        "Optimal (Default)\n(4 Iterations, 8 Bins)\nBalanced abstraction",
        "Over-Abstracted\n(8 Iterations, 4 Bins)\nJagged edges, lost structure"
    ]
    stitch_images(p1_paths, p1_titles, "Phase 1 Hyperparameter Sweep: Iterations and Color Bins", os.path.join(report_dir, "hyperparam_phase1.png"))
    
    # Phase 2
    p2_paths = [
        os.path.join(exp_dir, "p2_exp1_k4.png"),
        os.path.join(exp_dir, "p2_exp2_k8.png"),
        os.path.join(exp_dir, "p2_exp3_k16.png")
    ]
    p2_titles = [
        "Extreme Posterization\n(k=4, high gradient weight)\nToo stark, preserves noise",
        "Optimal (Default)\n(k=8, balanced weight)\nClean cartoon posterization",
        "High Fidelity\n(k=16, high color weight)\nToo realistic, weak abstraction"
    ]
    stitch_images(p2_paths, p2_titles, "Phase 2 Hyperparameter Sweep: K-Means Colors and Saliency Weights", os.path.join(report_dir, "hyperparam_phase2.png"))
    
    # Phase 3
    p3_paths = [
        os.path.join(exp_dir, "p3_exp1_bgblur6.0_kfg16.png"),
        os.path.join(exp_dir, "p3_exp2_bgblur10.0_kfg16.png"),
        os.path.join(exp_dir, "p3_exp3_bgblur20.0_kfg32.png")
    ]
    p3_titles = [
        "Mild Depth-of-Field\n(BG Blur=6.0, k_bg=8)\nBackground still draws the eye",
        "Optimal (Default)\n(BG Blur=10.0, k_bg=4)\nPerfect focal contrast",
        "Extreme Isolation\n(BG Blur=20.0, k_bg=2)\nUnnatural 'green-screen' effect"
    ]
    stitch_images(p3_paths, p3_titles, "Phase 3 Hyperparameter Sweep: Semantic Focal Isolation", os.path.join(report_dir, "hyperparam_phase3.png"))
