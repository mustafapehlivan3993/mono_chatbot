from flask import Flask
from app.routes import bp

def create_app():                            ## Application Factory (Uygulama Fabrikası) kalıbı. Flask uygulamasını burada güvenli bir şekilde kurar ve rotalarımızı (Blueprint) birbirine bağlarız.
    
    try:
        app = Flask(__name__)               ## Flask uygulamasını başlatıyoruz
        
        app.register_blueprint(bp)          ## routes.py içinde hazırladığımız Blueprint'i ana uygulamaya kaydediyoruz
        return app

    except Exception as e:                  ## Hata Yakalama
        print(f"KRİTİK HATA (App Factory): {e}")
        raise e










    