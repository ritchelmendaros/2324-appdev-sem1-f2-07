from flask import Blueprint, render_template

landing = Blueprint('landing', __name__)
home = Blueprint('home', __name__)
account = Blueprint('account', __name__)
choose = Blueprint('choose', __name__)
generate = Blueprint('generate', __name__)
presentation = Blueprint('presentation', __name__)
test = Blueprint('test', __name__)
choosetemplate = Blueprint('choosetemplate', __name__)


@landing.route('/')
def landing_page_route():
    return render_template('LandingPage.html')


@test.route('/Test')
def landing_page_route():
    return render_template('test.html')


@home.route('/Home')
def home_route():
    return render_template('Home.html')


@account.route('/SignIn')
def signin_route():
    return render_template('SignIn_UI.html')


@account.route('/SignUp')
def signup_route():
    return render_template('SignUp_UI.html')


@choose.route('/Choose')
def choose_route():
    return render_template('Choose.html')


@generate.route('/GeneratePresentation')
def presentation_route():
    return render_template('GeneratePresentation.html')


@generate.route('/GenerateKeyPoints')
def key_points_route():
    return render_template('GenerateKeyPoints.html')


@presentation.route('/ViewPresentation')
def view_presentation_route():
    return render_template('ViewPresentation.html')


@choose.route('/ChooseTemplate')
def choosetemplate_route():
    return render_template('ChooseTemplates.html')
