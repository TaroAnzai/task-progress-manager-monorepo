from flask_smorest import Blueprint
from flask.views import MethodView
from flask import send_file
from flask_login import login_required, current_user

from app.services.task_export_service import TaskDataExporter
from app.models import db
from app.schemas import YAMLResponseSchema, ErrorResponseSchema
from app.service_errors import ServiceError
from app.decorators import with_common_error_responses

task_export_bp = Blueprint("TaskExport", __name__, url_prefix="/exports", description="タスクエクスポート")


excel_download_doc = {
      "description": "Excel file",
      "headers": {
        "Content-Disposition": {
          "schema": {"type": "string"},
          "description": "Attachment filename",
        }
      },
      "content": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
          "schema": {"type": "string", "format": "binary"}
        }
      },
    }

@task_export_bp.route('/excel')
class ExportExcelResource(MethodView):
    @login_required
    @task_export_bp.doc(responses={200: excel_download_doc})
    def get(self):
        """タスクをExcelでエクスポート"""
        exporter = TaskDataExporter(current_user.id, db)
        file = exporter.export_as_excel()
        return send_file(
            file,
            as_attachment=True,
            download_name="tasks.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

@task_export_bp.route('/yaml')
class ExportYAMLResource(MethodView):
    @login_required
    @task_export_bp.response(200, YAMLResponseSchema)
    @with_common_error_responses(task_export_bp)
    def get(self):
        """タスクをYAMLでエクスポート"""
        exporter = TaskDataExporter(current_user.id, db)
        yaml_data = exporter.export_as_yaml()
        return {"yaml": yaml_data}

