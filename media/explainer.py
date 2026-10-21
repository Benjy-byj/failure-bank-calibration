"""Animated overview of the failure-bank papers (Manim Community).
Each scene is timed to its narration beats in timeline.json (see narration.py).
Render:  manim -qh explainer.py S3Noise        (1080p60; one class per scene, see SCENES)
All numbers come from the two workshop papers and the released artifact."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm
from manim import *

HERE = Path(__file__).resolve().parent
TL = json.load(open(HERE / "timeline.json"))
REPS = json.load(open(HERE / "replicates.json"))   # per-loop discoveries, sysloop/results (point truth)

BG, PANEL, FAINT = "#0F1923", "#16232F", "#2B3B4C"
INK, MUTED = "#E6ECF2", "#8FA0B2"
RED, TEAL, GOLD = "#E0685C", "#14A193", "#BD8524"   # validated: dark mode, CVD-safe with labels
RED_BG, TEAL_BG = "#2A1D22", "#122B2C"
FONT, MONO = "Inter", "JetBrains Mono"
config.background_color = BG


def T(s, size=30, color=INK, w=NORMAL, mono=False, **kw):
    return Text(s, font=MONO if mono else FONT, font_size=size, color=color, weight=w, **kw)


def header(title, sub=None):
    g = VGroup(T(title, 40, w="SEMIBOLD"))
    if sub:
        g.add(T(sub, 22, MUTED))
    return g.arrange(DOWN, aligned_edge=LEFT, buff=0.16).to_corner(UL, buff=0.55)


def caption(main, sub=None, y=-3.3, size=28):
    g = VGroup(VGroup(*[T(line, size) for line in main.split("\n")]).arrange(DOWN, buff=0.1))
    if sub:
        g.add(T(sub, 22, MUTED))
    return g.arrange(DOWN, buff=0.14).move_to([0, y, 0])


def card(w, h, stroke=MUTED, fill=PANEL, r=0.16, sw=2.2):
    return RoundedRectangle(width=w, height=h, corner_radius=r, stroke_color=stroke,
                            stroke_width=sw, fill_color=fill, fill_opacity=1)


def cross(size=0.22, color=RED, sw=5):
    return VGroup(Line([-size, -size, 0], [size, size, 0]), Line([-size, size, 0], [size, -size, 0])).set_stroke(color, sw)


def check(size=0.22, color=TEAL, sw=5):
    return VMobject().set_points_as_corners([[-size, 0, 0], [-size * 0.3, -size * 0.7, 0], [size, size * 0.8, 0]]).set_stroke(color, sw)


def stamp(text="DEAD", size=40, color=RED):
    t = T(text, size, color, w="BOLD")
    box = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.36, corner_radius=0.12,
                           stroke_color=color, stroke_width=4, fill_color=BG, fill_opacity=0.85)
    return VGroup(box, t.move_to(box))


def soft_backdrop(w, h, layers=10):
    return VGroup(*[Ellipse(width=w * (1 - 0.06 * i), height=h * (1 - 0.06 * i), stroke_width=0,
                            fill_color=BG, fill_opacity=0.16) for i in range(layers)])


def edge_curve(p0, p1):
    dx = (p1[0] - p0[0]) * 0.5
    return CubicBezier(p0, p0 + np.array([dx, 0, 0]), p1 - np.array([dx, 0, 0]), p1)


def bg_tree(depth=6, x0=-6.7, x1=6.7, ytop=3.5, ybot=-3.5, seed=4):
    rng = np.random.default_rng(seed)
    nodes = {(0, 0): np.array([x0, -0.2, 0.0])}
    edges, levels = [], [[(0, 0)]]
    for d in range(1, depth):
        n, lvl = 2 ** d, []
        for k in range(n):
            y = ytop - (ytop - ybot) * (k + 0.5) / n + rng.uniform(-0.12, 0.12) * (ytop - ybot) / n
            nodes[(d, k)] = np.array([x0 + (x1 - x0) * d / (depth - 1) + rng.uniform(-0.18, 0.18), y, 0.0])
            edges.append(((d - 1, k // 2), (d, k)))
            lvl.append((d, k))
        levels.append(lvl)
    return nodes, edges, levels


def build_tree(opacity=0.28, run_time=5.2):
    nodes, edges, levels = bg_tree()
    curves = {e: edge_curve(nodes[e[0]], nodes[e[1]]).set_stroke(MUTED, 1.6, opacity=opacity) for e in edges}
    dots = {k: Dot(p, radius=0.045, color=MUTED, fill_opacity=min(1, opacity * 1.6)) for k, p in nodes.items()}
    grow = LaggedStart(*[AnimationGroup(*[Create(curves[e]) for e in edges if e[1][0] == d],
                                        *[FadeIn(dots[k], scale=0.3) for k in levels[d]])
                         for d in range(1, len(levels))], lag_ratio=0.85, run_time=run_time)
    return nodes, curves, dots, grow


class Base(Scene):
    key = None

    def setup(self):
        self.tl, self.sfx = TL[self.key], []

    def until(self, t):
        dt = t - self.time
        if dt >= 1 / 30:
            self.wait(dt)
        elif dt < -0.08:
            print(f"WARN {self.key}: overran by {-dt:.2f}s before t={t:.2f}", flush=True)

    def b(self, i, f=0.0):
        bt = self.tl["beats"][i]
        self.until(bt["start"] + f * bt["dur"])

    def bt(self, i, f=0.0):
        bt = self.tl["beats"][i]
        return bt["start"] + f * bt["dur"]

    def snd(self, name, delay=0.0):
        self.sfx.append([round(self.time + delay, 3), name])

    def outro(self):
        self.until(self.tl["total"] - 0.55)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.45)
        self.until(self.tl["total"])
        json.dump(self.sfx, open(HERE / f"sfx_{self.key}.json", "w"))


# ---------------------------------------------------------------- 1 title
class S1Title(Base):
    key = "title"

    def construct(self):
        nodes, curves, dots, grow = build_tree()
        title = VGroup(T("Wrongful Convictions in", 66, w="BOLD"), T("Shared Failure Banks", 66, w="BOLD")).arrange(DOWN, buff=0.22).move_to(UP * 1.0)
        sub = T("why the memory of failure in automated science should keep its evidence", 26, MUTED).next_to(title, DOWN, buff=0.45)
        rule = Line(LEFT * 2.0, RIGHT * 2.0, color=TEAL, stroke_width=3).next_to(sub, DOWN, buff=0.42)
        auth = T("Yingjie Bai  ·  Weiming Zhi", 26).next_to(rule, DOWN, buff=0.38)
        aff = T("The University of Sydney  ·  NeurIPS 2026 workshops", 20, MUTED).next_to(auth, DOWN, buff=0.14)
        back = soft_backdrop(13.5, 6.6).move_to(UP * 0.1)
        self.add(back)
        self.bring_to_back(back)
        self.play(AnimationGroup(grow, Succession(Wait(0.5), FadeIn(title, shift=UP * 0.25, run_time=1.3)),
                                 Succession(Wait(self.bt(1) - 0.2), FadeIn(sub, shift=UP * 0.15, run_time=0.9))))
        # one branch is convicted: its whole subtree disappears
        cut = (3, 0)
        desc = [k for k in nodes if k[0] > cut[0] and (k[1] >> (k[0] - cut[0])) == cut[1]]
        x = cross(0.13, RED, 4).move_to(nodes[cut])
        self.play(curves[((cut[0] - 1, cut[1] // 2), cut)].animate.set_stroke(RED, 2.4, opacity=0.8), dots[cut].animate.set_color(RED).set_opacity(0.9),
                  FadeIn(x, scale=1.6), run_time=0.5)
        self.snd("thud", -0.35)
        self.play(*[curves[e].animate.set_stroke(opacity=0.03) for e in curves if e[1] in desc],
                  *[dots[k].animate.set_opacity(0.04) for k in desc], run_time=1.2)
        self.play(Create(rule), FadeIn(auth, shift=UP * 0.1), FadeIn(aff, shift=UP * 0.1), run_time=0.9)
        self.outro()


# ---------------------------------------------------------------- 2 bank
def agent_icon(label):
    body = RoundedRectangle(width=1.0, height=0.82, corner_radius=0.2, stroke_color=MUTED, stroke_width=2.5, fill_color=PANEL, fill_opacity=1)
    c = body.get_center()
    face = VGroup(Dot(c + [-0.2, 0.07, 0], radius=0.07, color=INK), Dot(c + [0.2, 0.07, 0], radius=0.07, color=INK),
                  Line(c + [-0.15, -0.17, 0], c + [0.15, -0.17, 0], stroke_width=3, color=INK))
    ant = VGroup(Line(body.get_top(), body.get_top() + UP * 0.18, stroke_width=2.5, color=MUTED),
                 Dot(body.get_top() + UP * 0.23, radius=0.055, color=TEAL))
    lab = T(label, 18, MUTED).next_to(body, DOWN, buff=0.12)
    return VGroup(body, face, ant, lab)


def pill(text, stroke=MUTED, fill=PANEL, w=1.8):
    box = card(w, 0.5, stroke, fill, r=0.25, sw=2)
    return VGroup(box, T(text, 22, mono=True).move_to(box))


def record(idea, w=3.5):
    box = card(w, 0.52, RED, RED_BG, r=0.1, sw=2)
    a = T(f"idea {idea}", 22, mono=True).move_to(box).align_to(box, LEFT).shift(RIGHT * 0.25)
    b = T("DEAD", 22, RED, w="BOLD", mono=True).move_to(box).align_to(box, RIGHT).shift(LEFT * 0.25)
    return VGroup(box, a, b)


class S2Bank(Base):
    key = "bank"

    def construct(self):
        hd = header("Autonomous research agents share a failure bank")
        ys = [1.55, -0.25, -2.05]
        agents = VGroup(*[agent_icon(f"agent {i + 1}").move_to([-5.7, y, 0]) for i, y in enumerate(ys)])
        bank = card(4.3, 5.1, MUTED, PANEL).move_to([4.5, -0.3, 0])
        btitle = T("shared failure bank", 24, w="SEMIBOLD").move_to(bank.get_top() + DOWN * 0.42)
        bline = Line(bank.get_left() + RIGHT * 0.25, bank.get_right() + LEFT * 0.25, stroke_width=1.5, color=FAINT).next_to(btitle, DOWN, buff=0.22)
        slots = [bline.get_center() + DOWN * (0.55 + 0.68 * i) for i in range(5)]
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), LaggedStart(*[GrowFromCenter(a) for a in agents], lag_ratio=0.25),
                  FadeIn(bank), FadeIn(btitle), Create(bline), run_time=1.6)

        # beat 1: three experiments fail and are written down
        self.b(1)
        ideas, recs, seqs = ["17", "42", "8"], [], []
        for i, (idea, y) in enumerate(zip(ideas, ys)):
            p = pill(f"idea {idea}").move_to([-4.2, y, 0])
            lab = np.array([-1.3, y, 0])
            track = card(1.6, 0.1, FAINT, FAINT, r=0.05, sw=0).move_to(lab + DOWN * 0.45)
            fill = Rectangle(width=1.6, height=0.1, stroke_width=0, fill_color=MUTED, fill_opacity=1).move_to(track)
            x = cross(0.16).move_to(lab + RIGHT * 1.25)
            rec = record(idea).move_to(lab)
            recs.append(rec)
            arc = ArcBetweenPoints(lab, slots[i], angle=-0.6)
            seqs.append(Succession(FadeIn(p, shift=RIGHT * 0.3, run_time=0.3),
                                   AnimationGroup(p.animate(run_time=0.5).move_to(lab), FadeIn(track, run_time=0.5)),
                                   GrowFromEdge(fill, LEFT, run_time=0.6),
                                   FadeIn(x, scale=1.8, run_time=0.2),
                                   AnimationGroup(FadeOut(p), FadeIn(rec), FadeOut(x), FadeOut(track), FadeOut(fill), run_time=0.3),
                                   MoveAlongPath(rec, arc, run_time=0.7, rate_func=smooth)))
        per, lag = 2.6, 0.36
        for i in range(3):
            self.snd("tick", i * lag * per + per)
        self.play(LaggedStart(*seqs, lag_ratio=lag), run_time=per * (1 + 2 * lag))

        # beat 2: another agent skips idea 17 because of the record
        self.b(2)
        q = pill("idea 17 ?", TEAL, PANEL, w=2.0).move_to([-4.0, ys[2], 0])
        link = DashedLine(q.get_right(), recs[0].get_left(), dash_length=0.12, color=MUTED, stroke_width=2)
        strike = Line(q.get_left() + RIGHT * 0.1, q.get_right() + LEFT * 0.1, color=RED, stroke_width=4)
        skip = T("skipped", 20, RED).next_to(q, DOWN, buff=0.12)
        self.play(FadeIn(q, shift=RIGHT * 0.2), run_time=0.4)
        self.play(Create(link), run_time=0.5)
        self.play(Indicate(recs[0], color=RED, scale_factor=1.08), run_time=0.6)
        self.play(Create(strike), FadeIn(skip), FadeOut(link), run_time=0.4)
        self.b(2, 0.30)
        focus = recs[0].copy()
        others = VGroup(agents, q, strike, skip, bank, btitle, bline, *recs)
        self.play(others.animate.set_opacity(0.18), focus.animate.scale(1.5).move_to([-1.0, 0.6, 0]), run_time=0.9)
        ev = VGroup(T("evidence behind this verdict:", 24, MUTED), T("1 run, one random seed", 30, mono=True)).arrange(DOWN, buff=0.18).next_to(focus, DOWN, buff=0.55)
        self.play(FadeIn(ev[0]), run_time=0.4)
        self.play(FadeIn(ev[1], shift=UP * 0.1), run_time=0.5)
        self.b(2, 0.58)
        cap = caption("A failure verdict is a statistical claim from a small, noisy experiment.")
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.outro()


# ---------------------------------------------------------------- 3 noise
class S3Noise(Base):
    key = "noise"
    DELTA, N, BW, S, X0, Y0, STEP = 0.4, 120, 0.2, 1.75, -0.35, -1.5, 0.19

    def X(self, u):
        return self.X0 + u * self.S

    def construct(self):
        D, N, BW = self.DELTA, self.N, self.BW
        hd = header("One noisy run can fail a good idea")
        axis = Line([self.X(-3.1), self.Y0, 0], [self.X(3.6), self.Y0, 0], color=MUTED, stroke_width=2)
        axl = T("measured improvement →", 20, MUTED).next_to(axis, DOWN, buff=0.18).align_to(axis, RIGHT)
        zero = DashedLine([self.X(0), self.Y0 - 0.1, 0], [self.X(0), 1.9, 0], dash_length=0.1, color=MUTED, stroke_width=2)
        zl = T("no improvement", 20, MUTED).next_to(zero, UP, buff=0.1)
        tline = Line([self.X(D), self.Y0, 0], [self.X(D), 1.2, 0], color=TEAL, stroke_width=4)
        tl = T("true effect: slightly positive", 20, TEAL).next_to(tline, RIGHT, buff=0.12).align_to(tline, UP)
        idea = VGroup(Circle(0.22, color=TEAL, stroke_width=3, fill_color=TEAL_BG, fill_opacity=1)).move_to([self.X(D), 1.5, 0])
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), Create(axis), FadeIn(axl), run_time=0.9)
        self.play(Create(zero), FadeIn(zl), run_time=0.6)
        self.play(GrowFromEdge(tline, DOWN), FadeIn(tl, shift=RIGHT * 0.1), GrowFromCenter(idea), run_time=0.9)

        # beat 1: measurements rain down around the true effect
        us = D + norm.ppf((np.arange(N) + 0.5) / N)
        rng = np.random.default_rng(7)
        order = rng.permutation(N)
        counts, dots, targets = {}, [None] * N, [None] * N
        for j in order:
            k = int(np.floor(us[j] / BW))
            h = counts.get(k, 0)
            counts[k] = h + 1
            targets[j] = np.array([self.X((k + 0.5) * BW), self.Y0 + 0.11 + h * self.STEP, 0])
            dots[j] = Dot(idea.get_center(), radius=0.085, color=INK)
        self.b(1, 0.15)
        rain = [Succession(FadeIn(dots[j], run_time=0.05), dots[j].animate(run_time=0.55, rate_func=rush_into).move_to(targets[j]))
                for j in order]
        self.play(LaggedStart(*rain, lag_ratio=0.03), run_time=4.3)
        uu = np.linspace(-3.1, 3.6, 200)
        hy = lambda u: self.Y0 + 0.11 + N * BW * norm.pdf(u - D) * self.STEP - self.STEP / 2
        curve = VMobject().set_points_smoothly([[self.X(u), hy(u), 0] for u in uu]).set_stroke(INK, 2.5, opacity=0.9)
        self.play(Create(curve), run_time=0.8)

        # beat 2: a third land below zero -> convicted
        self.b(2)
        left = [j for j in range(N) if us[j] < 0]
        ul = np.linspace(-3.1, 0, 80)
        area = Polygon(*[[self.X(u), hy(u), 0] for u in ul], [self.X(0), self.Y0, 0], [self.X(-3.1), self.Y0, 0],
                       stroke_width=0, fill_color=RED, fill_opacity=0.16)
        self.add(area)
        self.bring_to_back(area)
        self.play(*[dots[j].animate.set_color(RED) for j in left],
                  *[dots[j].animate.set_color(TEAL) for j in range(N) if us[j] >= 0], FadeIn(area), run_time=0.8)
        pct = ValueTracker(0)
        num = always_redraw(lambda: T(f"{pct.get_value():.0f}%", 54, RED, w="BOLD").move_to([-4.6, 1.15, 0]))
        nl = T("of single runs land below zero", 22, RED).move_to([-4.6, 0.6, 0])
        fails = T("fails", 30, RED, w="SEMIBOLD").move_to([self.X(-1.6), -0.35, 0])
        passes = T("passes", 30, TEAL, w="SEMIBOLD").move_to([self.X(2.3), 0.35, 0])
        self.add(num)
        self.play(pct.animate.set_value(100 * len(left) / N), FadeIn(nl), FadeIn(fails), FadeIn(passes), run_time=1.3)
        self.b(2, 0.52)
        j0 = min(left, key=lambda j: abs(us[j] + 0.35) + 0.05 * targets[j][1])
        ring = Circle(0.2, color=INK, stroke_width=3).move_to(targets[j0])
        st = stamp("DEAD", 40).move_to([-4.9, -0.85, 0])
        arr = Arrow(targets[j0] + LEFT * 0.15 + UP * 0.1, st.get_right() + RIGHT * 0.1, buff=0.05, color=RED, stroke_width=3, max_tip_length_to_length_ratio=0.08)
        tag = T("the one run we did", 20, INK).next_to(ring, DOWN, buff=0.12)
        self.play(dots[j0].animate.scale(1.5), Create(ring), FadeIn(tag), run_time=0.5)
        self.play(GrowArrow(arr), run_time=0.45)
        self.play(FadeIn(st, scale=1.7, rate_func=rush_into), run_time=0.25)
        self.snd("thud", -0.05)

        # beat 3
        self.b(3)
        cap = caption("Marginally good ideas are exactly the ones\na single noisy test is most likely to convict.",
                      "P(convict | true effect δ) = Φ(−δ√n / σ)", y=-2.95, size=26)
        self.play(FadeIn(cap[0], shift=UP * 0.1), run_time=0.7)
        self.b(3, 0.55)
        self.play(FadeIn(cap[1]), run_time=0.6)
        self.outro()


# ---------------------------------------------------------------- 4 asymmetry
def mini_tree(root, depth=3, dx=1.35, spread=1.55):
    pts, edges = {(0, 0): np.array(root, float)}, []
    for d in range(1, depth + 1):
        n = 2 ** d
        for k in range(n):
            y = root[1] + spread * (1 - (2 * k + 1) / n)
            pts[(d, k)] = np.array([root[0] + dx * d, y, 0.0])
            edges.append(((d - 1, k // 2), (d, k)))
    return pts, edges


class S4Asym(Base):
    key = "asym"

    def construct(self):
        hd = header("The two errors are not symmetric")
        pl = card(6.5, 5.1, FAINT, PANEL).move_to([-3.45, -0.35, 0])
        pr = card(6.5, 5.1, FAINT, PANEL).move_to([3.45, -0.35, 0])
        tl = VGroup(T("Wrongly kept", 30, GOLD, w="SEMIBOLD"), T("a bad idea passes by chance", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        tr = VGroup(T("Wrongly killed", 30, RED, w="SEMIBOLD"), T("a good idea fails by chance", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        tl.move_to(pl.get_corner(UL) + [0.3, -0.3, 0], aligned_edge=UL)
        tr.move_to(pr.get_corner(UL) + [0.3, -0.3, 0], aligned_edge=UL)
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), FadeIn(pl), FadeIn(pr), run_time=0.8)
        self.play(FadeIn(tl, shift=RIGHT * 0.1), FadeIn(tr, shift=RIGHT * 0.1), run_time=0.6)

        # beat 1: kept bad idea -> built on -> descendants fail -> exposed
        self.b(1)
        P, E = mini_tree([-6.1, -0.6, 0])
        ln = {e: edge_curve(P[e[0]], P[e[1]]).set_stroke(MUTED, 2.2) for e in E}
        nd = {k: Dot(P[k], radius=0.1, color=MUTED) for k in P}
        nd[(0, 0)] = Dot(P[(0, 0)], radius=0.16, color=GOLD)
        kept = T("kept", 20, GOLD).next_to(nd[(0, 0)], DOWN, buff=0.14)
        self.play(GrowFromCenter(nd[(0, 0)]), FadeIn(kept), run_time=0.5)
        self.play(LaggedStart(*[AnimationGroup(*[Create(ln[e]) for e in E if e[1][0] == d], *[FadeIn(nd[k], scale=0.4) for k in P if k[0] == d])
                                for d in (1, 2, 3)], lag_ratio=0.7), run_time=2.0)
        self.b(1, 0.55)
        fails = [k for k in P if k[0] >= 2]
        xs = [cross(0.09, RED, 3.5).move_to(P[k] + RIGHT * 0.22 + UP * 0.12) for k in fails]
        self.play(LaggedStart(*[FadeIn(x, scale=1.8) for x in xs], lag_ratio=0.12), *[nd[k].animate.set_color(RED) for k in fails], run_time=1.5)
        ring = Circle(0.3, color=RED, stroke_width=3).move_to(P[(0, 0)])
        exp = T("exposed: its descendants keep failing", 20, INK).move_to(pl.get_bottom() + UP * 0.45)
        self.play(Create(ring), FadeIn(exp, shift=UP * 0.1), run_time=0.7)

        # beat 2: killed good idea -> never retried -> descendants never generated
        self.b(2, 0.05)
        Q, F = mini_tree([1.2, -0.6, 0])
        root = Dot(Q[(0, 0)], radius=0.16, color=TEAL)
        good = T("good idea", 20, TEAL).next_to(root, DOWN, buff=0.14)
        self.play(GrowFromCenter(root), FadeIn(good), run_time=0.5)
        st = stamp("DEAD", 26).next_to(root, UP, buff=0.22)
        self.b(2, 0.18)
        self.play(FadeIn(st, scale=1.7, rate_func=rush_into), root.animate.set_color(RED), good.animate.set_color(RED), run_time=0.25)
        self.snd("thud", -0.05)
        self.b(2, 0.45)
        ghost_e = [DashedVMobject(edge_curve(Q[e[0]], Q[e[1]]), num_dashes=10).set_stroke(TEAL, 2, opacity=0.55) for e in F]
        ghost_n = [Star(5, outer_radius=0.14, inner_radius=0.06, color=TEAL, fill_opacity=0.55, stroke_width=0).move_to(Q[k]) for k in Q if k[0] > 0]
        would = T("what it would have led to", 20, TEAL).move_to(pr.get_bottom() + UP * 0.45)
        self.play(LaggedStart(*[Create(g) for g in ghost_e], lag_ratio=0.05), LaggedStart(*[FadeIn(g, scale=0.5) for g in ghost_n], lag_ratio=0.05),
                  FadeIn(would), run_time=1.3)
        self.b(2, 0.75)
        never = T("never generated, never observed", 20, INK).move_to(would)
        self.play(*[FadeOut(g) for g in ghost_e + ghost_n], ReplacementTransform(would, never), run_time=1.4)

        self.b(3)
        cap = caption("False positives expose themselves. False negatives never do.", y=-3.4)
        cap[0].set_color_by_t2c({"expose themselves": GOLD, "never do": RED})
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.outro()


# ---------------------------------------------------------------- 5 measured
class S5Measured(Base):
    key = "measured"

    def stat(self, tracker, fmt, color, label, sub, y):
        num = always_redraw(lambda: T(fmt(tracker.get_value()), 56, color, w="BOLD").move_to([0.9, y + 0.35, 0], aligned_edge=LEFT))
        lab = VGroup(T(label, 22), T(sub, 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([0.9, y - 0.08, 0], aligned_edge=UL)
        return num, lab

    def construct(self):
        hd = header("How often are failure verdicts wrong?", "measured in real training loops and on a public benchmark")
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), run_time=0.8)

        # beat 1: 40 convictions, 7 wrongful (17.5%)
        self.b(1)
        sq = VGroup(*[RoundedRectangle(width=0.44, height=0.44, corner_radius=0.07, stroke_width=0, fill_color=FAINT, fill_opacity=1) for _ in range(40)])
        sq.arrange_in_grid(5, 8, buff=0.13).move_to([-3.6, 0.15, 0])
        gl = T("convictions in a live char-GPT training loop", 20, MUTED).next_to(sq, UP, buff=0.25)
        self.play(FadeIn(gl), LaggedStart(*[FadeIn(s, scale=0.5) for s in sq], lag_ratio=0.03), run_time=1.6)
        wrong = [3, 9, 14, 22, 27, 31, 38]
        v1 = ValueTracker(0)
        n1, l1 = self.stat(v1, lambda v: f"{v:.1f}%", RED, "of convictions were wrongful", "char-GPT training loop · theory: 19%", 1.45)
        self.b(1, 0.45)
        self.add(n1)
        self.play(*[sq[i].animate.set_fill(RED) for i in wrong], v1.animate.set_value(17.5), FadeIn(l1), run_time=1.6)
        leg = VGroup(RoundedRectangle(width=0.22, height=0.22, corner_radius=0.04, stroke_width=0, fill_color=RED, fill_opacity=1),
                     T("wrongful: the idea was genuinely good", 20, INK)).arrange(RIGHT, buff=0.15).next_to(sq, DOWN, buff=0.3)
        self.play(FadeIn(leg), run_time=0.5)

        # beat 2: near-miss verdicts 35-50%
        self.b(2, 0.1)
        v2 = ValueTracker(0)
        n2 = always_redraw(lambda: T(f"{35 * min(1, v2.get_value()):.0f}–{50 * min(1, v2.get_value()):.0f}%", 56, RED, w="BOLD").move_to([0.9, -0.2 + 0.35, 0], aligned_edge=LEFT))
        l2 = VGroup(T("of near-miss verdicts were wrong", 22), T("passed once, failed verification", 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.08).move_to([0.9, -0.2 - 0.08, 0], aligned_edge=UL)
        track = Line([4.6, 0.15, 0], [6.6, 0.15, 0], color=FAINT, stroke_width=8)
        band = Line([4.6 + 2 * 0.35, 0.15, 0], [4.6 + 2 * 0.50, 0.15, 0], color=RED, stroke_width=8)
        self.add(n2)
        self.play(v2.animate.set_value(1), FadeIn(l2), FadeIn(track), run_time=1.4)
        self.play(Create(band), run_time=0.6)

        # beat 3: FCNet replay, conviction-vs-effect curve
        self.b(3)
        self.play(FadeOut(VGroup(sq, gl, leg)), run_time=0.5)
        ox, oy, W, H = -6.0, -2.35, 5.2, 3.6
        P = lambda d, p: np.array([ox + W * d / 3, oy + H * p / 0.5, 0])
        ax = VGroup(Line(P(0, 0), P(3, 0), color=MUTED, stroke_width=2), Line(P(0, 0), P(0, 0.5), color=MUTED, stroke_width=2))
        ticks = VGroup(*[T(s, 18, MUTED).next_to(P(d, 0), DOWN, buff=0.12) for d, s in ((0, "0"), (1, "1σ"), (2, "2σ"), (3, "3σ"))],
                       *[T(s, 18, MUTED).next_to(P(0, p), LEFT, buff=0.12) for p, s in ((0.25, "25%"), (0.5, "50%"))])
        xl = T("true improvement of a genuinely good idea", 20, MUTED).next_to(ax, DOWN, buff=0.5)
        yl = T("chance one run convicts it", 20, MUTED).next_to(P(0, 0.5), UP, buff=0.18).align_to(ax, LEFT)
        dd = np.linspace(0, 3, 120)
        cv = VMobject().set_points_smoothly([P(d, norm.cdf(-d)) for d in dd]).set_stroke(INK, 3)
        hot = Polygon(*[P(d, norm.cdf(-d)) for d in np.linspace(0, 0.5, 30)], P(0.5, 0), P(0, 0), stroke_width=0, fill_color=RED, fill_opacity=0.25)
        self.play(Create(ax), FadeIn(ticks), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(Create(cv), run_time=1.3)
        v3 = ValueTracker(0)
        n3, l3 = self.stat(v3, lambda v: f"{v:,.0f}", INK, "convictions replayed on FCNet", "public benchmark · same shape as the theory", -1.85)
        self.add(n3)
        self.play(v3.animate.set_value(122817), FadeIn(l3), run_time=1.6, rate_func=smooth)
        self.b(3, 0.55)
        pt = Dot(P(0.125, 0.44), radius=0.11, color=RED)
        ptl = VGroup(T("44% measured, 45% predicted", 20, INK), T("good configs under 0.25σ", 18, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.06).next_to(pt, RIGHT, buff=0.25).shift(UP * 0.05)
        self.play(FadeIn(hot), GrowFromCenter(pt), FadeIn(ptl, shift=RIGHT * 0.1), run_time=0.9)
        self.snd("tick", -0.6)
        self.outro()


# ---------------------------------------------------------------- 6 LLM agents
class S6LLM(Base):
    key = "llm"

    def construct(self):
        hd = header("Do LLM agents look past the label?", "12 deployed models from 9 families")
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), run_time=0.8)

        # beat 1: same record, two labels
        self.b(1)
        lines = VGroup(T("record #R-114", 20, MUTED, mono=True), T("1 run: 0.12% worse than baseline", 24, mono=True),
                       T("seed noise: 0.15%", 24, mono=True)).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        box = card(lines.width + 0.9, 2.6, MUTED, PANEL).move_to([0, 0.2, 0])
        lines.move_to(box.get_corner(UL) + [0.45, -0.32, 0], aligned_edge=UL)
        slab = T("status:", 24, mono=True).next_to(lines, DOWN, aligned_edge=LEFT, buff=0.22)
        dead = T("DEAD", 24, RED, w="BOLD", mono=True).next_to(slab, RIGHT, buff=0.25)
        inc = T("INCONCLUSIVE", 24, TEAL, w="BOLD", mono=True).next_to(slab, RIGHT, buff=0.25)
        rec = VGroup(box, lines, slab)
        self.play(FadeIn(rec, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(dead), run_time=0.3)
        self.b(1, 0.62)
        self.play(FadeOut(dead, shift=UP * 0.2), FadeIn(inc, shift=UP * 0.2), run_time=0.45)

        # beat 2: stated beliefs, 32.5% vs 8.5%
        self.b(2)
        self.play(VGroup(rec, inc).animate.scale(0.82).move_to([-3.55, 0.9, 0]), run_time=0.8)
        base_y, k = -2.35, 0.105
        bx = {"INCONCLUSIVE": (1.3, TEAL, 32.5), "DEAD": (3.9, RED, 8.5)}
        bars, vals, labs = {}, {}, {}
        for name, (x, c, v) in bx.items():
            bars[name] = RoundedRectangle(width=1.4, height=v * k, corner_radius=0.06, stroke_width=0, fill_color=c, fill_opacity=1).move_to([x, base_y + v * k / 2, 0])
            vals[name] = T(f"{v}%", 34, INK, w="BOLD").next_to(bars[name], UP, buff=0.14)
            labs[name] = T(name, 22, c, w="SEMIBOLD", mono=True).next_to([x, base_y, 0], DOWN, buff=0.18)
        baseline = Line([0.2, base_y, 0], [5.0, base_y, 0], color=MUTED, stroke_width=2)
        bcap = T("stated chance the idea is genuinely better  ·  3 Claude models", 20, MUTED).next_to(baseline, DOWN, buff=0.65)
        self.play(Create(baseline), FadeIn(labs["INCONCLUSIVE"]), FadeIn(bcap), run_time=0.6)
        self.play(GrowFromEdge(bars["INCONCLUSIVE"], DOWN), FadeIn(vals["INCONCLUSIVE"], shift=UP * 0.2), run_time=1.0)
        self.b(2, 0.78)
        dead2 = T("DEAD", 24 * 0.82, RED, w="BOLD", mono=True).move_to(inc, aligned_edge=LEFT)
        self.play(FadeOut(inc, shift=DOWN * 0.15), FadeIn(dead2, shift=DOWN * 0.15), FadeIn(labs["DEAD"]), run_time=0.4)
        self.play(GrowFromEdge(bars["DEAD"], DOWN), FadeIn(vals["DEAD"], shift=UP * 0.2), run_time=0.8)

        # beat 3: choices: 0/94 revisits; 9/9 families
        self.b(3)
        chart = VGroup(baseline, bcap, *bars.values(), *vals.values(), *labs.values())
        self.play(FadeOut(VGroup(rec, dead2)), chart.animate.scale(0.85).move_to([-3.4, -0.35, 0]), run_time=0.9)
        n94 = T("0 / 94", 60, RED, w="BOLD").move_to([0.7, 1.55, 0], aligned_edge=LEFT)
        l94 = T("dead-marked ideas revisited when agents\nchose their next experiment", 22, line_spacing=0.9).next_to(n94, DOWN, aligned_edge=LEFT, buff=0.18)
        self.play(FadeIn(n94, scale=1.2), FadeIn(l94), run_time=0.8)
        self.b(3, 0.5)
        n9 = T("9 / 9", 60, RED, w="BOLD").move_to([0.7, -0.75, 0], aligned_edge=LEFT)
        l9 = T("families picked the a-priori best idea\nless often once it was labeled DEAD", 22, line_spacing=0.9).next_to(n9, DOWN, aligned_edge=LEFT, buff=0.18)
        fam = VGroup(*[VGroup(Circle(0.2, color=MUTED, stroke_width=2.5, fill_color=PANEL, fill_opacity=1),
                              Arrow(UP * 0.13, DOWN * 0.15, buff=0, color=RED, stroke_width=5, max_tip_length_to_length_ratio=0.5))
                       for _ in range(9)]).arrange(RIGHT, buff=0.14).next_to(l9, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(FadeIn(n9, scale=1.2), FadeIn(l9), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(f, shift=DOWN * 0.15) for f in fam], lag_ratio=0.15), run_time=1.2)

        self.b(4)
        cap = caption("The models can price the evidence. The label overrides it.", y=-3.45)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.outro()


# ---------------------------------------------------------------- 7 fix
class S7Fix(Base):
    key = "fix"

    def construct(self):
        hd = header("The fix: records that carry their evidence")
        self.b(0)
        bin_box = card(3.6, 1.6, RED, RED_BG).move_to([0, 1.0, 0])
        bin_t = VGroup(T("binary record", 20, MUTED), T("DEAD", 48, RED, w="BOLD")).arrange(DOWN, buff=0.1).move_to(bin_box)
        binary = VGroup(bin_box, bin_t)
        self.play(FadeIn(hd, shift=DOWN * 0.15), FadeIn(binary, scale=0.9), run_time=0.9)

        # beat 1: the record gains its evidence
        self.b(1, 0.12)
        self.play(binary.animate.scale(0.8).move_to([-4.75, 1.0, 0]), run_time=0.8)
        arr = Arrow([-3.25, 1.0, 0], [-2.3, 1.0, 0], buff=0, color=MUTED, stroke_width=3, max_tip_length_to_length_ratio=0.25)
        g = card(7.6, 3.0, TEAL, TEAL_BG).move_to([1.85, 0.95, 0])
        gt = T("evidence-graded record", 20, MUTED).move_to(g.get_corner(UL) + [0.35, -0.3, 0], aligned_edge=UL)
        self.play(GrowArrow(arr), FadeIn(g), FadeIn(gt), run_time=0.7)
        L0 = g.get_corner(UL) + [0.35, -0.95, 0]
        def field(k, v, row):
            a = T(f"{k:<9}", 26, MUTED, mono=True).move_to(L0 + DOWN * 0.5 * row, aligned_edge=LEFT)
            b = T(v, 26, INK, mono=True).move_to(L0 + DOWN * 0.5 * row + RIGHT * 2.0, aligned_edge=LEFT)
            return a, b
        runs_k, runs_v = field("runs", "1", 0)
        eff_k, eff_v = field("effect", "0.12% worse", 1)
        noi_k, noi_v = field("noise σ", "0.15%", 2)
        for f, (a, b2) in zip((0.55, 0.72, 0.88), ((runs_k, runs_v), (eff_k, eff_v), (noi_k, noi_v))):
            self.b(1, f)
            self.play(FadeIn(a, shift=RIGHT * 0.1), FadeIn(b2, shift=RIGHT * 0.1), run_time=0.4)

        # beat 2: P(dead) = 0.79 -> OPEN
        self.b(2)
        gx0, gx1, gy = -4.5, 4.5, -1.55
        GX = lambda p: gx0 + (gx1 - gx0) * p
        track = RoundedRectangle(width=gx1 - gx0, height=0.26, corner_radius=0.13, stroke_width=0, fill_color=FAINT, fill_opacity=1).move_to([0, gy, 0])
        thr = Line([GX(0.8), gy - 0.3, 0], [GX(0.8), gy + 0.3, 0], color=INK, stroke_width=3)
        thl = T("lock threshold θ = 0.8", 20, INK).next_to(thr, UP, buff=0.1)
        e0, e1 = T("0", 18, MUTED).next_to(track, DOWN, buff=0.12).align_to(track, LEFT), T("1", 18, MUTED).next_to(track, DOWN, buff=0.12).align_to(track, RIGHT)
        p = ValueTracker(0.001)
        fill = always_redraw(lambda: RoundedRectangle(width=max(0.26, (gx1 - gx0) * p.get_value()), height=0.26, corner_radius=0.13, stroke_width=0,
                                                      fill_color=RED if p.get_value() > 0.8 else TEAL, fill_opacity=1).move_to([gx0, gy, 0], aligned_edge=LEFT))
        rd = always_redraw(lambda: T(f"P(dead | evidence) = {p.get_value():.2f}", 28, INK, w="SEMIBOLD").move_to([gx0, gy + 0.55, 0], aligned_edge=LEFT))
        fz = T("z = 0.12 / (0.15 / √1) = 0.80   →   P(dead) = Φ(z)", 22, MUTED).move_to([0, gy - 0.75, 0])
        self.play(FadeIn(track), FadeIn(e0), FadeIn(e1), Create(thr), FadeIn(thl), run_time=0.8)
        self.add(fill, rd)
        self.b(2, 0.33)
        self.play(p.animate.set_value(0.79), FadeIn(fz), run_time=1.6, rate_func=smooth)
        self.b(2, 0.62)
        chip = stamp("OPEN", 30, TEAL).move_to(g.get_corner(DR) + [-1.25, 1.0, 0])
        ra = T("retry allowed", 20, TEAL).next_to(chip, DOWN, buff=0.08)
        self.play(Indicate(thr, color=TEAL), run_time=0.6)
        self.play(FadeIn(chip, scale=1.4), FadeIn(ra), run_time=0.4)
        self.snd("chime", -0.3)

        # beat 3: five runs -> 0.96 -> CLOSED
        self.b(3)
        runs5 = T("5", 26, INK, mono=True).move_to(runs_v, aligned_edge=LEFT)
        eff5 = T("0.12% worse (mean)", 26, INK, mono=True).move_to(eff_v, aligned_edge=LEFT)
        fz5 = T("z = 0.12 / (0.15 / √5) = 1.79   →   P(dead) = Φ(z)", 22, MUTED).move_to(fz)
        self.play(FadeOut(runs_v, shift=UP * 0.2), FadeIn(runs5, shift=UP * 0.2), FadeOut(eff_v), FadeIn(eff5), ReplacementTransform(fz, fz5), run_time=0.6)
        self.play(p.animate.set_value(0.963), run_time=1.3)
        chip2 = stamp("CLOSED", 30, RED).move_to(chip)
        ra2 = T("lock earned", 20, RED).next_to(chip2, DOWN, buff=0.08)
        self.b(3, 0.62)
        self.play(FadeOut(chip), FadeIn(chip2, scale=1.4), ReplacementTransform(ra, ra2), g.animate.set_stroke(RED), run_time=0.4)
        self.snd("lock", -0.25)

        self.b(4)
        cap = caption("A standard confidence rule. Shared failure banks just don't implement it.", y=-3.45)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.outro()


# ---------------------------------------------------------------- 8 result
class S8Result(Base):
    key = "result"
    Y = staticmethod(lambda v: -2.75 + (v - 35) * 0.125)

    def construct(self):
        Y = self.Y
        hd = header("Does it matter? A closed research loop", "algorithmic proposer  ·  real training runs  ·  8 independent loops per memory rule")
        self.b(0)
        self.play(FadeIn(hd, shift=DOWN * 0.15), run_time=0.8)
        xl, xr = -6.0, 1.4
        grid = VGroup(*[Line([xl, Y(v), 0], [xr, Y(v), 0], color=FAINT, stroke_width=1.5) for v in (40, 50, 60, 70)])
        gl = VGroup(*[T(str(v), 18, MUTED).next_to([xl, Y(v), 0], LEFT, buff=0.12) for v in (40, 50, 60, 70)])
        yl = T("truth-validated discoveries per loop", 20, MUTED).move_to([xl - 0.45, Y(70) + 0.42, 0], aligned_edge=LEFT)
        cats = [("nomem", "no memory", MUTED), ("binary", "binary DEAD", RED), ("parole", "parole", MUTED), ("graded", "evidence-graded", TEAL)]
        xs = [-5.4, -3.6, -1.8, 0.0]
        labs = VGroup(*[T(n, 20, c if k in ("binary", "graded") else INK, w="SEMIBOLD" if k in ("binary", "graded") else NORMAL).move_to([x, Y(35) - 0.3, 0])
                        for (k, n, c), x in zip(cats, xs)])
        self.play(Create(grid), FadeIn(gl), FadeIn(yl), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in labs], lag_ratio=0.2), run_time=1.0)
        jit = [-0.3, 0.17, -0.09, 0.3, -0.21, 0.04, 0.24, -0.15]

        def column(i):
            k, _, c = cats[i]
            vs = REPS[k]
            col = TEAL if k == "graded" else (RED if k == "binary" else MUTED)
            ds = [Dot([xs[i] + jit[r], Y(v), 0], radius=0.085, color=col) for r, v in enumerate(vs)]
            m = float(np.mean(vs))
            ml = Line([xs[i] - 0.42, Y(m), 0], [xs[i] + 0.42, Y(m), 0], color=INK, stroke_width=4)
            mt = T(f"{m:.1f}", 22, INK, w="SEMIBOLD").next_to(ml, RIGHT, buff=0.08)
            return ds, ml, mt, m

        # beat 1: the three baselines
        self.b(1, 0.05)
        cols = [column(i) for i in range(4)]
        for i in range(3):
            ds, ml, mt, _ = cols[i]
            self.play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.6) for d in ds], lag_ratio=0.12), run_time=0.9)
            self.play(Create(ml), FadeIn(mt), run_time=0.4)
        # beat 2: graded
        self.b(2)
        ds, ml, mt, m = cols[3]
        self.play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.6) for d in ds], lag_ratio=0.12), run_time=1.0)
        self.play(Create(ml), FadeIn(mt), run_time=0.4)
        self.snd("chime", -0.2)
        mb = cols[1][3]
        self.b(2, 0.3)
        big = T("+30–32%", 64, TEAL, w="BOLD").move_to([1.85, 1.45, 0], aligned_edge=LEFT)
        bl = T("more truth-validated discoveries\nthan each alternative rule", 22, line_spacing=0.9).next_to(big, DOWN, aligned_edge=LEFT, buff=0.15)
        self.play(FadeIn(big, scale=1.15), FadeIn(bl), run_time=0.8)
        self.b(2, 0.5)
        da = DoubleArrow([1.3, Y(mb), 0], [1.3, Y(m), 0], buff=0, color=TEAL, stroke_width=3, tip_length=0.16)
        dg = DashedLine([xs[3] - 0.5, Y(mb), 0], [1.3, Y(mb), 0], dash_length=0.08, color=MUTED, stroke_width=1.5)
        dl = T("+13.9", 22, TEAL, w="SEMIBOLD").next_to(da, LEFT, buff=0.1)
        ci = T("difference vs. binary: 13.9\n95% CI [9.7, 18.1]", 20, MUTED, line_spacing=0.9).next_to(bl, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(Create(dg), GrowFromCenter(da), FadeIn(dl), run_time=0.8)
        self.play(FadeIn(ci), run_time=0.6)

        # beat 3: where it does not hold
        self.b(3, 0.02)
        wc = card(4.85, 2.05, FAINT, PANEL).move_to([4.27, -1.95, 0])
        wt = T("Where it does not hold", 22, INK, w="SEMIBOLD").move_to(wc.get_corner(UL) + [0.25, -0.25, 0], aligned_edge=UL)
        w1 = T("• low-noise, short-horizon loop:\n   binary edges ahead (18.0 vs 16.0)", 19, line_spacing=0.85).next_to(wt, DOWN, aligned_edge=LEFT, buff=0.18)
        w2 = T("• LLM proposers: ordering depends\n   on the proposer", 19, line_spacing=0.85).next_to(w1, DOWN, aligned_edge=LEFT, buff=0.14)
        self.play(FadeIn(wc), FadeIn(wt), run_time=0.6)
        self.b(3, 0.25)
        self.play(FadeIn(w1, shift=RIGHT * 0.1), run_time=0.5)
        self.b(3, 0.62)
        self.play(FadeIn(w2, shift=RIGHT * 0.1), run_time=0.5)
        self.outro()


# ---------------------------------------------------------------- 9 end
class S9End(Base):
    key = "end"

    def construct(self):
        nodes, curves, dots, grow = build_tree(0.2, run_time=4.0)
        back = soft_backdrop(13.0, 6.0)
        l1 = T("Records that carry their evidence.", 54, INK, w="BOLD")
        l2 = T("Locks that require it.", 54, TEAL, w="BOLD")
        g = VGroup(l1, l2).arrange(DOWN, buff=0.2).move_to(UP * 0.9)
        url = T("github.com/Benjy-byj/failure-bank-calibration", 28, INK, mono=True).next_to(g, DOWN, buff=0.75)
        sub = T("code · logs · cached runs · preregistrations", 20, MUTED).next_to(url, DOWN, buff=0.15)
        auth = T("Yingjie Bai · Weiming Zhi  —  The University of Sydney", 20, MUTED).to_edge(DOWN, buff=0.6)
        self.add(back)
        self.play(AnimationGroup(grow, Succession(Wait(0.3), FadeIn(l1, shift=UP * 0.2, run_time=0.9)),
                                 Succession(Wait(1.6), FadeIn(l2, shift=UP * 0.2, run_time=0.9))))
        self.b(1)
        self.play(FadeIn(url, shift=UP * 0.1), FadeIn(sub), FadeIn(auth), run_time=0.8)
        self.outro()


SCENES = ["S1Title", "S2Bank", "S3Noise", "S4Asym", "S5Measured", "S6LLM", "S7Fix", "S8Result", "S9End"]
