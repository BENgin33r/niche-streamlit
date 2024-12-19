import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import copy
import streamlit.components.v1 as components
from huggingface_hub import snapshot_download, list_repo_files, hf_hub_download
import os, json, random
import graphviz
import datetime

st.set_page_config(page_title="SN23 Dashboard", layout="wide")

st.markdown(
    """
    <div align="center" style="color: blue">

# SocialTensor Subnet <!-- omit in toc -->
[![](https://img.shields.io/badge/bittensor-discord-green?logo=discord)](https://discord.com/channels/799672011265015819/1191833510021955695)
[![](https://img.shields.io/badge/nicheimage-github-blue?logo=github)](https://github.com/SocialTensor/SocialTensorSubnet)

</div>
    """,
     unsafe_allow_html=True
)
tabs = st.tabs(["**Dashboard**", "**Playground**", "**Open Category**"])

with tabs[0]:
    VALID_UIDS = ["202", "1", "28", "58", "78", "127", "133", "159", "161", "178", "181", "183", "189", "227", "228", "244"]
    model_incentive_weight = {
        'AnimeV3': 0.18, 
        'JuggernautXL': 0.15, 
        'RealitiesEdgeXL': 0.19, 
        'Gemma7b': 0.03, 
        'StickerMaker': 0.03, 
        'FaceToMany': 0.00, 
        'Kolors': 0.10, 
        'FluxSchnell': 0.12, 
        'DreamShaperXL': 0.00, 
        'Llama3_70b': 0.05, 
        'GoJourney': 0.04, 
        'SUPIR': 0.08,
        'OpenGeneral': 0.01,
        'OpenDigitalArt': 0.01,
        'Pixtral_12b': 0.01
    }
    COLOR_MAP = {
        'AnimeV3': "#1f77b4", 
        'JuggernautXL': "#ff7f0e", 
        'RealitiesEdgeXL': "#2ca02c", 
        'Gemma7b': "#d62728", 
        'StickerMaker': "#9467bd", 
        'FaceToMany': "#8c564b", 
        'Kolors': "#e377c2", 
        'FluxSchnell': "#bcbd22", 
        'DreamShaperXL': "#7f7f7f", 
        'Llama3_70b': "#f7b6d2", 
        'GoJourney': "#17becf", 
        'SUPIR': "#c5b0d5",
        "": "#ffffcc",
        "OpenGeneral": "#98df8a ",
        "OpenDigitalArt": "#ffbb78",
        "Pixtral_12b": "#373606"
    }

    st.markdown(
        """
        > **NicheImage is a decentralized network of image generation models, powered by the Bittensor protocol. Below you find information about the current models on the network.**
        """,
        unsafe_allow_html=True,
    )

    def get_total_volumes(miner_info_data):
        VALIDATOR_UID = 202
        model_volumes = {}
        model_counts = {}
        info = miner_info_data[str(VALIDATOR_UID)]["info"]
        for uid, metadata in info.items():
            if metadata["model_name"].strip():
                if metadata["model_name"] not in model_volumes:
                    model_volumes[metadata["model_name"]] = 0
                if metadata["model_name"] not in model_counts:
                    model_counts[metadata["model_name"]] = 0
                model_volumes[metadata["model_name"]] += metadata["total_volume"]
                model_counts[metadata["model_name"]] += 1
        return model_volumes, model_counts

    def _get_incentive_weight(catalogue):
        model_incentive_weight = {k:v["model_incentive_weight"] for k,v in catalogue.items()}
        return model_incentive_weight
    
    def get_random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def _assign_color(model_name):
        if model_name not in COLOR_MAP:
            existing_colors = set(COLOR_MAP.values())
            new_color = get_random_color()
            
            while new_color in existing_colors:
                new_color = get_random_color()
            COLOR_MAP[model_name] = new_color
            return new_color
        return COLOR_MAP[model_name]
    
    # if "stats" not in st.session_state:
    response = requests.get("http://storage.nichetensor.com/get_miner_info")
    response = response.json()
    st.session_state.stats = response


    all_validator_response = st.session_state.stats
    model_volumes, model_counts = get_total_volumes(all_validator_response)
    all_validator_response = {k: v for k, v in all_validator_response.items() if str(k) in VALID_UIDS}
    validator_uids = list(all_validator_response.keys())
    validator_uids = [int(uid) for uid in validator_uids]
    validator_uids = sorted(validator_uids)
    print(validator_uids)
    validator_select = st.selectbox(
        "Select a validator",
        validator_uids,
        index=validator_uids.index(202)
    )
    validator_select = str(validator_select)
    response = all_validator_response[validator_select]
    if "catalogue" in response:
        model_incentive_weight = _get_incentive_weight(response["catalogue"])
    # Plot distribution of models
    model_distribution = {}
    for uid, info in response["info"].items():
        model_name = info["model_name"]
        model_distribution[model_name] = model_distribution.get(model_name, 0) + 1

    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]], subplot_titles=("Model Distribution", "Emission Distribution"))
    # Plot Model Distribution
    fig.add_trace(
        go.Pie(
            values=list(model_distribution.values()),
            labels=list(model_distribution.keys()),
            marker=dict(colors=[_assign_color(model) for model in model_distribution.keys()])
        ),
        row=1, col=1
    )
    # Plot Emission Distribution
    fig.add_trace(
        go.Pie(
            values=list(model_incentive_weight.values()),
            labels=list(model_incentive_weight.keys()),
            marker=dict(colors=[_assign_color(model) for model in model_incentive_weight.keys()])
        ),
        row=1, col=2
    )

    fig.update_layout(
        title_text="Distribution",
        width=1000,
        showlegend=True
    )
    st.plotly_chart(fig)

    # Plot volume of models
    models = list(model_volumes.keys())
    volumes = [x * 6 * 24 for x in list(model_volumes.values())]
    organic_volumes = [x * 0.8 for x in volumes]
    volume_per_miners = [volumes[i] / model_counts[model] for i,model in enumerate(models)]
    volume_per_percentage_emission = [volumes[i] / (model_incentive_weight.get(model, 0) * 100)  if model_incentive_weight.get(model, 0) > 0 else 0 for i,model in enumerate(models)]
    total_volume = sum(volumes)
    volumes += [total_volume]
    organic_volumes += [sum(organic_volumes)]
    volume_per_miners += [total_volume / sum(model_counts.values())]
    volume_per_percentage_emission += [total_volume / 100] 

    models += ["<b>Total</b>"]
    formatted_volumes = [f"{volume:,.0f}" for volume in organic_volumes]
    formatted_volumes[-1] = f"<b>{formatted_volumes[-1]}</b>"
    formatted_volume_per_miners = [f"{c:,.2f}" for c in volume_per_miners]
    formatted_volume_per_miners[-1] = f"<b>{formatted_volume_per_miners[-1]}</b>"
    formatted_volume_per_percentage_emission = [f"{c:,.2f}" for c in volume_per_percentage_emission]
    formatted_volume_per_percentage_emission[-1] = f"<b>{formatted_volume_per_percentage_emission[-1]}</b>"

    table = go.Figure(data=[go.Table(
        header=dict(values=["Model", "Generations Per Day*", "Average Volume Per Miner", "Average Volume Per Percentage Emission"],
                    fill_color='#4d79ff',
                    font=dict(color='white', size=16),
                    align='center'),
        cells=dict(
            values=[models, formatted_volumes, formatted_volume_per_miners, formatted_volume_per_percentage_emission],
            fill_color=[['#f0f8ff']*(len(model_volumes)) + ['#d9e6ff'],
                        ['#e6f2ff']*(len(model_volumes)) + ['#d9e6ff'],
                        ['#e6f2ff']*(len(model_volumes)) + ['#d9e6ff'],
                        ['#e6f2ff']*(len(model_volumes)) + ['#d9e6ff']],
            align=['left', 'right', 'right', 'right'], 
            font=dict(color='black', size=14),
            height=30 
        ),
        columnwidth=[25, 25, 25, 25]
    )])

    table.update_layout(
        height=30 * (len(models) + 4),
        width=1000,
        margin=dict(l=0, r=0, t=50, b=0)  # Adjust margins for better title positioning
    )
    st.plotly_chart(table)
    st.markdown(
        "<div style='width:1000px;'><p style='font-size:12px; font-style:italic;'>*Generations per day are calculated by taking the total volume miners say they can generate, and multiply with 0.8, since validators by default utilize about 80% of their available volume of generation.</p></div>",
        unsafe_allow_html=True
    )


    transformed_dict = []
    for k, v in response["info"].items():
        if "process_time" in v:
            process_time = [x for x in v["process_time"] if x >0]
            mean_process_time = sum(process_time) / len(process_time) if len(process_time) > 0 else 0
            success_rate = len(process_time) / len(v["process_time"]) if len(v["process_time"]) > 0 else 1
        else:
            process_time = []
            success_rate = 1
            mean_process_time = 0
        transformed_dict.append(
            {
                "uid": k,
                "model_name": v["model_name"],
                "mean_score": (
                    sum(v["scores"]) / 10
                ),
                "total_volume": v["total_volume"] if  v.get("total_volume") else 0,
                "device_info": v.get("device_info", {}),
                "mean_process_time": mean_process_time,
                "success_rate": success_rate
            }
        )
        
        response["info"][k]["mean_process_time"] = mean_process_time
        response["info"][k]["success_rate"] = success_rate

    transformed_dict = pd.DataFrame(transformed_dict)

    # plot overall chart
    overall_data = copy.deepcopy(response["info"])
    for uid, inf in overall_data.items():
        inf["scores"] = [f"{x:.4f}"for x in inf["scores"]]
        inf["scores"] = ", ".join(inf["scores"])
        inf["success_rate"] = f"{inf['success_rate']:.2f}"
        inf["mean_process_time"] = f"{inf['mean_process_time']:.2f}"
    pd_data = pd.DataFrame(overall_data).T
        
    st.markdown("**Total Information**", unsafe_allow_html=True)
    st.dataframe(pd_data,
        width=1200,
        column_order = ("model_name", "scores", "total_volume", "success_rate", "mean_process_time", "reward_scale", "rate_limit", "device_info"),
        column_config = {
            "scores": st.column_config.ListColumn(
                "Scores",
            ),
            "model_name": st.column_config.TextColumn(
                "Model"
            ),
            "total_volume": st.column_config.ProgressColumn(
                "Volume",
                format="%f",
                min_value=0,
                max_value=1000,
            ),
            "success_rate": st.column_config.ProgressColumn(
                "Success Rate",
                format="%f",
                min_value=0,
                max_value=1
            ),
            "reward_scale": st.column_config.NumberColumn(
                "Reward Scale"
            ),
            "mean_process_time": st.column_config.NumberColumn(
                "Mean Process Time"
            ),
            "rate_limit": st.column_config.NumberColumn(
                "Rate Limit"
            ),
            "device_info": st.column_config.TextColumn("Device Info"),
        })

    # plot N bar chart for N models, sorted by mean score
    for model in model_distribution.keys():
        model_data = transformed_dict[transformed_dict["model_name"] == model]
        model_data = model_data.sort_values(by="mean_score", ascending=False)
        model_data.uid = model_data.uid.astype(str)
        if model_data.mean_score.sum() == 0:
            continue
        fig = go.Figure(data=[go.Bar(x=model_data.uid, y=model_data.mean_score,
                hovertext=[f"Total volume {volume} - {str(device_info)}" for volume, device_info in zip(model_data.total_volume, model_data.device_info)], marker_color='lightsalmon')])
        fig.update_layout(title_text=f"Model: {model}", xaxis_title="UID", yaxis_title="Mean Score", width=1200)
        
        fig.update_layout(
            xaxis=dict(type="category"),
        )
        st.plotly_chart(fig)
        
        # # Plot process time and success rate chart
        # df = pd.DataFrame(model_data)
        # fig = px.scatter(df, x="mean_process_time", y="success_rate", 
        #         hover_data=["uid", "model_name", "mean_score"],
        #         size="total_volume", color="uid"
        #     )
        # fig.update_layout(
        #     xaxis_title="Mean Process Time (seconds)",
        #     yaxis_title="Success Rate",
        #     xaxis=dict(range=[0, df["mean_process_time"].max() * 1.1]),
        #     yaxis=dict(range=[0, 1.1]),
        #     legend_title="UID",
        #     width=1200
        # )
        # st.plotly_chart(fig)

