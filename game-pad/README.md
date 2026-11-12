# 已支持的手柄

这个目录存放 **已经实际调试、验证过可用** 的手柄，以及对应的接线、配对、驱动和按键映射教程。

不是“理论兼容列表”。没有实测过的手柄不要加进来，避免让别人照着买回来不能用。

## 已验证支持

| 手柄 | 型号 / 硬件 ID | 连接方式 | 状态 | 教程 |
|---|---|---|---|---|
| 小米蓝牙手柄（一代） | VID:PID `2717:3144`；Bluetooth 3.0 经典；2×AA；HID `input-gaming` | Bluetooth Classic | 已调试验证，可配对、可映射为虚拟 Xbox 360 | [xiaomi-gamepad-guide.html](xiaomi-gamepad-guide.html) |

> VID/PID 是产品/固件级标识，同型号通常相同，**不是单台手柄唯一**。单台唯一的是蓝牙 MAC，不写入本表。

## 目录约定

后续增加新手柄时，一个手柄对应一个 HTML 教程，放在本目录下：

```text
game-pad/
├── README.md
├── xiaomi-gamepad-guide.html
└── <vendor>-<model>-guide.html
```

文件名建议使用：

```text
<厂商>-<型号>-guide.html
```

例如：

```text
8bitdo-ultimate-guide.html
dualsense-guide.html
```

## 新增手柄的要求

一个手柄要进入上面的列表，至少需要确认：

- 能在目标板子上完成配对/连接
- 能稳定输出按键和摇杆
- 有可用的 Linux 驱动或映射方案
- 能映射成 `padd` / `robotd` 可识别的标准手柄
- 教程里写清：配对、驱动、键位、验证命令、已知问题

没有跑通的手柄只放在 Issue/讨论里，不放进本目录的“已验证支持”列表。

