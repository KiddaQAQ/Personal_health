# 个人健康管理系统

## 最近修复

### 2024-xx-xx 密码哈希不兼容问题修复

修复了登录时可能出现的"unsupported hash type scrypt:32768:8:1"错误。该问题是由于Python环境不支持scrypt哈希算法导致的。

#### 修复方法：

1. 更新了密码哈希算法，从scrypt改为更具兼容性的pbkdf2:sha256
2. 添加了密码验证错误处理逻辑
3. 创建了数据库密码哈希迁移脚本

#### 如果您遇到登录问题，请按照以下步骤操作：

1. 运行密码哈希迁移脚本（此操作会将所有用户密码重置为临时密码"123456"）：

```bash
python scripts/migrate_password_hash.py
```

2. 使用临时密码"123456"登录系统
3. 立即前往个人设置页面修改您的密码

#### 其他已修复问题：

1. 健康报告中运动和用药摘要不显示问题
2. 药物提醒创建失败的外键约束错误
3. 社交互动页面的点赞功能状态保存问题

## 系统简介

个人健康管理系统是一个全面的健康数据记录和分析平台，帮助用户追踪、管理和改善个人健康状况。

## 主要功能

- 健康记录：记录体重、血压、血糖等健康指标
- 饮食管理：记录饮食摄入，计算营养成分
- 运动追踪：记录运动活动和热量消耗
- 用药管理：记录药物服用和提醒
- 健康报告：生成健康数据分析报告
- 社交功能：分享健康成就与朋友互动

## 安装与运行

### 环境要求

- Python 3.8+
- Flask
- SQLAlchemy
- 其他依赖见requirements.txt

### 安装步骤

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 初始化数据库：`python init_db.py`
4. 运行应用：`python app.py`

## 联系方式

如有任何问题，请联系系统管理员。

### 技术栈
- 后端: Flask (Python)
- 数据库: MySQL
- 前端: HTML, CSS, JavaScript, Bootstrap
- 认证: JWT (JSON Web Tokens)

### 架构设计
系统采用模块化设计，将不同功能分离到独立的模块中：

- 每种健康记录类型都有独立的服务类和API路由
- 健康指标 - `health_metrics_service.py` 和 `/api/health-metrics`
- 饮食记录 - `diet_service.py` 和 `/api/diet`
- 运动记录 - `exercise_service.py` 和 `/api/exercise`
- 饮水记录 - `water_service.py` 和 `/api/water-intake`
- 药物记录 - `medication_service.py` 和 `/api/medication`

### API 接口
系统提供了丰富的REST API接口:

- 用户相关: `/api/auth/*`
- 健康指标: `/api/health-metrics/records`
- 饮食记录: `/api/diet/records`
- 运动记录: `/api/exercise/records`
- 饮水记录: `/api/water-intake/records`
- 药物记录: `/api/medication/records`
- 分析报告: `/api/analysis/*`
- 健康报告: `/api/health-report/*`
- 社交功能: `/api/social/*`

### 使用说明
1. 注册账号并登录系统
2. 在"添加记录"页面选择要添加的记录类型
3. 填写记录信息并保存
4. 在"所有记录"页面查看和管理已添加的记录
5. 使用分析工具查看健康趋势和建议

### 记录功能使用说明
系统提供了多种健康记录类型，每种类型都有独立的表单和数据处理流程:

1. **健康指标记录**: 记录体重、血压、心率等基本健康指标
2. **饮食记录**: 记录每日饮食内容、餐次和食物量
3. **运动记录**: 记录运动类型、时长、强度和消耗的卡路里
4. **饮水记录**: 记录饮水量、时间和水的类型
5. **药物记录**: 记录服用的药物、剂量和时间

### 贡献指南
欢迎贡献代码，请遵循以下步骤:
1. Fork代码库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 许可证
[许可证类型] 