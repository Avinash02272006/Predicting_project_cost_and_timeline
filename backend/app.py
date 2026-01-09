
from flask import Flask, send_from_directory
from flask_cors import CORS
from database import db
import os

# Init App
app = Flask(__name__, static_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "database/app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'GEN_Z_SECRET_KEY'

CORS(app)
db.init_app(app)

# Import Routes
from routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Serve Static Files
@app.route('/')
def index():
    return send_from_directory('../frontend/pages', 'index.html')

@app.route('/pages/<path:path>')
def serve_pages(path):
    return send_from_directory('../frontend/pages', path)

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('../frontend/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('../frontend/js', path)

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('../frontend/assets', path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
