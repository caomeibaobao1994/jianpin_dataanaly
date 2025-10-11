"""
讯飞语音转写API封装
使用讯飞开放平台的语音转写服务（REST API）
官方文档: https://www.xfyun.cn/doc/asr/lfasr/API.html
"""

import hashlib
import hmac
import base64
import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional, List
from config import Config


class IFlytekTranscriber:
    """讯飞语音转写API客户端"""
    
    # API端点
    API_UPLOAD = "https://raasr.xfyun.cn/v2/api/upload"
    API_PREPARE = "https://raasr.xfyun.cn/v2/api/prepare"
    API_QUERY = "https://raasr.xfyun.cn/v2/api/getResult"
    
    def __init__(self, app_id: str = None, secret_key: str = None):
        """
        初始化讯飞转写客户端
        
        Args:
            app_id: 讯飞APPID
            secret_key: 讯飞Secret Key
        """
        self.app_id = app_id or Config.IFLYTEK_APPID
        self.secret_key = secret_key or Config.IFLYTEK_SECRET_KEY
        
        if not self.app_id or not self.secret_key:
            raise ValueError("请设置讯飞API密钥")
    
    def _generate_signature(self, ts: str) -> str:
        """
        生成签名
        
        Args:
            ts: 时间戳字符串
            
        Returns:
            签名字符串
        """
        auth_str = f"{self.app_id}{ts}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            auth_str.encode('utf-8'),
            hashlib.sha1
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_headers(self) -> Dict[str, str]:
        """
        生成请求头
        
        Returns:
            请求头字典
        """
        ts = str(int(time.time()))
        signature = self._generate_signature(ts)
        
        return {
            'appId': self.app_id,
            'ts': ts,
            'signa': signature,
            'Content-Type': 'application/json'
        }
    
    def upload_audio(self, audio_path: Path) -> Optional[str]:
        """
        上传音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            上传成功返回upload_id，失败返回None
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        
        # 检查文件大小
        file_size = audio_path.stat().st_size
        if file_size > Config.MAX_FILE_SIZE:
            raise ValueError(f"文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持500MB")
        
        # 分片上传
        slice_size = 10 * 1024 * 1024  # 每片10MB
        total_slices = (file_size + slice_size - 1) // slice_size
        
        print(f"📤 开始上传音频: {audio_path.name}")
        print(f"   文件大小: {file_size / 1024 / 1024:.2f}MB，共{total_slices}片")
        
        with open(audio_path, 'rb') as f:
            for slice_id in range(total_slices):
                # 读取分片数据
                content = f.read(slice_size)
                
                # 构建请求参数
                headers = self._get_headers()
                body = {
                    'fileName': audio_path.name,
                    'fileSize': file_size,
                    'sliceNum': total_slices,
                    'sliceId': slice_id + 1,
                    'content': base64.b64encode(content).decode('utf-8')
                }
                
                # 发送请求
                try:
                    response = requests.post(
                        self.API_UPLOAD,
                        headers=headers,
                        json=body,
                        timeout=60
                    )
                    result = response.json()
                    
                    if result.get('code') != '000000':
                        print(f"❌ 上传失败: {result.get('descInfo')}")
                        return None
                    
                    print(f"   ✓ 已上传 {slice_id + 1}/{total_slices}")
                    
                except Exception as e:
                    print(f"❌ 上传异常: {str(e)}")
                    return None
        
        # 返回最后一个响应中的uploadId
        upload_id = result.get('data')
        print(f"✅ 上传完成，uploadId: {upload_id}")
        return upload_id
    
    def prepare_task(self, upload_id: str) -> Optional[str]:
        """
        提交转写任务
        
        Args:
            upload_id: 上传文件的ID
            
        Returns:
            任务ID，失败返回None
        """
        headers = self._get_headers()
        
        # 构建转写参数
        body = {
            'uploadId': upload_id,
            'language': Config.LANGUAGE,
            'hasParticiple': 'true' if Config.HAS_PARTICIPLE else 'false',
        }
        
        # 说话人分离参数
        if Config.ENABLE_SPEAKER_SEPARATION:
            body['hasSpeaker'] = 'true'
            body['speakerNumber'] = str(Config.SPEAKER_NUMBER)
        
        try:
            response = requests.post(
                self.API_PREPARE,
                headers=headers,
                json=body,
                timeout=30
            )
            result = response.json()
            
            if result.get('code') != '000000':
                print(f"❌ 任务提交失败: {result.get('descInfo')}")
                return None
            
            task_id = result.get('data')
            print(f"✅ 任务已提交，taskId: {task_id}")
            return task_id
            
        except Exception as e:
            print(f"❌ 提交异常: {str(e)}")
            return None
    
    def query_result(self, task_id: str, wait: bool = True) -> Optional[Dict]:
        """
        查询转写结果
        
        Args:
            task_id: 任务ID
            wait: 是否等待任务完成
            
        Returns:
            转写结果字典，失败返回None
        """
        headers = self._get_headers()
        body = {'taskId': task_id}
        
        start_time = time.time()
        
        while True:
            try:
                response = requests.post(
                    self.API_QUERY,
                    headers=headers,
                    json=body,
                    timeout=30
                )
                result = response.json()
                
                if result.get('code') != '000000':
                    print(f"❌ 查询失败: {result.get('descInfo')}")
                    return None
                
                # 获取任务状态
                data = result.get('data', {})
                status = data.get('status')
                
                if status == 9:  # 转写完成
                    print(f"✅ 转写完成")
                    return data
                
                elif status in [0, 1, 2, 3]:  # 处理中
                    status_map = {
                        0: '任务创建中',
                        1: '音频上传完成',
                        2: '预处理中',
                        3: '转写中'
                    }
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ {status_map.get(status, '处理中')}... (已等待{elapsed}秒)")
                    
                    if not wait:
                        return None
                    
                    # 检查是否超时
                    if elapsed > Config.MAX_POLL_TIME:
                        print(f"❌ 等待超时（超过{Config.MAX_POLL_TIME}秒）")
                        return None
                    
                    time.sleep(Config.POLL_INTERVAL)
                    
                else:  # 失败
                    print(f"❌ 转写失败，状态码: {status}")
                    return None
                    
            except Exception as e:
                print(f"❌ 查询异常: {str(e)}")
                return None
    
    def parse_result(self, result_data: Dict) -> List[Dict]:
        """
        解析转写结果
        
        Args:
            result_data: API返回的结果数据
            
        Returns:
            解析后的对话列表，每项包含 speaker 和 text
        """
        result_url = result_data.get('resultUrl')
        if not result_url:
            print("❌ 未找到结果URL")
            return []
        
        try:
            # 下载结果
            response = requests.get(result_url, timeout=60)
            result_json = response.json()
            
            # 解析对话片段
            dialogues = []
            
            # 讯飞返回的格式：lattice 数组
            lattice = result_json.get('lattice', [])
            
            for item in lattice:
                json_1best = item.get('json_1best', '{}')
                segment = json.loads(json_1best)
                
                # 提取说话人和文本
                speaker = segment.get('st', {}).get('speaker', '0')
                
                # 提取文本内容
                words = segment.get('st', {}).get('rt', [{}])[0].get('ws', [])
                text = ''.join([
                    w.get('cw', [{}])[0].get('w', '')
                    for w in words
                ])
                
                if text.strip():
                    dialogues.append({
                        'speaker': f"Speaker {int(speaker) + 1}",
                        'text': text.strip()
                    })
            
            print(f"✅ 解析完成，共{len(dialogues)}段对话")
            return dialogues
            
        except Exception as e:
            print(f"❌ 解析异常: {str(e)}")
            return []
    
    def transcribe(self, audio_path: Path) -> Optional[List[Dict]]:
        """
        完整的转写流程（一站式方法）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            对话列表
        """
        # 1. 上传音频
        upload_id = self.upload_audio(audio_path)
        if not upload_id:
            return None
        
        # 2. 提交任务
        task_id = self.prepare_task(upload_id)
        if not task_id:
            return None
        
        # 3. 等待并获取结果
        result_data = self.query_result(task_id, wait=True)
        if not result_data:
            return None
        
        # 4. 解析结果
        dialogues = self.parse_result(result_data)
        return dialogues

