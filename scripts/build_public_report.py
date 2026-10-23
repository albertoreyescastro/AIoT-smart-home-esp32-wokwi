#!/usr/bin/env python3
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "aiot_smart_home_public_report.pdf"
PAGE_W, _ = A4
M = 18 * mm

class StableCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["invariant"] = 1
        super().__init__(*args, **kwargs)

ss = getSampleStyleSheet()
ss.add(ParagraphStyle(name="TitleX", parent=ss["Title"], fontSize=25, leading=29, alignment=TA_CENTER, spaceAfter=10))
ss.add(ParagraphStyle(name="SubX", parent=ss["Normal"], fontSize=11.5, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#374151")))
ss.add(ParagraphStyle(name="H1X", parent=ss["Heading1"], fontSize=16, leading=20, spaceBefore=8, spaceAfter=8))
ss.add(ParagraphStyle(name="H2X", parent=ss["Heading2"], fontSize=11.5, leading=15, spaceBefore=5, spaceAfter=4))
ss.add(ParagraphStyle(name="BodyX", parent=ss["BodyText"], fontSize=9.4, leading=13.2, spaceAfter=6, textColor=colors.HexColor("#1F2937")))
ss.add(ParagraphStyle(name="CalloutX", parent=ss["BodyText"], fontName="Helvetica-Bold", fontSize=9.2, leading=13, borderWidth=.6, borderColor=colors.HexColor("#9CA3AF"), borderPadding=7, backColor=colors.HexColor("#F9FAFB"), spaceAfter=7))

P=lambda t,s="BodyX": Paragraph(t, ss[s])

def B(t):
    st=ParagraphStyle(name="b", parent=ss["BodyX"], leftIndent=10, firstLineIndent=-7, spaceAfter=3)
    return Paragraph("• "+t, st)

def T(rows, widths):
    t=Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#D1D5DB")),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E5E7EB")),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-1),8.2),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    return t

def footer(c, doc):
    c.saveState(); c.setFont("Helvetica",7.5); c.setFillColor(colors.HexColor("#6B7280"))
    c.drawString(M,10*mm,"AIoT Smart Home ESP32-S3 - Public Portfolio Report")
    c.drawRightString(PAGE_W-M,10*mm,f"Page {doc.page}"); c.restoreState()

doc=SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=17*mm, bottomMargin=17*mm,
    title="AIoT Smart Home ESP32-S3 - Public Portfolio Report", author="Alberto Reyes Castro")
s=[]
s += [Spacer(1,23*mm),P("AIoT Smart Home ESP32-S3","TitleX"),P("Simulation-based smart-home prototype for comfort, privacy, security and environmental safety","SubX"),Spacer(1,6*mm),HRFlowable(width="70%",color=colors.HexColor("#9CA3AF"),hAlign="CENTER"),Spacer(1,7*mm),P("<b>Alberto Reyes Castro</b>","SubX"),P("MSc Artificial Intelligence Technology portfolio project","SubX"),Spacer(1,8*mm),T([["Area","Public evidence"],["Embedded","Two ESP32-S3 Arduino/C++ room controllers"],["Simulation","Two public Wokwi room simulations"],["IoT","Optional Blynk monitoring; disabled by default"],["Safety","Deterministic gas, heat, occupancy and escalation logic"],["TinyML","Synthetic dataset + historical Edge Impulse evidence"],["Quality","Validator, scenario tests, pinned ESP32-S3 CI and deterministic report build"]],[42*mm,112*mm]),Spacer(1,8*mm),P("<b>Scope:</b> academic/portfolio prototype. Sensors are simulated, thresholds are demonstration values, and no physical-hardware or safety-certification claim is made.","CalloutX"),P("Hardening V2 - 23 October 2026"),PageBreak()]

s += [P("1. Current public architecture","H1X"),P("The repository implements a Bedroom controller focused on comfort, privacy, lighting and Home/Away security, plus a Kitchen/Living Room controller focused on environmental monitoring and staged safety escalation."),T([["Subsystem","Inputs","Outputs / decisions"],["Bedroom","PIR, indoor/outdoor light, DHT22, buttons","Blinds, ambient/manual lighting, AC, LCD, buzzer, Home/Away"],["Kitchen/Living","MQ2 score, DHT22, PIR, light, buttons","Gas/heat state, blinds, AC, alerts, emergency-cooling indicator"],["Optional cloud","Blynk virtual pins","Monitoring and selected controls"],["Optional ML","gas_score, temperature, humidity","Five-class Edge Impulse prediction when an actual generated runtime is enabled"]],[31*mm,57*mm,68*mm]),P("Both sketches keep <font name='Courier'>ENABLE_BLYNK = 0</font> by default, so placeholder cloud credentials cannot block the local Wokwi demo."),P("2. Bedroom module","H1X"),B("Normal, Sleep, Privacy and Eco modes; Standard, Elderly and Child profiles."),B("PIR occupancy, adaptive blinds/lighting, DHT22 thermal control and Home/Away escalation."),B("Physical Wokwi outdoor LDR is authoritative by default; an explicitly enabled Blynk V3 can take control until the physical LDR moves again."),B("Visible PIN/secret-word values are demonstration-only state-transition controls."),PageBreak()]

s += [P("3. Kitchen / Living Room module","H1X"),P("The deterministic environmental state is based on project-specific demonstration boundaries plus persistence/warm-up logic."),T([["Synthetic/demo condition","Label"],["gas_score >= 850 and temperature >= 55 C","GAS_HEAT_EMERGENCY"],["gas_score >= 850","GAS_DANGER"],["temperature >= 55 C","HEAT_ANOMALY"],["gas_score >= 420","COOKING_FUMES"],["otherwise","NORMAL"]],[98*mm,58*mm]),P("These are not calibrated domestic safety limits."),P("ML-disabled semantics","H2X"),P("The public Wokwi build keeps <font name='Courier'>USE_EDGE_IMPULSE_RUNTIME = 0</font>. In that mode no classifier runs, no model confidence is fabricated, the environmental state is rule-derived, ML confidence is shown as <b>N/A</b>, and raw ML prediction as <b>DISABLED</b>.","CalloutX"),P("If a reviewer supplies a compatible generated Edge Impulse library and enables the runtime, a valid ML prediction may only increase the selected environmental severity; it does not suppress a more severe deterministic state."),PageBreak()]

s += [P("4. TinyML experiment and evidence","H1X"),P("The checked-in dataset is simulated and rule-labelled from the same gas/temperature boundaries used by the demo. Humidity is an input feature but does not determine the synthetic ground-truth label. Strong model performance is therefore expected and is workflow evidence, not independent real-world predictive validation."),P("Historical Edge Impulse run","H2X"),T([["Item","Recorded evidence"],["Inputs","gas_score, temperature, humidity"],["Task","Five-class tabular classification"],["Training config","100 cycles; learning rate 0.0005; small dense classifier"],["Training accuracy","~93.4%"],["Held-out test accuracy","~85.9%"],["Weighted precision / recall / F1","~0.91 / 0.89 / 0.89"],["AUC","~0.99 (platform-reported)"],["Estimated embedded cost","~1 ms; ~1.4 KB RAM; ~14.4 KB flash"]],[57*mm,99*mm]),P("The generated inferencing ZIP is intentionally not redistributed. The historical screenshots/model card document the experiment, but the repository does not claim bit-for-bit reproduction of the original hosted Edge Impulse run."),PageBreak()]

s += [P("5. Reproducibility and CI","H1X"),T([["Gate","Purpose"],["Repository validator","Dataset rules, diagrams, placeholders, token patterns, offline defaults, dependency/document invariants"],["Scenario contracts","Environmental boundary cases, severity ordering and profile-sensitive gas thresholds"],["ESP32-S3 compile","Both sketches build against pinned toolchain/library versions"],["Report consistency","The PDF is rebuilt deterministically and compared with the committed report"]],[43*mm,113*mm]),P("Pinned build environment","H2X"),T([["Component","Pinned version"],["Arduino CLI","1.5.1"],["ESP32 Arduino core","3.3.12"],["Blynk","1.4.0"],["ESP32Servo","3.2.1"],["LiquidCrystal_PCF8574","2.3.0"],["DHT sensor library","1.4.7"],["ReportLab","5.1.0"]],[70*mm,86*mm]),P("The LCD dependency is architecture-agnostic rather than the AVR-declared library that previously generated an ESP32 compatibility warning."),PageBreak()]

s += [P("6. Security, privacy and limitations","H1X"),B("Blynk template/auth values are placeholders; Wokwi-GUEST is a simulator network."),B("The local room logic does not require Blynk; cloud integration is optional."),B("No real household monitoring dataset or private credentials are included."),B("The generated Edge Impulse deployment archive is not redistributed; third-party components retain their own licence terms."),B("No calibrated gas concentration, certified alarm behaviour or physical ESP32-S3 deployment is claimed."),B("Real deployment would require calibrated sensors, independently labelled data, target latency/RAM/flash/power measurements, fault/drift tests, secure provisioning, false-positive/false-negative analysis and domain safety review."),P("7. Future work","H1X"),B("Validate on physical ESP32-S3 hardware."),B("Collect real independently labelled environmental data under a documented protocol."),B("Measure deployment resources and failure modes on target hardware."),B("Only then reconsider ML-assisted safety decisions beyond the current transparent experimental role."),PageBreak()]

s += [P("8. Selected references","H1X"),P("Al-Fuqaha, A. et al. (2015). Internet of Things: A survey on enabling technologies, protocols, and applications. <i>IEEE Communications Surveys & Tutorials</i>, 17(4), 2347-2376."),P("Dutta, L. and Bharali, S. (2021). TinyML meets IoT: A comprehensive survey. <i>Internet of Things</i>, 16, 100461."),P("Merenda, M., Porcaro, C. and Iero, D. (2020). Edge machine learning for AI-enabled IoT devices: A review. <i>Sensors</i>, 20(9), 2533."),P("Shi, W. et al. (2016). Edge computing: Vision and challenges. <i>IEEE Internet of Things Journal</i>, 3(5), 637-646."),P("Stojkoska, B.L.R. and Trivodaliev, K.V. (2017). A review of Internet of Things for smart home: Challenges and solutions. <i>Journal of Cleaner Production</i>, 140, 1454-1464."),P("Warden, P. and Situnayake, D. (2019). <i>TinyML</i>. O'Reilly Media."),Spacer(1,5*mm),P("<b>Reviewer interpretation:</b> the current README, source code, reproducibility notes and model card define the public portfolio claim. Historical academic screenshots/metrics are retained as evidence of the earlier experiment, not as runtime telemetry from the hardened Wokwi build.","CalloutX"),P("Repository: github.com/albertoreyescastro/AIoT-smart-home-esp32-wokwi"),P("Wokwi Bedroom: wokwi.com/projects/465661521735358465"),P("Wokwi Kitchen/Living: wokwi.com/projects/465661368262601729")]

doc.build(s, onFirstPage=footer, onLaterPages=footer, canvasmaker=StableCanvas)
print(OUT)
