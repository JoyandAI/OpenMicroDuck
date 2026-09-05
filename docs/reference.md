# 参考项目

Microduck 相关资源散落在 GitHub 多个组织和 Hugging Face 三类资源（Space / Model / Dataset）里。

本文整理自社区相关的项目，统计数据可能会随时间变化不定期更新。

本仓库（[JoyandAI/OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck)）受 Hugging Face / Pollen Robotics 的 Microduck 启发，走完全开源路线；与官方及下列社区项目无隶属关系。

难免有误不全之处，请多核实。

---

## 官方仓库（pollen-robotics）


| 仓库                                                                                | Star | 许可         | 简介                                                                                    |
| --------------------------------------------------------------------------------- | ---- | ---------- | ------------------------------------------------------------------------------------- |
| **[microduck](https://github.com/pollen-robotics/microduck)**                     | 7356 | Apache-2.0 | 板载软件：`robotd` 50Hz 控制环、`mediad` 摄像头/WebRTC、`padd` 手柄、更新器。设备路径、I²C 地址、寄存器写死在代码里        |
| **[microduck_rl](https://github.com/pollen-robotics/microduck_rl)**               | 1758 | Apache-2.0 | RL 训练环境（mjlab / MuJoCo Warp），含 PPO、BAM 执行器模型、回差仿真与域随机化；**47 个 STL + 完整 MJCF**。需要 CUDA |
| **[elec_RPI_Robot_HAT](https://github.com/pollen-robotics/elec_RPI_Robot_HAT)**   | 24   | Apache-2.0 | HAT 板完整 KiCad 9 工程：原理图、PCB、Gerber、BOM、贴片坐标、STEP；`production/` 可直接打样（4 层板）             |
| **[lib_KiCAD](https://github.com/pollen-robotics/lib_KiCAD)**                     | 3    | —          | Pollen 的 KiCad 符号 / 封装 / 3D 库。打开上面工程必须先装，否则一片未解析符号                                    |
| [rustypot](https://github.com/pollen-robotics/rustypot)                           | 57   | Apache-2.0 | Dynamixel 通信库；运行时靠它跟舵机说话，`xl330.rs` 里是完整寄存器表                                          |
| [microduck-gst-plugins](https://github.com/pollen-robotics/microduck-gst-plugins) | 14   | Apache-2.0 | 预编译 aarch64 GStreamer 插件：Rockchip MPP 硬件编码器 + gst-plugins-rs WebRTC，供板载 `mediad` 使用   |
| `duck_detector`                                                                   | —    | —          | 不公开（404）。官方文档引用过的 NPU 检测模型训练仓，外部访问不到                                                  |




### 官方站点与文档


| 名称                                                                                                                 | 简介                                                                       |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| [产品页](https://pollen-robotics.com/microduck)                                                                       | 规格、配色与发布说明                                                               |
| [商店](https://store.pollen-robotics.com/products/microduck)                                                         | 官方预售，定价 $399                                                             |
| [新闻稿套件](https://pollen-robotics.com/microduck/press-kit/)                                                          | 规格表、照片与下载素材                                                              |
| [Meet Microduck](https://pollen-robotics.com/microduck/blog/introducing-microduck/)                                | Pollen 发布博文                                                              |
| [文档索引](https://github.com/pollen-robotics/microduck/blob/main/docs/README.md)                                      | 运行时仓库内全部文档入口                                                             |
| [架构说明](https://github.com/pollen-robotics/microduck/blob/main/docs/design/architecture.md)                         | 守护进程、控制环、策略与更新器如何拼在一起                                                    |
| [策略通道设计](https://github.com/pollen-robotics/microduck/blob/policy-hub-design/docs/design/policy-channel-design.md) | 社区策略如何上机：Hub 仓库布局、`manifest.json` 契约、`robotctl policy` 命令（仍在分支，未合入 main） |
| [路线图](https://github.com/pollen-robotics/microduck/blob/main/docs/project/roadmap.md)                              | 里程碑 M1–M9，含 Hub 模型通道（M8）与自主大脑（M9）                                        |


---



## Hugging Face



### 模拟器与可视化


| 名称                                                                                                           | Likes | 简介                                                        |
| ------------------------------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------- |
| **[pollen-robotics/microduck-simulator](https://huggingface.co/spaces/pollen-robotics/microduck-simulator)** | 418   | 官方网页沙盒：MuJoCo WASM + onnxruntime-web，50Hz 跑真实策略，支持手柄与轮滑变体 |
| [mishig/microduck-anatomy](https://huggingface.co/spaces/mishig/microduck-anatomy)                           | 10    | 交互式解剖可视化，可分阶段聚焦零件与爆炸装配                                    |
| [multimodalart/microduck-ar](https://huggingface.co/spaces/multimodalart/microduck-ar)                       | 1     | 官方沙盒的 WebXR 适配：真实地面放置 + 地面拾取                              |
| [ysharma/gr-workflow-microduck-lab](https://huggingface.co/spaces/ysharma/gr-workflow-microduck-lab)         | 1     | 把一段自然语言例程编排成技能序列再回放                                       |
| [osolmaz/microquack](https://huggingface.co/spaces/osolmaz/microquack)                                       | 1     | 程序化机器人语音，Rust 核心经 WASM 在浏览器里实时合成                          |




### 策略模型


| 名称                                                                                                                | Likes | 简介                                               |
| ----------------------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------ |
| **[pollen-robotics/microduck-policies](https://huggingface.co/pollen-robotics/microduck-policies)**               | 8     | 官方 9 个 ONNX（站立、行走、起坐、踢球、地面拾取、翻滚、轮滑等），不必克隆运行时即可拉取 |
| [RemiFabre/microduck-flamingo-cycle](https://huggingface.co/RemiFabre/microduck-flamingo-cycle)                   | 23    | 单脚站立并可左右切换                                       |
| [joanfox/microduck-happy-hop](https://huggingface.co/joanfox/microduck-happy-hop)                                 | 3     | 跳跃                                               |
| [q2p/microduck-beak-throw](https://huggingface.co/q2p/microduck-beak-throw)                                       | 2     | 用喙把物体抛出                                          |
| [fffiloni/microduck-polite-bow-b1d864](https://huggingface.co/fffiloni/microduck-polite-bow-b1d864)               | 2     | 鞠躬                                               |
| [fffiloni/microduck-moonwalk-backward-55e6af](https://huggingface.co/fffiloni/microduck-moonwalk-backward-55e6af) | 1     | 向后太空步                                            |
| [RemiFabre/microduck-rough-walk-g](https://huggingface.co/RemiFabre/microduck-rough-walk-g)                       | 1     | 崎岖地面行走（g）                                        |
| [HannesVonEssen/microduck-running](https://huggingface.co/HannesVonEssen/microduck-running)                       | 1     | 奔跑                                               |
| [Nupr-Haokun/microduck-step-up-head-brake](https://huggingface.co/Nupr-Haokun/microduck-step-up-head-brake)       | 1     | 用头当临时刹车跨 25mm 台阶，再恢复直立                           |


上游提供 `uv run publish`，可以把自训策略发到 Hub。契约约定：每个 Hub 仓库一份 `.onnx` + `manifest.json`（观测/动作维数、模型 API 版本、机型兼容性）。更多社区步态见 [Hub 搜索](https://huggingface.co/models?search=microduck)。

### 数据集


| 名称                                                                                                         | Likes | 简介                     |
| ---------------------------------------------------------------------------------------------------------- | ----- | ---------------------- |
| [craigm26/microduck-stairs-challenge](https://huggingface.co/datasets/craigm26/microduck-stairs-challenge) | 1     | 爬楼梯打分基准，物理模型按哈希钉死（仅仿真） |


> 数据集集中出现在 2026 年 9 月初，是社区从「玩」转向「训」的信号。

---



## 社区项目



### 工具、Agent 与应用


| 仓库                                                                                      | Star | 简介                                                                             |
| --------------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------------------------ |
| [rokbenko/quackd](https://github.com/rokbenko/quackd)                                   | 160  | 自然语言目标规划守护进程：用现有技能编排任务。自带模拟器、`.duck` 任务文件、安全规则、MCP，已上 PyPI；0.4 起也驱动其他小机器人      |
| [jonathanhawkins/microduck-lab](https://github.com/jonathanhawkins/microduck-lab)       | 78   | 在普通 Mac 上训 RL，不需要 CUDA；同一套 MJCF 与 61/14 契约，带浏览器实时查看                            |
| [joeynyc/awesome-microduck](https://github.com/joeynyc/awesome-microduck)               | 75   | 英文策展列表：软件、模拟器、策略、Agent 工具与媒体报道                                                 |
| [craigm26/duckkit](https://github.com/craigm26/duckkit)                                 | 6    | 纯 Swift 包：真实 ONNX + 61 维观测 @ 50Hz，含运动学、协议类型和 Linux 测试                          |
| [aj-dev-smith/microduck-mcp](https://github.com/aj-dev-smith/microduck-mcp)             | 2    | MCP 驱动 CPU MuJoCo 仿真鸭，工具输出含渲染画面，带 Agent 调试页（仅仿真）                               |
| [joeynyc/microduck-mcp](https://github.com/joeynyc/microduck-mcp)                       | 1    | 按真机 `robotd` 架构做的 MCP：mock / MuJoCo / Unix socket / SSH 同一套工具，带安全层。硬件传输尚未在真机验证 |
| [jvpflum/microduck-lab](https://github.com/jvpflum/microduck-lab)                       | 1    | 面向 NVIDIA DGX Spark 的可复现训练工作区，把官方运行时、模拟器和 `microduck_rl` 钉成子模块                 |
| [carpentry-liu/rl-physics-overlay](https://github.com/carpentry-liu/rl-physics-overlay) | 1    | 浏览器模拟器的无依赖遥测叠加层：关节力、力矩、接触与学习信号（中英）                                             |
| [kgediya/specs-microduck](https://github.com/kgediya/specs-microduck)                   | 1    | 用 Snap Spectacles 手势遥操作仿真鸭，镜内显示遥测                                              |
| [ngxson/wicroduck](https://github.com/ngxson/wicroduck)                                 | 1    | 整条回路塞进 URL：浏览器 WASM 步进真实 MJCF，无 Python、无后端。仿真已通，浏览器内训练仍是目标                     |


站点（非 GitHub 仓）：[MicroduckHub](https://microduckhub.com)（社区策略浏览器）、[uDuck Registry](https://uduck-registry.pages.dev)（策略描述符目录）、[OpenCastor 集成](https://docs.opencastor.com/robots/microduck/)、[Strands Robots provider](https://strands-labs.github.io/robots/policies/microduck/)、[microquack 网页](https://osolmaz.github.io/microquack/)。

### 训练与仿真


| 仓库                                                                                                        | Star | 简介                                                           |
| --------------------------------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------ |
| [Vottivott/microduck-playground](https://github.com/Vottivott/microduck-playground)                       | 30   | `microduck_rl` 的独立续作：可复现实验、策略演示、可打印附加件，停留在上游某次提交上             |
| [AlexBodner/microduck-tracking](https://github.com/AlexBodner/microduck-tracking)                         | 13   | 基于 roboflow/trackers 的多目标跟踪：在干扰物中锁定并取回一只球                    |
| [metahubaifeel/microduck-rl-on-thor](https://github.com/metahubaifeel/microduck-rl-on-thor)               | 12   | 让官方训练栈跑在 aarch64 CUDA（Thor / DGX Spark / Jetson），坑已在真机核对（中英） |
| [kabilankb/isaaclab-microduck](https://github.com/kabilankb/isaaclab-microduck)                           | 8    | Isaac Lab 3.0 / Newton MJWarp：运动、奔跑、踢球、双机对打，并与 mjlab 基线做 A/B |
| [Macmachi/microduck-rl-genesis](https://github.com/Macmachi/microduck-rl-genesis)                         | 3    | Genesis 移植行走任务，面向 AMD/ROCm；执行器模型相对上游 bit-exact               |
| [osrbot/microduck-ros2-isaac](https://github.com/osrbot/microduck-ros2-isaac)                             | 2    | ROS 2 Jazzy + Isaac Sim 教程：RViz 关节控制，USD 里跑官方行走策略            |
| [Lulzx/microduck-backflip](https://github.com/Lulzx/microduck-backflip)                                   | 1    | 可复现后空翻任务，含评估集、实验日志和明确安全门（仅仿真）                                |
| [selinayfilizp/microduck-courier](https://github.com/selinayfilizp/microduck-courier)                     | 2    | 公寓场景里的拾-运-放，含策略、rollout 与遥测（仅仿真）                             |
| [yangyihai/Microduck_RL_Ball_Follow](https://github.com/yangyihai/Microduck_RL_Ball_Follow)               | 1    | MuJoCo Warp 追球任务 + 指令块契约层 + 拖球演示（仅仿真）                        |
| [Liyucheng1997/318_lab-microduck-simulator](https://github.com/Liyucheng1997/318_lab-microduck-simulator) | 1    | 官方沙盒分叉，带自训垂直跳策略；[在线演示](https://duck.liyucheng.me)            |




### 复刻与硬件


| 仓库                                                                                                | Star | 简介                                                                            |
| ------------------------------------------------------------------------------------------------- | ---- | ----------------------------------------------------------------------------- |
| **[JoyandAI/OpenMicroDuck](https://github.com/JoyandAI/OpenMicroDuck)**（本仓库）                      | 32   | 完全开源复现：国产供应链、图纸 / PCB / BOM / 软件栈规划全公开                                        |
| [fanhao375/microduck-replica](https://github.com/fanhao375/microduck-replica)                     | 471  | 从官方 MJCF/STL/Rust 反推装配图、CAD 装配体、紧固件清单与电控方案（Radxa Zero 3W、TTL 总线、两块自制板）；未对真机核验 |
| [IronSpiderMan/MicroDuckModels](https://github.com/IronSpiderMan/MicroDuckModels)                 | 34   | Three.js + R3F 浏览器模拟器，MuJoCo WASM + 本地 ONNX，跑齐官方 9 个策略（中英 README）             |
| [ScrapMeta/microduck-diy](https://github.com/ScrapMeta/microduck-diy)                             | 18   | 「一个月手搓」日志：公开仿真网格 + 打印件，分阶段文件和零件清单（中文）                                         |
| [SaberOnGo/open-microduck](https://github.com/SaberOnGo/open-microduck)                           | 7    | 中英双语硬件/软件栈文档，明确写了官方硬件未开源；目前以文档为主，无 PCB 文件                                     |
| [boris721/microduck-3d](https://github.com/boris721/microduck-3d)                                 | 6    | 从官方模拟器提取的 STL + MJCF                                                          |
| [lingzolabs/microduck-hardware-replica](https://github.com/lingzolabs/microduck-hardware-replica) | 1    | FreeCAD 多件装配、可打印网格、规划阶段 BOM；中文，声明无隶属、未核验                                      |
| [Shiyao-Huang/ChinaMicroDuck](https://github.com/Shiyao-Huang/ChinaMicroDuck)                     | 1    | 复刻参考库：四条成本化制造路线对照、官方资产许可审计、环境核验报告、官方文档中译                                      |
| [Rhoban/microban](https://github.com/Rhoban/microban)                                             | 283  | **不是 Microduck**，但用同一块 HAT。19×XL330 + Pi Zero 2W，完整公开 BOM 与装配指南（约 $567）       |




### 谱系与历史

Microduck 从 Antoine Pirrone 的开源硬件 [Open Duck Mini](https://github.com/apirrone/Open_Duck_Mini) 演进而来，两边仍共享 Discord、执行器模型和 sim-to-real 经验。


| 仓库                                                                                    | Star | 简介                                                                                                                          |
| ------------------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------- |
| [apirrone/Open_Duck_Mini](https://github.com/apirrone/Open_Duck_Mini)                 | 3965 | 开源硬件前身：BOM、CAD，以及最初的 mjlab 训练工作                                                                                             |
| [apirrone/Open_Duck_Mini_Runtime](https://github.com/apirrone/Open_Duck_Mini_Runtime) | 172  | Open Duck Mini 的 Raspberry Pi 运行时                                                                                           |
| [TommyZihao/microduck_runtime](https://github.com/TommyZihao/microduck_runtime)       | 3    | 原型机运行时公开镜像（原仓 `apirrone/microduck_runtime` 已私有）。原型机 IMU 是 BNO055 走 I²C，不是现在的 `imu_to_dxl`；已被 `pollen-robotics/microduck` 取代 |
| [apirrone/microduck_maploc_rs](https://github.com/apirrone/microduck_maploc_rs)       | 6    | 原型机用的 ToF 子图 SLAM / 重定位 / A（Rust）。目标运行时未公开，crate 本身开源                                                                       |


