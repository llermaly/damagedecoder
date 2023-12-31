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
The images are of a damaged {make_name} {model_name} {year} car. 
I need to fill a vehicle condition report for this car.
Please fill the following details based on the images:
FRONT
1. Roof
2. Windshield
3. Hood
4. Grill
5. Front bumper
6. Mirrors
7. Front lights
BACK
8. Rear Window
9. Trunk/TGate
10. Trunk/Cargo area
11. Rear bumper
12. Tail lights
DRIVERS SIDE 
13. Left fender
14. Left front door
15. Left rear door
16. Left rear quarter panel
PASSENGER SIDE
17. Right rear quarter
18. Right rear door
19. Right front door
20. Right fender
TIRES
T1. Front left tire
T2. Front right tire
T3. Rear left tire
T4. Rear right tire

For each of the details you must answer with this alternatives to reflect the condition: 

- 0: Not visible
- 1: Seems OK (no damage)
- 2: Minor damage (scratches, dents, etc)
- 3: Major damage (bent, broken, etc)
"""


class DamagedPart(BaseModel):
    """Data model of the damaged part"""

    part_name: str = Field(..., description="Name of the damaged part")
    cost: float = Field(..., description="Estimated cost of repair")


class DamagedParts(BaseModel):
    """Data model of the damaged parts"""

    damaged_parts: list[DamagedPart] = Field(..., description="List of damaged parts")
    summary: str = Field(..., description="Summary of the damage")


class ConditionsReport(BaseModel):
    """Data model of conditions report"""

    roof: Annotated[int, Field(0, ge=0, le=3, description="Roof condition")]
    windshield: Annotated[int, Field(0, ge=0, le=3, description="Windshield condition")]
    hood: Annotated[int, Field(0, ge=0, le=3, description="Hood condition")]
    grill: Annotated[int, Field(0, ge=0, le=3, description="Grill condition")]
    front_bumper: Annotated[int, Field(0, ge=0, le=3, description="Front bumper condition")]
    mirrors: Annotated[int, Field(0, ge=0, le=3, description="Front mirror condition")]
    front_lights: Annotated[int, Field(0, ge=0, le=3, description="Front lights condition")]
    rear_window: Annotated[int, Field(0, ge=0, le=3, description="Rear window condition")]
    trunk_tgate: Annotated[int, Field(0, ge=0, le=3, description="Trunk/TGate condition")]
    trunk_cargo_area: Annotated[int, Field(0, ge=0, le=3, description="Trunk Cargo area condition")]
    rear_bumper: Annotated[int, Field(0, ge=0, le=3, description="Rear bumper condition")]
    tail_lights: Annotated[int, Field(0, ge=0, le=3, description="Tail lights condition")]
    left_fender: Annotated[int, Field(0, ge=0, le=3, description="Left fender condition")]
    left_front_door: Annotated[int, Field(0, ge=0, le=3, description="Left front door condition")]
    left_rear_door: Annotated[int, Field(0, ge=0, le=3, description="Left rear door condition")]
    left_rear_quarter_panel: Annotated[int, Field(0, ge=0, le=3, description="Left rear quarter panel condition")]
    right_rear_quarter: Annotated[int, Field(0, ge=0, le=3, description="Right rear quarter condition")]
    right_rear_door: Annotated[int, Field(0, ge=0, le=3, description="Right rear door condition")]
    right_front_door: Annotated[int, Field(0, ge=0, le=3, description="Right front door condition")]
    right_fender: Annotated[int, Field(0, ge=0, le=3, description="Right fender condition")]
    front_left_tire: Annotated[int, Field(0, ge=0, le=3, description="Front left tire condition")]
    front_right_tire: Annotated[int, Field(0, ge=0, le=3, description="Front right tire condition")]
    rear_left_tire: Annotated[int, Field(0, ge=0, le=3, description="Rear left tire condition")]
    rear_right_tire: Annotated[int, Field(0, ge=0, le=3, description="Rear right tire condition")]




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
