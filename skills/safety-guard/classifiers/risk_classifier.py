"""
OpenClaw Safety Guard - Risk Classifier
基于 ML 模型的风险分类器（支持多种后端）

支持：
1. Vijil Prompt Injection (推荐)
2. 简单的启发式评分（fallback）
3. 未来可扩展 LlamaGuard 等
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RiskAssessment:
    """风险评估结果"""
    score: float  # 0.0 - 1.0
    level: str    # low, medium, high, critical
    reasons: list
    model_used: str


class RiskClassifier:
    """风险分类器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model = None
        self.model_name = "heuristic"  # 默认使用启发式
        
        # 尝试加载 ML 模型
        self._try_load_model()
    
    def _try_load_model(self):
        """尝试加载 ML 模型"""
        detector_config = self.config.get("detectors", {}).get("prompt_injection", {})
        
        if not detector_config.get("enabled", True):
            return
        
        model_name = detector_config.get("model", "heuristic")
        
        if model_name == "vijil-prompt-injection":
            self._load_vijil_model()
        elif model_name == "modernbert-classifier":
            self._load_modernbert_model()
        # 其他模型...
    
    def _load_vijil_model(self):
        """加载 Vijil Prompt Injection 模型"""
        try:
            # 需要安装：pip install transformers torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            # Vijil 多语言 Prompt 注入检测模型
            model_path = "vijil/mbert-prompt-injection"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model_name = "vijil/mbert-prompt-injection"
            
        except ImportError:
            print("⚠️  transformers 未安装，使用启发式分类器")
        except Exception as e:
            print(f"⚠️  无法加载 Vijil 模型：{e}，使用启发式分类器")
    
    def _load_modernbert_model(self):
        """加载 ModernBERT 分类器"""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            model_path = "nlpcloud/modernbert-inject"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model_name = "modernbert-classifier"
            
        except Exception as e:
            print(f"⚠️  无法加载 ModernBERT 模型：{e}，使用启发式分类器")
    
    def assess(self, text: str) -> RiskAssessment:
        """
        评估文本风险
        
        Args:
            text: 用户输入
            
        Returns:
            风险评估结果
        """
        if self.model is not None:
            return self._assess_with_model(text)
        else:
            return self._assess_heuristic(text)
    
    def _assess_with_model(self, text: str) -> RiskAssessment:
        """使用 ML 模型评估"""
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            import torch
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)[0]
                
                # 假设 label 1 是"有害"
                risk_score = probabilities[1].item() if len(probabilities) > 1 else probabilities[0].item()
            
            level = self._score_to_level(risk_score)
            
            return RiskAssessment(
                score=risk_score,
                level=level,
                reasons=[f"{self.model_name} 评分：{risk_score:.2f}"],
                model_used=self.model_name
            )
            
        except Exception as e:
            # Fallback 到启发式
            return self._assess_heuristic(text)
    
    def _assess_heuristic(self, text: str) -> RiskAssessment:
        """
        启发式风险评估（不依赖外部模型）
        
        基于以下因素：
        1. 敏感关键词密度
        2. 指令覆盖尝试
        3. 命令危险性
        4. 文本长度异常
        """
        score = 0.0
        reasons = []
        
        text_lower = text.lower()
        text_for_matching = text_lower  # 保留原始用于中文匹配
        
        # 1. 检测指令覆盖尝试 (+0.5)
        injection_patterns = [
            r"ignore\s+(previous|all)",
            r"disregard\s+(instructions|all)",
            r"forget\s+(all\s+)?instructions",
            r"override\s+your",
            r"bypass\s+(your\s+)?(safety|restrictions)",
            r"(developer|dan)\s+mode",
            r"do\s+anything\s+now",
            r"without\s+(any\s+)?restrictions",
            r"no\s+(ethical\s+)?guidelines",
            # 中文注入模式
            r"忽略所有",
            r"忽略之前",
            r"忘记所有",
            r"覆盖指令",
            r"绕过安全",
            r"开发者模式",
            r"dan 模式",
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, text_for_matching, re.IGNORECASE):
                score += 0.5  # 注入检测权重更高
                reasons.append(f"检测到指令覆盖尝试")
                break  # 只计一次，避免累加过高
        
        # 2. 检测危险命令 (+0.4)
        dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r"sudo\s+rm",
            r"format\s+[c-z]:",
            r"dd\s+if=/dev/",
            r":\(\)\{:\|:&\};:",  # fork bomb
            r"chmod\s+-R\s+777",
            r"kill\s+-9\s+1",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower):
                score += 0.4
                reasons.append(f"检测到危险命令模式")
        
        # 3. 检测有害内容关键词 (+0.4)
        harmful_keywords = [
            "bomb", "weapon", "kill", "murder", "poison",
            "hack", "steal", "malware", "virus",
            "suicide", "self harm",
            "drugs", "meth", "synthesize",
            # 中文
            "炸弹", "武器", "杀人", "谋杀", "毒药",
            "黑客", "盗窃", "恶意软件", "病毒",
            "自杀", "自我伤害",
            "毒品", "冰毒", "合成",
            "钓鱼", "诈骗", "欺诈",
        ]
        
        # 高风险组合词（直接 +0.6）
        high_risk_phrases = [
            "钓鱼邮件", "phishing email", "phishing message",
            "诈骗邮件", "fraud email", "scam email",
            "伪造身份", "fake identity", "impersonate",
            "写一封钓鱼", "写钓鱼",
        ]
        
        # 检查高风险组合
        for phrase in high_risk_phrases:
            if phrase in text_for_matching:
                score += 0.8  # 高风险组合直接 +0.8
                reasons.append(f"检测到高风险请求")
                break
        
        # 检查单个关键词
        harmful_count = sum(1 for kw in harmful_keywords if kw in text_for_matching)
        if harmful_count > 0:
            score += min(0.4, harmful_count * 0.15)
            if not any("高风险" in r for r in reasons):
                reasons.append(f"检测到敏感内容")
        
        # 4. 检测过长输入（可能是注入攻击）(+0.1)
        if len(text) > 2000:
            score += 0.1
            reasons.append("输入长度异常")
        
        # 5. 检测重复字符（可能是绕过尝试）(+0.1)
        if re.search(r'(.)\1{10,}', text):
            score += 0.1
            reasons.append("检测到重复字符模式")
        
        # 归一化到 0-1
        score = min(1.0, score)
        level = self._score_to_level(score)
        
        if not reasons:
            reasons = ["未检测到明显风险模式"]
        
        return RiskAssessment(
            score=score,
            level=level,
            reasons=reasons,
            model_used="heuristic"
        )
    
    def _score_to_level(self, score: float) -> str:
        """将分数转换为风险级别"""
        if score < 0.3:
            return "low"
        elif score < 0.65:
            return "medium"
        elif score < 0.85:
            return "high"
        else:
            return "critical"
