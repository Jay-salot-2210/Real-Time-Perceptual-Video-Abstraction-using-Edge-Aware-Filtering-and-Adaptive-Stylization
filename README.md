# Real-Time Perceptual Video Abstraction using Edge-Aware Filtering and Adaptive Stylization

## Overview

This project implements and extends the paper:

> Winnemöller, H., Olsen, S. C., & Gooch, B. (2006)
> "Real-Time Video Abstraction"

The system transforms real-world videos into perceptually simplified and stylized representations while preserving important visual structures such as edges, object boundaries, and facial features.

The project focuses on:
- Real-time abstraction
- Edge-preserving smoothing
- Cartoon-like stylization
- Temporal stability in video
- Enhanced perceptual clarity

The implementation is divided into two phases:
1. Reproduction of the original paper pipeline
2. Novel improvements and extensions

---

# Motivation

Natural images contain excessive fine texture, noise, and visual clutter that may reduce perceptual clarity in low-bandwidth transmission, fast recognition, or memory-oriented tasks.

This project explores how visual abstraction can:
- Reduce unnecessary detail
- Preserve semantic structures
- Improve visual perception
- Create temporally stable stylized videos

Applications include:
- Low-bandwidth video streaming
- Artistic video rendering
- AR/VR preprocessing
- Perception enhancement systems
- Mobile graphics optimization
- Cartoon and animation filters

---

# Features

## Phase 1 — Paper Implementation

### 1. Bilateral Filtering
- Edge-preserving smoothing
- Iterative abstraction
- Mimics anisotropic diffusion
- Removes texture while preserving boundaries

### 2. Difference-of-Gaussians (DoG) Edge Enhancement
- Enhances visually important edges
- Retina-inspired edge detection
- Produces stylized contours

### 3. Soft Color Quantization
- Reduces color complexity
- Produces cartoon-like appearance
- Maintains temporal stability

### 4. Real-Time Video Processing
- Frame-by-frame abstraction
- Live webcam or video input support
- Optimized using OpenCV

---

## Phase 2 — Proposed Improvements

### 1. Adaptive Quantization
- K-means based dynamic color clustering
- Better scene adaptation
- Improved stylization quality

### 2. Saliency-Guided Abstraction
- Uses gradient magnitude maps
- Preserves perceptually important regions
- Better edge awareness

### 3. Enhanced Edge Detection
Optional:
- Holistically-Nested Edge Detection (HED)
- Cleaner contours
- Better object boundary extraction

### 4. Quantitative Evaluation
Evaluation metrics include:
- SSIM (Structural Similarity Index)
- PSNR (Peak Signal-to-Noise Ratio)
- Processing FPS
- Edge preservation score

---

# System Architecture

Input Video/Image
        ↓
Bilateral Filtering
        ↓
Difference-of-Gaussians Edge Extraction
        ↓
Color Quantization
        ↓
Saliency Enhancement (Phase 2)
        ↓
Final Abstracted Output

---

## Project Structure

```text
project/
├── phase1_paper_implementation/
│   ├── bilateral_abstraction.py
│   ├── dog_edges.py
│   ├── soft_quantization.py
│   └── pipeline.py
│
├── phase2_novelty/
│   ├── adaptive_quantization.py
│   ├── saliency_guided.py
│   └── enhanced_pipeline.py
│
├── datasets/
│   ├── input_videos/
│   └── sample_images/
│
├── results/
│   ├── images/
│   ├── videos/
│   └── metrics/
│
├── report/
│   └── report.tex
│
├── README.md
└── requirements.txt
```
---

# Technologies Used

## Programming Language
- Python 3.10+

## Libraries
- OpenCV
- NumPy
- SciPy
- scikit-image
- scikit-learn
- matplotlib
- imutils

Optional:
- PyTorch
- OpenCV DNN module

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/video-abstraction.git
cd video-abstraction
