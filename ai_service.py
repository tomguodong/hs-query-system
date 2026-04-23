# -*- coding: utf-8 -*-
"""
海关编码智能查询系统 - AI服务模块
使用OpenRouter免费大模型进行HS编码智能分类
Version: 1.0.0
"""

import json
import time
import requests
from models import get_db_context

OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 可用模型列表（按优先级排序）
AVAILABLE_MODELS = [
    {"id": "nvidia/nemotron-3-super-120b-a12b:free", "name": "NVIDIA Nemotron 3 Super", "context": 262144},
    {"id": "minimax/minimax-m2.5:free", "name": "MiniMax M2.5", "context": 196608},
    {"id": "openai/gpt-oss-120b:free", "name": "OpenAI GPT-OSS 120B", "context": 131072},
    {"id": "openai/gpt-oss-20b:free", "name": "OpenAI GPT-OSS 20B", "context": 131072},
    {"id": "qwen/qwen3-next-80b-a3b-instruct:free", "name": "Qwen3 Next 80B", "context": 262144},
    {"id": "google/gemma-4-26b-a4b-it:free", "name": "Google Gemma 4 26B", "context": 262144},
    {"id": "google/gemma-4-31b-it:free", "name": "Google Gemma 4 31B", "context": 262144},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Meta Llama 3.3 70B", "context": 65536},
    {"id": "nousresearch/hermes-3-llama-3.1-405b:free", "name": "Nous Hermes 3 405B", "context": 131072},
    {"id": "arcee-ai/trinity-large-preview:free", "name": "Arcee AI Trinity Large", "context": 131000},
    {"id": "inclusionai/ling-2.6-flash:free", "name": "InclusionAI Ling 2.6 Flash", "context": 262144},
    {"id": "z-ai/glm-4.5-air:free", "name": "Z.ai GLM 4.5 Air", "context": 131072},
]

# 当前活跃模型索引
current_model_index = 0


def get_current_model():
    """获取当前使用的模型"""
    global current_model_index
    return AVAILABLE_MODELS[current_model_index]


def switch_to_next_model():
    """切换到下一个可用模型"""
    global current_model_index
    current_model_index = (current_model_index + 1) % len(AVAILABLE_MODELS)
    return get_current_model()


def set_current_model(model_id):
    """设置当前使用的模型（按model_id查找）"""
    global current_model_index
    for i, model in enumerate(AVAILABLE_MODELS):
        if model["id"] == model_id:
            current_model_index = i
            return {"success": True, "model": get_current_model()}
    return {"success": False, "error": f"模型 {model_id} 不在可用列表中"}


def refresh_free_models():
    """从OpenRouter API获取最新的免费模型列表"""
    global AVAILABLE_MODELS, current_model_index
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"success": False, "error": f"API请求失败: {resp.status_code}"}
        data = resp.json()
        all_models = data.get("data", [])
        free_models = []
        for m in all_models:
            pricing = m.get("pricing", {})
            prompt_price = float(pricing.get("prompt", "1") or "1")
            if prompt_price == 0:
                ctx = m.get("context_length", 0) or 0
                free_models.append({
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "context": ctx,
                })
        free_models.sort(key=lambda x: x.get("context", 0), reverse=True)
        if free_models:
            AVAILABLE_MODELS = free_models
            if current_model_index >= len(AVAILABLE_MODELS):
                current_model_index = 0
        return {
            "success": True,
            "total": len(AVAILABLE_MODELS),
            "models": AVAILABLE_MODELS[:50],
            "current_model": get_current_model()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_api_key(new_key):
    """更新OpenRouter API Key"""
    global OPENROUTER_API_KEY
    OPENROUTER_API_KEY = new_key
    return {"success": True, "message": "API Key已更新"}


def call_openrouter(messages, model_id=None, max_tokens=1000, temperature=0.3):
    """
    调用OpenRouter API
    支持自动切换模型
    """
    global current_model_index

    if model_id is None:
        model_id = get_current_model()["id"]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hs-query-system.local",
        "X-Title": "HS Code Query System"
    }

    payload = {
        "model": model_id,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    for attempt in range(3):
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    print(f"⚠️ 模型 {model_id} 返回非JSON响应，切换模型...")
                    model_info = switch_to_next_model()
                    model_id = model_info["id"]
                    payload["model"] = model_id
                    time.sleep(0.5)
                    continue
                if "choices" in data and len(data["choices"]) > 0:
                    return {
                        "success": True,
                        "content": data["choices"][0]["message"]["content"],
                        "model": data.get("model", model_id),
                        "usage": data.get("usage", {}),
                        "model_id": model_id
                    }
                else:
                    return {"success": False, "error": "模型返回了空响应"}

            elif response.status_code == 429:
                # 限流，切换模型
                print(f"⚠️ 模型 {model_id} 限流，切换模型...")
                model_info = switch_to_next_model()
                model_id = model_info["id"]
                payload["model"] = model_id
                time.sleep(1)
                continue

            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "未知错误")
                if "location is not supported" in error_msg:
                    print(f"⚠️ 模型 {model_id} 不支持当前地区，切换模型...")
                    model_info = switch_to_next_model()
                    model_id = model_info["id"]
                    payload["model"] = model_id
                    time.sleep(0.5)
                    continue
                return {"success": False, "error": error_msg}

            elif response.status_code in (502, 503, 504, 529):
                # 网关超时/服务不可用，切换模型重试
                print(f"⚠️ 模型 {model_id} 返回 {response.status_code}，切换模型...")
                model_info = switch_to_next_model()
                model_id = model_info["id"]
                payload["model"] = model_id
                time.sleep(1)
                continue

            else:
                return {"success": False, "error": f"API错误: HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            print(f"⚠️ 模型 {model_id} 超时，切换模型...")
            model_info = switch_to_next_model()
            model_id = model_info["id"]
            payload["model"] = model_id
            time.sleep(1)
            continue

        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "所有模型均不可用，请稍后重试"}


