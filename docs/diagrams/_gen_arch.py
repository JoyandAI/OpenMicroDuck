# -*- coding: utf-8 -*-
"""Generate architecture SVGs for docs/architecture.md."""
from pathlib import Path

OUT = Path(__file__).resolve().parent

FONT = "'Microsoft YaHei', '微软雅黑', 'PingFang SC', 'Noto Sans SC', sans-serif"
TEXT = "#1B3A6B"
LINE = "#4A6A88"

# role -> (fill, stroke)
C = {
    "page": ("#F7F9FC", "#D5DEE8"),
    "group": ("#F4F7FB", "#B7C6D6"),
    "client": ("#FFF4E5", "#C47B2B"),
    "transport": ("#E8F4F0", "#2F7A6B"),
    "core": ("#E8EEF8", "#3A5A9A"),
    "recover": ("#EEF6E8", "#4A7A3A"),
    "ipc": ("#F3F0E8", "#8A6A3A"),
    "train": ("#FFF8E0", "#B08A20"),
    "model": ("#F3EAF8", "#7A4A9A"),
    "hat": ("#E8F4ED", "#3D7A58"),
    "actuator": ("#FDECEE", "#A84A62"),
    "sensor": ("#E6F5F8", "#2F7A8A"),
    "audio": ("#F4EEF8", "#6B4A8A"),
    "step": ("#EAF2FB", "#3A6A9A"),
    "safety": ("#FDEEEE", "#A05050"),
    "bus": ("#FFF4E5", "#B07A2A"),
    "note": ("#F7F8FA", "#7A8A9A"),
}


def defs():
    return f"""
  <defs>
    <marker id="ao" viewBox="0 0 12 10" refX="10.5" refY="5"
            markerWidth="9" markerHeight="7.5" orient="auto" markerUnits="userSpaceOnUse">
      <polyline points="1.5,1.5 10.5,5 1.5,8.5" fill="none" stroke="{LINE}"
                stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="ao-rev" viewBox="0 0 12 10" refX="1.5" refY="5"
            markerWidth="9" markerHeight="7.5" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
      <polyline points="1.5,1.5 10.5,5 1.5,8.5" fill="none" stroke="{LINE}"
                stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
"""


def svg_open(w, h, title):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">
{defs()}
  <rect x="0" y="0" width="{w}" height="{h}" fill="{C['page'][0]}" rx="16"/>
  <text x="24" y="34" font-family="{FONT}" font-size="16" font-weight="700" fill="{TEXT}">{esc(title)}</text>
