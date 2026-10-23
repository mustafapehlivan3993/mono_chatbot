import os

from flask import Flask, jsonify
from flask_cors import CORS


DEFAULT_ORIGINS = (
    'https://mustafapehlivan22.wixstudio.com',
    'https://mustafapehlivan22-mononutrition.editor.wix.com',
)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
    if test_config:
        app.config.update(test_config)

    origins = [origin.strip().rstrip('/') for origin in
               os.getenv('CORS_ORIGINS', ','.join(DEFAULT_ORIGINS)).split(',')
               if origin.strip()]
    CORS(app, resources={r'/sohbet': {}, r'/api/.*': {}},
         origins=origins, methods=['GET', 'POST', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization'],
         supports_credentials=False, always_send=False, max_age=600)

    from app.routes import bp
    app.register_blueprint(bp)

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(hata='İstek boyutu sınırı aşıldı.'), 413

    return app
