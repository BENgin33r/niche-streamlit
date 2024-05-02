import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


st.set_page_config(page_title="NicheImage Studio", layout="wide")
st.markdown("## :blue[Image Generation Studio by NicheImage]")
replicate_logo = "https://nichetensor.com/wp-content/uploads/2024/04/cropped-NicheTensor_logo_transparent.png"

with st.sidebar:
    st.image(replicate_logo, use_column_width=True)
st.markdown(
    """
    **NicheImage is a decentralized network of image generation models, powered by the Bittensor protocol. Below you find information about the current models on the network.**
    """,
    unsafe_allow_html=True,
)
if "stats" not in st.session_state:
    response = requests.get("http://nichestorage.nichetensor.com:10000/get_miner_info")
    response = response.json()
    st.session_state.stats = response

all_validator_response = st.session_state.stats
validator_uids = list(all_validator_response.keys())
validator_uids = [int(uid) for uid in validator_uids]
tabs = st.tabs
validator_uids = sorted(validator_uids)
print(validator_uids)
validator_select = st.selectbox(
    "Select a validator",
    validator_uids,
)
validator_select = str(validator_select)
response = all_validator_response[validator_select]
# Plot distribution of models
model_distribution = {}
for uid, info in response["info"].items():
    model_name = info["model_name"]
    model_distribution[model_name] = model_distribution.get(model_name, 0) + 1
fig = px.pie(
    values=list(model_distribution.values()),
    names=list(model_distribution.keys()),
    title="Model Distribution",
)
st.plotly_chart(fig)
transformed_dict = []
for k, v in response["info"].items():
    transformed_dict.append(
        {
            "uid": k,
            "model_name": v["model_name"],
            "mean_score": (
                sum(v["scores"]) / (len(v["scores"])) if len(v["scores"]) > 0 else 0
            ),
            "total_volume": v["total_volume"],
        }
    )
transformed_dict = pd.DataFrame(transformed_dict)
# plot N bar chart for N models, sorted by mean score
for model in model_distribution.keys():
    model_data = transformed_dict[transformed_dict["model_name"] == model]
    model_data = model_data.sort_values(by="mean_score", ascending=False)
    model_data.uid = model_data.uid.astype(str)
    if model_data.mean_score.sum() == 0:
        continue
    fig = go.Figure(data=[go.Bar(x=model_data.uid, y=model_data.mean_score,
            hovertext=[f"Total volume {volume}" for volume in model_data.total_volume], marker_color='lightsalmon')])
    fig.update_layout(title_text=f"Model: {model}", xaxis_title="UID", yaxis_title="Mean Score")
    
    fig.update_layout(
        xaxis=dict(type="category"),
    )
    st.plotly_chart(fig)
pd_data = pd.DataFrame(response["info"])
st.markdown(
    """
    **Total Information**
    """,
    unsafe_allow_html=True,
)
st.dataframe(pd_data.T)
