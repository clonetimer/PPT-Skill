#!/usr/bin/env python3
"""Source-grounded spacecraft bus mechanism diagram with typed interfaces."""
from __future__ import annotations
import json,sys
from pathlib import Path
import jsonschema

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"tools"))
from scientific_ir import CONTRACTS,enrich_spec,validate_drawn_routes,validate_spec  # noqa: E402
from render_figure_spec import render  # noqa: E402

ID="SC01_spacecraft_bus_mechanism"
SOURCE=json.loads((OUT/"expected_topology.json").read_text(encoding="utf-8"))
STYLE=json.loads((OUT/"source_style.json").read_text(encoding="utf-8"))
assert SOURCE["figure_id"]==ID and 5<=len(STYLE["anchors"])<=7
REQUIRED={tuple(v) for v in SOURCE["required_edges"]}
CONTRACTS[ID]={"claim":SOURCE["claim"],"archetype":"schematic_led_composite",
 "output_mode":"presentation","unverified":SOURCE["configuration_boundary"],
 "source":"dist/skill_tests/spacecraft/SOURCE.md",
 "source_locator":"NASA 2026 platform/avionics/GNC/power/thermal pages and Webb bus; NASA 1974 Fig. 2-9 visual reference, all enumerated in SOURCE.md",
 "evidence_status":"domain_adaptation",
 "evidence_scope":"Notional three-axis stabilized solar-powered satellite with propulsion; functional interface schematic, not flight hardware design.",
 "reuse":"NASA public technical sources; newly drawn editable diagram, no source image embedded."}

E=[];EDGES=[];INK="#25343C";MUTED="#5E6C72";POWER="#A25A1C";DATA="#185F72";CTRL="#655287";HEAT="#9B4C4C"

def txt(s,x,y,w,h,size=11,align="center",bold=False,color=INK,sid=None):
 z=dict(type="text",text=s,x=x,y=y,w=w,h=h,size=size,align=align,bold=bold,color=color)
 if sid:z["semantic_id"]=sid
 E.append(z)
def rect(x,y,w,h,fill="#FFFFFF",stroke=INK,sw=.9,dash=False,sid=None,radius=0):
 z=dict(type="rect",x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,sw=sw,radius=radius)
 if dash:z["dash"]=True
 if sid:z["semantic_id"]=sid
 E.append(z)
def box(sid,label,x,y,w,h,fill="#FFFFFF",size=10.5):
 rect(x,y,w,h,fill,sw=.9,sid=sid)
 txt(label,x+.03,y+.015,w-.06,h-.03,size)
def line(x1,y1,x2,y2,color=INK,sw=1.2,arrow=False,dash=False,link=None):
 z=dict(type="line",x1=x1,y1=y1,x2=x2,y2=y2,color=color,sw=sw,arrow=arrow)
 if dash:z["dash"]=True
 if link:z["semantic_link"]=link
 E.append(z)
def edge(a,b,points,color=INK,dash=False,sw=1.25):
 EDGES.append((a,b))
 for i,(p,q) in enumerate(zip(points,points[1:])):
  line(*p,*q,color=color,sw=sw,arrow=i==len(points)-2,dash=dash,link=f"{a}__{b}")
def group(sid,label,x,y,w,h,optional=False):
 rect(x,y,w,h,"#FFFFFF",stroke="#758389",sw=1,dash=True,sid=sid)
 txt(label,x+.10,y+.09,(w-1.36) if optional else (w-.20),.25,11.5,align="left",bold=True)
 if optional:txt("任务可选",x+w-1.12,y+.09,1.00,.25,9.7,color=MUTED)

# Figure-level hierarchy: external environment outside the dotted bus boundary.
txt("航天器关键分系统｜能量、信息、姿态与热的工作路径",.45,.19,15.05,.42,20,align="left",bold=True)
txt("示意对象：太阳能供电、三轴稳定、带推进的卫星平台；分系统器件与接口随任务配置。",.45,.66,15.05,.25,10.8,align="left",color=MUTED)
rect(2.00,1.34,13.12,6.61,"#FFFFFF",stroke="#374B56",sw=1.25,dash=True)
txt("航天器平台 / 结构与线缆接口",2.20,1.39,12.60,.24,10.5,align="left",bold=True)

group("comms_group","通信 TT&C",2.20,1.80,2.34,1.83)
group("cdh_group","指令与数据处理 C&DH",4.80,1.80,3.04,1.83)
group("payload_group","任务载荷",8.10,1.80,2.35,1.83)
group("thermal_group","热控 TCS",10.70,1.80,4.12,1.83)
group("eps_group","电源 EPS",2.20,5.15,3.25,2.48)
group("adcs_group","姿态确定与控制 ADCS",5.72,5.15,4.21,2.48)
group("prop_group","推进 PROP",10.19,5.15,4.63,2.48,optional=True)