'''


def svg_close():
    return "</svg>\n"


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def box(x, y, w, h, role, lines, size=13, weight=600, rx=10):
    fill, stroke = C[role]
    cy = y + h / 2
    n = len(lines)
    lh = size + 4
    start = cy - (n - 1) * lh / 2 + size * 0.35
    texts = []
    for i, line in enumerate(lines):
        fw = weight if i == 0 else 400
        fs = size if i == 0 else max(11, size - 1)
        texts.append(
            f'    <text x="{x + w/2}" y="{start + i * lh:.1f}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="{fs}" font-weight="{fw}" fill="{TEXT}">{esc(line)}</text>'
        )
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.9"/>\n' + "\n".join(texts)
    )


def group(x, y, w, h, label=""):
    fill, stroke = C["group"]
    s = (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
    )
    if label:
        s += (
            f'\n  <text x="{x + 14}" y="{y + 22}" font-family="{FONT}" '
            f'font-size="12" font-weight="700" fill="{TEXT}">{esc(label)}</text>'
        )
    return s


def arrow(x1, y1, x2, y2, both=False, label="", lx=None, ly=None):
    start = ' marker-start="url(#ao-rev)"' if both else ""
    s = (
        f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{LINE}" stroke-width="1.6" fill="none"{start} marker-end="url(#ao)"/>'
    )
    if label:
        tx = lx if lx is not None else (x1 + x2) / 2
        ty = ly if ly is not None else (y1 + y2) / 2 - 8
        s += (
            f'\n  <text x="{tx}" y="{ty}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="11" font-weight="400" fill="{TEXT}">{esc(label)}</text>'
        )
    return s


def path_arrow(d, both=False, label="", lx=0, ly=0):
    start = ' marker-start="url(#ao-rev)"' if both else ""
    s = (
        f'  <path d="{d}" fill="none" stroke="{LINE}" stroke-width="1.6"{start} marker-end="url(#ao)"/>'
    )
    if label:
        s += (
            f'\n  <text x="{lx}" y="{ly}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="11" font-weight="400" fill="{TEXT}">{esc(label)}</text>'
        )
    return s


def legend(items, x, y):
    parts = [f'  <g font-family="{FONT}" font-size="11" fill="{TEXT}">']
    cx = x
    for role, name in items:
        fill, stroke = C[role]
        parts.append(
            f'    <rect x="{cx}" y="{y}" width="14" height="14" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        )
        parts.append(f'    <text x="{cx + 20}" y="{y + 12}">{esc(name)}</text>')
        cx += 42 + max(12 * len(name), 36)
    parts.append("  </g>")
    return "\n".join(parts)


def write(name, body):
    path = OUT / name
    path.write_text(body, encoding="utf-8")
    print("wrote", path.name, "bytes", path.stat().st_size)


# ---------------------------------------------------------------------------
# 1. software overview
# ---------------------------------------------------------------------------
w, h = 980, 430
parts = [svg_open(w, h, "软件总览：离线训练与板载执行")]
parts.append(group(24, 52, 450, 318, "开发机 / Hugging Face Jobs"))
parts.append(group(506, 52, 450, 318, "板上 Linux（RK3566 同级）"))
parts.append(box(52, 92, 394, 118, "train", [
    "mjlab + MuJoCo Warp",
    "PPO · BAM 执行器模型",
    "域随机化 · 回差仿真",
], 14))
parts.append(box(52, 248, 394, 96, "model", [
    ".onnx + manifest.json",
    "obs 61  →  act 14  ·  50 Hz",
], 14))
parts.append(arrow(249, 210, 249, 248, label="导出", lx=278, ly=232))
parts.append(box(534, 92, 394, 118, "transport", [
    "systemd 守护进程簇",
    "JSON-RPC / Unix socket",
    "mediad · tofd · padd · btd …",
], 14))
parts.append(box(534, 248, 394, 96, "core", [
    "robotd  @  50 Hz",
    "观测 → 策略 → 安全钳位 → 舵机",
], 14))
parts.append(arrow(731, 210, 731, 248, label="拉起", lx=760, ly=232))
parts.append(path_arrow("M 446 296 L 534 296", label="部署 / Hub 拉取", lx=490, ly=282))
parts.append(legend([
    ("train", "训练"),
    ("model", "策略模型"),
    ("transport", "系统服务"),
    ("core", "控制环"),
], 24, 392))
parts.append(svg_close())
write("software-overview.svg", "\n".join(parts))

# ---------------------------------------------------------------------------
# 2. daemons
# ---------------------------------------------------------------------------
w, h = 1080, 720
parts = [svg_open(w, h, "板载进程：同一套 API，多种传输")]
# 5 equally spaced client boxes (narrower so they do not overlap)
cw, gap0 = 168, 48
xs = [24 + i * (cw + gap0) for i in range(5)]
clients = [
    ("手柄 BLE/USB", "padd 入口"),
    ("手机 BLE", "配网 / 状态"),
    ("笔记本 SSH", "robotctl"),
    ("远端 WebRTC", "遥操 / 推流"),
    ("GitHub Release", "发布包"),
]
for x, (t, s) in zip(xs, clients):
    parts.append(box(x, 56, cw, 62, "client", [t, s], 13))

# transports aligned under the first four clients
transports = [
    ["padd", "手柄 → 意图"],
    ["btd", "BLE GATT 门面"],
    ["robotctl", "CLI · 全部 socket"],
    ["mediad", "相机 / 音频 / WebRTC"],
]
for x, lines in zip(xs[:4], transports):
    cx = x + cw / 2
    parts.append(arrow(cx, 118, cx, 158))
    parts.append(box(x, 160, cw, 72, "transport", lines, 14))

# IPC bar spanning the four transports
ipc_x, ipc_w = xs[0], xs[3] + cw - xs[0]
parts.append(box(ipc_x, 278, ipc_w, 56, "ipc", ["Unix socket  ·  JSON-RPC 2.0（NDJSON）  ·  同一套 robot.* / net.* / update.*"], 13, 600))
for x in xs[:4]:
    cx = x + cw / 2
    parts.append(arrow(cx, 232, cx, 278))

# cores under the IPC bar
core_w, core_gap = 256, 24
core_xs = [ipc_x + i * (core_w + core_gap) for i in range(3)]
parts.append(box(core_xs[0], 378, core_w, 96, "core", ["robotd", "50 Hz 环 · 电机 / IMU / 策略 / 安全"], 14))
parts.append(box(core_xs[1], 378, core_w, 96, "recover", ["configd", "Wi-Fi · 名字 · 配对 PIN"], 14))
parts.append(box(core_xs[2], 378, core_w, 96, "recover", ["updaterd", "验签 · 切换 · 健康门 · 回滚"], 14))
for x in core_xs:
    cx = x + core_w / 2
    parts.append(arrow(cx, 334, cx, 378, both=True))

# GitHub -> updaterd
gh_cx = xs[4] + cw / 2
upd_right = core_xs[2] + core_w
parts.append(path_arrow(
    f"M {gh_cx:.0f} 118 L {gh_cx:.0f} 426 L {upd_right} 426",
    label="https 发布包", lx=gh_cx + 52, ly=270,
))

# hardware + tofd
parts.append(box(core_xs[0], 518, core_w, 80, "bus", ["舵机总线 + 机身 IMU", "仅 robotd 可写电机"], 13))
parts.append(arrow(core_xs[0] + core_w / 2, 474, core_xs[0] + core_w / 2, 518, both=True))
parts.append(box(core_xs[1], 518, core_xs[2] + core_w - core_xs[1], 80, "sensor", ["tofd  ·  只发布、不订阅", "8×8 深度 → /run/tofd/tof.sock    mediad / robotd 只读"], 13))

parts.append(legend([
    ("client", "外部入口"),
    ("transport", "传输 / 媒体"),
    ("ipc", "控制面 IPC"),
    ("core", "运动控制"),
    ("recover", "配置 / 更新"),
    ("bus", "执行器总线"),
    ("sensor", "感知发布"),
], 28, 632))
parts.append(
    f'  <text x="28" y="678" font-family="{FONT}" font-size="12" fill="{TEXT}">'
    f'configd / updaterd / btd 在 robotd 死掉时仍可用；控制环不对其他服务做同步 RPC。</text>'
)
parts.append(svg_close())
write("daemons.svg", "\n".join(parts))

# ---------------------------------------------------------------------------
# 3. control tick
# ---------------------------------------------------------------------------
w, h = 760, 900
parts = [svg_open(w, h, "50 Hz 控制环：一拍里的数据流")]
cx, bw = 170, 420
ys = [56, 156, 268, 378, 488, 598, 720]
hs = [72, 84, 82, 82, 82, 94, 82]
roles = ["sensor", "step", "step", "model", "step", "safety", "actuator"]
labels = [
    ["sync_read", "IMU + 15 舵机 · 寄存器 124–136"],
    ["建观测  [f32; 61]", "gyro · 投影重力 · 关节 · 上拍动作 · 指令"],
    ["技能仲裁", "翻滚 > 踢 > 拾取 > 起坐 > 站 > 走"],
    ["ONNX 推理", "obs 61  →  act 14"],
    ["家位 + scale × action", "头 / 腿一阶低通"],
    ["safety.apply", "拒绝 NaN · 钳行程 · 死区（断指令则站住）"],
    ["sync_write", "写入 15 个目标位置"],
]
for y, hh, role, lines in zip(ys, hs, roles, labels):
    parts.append(box(cx, y, bw, hh, role, lines, 14))
for i in range(len(ys) - 1):
    y1 = ys[i] + hs[i]
    y2 = ys[i + 1]
    parts.append(arrow(cx + bw / 2, y1, cx + bw / 2, y2))

# intent side → 建观测
parts.append(box(24, 156, 128, 84, "client", ["意图快照", "速度 / 头 / 身体"], 12))
parts.append(arrow(152, 198, 170, 198))

parts.append(
    f'  <text x="24" y="846" font-family="{FONT}" font-size="12" fill="{TEXT}">'
    f'每秒另读电压 / 温度（寄存器 144–146）。摔倒检测只报告；limp_fall 可短暂接管关节。</text>'
)
parts.append(legend([
    ("sensor", "采样"),
    ("client", "意图"),
    ("step", "控制步骤"),
    ("model", "策略"),
    ("safety", "安全层"),
    ("actuator", "下发"),
], 24, 868))
parts.append(svg_close())
write("control-tick.svg", "\n".join(parts))

# ---------------------------------------------------------------------------
# 4–5. hardware
# ---------------------------------------------------------------------------
def hw_diagram(filename, title, compute_lines, hat_lines, bus_label, devices, extras_note):
    w, h = 980, 720
    p = [svg_open(w, h, title)]
    p.append(box(190, 52, 580, 80, "core", compute_lines, 15))

    # CSI: leave the SoC from its right side, not along a border
    p.append(box(790, 148, 164, 80, "sensor", ["图像传感器", extras_note["cam"]], 12))
    p.append(path_arrow("M 776 92 L 872 92 L 872 142", label="MIPI CSI", lx=824, ly=80))

    # HAT: vertical stub from SoC bottom, with a gap so it does not sit on the stroke
    p.append(box(360, 160, 360, 122, "hat", hat_lines, 13))
    p.append(arrow(480, 138, 480, 154, label="40-pin I²C+I²S", lx=568, ly=150))

    # I2C devices under HAT
    p.append(box(200, 330, 168, 70, "sensor", ["DToF 8×8", extras_note["tof"]], 12))
    p.append(box(392, 330, 168, 70, "sensor", ["头部 IMU", extras_note["himu"]], 12))
    p.append(box(584, 330, 196, 70, "audio", ["麦克风 / 扬声器", extras_note["audio"]], 12))
    p.append(path_arrow("M 430 288 L 284 324", both=True, label="I²C ≤400 kHz", lx=300, ly=300))
    p.append(path_arrow("M 540 288 L 476 324", both=True))
    p.append(path_arrow("M 640 288 L 682 324", both=True))

    # UART: exit SoC left-center, drop in the left gutter, land on the bus top with a gap
    p.append(path_arrow("M 184 92 L 80 92 L 80 446", both=True, label="UART TTL 半双工", lx=132, ly=270))

    # bus bar
    p.append(box(40, 452, 900, 50, "bus", [bus_label], 14))

    # bottom devices: stubs off the bus bottom, not drawn on the stroke
    xs = [40, 270, 500, 730]
    for x, (role, lines) in zip(xs, devices):
        p.append(box(x, 536, 210, 78, role, lines, 13))
        p.append(arrow(x + 105, 508, x + 105, 530, both=True))

    p.append(legend([
        ("core", "SoC"),
        ("hat", "扩展板 / 电源"),
        ("sensor", "传感器"),
        ("audio", "音频"),
        ("bus", "舵机总线"),
        ("actuator", "执行器"),
        ("model", "IMU 从机"),
    ], 40, 640))
    p.append(
        f'  <text x="40" y="688" font-family="{FONT}" font-size="12" fill="{TEXT}">{esc(extras_note["foot"])}</text>'
    )
    p.append(svg_close())
    write(filename, "\n".join(p))


hw_diagram(
    "hw-openmicroduck.svg",
    "OpenMicroDuck 硬件模块（规划）",
    ["SoC", "NPU · ISP · Wi-Fi / BT"],
    [
        "开源 HAT / 电源扩展板",
        "半双工方向电路  ·  18650 配电",
        "音频 codec  ·  I²C 扩展",
    ],
    "舵机总线  ·  Feetech 兼容协议  ·  TTL 半双工",
    [
        ("actuator", ["左腿 ×5", "ID 20–24"]),
        ("actuator", ["右腿 ×5", "ID 10–14"]),
        ("actuator", ["头颈 + 嘴 ×5", "ID 30–34"]),
        ("model", ["机身 imu_to_ft", "总线从机  ID 200"]),
    ],
    {
        "cam": "CSI 模组（未钉死）",
        "tof": "Qwiic / 0x29 一类",
        "himu": "I²C · 不进控制环",
        "audio": "经 codec · ALSA",
        "foot": "NPU 与 ISP 必备（入门算力即可，为控功耗）；换 Feetech 后须重训，契约仍为 obs 61 → act 14。",
    },
)

hw_diagram(
    "hw-microduck.svg",
    "Microduck 硬件模块（源码还原，非官方 BOM）",
    ["SoC", "Radxa Zero 3W · RK3566 · NPU · ISP"],
    [
        "Pollen RPI Robot HAT（已开源）",
        "TLV320AIC3104 @ 0x18  ·  BMI088 dormant",
        "Stemma J5 → ToF  ·  半双工 DXL PHY  ·  NP-F550",
    ],
    "Dynamixel Protocol 2.0  ·  1 Mbps  ·  单线半双工 TTL",
    [
        ("actuator", ["XL330 ×5  右腿", "ID 10–14"]),
        ("actuator", ["XL330 ×5  左腿", "ID 20–24"]),
        ("actuator", ["XL330 ×5  头 / 嘴", "ID 30–34"]),
        ("model", ["imu_to_dxl v2", "LSM6DSV16X  ID 200"]),
    ],
    {
        "cam": "IMX219 / I²C 0x10",
        "tof": "VL53L5/8CX @ 0x29",
        "himu": "规格有 · 运行时未用",
        "audio": "Mic3R + LOP 喇叭",
        "foot": "NPU / ISP 随相机与语音路径必备。imu_to_dxl 原理图未开源；头部 IMU 与控制环「只用一颗」尚未对齐。",
    },
)

print("done")
