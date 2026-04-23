"""
外部海关HS编码API集成服务
整合多个官方/权威数据源，提供准确的HS编码查询
"""

import requests
import time
import pyhscodes

# ===== 1. HS DataHub API (WCO标准) =====
HS_DATAHUB_BASE = "https://hs.datahub.io/api/v1"

def query_hs_datahub(code=None, keyword=None):
    """查询HS DataHub API（WCO HS编码数据库）"""
    results = []
    try:
        if code:
            # 精确查询
            resp = requests.get(f"{HS_DATAHUB_BASE}/products/{code}", timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data:
                    results.append({
                        "code": data.get("hscode", code),
                        "description_en": data.get("description", ""),
                        "section": data.get("section", ""),
                        "parent": data.get("parent", ""),
                        "level": data.get("level", len(str(code))),
                        "source": "WCO HS DataHub",
                        "source_url": "https://hs.datahub.io",
                        "source_type": "api"
                    })
        elif keyword:
            # 搜索
            resp = requests.get(f"{HS_DATAHUB_BASE}/products/search", params={"q": keyword}, timeout=10)
            if resp.status_code == 200:
                data_list = resp.json().get("data", [])
                for item in data_list[:10]:
                    results.append({
                        "code": item.get("hscode", ""),
                        "description_en": item.get("description", ""),
                        "section": item.get("section", ""),
                        "parent": item.get("parent", ""),
                        "level": item.get("level", 0),
                        "source": "WCO HS DataHub",
                        "source_url": "https://hs.datahub.io",
                        "source_type": "api"
                    })
    except Exception as e:
        print(f"HS DataHub查询失败: {e}")
    return results


# ===== 0. 中国海关总署 (hsbianma.com - 数据来源于海关总署官方发布) =====
CHINA_CUSTOMS_BASE = 'https://www.hsbianma.com'

def query_china_customs(code=None, keyword=None):
    """查询中国海关HS编码（数据来源于海关总署官方发布）"""
    results = []
    try:
        if code:
            # 精确查询10位编码详情
            code_clean = str(code).replace(".", "")[:10]
            url = f'{CHINA_CUSTOMS_BASE}/Code/{code_clean}.html'
            resp = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'lxml')
                wrap = soup.find(id='wrap')
                if wrap and len(wrap.contents) > 3:
                    tables = wrap.contents[3].find_all('table')
                    if len(tables) >= 2:
                        # 基本信息
                        tds0 = tables[0].find_all('td')
                        info = {}
                        for i in range(0, len(tds0)-1, 2):
                            info[tds0[i].text.strip()] = tds0[i+1].text.strip()
                        # 税率信息
                        tds1 = tables[1].find_all('td')
                        tax = {}
                        for i in range(0, len(tds1)-1, 2):
                            tax[tds1[i].text.strip()] = tds1[i+1].text.strip()

                        result = {
                            "code": info.get('商品编码', code_clean),
                            "description_cn": info.get('商品名称', ''),
                            "source": "中国海关总署",
                            "source_url": "https://www.customs.gov.cn/customs/302249/index.html",
                            "source_type": "official",
                            "tax_rate_import": tax.get('最惠国税率', '').replace('%', ''),
                            "tax_rate_export": tax.get('出口税率', '').replace('%', ''),
                            "vat_rate": tax.get('增值税率', '').replace('%', ''),
                            "export_rebate_rate": tax.get('出口退税税率', '').replace('%', ''),
                            "consumption_tax": tax.get('消费税率', '').replace('%', ''),
                            "unit": tax.get('计量单位', ''),
                            "status": info.get('编码状态', ''),
                            "update_time": info.get('更新时间', ''),
                        }
                        # 监管条件
                        if len(tables) >= 4:
                            tds3 = tables[3].find_all('td')
                            sups = []
                            for i in range(0, len(tds3)-1, 2):
                                c, d = tds3[i].text.strip(), tds3[i+1].text.strip()
                                if c and c != '无':
                                    sups.append(f"{c}:{d}")
                            result["supervision_conditions"] = sups
                        results.append(result)
        elif keyword:
            # 按关键词搜索
            url = f'{CHINA_CUSTOMS_BASE}/Search/1?keywords={keyword}'
            resp = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'lxml')
                trs = soup.find_all('tr', class_='result-grid')
                for tr in trs[:15]:
                    tds = tr.find_all('td')
                    if len(tds) >= 2:
                        code_text = tds[0].text.strip()
                        hs_code = code_text.replace('[过期]', '').replace('.', '').replace(' ', '')
                        name = tds[1].text.strip().split('\n')[0].strip()
                        outdated = '[过期]' in code_text
                        results.append({
                            "code": hs_code,
                            "description_cn": name,
                            "source": "中国海关总署",
                            "source_url": "https://www.customs.gov.cn/customs/302249/index.html",
                            "source_type": "official",
                            "outdated": outdated
                        })
    except Exception as e:
        print(f"中国海关查询失败: {e}")
    return results


