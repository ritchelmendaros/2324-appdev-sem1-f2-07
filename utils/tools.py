import json
from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT
from pptx.util import Pt

load_dotenv()
API_KEY = "oi7CBx6u1DQhpPJB4187TgBDdZH2r6eGsdxPvrCfHRe2oFd3pgr2mkQs"
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

def slide_format(content_frame, font_size, font, r, g, b, align, space):
    for paragraph in content_frame.paragraphs:
        paragraph.font.size = Pt(font_size)
        paragraph.font.name = font
        paragraph.font.color.rgb = RGBColor(r,g,b)
        if align == 0:
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.LEFT
        else:
            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.RIGHT
        paragraph.space_after = Pt(space)