with tabs[1]:
    components.iframe("https://app.nichetensor.com", height=1024)

# with tabs[2]:
#     MAX_PROMPT = 10
#     SCORE_WEIGHTS = {"iqa": 0.5, "prompt_adherence": 0.5}
#     def calculate_score(prompt_adherence_scores, iqa_score):
#         pa_score = sum(prompt_adherence_scores) / len(prompt_adherence_scores) if len(prompt_adherence_scores) > 0 else 0
#         final_score = SCORE_WEIGHTS["prompt_adherence"] * pa_score + SCORE_WEIGHTS["iqa"] * iqa_score
#         return pa_score, final_score
#     def _download_folder(repo_id, repo_type, folder_path, local_dir):
#         files = list_repo_files(repo_id=repo_id, repo_type=repo_type)
#         file_names = []
#         for file_path in files:
#             if file_path.startswith(folder_path):
#                 local_file_path = os.path.join(local_dir, file_path[len(folder_path)+1:])
#                 if not os.path.exists(local_file_path):
#                     os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
#                     hf_hub_download(repo_id=repo_id, repo_type=repo_type, filename=file_path, local_dir=local_dir)
#             file_names.append(os.path.basename(file_path))
#         return file_names
        
#     oc_data_path = "data"
#     oc_metadata_dir = os.path.join(oc_data_path, "metadata")
#     oc_img_dir = os.path.join(oc_data_path, "images")
#     os.makedirs(oc_metadata_dir, exist_ok=True)
#     os.makedirs(oc_img_dir, exist_ok=True)
#     repo_id = "nichetensor-org/open-category"
#     repo_type="dataset"
#     metadata_file_names = _download_folder(repo_id=repo_id, repo_type=repo_type, folder_path="metadata", local_dir=oc_data_path)
    
