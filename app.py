import openai
import os
import uuid
import firebase_admin

from flask import Flask, request, redirect, url_for, flash, session, send_from_directory, send_file
from views import *
from firebase_admin import credentials, firestore, storage
from flask_login import login_required, logout_user
from utils.generate import parse_response, create_ppt, update_slide_ppt
from utils.chatdev import chat_development, slide_chat_development
from pptx import Presentation
from pptx.dml.color import RGBColor
from werkzeug.utils import secure_filename
import aspose.slides as slides
import aspose.pydrawing as drawing


app: Flask = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.register_blueprint(home)
app.register_blueprint(landing)
app.register_blueprint(account)
app.register_blueprint(choose)
app.register_blueprint(generate)
app.register_blueprint(presentation)
app.register_blueprint(test)

# Generate a random secret key
app.secret_key = os.urandom(24)


# Your web app's Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyBl2jxG_tenXKAX2NySytDXgw3PSoqaci0",
    "authDomain": "smartsync-ade70.firebaseapp.com",
    "projectId": "smartsync-ade70",
    "storageBucket": "smartsync-ade70.appspot.com",
    "messagingSenderId": "602190235087",
    "appId": "1:602190235087:web:dcc245609c0ccd2f1d3eba",
    "measurementId": "G-MWF9ER8V2Z"
}

# OpenAI API key
openai.api_key = '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'

# Your Firebase configuration
cred = credentials.Certificate(r"C:\Users\HP\PycharmProjects\smartsync-ade70-firebase-adminsdk-l2ti0-1ea8a94791.json")
firebase_admin.initialize_app(cred)

# Initialize Firebase Storage
firebase_storage = storage.bucket(app=firebase_admin.get_app(), name="smartsync-ade70.appspot.com")

# Reference to the Firestore database
db = firestore.client()

os.makedirs('generated', exist_ok=True)


@app.route('/')
def default():
    return render_template('LandingPage.html')


# for signin
@app.route('/signin', methods=['POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            # Query the users collection for the specified username
            users_ref = db.collection('users')
            query = users_ref.where('username', '==', username).limit(1)
            user_documents = list(query.stream())
            # Check if the user exists
            if len(user_documents) == 1:
                user_doc = user_documents[0].to_dict()
                # Now you have the user document, and you can check the password or perform further authentication steps
                # For simplicity, I'm assuming you store the password in the user document (Note: In practice, passwords
                # should be hashed and securely stored)
                if user_doc['password'] == password:
                    # Authentication successful, add your session handling or redirection logic
                    session['username'] = username
                    return redirect(url_for('home.home_route'))
                else:
                    flash('Invalid username or password', 'error')
                    return render_template('SignIn_UI.html')
            else:
                flash('User not found!', 'error')
                return render_template('SignIn_UI.html')
        except Exception as e:
            # Error during authentication
            print(f"Error during sign-in: {e}")
            flash('Error during sign-in', 'error')
            return render_template('SignIn_UI.html')
    # Handle other cases (GET request, etc.)
    return redirect(url_for('default'))


# for signing up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Extract user data from the form
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        contact_number = request.form['contact_number']
        # Check for non-empty fields
        if not all([username, password, first_name, last_name, email, contact_number]):
            flash('All fields must be filled out.', 'error')
            return render_template('SignUp_UI.html')
        # Check email format
        if not is_valid_email(email):
            flash('Invalid email address.', 'error')
            return render_template('SignUp_UI.html')
        # Check contact number format
        if not is_valid_contact_number(contact_number):
            flash('Invalid contact number.', 'error')
            return render_template('SignUp_UI.html')
        try:
            # Create a new user document in the 'users' collection
            user_ref = db.collection('users').document(username)
            user_ref.set({
                'username': username,
                'password': password,  # Note: You might want to hash the password for security
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'contact_number': contact_number
            })
            # Successful sign-up, you can add session handling or redirect as needed
            flash('Signup successful! You can now log in.', 'success')
            session['username'] = username
            return redirect(url_for('home.home_route'))
        except Exception as e:
            # Error during user creation
            print(f"Error during sign-up: {e}")
            flash('Error during sign-up', 'error')
            return render_template('SignUp_UI.html')
    return render_template('SignUp_UI.html')


# checks if inputted email has @
def is_valid_email(email):
    return '@' in email


# checks if inputted contact_number is a digit
def is_valid_contact_number(contact_number):
    return contact_number.isdigit()


# Context processor to make user_info(firstname) available to all templates
@app.context_processor
def inject_user_info():
    user_info = {'first_name': None, 'username': None, 'is_logged_in': False}
    # Check if the user is authenticated
    if 'username' in session:
        username = session['username']
        user_info['is_logged_in'] = True
        # Retrieve user information from Firestore using the username
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).limit(1)
        user_documents = list(query.stream())
        if len(user_documents) == 1:
            user_doc = user_documents[0].to_dict()
            user_info['first_name'] = user_doc.get('first_name')
            user_info['username'] = username
    return {'user_info': user_info}


# Get response for GenerateKeyPoints
@app.route('/get_response', methods=['POST'])
def get_response():
    topic = request.form['topic']
    num_slides = request.form.get('num_slides')
    objectives = request.form['objectives']
    prompt = (
        f"You are an expert in {topic}. Write the slide titles for a powerpoint presentation covering the "
        f"following topics and objectives {objectives}. Make it {num_slides} slides."
    )
    # Generate a response from OpenAI's GPT-3
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1000  # You can adjust the token limit as needed
    )
    bot_response = response.choices[0].text.strip()
    # Split the response into slide contents
    slide_contents = bot_response.split('\n')
    # Initialize the structured response with the title slide
    structured_response = f"\nTopic: {topic}\n\n"
    # Add slide content for the subsequent slides
    current_slide = 0  # Start with the second slide
    for i in range(len(slide_contents)):
        content = slide_contents[i].strip()
        if content and content[0].isdigit():
            # New slide detected
            current_slide += 1
            structured_response += f"Slide {current_slide}: {content.split(maxsplit=1)[1]}\n"
        else:
            structured_response += f"{content}\n"
    return structured_response


