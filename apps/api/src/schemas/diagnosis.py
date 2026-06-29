from pydantic import Field

from src.schemas.resume import _DropNone


class DimScore(_DropNone):
    """单维度评分 1-5 + 说明。"""

    score: int = 3
    comment: str = ""


class StructureScore(_DropNone):
    """一、整体结构评分（4 维度）+ 综合分。"""

    module_completeness: DimScore = Field(default_factory=DimScore)  # 模块完整性
    module_order: DimScore = Field(default_factory=DimScore)  # 模块顺序
    length_control: DimScore = Field(default_factory=DimScore)  # 篇幅控制
    readability: DimScore = Field(default_factory=DimScore)  # 视觉可读性
    composite_score: int = 0  # 综合 0-100


class WeakVerbs(_DropNone):
    ratio_pct: int = 0
    comment: str = ""
    examples: list[str] = Field(default_factory=list)


class ATSCheck(_DropNone):
    """二、ATS 兼容性检查。"""

    format_risks: list[str] = Field(default_factory=list)  # 格式风险
    keyword_density_comment: str = ""  # 关键词密度
    missing_keywords: list[str] = Field(default_factory=list)  # 缺失关键词
    weak_verbs: WeakVerbs = Field(default_factory=WeakVerbs)  # 弱动词


class HighlightsIssues(_DropNone):
    """三、亮点与硬伤。"""

    issues: list[str] = Field(default_factory=list)  # 🔴 硬伤
    highlights: list[str] = Field(default_factory=list)  # 🟢 亮点


class BenchmarkRow(_DropNone):
    """四、行业对标的一行。"""

    dimension: str = ""  # 项目深度 / 量化成果 / 技术技能栈 / 软素质
    expected: str = ""  # 行业期望
    current: str = ""  # 你当前
    gap: str = ""  # 差距小结


class FixPriorities(_DropNone):
    """五、修复优先级。"""

    urgent: list[str] = Field(default_factory=list)  # 🔴 最紧急
    important: list[str] = Field(default_factory=list)  # 🟠 重要
    nice_to_have: list[str] = Field(default_factory=list)  # 🟡 锦上添花


class WeakCard(_DropNone):
    """低含金量卡片标记（保留原有逐卡标记能力）。"""

    type: str = ""  # ability | project | experience
    id: str = ""
    reasons: list[str] = Field(default_factory=list)


class DiagnosisReport(_DropNone):
    """简历全景诊断报告。"""

    target_industry: str = ""  # 模型推断的目标行业/角色
    structure: StructureScore = Field(default_factory=StructureScore)
    ats: ATSCheck = Field(default_factory=ATSCheck)
    highlights_issues: HighlightsIssues = Field(default_factory=HighlightsIssues)
    industry_benchmark: list[BenchmarkRow] = Field(default_factory=list)
    fix_priorities: FixPriorities = Field(default_factory=FixPriorities)
    weak_cards: list[WeakCard] = Field(default_factory=list)
    # 后端派生：综合分 < 30 判为不合格，前端引导去"AI 挖经历"
    qualified: bool = True


__all__ = ["DiagnosisReport"]