# ===== 2. pyhscodes (本地WCO HS编码库) =====
def query_pyhscodes(code=None, keyword=None):
    """使用pyhscodes本地库查询（WCO 6位标准编码）"""
    results = []
    try:
        if code:
            code_clean = str(code).replace(".", "")[:6]
            item = pyhscodes.hscodes.get(hscode=code_clean)
            if item:
                results.append({
                    "code": item.hscode,
                    "description_en": item.description,
                    "level": item.level,
                    "source": "WCO (pyhscodes)",
                    "source_url": "https://www.wcoomd.org",
                    "source_type": "local_db"
                })
                # 获取子编码
                children = pyhscodes.hscodes.get_children(code_clean)
                for child in children[:10]:
                    results.append({
                        "code": child.hscode,
                        "description_en": child.description,
                        "level": child.level,
                        "source": "WCO (pyhscodes)",
                        "source_url": "https://www.wcoomd.org",
                        "source_type": "local_db"
                    })
        elif keyword:
            items = pyhscodes.hscodes.search_fuzzy(keyword)
            for item in (items or [])[:10]:
                results.append({
                    "code": item.hscode,
                    "description_en": item.description,
                    "level": item.level,
                    "source": "WCO (pyhscodes)",
                    "source_url": "https://www.wcoomd.org",
                    "source_type": "local_db"
                })
    except Exception as e:
        print(f"pyhscodes查询失败: {e}")
    return results


# ===== 3. 法国海关开放数据 =====
FR_DATA_BASE = "https://data.economie.gouv.fr/api/records/1.0/search/"

