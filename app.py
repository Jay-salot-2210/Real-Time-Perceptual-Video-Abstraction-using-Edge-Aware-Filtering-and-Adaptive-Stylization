"""
Phase 3 Semantic Focal Abstraction Web App
A Streamlit application for artistic image abstraction with semantic foreground/background separation.
"""

import streamlit as st
import cv2
import numpy as np
import os
import sys
from io import BytesIO
from PIL import Image

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase1_paper_implementation'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase2_novelty'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase3_deep_semantic'))

from semantic_pipeline import semantic_pipeline

# Page configuration
st.set_page_config(
    page_title="Semantic Focal Abstraction",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetic styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTitle {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 5px solid #667eea;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .result-container {
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .image-label {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1rem;
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("# 🎨 Semantic Focal Abstraction")
st.markdown("### Transform your photos into artistic abstractions with intelligent foreground-background separation")

# Sidebar for controls
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    
    st.markdown("### Bilateral Filter Parameters")
    n_bilateral = st.slider("Iterations", min_value=2, max_value=8, value=4, 
                            help="More iterations = more abstraction (slower processing)")
    sigma_d = st.slider("Spatial Sigma (σ_d)", min_value=1.0, max_value=8.0, value=3.0, step=0.5,
                        help="Controls the spatial extent of the bilateral filter")
    sigma_r_fg = st.slider("Foreground Detail (σ_r_fg)", min_value=0.5, max_value=5.0, value=2.0, step=0.5,
                           help="Lower = preserve more foreground detail")
    sigma_r_bg = st.slider("Background Blur (σ_r_bg)", min_value=8.0, max_value=20.0, value=14.0, step=1.0,
                           help="Higher = more background abstraction")
    
    st.markdown("### Quantization Parameters")
    k_fg = st.slider("Foreground Colors (k_fg)", min_value=8, max_value=32, value=16, step=2,
                     help="Number of colors in the foreground")
    k_bg = st.slider("Background Colors (k_bg)", min_value=1, max_value=8, value=2, step=1,
                     help="Number of colors in the background (lower = more artistic)")
    
    st.markdown("### Edge Detection")
    sigma_e = st.slider("Edge Sigma (σ_e)", min_value=0.5, max_value=3.0, value=1.0, step=0.25,
                        help="Controls edge detection sensitivity")
    fg_edge_str = st.slider("Foreground Edge Strength", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    bg_edge_str = st.slider("Background Edge Strength", min_value=0.0, max_value=1.0, value=0.0, step=0.1,
                            help="Keep at 0 for clean background")

# Main content
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<p class="image-label">📤 Upload Your Image</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png", "bmp"],
        help="Supported formats: JPG, PNG, BMP"
    )

with col2:
    st.markdown('<p class="image-label">💡 Tips</p>', unsafe_allow_html=True)
    st.markdown("""
    - **Best results**: Images with clear subjects and backgrounds
    - **Portrait photos**: Excellent for people with distinct backgrounds
    - **Landscape**: Works well with textured foregrounds
    - **Avoid**: Very small images (< 300px), very cluttered scenes
    """)

st.markdown("---")

if uploaded_file is not None:
    # Read and process the image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # Display input image info
    st.markdown("### 📊 Image Information")
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Dimensions", f"{img_bgr.shape[1]} × {img_bgr.shape[0]}")
    with col_info2:
        st.metric("Format", uploaded_file.type.split("/")[-1].upper())
    with col_info3:
        st.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
    
    # Process button
    st.markdown("---")
    process_button = st.button(
        "🚀 Generate Abstract Art",
        use_container_width=True,
        type="primary"
    )
    
    if process_button:
        with st.spinner("✨ Creating artistic abstraction... (this may take a moment)"):
            try:
                # Run the semantic pipeline
                results = semantic_pipeline(
                    img_bgr,
                    n_bilateral=n_bilateral,
                    sigma_d=sigma_d,
                    sigma_r_fg=sigma_r_fg,
                    sigma_r_bg=sigma_r_bg,
                    k_fg=k_fg,
                    k_bg=k_bg,
                    sigma_e=sigma_e,
                    fg_edge_str=fg_edge_str,
                    bg_edge_str=bg_edge_str
                )
                
                final_image = cv2.cvtColor(results['final'], cv2.COLOR_BGR2RGB)
                semantic_mask = results['semantic_mask']
                
                # Display results
                st.markdown("---")
                st.markdown("### ✅ Processing Complete!")
                
                # Results visualization
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.markdown('<p class="image-label">Original Image</p>', unsafe_allow_html=True)
                    st.image(img_rgb, use_column_width=True)
                
                with res_col2:
                    st.markdown('<p class="image-label">🎨 Abstract Result</p>', unsafe_allow_html=True)
                    st.image(final_image, use_column_width=True)
                
                # Semantic mask visualization
                st.markdown("---")
                col_mask1, col_mask2 = st.columns(2)
                
                with col_mask1:
                    st.markdown('<p class="image-label">Semantic Segmentation Mask</p>', unsafe_allow_html=True)
                    st.image((semantic_mask * 255).astype(np.uint8), 
                            use_column_width=True, 
                            clamp=True,
                            caption="White = Foreground, Black = Background")
                
                with col_mask2:
                    st.markdown('<p class="image-label">Processing Details</p>', unsafe_allow_html=True)
                    st.info(f"""
                    **Pipeline Configuration:**
                    - Iterations: {n_bilateral}
                    - Foreground colors: {k_fg}, Background colors: {k_bg}
                    - Foreground blur: σ_r={sigma_r_fg}, Background blur: σ_r={sigma_r_bg}
                    - Edge detection sensitivity: σ_e={sigma_e}
                    """)
                
                # Download buttons
                st.markdown("---")
                st.markdown("### 📥 Download Results")
                
                col_down1, col_down2, col_down3 = st.columns(3)
                
                # Convert images to PIL for saving
                pil_final = Image.fromarray(final_image)
                pil_original = Image.fromarray(img_rgb)
                pil_mask = Image.fromarray((semantic_mask * 255).astype(np.uint8))
                
                # Download abstract image
                buf_final = BytesIO()
                pil_final.save(buf_final, format="PNG")
                buf_final.seek(0)
                with col_down1:
                    st.download_button(
                        label="🎨 Abstract Image",
                        data=buf_final,
                        file_name="abstract_result.png",
                        mime="image/png",
                        use_container_width=True
                    )
                
                # Download mask
                buf_mask = BytesIO()
                pil_mask.save(buf_mask, format="PNG")
                buf_mask.seek(0)
                with col_down2:
                    st.download_button(
                        label="🎯 Segmentation Mask",
                        data=buf_mask,
                        file_name="segmentation_mask.png",
                        mime="image/png",
                        use_container_width=True
                    )
                
                # Download comparison
                with col_down3:
                    # Create side-by-side comparison
                    h, w = img_rgb.shape[:2]
                    comparison = np.hstack([img_rgb, final_image])
                    pil_comparison = Image.fromarray(comparison)
                    buf_comparison = BytesIO()
                    pil_comparison.save(buf_comparison, format="PNG")
                    buf_comparison.seek(0)
                    st.download_button(
                        label="📊 Comparison",
                        data=buf_comparison,
                        file_name="comparison.png",
                        mime="image/png",
                        use_container_width=True
                    )
                
            except Exception as e:
                st.error(f"❌ Error processing image: {str(e)}")
                st.info("Please try with a different image or adjust the parameters.")

# Info section at the bottom
st.markdown("---")
st.markdown("""
<div class="info-box">
    <strong>🔍 About Semantic Focal Abstraction</strong><br>
    This application uses advanced computer vision techniques to separate your image into foreground and background regions,
    applying different levels of artistic abstraction to each. The result is a striking depth-of-field effect that makes your subject
    stand out while transforming the background into a stylized, cartoon-like representation.
    <br><br>
    <strong>Research:</strong> Dhirubhai Ambani University | <strong>Advisor:</strong> Dr. Srimanta Mandal (IIT Mandi)
</div>
""", unsafe_allow_html=True)
