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
from pydantic_llm import pydantic_llm, DamagedParts, initial_prompt_str
import pandas as pd
from llama_index.multi_modal_llms.openai import OpenAIMultiModal

load_dotenv()

states_names = ["front_image", "back_image", "left_image", "right_image"]

auth_config = weaviate.AuthApiKey(api_key=os.environ["WEAVIATE_API_KEY"])
openai_mm_llm = OpenAIMultiModal(model="gpt-4-vision-preview")

client = weaviate.Client(
    "https://carparts-28-12-2023-qpdn512a.weaviate.network",
    auth_client_secret=auth_config,
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


if not "front_image" in st.session_state:
    st.session_state["front_image"] = None

if not "back_image" in st.session_state:
    st.session_state["back_image"] = None

if not "left_image" in st.session_state:
    st.session_state["left_image"] = None

if not "right_image" in st.session_state:
    st.session_state["right_image"] = None


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
    create_drag_and_drop("right_image", "Right Image")

with col2:
    create_drag_and_drop("back_image", "Back Image")
    create_drag_and_drop("left_image", "Left Image")


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

        response = pydantic_llm(
            output_class=DamagedParts,
            image_documents=image_documents,
            prompt_template_str=initial_prompt_str.format(
                make_name=selected_make, model_name=selected_model, year=selected_year
            ),
        )

        for state_name in states_names:
            delete_image(state_name)

        st.subheader("Summary")
        st.write(response.summary)

        st.subheader("Damaged Parts")
        df = pd.DataFrame.from_records(
            [part.model_dump() for part in response.damaged_parts]
        )
        st.dataframe(df)

        # TODO: look for the parts in the vector store

        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="make", value=selected_make),
                MetadataFilter(key="model", value=selected_model),
                MetadataFilter(key="year", value=selected_year),
            ]
        )

        retriever = VectorStoreIndex.from_vector_store(vector_store).as_retriever(
            filters=filters,
        )

        query_engine = RetrieverQueryEngine(
            retriever=retriever,
        )
