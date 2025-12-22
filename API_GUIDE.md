# PrepGo Practice Generator - External API 测试手册

## 服务信息

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:18300 |
| 后端 API | http://localhost:18301 |
| API 文档 | http://localhost:18301/docs |

---

## External API 端点

### 1. 生成练习题（JSON 格式）

**POST** `/api/v1/external/generate`

生成练习题并返回 **结构化 JSON 数据**，包含科目特定格式（数学 LaTeX、化学公式等）。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | ✅ | 课程 ID（见下方完整列表）|
| unit_numbers | int[] | ✅ | Unit 编号数组 |
| mcq_count | int | ❌ | MCQ 题目数量（1-50，默认 15）|
| frq_count | int | ❌ | FRQ 题目数量（0-10，默认 2）|
| difficulty | string | ❌ | 难度：easier / ap_level / harder（默认 ap_level）|

#### 测试命令

```bash
# 数学课程测试（LaTeX 格式）
curl -X POST http://localhost:18301/api/v1/external/generate \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "calculus-ab",
    "unit_numbers": [1],
    "mcq_count": 2,
    "frq_count": 1,
    "difficulty": "ap_level"
  }' | jq '.'

# 物理课程测试（公式 + 单位）
curl -X POST http://localhost:18301/api/v1/external/generate \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "physics-1",
    "unit_numbers": [1],
    "mcq_count": 2,
    "frq_count": 1
  }' | jq '.'

# 历史课程测试（文档分析）
curl -X POST http://localhost:18301/api/v1/external/generate \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "us-history",
    "unit_numbers": [1, 2],
    "mcq_count": 5,
    "frq_count": 1
  }' | jq '.'
```

---

## 完整课程 ID 列表

### Math（数学）- LaTeX 格式

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| precalculus | AP Precalculus | math |
| calculus-ab | AP Calculus AB | math |
| calculus-bc | AP Calculus BC | math |
| statistics | AP Statistics | math |
| computer-science-a | AP Computer Science A | computer-science |
| computer-science-principles | AP Computer Science Principles | computer-science |

### Science（科学）- LaTeX 公式 + 单位

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| biology | AP Biology | biology |
| chemistry | AP Chemistry | chemistry |
| environmental-science | AP Environmental Science | science |
| physics-1 | AP Physics 1 | physics |
| physics-2 | AP Physics 2 | physics |
| physics-c-electricity-and-magnetism | AP Physics C: E&M | physics |
| physics-c-mechanics | AP Physics C: Mechanics | physics |

### History（历史）- 文档分析 + DBQ

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| us-history | AP U.S. History | history |
| world-history-modern | AP World History: Modern | history |
| european-history | AP European History | history |

### Social Science（社会科学）

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| macroeconomics | AP Macroeconomics | economics |
| microeconomics | AP Microeconomics | economics |
| us-government-and-politics | AP U.S. Government & Politics | social-science |
| comparative-government-and-politics | AP Comparative Government | social-science |
| psychology | AP Psychology | social-science |
| human-geography | AP Human Geography | social-science |

### Languages（语言）

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| spanish-language-and-culture | AP Spanish Language | language |
| spanish-literature-and-culture | AP Spanish Literature | language |
| latin | AP Latin | language |
| chinese-language-and-culture | AP Chinese Language | language |
| french-language-and-culture | AP French Language | language |
| german-language-and-culture | AP German Language | language |
| italian-language-and-culture | AP Italian Language | language |
| japanese-language-and-culture | AP Japanese Language | language |

### English（英语）

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| english-language-and-composition | AP English Language | english |
| english-literature-and-composition | AP English Literature | english |

### Arts（艺术）

| course_id | 课程名称 | 格式类型 |
|-----------|---------|---------|
| art-history | AP Art History | art |
| music-theory | AP Music Theory | music |

---

## 科目特定格式说明

### Math / Physics（LaTeX 示例）

```json
{
  "question": "Evaluate the limit: $\\lim_{x \\to 3} \\frac{x^2 - x - 6}{x^2 - 9}$",
  "options": {
    "A": "$0$",
    "B": "$\\frac{5}{6}$",
    "C": "$1$",
    "D": "Undefined"
  },
  "explanation": "Factor: $x^2 - x - 6 = (x-3)(x+2)$..."
}
```

### Chemistry（化学公式）

```json
{
  "question": "Balance the equation: $H_2 + O_2 \\rightarrow H_2O$",
  "options": {
    "A": "$2H_2 + O_2 \\rightarrow 2H_2O$",
    "B": "..."
  }
}
```

### Computer Science（代码格式）

```json
{
  "stimulus": "```java\npublic static int sum(int[] arr) {\n  int total = 0;\n  for (int i = 0; i < arr.length; i++) {\n    total += arr[i];\n  }\n  return total;\n}\n```",
  "question": "What is the Big-O time complexity of this method?",
  "options": {
    "A": "$O(1)$",
    "B": "$O(n)$",
    "C": "$O(n^2)$",
    "D": "$O(\\log n)$"
  }
}
```

### History（文档分析）

```json
{
  "type": "DBQ",
  "stimulus": "**Document 1**\nSource: Thomas Jefferson, Letter to James Madison, 1787\n> \"I hold it that a little rebellion now and then is a good thing...\"",
  "parts": [
    {
      "part": "a",
      "task_verb": "Identify",
      "prompt": "Identify the historical context of this document."
    }
  ]
}
```

---

## 响应结构

```json
{
  "success": true,
  "data": {
    "course_id": "calculus-ab",
    "course_name": "AP Calculus AB",
    "unit_numbers": [1],
    "unit_titles": ["Unit 1: Limits and Continuity"],
    "mcq_count": 2,
    "frq_count": 1,
    "difficulty": "ap_level",
    "content": {
      "header": { ... },
      "mcq_questions": [ ... ],
      "frq_questions": [ ... ],
      "answer_key": { ... }
    },
    "generated_at": "2025-12-22T..."
  }
}
```

---

## 其他 API 端点

### 2. 获取课程列表（按分类）

**GET** `/api/v1/external/courses`

```bash
curl http://localhost:18301/api/v1/external/courses | jq '.data.categories'
```

### 3. 获取课程 Units

**GET** `/api/v1/external/courses/{course_id}/units`

```bash
curl http://localhost:18301/api/v1/external/courses/calculus-ab/units | jq '.'
```

### 4. 队列状态

**GET** `/api/v1/external/queue-status`

```bash
curl http://localhost:18301/api/v1/external/queue-status | jq '.'
```

---

## 难度级别说明

| difficulty | 说明 |
|------------|------|
| easier | 比 AP 考试简单，基础概念 |
| ap_level | AP 考试难度（默认）|
| harder | 比 AP 考试难，综合分析 |

---

## 前端 LaTeX 渲染

推荐使用 KaTeX 或 MathJax 渲染 LaTeX：

```tsx
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

// 渲染行内公式
<InlineMath math="x^2 + y^2 = r^2" />

// 渲染块级公式
<BlockMath math="\int_0^1 x^2 dx = \frac{1}{3}" />
```

---

## 错误处理

```json
{
  "success": false,
  "data": null,
  "error": "Course not found: invalid-course"
}
```

常见错误：
- `Course not found` - 课程 ID 无效
- `Units not found` - Unit 编号不存在
- `Request timed out` - 队列等待超时
- `Failed to parse generated content as JSON` - AI 生成格式异常，请重试
