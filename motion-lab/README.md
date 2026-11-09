# OpenMicroDuck · 动作实验室

一个完全在本地 CPU 上运行的 OpenMicroDuck 动作回放/仿真界面。它把 MuJoCo 模型和 6 个 ONNX 策略接到一个网页里：左边是机身遥测和中文互动，中间是 MuJoCo 实时三维画面，右边是六个动作预设与手动微调。

界面参考了屏幕录制里的「动作实验室 / MOTION LAB」布局；三维模型**没有自绘**，使用的是项目现有的 MJCF 场景与 STL 网格。模型和网格随 `motion-lab/` 分发；6 个策略直接引用**仓库根目录的 `policies/`**，不再在 `motion-lab/` 内复制一份。

## 特性

- **纯 CPU**：ONNX Runtime 使用 `CPUExecutionProvider`，不需要 CUDA / 显卡。
- **真实物理**：MuJoCo 以 50 Hz 步进；每个控制周期跑一次 ONNX 推理，驱动物理关节。
- **六个仓库策略**：行走、站立、坐下/站起、捡拾、右踢、前滚翻。
- **训练用球**：右踢时按训练代码的脚前偏移把 70 mm 球放到右脚前；其他动作时球被移出场景并关闭碰撞。
- **实时三维**：MuJoCo 离屏渲染，通过 MJPEG 推流到浏览器；支持鼠标拖动旋转、滚轮缩放。只绘制完整外观，不绘制碰撞可视化网格。
- **位置示波器**：机身遥测下方是 4.2 秒滚动窗口，X/Y 两条轨迹实时显示相对原点的位移，并随幅度自动缩放量程。
- **大屏排版**：1700 px 以上自动放大字体与侧栏；1920×1080 另有紧凑纵向布局，保证三栏仍在首屏。
- **本地中文互动**：确定性指令解析，不调用云端大模型；能控制动作、头部、停止和重置。
- **无外部前端资源**：CSS、JS、字体回退全部本地提供；不依赖 CDN、Three.js 或在线模型。

## 运行环境

- Python **3.9+**（macOS / Linux 均可；Windows 需要对应平台的 MuJoCo 与 onnxruntime wheel）。
- 不需要 GPU，也不需要安装 MuJoCo 桌面程序；`mujoco` Python 包自带渲染后端。
- 首次安装依赖需要网络；运行本身不访问网络。

## 快速开始

```bash
cd OpenMicroDuck/motion-lab

./setup.sh          # 创建 .venv 并安装 mujoco / onnxruntime / numpy / Pillow
./run.sh            # 启动并自动打开 http://127.0.0.1:18765
```