def query_france_customs(code=None, keyword=None):
    """查询法国海关开放数据（基于TARIC）"""
    results = []
    try:
        params = {
            "dataset": "statistiques-nationales-du-commerce-exterieur",
            "rows": 5
        }
        if code:
            params["q"] = str(code).replace(".", "")[:8]
        elif keyword:
            params["q"] = keyword

        resp = requests.get(FR_DATA_BASE, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for record in data.get("records", []):
                fields = record.get("fields", {})
                # 尝试多种字段名
                nc8_code = fields.get("cod_nc8") or fields.get("column_1") or ""
                nc8_desc = fields.get("libelle_nc8") or fields.get("column_2") or ""
                if nc8_code or nc8_desc:
                    results.append({
                        "code": str(nc8_code),
                        "description_cn": nc8_desc,
                        "source": "法国海关 (DGDDI)",
                        "source_url": "https://www.douane.gouv.fr/fr/outils-et-services/recherche-de-codes-tarifaires",
                        "source_type": "api"
                    })
    except Exception as e:
        print(f"法国海关查询失败: {e}")
    return results


# ===== 4. UK Trade Tariff API (欧盟TARIC数据) =====
UK_TARIFF_BASE = "https://api.trade-tariff.service.gov.uk/api/v2"

def query_uk_tariff(code=None):
    """查询UK Trade Tariff API（基于EU TARIC数据结构）"""
    results = []
    try:
        if not code:
            return results
        code_clean = str(code).replace(".", "")

        # 尝试commodities查询
        resp = requests.get(
            f"{UK_TARIFF_BASE}/commodities/{code_clean}",
            headers={"Accept": "application/json"},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            if data:
                measures = data.get("import_measures", [])
                duty_info = []
                for m in measures[:5]:
                    mtype = m.get("measure_type", {}).get("description", "")
                    duty = m.get("duty_expression", {}).get("duty_amount", "")
                    if duty:
                        duty_info.append(f"{mtype}: {duty}")

                results.append({
                    "code": data.get("goods_nomenclature_item_id", code_clean),
                    "description_en": data.get("description", ""),
                    "source": "UK Trade Tariff (EU TARIC)",
                    "source_url": "https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp",
                    "source_type": "api",
                    "duties": duty_info,
                    "measures_count": len(measures)
                })
    except Exception as e:
        print(f"UK Tariff查询失败(可能网络不通): {e}")
    return results


# ===== 综合查询函数 =====
def query_external_sources(code=None, keyword=None):
    """
    综合查询所有外部数据源
    返回: {"success": True, "results": [...], "total": N, "sources_used": [...]}
    """
    all_results = []
    source_names = set()

    # 如果是中文关键词，尝试用AI翻译成英文用于外部搜索
    en_keyword = keyword
    if keyword and any('\u4e00' <= c <= '\u9fff' for c in keyword):
        # 简单的常见中文-英文关键词映射
        cn_en_map = {
            '钢琴': 'piano', '电池': 'battery', '锂电池': 'lithium battery',
            '集成电路': 'integrated circuit', '半导体': 'semiconductor',
            '棉布': 'cotton fabric', '钢铁': 'steel', '塑料': 'plastic',
            '汽车': 'automobile car', '手机': 'mobile phone', '电脑': 'computer',
            '服装': 'clothing garment', '鞋': 'shoes footwear', '玩具': 'toy',
            '家具': 'furniture', '陶瓷': 'ceramic porcelain', '茶叶': 'tea',
            '橡胶': 'rubber', '玻璃': 'glass', '纸张': 'paper',
            '电机': 'electric motor', '发动机': 'engine', '轴承': 'bearing',
            '阀门': 'valve', '泵': 'pump', '压缩机': 'compressor',
            '电缆': 'cable wire', '变压器': 'transformer', '太阳能': 'solar',
            'LED': 'LED', '芯片': 'chip microchip', '光纤': 'optical fiber',
            '摄像头': 'camera', '显示器': 'display monitor', '打印机': 'printer',
            '冰箱': 'refrigerator', '空调': 'air conditioner', '洗衣机': 'washing machine',
            '微波炉': 'microwave oven', '电视机': 'television TV', '音响': 'audio speaker',
            '医疗器械': 'medical device instrument', '药品': 'pharmaceutical medicine drug',
            '化妆品': 'cosmetic', '食品': 'food', '饮料': 'beverage drink',
            '酒': 'wine alcohol beverage', '烟草': 'tobacco', '纺织品': 'textile fabric',
            '机械设备': 'machinery mechanical equipment', '电子产品': 'electronic product',
            '化工产品': 'chemical product', '矿产品': 'mineral product',
            '农产品': 'agricultural product', '水产品': 'aquatic product seafood',
            '木材': 'wood timber', '石材': 'stone marble', '皮革': 'leather',
            '铝': 'aluminum', '铜': 'copper', '不锈钢': 'stainless steel',
            '流水线': 'production line assembly line', '机器人': 'robot robotics',
            '无人机': 'drone UAV', '电动车': 'electric vehicle EV',
        }
        en_keyword = cn_en_map.get(keyword, keyword)
        # 如果没有精确匹配，尝试部分匹配
        if en_keyword == keyword:
            for cn, en in cn_en_map.items():
                if cn in keyword:
                    en_keyword = en
                    break

    # 0. 中国海关总署（优先，数据最权威）
    results = query_china_customs(code=code, keyword=keyword)
    for r in results:
        r["source_order"] = 0
        all_results.append(r)
        source_names.add(r["source"])

    # 1. pyhscodes (本地，最快)
    results = query_pyhscodes(code=code, keyword=en_keyword)
    for r in results:
        r["source_order"] = 1
        all_results.append(r)
        source_names.add(r["source"])

    # 2. HS DataHub (在线API)
    results = query_hs_datahub(code=code, keyword=en_keyword)
    for r in results:
        if not any(existing["code"] == r["code"] and existing["source"] == r["source"] for existing in all_results):
            r["source_order"] = 2
            all_results.append(r)
            source_names.add(r["source"])

    # 3. UK Tariff (在线API，可能超时)
    if code:
        results = query_uk_tariff(code=code)
        for r in results:
            if not any(existing["code"] == r["code"] and existing["source"] == r["source"] for existing in all_results):
                r["source_order"] = 3
                all_results.append(r)
                source_names.add(r["source"])

    # 4. 法国海关 (在线API)
    results = query_france_customs(code=code, keyword=en_keyword)
    for r in results:
        if not any(existing["code"] == r["code"] and existing["source"] == r["source"] for existing in all_results):
            r["source_order"] = 4
            all_results.append(r)
            source_names.add(r["source"])

    return {
        "success": True,
        "results": all_results,
        "total": len(all_results),
        "sources_used": list(source_names)
    }
