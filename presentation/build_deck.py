"""Build an editable submission deck and a PDF proof from one layout.

No analytics are fitted here. Every rank, rating and match example comes from
the frozen dashboard export. Supplied photos are cropped by native viewports;
the original files are never changed.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard/public/reports"
CHECKS = ROOT / "reports/presentation_2026-11-18"
PLAYERS = json.loads((ROOT / "dashboard/content/generated/players.json").read_text())
ASSETS = json.loads((ROOT / "dashboard/content/player-assets.json").read_text())
RELEASE = json.loads((ROOT / "dashboard/content/generated/release.json").read_text())
BAT = sorted((p for p in PLAYERS if p["selected"] and p["role"] == "batting"), key=lambda p: p["rank"])
BOWL = sorted((p for p in PLAYERS if p["selected"] and p["role"] == "bowling"), key=lambda p: p["rank"])
NAVY, PINK, BLUSH, BORDER = "15243C", "BB1D64", "FFF6FA", "F0CDDC"
MUTED, GREEN, AMBER, WHITE = "526175", "176345", "86520D", "FFFFFF"
URL = "https://your-dashboard.vercel.app"
W, H = 13.333333, 7.5
CASE_IDS = {
    "6396": (50135, 30069), "1699": (31243, 19716), "3125": (20238, 31266),
    "2756": (31260, 40711), "23311": (45391, 36199), "1318": (40746, 31240),
    "6726": (30075, 50375), "7897": (50351, 45392), "3647": (31260, 31246),
    "4391": (28066, 25161), "781": (50372, 20199), "2933": (45510, 48591),
    "4373": (44265, 31257), "5837": (38843, 37278), "6354": (50599, 29817),
    "35318": (50943, 50357), "6256": (45496, 30058), "7327": (31280, 31258),
    "6284": (50372, 50126), "23": (20192, 20185),
}
TEAM_LABELS = {
    'Chennai Super Kings':'CSK', 'Delhi Capitals':'DC', 'Gujarat Titans':'GT',
    'Kolkata Knight Riders':'KKR', 'Lucknow Super Giants':'LSG', 'Mumbai Indians':'MI',
    'Punjab Kings':'PBKS', 'Rajasthan Royals':'RR', 'Royal Challengers Bengaluru':'RCB',
    'Sunrisers Hyderabad':'SRH', 'West Indies':'WI', 'New Zealand':'NZ',
    'United Arab Emirates':'UAE', 'Bangladesh':'BAN', 'Pakistan':'PAK', 'India':'IND',
    'England':'ENG',
}


class Deck:
    def __init__(self, dashboard_url: str):
        self.url = dashboard_url
        self.placeholder = dashboard_url == URL
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(W), Inches(H)
        self.prs.core_properties.title = "Pressure Index | SupeRR Selector Season 2"
        self.prs.core_properties.subject = "Round 1: twenty pressure-performance selections and evidence"
        self.prs.core_properties.author = "Independent SupeRR Selector submission"
        self.prs.core_properties.keywords = "Rajasthan Royals, pressure, audited evidence, cricket"
        OUT.mkdir(parents=True, exist_ok=True)
        CHECKS.mkdir(parents=True, exist_ok=True)
        font_root = Path("/usr/share/fonts/truetype/msttcorefonts")
        for name, file in [("Arial", "Arial.ttf"), ("ArialBold", "Arial_Bold.ttf")]:
            pdfmetrics.registerFont(TTFont(name, str(font_root / file)))
        self.pdf = canvas.Canvas(str(OUT / "pressure-index-slides.pdf"), pagesize=(W * 72, H * 72))
        self.pdf.setTitle("Pressure Index | submission slides")
        self.audit = []
        self.slide = None
        self.page = 0
        self.images = set()
        self.overflows = []

    def boxcheck(self, x, y, w, h, kind):
        assert x >= -0.001 and y >= -0.001 and x + w <= W + .001 and y + h <= H + .001, (self.page, kind, x, y, w, h)

    def rect(self, x, y, w, h, fill=BLUSH, stroke=None):
        self.boxcheck(x, y, w, h, "rectangle")
        shape = self.slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
        if stroke:
            shape.line.color.rgb = RGBColor.from_string(stroke)
            shape.line.width = Pt(.7)
        else:
            shape.line.fill.background()
        self.pdf.setFillColor(HexColor("#" + fill))
        if stroke:
            self.pdf.setStrokeColor(HexColor("#" + stroke))
            self.pdf.setLineWidth(.7)
        self.pdf.rect(x * 72, (H - y - h) * 72, w * 72, h * 72, fill=1, stroke=int(bool(stroke)))

    def line(self, x, y, w, color=BORDER):
        self.rect(x, y, w, .012, color)

    def text(self, x, y, w, h, value, size=18, bold=False, color=NAVY, link=None):
        self.boxcheck(x, y, w, h, "text")
        font = "ArialBold" if bold else "Arial"
        lines = []
        for para in str(value).split("\n"):
            current = ""
            for word in para.split():
                attempt = (current + " " + word).strip()
                if pdfmetrics.stringWidth(attempt, font, size) > w * 72 - 2 and current:
                    lines.append(current)
                    current = word
                else:
                    current = attempt
                assert pdfmetrics.stringWidth(current, font, size) <= w * 72, (self.page, current, w, size)
            lines.append(current)
        leading = size * 1.16
        if len(lines) * leading > h * 72 + 1:
            self.overflows.append((self.page, str(value)[:100], len(lines), h, size))
        tb = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for i, content in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_before = p.space_after = Pt(0)
            p.line_spacing = Pt(leading)
            r = p.add_run()
            r.text = content
            r.font.name = "Arial"
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = RGBColor.from_string(color)
            if link:
                r.hyperlink.address = link
        self.pdf.setFont(font, size)
        self.pdf.setFillColor(HexColor("#" + color))
        for i, content in enumerate(lines):
            self.pdf.drawString(x * 72, (H - y) * 72 - size - i * leading, content)
        if link:
            self.pdf.linkURL(link, (x * 72, (H-y-h)*72, (x+w)*72, (H-y)*72), relative=0)
        self.audit.append({"slide": self.page, "text": str(value), "lines": len(lines), "size": size})

    def photo(self, player, x, y, w, h, head=False):
        self.boxcheck(x, y, w, h, "photo")
        a = ASSETS[player["id"]]
        c = a["crop"]
        cx, cy, cw, ch = c["x"], c["y"], c["width"], c["height"]
        if head:
            side = ch * .48
            cx, cy, cw, ch = cx + cw/2-side/2, cy + ch*.02, side, side
        assert math.isclose(w/h, cw/ch, rel_tol=.001)
        t, r, b, l = a["trim"]
        left, top = max(cx, l), max(cy, t)
        right, bottom = min(cx+cw, a["width"]-r), min(cy+ch, a["height"]-b)
        dx, dy = x+(left-cx)/cw*w, y+(top-cy)/ch*h
        dw, dh = (right-left)/cw*w, (bottom-top)/ch*h
        path = ROOT / "dashboard/public" / a["src"].lstrip("/")
        self.rect(x, y, w, h, WHITE)
        pic = self.slide.shapes.add_picture(str(path), Inches(dx), Inches(dy), width=Inches(dw), height=Inches(dh))
        pic.crop_left, pic.crop_right = left/a["width"], 1-right/a["width"]
        pic.crop_top, pic.crop_bottom = top/a["height"], 1-bottom/a["height"]
        self.pdf.saveState()
        clip = self.pdf.beginPath()
        clip.rect(dx*72, (H-dy-dh)*72, dw*72, dh*72)
        self.pdf.clipPath(clip, stroke=0)
        self.pdf.drawImage(str(path), (x-cx/cw*w)*72,
                           (H-y-(a["height"]-cy)/ch*h)*72,
                           width=a["width"]/cw*w*72, height=a["height"]/ch*h*72, mask="auto")
        self.pdf.restoreState()
        self.images.add(player["id"])

    def new(self, section, title, subtitle=None, notes="", portrait=False):
        if self.slide is not None:
            self.pdf.showPage()
        self.page += 1
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.slide.notes_slide.notes_text_frame.text = notes
        self.rect(0, 0, W, H, WHITE)
        self.rect(0, 0, W, .07, PINK)
        self.text(.5, .3, 11.8, .25, "PRESSURE INDEX  /  " + section.upper(), 10, True, PINK)
        self.text(.5, .78, 12.2, .65, title, 30, True)
        if subtitle:
            self.text(.52, 1.5, 12.1, .6, subtitle, 15, color=MUTED)
        self.line(.5, 7.02, 12.3)
        foot = "Independent analysis  |  Data cutoff: 1 Nov 2026"
        if portrait:
            foot += "  |  AI-generated RR concept portraits"
        self.text(.5, 7.16, 11.8, .2, foot, 9, color=MUTED)
        self.text(12.2, 7.12, .6, .25, f"{self.page:02}", 11, True, PINK)

    def card(self, x, y, w, h, kicker, heading, body, body_size=18):
        self.rect(x, y, w, h, BLUSH, BORDER)
        self.text(x+.22, y+.2, w-.44, .3, kicker.upper(), 11, True, PINK)
        self.text(x+.22, y+.65, w-.44, .8, heading, 24, True)
        self.text(x+.22, y+1.62, w-.44, h-1.83, body, body_size, color=MUTED)

    def ranked_table(self, players, role):
        self.new("The selections", f"Ten {role}. The frozen order.",
                 "Ranked by the 10th bootstrap percentile (P10); higher is better. Recent status describes eligibility, not form.",
                 notes="Source: dashboard/content/generated/players.json; release pressure-index-2026-11-01-v1. Match count is retained pressure exposure; Shreyas Iyer has 42 peer-supported pressure matches from 43 retained. P10 is an index quantile, not a probability. No availability or auction-price filter.", portrait=True)
        xs = [.55, 1.02, 1.58, 6.7, 8.15, 9.45, 10.8]
        for x, width, label in zip(xs, [.4,.5,4.9,1.3,1.15,1.2,1.9], ["#", "", "PLAYER / OBSERVED TASK", "P10 INDEX", "MATCHES", "PRESSURE", "2026 STATUS"]):
            if label:
                self.text(x, 2.17, width, .23, label, 10, True, MUTED)
        for i, p in enumerate(players):
            y = 2.52 + i*.416
            if i % 2 == 0:
                self.rect(.5, y-.02, 12.3, .415, BLUSH)
            self.text(xs[0], y+.035, .4, .28, str(p["rank"]), 13, True, PINK)
            self.photo(p, xs[1], y, .36, .36, head=True)
            self.text(xs[2], y+.005, 4.9, .24, p["name"], 13, True)
            self.text(xs[2], y+.225, 4.9, .15, p["task"], 9, color=MUTED)
            self.text(xs[3], y+.04, 1.3, .28, f"{p['rating']['low']:+.4f}", 13, True)
            self.text(xs[4], y+.04, 1.15, .28, str(int(p["exposure"]["pressureMatches"])), 13)
            self.text(xs[5], y+.04, 1.2, .28, str(int(p["exposure"]["pressureEvents"])), 13)
            status = p["recent"]["status"]
            self.text(xs[6], y+.04, 1.9, .28, status.upper() if status!='no_retained_pressure' else 'NONE RETAINED', 11, True, GREEN if status=="adequate" else AMBER)
        self.text(.55, 6.78, 12.1, .18, "Pressure = retained analytical opportunities. Adequate = passes all standalone-year gates. Exact dropdown aliases still require final mapping.", 9, color=MUTED)

    def dossiers(self, players, role):
        for i in range(0, 10, 2):
            pair = players[i:i+2]
            notes = ["All statistics below describe retained pressure segments, not complete innings or spells. Dismissals are bowler-attributable striker dismissals; bowling runs exclude byes, leg-byes and penalties. Exact source records follow."]
            self.new(f"{role} evidence  /  {i+1:02}–{i+2:02}",
                     "The role. The evidence. The challenge.", portrait=True)
            self.text(.52,1.45,12.1,.2,"RR role options from observed workload. Each card pairs a selection case with concrete counterevidence.",11,color=MUTED)
            for col, p in enumerate(pair):
                x, y, width = .5+col*6.25, 1.68, 6.05
                self.rect(x,y,width,5.15,BLUSH,BORDER)
                self.photo(p,x+.2,y+.2,1.32,1.65)
                self.text(x+1.72,y+.19,4.1,.27,f"#{p['rank']:02}  /  {p['task']}",11,True,PINK)
                self.text(x+1.72,y+.62,4.08,.84,p["name"],23,True)
                self.text(x+1.72,y+1.5,4.05,.3,f"P10 {p['rating']['low']:+.4f}  |  {int(p['exposure']['pressureMatches'])} matches",15,True)
                self.text(x+.22,y+1.99,5.6,.4,
                          f"{int(p['exposure']['pressureEvents'])} pressure opportunities  /  2026: {p['recent']['status'].replace('no_retained_pressure', 'none retained')}",12,True,MUTED)
                self.text(x+.22,y+2.47,5.6,.79,p["editorial"]["why"],16)
                self.text(x+.22,y+3.33,5.6,.71,"Review: "+p["editorial"]["caution"],14,color=AMBER)
                good, bad = (next(c for c in p["cases"] if c["match_id"]==mid) for mid in CASE_IDS[p["id"]])
                for j, c in enumerate((good,bad)):
                    label = "SUPPORT" if j==0 else "CHALLENGE"
                    result = (f"{c['runs']} runs / {c['opportunities']} opp; {c['wickets']} dismissal(s)" if role=="Batting" else
                              f"{c['runs']} conceded / {c['opportunities']} attempts; {c['wickets']} wicket(s)")
                    team = TEAM_LABELS.get(c['opposition'],c['opposition'])
                    self.text(x+.22,y+4.18+j*.41,5.6,.35,f"{label}: {result} | {team}",11.5,True,GREEN if j==0 else AMBER)
                    notes.append(f"{p['name']} {label}: {json.dumps(c)}")
                notes.append(f"{p['name']} RR contribution: {p['editorial']['contribution']} Review: {p['editorial']['review']}")
            self.slide.notes_slide.notes_text_frame.text = "\n\n".join(notes)
            self.text(.53,6.88,12.2,.15,"Examples are pressure segments, not complete innings/spells. Opponents, dates and source match IDs are recorded in the speaker notes.",9,color=MUTED)

    def finish(self):
        self.pdf.save()
        assert not self.overflows, self.overflows
        self.prs.save(str(OUT/"pressure-index-submission.pptx"))
        ppt = OUT/"pressure-index-submission.pptx"
        assert ppt.stat().st_size < 50*1024**2
        assert self.images == {p["id"] for p in BAT+BOWL}
        assert RELEASE['id']=='pressure-index-2026-11-01-v1'
        assert len(BAT)==len(BOWL)==10
        assert sum(p['recent']['status']=='adequate' for p in BAT+BOWL)==7
        with ZipFile(ppt) as z:
            assert z.testzip() is None
            ns = {"a":"http://schemas.openxmlformats.org/drawingml/2006/main"}
            slides = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+.xml",n)),key=lambda n:int(re.search(r"(\d+)\.xml",n).group(1)))
            texts = [" ".join(ET.fromstring(z.read(n)).itertext()) for n in slides]
            assert len(slides) == self.page
            for n, players in [(8,BAT),(9,BOWL)]:
                plain = " ".join(t.text or "" for t in ET.fromstring(z.read(slides[n-1])).findall(".//a:t",ns))
                offsets = [plain.index(p["name"]) for p in players]
                assert offsets == sorted(offsets)
                assert all(f"{p['rating']['low']:+.4f}" in plain for p in players)
            assert self.url in " ".join(texts)
            assert not any(t in " ".join(texts) for t in ("localhost", "/home/manav", "TODO", "TBD"))
            media = [n for n in z.namelist() if n.startswith("ppt/media/")]
            assert len(media)==20, len(media)
            assert len([n for n in z.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+.xml",n)])==self.page
        result = {"slides":self.page,"pptx_bytes":ppt.stat().st_size,
                  "pdf_bytes":(OUT/"pressure-index-slides.pdf").stat().st_size,
                  "embedded_portraits":len(self.images),"rank_and_score_parity":True,
                  "native_text_boxes":len(self.audit),"text_fit_and_bounds_checks":True,
                  "dashboard_url":self.url,"placeholder":self.placeholder,
                  "preview":"PDF generated from the same layout, not a PowerPoint renderer"}
        (CHECKS/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
        (CHECKS/"text-layout.json").write_text(json.dumps(self.audit,indent=2)+"\n")
        print(json.dumps(result,indent=2))


def build(d):
    d.new("SupeRR Selector  /  Season 2", "Pressure, with proof.",
          notes="Round 1 submission. Independent analysis, not an official RR product. Portraits are user-supplied AI-generated jersey concepts; team association is illustrative. Rankings describe the frozen retained population, not auction availability or future performance.",portrait=True)
    d.text(.55,1.9,6.7,1.3,"Twenty selections.\nEvery decision accountable.",35,True)
    d.text(.55,3.49,6.0,1.25,"Two ranked top tens backed by verified match states, peer comparisons and reviewed counterexamples.",22,color=MUTED)
    d.rect(.55,5.04,5.7,.73,BLUSH,BORDER)
    d.text(.76,5.25,5.27,.3,"ROUND 1  /  RELIABLE PLAYERS UNDER PRESSURE",12,True,PINK)
    d.text(.55,6.02,6.7,.65,"IPL + T20I evidence, 2023–1 Nov 2026\nIndependent SupeRR Selector submission",14,color=MUTED)
    d.photo(BAT[0],7.5,1.85,2.16,2.7)
    d.photo(BOWL[0],10.05,1.85,2.16,2.7)
    for x,p in [(7.5,BAT[0]),(10.05,BOWL[0])]:
        d.text(x,4.79,2.35,.4,p['name'],18,True)
        d.text(x,5.29,2.35,.5,"#1 "+("BATTING" if p['role']=='batting' else "BOWLING"),12,True,PINK)
    d.text(7.5,6.02,5.0,.57,"Illustrative RR jersey concepts.\nSelections are analytical recommendations.",12,color=MUTED)

    d.new("Executive decision", "Select the pressure task. Show the evidence.",
          "The output is two ranked top tens. It is not an auction availability list or a forecast of the 2027 season.")
    d.card(.5,2.3,4.0,3.65,"Batting lead","Tim David","66 pressure matches. First under all three registered runs / wickets mixes.",19)
    d.card(4.66,2.3,4.0,3.65,"Bowling lead","Sunil Narine","40 pressure matches. First under all three mixes; retained evidence is IPL-only.",19)
    d.card(8.82,2.3,4.0,3.65,"Evidence qualifier","7 of 20","Pass every standalone 2026 gate. Eleven have limited evidence; two have none.",19)
    d.text(.55,6.25,12.1,.65,"Decision standard: scoring with preservation; wickets with concession control. Every pick receives a role, a positive case and a challenge.",18,True)

    d.new("The selector's question", "Who delivers the task when the game tightens?",
          "Use observed match context to interpret performance; do not let reputation or one highlight decide the list.")
    d.card(.5,2.3,4,3.95,"01 / Define","Situation first","Identify late overs, a collapse or a tight chase from information available before the delivery.",19)
    d.card(4.66,2.3,4,3.95,"02 / Compare","A fairer reference","Compare with other players in the same family, year, innings, phase and wicket band.",19)
    d.card(8.82,2.3,4,3.95,"03 / Challenge","Repeatability matters","Resample whole matches, remove matches/seasons and inspect adverse evidence before endorsing a pick.",19)
    d.text(.55,6.52,12,.3,"Observe → verify → flag pressure → compare peers → shrink → bootstrap → review → rank",17,True,PINK)

    d.new("Trust before ranking", "Repair the scoreboard before reading the pressure.",
          "The ambiguous extras field was tested against match results. Neither simple reconstruction rule was reliable enough.",
          notes="883 supplied matches accounted for. 651 complete matches / 155,799 delivery events verified across available years. Final 2023–cutoff cohort: 511 matches / 121,891 events. Revised official extras agreement: all 121,891 retained events; two batter-run repairs remain. Unresolved matches excluded, raw data preserved; no cohort expansion after evaluation.")
    for x,num,label in [(.5,"883","supplied matches"),(3.62,"651","complete verified matches"),(6.74,"511","in the frozen rating window"),(9.86,"43,029","pressure events")]:
        d.rect(x,2.4,2.95,1.5,BLUSH,BORDER)
        d.text(x+.18,2.61,2.6,.62,num,34,True,PINK)
        d.text(x+.18,3.32,2.6,.4,label,13,color=MUTED)
    d.text(.55,4.28,5.8,.45,"What changed",23,True)
    d.text(.55,4.98,5.8,1.4,"External event reconciliation rebuilt trustworthy scores and chase states. Unresolved cases remain excluded; the supplied raw data is preserved.",20)
    d.text(6.9,4.28,5.8,.45,"What remains a risk",23,True)
    d.text(6.9,4.98,5.8,1.4,"Verified event retention differs: IPL 92.50%, T20I 70.24%. Player-level retention gates help, but cannot eliminate missing-data bias.",20)

    d.new("Frozen pressure rule", "Three situations. One pre-ball pressure flag.",
          "Use late OR collapse OR tight chase; overlapping conditions count the delivery once.")
    d.card(.5,2.3,4,3.6,"Late","Overs 16–20","Every delivery in the closing five overs is pressure.",20)
    d.card(4.66,2.3,4,3.6,"Collapse","Wickets disrupt","At least 2 wickets in the preceding 12 legal balls, OR 4 already lost in overs 1–10.",19)
    d.card(8.82,2.3,4,3.6,"Tight chase","A live equation","Innings 2; 1–60 legal balls left; required runs per ball between 0.75 and 1.50 inclusive.",19)
    d.text(.55,6.14,12.05,.69,"35.30% of final-window events are flagged, above the 20–30% diagnostic target. The broad late-over rule plus collapse/chase expansion explains this; thresholds were not tuned to favour players.",17,True,PINK)

    d.new("The active rating", "Reward the output. Respect the cost.",
          "A descriptive peer-relative pressure index, with frozen rules and separate batting and bowling lists.",
          notes="Peers: competition family × year × innings × phase × pre-ball wicket band. Exclude all evaluated player's outcomes in that role from own peer means. Cell requires at least 20 other-player opportunities across 3 matches; no parent or cross-year fallback. 730-day recency; development-frozen run/wicket SD scales. n_eff=(sum w)^2/sum(w^2); shrink n_eff/(n_eff+k), k=75 batting/60 bowling. Default runs:wickets 60:40; sensitivities 50:50 and 70:30 on identical cohorts.")
    d.card(.5,2.35,5.98,2.85,"Batting","Scoring + preservation","More batter runs; fewer attributed dismissals versus supported peers.",18)
    d.card(6.65,2.35,6.18,2.85,"Bowling","Control + wickets","Fewer charged runs; more credited wickets versus supported peers.",18)
    d.text(.6,5.56,12,.45,"60% runs  +  40% wickets  →  recency-weighted peer differences  →  sample-size shrinkage",18,True,PINK)
    d.text(.6,6.25,12,.5,"730-day half-life. Frozen development scales. Each player's own outcomes are removed from their peer reference.",17,color=MUTED)

    d.new("What the score can say", "Rank by a cautious quantile. Keep the limits visible.",
          "1,000 shared whole-match bootstrap draws preserve within-match dependence; final order uses the 10th percentile (P10).",
          notes="Resampling stratified by competition family/year, seed 1729. Each draw recomputes player and peer means, effective exposure, workload and shrinkage; eligibility, support and development scales fixed. At least 95% finite draws required. Ties: point estimate, supported pressure matches, stable ID. Prior predictive baselines were fitted and failed calibration gates; no ML model promoted. Supported level/change 70/30 and 50/50 companion withheld because no reliable final change intervals.")
    d.card(.5,2.4,4,3.85,"Interpretation","A pressure level","The list describes observed performance against supported peers. P10 is an index quantile, not a probability.",18)
    d.card(4.66,2.4,4,3.85,"Material limitation","Usual is unresolved","All late-over events are pressure. Reliable same-context pressure-minus-usual intervals are unavailable for the final picks.",18)
    d.card(8.82,2.4,4,3.85,"Model discipline","No promoted ML","Historical models failed calibration gates. We stopped refinement and built reviewed player evidence instead.",18)
    d.text(.55,6.46,12,.34,"No claim of a causal pressure effect, fully adjusted ability, or a validated IPL 2027 forecast.",17,True,AMBER)

    d.ranked_table(BAT,"batters")
    d.ranked_table(BOWL,"bowlers")

    d.new("Stability and recency", "Strong leaders. Qualified edges.",
          "Sensitivity changes runs/wickets weights on identical cohorts. It is a challenge to the decision, not a search for preferred names.")
    d.card(.5,2.3,4,3.6,"Weight sensitivity","10/10 and 8/10","Batting membership retained under 50/50 and 70/30; bowling retains 9/10 under each.",19)
    d.card(4.66,2.3,4,3.6,"Ordering uncertainty","Ranks can move","Tilak: 5–15. Rasikh: 4–11. Chawla: 7–13. Exact ordering is less stable than the leading names.",19)
    d.card(8.82,2.3,4,3.6,"Recent evidence","Adequate ≠ good","Varun passes 2026 eligibility, but his standalone-year point estimate is negative. Russell and Chawla have no retained 2026 pressure events.",17)
    d.text(.55,6.15,12.1,.65,"2026 was separately evaluated before the combined freeze. Earlier aggregate 2026 EDA had been seen: this is retrospective evaluation, not a pristine unseen forecast test.",17,color=AMBER)

    d.new("The boundary decisions", "Tenth place is a close call, not a certainty.",
          "The registered P10 ordering decides inclusion. Substantial interval overlap remains visible.")
    for x,role,ids,title in [(.5,"batting",("4391","37052"),"Livingstone / Naman Dhir"),(6.75,"bowling",("23","4101"),"Chawla / Santner")]:
        d.rect(x,2.35,6.05,3.9,BLUSH,BORDER)
        d.text(x+.22,2.57,5.6,.4,title,21,True)
        rows=[next(p for p in PLAYERS if p['role']==role and p['id']==pid) for pid in ids]
        d.text(x+.22,3.14,5.55,.22,"Index scale: 0.00 to 0.18  |  bar = P10–P90",11,color=MUTED)
        for j,p in enumerate(rows):
            yy=3.58+j*1.09
            d.text(x+.22,yy,5.55,.29,f"#{p['rank']}  {p['name']}",16,True)
            start=x+.3
            d.rect(start,yy+.43,5.1,.025,BORDER)
            lo,hi,point=(p['rating'][k]/.18*5.1 for k in ('low','high','point'))
            d.rect(start+lo,yy+.40,hi-lo,.09,PINK if j==0 else MUTED)
            d.rect(start+point-.035,yy+.355,.07,.18,NAVY)
            d.text(x+.22,yy+.64,5.55,.25,f"P10 {p['rating']['low']:+.6f}   |   P90 {p['rating']['high']:+.4f}",13,color=PINK)
        d.text(x+.22,5.9,5.6,.24,"Overlapping intervals; tick = point estimate",11,color=MUTED)
    d.text(.55,6.35,12,.55,"Other credible exclusions: Phil Salt and Glenn Phillips; Mohsin Khan and Lungi Ngidi. Profiles remain accessible in the dashboard.",16,color=MUTED)

    d.new("How this can strengthen RR", "Build a menu of pressure skills.",
          "Translate the observed workload into selection options, then assess real squad needs and auction availability separately.")
    d.card(.5,2.3,4,3.95,"Scoring options","Close or rebuild","David / Pooran: late scoring. Suryakumar / Shreyas: middle-over tempo. Tilak: preservation alongside scoring.",18)
    d.card(4.66,2.3,4,3.95,"Bowling options","Control or strike","Narine: retained IPL control. Bumrah: opening/closing workload. Mustafizur: late bowling. Rasikh: wickets with concession risk.",18)
    d.card(8.82,2.3,4,3.95,"Review priorities","Resolve transfer","Mahedi has T20I-only evidence. Bethell, Sakib and Anukul need short-history caution. Verify current form and availability independently.",18)
    d.text(.55,6.39,12,.55,"These are evidence-backed options, without invented squad quotas, prices, retained-player assumptions or availability claims.",16,True,AMBER)

    d.dossiers(BAT,"Batting")
    d.dossiers(BOWL,"Bowling")

    d.new("Why this submission is distinctive", "An accountable decision, not a highlight reel.",
          "The differentiator is how the evidence can be challenged: repairs, peer definitions, uncertainty, counterexamples and close exclusions.")
    for x,heading,body in [(.55,"Trust","Audited extras before deriving pressure."),(4.74,"Discipline","Stopped models that failed validation."),(8.93,"Transparency","Published the weaknesses of our own picks.")]:
        d.text(x,2.43,3.75,.6,heading,26,True,PINK)
        d.text(x,3.19,3.75,1.04,body,21)
    d.line(.55,4.63,12.2)
    d.text(.55,4.98,12,.45,"Explore the evidence dashboard",25,True)
    d.text(.55,5.65,12,.4,d.url,22,True,PINK,link=d.url)
    d.text(.55,6.25,12,.45,"PLACEHOLDER — replace with the deployed public URL before submission." if d.placeholder else "Public dashboard link supplied for this build; verify public access before submission.",16,color=AMBER)

    d.new("Technical appendix", "Reproducible rules behind the decisions.",
          "The analytical opportunity count is not official balls faced, strike rate or economy.")
    blocks=[(.55,2.34,"Opportunity definitions","Batting excludes wides, includes no-balls; use batter runs and bowler-attributable striker dismissals. Bowling uses all attempts; charged runs exclude byes, leg-byes and penalties."),
            (6.84,2.34,"Eligibility and support","Total opportunities ≥300 batting / 240 bowling; pressure ≥75 / 60; ≥8 pressure matches; effective count ≥40. Source retention ≥80%; supported pressure count and weighted mass ≥80%."),
            (.55,4.55,"Exact rating ingredients","Same-family/year/innings/phase/wicket-band peers; ≥20 other-player opportunities in ≥3 matches. Standardized favourable run and wicket differences, 60/40 weighted; shrink by n_eff / (n_eff + k)."),
            (6.84,4.55,"Frozen evaluation","k=75 batting / 60 bowling. Development 2023–25: 402 matches; reserved 2026: 109. Protocol 5ca8bea. Combined cutoff 1 Nov 2026. No missing change imputed as zero; level/change variants withheld.")]
    for x,y,title,body in blocks:
        d.text(x,y,5.85,.4,title,20,True,PINK)
        d.text(x,y+.62,5.85,1.45,body,16)

    d.new("Sources and scope", "Traceable inputs. Honest boundaries.",
          "Release: pressure-index-2026-11-01-v1  /  The published ordering is frozen; presentation work does not refit it.")
    sources=[("Competition and supplied brief", "https://unstop.com/hackathons/crp-superr-selector-season-2-help-shape-rajasthan-royals-ipl-2027-auction-strategy-rajasthan-royals-1792758"),
             ("Cricsheet event reconciliation", "https://cricsheet.org/"),
             ("Cricsheet data attribution: ODC-By 1.0", "https://opendatacommons.org/licenses/by/1-0/"),
             ("Reproducible project, method and evidence", "https://github.com/TheManavGohil/SupeRR")]
    for i,(label,url) in enumerate(sources):
        d.text(.55,2.4+i*.59,6.1,.35,label,17,True,PINK,link=url)
    d.text(7.06,2.4,5.7,.45,"What this does not measure",21,True)
    d.text(7.06,3.1,5.6,1.8,"Venue or opposition-strength adjustment, full chase-difficulty adjustment, causal response to pressure, 2027 availability, auction prices or current RR squad fit.",19,color=MUTED)
    d.text(.55,5.24,12.05,.7,"Portraits: user-supplied AI-generated RR jersey concepts, used illustratively; no official team association or signing is implied. Presentation is an independent participant submission.",15,color=MUTED)
    d.text(.55,6.18,12.05,.5,"Before uploading: replace the placeholder URL, map the exact dropdown aliases and complete participant review. The dashboard and deck contain the same two ranked top tens.",15,True,AMBER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard-url",default=URL)
    args = parser.parse_args()
    assert args.dashboard_url.startswith("https://")
    deck=Deck(args.dashboard_url)
    build(deck)
    deck.finish()
