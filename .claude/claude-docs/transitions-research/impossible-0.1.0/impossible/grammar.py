"""The transition grammar: what the user can say, with sensible defaults.

A TransitionSpec composes PATHS (warp, dissolve, portal, color, generative)
each with its own timing curve over the normalized time u in [0,1]. Presets
are named specs. A SequenceSpec chains N media items with N-1 transitions,
which is the multi-clip/multi-photo use case the operator is heading for.
"""
import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path

MIN_SECONDS, MAX_SECONDS = 0.1, 10.0

CURVES = {
    "linear": lambda u: u,
    "ease": lambda u: 0.5 - 0.5 * math.cos(math.pi * u),
    "ease-in": lambda u: u * u,
    "ease-out": lambda u: 1 - (1 - u) ** 2,
    "snap": lambda u: 0.0 if u < 0.5 else 1.0,
    "hold-then-go": lambda u: 0.0 if u < 0.35 else (u - 0.35) / 0.65,
}


def curve(name, u):
    return float(min(1.0, max(0.0, CURVES.get(name, CURVES["ease"])(u))))


@dataclass
class TransitionSpec:
    seconds: float = 1.0
    fps: float = 30.0
    style: str = "morph"           # morph | dissolve | warp-dissolve | portal | luma
    warp_curve: str = "ease"       # geometric progress
    mix_curve: str = "ease"        # cross-dissolve progress
    mix_delay: float = 0.0         # shift dissolve later (+) or earlier (-), in u
    warp_amount: float = 1.0       # 0 = pure dissolve on the skeleton, 1 = full
    color_strength: float = 0.7    # time-varying color pull, 0..1
    portal: str = "iris"           # iris | wipe (style=portal)
    portal_feather: float = 0.08
    dreaminess: int = 0            # 0..100; >0 enables the generative tier
    gen_window: tuple = (0.2, 0.8) # u-window where enrichment may act
    seed: int = 0
    budget_minutes: float = 10.0   # hard wall-clock cap for generative work
    max_long_edge: int = 0         # 0 = native canvas
    anchors: list = field(default_factory=list)   # [[ax, ay, bx, by], ...]
    force_class: str = ""          # "", "A", "B"

    def n_frames(self):
        return max(2, int(round(self.seconds * self.fps)))

    def clamp(self):
        self.seconds = float(min(MAX_SECONDS, max(MIN_SECONDS, self.seconds)))
        self.dreaminess = int(min(100, max(0, self.dreaminess)))
        self.warp_amount = float(min(1.0, max(0.0, self.warp_amount)))
        self.color_strength = float(min(1.0, max(0.0, self.color_strength)))
        return self

    def progress(self, i):
        """(t_warp, t_mix) for frame i of n."""
        n = self.n_frames()
        u = i / (n - 1)
        tw = curve(self.warp_curve, u) * self.warp_amount + (1 - self.warp_amount) * u
        um = min(1.0, max(0.0, u - self.mix_delay)) if self.mix_delay >= 0 \
            else min(1.0, max(0.0, u / (1 + self.mix_delay)))
        return tw, curve(self.mix_curve, um), u


PRESETS = {
    "auto": {},
    "morph": {"style": "morph", "warp_curve": "ease", "mix_curve": "ease"},
    "dissolve": {"style": "dissolve", "warp_amount": 0.0},
    "flow-dissolve": {"style": "warp-dissolve", "warp_amount": 0.6, "mix_delay": 0.1},
    "snap-morph": {"style": "morph", "warp_curve": "hold-then-go", "mix_curve": "ease-in"},
    "iris": {"style": "portal", "portal": "iris"},
    "luma": {"style": "luma"},
    "dream": {"style": "morph", "dreaminess": 60},
}


def spec_from(preset="auto", **over):
    s = TransitionSpec(**{**PRESETS.get(preset, {}), **over})
    return s.clamp()


@dataclass
class MediaItem:
    path: str
    kind: str = "auto"      # auto | image | video
    hold: float = 2.0       # seconds an image is shown
    cut_in: float = 0.0     # video: start (s)
    cut_out: float = -1.0   # video: end (s), -1 = until end


@dataclass
class SequenceSpec:
    items: list                  # [MediaItem]
    transitions: list            # [TransitionSpec], len = len(items)-1
    output: str = "sequence.mp4"
    fps: float = 0.0             # 0 = from the first video item, else 30
    width: int = 0               # 0 = from the first video item
    height: int = 0

    @staticmethod
    def load(path):
        d = json.loads(Path(path).read_text())
        items = [MediaItem(**it) for it in d["items"]]
        trans = [spec_from(t.pop("preset", "auto"), **t) for t in d.get("transitions", [])]
        while len(trans) < len(items) - 1:
            trans.append(spec_from("auto"))
        return SequenceSpec(items, trans, d.get("output", "sequence.mp4"),
                            d.get("fps", 0.0), d.get("width", 0), d.get("height", 0))

    def dump(self):
        return {"items": [asdict(i) for i in self.items],
                "transitions": [asdict(t) for t in self.transitions],
                "output": self.output, "fps": self.fps,
                "width": self.width, "height": self.height}
