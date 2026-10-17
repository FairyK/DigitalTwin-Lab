# Day011 学习文档：事件驱动、动态材质与 UE 资源管理

> 计划学习日：Day011  
> 建议时长：理论 60–90 分钟，实验 2–3 小时  
> 环境：Unreal Engine 5.6，项目 `E:\DT\DigitalTwinLab`  
> 前置完成：Day010 理论；`BP_Motor`、`ApplyMotorData`、`BP_MotorManager` 已创建；`MotorMap` 配置与设备 ID 查找、未知 ID 测试已完成；Tick 与事件驱动对比已完成。  
> 本日目标：实现故障事件通知、单台电机独立的动态材质表现，并理解 MPC 与软/硬引用的后续学习边界。

---

# Part A — 理论补足

## 1. 从“对象更新”走向“系统协作”

你当前已经有三个重要部件：

1. `BP_Motor`：代表单台电机，保存温度、转速、运行、故障状态，并提供 `ApplyMotorData`。
2. `BP_MotorManager`：维护设备 ID 与电机 Actor 引用的映射，负责找到正确对象。
3. 外部数据链路的基础：Python/JSON/MQTT 的数据格式与发布订阅概念。

它们的关系是：

```text
数据输入 → Manager 根据 device_id 找 Actor
                   ↓
            ApplyMotorData
                   ↓
           状态变量被更新
                   ↓
        事件通知 / 材质 / UI
```

要注意：你目前还没有完成真正的 MQTT → UE 通信集成。Manager 的存在只解决 UE 内部的对象定位，不会自动跨进程取到 Python 的 MQTT 数据。

### 本日要建立的架构原则

- **数据状态与视觉表现分离**：`Fault=true` 是业务状态，红色只是表现。
- **命令与通知分离**：函数用于请求对象执行操作；事件分发器用于广播某个变化。
- **每个模块职责清晰**：Motor 管自己的状态，Manager 负责映射与分发，材质负责视觉表现。
- **所有实验都要验证行为**：不只看节点能否编译，还要检查输入、输出和异常路径。

## 2. 状态、变化与事件：边沿检测

假设设备状态为 Boolean：

- `Fault=false`：当前没有故障。
- `Fault=true`：当前处于故障状态。

“当前故障”是状态；“刚刚进入故障”是状态变化；`OnMotorFault` 是用来通知监听者的事件。

| 旧状态 | 新状态 | 语义 | 是否广播进入故障事件 |
|---|---|---|---|
| false | false | 仍然正常 | 否 |
| false | true | 刚刚进入故障 | 是 |
| true | true | 故障持续 | 否 |
| true | false | 故障恢复 | 否，除非另设恢复事件 |

这叫变化检测或边沿检测。它能防止重复告警。例如传感器每秒上报 10 次 `fault=true`，如果每次都广播“进入故障”，一秒就可能生成 10 条重复告警。

在真实系统中还要考虑抖动：若状态在 true/false 之间快速切换，可能需要去抖、最短持续时间或阈值滞回。

## 3. Function、Event Dispatcher、Delegate 的工程区别

### Function：命令/计算入口

例如 `ApplyMotorData`：调用者明确要求电机应用新数据。它适合有明确输入和执行目的的操作。

### Event Dispatcher：发布通知

例如 `OnMotorFault`：电机宣布“我刚刚进入故障”，已绑定的监听者各自响应。电机不需要知道所有监听者是谁，降低了直接依赖。

### Delegate：回调机制的更广义概念

Delegate 可理解为保存一个可调用目标的机制。Event Dispatcher 是 UE 蓝图中用于广播事件通知的一种模式。现在重点掌握调用方向即可，不必急着深入 C++ 模板和委托类型。

架构原则：
- 命令：调用者知道要让谁执行什么。
- 事件：发布者只表达发生了什么，监听者自行响应。
- 不要用广播事件代替所有函数调用，也不要让所有对象相互硬引用。

## 4. MID 与 MPC：对象级参数和全局参数

### 4.1 Base Material

