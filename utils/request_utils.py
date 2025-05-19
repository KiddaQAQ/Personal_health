from flask import request
import logging

logger = logging.getLogger(__name__)

def validate_params(data, required_params, allow_empty=False):
    """
    验证请求参数是否包含所有必需的参数
    
    参数:
        data: 请求数据字典
        required_params: 必需参数列表
        allow_empty: 是否允许空值
        
    返回:
        如果所有必需参数都存在且有效，则返回True；否则返回False
    """
    if not data:
        logger.warning("验证参数失败：请求数据为空")
        return False
    
    for param in required_params:
        if param not in data:
            logger.warning(f"验证参数失败：缺少必需参数 {param}")
            return False
        if not allow_empty and data[param] in [None, '', []]:
            logger.warning(f"验证参数失败：参数 {param} 值为空")
            return False
    
    return True

def get_pagination_params(default_page=1, default_per_page=10, max_per_page=100):
    """
    从请求参数中获取分页参数
    
    参数:
        default_page: 默认页码
        default_per_page: 默认每页记录数
        max_per_page: 最大每页记录数
        
    返回:
        page, per_page, offset, limit: 页码，每页记录数，起始偏移量，限制数量
    """
    try:
        page = request.args.get('page', default_page, type=int)
        per_page = request.args.get('per_page', default_per_page, type=int)
        
        # 确保页码和每页记录数都是正数
        page = max(1, page)
        per_page = max(1, min(per_page, max_per_page))
        
        offset = (page - 1) * per_page
        limit = per_page
        
        return page, per_page, offset, limit
    except Exception as e:
        logger.error(f"获取分页参数时出错: {str(e)}")
        return default_page, default_per_page, 0, default_per_page 