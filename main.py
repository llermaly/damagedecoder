from dotenv import load_dotenv
from llama_index import VectorStoreIndex
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.vector_stores import WeaviateVectorStore
from llama_index.vector_stores.types import MetadataFilters, MetadataFilter
import cv2
import numpy as np
import os
import streamlit as st
import weaviate
from llama_index import SimpleDirectoryReader
from pydantic_llm import (
    pydantic_llm,
    DamagedParts,
    damages_initial_prompt_str,
    ConditionsReport,
    conditions_report_initial_prompt_str,
)
import pandas as pd
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from car_colorizer import process_car_parts
from report import generate_report
import requests
from io import BytesIO
from streamlit_modal import Modal
import streamlit.components.v1 as components

modal = Modal("Damage Report", key="demo", max_width=1280)

api_url = "https://dmg-decoder.up.railway.app"


def create_report(data={"test": "123"}):
    url = f"{api_url}/api/create_report"
    response = requests.post(
        url, json=data, headers={"Content-Type": "application/json"}
    )
    json = response.json()
    print(json)
    return json["id"]


load_dotenv()







states_names = ["front_image", "back_image", "left_image", "right_image", "report_id"]

auth_config = weaviate.AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"])
openai_mm_llm = OpenAIMultiModal(model="gpt-4-vision-preview")

client = weaviate.Client(
    os.environ["WEAVIATE_URL"],
    auth_client_secret=weaviate.AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"]),
)

vector_store = WeaviateVectorStore(
    weaviate_client=client, index_name="CarPart", text_key="title"
)

# Remove form border and padding styles
css = r"""
    <style>
        [data-testid="stForm"] {border: 0px;padding:0px}
    </style>
"""
st.markdown(css, unsafe_allow_html=True)


for state_name in states_names:
    if state_name not in st.session_state:
        st.session_state[state_name] = None


st.title("Repair your car!")
st.write(
    "Upload your car crash pictures and we weill give you an aproximate repair cost and which parts do you need."
)


st.subheader("Upload your car crash pictures")


def create_drag_and_drop(state_name, label):
    st.session_state[state_name] = st.file_uploader(
        label=label, key=f"{state_name}_image"
    )

    if st.session_state[state_name] is not None:
        css = f"""
            <style>
                [aria-label="{label}"] {{display: none;}}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
        file_bytes = np.asarray(
            bytearray(st.session_state[state_name].read()), dtype=np.uint8
        )
        opencv_image = cv2.imdecode(file_bytes, 1)
        st.image(opencv_image, channels="BGR")


col1, col2 = st.columns(2)

with col1:
    create_drag_and_drop("front_image", "Front Image")
    create_drag_and_drop("right_image", "Left Image")

with col2:
    create_drag_and_drop("back_image", "Back Image")
    create_drag_and_drop("left_image", "Right Image")


def save_image(state_name):
    path = os.path.join(os.getcwd(), "images")
    if not os.path.exists(path):
        os.makedirs(path)

    if st.session_state[state_name] is not None:
        with open(os.path.join(path, f"{state_name}.jpg"), "wb") as f:
            f.write(st.session_state[state_name].getbuffer())


def delete_image(state_name):
    path = os.path.join(os.getcwd(), "images")
    if st.session_state[state_name] is not None and os.path.exists(
        os.path.join(path, f"{state_name}.jpg")
    ):
        os.remove(os.path.join(path, f"{state_name}.jpg"))


with st.form(key="car_form"):
    selected_make = st.selectbox(
        "Select your car make",
        ("Ford", "Subaru", "BMW", "Mercedes", "Volkswagen", "Volvo"),
    )

    selected_model = st.selectbox(
        "Select your car model",
        ("Mustang", "Outback", "X3", "C-Class", "Golf", "XC60"),
    )

    selected_year = st.selectbox(
        "Select your car year",
        ("2007", "2010", "2011", "2012", "2013", "2014"),
    )

    submit_button = st.form_submit_button(label="Submit")

if submit_button:
    with st.spinner("Processing..."):
        for state_name in states_names:
            save_image(state_name)
        path = os.path.join(os.getcwd(), "images")

        image_documents = SimpleDirectoryReader(path).load_data()

        conditions_report_response = pydantic_llm(
            output_class=ConditionsReport,
            image_documents=image_documents,
            prompt_template_str=conditions_report_initial_prompt_str.format(
                make_name=selected_make, model_name=selected_model, year=selected_year
            ),
        )

        for state_name in states_names:
            delete_image(state_name)

        request_data = []

        for part, condition in dict(conditions_report_response).items():
            request_data.append({"part": part, "condition": condition})

        id = create_report(
            data={
                "conditions_report": request_data,
                "car_name": f"{selected_make} {selected_model} {selected_year}",
            }
        )

        st.session_state["report_id"] = id

        car_sides = ["front", "back", "left", "right"]
        import boto3

        s3 = boto3.resource("s3")

        for side in car_sides:
            colored_side = process_car_parts(dict(conditions_report_response), side)
            in_memory_file = BytesIO()
            colored_side.save(in_memory_file, format="PNG")
            in_memory_file.seek(0)
            s3.Bucket("elastic-llm").put_object(
                Key=f"{id}/colored_car_{side}.png",
                Body=in_memory_file,
            )

        modal.open()

if modal.is_open():
    with modal.container():

        st.markdown(
            f"<a href='{api_url}/report/{st.session_state["report_id"]}' target='_blank'>Go to report</a>",
            unsafe_allow_html=True,
        )

        st.code(f"{api_url}/report/{st.session_state["report_id"]}", language="python")


        html_string = f"""
            <div style="max-height:450px;overflow-y:auto;overflow-x:hidden">
                <iframe style="overflow-x:hidden" src="{api_url}/report/{st.session_state["report_id"]}" width="100%" height="960px"></iframe>
            </div>
        """
        components.html(html_string, height=450)


        # st.subheader("Summary")
        # st.write(damages_response.summary)

        # st.subheader("Damaged Parts")
        # df = pd.DataFrame.from_records(
        #     [part.model_dump() for part in damages_response.damaged_parts]
        # )
        # st.dataframe(df)

        # TODO: look for the parts in the vector store

        # filters = MetadataFilters(
        #     filters=[
        #         MetadataFilter(key="make", value=selected_make),
        #         MetadataFilter(key="model", value=selected_model),
        #         MetadataFilter(key="year", value=selected_year),
        #     ]
        # )

        # retriever = VectorStoreIndex.from_vector_store(vector_store).as_retriever(
        #     filters=filters,
        # )

        # query_engine = RetrieverQueryEngine(
        #     retriever=retriever,
        # )