基础材质定义外观计算规则。例如 `M_Motor_Base` 暴露 Vector Parameter `MotorColor`，把它连接到 `Base Color`。这样颜色就可以被实例参数控制。

### 4.2 MID：每个对象单独控制

Material Instance Dynamic 是运行时创建的动态材质实例。它适合让每台电机根据自己的状态改变颜色。

例：
- Motor01 的 MID 为绿色；
- Motor02 的 MID 为红色；
- Motor03 的 MID 为灰色。

每个 Actor 应保存并修改自己的 MID。若误把同一个 MID 共享给多个设备，可能出现一起变化的结果。

### 4.3 MPC：全局共享控制

Material Parameter Collection 提供多个材质共同读取的共享参数。适合全场景统一效果，例如“全厂进入警报视觉模式”或全局环境参数。

| 需求 | 典型选择 |
|---|---|
| 只让 Motor02 变红 | MID |
| 每台电机根据自身 Fault 变化 | 每对象独立 MID |
| 全场景一起进入警报模式 | MPC |
| 所有材质读取同一个全局效果强度 | MPC |

MPC 不是设备状态数据库。`Fault`、`RPM` 等业务状态仍应由数据模型管理；MPC 只是视觉层可读取的共享参数。

## 5. 材质参数与颜色规则

在蓝图中用 `Set Vector Parameter Value` 修改参数时，Parameter Name 必须和材质里创建的参数名完全一致，例如 `MotorColor`。

建议视觉优先级：

1. `Fault == true` → 红色；
2. 否则 `Running == true` → 绿色；
3. 否则 → 灰色。

为什么先判断 Fault？因为故障时设备可能仍报告 `Running=true`。如果先判断运行状态，故障电机就可能显示绿色，误导操作人员。

颜色只是辅助表达，正式工业界面不应只靠颜色；应结合文字、图标、闪烁规则或告警列表，并考虑色觉差异和显示环境。

## 6. Hard Reference、Soft Reference、异步加载

### Hard Reference

硬引用建立直接资源依赖，使用方便。依赖关系可能让资源随引用链一起加载，增加加载时间或内存占用。具体行为取决于资源类型和加载路径。

### Soft Reference

软引用主要保留资源路径/标识，让系统可以在需要时请求加载。它不等于自动加载，更不等于自动异步加载。

概念流程：

```text
软引用路径 → 发起加载请求 → 加载完成 → 检查结果 → 使用资源
```

### 同步与异步

- 同步加载：调用路径可能等待加载完成；若在游戏线程等待大资源，可能造成卡顿。
- 异步加载：请求加载后继续做其他工作，加载完成时再处理结果；但加载、解压、资源创建、显存上传等仍有成本。

软引用适合考虑用于大量可选模型、特效、设备变体等按需资源。常驻且总会用到的小型核心资源，硬引用可能更简单。应结合资源数量、加载时机、内存预算和打包测试决定。

## 7. 事件驱动与 Tick 的更深一层理解

Tick 是按帧执行的机会，不是“实时数据”的同义词。60 FPS 每帧约 16.67 ms，但这是整帧预算，不是每个 Actor 的独占预算。

若 3000 个设备每帧都执行复杂逻辑，会造成大量重复工作。更合理的分工通常是：
- 新数据到达时更新状态；
- 状态发生变化时触发事件；
- 必须连续计算的运动或插值才使用 Tick；
- UI 按合适频率刷新；
- 高频数据可以缓存最新值，但不能随意丢弃必须保存的告警和历史采样。

事件驱动并非零成本：大量事件也可能形成拥塞。因此仍需节流、合并、队列上限和指标监控。

## 8. 可靠数据更新的五条原则

即使目前还没有接入 MQTT→UE，建议从现在开始按可靠系统思维设计：

1. **验证输入**：字段存在、类型正确、单位明确、值在合理范围。
2. **明确数据新旧**：使用时间戳或序列号，防止旧消息覆盖新状态。
3. **处理未知设备**：不应让未知 ID 导致整个蓝图逻辑失败。
4. **区分离线与停止**：没有收到消息不代表设备停止；应有通信状态和超时策略。
5. **避免阻塞游戏线程**：网络接收、长时间等待和重解析不应卡住主线程；Actor 更新通常应在游戏线程安全执行。

