import json
import math
import os
from io import BytesIO

import requests
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT, MSO_AUTO_SIZE
from urllib.parse import quote_plus
from dotenv import load_dotenv

dir_path = 'static/presentations'

load_dotenv()
API_KEY = "oi7CBx6u1DQhpPJB4187TgBDdZH2r6eGsdxPvrCfHRe2oFd3pgr2mkQs"


def parse_response(response):
    holdTitle = ""
    isOneNewLine = 0
    isSlideTitleNewLine = 0
    # select split structure
    if response.__contains__('\n\n\n'):  # Ends with 2 newlines
        slides = response.split('\n\n\n')
    else:  # End with 1 newline
        isOneNewLine = 1
        slides = response.split('\n\n')

    slides_content = []

    for slide in slides:
        lines = slide.split('\n')

        if isOneNewLine == 1 and (len(lines) == 1 or isSlideTitleNewLine == 1): # End with 1 newline it have newline after slide title
            if holdTitle == "":
                title_line = lines[0]
                title = title_line.split(': ', 1)[1] if ': ' in title_line else title_line
                isSlideTitleNewLine = 1
                holdTitle = title
                continue
            else:
                title = holdTitle
                holdTitle = ""
        else:
            title_line = lines[0]
            title = title_line.split(': ', 1)[1] if ': ' in title_line else title_line

        #Contents for slide that ends with 2 newlines
        if isOneNewLine == 0:
            if lines.__contains__('\n\n'):# have a newline after the slide title
                content_lines = [line.lstrip('- ') for line in lines[2:] if line and 'Content:' not in line]
            else:
                content_lines = [line.lstrip('- ') for line in lines[1:] if line and 'Content:' not in line]
        else: #Contents for slide that ends with 1 newline
            if isSlideTitleNewLine == 1: # There is a newline after slide title
                content_lines = [line.lstrip('- ') for line in lines[0:] if line and 'Content:' not in line]
            else:
                content_lines = [line.lstrip('- ') for line in lines[1:] if line and 'Content:' not in line]

            isSlideTitleNewLine = 0

        content = '\n'.join(content_lines)
        keyword_line = [line for line in lines if 'Keyword:' in line or 'Keywords:' in line]
        keyword = keyword_line[0].split(': ', 1)[1].strip() if keyword_line else 'computer'
        slides_content.append({'title': title, 'content': content, 'keyword': keyword})

    return slides_content


def search_pexels_images(keyword):
    query = quote_plus(keyword.lower())
    print("Query:", query) # Debug
    PEXELS_API_URL = f'https://api.pexels.com/v1/search?query={query}&per_page=1'
    print("URL:", PEXELS_API_URL) # Debug
    headers = {
        'Authorization': API_KEY,
    }

    response = requests.get(PEXELS_API_URL, headers=headers)
    limit = response.headers.get('X-RateLimit-Limit')
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset_time = response.headers.get('X-RateLimit-Reset')

    print('Rate Limit Limit:', limit)
    print('Rate Limit Remaining:', remaining)
    print('Rate Limit Reset Time:', reset_time)
    print("Response Status Code:", response.status_code) # Debug
    print("Response Content:", response.text) # Debug
    data = json.loads(response.text)
    if 'photos' in data:
        if len(data['photos']) > 0:
            return data['photos'][0]['src']['medium']
    return None


def delete_first_two_slides(presentation):
    slide_ids = [1, 0, len(presentation.slides)-1]
    for slide_id in slide_ids:
        if slide_id < len(presentation.slides):
            xml_slides = presentation.slides._sldIdLst
            slides = list(xml_slides)
            xml_slides.remove(slides[slide_id])

# def update_specific_slide():

