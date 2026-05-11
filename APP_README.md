# Semantic Focal Abstraction Web App

A beautiful, fully-featured Streamlit web application for artistic image abstraction with intelligent foreground/background separation.

## 🎨 Features

- **Aesthetic UI** with gradient colors and smooth animations
- **Real-time image processing** with semantic segmentation
- **Configurable parameters** for customizing the artistic effect
- **Side-by-side comparison** of original and processed images
- **Semantic mask visualization** showing foreground/background separation
- **Multiple download options** (abstract image, mask, comparison)
- **Mobile responsive** design
- **Free deployment** on Streamlit Cloud

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.8+
- pip

### Setup & Run

```bash
# 1. Navigate to project directory
cd c:\Users\Jay\Desktop\DAU\SEM-2\AIP\Project

# 2. Install Streamlit (if not already installed)
pip install streamlit

# 3. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

## ☁️ Free Deployment (Streamlit Cloud)

### Super Easy - Just 3 Steps!

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Semantic Focal Abstraction web app"
   git push origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Click "Create app"
   - Select your GitHub repo and `app.py`

3. **Done!** 🎉
   - Your app is live at: `https://yourapp.streamlit.app`
   - Share the link with anyone!

**No credit card required. Completely free forever.**

## 📚 How It Works

The app uses three phases of image processing:

1. **Phase 1**: Iterative bilateral filtering (from original paper)
2. **Phase 2**: Saliency-guided adaptive abstraction
3. **Phase 3**: Semantic focal abstraction with hardened foreground/background separation

## ⚙️ Configuration Parameters

### Bilateral Filter
- **Iterations**: Number of filtering passes (higher = more abstraction)
- **Spatial Sigma (σ_d)**: Spatial extent of the filter
- **Foreground/Background Detail**: Control detail preservation vs abstraction

### Quantization
- **Foreground Colors**: Number of colors in foreground (8-32)
- **Background Colors**: Number of colors in background (1-8)

### Edge Detection
- **Edge Sigma**: Sensitivity of edge detection
- **Edge Strength**: How visible edges are in foreground/background

## 📊 Recommended Settings

### Portraits
- Iterations: 4
- Foreground Colors: 16
- Background Colors: 2

### Landscapes
- Iterations: 6
- Foreground Colors: 20
- Background Colors: 3

### Artistic/Extreme
- Iterations: 8
- Foreground Colors: 32
- Background Colors: 1

## 🎯 Best For

✅ Portrait photography
✅ Product photography
✅ Face photography
✅ Images with clear subject/background separation

⚠️ May struggle with:
- Very cluttered/complex scenes
- Very small images (< 300px)
- Uniform backgrounds

## 📁 Files Overview

```
├── app.py                          # Main Streamlit web app
├── requirements_streamlit.txt      # Dependencies for deployment
├── DEPLOYMENT.md                   # Detailed deployment guide
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── phase3_deep_semantic/
│   ├── semantic_pipeline.py        # Phase 3 processing
│   └── semantic_saliency.py        # Semantic segmentation
├── phase2_novelty/
│   ├── enhanced_pipeline.py
│   ├── saliency_guided.py
│   └── adaptive_quantization.py
└── phase1_paper_implementation/
    ├── pipeline.py
    ├── bilateral_abstraction.py
    └── dog_edges.py
```

## 🔧 Troubleshooting

**Q: App runs slowly locally**
- Normal for first run, Streamlit caches results
- Processing complex images takes time

**Q: Image too large for upload**
- Max 200MB on Streamlit Cloud (free tier)
- App automatically handles scaling

**Q: Foreground/background separation not working well**
- Try different image or different parameters
- Works best with clear subjects

**Q: How to deploy?**
- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
- Streamlit Cloud is easiest and free

## 📞 Support

For issues with:
- **Streamlit**: https://docs.streamlit.io
- **Code/Algorithm**: Check original paper or Phase 3 documentation
- **Deployment**: See DEPLOYMENT.md

## 🎓 Academic

**Research**: Dhirubhai Ambani University
**Advisor**: Dr. Srimanta Mandal (PhD, IIT Mandi)

Based on: Winnemöller et al. (SIGGRAPH 2006)

## 📜 License

[Add your license here]

---

**Happy abstracting! 🎨✨**