## 9. 今日理论地图

```text
设备数据
  ├─ 身份：device_id → Map → Actor Reference
  ├─ 状态：RPM / Temperature / Running / Fault
  ├─ 变化：旧状态 vs 新状态
  ├─ 事件：OnMotorFault → Manager/UI/告警
  └─ 表现：Base Material → MID（单对象）/ MPC（共享）
```

本日的核心不是记住所有名词，而是能说明每一层负责什么，以及一条数据从进入系统到改变画面经过哪些步骤。

---

# Part B — 实验操作

## 实验前检查

- 打开 UE 5.6 项目 `E:\DT\DigitalTwinLab`。
- 打开 `FactoryLevel`。
- 确认关卡中有 `Motor01`、`Motor02`。
- 确认 `BP_Motor` 已有 `ApplyMotorData` 和 `Fault`、`Running` 变量。
- 确认 `BP_MotorManager` 已创建，`MotorMap` 和设备 ID 查询实验已完成。
- 不要重做已完成的设备映射和 Tick 对比实验。
- 操作前先保存项目；每完成一个实验 Compile、Save 并运行测试。

## 实验 1：创建 OnMotorFault Event Dispatcher

### 目标

当电机 Fault 从 false 变 true 时通知 Manager 一次；持续为 true 不重复通知。

### A. 在 BP_Motor 中创建 Dispatcher

1. 打开 `BP_Motor`。
2. 在 My Blueprint 面板找到 Event Dispatchers。
3. 点击 `+`，命名 `OnMotorFault`。
4. 暂不添加参数；后续可以扩展 `DeviceID` 参数。
5. Compile 并保存。

### B. 在 ApplyMotorData 中检测状态变化

为避免覆盖原有逻辑，先另存一个版本或确认可撤销。

推荐流程顺序：

1. 在 `ApplyMotorData` 中、`Set Fault` 之前读取当前 `Fault`。
2. 把旧值存入 Boolean 局部/成员变量 `OldFault`。如果使用成员变量，记住每次调用都要先覆盖它。
3. 将 `NewFault` 写入 `Fault`。
4. 添加 `Branch`，Condition 接 `OldFault != NewFault` 的 Boolean 比较结果。
5. False 分支结束，不广播。
6. True 分支再添加 `Branch`，Condition 接 `NewFault`。
7. 第二个 Branch 的 True 分支调用 `OnMotorFault` 的 Call/Broadcast 节点。
8. Compile 并保存。

伪流程：

```text
OldFault = Fault
Set Fault = NewFault
if OldFault != NewFault:
    if NewFault == true:
        Broadcast OnMotorFault
```

不要在 Set Fault 之后才读取旧 Fault，否则会把新值当成旧值。

### C. 在 BP_MotorManager 中绑定

1. 打开 `BP_MotorManager`。
2. 在 BeginPlay 中，确保 `Motor01Ref`、`Motor02Ref` 已经有效。
3. 从 `Motor01Ref` 拖出引线，搜索 `Bind Event to OnMotorFault`。
4. 从该节点创建绑定事件，命名或使用 `HandleMotorFault`。
5. 为 `Motor02Ref` 重复绑定到相同处理逻辑。
6. 在 `HandleMotorFault` 中添加 `Print String`，文字先设为 `收到电机故障事件`。
7. 确保绑定发生在测试输入/数据更新之前。
8. Compile、Save。

如果需要打印设备名，可以给 Dispatcher 增加 `DeviceID` 输入参数，并在广播时传入设备 ID；本次可以先验证基本通知链路。

### D. 验收测试

- Fault false → true：打印一次。
- Fault 保持 true：不再打印。
- Fault true → false：不触发进入故障事件。
- Fault false → true 再次发生：再打印一次。
- Motor02 故障时，Motor01 不应收到 Motor02 的事件。

如果打印多次，检查是否无条件广播或重复绑定。

