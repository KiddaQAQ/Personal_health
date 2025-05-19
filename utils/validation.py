from flask import jsonify
import logging
import jsonschema

logger = logging.getLogger(__name__)

def validate_request(data, required_fields):
    """
    验证请求数据中是否包含所有必需字段
    
    参数:
        data: 请求数据
        required_fields: 必需字段列表
    
    返回:
        如果验证失败，抛出异常
    """
    if not data:
        raise ValueError('未提供请求数据')
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f'缺少必要字段: {", ".join(missing_fields)}')
    
    return True

def validate_numeric_fields(data, numeric_fields):
    """
    验证请求数据中的数值字段
    
    参数:
        data: 请求数据
        numeric_fields: 需要验证为数值的字段列表
    
    返回:
        如果验证失败，抛出异常
    """
    invalid_fields = []
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                float(data[field])
            except (ValueError, TypeError):
                invalid_fields.append(field)
    
    if invalid_fields:
        raise ValueError(f'以下字段必须为数值类型: {", ".join(invalid_fields)}')
    
    return True

def validate_date_format(data, date_fields, format='%Y-%m-%d'):
    """
    验证请求数据中的日期字段格式
    
    参数:
        data: 请求数据
        date_fields: 需要验证为日期的字段列表
        format: 日期格式
    
    返回:
        如果验证失败，抛出异常
    """
    from datetime import datetime
    
    invalid_fields = []
    for field in date_fields:
        if field in data and data[field]:
            try:
                datetime.strptime(data[field], format)
            except ValueError:
                invalid_fields.append(field)
    
    if invalid_fields:
        raise ValueError(f'以下字段日期格式无效: {", ".join(invalid_fields)}，请使用格式 {format}')
    
    return True

def validate_request_json(data, schema):
    """
    使用JSONSchema验证请求数据
    
    参数:
        data: 请求数据 (字典格式)
        schema: JSONSchema验证模式
        
    返回:
        如果验证成功返回None，否则返回错误消息
    """
    if not data:
        return "未提供请求数据"
    
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"JSON验证错误: {str(e)}")
        return f"数据验证失败: {e.message}"
    
    return None 