def classify_hs_code(product_name, product_desc="", extra_info=""):
    """
    使用AI对产品名称进行HS编码分类
    返回结构化的HS编码建议
    """
    system_prompt = """你是一个专业的海关编码(HS Code)分类专家。你的任务是根据用户提供的产品名称和描述，推荐最合适的HS编码。

请严格按照以下JSON格式返回结果（不要包含任何其他文字，只返回JSON）：
{
  "hs_code": "推荐的主要HS编码（6位）",
  "hs_code_full": "推荐的完整HS编码（可能包含8-10位）",
  "description_cn": "该HS编码对应的中文描述",
  "description_en": "该HS编码对应的英文描述",
  "confidence": 0.0到1.0之间的置信度,
  "alternative_codes": [
    {"code": "备选HS编码", "description": "描述", "reason": "推荐原因"}
  ],
  "notes": "分类说明和注意事项",
  "import_tax_rate": "进口关税税率（如已知）",
  "vat_rate": "增值税税率（如已知）",
  "export_rebate_rate": "出口退税率（如已知）",
  "customs_supervision": "海关监管条件（如已知）",
  "declaration_elements": "申报要素提示",
  "is_dual_use": false,
  "dual_use_risk": "两用物项风险评估"
}

重要规则：
1. HS编码前2位代表章(Chapter)，前4位代表品目(Heading)，前6位代表子目(Subheading)
2. 6位编码是国际通用的(WCO标准)，7-10位是各国自定义的
3. 如果产品可能涉及两用物项管控，请将is_dual_use设为true并详细说明
4. 置信度低于0.7时，请在notes中明确提示用户需要进一步确认
5. 如果产品信息不够明确，请列出可能的分类并说明判断依据"""

    user_prompt = f"请对以下产品进行HS编码分类：\n\n产品名称：{product_name}"
    if product_desc:
        user_prompt += f"\n产品描述：{product_desc}"
    if extra_info:
        user_prompt += f"\n补充信息：{extra_info}"
    user_prompt += "\n\n请返回JSON格式的分类结果。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    result = call_openrouter(messages, max_tokens=1500, temperature=0.2)

    if result["success"]:
        try:
            # 尝试解析JSON
            content = result["content"].strip()
            # 去除可能的markdown代码块标记
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            if content.startswith("json"):
                content = content[4:]

            classification = json.loads(content.strip())
            classification["model_used"] = result["model_id"]
            classification["raw_response"] = result["content"]
            return {
                "success": True,
                "classification": classification,
                "model": result["model_id"],
                "usage": result.get("usage", {})
            }
        except json.JSONDecodeError as e:
            return {
                "success": True,
                "classification": {
                    "hs_code": "",
                    "description_cn": result["content"],
                    "confidence": 0.3,
                    "notes": f"AI返回了非结构化结果，原始回复如上。JSON解析错误: {str(e)}",
                    "is_dual_use": False,
                    "dual_use_risk": "无法自动评估"
                },
                "model": result["model_id"],
                "usage": result.get("usage", {})
            }
    else:
        return {
            "success": False,
            "error": result.get("error", "未知错误"),
            "model": result.get("model_id", "unknown")
        }