也可以手动运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python server.py --open
```

启动后终端会打印实际使用的模型与策略路径：

```text
OpenMicroDuck Motion Lab  http://127.0.0.1:18765
model:    .../OpenMicroDuck/motion-lab/assets/microduck/scene.xml
policies: .../OpenMicroDuck/policies  (CPUExecutionProvider)
```

### 后台启动 / 停止

```bash
./start.sh     # 后台启动，自动打开浏览器，PID/日志写入本目录
./stop.sh      # 停止并释放端口
```

`start.sh` 启动成功后会调用 `open`（macOS）或 `xdg-open`（Linux）打开页面；如果已经有一个实例在运行，也会直接打开浏览器。无桌面环境或想手动管理页面时：

```bash
NO_OPEN=1 ./start.sh
```

`start.sh` 会自动选择可用的 Python（优先 `.venv`，也支持 `MOTION_LAB_PYTHON`）。如果 18765 已被其他进程占用，它只报错，不会误杀。停止后可再次运行 `./start.sh`。

端口或日志文件可以临时覆盖：

```bash
PORT=18766 PID_FILE=/tmp/motion-lab.pid LOG_FILE=/tmp/motion-lab.log ./start.sh
PORT=18766 PID_FILE=/tmp/motion-lab.pid ./stop.sh
```

如果 18765 被占用：

```bash
./run.sh --port 18766
# 或
.venv/bin/python server.py --port 18766 --open
```

## 界面与操作

| 区域 | 功能 |
| --- | --- |
| 中间三维视口 | MuJoCo 实时画面；拖动旋转，滚轮缩放 |
| 底部播放条 | `Ⅱ` 暂停/继续；`重置` 回到默认站姿；时间轴显示当前模式时长 |
| 右上「复位视角」 | 恢复相机默认的 3/4 视角 |
| 右侧「动作预设」 | 切换 6 个 ONNX 策略；`坐下/站起` 按钮会随状态变成「站起」 |
| 右侧「基础控制」 | 头部左/右/回正、前进速度滑杆、坐下、站起、向前走、停止 |
| 左侧「机身遥测」 | 机身高度、横滚/俯仰、横向位移、速度指令、4.2 s 位置轨迹、自动重置次数 |
| 左侧「中文互动」 | 输入或点快捷指令；演示本地指令解析 |
| 空格 / R | 暂停/继续 / 重置 |

### 中文指令示例

```text
站起来
向前走
停下
坐下
捡东西
右踢
前滚翻
左看 / 右看 / 回正
红球在哪里
重置
```

场景里带一只 70 mm、15 g 的训练用球。平时它被移到场外并关闭碰撞；触发“右踢”时，按训练代码的脚前偏移放到右脚前 9 cm、向右 4.2 cm（`BALL_OFFSET_X=0.09`、`BALL_OFFSET_ABS_Y=0.042`，z=球半径），踢完留在场上。球不参与 61 维观测，也不影响站立/行走/坐下/前滚翻。

## 六个策略

策略文件位于仓库根目录 `policies/`（`MOTION_LAB_POLICIES` 可覆盖），输入都是 `obs[1,61]`，输出 `actions[1,14]`：

| 模式 | 文件 | 行为 |
| --- | --- | --- |
| `walk` | `OpenMD_walk.onnx` | 速度跟踪，默认前进 0.12 m/s |
| `stand` | `OpenMD_stand.onnx` | 站立姿态保持 |
| `sitstand` | `OpenMD_sitstand.onnx` | 同一策略完成坐下/站起；`command[0]=1` 坐下，`0` 站起。静止站姿下先给 0.10 s 起坐脉冲，避免策略停在双稳态；站起前 0.3 s 由 sitstand 起步，随后交给 `stand` 策略收尾 |
| `ground_pick` | `OpenMD_ground_pick.onnx` | 一次捡拾循环，用相位编码 |
| `kick_right` | `OpenMD_kick_right.onnx` | 右踢：球放到右脚前，约 0.5 秒后回站立 |
| `roulade` | `OpenMD_roulade.onnx` | 前滚翻：先用 1 秒校准站姿，再翻过头顶约 1 秒，落地后回站立 |

前滚翻不是普通的持续指令，而是从 HOME 站姿开始的一次性技能；服务会在触发时回到精确的 `STAND` 关键帧（位置/朝向也回到默认原点）并让站立策略稳定 1 秒，再切到 roulade。

动作切换、暂停、重置、相机控制都通过本地 HTTP JSON API 完成；状态轮询 `GET /api/state`，三维画面走 `GET /stream.mjpg`（MJPEG）。另外提供 `GET /frame.jpg` 单帧快照，便于确认画面链路。

动作执行采用部署参数：50 Hz 控制、5 ms 物理步长 × 4；walk/kick 动作缩放 0.7，坐下/站起、捡拾、前滚翻 1.0。坐下约 1 秒落座；从完全静止的站姿直接发坐姿命令时，策略会停在“保持站立”的双稳态，因此先施加 0.10 s 的低幅起坐脉冲，再交给策略。站起先让 sitstand 抬膝 0.3 秒，再交给站立策略，避免在坐姿下卡住。

右踢和 roulade 都按 `infer_policy.py` 的做法在行为期间喂全零 13 维 command（避免残留的头部/身体命令变成分布外输入）。

前滚翻有三处专门处理，都只在翻滚期间生效，切回站立或重置时恢复（`ROULADE_*` 常量）：

- **执行器**：策略是在 BAM 舵机模型 + 3–6 个物理步指令延迟下训练的。MJCF 的软位置执行器（kp 0.55）推不过头顶，会以「头 + 双脚」卡在身体水平的姿势。翻滚时使用 kp ×4、力矩上限 ×0.8（0.77 N·m）、5 个物理步（25 ms）延迟。这组值来自无头参数扫描，30 次带扰动起步中 29 次直立落地。这是对 BAM 模型的等效近似，不是其精确复现。
- **碰撞**：保持原始全碰撞模型，和训练一样以平头顶为支点。关掉头部碰撞或另加球形碰撞体都会让动作偏离训练环境，翻向侧面。
- **结束条件**：按身体状态而不是计时器。向前转过 240° 且机身回正（`up > 0.8`）就交回站立，通常约 1 秒，与部署配置的 `roulade_duration: 1` 一致；`roulade_duration` 只是卡住时的放弃时限（3 秒）。

## 部署 JSON 里哪些参数进了仿真

`../policies/OpenMD_policy_settings_20261028.json` 是 **robotd 部署配置 + 模型索引**，不是 MuJoCo 仿真配置；`server.py` 目前不直接解析这个文件，而是把其中真正影响动作的已解析值手工落到代码里。这样做是为了避免把板端路径、robotd 专用字段和 `null` 默认值带进仿真。

| JSON 字段 | 仿真里是否使用 | 说明 |
| --- | --- | --- |
| `policy.*.onnx` 槽位 | 使用 | 决定六个动作各自加载哪个 ONNX |
| `action_scale` / `standing_action_scale` / `ground_pick_action_scale` / `roulade_action_scale` | 使用 | 对应 `ACTION_SCALES`：walk/kick `0.7`，其余 `1.0` |
| `kick_duration` | 使用 | 右踢 `0.5 s` 后交回站立 |
| `roulade_duration` | 不原样使用 | 部署值 `1.0 s`；这里改为状态判定结束（实测约 1.0 s），该字段对应的旋钮只作放弃时限，默认 3 s |
| `home_deg` | 间接使用 | 和 MJCF `STAND` 关键帧、ONNX 里的 default pose 对齐；JSON 有 15 项（含 `mouth`），策略是 14 项，不能直接拿来当观测默认值 |
| `head_lowpass` / `legs_lowpass` | 未使用 | 真实舵机目标的一阶滤波；加进仿真会改变所有动作轨迹，需要重新验证，当前先保持原始策略输出 |
| `gain` | 未使用 | robotd 伺服环增益，和 MJCF 的 `actuator_gainprm`（本模型约 0.55）不是同一量纲，不能直接把 6 赋进去 |
| `voltage_adapt` | 未使用 | 真实电池电压自适应；仿真没有电池模型 |
| `limp_fall` | 未使用 | 真实机器人跌倒卸力逻辑；仿真用自己的失稳自动复位 |
| `stand_on_zero_command` | 不用 | 网页里站立/行走是显式模式，不走“twist 为零自动切站立”的 robotd 逻辑 |
| `kick_left` | 不用 | 配置本身就是 `none`，只有右踢 |
| `models.*` 路径 / sha256 / notes | 不用 | 溯源信息，不参与控制 |

所以：**ONNX 负责“看到状态后输出 14 个关节目标”，JSON/代码负责“把机器人、球、地面、接触、时序和模式切换摆成策略训练时见到的样子”**。两者不是替代关系；环境不对，同一个 ONNX 会输出完全不同的动作。

## 目录结构

```text
motion-lab/
├── server.py           # HTTP 服务、MuJoCo 仿真、ONNX 推理、MJPEG
├── assets/microduck/   # 完整 MJCF + STL 模型（随应用分发）
├── （仓库根目录 `../policies/` 提供 6 个 ONNX 策略）
├── static/
│   ├── index.html      # 三栏「动作实验室」布局
│   ├── style.css       # 暖色编辑部/实验室风格
│   └── app.js          # 状态轮询、位置示波器、控制、聊天、相机拖动
├── tests/              # 无头回归测试（外观部件、前滚翻、其他动作）
├── requirements.txt
├── setup.sh
├── run.sh
└── README.md
```

## 三维模型从哪里来

- MJCF：`assets/microduck/scene.xml`
- 网格：`assets/microduck/assets/` 下的 STL
- 策略：`../policies/OpenMD_*.onnx`

模型和网格随 `motion-lab/` 分发；6 个策略从仓库根目录 `policies/` 加载，**不再在 motion-lab 内复制**。

策略元数据里的 14 个 `joint_names`、`[1,61] -> [1,14]` 形状和 `default_joint_pos` 与 MJCF 的关节顺序、`STAND` 关键帧一致；服务启动时会校验这些契约，服务和模型之间没有做关节重映射。三维模型不是通用模型：它绑定这套关节树、默认姿态、碰撞体和执行器参数，换成别的鸭子或别的 MJCF 变体就不能假设动作仍然正确。

`server.py` 对场景做了四处显示层处理和两处运行时物理/接触设置：

1. 把训练场景的棋盘格地面改成深色工作室地面，让白色机身更清楚。
2. 降低方向光强度、去掉高光，并保留少量头灯作为补光，避免白色外壳过曝。
3. 渲染只启用地板（geom group 0）和完整外观（geom group 2）。group 3 是碰撞可视化子集，单独打开会像“模型炸开”，不能作为外观。
4. 把 24 个被外壳完全遮住的内部件（轴承、PCB、电池、电机座、头颈机构）移到不渲染的 group 4；物理碰撞不受影响，外观看不出缺失。这些部件按「body + mesh + 序号」定位（`OCCLUDED_GEOMS`），找不到时启动直接报错；不要用数字 geom ID，往 MJCF 加 geom 会让 ID 偏移，隐藏掉外壳。

运行时还会按动作切换碰撞掩码：kick 只保留脚、腿、髋、机身的 floor-only 接触；其他动作（包括前滚翻）都用 MJCF 原始 full collision。碰撞几何本身（STL / MJCF 文件）没有被改写，只是运行时 `geom_contype` / `geom_conaffinity` 的取舍。

## 实现说明

```text
浏览器
  ├─ GET /              → index.html
  ├─ GET /style.css     → 本地样式
  ├─ GET /app.js        → 本地交互
  ├─ GET /api/state     → 150 ms 轮询遥测（位置示波器数据源）
  ├─ GET /stream.mjpg   → multipart MJPEG 三维画面
  └─ GET /frame.jpg     → 单帧 JPEG（首屏和排障）

