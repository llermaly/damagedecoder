from llama_index.multi_modal_llms import GeminiMultiModal
from llama_index.program import MultiModalLLMCompletionProgram
from llama_index.output_parsers import PydanticOutputParser
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from pydantic import BaseModel, Field
from typing_extensions import Annotated

damages_initial_prompt_str = """
The images are of a damaged {make_name} {model_name} {year} car. 
The images are taken from different angles.
Please analyze them and tell me what parts are damaged and what is the estimated cost of repair.
"""

conditions_report_initial_prompt_str = """
The images are of a damaged vehicle. 
I need to fill a vehicle condition report based on the picture(s).
Please fill the following details based on the image(s):
FRONT
1. Roof
2. Windshield
3. Hood
4. Grill
5. Front bumper
6. Right mirror
7. Left mirror
8. Front right light
9. Front left light
BACK
10. Rear Window
11. Trunk/TGate
12. Trunk/Cargo area
13. Rear bumper
14. Tail lights
DRIVERS SIDE 
15. Left fender
16. Left front door
17. Left rear door
18. Left rear quarter panel
PASSENGER SIDE
19. Right rear quarter
20. Right rear door
21. Right front door
22. Right fender
TIRES
T1. Front left tire
T2. Front right tire
T3. Rear left tire
T4. Rear right tire

For each of the details you must answer with a score based on this descriptions to reflect the condition: 

- 0: Not visible
- 1: Seems OK (no damage)
- 2: Minor damage (scratches, dents)
- 3: Major damage (bent, broken, missing)
"""


class DamagedPart(BaseModel):
    """Data model of the damaged part"""

    part_name: str = Field(..., description="Name of the damaged part")
    cost: float = Field(..., description="Estimated cost of repair")


class DamagedParts(BaseModel):
    """Data model of the damaged parts"""

    damaged_parts: list[DamagedPart] = Field(...,
                                             description="List of damaged parts")
    summary: str = Field(..., description="Summary of the damage")


class ConditionsReport(BaseModel):
    """Data model of conditions report"""

    roof: Annotated[int, Field(0, ge=0, le=3, description="Roof condition")]
    windshield: Annotated[int, Field(
        0, ge=0, le=3, description="Windshield condition")]
    hood: Annotated[int, Field(0, ge=0, le=3, description="Hood condition")]
    grill: Annotated[int, Field(0, ge=0, le=3, description="Grill condition")]
    front_bumper: Annotated[int, Field(
        0, ge=0, le=3, description="Front bumper condition")]
    right_mirror: Annotated[int, Field(
        0, ge=0, le=3, description="Right mirror condition")]
    left_mirror: Annotated[int, Field(
        0, ge=0, le=3, description="Left mirror condition")]
    front_right_light: Annotated[int, Field(
        0, ge=0, le=3, description="Front right light condition")]
    front_left_light: Annotated[int, Field(
        0, ge=0, le=3, description="Front left light condition")]
#back 
    rear_window: Annotated[int, Field(
        0, ge=0, le=3, description="Rear window condition")]
    trunk_tgate: Annotated[int, Field(
        0, ge=0, le=3, description="Trunk/TGate condition")]
    trunk_cargo_area: Annotated[int, Field(
        0, ge=0, le=3, description="Trunk/Cargo area condition")]
    rear_bumper: Annotated[int, Field(
        0, ge=0, le=3, description="Rear bumper condition")]
    right_tail_light: Annotated[int, Field(
        0, ge=0, le=3, description="Right tail light condition")]
    left_tail_light: Annotated[int, Field(
        0, ge=0, le=3, description="Left tail light condition")]
#left
    left_rear_quarter: Annotated[int, Field(
        0, ge=0, le=3, description="Left rear quarter condition")]
    left_rear_door: Annotated[int, Field(
        0, ge=0, le=3, description="Left rear door condition")]
    left_front_door: Annotated[int, Field(
        0, ge=0, le=3, description="Left front door condition")]
    left_fender: Annotated[int, Field(
        0, ge=0, le=3, description="Left fender condition")]
    left_front_tire: Annotated[int, Field(
        0, ge=0, le=3, description="Left front tire condition")]
    left_rear_tire: Annotated[int, Field(
        0, ge=0, le=3, description="Left rear tire condition")]
#right
    right_rear_quarter: Annotated[int, Field(
        0, ge=0, le=3, description="Right rear quarter condition")]
    right_rear_door: Annotated[int, Field(
        0, ge=0, le=3, description="Right rear door condition")]
    right_front_door: Annotated[int, Field(
        0, ge=0, le=3, description="Right front door condition")]
    right_fender: Annotated[int, Field(
        0, ge=0, le=3, description="Right fender condition")]
    right_front_tire: Annotated[int, Field(
        0, ge=0, le=3, description="Right front tire condition")]
    right_rear_tire: Annotated[int, Field(
        0, ge=0, le=3, description="Right rear tire condition")]
    
    
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