---

## 实验 2：创建基础材质 M_Motor_Base

### 目标

创建可由蓝图修改的 `MotorColor` 参数。

1. Content Browser 进入 `Content/Materials`。
2. 右键 → Material，命名 `M_Motor_Base`。
3. 双击打开材质编辑器。
4. 空白处右键，搜索 `Vector Parameter`。
5. 命名为 `MotorColor`，默认设为灰色。
6. 将 RGB 输出连接到材质主节点 `Base Color`。
7. Apply、Save。

结构：

```text
Vector Parameter: MotorColor
            ↓ RGB
        Base Color
```

### 把材质赋给电机

1. 打开 `BP_Motor`。
2. 选择 `MotorMesh`。
3. 在 Details 的材质槽中，将 `M_Motor_Base` 赋给对应槽位。
4. Compile、Save。
5. 回到关卡确认电机显示材质。

如果模型有多个材质槽，要记录实际使用的 Element Index，后续创建 MID 时使用相同槽位。

---

## 实验 3：创建每台电机自己的 MID

### A. 创建变量

在 `BP_Motor` 新建变量：

- 名称：`MotorMID`
- 类型：`Material Instance Dynamic` Object Reference

### B. BeginPlay 创建 MID

1. 打开 Event Graph。
2. 在 `Event BeginPlay` 执行链上添加 `Create Dynamic Material Instance`。
3. Target 连接 `MotorMesh`。
4. Element Index 设为对应材质槽索引，通常是 0。
5. Return Value 连接到 `Set MotorMID`。
6. Compile、Save。

概念结构：

```text
BeginPlay
   ↓
Create Dynamic Material Instance (Target = MotorMesh)
   ↓ Return Value
Set MotorMID
```

每个 `BP_Motor` 实例在 BeginPlay 时都应创建并保存自己的 MID。

---

## 实验 4：创建 UpdateMotorVisual 函数

### A. 创建函数

1. 在 `BP_Motor` 新建 Function：`UpdateMotorVisual`。
2. 不需要输入参数。
3. 从变量读取 `Fault`、`Running` 和 `MotorMID`。

### B. 连接状态判断

执行顺序：

```text
UpdateMotorVisual
   ↓
Branch (Fault)
 ├─ True  → Set Vector Parameter Value: Red
 └─ False → Branch (Running)
              ├─ True  → Set Vector Parameter Value: Green
              └─ False → Set Vector Parameter Value: Gray
```

每个颜色分支都要：

1. 从 `MotorMID` 取引用。
2. 调用 `Set Vector Parameter Value`。
3. Parameter Name 填写 `MotorColor`，大小写必须一致。
4. Value 填写红色、绿色或灰色。
5. 确保 MID 有效再调用。

### C. 颜色参考值

可用以下近似值：

- 红色：R=1，G=0，B=0，A=1。
- 绿色：R=0，G=1，B=0，A=1。
- 灰色：R=0.35，G=0.35，B=0.35，A=1。

颜色可能受曝光、灯光和材质设置影响；本次只需能清楚区分三种状态。

### D. 在 ApplyMotorData 中刷新视觉

1. 打开 `ApplyMotorData`。
2. 保留已有的状态写入顺序。
3. 在 `Running`、`Fault` 等变量更新后调用 `UpdateMotorVisual`。
4. Compile、Save。

注意：BeginPlay 创建 MID 的时机必须早于第一次视觉更新。如果函数可能在初始化之前被调用，要在函数中检查 MID 是否有效，并在必要时安全地创建/处理它。

### E. 测试

| Running | Fault | 预期颜色 |
|---|---|---|
| false | false | 灰色 |
| true | false | 绿色 |
| false | true | 红色 |
| true | true | 红色 |

分别更新 Motor01 和 Motor02。只更新其中一个时，另一个颜色不能变化。

如果两台一起变色，检查是否每台电机都创建自己的 MID、是否更新了正确的 `MotorMID`，以及是否误用全局参数控制单对象颜色。

---

## 实验 5：回归与故障排查

按以下顺序测试并记录结果：

