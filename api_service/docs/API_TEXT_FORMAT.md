# API文字描述格式说明

## 概述

API现在返回结构化的文字描述，而不是纯数值，便于前端直接渲染和用户理解。

## 响应格式

所有API响应都遵循以下统一格式：

```json
{
  "success": true,
  "message": "操作结果描述",
  "template": "模板类型",
  "data": {
    // 详细数据
  },
  "summary": {
    // 文字描述摘要
  }
}
```

## 模板类型

### 1. tuning_result - 调优结果模板

**接口**: `POST /api/tune`

**响应示例**:
```json
{
  "success": true,
  "message": "内核参数调优完成（包含元学习）",
  "template": "tuning_result",
  "data": {
    "optimized_params": {...},
    "performance_improvement": {...},
    "confidence_score": 0.85,
    "baseline_metrics": {...},
    "final_metrics": {...}
  },
  "summary": {
    "status": "success",
    "performance_description": "系统性能显著提升，QPS上升了15.2%，响应时间大幅缩短",
    "params_changed": "调整了8个内核参数",
    "system_type": "检测到kylin系统",
    "confidence_description": "调优结果较为可信，可以应用"
  }
}
```

**文字描述规则**:
- `performance_description`: 根据性能提升百分比生成描述
  - >20%: "系统性能显著提升，QPS上升了X%，响应时间大幅缩短"
  - >10%: "系统性能明显改善，QPS提升了X%，响应时间明显减少"
  - >5%: "系统性能有所提升，QPS增加了X%，响应时间略有改善"
  - >0%: "系统性能小幅提升，QPS增长了X%，响应时间轻微改善"
  - ≤0%: "系统性能保持稳定，未发现明显改进"

- `confidence_description`: 根据置信度生成描述
  - >0.9: "调优结果高度可信，建议应用"
  - >0.7: "调优结果较为可信，可以应用"
  - >0.5: "调优结果可信度一般，建议观察"
  - ≤0.5: "调优结果可信度较低，建议谨慎应用"

### 2. v9_status - V9状态模板

**接口**: `GET /api/model/v9/status`

**响应示例**:
```json
{
  "success": true,
  "message": "V9模型状态获取成功",
  "template": "v9_status",
  "data": {
    "enhancement_enabled": true,
    "fallback_count": 2,
    "safety_threshold": 0.8,
    "meta_learning": true,
    "bayesian_optimization": true,
    "nas_architecture": {...},
    "training_stats": {...}
  },
  "summary": {
    "status": "active",
    "model_status": "V9模型运行正常，已启用元学习, 贝叶斯优化等增强功能",
    "enhancement_description": "V9增强功能已启用",
    "safety_description": "安全阈值设置为0.8，确保系统稳定性",
    "fallback_description": "已触发2次安全回退机制"
  }
}
```

**文字描述规则**:
- `model_status`: 根据启用的功能生成描述
- `enhancement_description`: 增强功能状态描述
- `safety_description`: 安全机制描述
- `fallback_description`: 回退机制描述

### 3. rollback_result - 回滚结果模板

**接口**: `POST /api/rollback`

**响应示例**:
```json
{
  "success": true,
  "message": "参数已回滚到原始状态",
  "template": "rollback_result",
  "data": {
    "rolled_back_params": {...},
    "original_params": {...}
  },
  "summary": {
    "status": "rolled_back",
    "rollback_description": "系统已成功回滚12个内核参数，所有调优更改已撤销",
    "params_restored": "已恢复12个内核参数",
    "action": "回滚操作已完成，系统已恢复到调优前状态"
  }
}
```

**文字描述规则**:
- `rollback_description`: 根据参数数量生成描述
  - >10个: "系统已成功回滚X个内核参数，所有调优更改已撤销"
  - >5个: "系统已回滚X个内核参数，调优效果已清除"
  - >0个: "系统已恢复X个内核参数到原始状态"
  - 0个: "系统参数保持原始状态，无需回滚"

## 前端渲染建议

1. **直接显示**: 可以直接显示 `summary` 中的文字描述
2. **条件渲染**: 根据 `template` 字段选择不同的渲染模板
3. **状态指示**: 使用 `status` 字段控制UI状态
4. **详细信息**: 从 `data` 字段获取详细数据用于图表等

## 测试方法

运行测试脚本验证文字描述格式：

```bash
cd api_service
python test_text_format.py
```

## 优势

1. **用户友好**: 文字描述比数值更易理解
2. **前端简化**: 减少前端数据处理逻辑
3. **统一格式**: 所有接口使用相同的响应结构
4. **可扩展**: 易于添加新的描述模板 