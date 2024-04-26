import base64
import io
import random
import time
from typing import List
from PIL import Image
import aiohttp
import asyncio
import requests
import streamlit as st
import requests
import zipfile
import io
import pandas as pd
from utils import icon
from streamlit_image_select import image_select
from PIL import Image
import random
import time
import base64
from typing import List
import aiohttp
import asyncio
import plotly.express as px
from common import set_page_container_style


def pil_image_to_base64(image: Image.Image) -> str:
    image_stream = io.BytesIO()
    image.save(image_stream, format="PNG")
    base64_image = base64.b64encode(image_stream.getvalue()).decode("utf-8")

    return base64_image


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()
# convert this config to dict
# 1:1 (square): 512x512, 768x768
# 3:2 (landscape): 768x512
# 2:3 (portrait): 512x768
# 4:3 (landscape): 768x576
# 3:4 (portrait): 576x768
# 16:9 (widescreen): 912x512
# 9:16 (tall): 512x912

sd_ratio_to_size = {
    "1:1": (512, 512),
    "3:2": (768, 512),
    "2:3": (512, 768),
    "4:3": (768, 576),
    "3:4": (576, 768),
    "16:9": (912, 512),
    "9:16": (512, 912),
}

# 1:1 (square): 1024x1024, 768x768
# 3:2 (landscape): 1152x768
# 2:3 (portrait): 768x1152
# 4:3 (landscape): 1152x864
# 3:4 (portrait): 864x1152
# 16:9 (widescreen): 1360x768
# 9:16 (tall): 768x1360

sdxl_ratio_to_size = {
    "1:1": (1024, 1024),
    "3:2": (1152, 768),
    "2:3": (768, 1152),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
    "16:9": (1360, 768),
    "9:16": (768, 1360),
}

model_config = {
    "RealisticVision": {
        "ratio": sd_ratio_to_size,
        "num_inference_steps": 30,
        "guidance_scale": 7.0,
        "clip_skip": 2,
    },
    "AnimeV3": {
        "num_inference_steps": 25,
        "guidance_scale": 7,
        "clip_skip": 2,
        "ratio": sdxl_ratio_to_size
    },
    "DreamShaper": {
        "num_inference_steps": 35,
        "guidance_scale": 7,
        "clip_skip": 2,
        "ratio": sd_ratio_to_size,
    },
    "RealitiesEdgeXL": {
        "num_inference_steps": 7,
        "guidance_scale": 1,
        "clip_skip": 2,
        "ratio": sdxl_ratio_to_size,
    },
}


def base64_to_image(base64_string):
    return Image.open(io.BytesIO(base64.b64decode(base64_string)))


async def call_niche_api(url, data) -> List[Image.Image]:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(64)) as session:
            async with session.post(url, json=data) as response:
                response = await response.json()
            if isinstance(response, dict):
                response = response["image"]
            else:
                response = response
        return base64_to_image(response)
    except Exception as e:
        print(e)
        return None


async def get_output(url, datas):
    tasks = [asyncio.create_task(call_niche_api(url, data)) for data in datas]
    return await asyncio.gather(*tasks)