#     metadata_files = os.listdir(oc_metadata_dir)
#     oc_prompt_data = {}
#     for file in metadata_files:
#         file_path = os.path.join(oc_metadata_dir,  file)
#         if file not in metadata_file_names:
#             os.remove(file_path)
#         else:
#             file_time = os.path.getmtime(file_path)
#             with open(file_path) as f:
#                 dt = json.load(f)
#             prompt = dt.get("prompt")

#             dt["questions"] = [x.rstrip("Answer only Y or N.") for x in dt["questions"]]
#             dt["pa_score"], dt["final_score"] = calculate_score(dt["prompt_adherence_scores"]["0"], dt["iqa_scores"][0])
#             dt["iqa_score"] = [f"{x:.4f}"for x in dt["iqa_scores"]][0]
#             dt["file_time"] = file_time 
#             if dt["final_score"] > 0:
#                 if prompt not in oc_prompt_data:
#                     oc_prompt_data[prompt] = []
#                 oc_prompt_data[prompt].append(dt)

#     last_update_times = []
#     for prompt, dt in oc_prompt_data.items():
#         latest_file = max(dt, key=lambda x: x["file_time"])
#         latest_time = latest_file["file_time"]
#         last_update_times.append(latest_time)
#     combined = list(zip(last_update_times, oc_prompt_data.items()))
#     combined_sorted = sorted(combined, key=lambda x: x[0], reverse=True)[:MAX_PROMPT]
#     oc_prompt_data = dict([x[1] for x in combined_sorted])
    
