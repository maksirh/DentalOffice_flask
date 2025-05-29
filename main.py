import os
from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager
from db import db
from models import User

def create_app():
    app = Flask(__name__)

    # Конфігурація
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret'),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'DATABASE_URL',
            'postgresql+pg8000://postgres:26041564@127.0.0.1:5432/dentalDBFlask'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'false').lower() in ('1', 'true')
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() in ('1', 'true')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = 'main.login'
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    mail = Mail(app)

    from routes import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='')

    app.extensions['mail'] = mail

    return app


# Створюємо і запускаємо додаток
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
