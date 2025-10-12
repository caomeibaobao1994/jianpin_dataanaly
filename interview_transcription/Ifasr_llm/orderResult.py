import json
import re

def parse_order_result(api_response, with_speaker=True, debug=False):
    """
    解析完整的API响应，提取orderResult中的所有w字段内容
    
    参数:
        api_response: 完整的API响应字典
        with_speaker: 是否解析说话人信息（默认True）
        debug: 是否打印调试信息（默认False）
    返回:
        如果with_speaker=True，返回带说话人和分段的文本
        如果with_speaker=False，返回简单拼接的文本
    """
    try:
        # 从API响应中获取orderResult字段
        order_result_str = api_response.get('content', {}).get('orderResult', '{}')
        
        # 处理转义字符问题
        cleaned_str = re.sub(r'\\\\', r'\\', order_result_str)
        
        # 解析orderResult字符串为JSON对象
        order_result = json.loads(cleaned_str)
        
        if with_speaker:
            return _parse_with_speaker_separation(order_result, debug)
        else:
            return _parse_simple(order_result)
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return ""
    except Exception as e:
        print(f"处理过程中出错: {e}")
        return ""


def _parse_simple(order_result):
    """简单解析：只拼接文本，不区分说话人"""
    w_values = []
    
    if 'lattice' in order_result:
        for lattice_item in order_result['lattice']:
            if 'json_1best' in lattice_item:
                json_1best = json.loads(lattice_item['json_1best'])
                
                if 'st' in json_1best and 'rt' in json_1best['st']:
                    for rt_item in json_1best['st']['rt']:
                        if 'ws' in rt_item:
                            for ws_item in rt_item['ws']:
                                if 'cw' in ws_item:
                                    for cw_item in ws_item['cw']:
                                        if 'w' in cw_item:
                                            w_values.append(cw_item['w'])
    
    return ''.join(w_values)


def _parse_with_speaker_separation(order_result, debug=False):
    """
    解析带说话人分离的结果，使用rl字段（角色分离编号）
    
    返回格式化的文本，包含：
    - 说话人标识（基于音色的说话人ID）
    - 段落分隔
    """
    # 优先使用lattice2（包含说话人信息），如果不存在则回退到lattice
    lattice_data = order_result.get('lattice2', order_result.get('lattice', []))
    
    if not lattice_data:
        if debug:
            print("警告：未找到lattice2或lattice数据")
        return _parse_simple(order_result)
    
    # 检查是否有lattice2（说话人分离结果）
    has_lattice2 = 'lattice2' in order_result
    if debug:
        print(f"{'✓' if has_lattice2 else '✗'} 检测到lattice2数据（说话人分离）")
    
    # 收集每个句段的信息
    segments = []
    speaker_ids = set()  # 收集所有唯一的说话人ID
    
    for item in lattice_data:
        try:
            # 解析json_1best
            if 'json_1best' in item:
                if isinstance(item['json_1best'], str):
                    json_1best = json.loads(item['json_1best'])
                else:
                    json_1best = item['json_1best']
                
                st_data = json_1best.get('st', {})
                
                # 重要：使用rl字段作为说话人ID（角色分离编号）
                # rl字段才是真正的说话人标识，pa只是段落编号
                speaker_id = st_data.get('rl', '0')  # 从json_1best.st.rl字段获取
                speaker_ids.add(speaker_id)
                
                if debug and len(segments) < 5:  # 只显示前几条，避免刷屏
                    pa_id = st_data.get('pa', 'N/A')
                    print(f"  段落 {len(segments)+1}: pa={pa_id}, rl={speaker_id}")
                
                bg = int(item.get('begin', 0))  # 开始时间（毫秒）
                ed = int(item.get('end', 0))    # 结束时间（毫秒）
                
                # 提取该段落的文本
                text_parts = []
                if 'rt' in st_data:
                    for rt_item in st_data['rt']:
                        if 'ws' in rt_item:
                            for ws_item in rt_item['ws']:
                                if 'cw' in ws_item:
                                    for cw_item in ws_item['cw']:
                                        if 'w' in cw_item:
                                            text_parts.append(cw_item['w'])
                
                text = ''.join(text_parts).strip()
                
                if text:
                    segments.append({
                        'speaker_id': speaker_id,  # 真正的说话人ID
                        'text': text,
                        'begin': bg,
                        'end': ed
                    })
        
        except (json.JSONDecodeError, KeyError) as e:
            if debug:
                print(f"解析段落时出错: {e}")
            continue
    
    if debug:
        print(f"\n说话人统计：")
        print(f"- 检测到 {len(speaker_ids)} 个不同的说话人ID: {sorted(speaker_ids)}")
        print(f"- 共 {len(segments)} 个语音段落")
    
    # 按时间排序
    segments.sort(key=lambda x: x['begin'])
    
    # 为说话人ID分配标签
    # rl通常是数字字符串，如"0", "1", "2"...
    speaker_id_to_label = {}
    speaker_names = ['访谈者', '受访者', '角色C', '角色D', '角色E', '角色F']
    
    # 按说话人ID排序，确保一致性
    sorted_speaker_ids = sorted(speaker_ids, key=lambda x: int(x) if x.isdigit() else x)
    
    for i, sid in enumerate(sorted_speaker_ids):
        if i < len(speaker_names):
            speaker_id_to_label[sid] = speaker_names[i]
        else:
            speaker_id_to_label[sid] = f"角色{chr(65+i)}"  # A, B, C, D...
    
    if debug:
        print(f"\n说话人映射：")
        for sid, label in speaker_id_to_label.items():
            seg_count = sum(1 for seg in segments if seg['speaker_id'] == sid)
            print(f"  rl={sid} → {label} (共{seg_count}段)")
    
    # 格式化输出（保持原始分段，由text_cleaner负责合并）
    result_lines = []
    current_speaker = None
    
    for seg in segments:
        speaker_id = seg['speaker_id']
        speaker_label = speaker_id_to_label.get(speaker_id, f"未知角色({speaker_id})")
        
        # 当说话人切换时，添加空行分隔
        if current_speaker is not None and current_speaker != speaker_id:
            result_lines.append("")
        
        # 格式化输出：【说话人】文本
        result_lines.append(f"【{speaker_label}】{seg['text']}")
        current_speaker = speaker_id
    
    return '\n'.join(result_lines)

