from typing import Optional

def check_response_message(expected: str, response: dict, key: Optional[str] = None) -> bool:
    """
    エラーレスポンス内に期待する文字列が含まれているかチェックする関数
    
    :param expected: 確認する文字列
    :param response: APIレスポンス（辞書形式）
    :param key: 特定のキー名（例: "order"）。Noneならすべてのキーを対象にする
    :return: 文字列が見つかれば True、見つからなければ False
    """
    json_errors = response.get("errors", {}).get("json", {})
    
    # 特定のキーが指定された場合
    if key:
        values = json_errors.get(key, [])
        if isinstance(values, list):
            return any(expected in v for v in values)
        elif isinstance(values, str):
            return expected in values
        return False

    # キー指定がない場合 → すべてのキーを確認
    for value in json_errors.values():
        if isinstance(value, list):
            if any(expected in v for v in value):
                return True
        elif isinstance(value, str):
            if expected in value:
                return True
    return False