def create_ppt(slides_content, template_choice, presentation_title, presenter_name):
    template_path = os.path.join(dir_path, f"{template_choice}.pptx")

    prs = Presentation(template_path)

    title_slide_layout = prs.slide_layouts[0]

    # add title slide
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    title.text = presentation_title

    #add subtitle
    subtitle = slide.placeholders[1]
    subtitle.text = f"Presented by {presenter_name}"

    if template_choice == 'simple':
        for paragraph in title.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(166)
                run.font.name = 'Gill Sans MT'
                run.font.color.rgb = RGBColor(5, 14, 56) # RGB for orange color
    elif template_choice == 'dark_modern':
        for paragraph in title.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(115)
                run.font.color.rgb = RGBColor(255, 165, 0)  # RGB for orange color

    elif template_choice == 'bright_modern':
        for paragraph in title.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Arial'
                run.font.size = Pt(115)
                run.font.color.rgb = RGBColor(255, 20, 147)  # RGB for deep pink color

    elif template_choice == 'dark_blue':
        for paragraph in title.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Corbel(Headings)'
                run.font.size = Pt(115)
                run.font.color.rgb = RGBColor(255, 255, 255)

    numslides = len(slides_content)
    divided = (numslides-1) / 4

    first = math.ceil(divided+1)
    second = math.ceil(first+divided)
    third = math.ceil(second+divided)

    count = 1
    print(numslides)
    # add content slides

    for slide_content in slides_content:
        if slide_content != '':
            if count < first:
                content_structure_1(prs, slide_content, template_choice)
            elif count < second and count >= first:
                content_structure_2(prs, slide_content, template_choice)
            elif count < third and count >= second:
                content_structure_3(prs, slide_content, template_choice)
            else:
                content_structure_4(prs, slide_content, template_choice)

        count += 1

    # Delete the first two slides after all new slides have been added
    delete_first_two_slides(prs)

    # Save the presentation
    prs.save(os.path.join('generated', 'generated_presentation.pptx'))


# openai image generation using dall-e 3
def generate_openai_image(prompt, model="dall-e-3", n=1, size="1024x1024", response_format="url", quality="standard",
                          style="vivid"):

    OPEN_API_KEY = "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"
    OPENAI_API_URL = "https://api.openai.com/v1/images/generations"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPEN_API_KEY}',
    }

    data = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
        "response_format": response_format,
        "quality": quality,
        "style": style,
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result['data'][0]['url'] if response_format == 'url' else result['data'][0]
    else:
        print(f"Error: {response.status_code}")
        return None


# image generation using openai
def content_structure_1(prs, slide_content, template_choice):
    if template_choice == 'simple':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))
        title_box = slide.shapes.add_textbox(Inches(1.28), Inches(5.95), Inches(7.81), Inches(4.1))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(9.76), Inches(1.33), Inches(8.92), Inches(8.7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(50)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[3])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, 0, 0, Inches(20), Inches(4.95669291))

        title_box = slide.shapes.add_textbox(Inches(0.4173228), Inches(5.3543307), Inches(5.8346457), Inches(5.3543307))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(6.5), Inches(5.3543307), Inches(13.08), Inches(5))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.RIGHT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(36)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_blue':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))
        title_box = slide.shapes.add_textbox(Inches(1.28), Inches(5.95), Inches(7.81), Inches(4.1))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(9.76), Inches(1.33), Inches(8.92), Inches(8.7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255,255,255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'bright_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, 0, 0, Inches(20), Inches(4.95669291))

        title_box = slide.shapes.add_textbox(Inches(0.4173228), Inches(5.3543307), Inches(5.8346457), Inches(5.3543307))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(6.5), Inches(5.3543307), Inches(13.08), Inches(5))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.RIGHT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)



# image generation using openai
def content_structure_2(prs, slide_content, template_choice):
    if template_choice == 'simple':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(10.13), Inches(3), Inches(8.5), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'dark_modern':
        # image_url = search_pexels_images(slide_content['title'])
        slide = prs.slides.add_slide(prs.slide_layouts[3])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))

        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(8.67), Inches(3), Inches(10), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(36)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'dark_blue':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(10.13), Inches(3), Inches(8.5), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255,255,255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'bright_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))

        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(8.67), Inches(3), Inches(10), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)