server.py
  ├─ 仿真线程：0.02 s 周期，4 × mj_step(0.005)，每周期一次 ONNX 推理
  ├─ 动作：walk/kick 使用部署缩放 0.7，其余动作 1.0
  ├─ 渲染线程：MuJoCo Renderer 只画地板 + 视觉网格（不画碰撞副本）→ JPEG → MJPEG
  └─ HTTP 线程：标准库 ThreadingHTTPServer，无 Flask 依赖
```

设计取舍：

- **渲染完整外观并去掉内部遮挡件**：group 2 才是完整机器人外观，group 3 只是碰撞可视化的子集（单独显示会像模型炸开）。默认渲染 floor（group 0）+ group 2；再把 24 个被外壳完全遮住的内部件移到 group 4。外观部件一个不少。物理接触按动作使用 full / support 两套掩码，见上一节。
- **不使用 Flask**：标准库足够，部署更轻；代价是路由和静态文件处理都要手写。
- **不使用 WebSocket**：遥测轮询 + MJPEG 对本地回放足够，且浏览器兼容性好。
- **不使用云端语音/大模型**：中文指令由本地规则解析；界面上的「开始录音」使用浏览器可选的 Web Speech API，是否可用、是否走系统语音服务取决于浏览器，不是本项目的必需路径。直接输入文字总能工作。
- **相机采用 MuJoCo free camera**：网页拖动改变 `azimuth/elevation/distance`，服务端把参数应用到渲染相机；观察点平滑跟随机身，前滚翻和行走不会跑出画面。

## 调参

一次实测的示例调参快照见 [EXAMPLE_TUNING.md](EXAMPLE_TUNING.md)；它是示例，不是项目默认值。

```bash
# 更流畅、画面略小（默认就是 840×472 / 20 FPS）
.venv/bin/python server.py --width 720 --height 405 --fps 20

