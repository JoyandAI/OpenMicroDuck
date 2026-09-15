# OpenMicroDuck 结构说明

> 优化结构版本：**v0.1**

本仓库内的结构经过修改以适配舵机 **2909**，与之结构相同的还有 **1910** 舵机（本文以 2909 为例）。同时优化了部分结构，让它更适合 3D 打印、也更加稳定。

## 打印与装配

- 使用 Bambu Studio 直接打印已经摆盘好的 `cad/openmicroduck.3mf` 即可。
- 装配参考文件：`cad/openmicroduck-assembly-opt.stl`。
- 散件文件：`cad/psrts`。
- 结构件 BOM 表：[bom.md](bom.md)

## 结构差异（舵机）

MicroDuck 上使用的舵机大部分要拆掉副舵盘来安装。官方使用 XL330，与本仓库兼容的舵机在拆掉副舵盘后有明显的结构差异：

<img src="assets/structure/xl330-288-rear.png" height="310" />
<img src="assets/structure/2909-rear.png" height="310" />

XL330 在拆掉副舵盘后是**凹下去**的，而 2909 是**突起的**——本仓库大部分结构变化主要由这一点引起。

## 优化内容

### 头部

- **优化前**：2909 的突起部分会与后面的螺丝柱发生干涉（下图）。
<img src="assets/structure/head-opt.png" height="310" />
- **优化后**：切掉螺丝柱一部分消除干涉，不影响螺丝安装。
<img src="assets/structure/head-opt1.png" height="310" />
<img src="assets/structure/head-opt2.png" height="310" />

### 下巴

由于 3D 打印精度的缘故，下巴内的 `jaw_soft` 会与 `bottom_head_shell` 摩擦，导致开嘴困难甚至开不了嘴。已将 `jaw_soft` 缩短消除影响。

<img src="assets/structure/jaw-opt.png" height="310" />

### 脖子

加厚脖子连接件。原版仅 1 mm 厚，3D 打印风险较高。

<img src="assets/structure/neck-opt.png" height="310" />

### 躯干

**优化前**：`trunk_base` 结构薄弱，不利于 3D 打印，且舵机只有 2 个孔固定，更加脆弱。

<img src="assets/structure/trunk-org.png" height="310" />

**优化后**：

- 增厚 `trunk_base`；
- 每个舵机都有 3 个孔固定；
- 优化 `power_support` 固定方式，以舵机为基准固定；
- 修改陀螺仪固定孔，兼容 LSM6DSX 陀螺仪。

<img src="assets/structure/trunk-opt.png" height="310" />
<img src="assets/structure/trunk-opt1.png" height="310" />
<img src="assets/structure/trunk-opt2.png" height="310" />

### 胯部

**优化前**：yaw 部分由两个零件锁定舵机，3D 打印后实测稳定性较差，且不与 2909 兼容；连接的螺丝孔位还导致 `trunk_base` 舵机前方不能拧螺丝。

<img src="assets/structure/yaw-org.png" height="310" />
<img src="assets/structure/yaw-org1.png" height="310" />
<img src="assets/structure/yaw-org2.png" height="310" />

**优化后**：

- yaw 改为一体式，结构简单稳固；
- 为上述 `trunk_base` 的舵机留出拧螺丝的位置。

<img src="assets/structure/yaw-opt1.png" height="310" />
<img src="assets/structure/yaw-opt3.png" height="310" />

### 腿部

- **upper_leg**：
  - 加厚了 `upper_leg_rigidity_plate`；
  - 修改 `upper_leg` 使其兼容 2909 舵机：去掉两个定位柱，让线路更好走、更容易安装。
<img src="assets/structure/upper-leg-rigidity-plate-opt.png" height="310" />
<img src="assets/structure/upperleg-opt.png" height="310" />

- **leg**：优化使其兼容 2909。
<img src="assets/structure/leg-org.png" height="310" />
<img src="assets/structure/leg-opt.png" height="310" />

### 脚（ankle）

**优化前**：轴承从内部安装，再装到腿部模组上——除非这个部件很软，否则不论是 XL330 还是 2909 都很难安装到腿上；且底部是平的，会与舵机干涉，导致脚无法转动。

<img src="assets/structure/ankle-org.png" height="310" />

**优化后**：

- 将内部改成圆弧结构，让脚能顺利转动；
- 增加一个弹筋结构：
  1. 让 ankle 更顺利地安装到腿部模组（Leg module）上；
  2. 通过卡扣结构从外侧能更好地安装轴承；
  3. 通过 foot 限位卡扣，极大缩小轴承松脱风险。

<img src="assets/structure/ankle-opt.png" height="310" />
<img src="assets/structure/ankle-opt2.png" height="310" />