# External symbols: ground dish, Sun, deep-space heat sink and orbit state.
txt("地面站",.38,1.94,1.30,.29,11,bold=True,sid="ground")
line(.80,2.37,1.08,2.66);line(1.08,2.66,1.27,2.66)
E.append(dict(type="ellipse",x=.58,y=2.25,w=.47,h=.18,fill="#FFFFFF",stroke=INK,sw=1))
txt("上行指令 / 下行遥测",.30,3.12,1.58,.31,9.4,color=MUTED)
E.append(dict(type="ellipse",x=.62,y=5.88,w=.55,h=.55,fill="#F7E9C8",stroke=POWER,sw=1,semantic_id="sun"))
txt("太阳",.52,6.47,.75,.24,10.4,bold=True)
txt("深空",15.18,2.32,.72,.30,10.5,sid="space")
txt("轨道 Δv",15.16,6.07,.78,.35,10.5,sid="orbit")

# TT&C antenna and transceiver. Antenna is a semantic hardware glyph, not a decoration.
E.append(dict(type="ellipse",x=2.48,y=2.34,w=.37,h=.24,fill="#FFFFFF",stroke=INK,sw=1))
line(2.64,2.58,2.83,2.75);line(2.83,2.75,2.90,2.75)
box("transceiver","收发机\n调制 / 解调",2.98,2.28,1.20,.69,size=9.8)
edge("ground","transceiver",[(1.68,2.08),(1.82,2.08),(1.82,2.43),(2.94,2.43)],DATA)
edge("transceiver","ground",[(2.98,2.83),(1.86,2.83),(1.86,2.26),(1.68,2.26)],DATA,dash=True)

# Command, storage and mission data path.
box("obc","星载计算机\n指令 / 遥测",5.23,2.26,1.22,.70,size=9.8)
box("storage","固态存储",6.74,2.32,.83,.54,size=9.7)
box("payload","任务仪器\n观测 / 数据",8.78,2.27,1.20,.66,size=9.8)
line(8.39,2.59,8.73,2.59);line(8.55,2.45,8.55,2.72)
edge("transceiver","obc",[(4.18,2.55),(5.19,2.55)],DATA)
edge("payload","storage",[(8.78,2.72),(7.60,2.72)],DATA)
edge("storage","transceiver",[(7.15,2.86),(7.15,3.23),(4.25,3.23),(4.25,2.86),(4.20,2.86)],DATA,dash=True)
txt("科学数据 → 存储 → 下传",5.02,3.28,4.06,.20,9.2,color=DATA)

# The routed command bus and distributed power rail are different interfaces.
rect(5.12,3.87,9.54,.13,"#E8E4EF",stroke=CTRL,sw=.75,sid="command_bus")
txt("指令 / 状态总线",8.48,3.67,2.35,.20,9.3,color=CTRL)
rect(2.40,4.50,12.26,.17,"#F5E9D9",stroke=POWER,sw=.9,sid="power_bus")
txt("稳压直流配电母线（至各负载）",5.73,4.72,5.50,.20,9.5,color=POWER)
edge("obc","command_bus",[(5.84,2.96),(5.84,3.84)],CTRL,dash=True)
edge("command_bus","payload",[(9.42,3.87),(9.42,2.96)],CTRL,dash=True)

# EPS: source, control/distribution and rechargeable storage.
E.append(dict(type="grid",x=2.60,y=5.86,w=.70,h=.59,rows=3,cols=4,fill="#F3F7F8",stroke="#9BB1BB",border=INK,sw=.55,semantic_id="solar_array"))
txt("太阳阵",2.52,6.54,.86,.24,9.9)
box("pcdu","功率调节\n与配电",3.65,5.88,1.00,.58,size=9.7)
box("battery","蓄电池",4.89,5.92,.47,.51,size=8.8)
edge("sun","solar_array",[(1.17,6.15),(2.56,6.15)],POWER)
edge("solar_array","pcdu",[(3.30,6.15),(3.61,6.15)],POWER)
edge("pcdu","battery",[(4.65,6.04),(4.85,6.04)],POWER)
edge("battery","pcdu",[(4.89,6.32),(4.69,6.32)],POWER,dash=True)
edge("pcdu","power_bus",[(4.15,5.88),(4.15,4.70)],POWER)
txt("充 / 放电",4.51,6.65,.83,.22,9,color=POWER)

# Power taps: actual voltage/current and harness implementation are unspecified.
for target,x,ys,ye in [
 ("comms_group",3.60,4.50,3.66),("cdh_group",5.03,4.50,3.66),
 ("payload_group",9.27,4.50,3.66),("thermal_group",12.95,4.50,3.66),
 ("adcs_group",6.83,4.67,5.11),("prop_group",12.74,4.67,5.11)]:
 edge("power_bus",target,[(x,ys),(x,ye)],POWER,sw=1.2)

