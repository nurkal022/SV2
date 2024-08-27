import streamlit as st
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
import json

# Set page config at the very beginning
st.set_page_config(page_title="StoryVision", page_icon="🎬", layout="wide")

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Custom CSS to enhance the UI
st.markdown("""
<style>
    .stApp {
        background-color: #f0f0f0;
    }
    .main-title {
        font-size: 3rem;
        color: #1e1e1e;
        text-align: center;
        padding: 2rem 0;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .scene-title {
        font-size: 1.5rem;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .scene-description {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .style-guide {
        background-color: #e8f4f8;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    .regenerate-button {
        border-radius: 20px;
        border: none;
        color: white;
        background-color: #3498db;
        padding: 0.5rem 1rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        transition-duration: 0.4s;
    }
    .regenerate-button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

def analyze_text(text):
    messages = [
        {"role": "system", "content": """You are an experienced screenwriter and director. Analyze the following text and identify 5-7 key scenes for a storyboard. Provide your analysis in the following JSON format:

{
  "style_guide": {
    "color_palette": ["color1", "color2", "color3"],
    "mood": "overall mood description",
    "artistic_style": "style description"
  },
  "scenes": [
    {
      "description": "Brief scene description",
      "frame_description": "Detailed description of a single frame from this scene, including specific objects, characters, their positions, expressions, lighting, and any other visual details",
      "key_elements": ["element1", "element2", "element3"]
    },
    ...
  ]
}

Ensure that each scene has all required fields filled out. The frame_description should be very specific, as if describing a single photograph or film frame from the scene."""},
        {"role": "user", "content": text}
    ]
    
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    return json.loads(completion.choices[0].message.content)

def generate_image_dalle(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return Image.open(BytesIO(requests.get(image_url).content))
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

def create_scene_prompt(style_guide, scene):
    style_guide_text = f"Artistic Style: {style_guide['artistic_style']}. Mood: {style_guide['mood']}. Color palette: {', '.join(style_guide['color_palette'])}."
    scene_specific_elements = ", ".join(scene['key_elements'])
    full_prompt = f"{style_guide_text}\n\nScene-specific elements: {scene_specific_elements}\n\nFrame description: {scene['frame_description']}"
    return full_prompt

def main():
    st.markdown("<h1 class='main-title'>🎬 StoryVision</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Transform your text into a visual storyboard with AI-powered scene analysis and image generation.</p>", unsafe_allow_html=True)

    if 'analysis' not in st.session_state:
        st.session_state.analysis = None

    text_input = st.text_area("Enter your story or script here:", height=200)
    
    if st.button("Analyze and Visualize", key="analyze_button"):
        if text_input:
            with st.spinner("🔍 Analyzing your story and creating a visual storyboard..."):
                st.session_state.analysis = analyze_text(text_input)
    
    if st.session_state.analysis:
        style_guide = st.session_state.analysis['style_guide']
        scenes = st.session_state.analysis['scenes']
        
        st.markdown("<div class='style-guide'>", unsafe_allow_html=True)
        st.subheader("Style Guide")
        st.write(f"🎨 Color Palette: {', '.join(style_guide['color_palette'])}")
        st.write(f"🌟 Mood: {style_guide['mood']}")
        st.write(f"🖼️ Artistic Style: {style_guide['artistic_style']}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        for i, scene in enumerate(scenes):
            st.markdown(f"<h2 class='scene-title'>Scene {i+1}</h2>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("<div class='scene-description'>", unsafe_allow_html=True)
                st.markdown(f"**Scene Description:**")
                st.write(scene['description'])
                
                st.markdown(f"**Key Elements:**")
                st.write(", ".join(scene['key_elements']))
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                full_prompt = create_scene_prompt(style_guide, scene)
                
                if f'image_{i}' not in st.session_state:
                    with st.spinner(f"🎨 Generating image for scene {i+1}..."):
                        st.session_state[f'image_{i}'] = generate_image_dalle(full_prompt)
                
                image_placeholder = st.empty()
                if st.session_state[f'image_{i}']:
                    image_placeholder.image(st.session_state[f'image_{i}'], caption=f"Visualization for scene {i+1}", use_column_width=True)
                else:
                    image_placeholder.error("Failed to generate image for this scene.")
                
                if st.button(f"Regenerate Image", key=f"regenerate_{i}"):
                    with st.spinner(f"🎨 Regenerating image for scene {i+1}..."):
                        new_image = generate_image_dalle(full_prompt)
                        if new_image:
                            st.session_state[f'image_{i}'] = new_image
                            image_placeholder.image(new_image, caption=f"Visualization for scene {i+1}", use_column_width=True)
                            st.success(f"Image for Scene {i+1} has been regenerated.")

    st.markdown("---")
    st.markdown("<p style='text-align: center;'>Powered by OpenAI GPT-4 and DALL-E 3</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()