def check_dual_use(product_name, hs_code=""):
    """
    检查产品是否可能涉及两用物项管控
    """
    system_prompt = """你是一个出口管制和两用物项管控专家。根据《中华人民共和国两用物项出口管制清单》（2024年版），判断以下产品是否可能涉及两用物项管控。

请严格按照以下JSON格式返回结果（不要包含任何其他文字，只返回JSON）：
{
  "is_dual_use": true/false,
  "risk_level": "高/中/低/无",
  "matched_categories": ["匹配的管控类别"],
  "matched_items": ["匹配的具体管控项目编号"],
  "control_measures": ["需要采取的管控措施"],
  "license_required": true/false,
  "license_type": "需要的许可证类型（如适用）",
  "notes": "详细说明和建议"
}

重要规则：
1. 两用物项清单涵盖10大领域：专用材料、材料加工、电子、计算机、电信和信息安全、传感器和激光器、导航和航空电子、船舶、航空航天与推进、其他物项
2. 如果产品涉及化学品前体、特种材料、高性能电子设备、航空航天部件等，需要特别关注
3. 即使HS编码不在清单中，也要考虑产品的最终用途是否可能涉及两用物项"""

    user_prompt = f"请判断以下产品是否涉及两用物项管控：\n\n产品名称：{product_name}"
    if hs_code:
        user_prompt += f"\nHS编码：{hs_code}"
    user_prompt += "\n\n请返回JSON格式的评估结果。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    result = call_openrouter(messages, max_tokens=1000, temperature=0.1)

    if result["success"]:
        try:
            content = result["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            if content.startswith("json"):
                content = content[4:]

            assessment = json.loads(content.strip())
            return {
                "success": True,
                "assessment": assessment,
                "model": result["model_id"]
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "assessment": {
                    "is_dual_use": False,
                    "risk_level": "无法确定",
                    "matched_categories": [],
                    "matched_items": [],
                    "control_measures": [],
                    "license_required": False,
                    "notes": f"AI返回了非结构化结果: {result['content'][:200]}"
                },
                "model": result["model_id"]
            }
    else:
        return {
            "success": False,
            "error": result.get("error", "未知错误"),
            "assessment": {
                "is_dual_use": False,
                "risk_level": "无法确定",
                "notes": f"两用物项检查失败: {result.get('error', '未知错误')}"
            }
        }


def learn_from_feedback(product_name, hs_code, feedback, user_id=None):
    """
    从用户反馈中学习，更新知识库
    """
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 检查是否已存在相同的产品-HS编码对
        cursor.execute('''
            SELECT id, confidence, usage_count, success_count
            FROM ai_knowledge
            WHERE product_name = ? AND hs_code = ?
        ''', (product_name, hs_code))

        existing = cursor.fetchone()

        if existing:
            # 更新现有记录
            new_usage = existing["usage_count"] + 1
            new_success = existing["success_count"] + (1 if feedback == "correct" else 0)
            new_confidence = min(0.99, existing["confidence"] + 0.05 * (1 if feedback == "correct" else -0.5))

            cursor.execute('''
                UPDATE ai_knowledge
                SET usage_count = ?,
                    success_count = ?,
                    confidence = ?,
                    feedback = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_usage, new_success, new_confidence, feedback, existing["id"]))
        else:
            # 新增记录
            confidence = 0.8 if feedback == "correct" else 0.5
            cursor.execute('''
                INSERT INTO ai_knowledge
                (product_name, hs_code, confidence, source, verified, usage_count, success_count, feedback)
                VALUES (?, ?, ?, 'user_feedback', ?, 1, ?, ?)
            ''', (product_name, hs_code, confidence, 1 if feedback == "correct" else 0, feedback))

        return True


def get_knowledge_suggestion(product_name):
    """
    从知识库中获取已有的分类建议
    """
    with get_db_context() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT hs_code, confidence, usage_count, success_count, source, verified
            FROM ai_knowledge
            WHERE product_name LIKE ? OR product_name = ?
            ORDER BY confidence DESC, usage_count DESC
            LIMIT 5
        ''', (f"%{product_name}%", product_name))

        results = cursor.fetchall()

        if results:
            return [
                {
                    "hs_code": r["hs_code"],
                    "confidence": r["confidence"],
                    "usage_count": r["usage_count"],
                    "success_count": r["success_count"],
                    "source": r["source"],
                    "verified": bool(r["verified"])
                }
                for r in results
            ]
        return None


def get_model_status():
    """获取模型状态信息"""
    return {
        "current_model": get_current_model(),
        "available_models": AVAILABLE_MODELS,
        "total_models": len(AVAILABLE_MODELS),
        "api_key_configured": bool(OPENROUTER_API_KEY)
    }


def test_model_connection(model_id=None):
    """测试模型连接"""
    messages = [{"role": "user", "content": "请回复'连接成功'"}]
    result = call_openrouter(messages, model_id=model_id, max_tokens=20)
    return result


if __name__ == '__main__':
    # 测试AI分类
    print("🧪 测试AI分类功能...")
    result = classify_hs_code("笔记本电脑", "联想ThinkPad X1 Carbon, 14英寸, Intel i7处理器")
    if result["success"]:
        print("✅ AI分类成功!")
        print(json.dumps(result["classification"], ensure_ascii=False, indent=2))
    else:
        print(f"❌ AI分类失败: {result['error']}")
