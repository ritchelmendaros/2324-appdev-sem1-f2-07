import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def chat_development(user_message):
    conversation = build_conversation(user_message)
    try:
        assistant_message = generate_assistant_message(conversation)
    except openai.error.RateLimitError as e:
        assistant_message = "Rate limit exceeded. Sleeping for a bit..."

    return assistant_message


def build_conversation(user_message):
    return [
        {"role": "system",
         "content": f"Expand on each of the subtopics provided by the user on the topic: {user_message}. "
                    f"You can consider elaborating on the key ideas, offering supporting examples, and explaining "
                    f"any details that you think would enhance the audience's understanding of the topic. Don't give me guidelines put directly the contents"
                    f"It should strictly contain the title (dont put \n after the slide number) and content only. "
                    f"The content should have at most 4 lines with a minimum of 15 and maximum of 20 words every lines "
                    f"in slide without nested bullets. Expand the ideas in bullet format with summary detail."},
        {"role": "user", "content": user_message}
    ]


def slide_chat_development(structure, instruction, slideNum):
    conversation = slide_build_conversation(structure, instruction, slideNum)
    try:
        assistant_message = generate_assistant_message(conversation)
    except openai.error.RateLimitError as e:
        assistant_message = "Rate limit exceeded. Sleeping for a bit..."

    return assistant_message

def slide_build_conversation(structure, instruction, slideNum):
    return [
        {"role": "system",
         "content": f"This is my slides content structure\n{str(structure)}"
                    f"change the slide {str(slideNum)} based on the instructions given: {str(instruction)}"
                    f"the output should follow the format in the structure."
                    f"It should contain at most 4 lines every slide."
                    f"give me only the slide title and new contents for the slide {str(slideNum)}"
         },
        {"role": "user", "content": structure}
    ]
def generate_assistant_message(conversation):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )
    return response['choices'][0]['message']['content']