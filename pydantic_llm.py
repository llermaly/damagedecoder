from llama_index.multi_modal_llms import GeminiMultiModal
from llama_index.program import MultiModalLLMCompletionProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from pydantic import BaseModel, Field


initial_prompt_str = """
The images are of a damaged {make_name} {model_name} {year} car. 
The images are taken from different angles.
Please analyze them and tell me what parts are damaged and what is the estimated cost of repair.
"""


class DamagedPart(BaseModel):
    """Data model of the damaged part"""

    part_name: str = Field(..., description="Name of the damaged part")
    cost: float = Field(..., description="Estimated cost of repair")


class DamagedParts(BaseModel):
    """Data model of the damaged parts"""

    damaged_parts: list[DamagedPart] = Field(..., description="List of damaged parts")
    summary: str = Field(..., description="Summary of the damage")


def pydantic_llm(output_class, image_documents, prompt_template_str):
    openai_mm_llm = OpenAIMultiModal(model="gpt-4-vision-preview")
    gemini_llm = GeminiMultiModal(model_name="models/gemini-pro-vision")

    llm_program = MultiModalLLMCompletionProgram.from_defaults(
        output_parser=PydanticOutputParser(output_class),
        image_documents=image_documents,
        prompt_template_str=prompt_template_str,
        multi_modal_llm=gemini_llm,
        verbose=True,
    )

    response = llm_program()
    return response
