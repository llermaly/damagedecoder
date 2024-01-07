from car_colorizer import process_car_parts
from dotenv import load_dotenv
from io import BytesIO
from llama_index import SimpleDirectoryReader
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.vector_stores import WeaviateVectorStore
from streamlit_modal import Modal
import cv2
import os
import requests
import streamlit as st
import streamlit.components.v1 as components
import weaviate
from pydantic_llm import (
    pydantic_llm,
    ConditionsReport,
    conditions_report_initial_prompt_str,
)

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


st.title("Repair your car!")
st.write(
    "Upload your car crash pictures and we weill give you an aproximate repair cost and which parts do you need."
)


st.subheader("Upload your car crash pictures")


images_directory = "./examples/2007 FORD MUSTANG"


def load_image_from_directory(image_name):
    image_path = os.path.join(images_directory, image_name)
    if os.path.exists(image_path):
        image = cv2.imread(image_path)
        st.image(image, channels="BGR")


col1, col2 = st.columns(2)

with col1:
    load_image_from_directory("front.jpeg")
    load_image_from_directory("right.jpeg")

with col2:
    load_image_from_directory("back.jpeg")
    load_image_from_directory("left.jpeg")


with st.form(key="car_form"):
    selected_make = st.selectbox(
        "Select your car make",
        ("Ford",),
    )

    selected_model = st.selectbox(
        "Select your car model",
        ("Mustang",),
    )

    selected_year = st.selectbox(
        "Select your car year",
        ("2007",),
    )

    selected_llm_model = st.selectbox(
        "Select LLM model",
        ("Gemini", "OpenAI"),
    )

    submit_button = st.form_submit_button(label="Submit")

if submit_button:
    with st.spinner("Processing..."):
        image_documents = SimpleDirectoryReader(images_directory).load_data()

        conditions_report_response = pydantic_llm(
            output_class=ConditionsReport,
            image_documents=image_documents,
            prompt_template_str=conditions_report_initial_prompt_str.format(
                make_name=selected_make, model_name=selected_model, year=selected_year
            ),
            selected_llm_model=selected_llm_model,
        )

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
            f"<a href='{api_url}/report/{st.session_state['report_id']}' target='_blank'>Go to report</a>",
            unsafe_allow_html=True,
        )

        st.code(f"{api_url}/report/{st.session_state['report_id']}", language="python")

        html_string = f"""
            <div style="max-height:350px;overflow-y:auto;overflow-x:hidden">
                <iframe style="overflow-x:hidden" src="{api_url}/report/{st.session_state['report_id']}" width="100%" height="960px"></iframe>
            </div>
        """
        components.html(html_string, height=350)
