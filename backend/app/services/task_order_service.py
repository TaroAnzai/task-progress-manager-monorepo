from app.models import db, UserTaskOrder, Task
from app.service_errors import ServiceValidationError

def get_task_order(user_id):
    orders = (
        db.session.query(UserTaskOrder)
        .filter_by(user_id=user_id)
        .order_by(UserTaskOrder.display_order)
        .all()
    )

    result = []
    for order in orders:
        if order.task and not order.task.is_deleted:
            result.append({
                'task_id': order.task_id,
                'title': order.task.title
            })

    return result

def save_task_order(user_id, data):
    task_ids = data.get('task_ids', [])
    if not isinstance(task_ids, list):
        raise ServiceValidationError('task_ids はリストである必要があります')

    # 一括削除 & 再登録
    db.session.query(UserTaskOrder).filter_by(user_id=user_id).delete()
    for index, task_id in enumerate(task_ids):
        db.session.add(UserTaskOrder(user_id=user_id, task_id=task_id, display_order=index))

    db.session.commit()
    return {'message': 'タスクの並び順を保存しました'}