# 更清晰、CPU 占用更高
.venv/bin/python server.py --width 960 --height 540 --fps 20

# 换端口
.venv/bin/python server.py --port 18766
```

在当前测试机上，默认 840×472、20 FPS 目标下实际渲染约 16–20 FPS；960×540 会明显下降（和 CPU 负载有关）。MuJoCo 的 CPU 软件光栅化是主要开销，仿真本身稳定在约 50 Hz，动作时间不会因渲染帧率变化。

### 模型精度 / FP16 / INT8 可行性

结论：**降低 ONNX 精度对当前帧率几乎没有帮助**。实测一次 `[1,61] → [1,14]` MLP 策略推理约 **0.24 ms**，50 Hz 控制下只占约 1% 的墙钟时间；`_advance`（推理 + 4 次物理步进）约 **1.3 ms/控制周期**，而一帧 840×472 的离屏渲染 + JPEG 约 **30–50 ms**。瓶颈在 MuJoCo 渲染，不在策略网络。

- `CPUExecutionProvider` 对 FP16 通常没有高效原生 kernel，很多算子会回退/转成 FP32，速度不会提升；FP16 还要求模型数值范围安全。
- INT8 需要校准数据和量化算子支持；这个策略是闭环控制，量化误差会直接改变动作轨迹，风险和验证成本远高于收益。
- 物理精度也不是“ONNX 精度”：MuJoCo 的碰撞/积分精度由模型和求解器参数决定，降低它反而会改变动作是否成功。
- 真正有效的顺序是：**只渲染完整外观 → 去掉被遮挡的内部件 → 降低离屏分辨率 → 降低目标 FPS / JPEG 质量**。前两项已经内置；后两项可用 `--width`、`--height`、`--fps` 调。

## 常见问题

**浏览器打开是空白/一直转圈？**

先直接访问 `http://127.0.0.1:18765/api/state`，确认返回 JSON；再访问 `/frame.jpg` 看是否能拿到单帧。若 `stream.mjpg` 被代理或浏览器扩展拦截，单帧接口可用于排查。