def main():
    # 示例API成功响应（截取部分示例数据）
    sample_api_response = {
        "content": {
            "orderResult": "{\"lattice\":[{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"为\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.7511\\\"}],\\\"wb\\\":22,\\\"we\\\":75}]}],\\\"bg\\\":\\\"880\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"1680\\\"}}\"},{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"喂\\\",\\\"wp\\\":\\\"s\\\",\\\"wc\\\":\\\"0.9806\\\"}],\\\"wb\\\":19,\\\"we\\\":52},{\\\"cw\\\":[{\\\"w\\\":\\\"你好\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":53,\\\"we\\\":111},{\\\"cw\\\":[{\\\"w\\\":\\\"｡\\\",\\\"wp\\\":\\\"p\\\",\\\"wc\\\":\\\"0.0000\\\"}],\\\"wb\\\":111,\\\"we\\\":111}]}],\\\"bg\\\":\\\"2390\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"3640\\\"}}\"},{\"json_1best\":\"{\\\"st\\\":{\\\"pa\\\":\\\"0\\\",\\\"rt\\\":[{\\\"ws\\\":[{\\\"cw\\\":[{\\\"w\\\":\\\"舒\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.8630\\\"}],\\\"wb\\\":20,\\\"we\\\":44},{\\\"cw\\\":[{\\\"w\\\":\\\"高\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":45,\\\"we\\\":65},{\\\"cw\\\":[{\\\"w\\\":\\\"生\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.2461\\\"}],\\\"wb\\\":66,\\\"we\\\":79},{\\\"cw\\\":[{\\\"w\\\":\\\"先生\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"0.9709\\\"}],\\\"wb\\\":80,\\\"we\\\":109},{\\\"cw\\\":[{\\\"w\\\":\\\"是\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":110,\\\"we\\\":118},{\\\"cw\\\":[{\\\"w\\\":\\\"吧\\\",\\\"wp\\\":\\\"n\\\",\\\"wc\\\":\\\"1.0000\\\"}],\\\"wb\\\":119,\\\"we\\\":138},{\\\"cw\\\":[{\\\"w\\\":\\\"?\\\",\\\"wp\\\":\\\"p\\\",\\\"wc\\\":\\\"0.0000\\\"}],\\\"wb\\\":138,\\\"we\\\":138}]}],\\\"bg\\\":\\\"5130\\\",\\\"rl\\\":\\\"1\\\",\\\"ed\\\":\\\"7200\\\"}}\"}]}",
            "orderInfo": {
                "failType": 0,
                "status": 4,
                "orderId": "DKHJQ202003171520031715109E1FF5E50001D",
                "originalDuration": 14000
            }
        },
        "descInfo": "success",
        "code": "000000"
    }
    
    # 解析并获取拼接后的文本
    result_text = parse_order_result(sample_api_response)
    
    # 展示结果
    print("解析并拼接后的w字段内容：")
    print("----------------------------------------")
    print(result_text)
    print("----------------------------------------")

if __name__ == "__main__":
    main()
    