#     prompts = list(oc_prompt_data.keys())
#     prompt_select = st.selectbox(
#         "Select a prompt",
#         prompts,
#         index=0
#     )
#     prompt_data = oc_prompt_data[prompt_select]
#     prompt_data = sorted(prompt_data, key = lambda x: -x["final_score"])

#     pd_data = pd.DataFrame(prompt_data)
#     st.header("**Total Information**")
#     st.dataframe(pd_data,
#         width=1200,
#         column_order = ("pa_score", "iqa_score", "final_score"),
#         column_config = {
#             "iqa_score": st.column_config.NumberColumn(
#                 "IQA Score",
#             ),
#             "final_score": st.column_config.ProgressColumn(
#                 "Overall Score",
#                 format="%.2f",
#                 min_value=0,
#                 max_value=1,
#             ),
#             "pa_score": st.column_config.NumberColumn(
#                 "Prompt Adherence Score"
#             ),
#         })

#     st.header("**Davidsonian Scene Graph**")
#     nodes = []
#     edges = []
#     questions = prompt_data[0]["questions"]
#     dependencies = prompt_data[0]["dependencies"]
   
#     # Create a graphviz Digraph object
#     dot = graphviz.Digraph()
#     dot.attr(size='10,10', rankdir='TB', nodesep='0.5', ranksep='1.0', newrank='true')  

#     dot.node("-1", "root")
#     # Add nodes (questions) to the graph
#     for i, question in enumerate(questions):
#         dot.node(str(i), question)
        
#     # Add edges (dependencies) to the graph
#     children = []
#     for child, parents in dependencies.items():
#         for parent in parents:
#             dot.edge(str(parent), str(child))
#         if len(parents) > 0:
#             children.append(child)
#     for i, question in enumerate(questions):
#         if str(i) not in children:
#             dot.edge("-1", str(i))

#     st.graphviz_chart(dot, use_container_width=True)



#     df = pd.DataFrame(prompt_data[:10])

#     for idx, row in df.iterrows():
#         try:
#             img_path = row["images"][0]
#             local_img_path = os.path.join("data/images", img_path)
#             if not os.path.exists(local_img_path):
#                 hf_hub_download(repo_id=repo_id, repo_type=repo_type, filename=os.path.join("images", img_path), local_dir=oc_data_path)
            
#             mean_adherence_score = sum(row["prompt_adherence_scores"]["0"]) / len(row["prompt_adherence_scores"]["0"])
#             iqa_score = row["iqa_scores"][0]
#             total_score = row["final_score"]

#             st.subheader(f"Rank {idx+1}")
#             st.image(local_img_path, caption="")
            
#             st.write(f"**Prompt Adherence Score**: {mean_adherence_score:.4f}")
#             st.write(f"**IQA Score**: {iqa_score:.4f}")
#             st.write(f"**Total Score**: {total_score:.4f}")
            
        #     st.markdown("---") 
        # except Exception as ex:
        #     print("Show imgage ex: ", ex)