@app.route('/GeneratePresentation', methods=['POST'])
def generate_presentation():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'action1':
            content = request.form.get('contents')
            template_choice = request.form.get('templates')
            print(template_choice)
            topic = request.form.get('title')
            presentor = request.form.get('presentation-presentor')
            if template_choice == "simple":
                template_choice = "simple"
            elif template_choice == "dark_modern":
                template_choice = "dark_modern"
            elif template_choice == "bright":
                template_choice = "bright_modern"
            elif template_choice == "darkblue":
                template_choice = "dark_blue"

            assistant_response = chat_development(content)
            session['assistant_response'] = assistant_response
            session['template'] = template_choice
            print(assistant_response)
            slides_content = parse_response(assistant_response)
            print(slides_content)

            try:
                ppt_filename = create_ppt(slides_content, template_choice, topic, presentor)
                ppt_path = os.path.join(os.path.abspath('generated'), 'generated_presentation.pptx')

                # Convert the PowerPoint presentation to images
                images_folder = os.path.join('generated', 'slides')
                os.makedirs(images_folder, exist_ok=True)
                # image_paths = convert_ppt_to_images(ppt_path, images_folder)
                # image_paths = save_slides_as_images(ppt_path, images_folder)
                images_folder = os.path.join('generated', 'ppt_test')
                os.makedirs(images_folder, exist_ok=True)
                conversion_id = save_slides_as_images(ppt_path, images_folder)
                return render_template('GeneratePresentation.html', conversion_id=conversion_id)
            except Exception as e:
                flash(f'Error: {e}', 'error')
                return render_template('GeneratePresentation.html')
        elif action == 'action2':
            slideNum = request.form.get('slide_num')
            instruction = request.form.get('instruction')
            uploaded_file = request.files.get('filename')
            # template = request.form.get('instruction')
            is_auto_generated = 'isAuto' in request.form
            if uploaded_file:
                hasPicture = True
            else:
                hasPicture = False
            print(slideNum)
            print(instruction)
            print(is_auto_generated)
            file_path = ""
            if not is_auto_generated:
                if 'filename' not in request.files:
                    return "No file part"

                uploaded_file = request.files['filename']

                # If the user does not select a file, the browser submits an empty file without a filename
                if uploaded_file.filename == '':
                    return "No selected file"

                # Save the file to a location (replace 'uploads' with your desired directory)
                upload_folder = 'uploads'
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, uploaded_file.filename)
                uploaded_file.save(file_path)
            slide_content_from_session = session.get('assistant_response')
            assistant_response = slide_chat_development(slide_content_from_session, instruction, slideNum)
            print(assistant_response)
            slides_content = parse_response(assistant_response)
            print(slides_content)
            template_choice = session.get('template')
            update_slide_ppt(slides_content, file_path, is_auto_generated, hasPicture, template_choice, slideNum)
            return render_template('GeneratePresentation.html')


