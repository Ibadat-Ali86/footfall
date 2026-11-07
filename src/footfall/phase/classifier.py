"""Rule-based lifecycle phase classifier.

Implements Section 9.7 and Appendix C of docs/BUILD.md:
- First-match-wins rule evaluation
- 8 discrete lifecycle phases
- Input provenance tracking for every classification
- Configured via config/methods.yaml
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class LifecyclePhase(StrEnum):
    """Discrete lifecycle phase of an AI developer tool."""

    INSUFFICIENT_DATA = "insufficient_data"
    BREAKOUT = "breakout"
    ATTENTION_AHEAD = "attention_ahead"
    USE_AHEAD = "use_ahead"
    FADING = "fading"
    EMERGING = "emerging"
    MAINSTREAM = "mainstream"
    PLATEAU = "plateau"


@dataclass(frozen=True)
class PhaseInput:
    """Provenance inputs required for deterministic phase classification."""

    history_weeks: int
    star_history_days: int
    weekly_volume: float
    adoption_z: float
    attention_z: float
    divergence: float
    g4: float
    g12: float
    age_months: float
    consecutive_fading_weeks: int = 0
    is_category_top_quartile: bool = False
    consecutive_plateau_weeks: int = 0


@dataclass(frozen=True)
class PhaseResult:
    """Output phase classification with confidence and audit provenance."""

    phase: LifecyclePhase
    confidence: str
    rule_matched: str
    method_version: str = "m1.0"
    inputs: PhaseInput | None = None


class PhaseClassifier:
    """Evaluates Section 9.7 rules in strict first-match-wins order."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        if config_path is None:
            config_path = Path(__file__).parents[3] / "config" / "methods.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.method_version = str(self.config.get("method_version", "m1.0"))

        # Thresholds
        self.w_min = float(self.config.get("volume", {}).get("W_min", 500.0))
        phases_cfg = self.config.get("phases", {})
        self.breakout_adoption_z = float(phases_cfg.get("breakout", {}).get("adoption_z_min", 1.0))
        self.breakout_g4_min = float(phases_cfg.get("breakout", {}).get("g4_min_ln", 0.2231))
        self.attn_ahead_div_min = float(
            phases_cfg.get("attention_ahead", {}).get("divergence_min", 1.0)
        )
        self.attn_ahead_adopt_max = float(
            phases_cfg.get("attention_ahead", {}).get("adoption_z_max", 0.5)
        )
        self.use_ahead_div_max = float(phases_cfg.get("use_ahead", {}).get("divergence_max", -1.0))
        self.use_ahead_adopt_min = float(phases_cfg.get("use_ahead", {}).get("adoption_z_min", 0.5))
        self.fading_adopt_max = float(phases_cfg.get("fading", {}).get("adoption_z_max", -1.0))
        self.fading_weeks = int(phases_cfg.get("fading", {}).get("weeks", 4))
        self.emerging_max_age = float(phases_cfg.get("emerging", {}).get("max_age_months", 6.0))
        self.mainstream_abs_g4 = float(phases_cfg.get("mainstream", {}).get("abs_g4_max", 0.1))
        self.plateau_abs_g12 = float(phases_cfg.get("plateau", {}).get("abs_g12_max", 0.1))
        self.plateau_weeks = int(phases_cfg.get("plateau", {}).get("weeks", 8))

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML."""
        if not self.config_path.is_file():
            return {}
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}

    def classify(self, inp: PhaseInput) -> PhaseResult:
        """Apply Section 9.7 rules. First match wins."""
        # 1. insufficient_data: Fewer than 12 weeks of downloads or 56 days of stars
        if inp.history_weeks < 12 or inp.star_history_days < 56:
            return PhaseResult(
                phase=LifecyclePhase.INSUFFICIENT_DATA,
                confidence="high",
                rule_matched="rule_1_insufficient_data",
                method_version=self.method_version,
                inputs=inp,
            )

        # 2. breakout: adoption_z >= 1.0 and g4 >= ln(1.25) and W >= W_min
        if (
            inp.adoption_z >= self.breakout_adoption_z
            and inp.g4 >= self.breakout_g4_min
            and inp.weekly_volume >= self.w_min
        ):
            return PhaseResult(
                phase=LifecyclePhase.BREAKOUT,
                confidence="high",
                rule_matched="rule_2_breakout",
                method_version=self.method_version,
                inputs=inp,
            )

        # 3. attention_ahead: D >= 1.0 and adoption_z < 0.5
        if inp.divergence >= self.attn_ahead_div_min and inp.adoption_z < self.attn_ahead_adopt_max:
            return PhaseResult(
                phase=LifecyclePhase.ATTENTION_AHEAD,
                confidence="high",
                rule_matched="rule_3_attention_ahead",
                method_version=self.method_version,
                inputs=inp,
            )

        # 4. use_ahead: D <= -1.0 and adoption_z >= 0.5
        if inp.divergence <= self.use_ahead_div_max and inp.adoption_z >= self.use_ahead_adopt_min:
            return PhaseResult(
                phase=LifecyclePhase.USE_AHEAD,
                confidence="high",
                rule_matched="rule_4_use_ahead",
                method_version=self.method_version,
                inputs=inp,
            )

        # 5. fading: adoption_z <= -1.0 and g12 < 0 for 4 consecutive weeks
        if (
            inp.adoption_z <= self.fading_adopt_max
            and inp.g12 < 0.0
            and inp.consecutive_fading_weeks >= self.fading_weeks
        ):
            return PhaseResult(
                phase=LifecyclePhase.FADING,
                confidence="high",
                rule_matched="rule_5_fading",
                method_version=self.method_version,
                inputs=inp,
            )

        # 6. emerging: Age under 6 months and none of the above
        if inp.age_months < self.emerging_max_age:
            return PhaseResult(
                phase=LifecyclePhase.EMERGING,
                confidence="high",
                rule_matched="rule_6_emerging",
                method_version=self.method_version,
                inputs=inp,
            )

        # 7. mainstream: W in the top quartile of category and abs(g4) < 0.1
        if inp.is_category_top_quartile and abs(inp.g4) < self.mainstream_abs_g4:
            return PhaseResult(
                phase=LifecyclePhase.MAINSTREAM,
                confidence="high",
                rule_matched="rule_7_mainstream",
                method_version=self.method_version,
                inputs=inp,
            )

        # 8. plateau: abs(g12) < 0.1 for 8 weeks
        if (
            abs(inp.g12) < self.plateau_abs_g12
            and inp.consecutive_plateau_weeks >= self.plateau_weeks
        ):
            return PhaseResult(
                phase=LifecyclePhase.PLATEAU,
                confidence="high",
                rule_matched="rule_8_plateau",
                method_version=self.method_version,
                inputs=inp,
            )

        # Default fallback: plateau with confidence = low
        return PhaseResult(
            phase=LifecyclePhase.PLATEAU,
            confidence="low",
            rule_matched="fallback_plateau_low_confidence",
            method_version=self.method_version,
            inputs=inp,
        )
