"""
OpenClaw Safety Guard - Pattern Matcher
基于规则的快速模式匹配检测器
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """模式匹配结果"""
    pattern: str
    category: str
    severity: str
    policy_id: Optional[str] = None


class PatternMatcher:
    """基于 YAML 配置的模式匹配器"""
    
    def __init__(self, patterns_file: Optional[str] = None, policies_file: Optional[str] = None):
        self.base_path = Path(__file__).parent.parent
        
        # 加载配置
        patterns_path = patterns_file or self.base_path / "rules" / "patterns.yaml"
        policies_path = policies_file or self.base_path / "rules" / "policies.yaml"
        
        self.patterns = self._load_yaml(patterns_path)
        self.policies = self._load_yaml(policies_path)
        
        # 编译正则表达式（预编译提高性能）
        self.compiled_patterns = self._compile_patterns()
    
    def _load_yaml(self, path: Path) -> Dict:
        """加载 YAML 文件"""
        if not path.exists():
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, str, str]]]:
        """预编译所有模式"""
        compiled = {}
        
        for category, patterns in self.patterns.items():
            compiled[category] = []
            
            if isinstance(patterns, dict):
                # 嵌套结构（如 harmful_content）
                for subcategory, subpatterns in patterns.items():
                    if isinstance(subpatterns, list):
                        for pattern in subpatterns:
                            try:
                                regex = re.compile(re.escape(pattern), re.IGNORECASE)
                                compiled[category].append((regex, subcategory, "medium"))
                            except re.error:
                                pass
            elif isinstance(patterns, list):
                # 扁平列表
                for pattern in patterns:
                    try:
                        regex = re.compile(re.escape(pattern), re.IGNORECASE)
                        compiled[category].append((regex, category, "medium"))
                    except re.error:
                        pass
        
        return compiled
    
    def match(self, text: str) -> List[PatternMatch]:
        """
        匹配输入文本
        
        Args:
            text: 用户输入文本
            
        Returns:
            匹配结果列表
        """
        matches = []
        text_lower = text.lower()
        
        for category, patterns in self.compiled_patterns.items():
            for regex, subcategory, default_severity in patterns:
                if regex.search(text_lower):
                    # 查找对应的策略
                    policy_id = self._find_policy_for_pattern(category, regex.pattern)
                    
                    matches.append(PatternMatch(
                        pattern=regex.pattern,
                        category=category,
                        severity=self._get_severity(category, subcategory),
                        policy_id=policy_id
                    ))
        
        return matches
    
    def _find_policy_for_pattern(self, category: str, pattern: str) -> Optional[str]:
        """查找匹配的策略 ID"""
        if not self.policies or "policies" not in self.policies:
            return None
        
        for policy in self.policies.get("policies", []):
            policy_patterns = policy.get("patterns", [])
            if pattern in policy_patterns:
                return policy.get("id")
        
        return None
    
    def _get_severity(self, category: str, subcategory: str) -> str:
        """获取严重级别"""
        # 高风险类别
        high_risk_categories = ["jailbreak", "dangerous_commands"]
        if category in high_risk_categories:
            return "high"
        
        # 有害内容的某些子类也是高风险
        if category == "harmful_content":
            if subcategory in ["violence", "illegal", "self_harm"]:
                return "high"
        
        return "medium"
    
    def has_match(self, text: str) -> bool:
        """快速检查是否有匹配"""
        return len(self.match(text)) > 0
    
    def get_match_summary(self, text: str) -> str:
        """获取匹配摘要（用于用户提示）"""
        matches = self.match(text)
        
        if not matches:
            return "未检测到风险模式"
        
        categories = set(m.category for m in matches)
        return f"检测到风险模式：{', '.join(categories)}"