1. 启动关卡，确认没有编译错误。
2. Motor01 运行，检查只有 Motor01 变绿。
3. Motor02 故障，检查只有 Motor02 变红。
4. 重复应用相同故障状态，检查 Dispatcher 不重复通知。
5. 故障恢复，再次进入故障，确认事件能再次通知。
6. 在 `BP_MotorManager` 中检查两台引用和 Map Key 是否正确。
7. 观察 Output Log / Print String 是否出现重复事件。
8. 保存项目。

若失败，按层定位：
- 状态变量不正确：检查 `ApplyMotorData` 的输入和 Set 节点。
- 状态正确但事件没触发：检查旧/新值比较和 Dispatcher 调用。
- Dispatcher 调用但 Manager 没收到：检查绑定目标实例、BeginPlay 时序和重复/无效引用。
- 状态和事件正确但颜色不变：检查材质参数名、MID 创建、材质槽和 `UpdateMotorVisual` 调用。
- 两台同时变色：检查 MID 是否被错误共享。

---

# Part C — MPC 与资源引用的理论预习（本日可选）

如果前两个实验提前完成，可阅读本部分，但不要求今天全部实操。

## 1. MPC 预习

1. 在 `Content/Materials` 创建 `Material Parameter Collection`，命名 `MPC_Motor_Global`。
2. 添加 Scalar 参数 `GlobalAlarm`。
3. 添加 Vector 参数 `GlobalMotorColor`。
4. 在材质图中使用 `Collection Parameter` 节点读取相应参数。
5. 用蓝图的 `Set Scalar Parameter Value` / `Set Vector Parameter Value` 更新 Collection。
6. 验证所有读取同一参数的材质都会受到影响。

与 MID 的区别：MID 适合单对象独立参数；MPC 适合共享全局参数。建议下一学习日单独完成，以免把两种机制混淆。

## 2. Hard / Soft Reference 预习

- Hard Reference：直接依赖资源，简单，但可能扩大加载依赖。
- Soft Reference：保存资源路径，允许按需请求加载。
- Async Load Asset：发起异步加载请求，完成后处理结果。
- 需要测试加载成功、路径错误、重复请求和打包后资源可用性。

实际蓝图节点名称可能随 UE 版本、引用变量类型和上下文有所不同；若搜索不到完全相同节点，先确认变量类型和节点上下文，不要随意换成不匹配的节点。

---

# Part D — 今日学习记录与 GitHub

## 今日验收清单

- [ ] 理解状态变化检测，能解释旧状态和新状态。
- [ ] 创建 `OnMotorFault` Dispatcher。
- [ ] Manager 绑定两个电机的事件。
- [ ] 验证进入故障时只通知一次。
- [ ] 创建 `M_Motor_Base` 与 `MotorColor` 参数。
- [ ] 为每个电机创建自己的 MID。
- [ ] 实现 `UpdateMotorVisual`。
- [ ] 验证两台电机颜色互不干扰。
- [ ] 记录失败现象、原因和修复方式。
- [ ] 更新学习日志并提交 GitHub。

## 建议日志位置

`E:\DT\DigitalTwin-Lab\docs\learning-log\Day011.md`

## Git 命令

```powershell
cd E:\DT\DigitalTwin-Lab
git add docs/learning-log/Day011.md
git commit -m "Day011: implement motor fault events and dynamic materials"
git push origin main
```

如果还要同时提交本操作文档，请把它放在 `docs/learning-log/Day011_Study_Guide.md`，并将该路径也加入 `git add`。

## Day011 总结模板

- 理论完成情况：
- Event Dispatcher 实验结果：
- MID 实验结果：
- 测试了哪些输入组合：
- 遇到的错误：
- 错误原因：
- 修复方式：
- 尚未完成的项目：
- 下一步：MPC、Hard/Soft Reference、MQTT → UE 数据集成。

**完成标准：** 不是只把蓝图节点连通，而是能解释为什么状态变化才触发事件、为什么每台电机需要独立的 MID，以及当测试失败时应从哪一层定位。