def content_structure_3(prs, slide_content, template_choice):
    if template_choice == 'simple':
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        title_box = slide.shapes.add_textbox(Inches(1.15), Inches(1), Inches(17.55), Inches(1.8))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1.15), Inches(3), Inches(17.55), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(50)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'dark_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[3])

        title_box = slide.shapes.add_textbox(Inches(1), Inches(1.1), Inches(18), Inches(2))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1), Inches(3.3), Inches(18), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(44)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'dark_blue':
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        title_box = slide.shapes.add_textbox(Inches(1.15), Inches(1), Inches(17.55), Inches(1.8))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1.15), Inches(3), Inches(17.55), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'bright_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        title_box = slide.shapes.add_textbox(Inches(1), Inches(1.1), Inches(18), Inches(2))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1), Inches(3.3), Inches(18), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)




def content_structure_4(prs, slide_content, template_choice):
    if template_choice == 'simple':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_modern':
        # image_url = search_pexels_images(slide_content['title'])
        slide = prs.slides.add_slide(prs.slide_layouts[3])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(66)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(32)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'dark_blue':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255,255,255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'bright_modern':
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        file_path = os.path.join('static', 'pictures', '4.png')
        # image_url = search_pexels_images(slide_content['title'])
        # if image_url:
        #     # Download the image
        #     response = requests.get(image_url)
        #     image_data = BytesIO(response.content)
        slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)


def update_slide_ppt(slides_content, file_path, auto, hasPicture, template_choice, slideNum):
    ppt = os.path.join('generated', f'generated_presentation.pptx')
    prs = Presentation(ppt)
    num = int(slideNum)
    print(num)
    numslides = len(prs.slides)
    divided = (numslides - 1) / 4

    first = math.ceil(divided + 1)
    second = math.ceil(first + divided)
    third = math.ceil(second + divided)

    # add content slides
    if num < len(prs.slides):
        print("1")
        remove_all_elements(prs, num)
    else:
        print("2")
        prs.slides.add_slide(prs.slide_layouts[6])

    if num < first:
        update_content_structure_1(prs, file_path, auto, hasPicture, slides_content[0], template_choice, num)
    elif num < second and num >= first:
        update_content_structure_2(prs, file_path, auto, hasPicture, slides_content[0], template_choice, num)
    elif num < third and num >= second:
        update_content_structure_3(prs, slides_content[0], template_choice, num)
    else:
        update_content_structure_4(prs, file_path, auto, hasPicture, slides_content[0], template_choice, num)

    prs.save(os.path.join('generated', 'generated_presentation.pptx'))


def remove_all_elements(prs,slideNum):
    # Iterate through each shape on the slide and remove it
    slide = prs.slides[slideNum]
    for shape in slide.shapes:
        shape.element.getparent().remove(shape.element)

    # Clear the notes on the slide
    # prs.slides.add_slide(slide_layouts[6])
    # slide.notes_slide.notes_text_frame.clear()


def update_content_structure_1(prs, file_path, auto, hasPicture, slide_content, template_choice, slideNum):
    if template_choice == 'simple':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))
        title_box = slide.shapes.add_textbox(Inches(1.28), Inches(5.95), Inches(7.81), Inches(4.1))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(9.76), Inches(1.33), Inches(8.92), Inches(8.7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(50)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, 0, 0, Inches(20), Inches(4.95669291))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, 0, 0, Inches(20), Inches(4.95669291))

        title_box = slide.shapes.add_textbox(Inches(0.4173228), Inches(5.3543307), Inches(5.8346457), Inches(5.3543307))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(6.5), Inches(5.3543307), Inches(13.08), Inches(5))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.RIGHT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(36)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_blue':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(1.28), Inches(1.33), Inches(7.90), Inches(4.52))

        title_box = slide.shapes.add_textbox(Inches(1.28), Inches(5.95), Inches(7.81), Inches(4.1))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(9.76), Inches(1.33), Inches(8.92), Inches(8.7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'bright_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data,0, 0, Inches(20), Inches(4.95669291))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, 0, 0, Inches(20), Inches(4.95669291))

        title_box = slide.shapes.add_textbox(Inches(0.4173228), Inches(5.3543307), Inches(5.8346457), Inches(5.3543307))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(6.5), Inches(5.3543307), Inches(13.08), Inches(5))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.RIGHT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)


