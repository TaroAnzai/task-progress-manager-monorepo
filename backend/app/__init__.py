# app/__init__.py
from typing import Type, Union

from flask import Flask
from flask_cors import CORS
from app.util.register_cli import register_cli
from config import Config
from flask_smorest import Api # type: ignore

from app.extensions import db, login_manager, migrate

def create_app(config_class: Union[Type[Config], str] = Config):

    app = Flask(__name__)
    app.config.from_object(config_class)
    URL_PREFIX = app.config.get("URL_PREFIX")

    CORS(app, resources={
        r"/*": {"origins": app.config['CORS_ORIGINS']}
    })

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    register_cli(app)

    from app.auth import auth_bp

    # モデル登録
    from . import models # type: ignore

    # Flask-SmorestのApiオブジェクト生成
    api = Api(app)


    #Blueprint登録
    from app.routes.access_scope_routes import access_scope_bp
    from app.routes.ai_route import ai_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.company_routes import company_bp
    from app.routes.objectives_route import objectives_bp
    from app.routes.organization_routes import organization_bp
    from app.routes.progress_updates_route import progress_bp
    from app.routes.task_access_route import task_access_bp
    from app.routes.task_core_route import task_core_bp
    from app.routes.task_export_route import task_export_bp
    from app.routes.task_order_route import task_order_bp
    from app.routes.test_routes import test_bp
    from app.routes.user_routes import user_bp
    from app.routes.reminder_routes import reminder_bp
    from app.routes.auth_password_reset_route import password_reset_bp

    api.register_blueprint(access_scope_bp, url_prefix=f"{URL_PREFIX}{access_scope_bp.url_prefix}")
    api.register_blueprint(ai_bp, url_prefix=f"{URL_PREFIX}{ai_bp.url_prefix}")
    api.register_blueprint(auth_bp, url_prefix=f"{URL_PREFIX}{auth_bp.url_prefix}")
    api.register_blueprint(company_bp, url_prefix=f"{URL_PREFIX}{company_bp.url_prefix}")
    api.register_blueprint(objectives_bp, url_prefix=f"{URL_PREFIX}{objectives_bp.url_prefix}")
    api.register_blueprint(organization_bp, url_prefix=f"{URL_PREFIX}{organization_bp.url_prefix}")
    api.register_blueprint(progress_bp, url_prefix=f"{URL_PREFIX}{progress_bp.url_prefix}")
    api.register_blueprint(task_access_bp, url_prefix=f"{URL_PREFIX}{task_access_bp.url_prefix}")
    api.register_blueprint(task_core_bp, url_prefix=f"{URL_PREFIX}{task_core_bp.url_prefix}")
    api.register_blueprint(task_export_bp, url_prefix=f"{URL_PREFIX}{task_export_bp.url_prefix}")
    api.register_blueprint(task_order_bp, url_prefix=f"{URL_PREFIX}{task_order_bp.url_prefix}")
    api.register_blueprint(test_bp, url_prefix=f"{URL_PREFIX}{test_bp.url_prefix}")
    api.register_blueprint(user_bp, url_prefix=f"{URL_PREFIX}{user_bp.url_prefix}")
    api.register_blueprint(reminder_bp, url_prefix=f"{URL_PREFIX}{reminder_bp.url_prefix}") 
    api.register_blueprint(password_reset_bp, url_prefix=f"{URL_PREFIX}{password_reset_bp.url_prefix}")

    return app

