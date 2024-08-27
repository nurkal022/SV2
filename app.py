import streamlit as st
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

def analyze_text(text):
    messages = [
        {"role": "system", "content": """You are an experienced screenwriter and director. Analyze the following text and identify 5-7 key scenes for a storyboard. Provide your analysis in the following JSON format:

{
  "style_guide": {
    "color_palette": ["color1", "color2", "color3"],
    "mood": "overall mood description",
    "artistic_style": "style description",
    "recurring_elements": ["element1", "element2"]
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

def generate_image_leonardo(frame_description, style_guide):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}"
    }
    style_guide_text = f"Style: {style_guide['artistic_style']}. Mood: {style_guide['mood']}. Color palette: {', '.join(style_guide['color_palette'])}. Recurring elements: {', '.join(style_guide['recurring_elements'])}."
    full_prompt = f"{style_guide_text}\n\nFrame description: {frame_description}"
    payload = {
        "prompt": full_prompt,
        "modelId": "ac614f96-1082-45bf-be9d-757f2d31c174",
        "width": 512,
        "height": 512,
        "num_images": 1,
        "promptMagic": True,
        "public": False
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        generation_id = response.json()['sdGenerationJob']['generationId']
        while True:
            status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            status_response = requests.get(status_url, headers=headers)
            
            if status_response.status_code == 200:
                generation_data = status_response.json()['generations_by_pk']
                if generation_data['status'] == 'COMPLETE':
                    image_url = generation_data['generated_images'][0]['url']
                    return Image.open(BytesIO(requests.get(image_url).content))
    return None

def main():
    st.set_page_config(page_title="StoryVision", page_icon="🎬", layout="wide")
    
    st.title("🎬 StoryVision")
    st.markdown("Transform your text into a cohesive visual storyboard with AI-powered scene analysis and image generation.")

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            text_input = st.text_area("Enter your story or script here:", height=200)
        with col2:
            st.markdown("### How it works:")
            st.markdown("1. Enter your text in the box")
            st.markdown("2. Click 'Analyze and Visualize'")
            st.markdown("3. AI will identify key scenes and create a style guide")
            st.markdown("4. Detailed frame descriptions will be generated for each scene")
            st.markdown("5. Images will be created based on these specific frame descriptions")
    
    if st.button("Analyze and Visualize", key="analyze_button"):
        if text_input:
            with st.spinner("🔍 Analyzing your story and creating a style guide..."):
                analysis = analyze_text(text_input)
            
            style_guide = analysis['style_guide']
            scenes = analysis['scenes']
            
            st.subheader("Style Guide")
            st.write(f"Color Palette: {', '.join(style_guide['color_palette'])}")
            st.write(f"Mood: {style_guide['mood']}")
            st.write(f"Artistic Style: {style_guide['artistic_style']}")
            st.write(f"Recurring Elements: {', '.join(style_guide['recurring_elements'])}")
            
            for i, scene in enumerate(scenes):
                with st.expander(f"Scene {i+1}", expanded=True):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"**Scene Description:**")
                        st.write(scene['description'])
                        
                        st.markdown(f"**Frame Description:**")
                        st.write(scene['frame_description'])
                    
                    with col2:
                        with st.spinner(f"🎨 Generating image for scene {i+1}..."):
                            image = generate_image_leonardo(scene['frame_description'], style_guide)
                        
                        if image:
                            st.image(image, caption=f"Visualization for scene {i+1}", use_column_width=True)
                        else:
                            st.error("Failed to generate image for this scene.")
                    
                    st.markdown(f"**Key Elements:**")
                    st.write(", ".join(scene['key_elements']))

    st.markdown("---")
    st.markdown("Powered by OpenAI GPT-4 and Leonardo AI")

if __name__ == "__main__":
    main()