conversion_counter = 0
def save_slides_as_images(pptx_path, output_folder):
    global conversion_counter
    conversion_counter += 1
    conversion_id = conversion_counter

    pres = slides.Presentation(pptx_path)

    # Convert conversion_id to a string to use it in the folder name
    conversion_folder_name = f"conversion_{conversion_id}"
    conversion_images_folder = os.path.join(output_folder, conversion_folder_name)

    if not os.path.exists(conversion_images_folder):
        print("0")
        os.makedirs(conversion_images_folder)

    # Loop through slides
    for index, slide in enumerate(pres.slides):
        # Define custom size
        size = drawing.Size(1080, 720)

        # Save as PNG within the conversion folder
        image_path = os.path.join(conversion_images_folder, f"slide_{index}.png")
        slide.get_thumbnail(size).save(image_path, drawing.imaging.ImageFormat.png)

    return [f"slide_{index}.png" for index in range(len(pres.slides))], conversion_id


# @app.route('/Test', methods=['POST'])
# def test():
#     if request.method == 'POST':
#         action = request.form.get('action')
#
#         if action == 'action1':
#             content = request.form.get('contents')
#             template_choice = request.form.get('templates')
#             print(template_choice)
#             topic = request.form.get('title')
#             presentor = request.form.get('presentation-presentor')
#             if template_choice == "modern":
#                 template_choice = "dark_modern"
#             elif template_choice == "bright":
#                 template_choice = "bright_modern"
#             elif template_choice == "darkblue":
#                 template_choice = "dark_blue"
#             else:
#                 template_choice = template_choice
#             assistant_response = chat_development(content)
#             session['assistant_response'] = assistant_response
#             session['template'] = template_choice
#             print(assistant_response)
#             slides_content = parse_response(assistant_response)
#             print(slides_content)
#
#             try:
#                 ppt_filename = create_ppt(slides_content, template_choice, topic, presentor)
#                 ppt_path = os.path.join(os.path.abspath('generated'), 'generated_presentation.pptx')
#
#                 # Convert the PowerPoint presentation to images
#                 images_folder = os.path.join('generated', 'slides')
#                 os.makedirs(images_folder, exist_ok=True)
#                 image_paths = convert_ppt_to_images(ppt_path, images_folder)
#                 # image_paths = save_slides_as_images(ppt_path, images_folder)
#                 return render_template('test.html', image_paths=image_paths)
#             except Exception as e:
#                 flash(f'Error: {e}', 'error')
#                 return render_template('test.html')
#         elif action == 'action2':
#             slideNum = request.form.get('slide_num')
#             instruction = request.form.get('instruction')
#             # template = request.form.get('instruction')
#             is_auto_generated = 'isAuto' in request.form
#             print(slideNum)
#             print(instruction)
#             print(is_auto_generated)
#             file_path = ""
#             if not is_auto_generated:
#                 if 'filename' not in request.files:
#                     return "No file part"
#
#                 uploaded_file = request.files['filename']
#
#                 # If the user does not select a file, the browser submits an empty file without a filename
#                 if uploaded_file.filename == '':
#                     return "No selected file"
#
#                 # Save the file to a location (replace 'uploads' with your desired directory)
#                 upload_folder = 'uploads'
#                 if not os.path.exists(upload_folder):
#                     os.makedirs(upload_folder)
#
#                 file_path = os.path.join(upload_folder, uploaded_file.filename)
#                 uploaded_file.save(file_path)
#             slide_content_from_session = session.get('assistant_response')
#             assistant_response = slide_chat_development(slide_content_from_session, instruction, slideNum)
#             print(assistant_response)
#             slides_content = parse_response(assistant_response)
#             print(slides_content)
#             template_choice = session.get('template')
#             update_slide_ppt(slides_content, file_path, is_auto_generated, template_choice, slideNum)
#             return render_template('test.html')