**端口被占用？**

```bash
lsof -nP -iTCP:18765 -sTCP:LISTEN
# 换端口启动
./run.sh --port 18766
```

**macOS 上 `pip install mujoco` 尝试源码编译？**

说明当前 `python3` 是错误架构（例如 x86_64 Python 跑在 arm64 机器上）。请使用原生 arm64 的 Python 3.9+ 创建 venv；本项目在原生 Python 3.9 上验证通过。

**没有图形界面（SSH/服务器）怎么办？**

MuJoCo 使用离屏渲染，不需要桌面窗口；但仍需要系统具备 OpenGL/OSMesa 等离屏渲染能力。无显示环境建议在本地电脑运行，或使用带 GPU/EGL 的 Linux 容器并确认 `mujoco.Renderer` 可用。

## 已验证

- 6 个 ONNX 全部以 `CPUExecutionProvider` 加载。
- `/api/state`、`/api/mode`、`/api/twist`、`/api/head`、`/api/sit`、`/api/pause`、`/api/reset`、`/api/camera`、`/api/camera/reset`、`/api/chat` 均可用。
- `stand` / `walk` / `sitstand` / `ground_pick` / `kick_right` / `roulade` 都做过实际 rollout：坐姿高度约 58 mm、站起约 115 mm；前滚翻完整翻过头顶约 1 秒，恢复站立到约 115 mm（终点约在起点前方 58 cm、横向 30 cm，每次朝向略有差异）。
- 回归测试：`python tests/test_motion_lab.py`。
- 六个策略的切换、计时回站立和自动跌倒重置逻辑已做 HTTP 回归。
- 页面在 1920×1080、2560×1440、3840×2160 下检查过全宽布局；1700 px 以上启用大屏字号，1920×1080 启用紧凑纵向布局。1180/860/560 px 的响应式断点保留；三维视口使用随应用分发的 MJCF/STL 渲染。
- 位置示波器在站立、坐下、行走时均能刷新；窗口 4.2 s，X/Y 轨迹和量程会自动更新。
- 三维画面现在显示完整外观（不再是碰撞网格拼片）；右踢会真实推动球（球从右脚前约 0.09 m 滚到约 0.34 m），前滚翻先校准 1 秒、翻滚约 1 秒后切回站立。

## License / 归属

界面与本地服务代码为本项目新增；机器人模型、网格、策略来自 OpenMicroDuck 仓库，遵循其原有许可。使用或再分发前请确认上游仓库的许可证与资产归属。
