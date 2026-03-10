# API 文档

## POST /api/nodes/report

提交节点状态报告。

### 请求方法
`POST`

### 请求头
- `Content-Type`: `application/json`

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `hotkey` | string | 是 | 节点的hotkey，非空字符串 |
| `nodeType` | string | 是 | 节点类型，必须是 `"miner"` 或 `"validator"` |
| `version` | string | 是 | 节点版本号，非空字符串 |
| `status` | string | 是 | 节点状态描述，非空字符串 |
| `uptime` | number | 是 | 节点运行时间（秒），必须为非负数 |
| `timestamp` | number | 是 | 时间戳（Unix秒），必须为正数 |
| `signature` | string | 是 | 签名，非空字符串 |
| `metadata` | object | 否 | 元数据对象，最多64个键，JSON字符串大小不超过512KB |

### 元数据说明

#### Validator节点的特殊metadata
当 `nodeType` 为 `"validator"` 时，`metadata` 可以包含以下特殊字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `miner_scores` | object | 矿工评分数据，键为矿工hotkey，值为评分对象 |
| `block_height` | number | 当前区块高度 |

#### miner_scores 对象结构
| 字段 | 类型 | 说明 |
|------|------|------|
| `uid` | number | 矿工UID |
| `score` | number | 评分 |
| `weight` | number | 权重 |
| `cost` | number | 成本（美元） |
| `qualified` | boolean | 是否合格 |
| `pack_url` | string | 数据包URL |

### 请求示例

```json
{
  "hotkey": "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6f",
  "nodeType": "validator",
  "version": "1.0.0",
  "status": "active",
  "uptime": 86400,
  "timestamp": 1710000000,
  "signature": "0xabc123...",
  "metadata": {
    "block_height": 12345,
    "miner_scores": {
      "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6e": {
        "uid": 1,
        "score": 95.5,
        "weight": 1.0,
        "cost": 10.5,
        "qualified": true,
        "pack_url": "https://example.com/pack1.zip"
      }
    }
  }
}
```

### 成功响应

```json
{
  "success": true,
  "node": {
    "hotkey": "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6f",
    "nodeType": "validator",
    "lastSeen": "2025-03-09T10:30:00.000Z"
  }
}
```

### 错误响应

| 错误类型 | 说明 |
|----------|------|
| 请求体不是对象 | `"Request body must be a JSON object"` |
| hotkey无效 | `"hotkey is required and must be a non-empty string"` |
| nodeType无效 | `"nodeType must be one of: miner, validator"` |
| version无效 | `"version is required"` |
| status无效 | `"status is required"` |
| uptime无效 | `"uptime must be a non-negative number (seconds)"` |
| timestamp无效 | `"timestamp is required (unix seconds)"` |
| signature无效 | `"signature is required"` |
| 签名验证失败 | 验证错误信息 |
| 服务器错误 | `"Internal server error"` |

### 处理流程

1. 验证请求体字段格式
2. 验证签名
3. 提取请求者IP地址（从 `x-forwarded-for` 或 `x-real-ip` 头）
4. 更新节点心跳记录到 Supabase
5. 插入报告日志到 Supabase
6. 如果是 validator 且包含 `miner_scores` 元数据，提取并存储矿工评分数据
7. 返回成功响应

---

## GET /api/nodes/status

获取节点状态摘要。

### 请求方法
`GET`

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | 过滤节点类型，`"miner"` 或 `"validator"` |

### 响应示例

```json
{
  "totalMiners": 100,
  "totalValidators": 10,
  "onlineMiners": 95,
  "onlineValidators": 9,
  "nodes": [
    {
      "hotkey": "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6e",
      "nodeType": "miner",
      "version": "1.0.0",
      "status": "active",
      "uptime": 86400,
      "timestamp": 1710000000,
      "signature": "0xabc123...",
      "lastSeen": "2025-03-09T10:30:00.000Z",
      "ip": "192.168.1.1"
    }
  ]
}
```

---

## GET /api/reports

获取报告日志。

### 请求方法
`GET`

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | 否 | 日期格式 `YYYY-MM-DD`，如果提供则返回该日期的报告 |

### 响应示例（不带date参数）

```json
{
  "files": [
    {
      "name": "2025-03-09.jsonl",
      "date": "2025-03-09",
      "size": 150
    }
  ]
}
```

### 响应示例（带date参数）

```json
{
  "date": "2025-03-09",
  "count": 150,
  "records": [
    {
      "id": 1,
      "hotkey": "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6e",
      "node_type": "miner",
      "version": "1.0.0",
      "status": "active",
      "uptime": 86400,
      "timestamp": 1710000000,
      "ip": "192.168.1.1",
      "metadata": {}
    }
  ]
}
```

---

## GET /api/scores

获取排行榜数据（基于成本的评分系统）。

### 请求方法
`GET`

### 缓存
响应缓存5分钟（`revalidate: 300`）

### 响应示例

```json
{
  "blockHeight": 12345,
  "activeMiners": 50,
  "totalMiners": 100,
  "qualifiedMiners": 45,
  "isBootstrap": false,
  "validatorCount": 10,
  "entries": [
    {
      "rank": 1,
      "uid": 1,
      "hotkey": "5FFApaS75bvpgP9gQ5hTUdZHiTc6LB2VPP9gvHN6VQCNug6e",
      "qualified": true,
      "totalCostUsd": 10.5,
      "score": 95.5,
      "packHash": "abc123...",
      "packUrl": "https://example.com/pack1.zip",
      "commitBlock": 12340,
      "isActive": true,
      "isWinner": true,
      "validatorCount": 8,
      "rewardShare": 0.15
    }
  ],
  "scenarioNames": ["scenario1", "scenario2"],
  "updatedAt": "2025-03-09T10:30:00.000Z"
}
```

### 空数据响应

```json
{
  "blockHeight": 0,
  "activeMiners": 0,
  "totalMiners": 0,
  "qualifiedMiners": 0,
  "isBootstrap": true,
  "validatorCount": 0,
  "entries": [],
  "scenarioNames": [],
  "updatedAt": "2025-03-09T10:30:00.000Z",
  "message": "No epoch data available"
}
```
