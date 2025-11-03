#!/usr/bin/env python3
"""
SPO三元组提取器
基于LLM的Subject-Predicate-Object三元组提取
整合自Fareed Khan的知识图谱构建方法
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    import openai
except ImportError:
    print("⚠️ 警告: openai库未安装，请运行: pip install openai")
    openai = None


class SPOTripleExtractor:
    """SPO三元组提取器"""
    
    def __init__(
        self,
        model_name: str = "deepseek/deepseek-chat-v3-0324",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        use_openrouter: bool = True
    ):
        """
        初始化SPO三元组提取器
        
        Args:
            model_name: LLM模型名称
            api_key: API密钥（如果为None，将从环境变量读取）
            base_url: API基础URL（如果为None，将使用默认值）
            temperature: 生成温度（0.0用于确定性提取）
            max_tokens: 最大token数
            use_openrouter: 是否使用OpenRouter（否则使用OpenAI）
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 配置API
        if use_openrouter:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            self.base_url = base_url or "https://openrouter.ai/api/v1"
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = base_url or None
        
        # 初始化OpenAI客户端
        if not self.api_key:
            raise ValueError(
                "API key未设置。请设置环境变量 OPENROUTER_API_KEY 或 OPENAI_API_KEY，"
                "或者在初始化时传入api_key参数。"
            )
        
        try:
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        except Exception as e:
            raise Exception(f"OpenAI客户端初始化失败: {e}")
        
        # 系统提示词
        self.extraction_system_prompt = """
你是一个专门的知识图谱提取专家。
你的任务是从给定文本中识别并提取事实性的Subject-Predicate-Object (SPO) 三元组。
专注于准确性，并严格遵循用户提示中要求的JSON输出格式。
提取核心实体和最直接的关系。
"""
        
        # 用户提示词模板
        self.extraction_user_prompt_template = """
请从以下文本中提取Subject-Predicate-Object (S-P-O) 三元组。

**非常重要的规则：**
1. **输出格式：** 仅响应一个有效的JSON数组。每个元素必须是一个包含"subject"、"predicate"、"object"键的对象。
2. **仅JSON：** 不要在JSON数组前后包含任何文本（例如，不要写"这是JSON："或解释）。不要使用markdown ```json ... ```标签。
3. **简洁谓词：** 保持'predicate'值简洁（1-3个词，理想情况下1-2个词）。使用动词或短动词短语（例如，'discovered'、'was born in'、'won'）。
4. **小写：** 'subject'、'predicate'和'object'的所有值必须为小写。
5. **代词解析：** 将代词（she、he、it、her等）替换为它们基于文本上下文所指的特定小写实体名称（例如，'marie curie'）。
6. **具体性：** 捕获具体细节（例如，如果指定了，使用'nobel prize in physics'而不是仅仅'nobel prize'）。
7. **完整性：** 提取所有提到的不同事实关系。

**要处理的文本：**
```text
{text_chunk}
```

**必需的JSON输出格式示例：**
[
{{ "subject": "marie curie", "predicate": "discovered", "object": "radium" }},
{{ "subject": "marie curie", "predicate": "won", "object": "nobel prize in physics" }}
]

**你的JSON输出（必须以'['开头，以']'结尾）：**
"""
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 150,
        overlap: int = 30
    ) -> List[Dict[str, Any]]:
        """
        将文本分块
        
        Args:
            text: 要分块的文本
            chunk_size: 每块的词数
            overlap: 重叠词数（必须小于chunk_size）
            
        Returns:
            分块列表，每个块包含text和chunk_number
        """
        if overlap >= chunk_size and chunk_size > 0:
            raise ValueError(f"重叠({overlap})必须小于块大小({chunk_size})")
        
        words = text.split()
        total_words = len(words)
        chunks = []
        start_index = 0
        chunk_number = 1
        
        while start_index < total_words:
            end_index = min(start_index + chunk_size, total_words)
            chunk_text = " ".join(words[start_index:end_index])
            chunks.append({
                "text": chunk_text,
                "chunk_number": chunk_number
            })
            
            # 计算下一个块的起始位置
            next_start_index = start_index + chunk_size - overlap
            
            # 确保有进展
            if next_start_index <= start_index:
                if end_index == total_words:
                    break
                next_start_index = start_index + 1
            
            start_index = next_start_index
            chunk_number += 1
            
            # 安全中断
            if chunk_number > total_words:
                print("⚠️ 警告: 分块循环超过总词数，中断。")
                break
        
        return chunks
    
    def extract_triples_from_chunk(
        self,
        chunk_text: str,
        chunk_number: int = 1,
        verbose: bool = False
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        从单个chunk中提取三元组
        
        Args:
            chunk_text: chunk文本
            chunk_number: chunk编号
            verbose: 是否打印详细信息
            
        Returns:
            (triples_list, error_message) 元组
        """
        # 格式化用户提示
        user_prompt = self.extraction_user_prompt_template.format(text_chunk=chunk_text)
        
        llm_output = None
        error_message = None
        
        try:
            if verbose:
                print(f"📤 发送请求到LLM (chunk {chunk_number})...")
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.extraction_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # API调用参数
            call_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
            }
            
            # 某些模型不支持temperature=0.0，使用条件设置
            try:
                call_params["temperature"] = self.temperature
            except:
                pass  # 如果模型不支持，跳过
            
            # 某些模型可能支持response_format
            try:
                call_params["response_format"] = {"type": "json_object"}
            except:
                pass
            
            response = self.client.chat.completions.create(**call_params)
            
            if verbose:
                print(f"✅ LLM响应已接收 (chunk {chunk_number})")
            
            # 提取原始响应内容
            llm_output = response.choices[0].message.content.strip()
            
            if verbose:
                print(f"--- 原始LLM输出 (Chunk {chunk_number}) ---")
                print(llm_output[:500] + "..." if len(llm_output) > 500 else llm_output)
        
        except Exception as e:
            error_message = f"API调用错误: {str(e)}"
            if verbose:
                print(f"❌ {error_message}")
            return [], error_message
        
        # 解析JSON
        parsed_json = None
        parsing_error = None
        
        if llm_output is not None:
            try:
                # 策略1: 直接解析（理想情况）
                parsed_data = json.loads(llm_output)
                
                # 处理response_format={'type':'json_object'}返回包含列表的字典的情况
                if isinstance(parsed_data, dict):
                    if verbose:
                        print("   🔍 检测到字典响应，尝试提取列表...")
                    list_values = [v for v in parsed_data.values() if isinstance(v, list)]
                    if len(list_values) == 1:
                        parsed_json = list_values[0]
                        if verbose:
                            print("      ✅ 成功从字典中提取列表")
                    elif isinstance(parsed_data, dict) and any(k in parsed_data for k in ['triples', 'results', 'data', 'items']):
                        # 尝试常见的关键字
                        for key in ['triples', 'results', 'data', 'items']:
                            if key in parsed_data and isinstance(parsed_data[key], list):
                                parsed_json = parsed_data[key]
                                if verbose:
                                    print(f"      ✅ 从字典的'{key}'键中提取列表")
                                break
                        else:
                            # 检查是否是单个三元组字典（包含subject, predicate, object）
                            if all(k in parsed_data for k in ['subject', 'predicate', 'object']):
                                # 单个三元组，转换为列表
                                parsed_json = [parsed_data]
                                if verbose:
                                    print("      ✅ 检测到单个三元组字典，转换为列表")
                            else:
                                raise ValueError("JSON对象接收到了，但不包含单个三元组列表。")
                    elif all(k in parsed_data for k in ['subject', 'predicate', 'object']):
                        # 单个三元组，转换为列表
                        parsed_json = [parsed_data]
                        if verbose:
                            print("      ✅ 检测到单个三元组字典，转换为列表")
                    else:
                        raise ValueError("JSON对象接收到了，但不包含单个三元组列表。")
                elif isinstance(parsed_data, list):
                    parsed_json = parsed_data
                    if verbose:
                        print("   ✅ 成功直接解析JSON列表")
                else:
                    raise ValueError("解析的JSON不是列表或预期的字典包装器。")
            
            except json.JSONDecodeError as json_err:
                parsing_error = f"JSONDecodeError: {json_err}。尝试正则表达式回退..."
                if verbose:
                    print(f"   ⚠️ {parsing_error}")
                
                # 策略2: 正则表达式回退（用于可能包装在文本/markdown中的数组）
                match = re.search(r'^\s*(\[.*?\])\s*$', llm_output, re.DOTALL)
                if match:
                    json_string_extracted = match.group(1)
                    if verbose:
                        print("      🔍 正则表达式找到潜在的JSON数组结构")
                    try:
                        parsed_json = json.loads(json_string_extracted)
                        if verbose:
                            print("      ✅ 从正则表达式提取成功解析JSON")
                        parsing_error = None
                    except json.JSONDecodeError as nested_err:
                        parsing_error = f"正则表达式后JSONDecodeError: {nested_err}"
                        if verbose:
                            print(f"      ❌ 错误: 正则表达式内容不是有效的JSON: {nested_err}")
                else:
                    parsing_error = "JSONDecodeError和正则表达式回退都失败了。"
                    if verbose:
                        print("      ❌ 错误: 正则表达式无法找到JSON数组结构")
            
            except ValueError as val_err:
                parsing_error = f"ValueError: {val_err}"
                if verbose:
                    print(f"   ❌ 错误: {parsing_error}")
        
        # 验证并提取三元组
        valid_triples = []
        
        if parsed_json is not None:
            if isinstance(parsed_json, list):
                for item in parsed_json:
                    if isinstance(item, dict) and all(k in item for k in ['subject', 'predicate', 'object']):
                        # 基本检查：确保值是字符串
                        if all(isinstance(item[k], str) for k in ['subject', 'predicate', 'object']):
                            item['chunk'] = chunk_number
                            valid_triples.append(item)
                        else:
                            if verbose:
                                print(f"   ⚠️ 跳过非字符串值的三元组: {item}")
                    else:
                        if verbose:
                            print(f"   ⚠️ 跳过结构不正确的项: {item}")
            else:
                parsing_error = "解析的数据不是列表，无法提取三元组。"
        
        if parsing_error and not valid_triples:
            return [], parsing_error
        
        return valid_triples, None
    
    def extract_triples_from_text(
        self,
        text: str,
        chunk_size: int = 150,
        overlap: int = 30,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        从完整文本中提取所有三元组
        
        Args:
            text: 要处理的文本
            chunk_size: 每块的词数
            overlap: 重叠词数
            verbose: 是否打印详细信息
            
        Returns:
            包含triples、failed_chunks等信息的字典
        """
        # 分块
        if verbose:
            print(f"📝 开始文本分块 (chunk_size={chunk_size}, overlap={overlap})...")
        chunks = self.chunk_text(text, chunk_size, overlap)
        if verbose:
            print(f"✅ 文本已分割为 {len(chunks)} 个块")
        
        # 提取三元组
        all_extracted_triples = []
        failed_chunks = []
        
        if verbose:
            print(f"\n🔍 开始从 {len(chunks)} 个块中提取三元组...")
        
        for chunk_info in chunks:
            chunk_text = chunk_info['text']
            chunk_num = chunk_info['chunk_number']
            
            triples, error = self.extract_triples_from_chunk(
                chunk_text, chunk_num, verbose=verbose
            )
            
            if error:
                failed_chunks.append({
                    'chunk_number': chunk_num,
                    'error': error
                })
            else:
                all_extracted_triples.extend(triples)
                if verbose:
                    print(f"   ✅ Chunk {chunk_num}: 提取了 {len(triples)} 个三元组")
        
        return {
            'triples': all_extracted_triples,
            'failed_chunks': failed_chunks,
            'total_chunks': len(chunks),
            'successful_chunks': len(chunks) - len(failed_chunks)
        }
    
    def normalize_triples(
        self,
        triples: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        规范化三元组（去重、标准化）
        
        Args:
            triples: 原始三元组列表
            
        Returns:
            规范化后的三元组列表
        """
        normalized_triples = []
        seen_triples = set()  # 跟踪(subject, predicate, object)元组
        
        for triple in triples:
            subject_raw = triple.get('subject')
            predicate_raw = triple.get('predicate')
            object_raw = triple.get('object')
            chunk_num = triple.get('chunk', 'unknown')
            
            if isinstance(subject_raw, str) and isinstance(predicate_raw, str) and isinstance(object_raw, str):
                # 规范化
                normalized_sub = subject_raw.strip().lower()
                normalized_pred = re.sub(r'\s+', ' ', predicate_raw.strip().lower()).strip()
                normalized_obj = object_raw.strip().lower()
                
                # 过滤空值
                if normalized_sub and normalized_pred and normalized_obj:
                    triple_identifier = (normalized_sub, normalized_pred, normalized_obj)
                    
                    # 去重
                    if triple_identifier not in seen_triples:
                        normalized_triples.append({
                            'subject': normalized_sub,
                            'predicate': normalized_pred,
                            'object': normalized_obj,
                            'source_chunk': chunk_num
                        })
                        seen_triples.add(triple_identifier)
        
        return normalized_triples


def test_spo_extractor():
    """测试SPO提取器"""
    test_text = """
    玛丽·居里，原名玛丽亚·斯克沃多夫斯卡，出生于波兰华沙，是一位开创性的物理学家和化学家。
    她在放射性研究方面进行了开创性的研究。与她的丈夫皮埃尔·居里一起，
    她发现了元素钋和镭。玛丽·居里是第一位获得诺贝尔奖的女性，
    第一位也是唯一一位两次获得诺贝尔奖的女性，
    也是唯一一位在两个不同科学领域获得诺贝尔奖的人。
    """
    
    print("🧪 测试SPO三元组提取器")
    print("=" * 60)
    
    try:
        extractor = SPOTripleExtractor(verbose=True)
        result = extractor.extract_triples_from_text(
            test_text,
            chunk_size=50,
            overlap=10,
            verbose=True
        )
        
        print(f"\n📊 提取结果:")
        print(f"   总块数: {result['total_chunks']}")
        print(f"   成功块数: {result['successful_chunks']}")
        print(f"   失败块数: {len(result['failed_chunks'])}")
        print(f"   提取的三元组数: {len(result['triples'])}")
        
        # 规范化
        normalized = extractor.normalize_triples(result['triples'])
        print(f"   规范化后的三元组数: {len(normalized)}")
        
        print(f"\n📋 前5个三元组:")
        for i, triple in enumerate(normalized[:5]):
            print(f"   {i+1}. {triple['subject']} --[{triple['predicate']}]--> {triple['object']}")
        
        return normalized
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return []


if __name__ == "__main__":
    test_spo_extractor()