async def main_page(
    submitted: bool,
    model_name: str,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
    num_images: int,
    uid: str,
    secret_key: str,
    seed: str,
    conditional_image: str,
    controlnet_conditioning_scale: list,
    pipeline_type: str,
    api_token: str,
    generated_images_placeholder,
) -> None:
    """Main page layout and logic for generating images.

    Args:
        submitted (bool): Flag indicating whether the form has been submitted.
        width (int): Width of the output image.
        height (int): Height of the output image.
        num_inference_steps (int): Number of denoising steps.
        guidance_scale (float): Scale for classifier-free guidance.
        prompt_strength (float): Prompt strength when using img2img/inpaint.
        prompt (str): Text prompt for the image generation.
        negative_prompt (str): Text prompt for elements to avoid in the image.
    """
    if submitted:
        if secret_key != api_token and uid != "-1":
            st.error("Invalid secret key")
            return
        try:
            uid = int(uid)
        except ValueError:
            uid = -1
        width, height = model_config[model_name]["ratio"][aspect_ratio.lower()]
        width = int(width)
        height = int(height)
        num_inference_steps = model_config[model_name]["num_inference_steps"]
        guidance_scale = model_config[model_name]["guidance_scale"]

        with st.status(
            "👩🏾‍🍳 Whipping up your words into art...", expanded=True
        ) as status:
            try:
                # Only call the API if the "Submit" button was pressed
                if submitted:
                    start_time = time.time()
                    # Calling the replicate API to get the image
                    with generated_images_placeholder.container():
                        try:
                            seed = int(seed)
                        except ValueError:
                            seed = -1
                        if seed >= 0:
                            seeds = [int(seed) + i for i in range(num_images)]
                        else:
                            seeds = [random.randint(0, 1e9) for _ in range(num_images)]
                        all_images = []  # List to store all generated images
                        data = {
                            "key": api_token,
                            "prompt": prompt,  # prompt
                            "model_name": model_name,  # See avaialble models in https://github.com/NicheTensor/NicheImage/blob/main/configs/model_config.yaml
                            "seed": seed,  # -1 means random seed
                            "miner_uid": int(
                                uid
                            ),  # specify miner uid, -1 means random miner selected by validator
                            "pipeline_type": pipeline_type,
                            "conditional_image": conditional_image,
                            "pipeline_params": {  # params feed to diffusers pipeline, see all params here https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img#diffusers.StableDiffusionPipeline.__call__
                                "width": width,
                                "height": height,
                                "num_inference_steps": num_inference_steps,
                                "guidance_scale": guidance_scale,
                                "negative_prompt": negative_prompt,
                                "controlnet_conditioning_scale": controlnet_conditioning_scale,
                                "clip_skip": model_config[model_name]["clip_skip"],
                            },
                        }
                        duplicate_data = [data.copy() for _ in range(num_images)]
                        for i, d in enumerate(duplicate_data):
                            d["seed"] = seeds[i]
                        # Call the NicheImage API
                        loop = get_or_create_eventloop()
                        asyncio.set_event_loop(loop)
                        tasks = [
                            get_output(
                                "http://proxy_client_nicheimage.nichetensor.com:10003/generate",
                                [d],
                            )
                            for d in duplicate_data
                        ]
                        line_1, line_2 = st.columns(2)
                        for i, task in enumerate(asyncio.as_completed(tasks)):
                            
                            output = await task
                            if output:
                                image = output[0]
                            else:
                                image = Image.new("RGB", (width, height), (0, 0, 0))
                            all_images.append(image)
                            if i % 2 == 0:
                                with line_1:
                                    st.image(
                                        image,
                                        caption=f"Image {i+1} 🎈",
                                        use_column_width=True,
                                        output_format="JPEG",
                                    )
                            else:
                                with line_2:
                                    st.image(
                                        image,
                                        caption=f"Image {i+1} 🎈",
                                        use_column_width=True,
                                        output_format="JPEG",
                                    )
                        end_time = time.time()

                        # Save all generated images to session state
                        st.session_state.all_images = all_images
                        zip_io = io.BytesIO()
                        # Download option for each image
                        with zipfile.ZipFile(zip_io, "w") as zipf:
                            for i, image in enumerate(st.session_state.all_images):
                                image_data = io.BytesIO()
                                image.save(image_data, format="PNG")
                                image_data.seek(0)
                                # Write each image to the zip file with a name
                                zipf.writestr(
                                    f"output_file_{i+1}.png", image_data.read()
                                )
                        # Create a download button for the zip file
                        st.download_button(
                            ":red[**Download All Images**]",
                            data=zip_io.getvalue(),
                            file_name="output_files.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
                status.update(
                    label=f"✅ Images generated in {round(end_time-start_time, 3)} seconds", state="complete", expanded=False
                )
            except Exception as e:
                print(e)
                st.error(f"Encountered an error: {e}", icon="🚨")

    # If not submitted, chill here 🍹
    else:
        pass
