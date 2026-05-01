from flask_smorest import Blueprint
from flask.views import MethodView
from app.schemas import MessageSchema

test_bp = Blueprint('Test', __name__, url_prefix ="", description="テスト用エンドポイント")

@test_bp.route('/ping')
class PingResource(MethodView):
    @test_bp.response(200, MessageSchema)
    def get(self):
        """動作確認用"""
        return {"message": "pong"}