# ADCS closed loop: measurements -> control -> wheel torque -> attitude -> measurements.
box("adcs_sensor","星敏 / 惯导\n姿态测量",6.01,5.87,1.07,.61,size=9.6)
box("adcs_control","状态估计\n控制律",7.37,5.87,1.07,.61,size=9.6)
E.append(dict(type="ellipse",x=8.76,y=5.88,w=.55,h=.55,fill="#FFFFFF",stroke=INK,sw=1,semantic_id="reaction_wheel"))
E.append(dict(type="ellipse",x=8.88,y=6.00,w=.31,h=.31,fill="#FFFFFF",stroke=INK,sw=.8))
txt("飞轮",8.67,6.52,.76,.20,9.4)
E.append(dict(type="ellipse",x=9.17,y=6.80,w=.49,h=.31,fill="#FFFFFF",stroke=INK,sw=1,semantic_id="attitude"))
txt("姿态 θ",9.05,7.13,.73,.18,8.8)
edge("adcs_sensor","adcs_control",[(7.08,6.17),(7.33,6.17)],CTRL)
edge("adcs_control","reaction_wheel",[(8.44,6.17),(8.72,6.17)],CTRL)
edge("reaction_wheel","attitude",[(9.31,6.17),(9.60,6.17),(9.60,6.76)],CTRL)
edge("attitude","adcs_sensor",[(9.17,6.96),(6.55,6.96),(6.55,6.52)],CTRL,dash=True)
edge("command_bus","adcs_control",[(7.92,4.00),(7.92,5.83)],CTRL,dash=True)
txt("反馈：指向 / 稳定",6.44,7.22,2.28,.20,9,color=CTRL)

# Thermal path: payload heat -> temperature management -> radiator -> space.
box("thermal_control","测温 / 加热\n热控管理",11.62,2.27,1.15,.65,size=9.5)
rect(13.28,2.28,.79,.60,"#FFFFFF",sid="radiator",sw=.9)
for i in range(4):line(13.38+i*.16,2.34,13.38+i*.16,2.82,HEAT,sw=.8)
txt("散热器",13.24,2.98,.89,.20,9.5)
edge("payload","thermal_control",[(9.98,2.60),(11.58,2.60)],HEAT)
edge("thermal_control","radiator",[(12.77,2.60),(13.24,2.60)],HEAT)
edge("radiator","space",[(14.07,2.60),(15.14,2.60)],HEAT)

# Optional propulsion branch: propellant flow and commanded valve.
E.append(dict(type="ellipse",x=10.60,y=5.88,w=.75,h=.59,fill="#FFFFFF",stroke=INK,sw=.9,semantic_id="prop_tank"))
txt("贮箱",10.63,6.52,.69,.20,9.5)
box("prop_valve","阀门",11.81,5.94,.66,.47,size=9.4)
E.append(dict(type="trapezoid",x=13.09,y=5.89,w=.74,h=.56,fill="#FFFFFF",stroke=INK,sw=.9,semantic_id="thruster"))
txt("推力器",13.01,6.55,.91,.20,9.4)
edge("command_bus","prop_valve",[(12.14,4.00),(12.14,5.90)],CTRL,dash=True)
edge("prop_tank","prop_valve",[(11.35,6.18),(11.77,6.18)],INK)
edge("prop_valve","thruster",[(12.47,6.18),(13.05,6.18)],INK)
edge("thruster","orbit",[(13.83,6.18),(15.12,6.18)],INK)
txt("姿态约束推力方向；推进配置依任务决定",10.48,7.18,4.14,.20,9,color=MUTED)

# Interface legend and evidence boundary.
line(.53,8.27,1.01,8.27,POWER,sw=2);txt("电能",1.04,8.14,.55,.25,9.6,align="left")
line(1.83,8.27,2.31,8.27,DATA,sw=1.5);txt("数据 / 遥测",2.35,8.14,1.18,.25,9.6,align="left")
line(3.86,8.27,4.34,8.27,CTRL,sw=1.5,dash=True);txt("指令 / 控制",4.38,8.14,1.18,.25,9.6,align="left")
line(5.91,8.27,6.39,8.27,HEAT,sw=1.5);txt("热流",6.43,8.14,.62,.25,9.6,align="left")
txt("线交叉无节点不相连；箭头仅示功能关系，非线缆与协议定义。",7.27,8.13,8.08,.28,9.4,align="right",color=MUTED)
txt("来源：NASA 2026 SmallSat SoA；工程图语法参考 NASA NTRS Figure 2-9（历史任务设备未复用）。",.51,8.61,14.95,.24,9.2,align="left",color=MUTED)

assert set(EDGES)==REQUIRED,("source-required relation mismatch",set(EDGES)^REQUIRED)
spec=enrich_spec({"id":ID,"title":"Spacecraft subsystem functional mechanism",
                  "canvas":{"width_in":16.0,"height_in":9.15},
                  "style":{"font":"Microsoft YaHei"},
                  "semantic_edges":[list(e) for e in EDGES],"elements":E})
jsonschema.validate(spec,json.loads((ROOT/"specs/figure_spec_v76.schema.json").read_text(encoding="utf-8")))
validate_spec(spec);validate_drawn_routes(spec,REQUIRED)
(OUT/(ID+".json")).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
render(spec,OUT/(ID+".svg"),OUT/(ID+".pptx"))
print(f"Built {ID}: {len(E)} editable elements, {len(REQUIRED)} independently checked relations")
