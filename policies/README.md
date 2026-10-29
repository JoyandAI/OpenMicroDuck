# OpenMD policies（HD-1910 / robotd 部署用）

这个目录是 OpenMD 稳定版策略的**可携带副本**：5 个可部署的 ONNX + 一份把索引路径改到本目录的部署参数 JSON。训练 checkpoint（`.pt`）不随本目录分发，这里只放部署要用的 ONNX。

- 策略索引与部署参数：`OpenMD_policy_settings_20261028.json`
- 命名规则：`OpenMD_<角色>.onnx`，角色沿用原 JSON 的键。
- 槽位分工（walk 槽 = walk、stand 槽 = velstand）与 sitstand 未发布的原因见下文两节。

## 文件清单

| 角色 | ONNX | 字节 | sha256（前 12 位） |
|---|---|---|---|
| walk | `OpenMD_walk.onnx` | 793890 | `24267be20b81` |
| stand | `OpenMD_stand.onnx` | 793842 | `783951c98a74` |
| ground_pick | `OpenMD_ground_pick.onnx` | 804473 | `c3eff49abe24` |
| kick_right | `OpenMD_kick_right.onnx` | 793722 | `31ce29f29a76` |
| roulade | `OpenMD_roulade.onnx` | 793717 | `3c54f3b3111c` |
| ~~sitstand~~ | ~~本次不发布（见"sitstand 暂不发布"）~~ | — | — |

五个 ONNX 的 sha256 与原始 `OpenMD_policy_settings_20261028.json` 里 `models.*.sha256` **逐字节一致**，即搬过来的就是当时部署的那一份。



## 槽位分配：walk 槽放 walk 模型，stand 槽放 velstand 模型

这套槽位没有照抄官方的配法（官方是 walk 槽管走路、stand 槽放 standup，或者 walk 槽放 velstand、stand 槽留空）。这里的分配是：walk 槽给 `OpenMD_walk.onnx`（`openmd_velocity`，model_9999），stand 槽给 `OpenMD_stand.onnx`（`openmd_velstand` r3 walkpt orig，model_17500），再配 `stand_on_zero_command=true` —— 零 twist 交给 velstand 站立，非零 twist 交给 walk 行走。

这样配的原因是现阶段 velstand 单独承担走路还不够好，这一路仍在优化中；用 walk 管行走、velstand 管站立的分工，实际效果更好。等后续 velstand 训练到能独立覆盖行走，直接把 velstand 放到 walk 槽、stand 槽置为 none 即可，其余参数不用动。

## sitstand 暂不发布

目前训练出来的 sitstand 效果不达标，所以这次不放进本目录（`policy.sitstand` 置为 `"none"`，`models.sitstand` 为 `null`）。后续训练出可用的版本会补充上来，届时按文末"恢复 sitstand"一节放回 `OpenMD_sitstand.onnx` 并把槽位改回文件名即可。

## 部署参数（`policy.resolved`，robotd 0.13.3）

| 参数 | 生效值 | 说明 |
|---|---|---|
| `action_scale` | 0.7 | 行走 / 默认网路缩放 |
| `standing_action_scale` | 1.0 | stand 网路缩放（walk 不走这个 key） |
| `stand_on_zero_command` | true | 零 twist → stand；非零 twist → walk m9999 |
| `head_lowpass` / `legs_lowpass` | 0.5 / 0.7 | 原 JSON 为 null，取 robotd 默认 |
| `gain` | 6 | 同上，null → 6 |
| `voltage_adapt` | false | null → false |
| `ground_pick_action_scale` | 1.0 | 未设 → 1.0 |
| `roulade_action_scale` | 1.0 | |
| `roulade_duration` | 1.0 s | |
| `kick_duration` | 0.5 s | 未设 → 0.5 |
| `limp_fall` | false | 不做自动跌倒恢复 |
| `sitstand` | none | 本目录不提供（效果不达标） |
| `kick_left` | none | 只有右踢 |

HOME 帧（`policy.home_deg`）：neck_pitch/head_pitch 20°，hip_roll −5/+5°，hip_pitch −26.2/+26.2°，ankle +26/−26°，knee 0°。列表有 15 项，因为板端配置还包含 `mouth` 关节；按原样保留，未做删改。

## 用法

JSON 里所有路径都相对于本目录（`base_dir: "policies"`），把整个 `policies/` 拷到别处即可直接用；原始板端绝对路径保留在每个模型的 `board_path` 字段里备查。

```bash
# 部署到机器人
sudo robotctl policy add walk <owner>/<repo>@policies/OpenMD_walk.onnx
# 或直接把文件拷到板端 /opt/robot/policies/trials/<name>/ 再改 robotd.toml

# 本地 CPU 复演（不碰真机）
uv run scripts/infer_policy.py --walking policies/OpenMD_walk.onnx --standing policies/OpenMD_stand.onnx
```

ONNX 形状固定 `[1,61] -> [1,14]`，观测归一化已烘进图里；**不要**手写脚本从训练 checkpoint 直接转 ONNX 覆盖这些文件。



## 复核命令

```powershell
# 每个 ONNX 能加载、形状正确、输出有限
python - <<'PY'
import onnxruntime as ort, numpy as np, glob
for p in sorted(glob.glob("policies/*.onnx")):
    s = ort.InferenceSession(p, providers=["CPUExecutionProvider"])
    o = s.run(None, {"obs": np.zeros((1, 61), np.float32)})[0]
    print(p, s.get_inputs()[0].shape, "->", o.shape, "finite:", np.isfinite(o).all())
PY
```
