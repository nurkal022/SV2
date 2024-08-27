import streamlit as st
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Leonardo API key constant
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

def analyze_text(text):
    messages = [
        {"role": "system", "content": "You are an experienced screenwriter and director. Analyze the following text and identify 5-7 key scenes for a storyboard. For each scene, provide:\n1. A brief description of the scene (2-3 sentences)\n2. A detailed visual prompt for image generation (4-5 sentences)\n3. Key elements that should be in the frame"},
        {"role": "user", "content": text}
    ]
    
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    return completion.choices[0].message.content

def generate_image_leonardo(prompt):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {LEONARDO_API_KEY}"
    }
    payload = {
        "prompt": prompt,
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
    st.markdown("Transform your text into a visual storyboard with AI-powered scene analysis and image generation.")

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            text_input = st.text_area("Enter your story or script here:", height=200)
        with col2:
            st.markdown("### How it works:")
            st.markdown("1. Enter your text in the box")
            st.markdown("2. Click 'Analyze and Visualize'")
            st.markdown("3. AI will identify key scenes")
            st.markdown("4. Images will be generated for each scene")
    
    if st.button("Analyze and Visualize", key="analyze_button"):
        if text_input:
            with st.spinner("🔍 Analyzing your story..."):
                analysis = analyze_text(text_input)
            
            scenes = analysis.split("\n\n")
            
            for i, scene in enumerate(scenes):
                with st.expander(f"Scene {i+1}", expanded=True):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown(f"**Description:**")
                        st.write(scene.split("Visual prompt:")[0].strip())
                        
                        prompt_start = scene.find("Visual prompt:") + len("Visual prompt:")
                        prompt_end = scene.find("Key elements:")
                        if prompt_start != -1 and prompt_end != -1:
                            prompt = scene[prompt_start:prompt_end].strip()
                            
                            st.markdown(f"**Visual Prompt:**")
                            st.write(prompt)
                    
                    with col2:
                        with st.spinner(f"🎨 Generating image for scene {i+1}..."):
                            image = generate_image_leonardo(prompt)
                        
                        if image:
                            st.image(image, caption=f"Visualization for scene {i+1}", use_column_width=True)
                        else:
                            st.error("Failed to generate image for this scene.")
                    
                    st.markdown(f"**Key Elements:**")
                    st.write(scene.split("Key elements:")[-1].strip())

    st.markdown("---")
    st.markdown("Powered by OpenAI GPT-4 and Leonardo AI")

if __name__ == "__main__":
    main()