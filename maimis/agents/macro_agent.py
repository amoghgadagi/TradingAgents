from __future__ import annotations

import math

from maimis.models import AgentSignal


class MacroeconomicAgent:
    name = "macroeconomic"

    def run(self, macro: dict[str, float]) -> AgentSignal:
        vix = macro.get("vix", float("nan"))
        tnx = macro.get("tnx", float("nan"))
        dxy = macro.get("dxy", float("nan"))

        safe_vix = 20 if math.isnan(vix) else vix
        safe_tnx = 4.0 if math.isnan(tnx) else tnx
        safe_dxy = 103 if math.isnan(dxy) else dxy

        risk_on = 0
        risk_on += 1 if safe_vix < 18 else -1
        risk_on += 1 if safe_tnx < 4.5 else -1
        risk_on += 1 if safe_dxy < 104 else -1

        direction = "bullish" if risk_on >= 1 else "bearish"
        score = 0.5 + (risk_on / 6)
        confidence = 0.55 + abs(risk_on) * 0.08

        summary = f"Macro proxies VIX={safe_vix:.2f}, TNX={safe_tnx:.2f}, DXY={safe_dxy:.2f}; context={direction}."

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(max(0.05, min(0.95, score))),
            confidence=float(min(0.9, confidence)),
            details={"vix": safe_vix, "tnx": safe_tnx, "dxy": safe_dxy},
        )
