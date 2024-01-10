# from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML
# import os
# from car_colorizer import sides_map

# # Define a mapping of condition codes to text
# status_texts = {
#     0: "Not visible",
#     1: "Seems OK",
#     2: "Minor damage",
#     3: "Major damage",
# }

# images_dict = {
#     "car_front": "colored_car_front.png",
#     "car_back": "colored_car_back.png",
#     "car_left": "colored_car_left.png",
#     "car_right": "colored_car_right.png",
# }

# IMAGES_DIR = os.path.abspath("images")


# def generate_html(conditions):
#     # Load the template
#     env = Environment(loader=FileSystemLoader("."))
#     template = env.get_template("report.html")

#     conditions_map = {"front": {}, "back": {}, "left": {}, "right": {}}

#     for part, condition in conditions.items():
#         for side in conditions_map:
#             if part in sides_map[side]["parts"]:
#                 conditions_map[side][part] = condition
#                 break

#     # Render the template with the conditions and status texts
#     html_content = template.render(
#         car_image=images_dict,
#         images_dir=IMAGES_DIR,
#         conditions=conditions_map,
#         status_texts=status_texts,
#     )

#     return html_content


# def create_pdf_from_html(html_content, output_path):
#     HTML(string=html_content, base_url=".").write_pdf(output_path)
#     return output_path


# def generate_report(conditions_dict):
#     # Generate HTML
#     html_output = generate_html(conditions_dict)
#     # Create PDF from HTML
#     output_pdf_path = "report.pdf"
#     pdf = create_pdf_from_html(html_output, output_pdf_path)
#     return pdf