def update_content_structure_2(prs, file_path, auto, hasPicture, slide_content, template_choice, slideNum):
    if template_choice == 'simple':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(10.13), Inches(3), Inches(8.5), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)
    elif template_choice == 'dark_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))

        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(8.67), Inches(3), Inches(10), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(36)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'dark_blue':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(1.4), Inches(3), Inches(8.48), Inches(7.15))
        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(10.13), Inches(3), Inches(8.5), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'bright_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(0.95), Inches(3), Inches(7.15), Inches(7.15))
        title_box = slide.shapes.add_textbox(Inches(1.38), Inches(1.15), Inches(17.22), Inches(1.31))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(8.67), Inches(3), Inches(10), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)


def update_content_structure_3(prs, slide_content, template_choice, slideNum):
    if template_choice == 'simple':
        slide = prs.slides[slideNum]

        title_box = slide.shapes.add_textbox(Inches(1.15), Inches(1), Inches(17.55), Inches(1.8))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1.15), Inches(3), Inches(17.55), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(50)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'dark_modern':
        slide = prs.slides[slideNum]

        title_box = slide.shapes.add_textbox(Inches(1), Inches(1.1), Inches(18), Inches(2))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1), Inches(3.3), Inches(18), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(72)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(44)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'dark_blue':
        slide = prs.slides[slideNum]

        title_box = slide.shapes.add_textbox(Inches(1.15), Inches(1), Inches(17.55), Inches(1.8))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1.15), Inches(3), Inches(17.55), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)

    elif template_choice == 'bright_modern':
        slide = prs.slides[slideNum]
        title_box = slide.shapes.add_textbox(Inches(1), Inches(1.1), Inches(18), Inches(2))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(1), Inches(3.3), Inches(18), Inches(7.1))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(72)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(25)


def update_content_structure_4(prs, file_path, auto, hasPicture, slide_content, template_choice, slideNum):
    if template_choice == 'simple':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Gill Sans MT'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Segoe UI Semibold'
            paragraph.font.color.rgb = RGBColor(5, 14, 56)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'dark_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame

        for paragraph in title_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(66)
            paragraph.font.color.rgb = RGBColor(255, 165, 0)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.name = 'Times New Roman'
            paragraph.font.size = Pt(32)
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)

    elif template_choice == 'dark_blue':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.24), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(80)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 255, 255)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(16)

    elif template_choice == 'bright_modern':
        slide = prs.slides[slideNum]
        if auto:
            print("3")
            image_url = search_pexels_images(slide_content['title'])
            if image_url:
                # Download the image
                response = requests.get(image_url)
                image_data = BytesIO(response.content)
                slide.shapes.add_picture(image_data, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))
        elif hasPicture:
            print("4")
            slide.shapes.add_picture(file_path, Inches(11), Inches(0.8), Inches(8.12), Inches(9.65))

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.9), Inches(9.71), Inches(2.12))
        title_box.text = slide_content['title']
        content_box = slide.shapes.add_textbox(Inches(0.9), Inches(3.38), Inches(9.71), Inches(7))
        content_box.text = slide_content['content']

        title_box.text_frame.word_wrap = content_box.text_frame.word_wrap = True
        content_frame = content_box.text_frame
        title_frame = title_box.text_frame
        for paragraph in title_frame.paragraphs:
            paragraph.font.size = Pt(66)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(255, 20, 147)
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT

        for paragraph in content_frame.paragraphs:
            paragraph.font.size = Pt(32)
            paragraph.font.name = 'Arial'
            paragraph.font.color.rgb = RGBColor(0, 0, 0)
            paragraph.style = 'Bullet'
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
            paragraph.space_after = Pt(20)