# @app.route('/updateSlide', methods=['POST'])
# def update_slide():
#     if request.method == 'POST':
#         slideNum = request.form.get('slide_num')
#         instruction = request.form.get('instruction')
#         # template = request.form.get('instruction')
#         is_auto_generated = 'isAuto' in request.form
#         print(slideNum)
#         print(instruction)
#         print(is_auto_generated)
#         file_path = ""
#         if not is_auto_generated:
#             if 'filename' not in request.files:
#                 return "No file part"
#
#             uploaded_file = request.files['filename']
#
#             # If the user does not select a file, the browser submits an empty file without a filename
#             if uploaded_file.filename == '':
#                 return "No selected file"
#
#             # Save the file to a location (replace 'uploads' with your desired directory)
#             upload_folder = 'uploads'
#             if not os.path.exists(upload_folder):
#                 os.makedirs(upload_folder)
#
#             file_path = os.path.join(upload_folder, uploaded_file.filename)
#             uploaded_file.save(file_path)
#         slide_content_from_session = session.get('assistant_response')
#         assistant_response = slide_chat_development(slide_content_from_session, instruction, slideNum)
#         print(assistant_response)
#         slides_content = parse_response(assistant_response)
#         print(slides_content)
#         template_choice = session.get('template')
#         update_slide_ppt(slides_content, file_path, is_auto_generated, template_choice, slideNum)
#
#
#     return render_template('test.html')
#test
# def save_slides_as_images(input_pptx_path, output_folder):
#     pres = slides.Presentation(input_pptx_path)
#
#     # Create output folder if it doesn't exist
#     os.makedirs(output_folder, exist_ok=True)
#
#     # Loop through slides
#     for index, slide in enumerate(pres.slides):
#         # Define custom size
#         size = drawing.Size(1080, 720)
#
#         # Save as PNG
#         image_path = os.path.join(output_folder, f"slide_{index}.png")
#         slide.get_thumbnail(size).save(image_path, drawing.imaging.ImageFormat.png)
#
#     return [f"slide_{index}.png" for index in range(pres.slides.length)]

@app.route('/')
def save_and_display_slides(pptx_path, output_folder):
    image_paths = save_slides_as_images(pptx_path, output_folder)
    return render_template('view_presentation.html', image_paths=image_paths)
# Add a route to serve individual slide images
@app.route('/slide/<int:slide_number>', methods=['GET'])
def serve_slide_image(slide_number):
    images_folder = os.path.join('generated', 'slides')
    image_path = os.path.join(images_folder, f"slide_{slide_number}.png")

    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    else:
        os.abort(404)


def convert_ppt_to_images(ppt_path, images_folder):
    prs = Presentation(ppt_path)

    image_paths = []

    for slide_number, slide in enumerate(prs.slides, start=1):
        # Create a new presentation with one slide
        new_prs = Presentation()
        new_slide = new_prs.slides.add_slide(new_prs.slide_layouts[5])  # Using a blank slide layout

        # Copy the shapes from the original slide to the new slide
        for shape in slide.shapes:
            if shape.has_text_frame:
                if hasattr(shape,
                           'text_frame') and shape.text_frame.text.strip():  # Check if the shape has non-empty text
                    new_shape = new_slide.shapes.add_textbox(
                        left=shape.left, top=shape.top, width=shape.width, height=shape.height
                    )
                    new_shape.text_frame.text = shape.text

                    # Access the font attribute through the text_frame property if available
                    if hasattr(new_shape.text_frame, 'text_frame') and hasattr(new_shape.text_frame.text_frame,
                                                                               'paragraphs') \
                            and new_shape.text_frame.text_frame.paragraphs:
                        new_shape.text_frame.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 0,
                                                                                                0)  # Set font color to black

        # Save the new presentation as an image
        image_path = os.path.join(images_folder, f"slide_{slide_number}.png")
        image_paths.append(image_path)
        new_prs.save(image_path)

    return image_paths


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('signin'))


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory('generated', filename, as_attachment=True)

    except FileNotFoundError:
        os.abort(404)


def save_to_firebase_storage(local_filename, title, username):
    if username and title:
        # Generate a unique filename for Firebase Storage
        firebase_filename = f"{username}_{title}_{str(uuid.uuid4())}.pptx"
        firebase_path = f"presentations/{firebase_filename}"

        # Upload the file to Firebase Storage
        firebase_storage.blob(firebase_path).upload_from_filename(local_filename)

        # Add the Firebase storage path to the "presentations" collection in Firestore
        user_ref = db.collection('presentations').document(username)
        user_ref.set({
            'username': username,
            'title': title,
            'firebase_path': firebase_path,
        })
    else:
        print("Error in saving to database")
        flash('Error: Username or title is missing.', 'error')


# try push

if __name__ == '__main__':
    app.run(debug=True)
