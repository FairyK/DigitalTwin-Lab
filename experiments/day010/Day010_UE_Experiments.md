# Day010：UE 未完成实验集中实操手册（UE 5.6）

**目标：** 在现有 `E:\DT\DigitalTwinLab` 项目中完成设备映射、事件驱动、MID、MPC、Hard/Soft Reference 实验。  
**前置状态：** UE-007 已完成；`BP_Motor` 已有 `Temperature`、`RPM`、`Running`、`Fault`，并有 `ApplyMotorData(NewTemperature, NewRPM, NewRunning, NewFault)` 函数。  
**重要原则：** 不重做 UE-007；每完成一组先保存，再进入下一组。不同 UE 5.6 项目模板/编辑器布局可能略有差异，节点搜索名称以英文为准。

---

## 0. 开始前检查（5 分钟）

1. 在 Windows 打开 Unreal Engine 5.6。
2. 打开项目：`E:\DT\DigitalTwinLab\DigitalTwinLab.uproject`。
3. 打开关卡：`Content/Maps/FactoryLevel`。
4. 在 Content Drawer 确认存在：
   - `Blueprints/Motors/BP_Motor`
   - `Blueprints/Managers` 文件夹（没有就新建）
   - `Materials` 文件夹
5. 确认关卡中有两个 `BP_Motor` 实例，分别命名为 `Motor01`、`Motor02`。
6. 打开 `BP_Motor`，确认 `ApplyMotorData` 的四个输入和四个 Set 节点正常。
7. 按 `Ctrl+Shift+S` 或使用 File → Save All 保存。

**检查点：** 如果以上资产或关卡名与实际项目不同，以现有资产为准，不要新建第二套同名项目。

---

# 实验一：UE-008 设备 ID → Actor 映射（约 35–50 分钟）

## 1.1 创建 BP_MotorManager

1. 在 Content Drawer 进入 `Content/Blueprints/Managers`。
2. 右键空白处 → Blueprint Class。
3. 选择 `Actor`。
4. 命名为 `BP_MotorManager`。
5. 双击打开，点击 Compile，再 Save。

## 1.2 建立可配置的 Actor 引用变量

为了避免 UE 5.6 中直接在 Map 详情里配置关卡 Actor 引用不方便，先用两个明确的引用变量，再在 BeginPlay 中建立 Map。

1. 在 `BP_MotorManager` 的 My Blueprint → Variables 点击 `+`。
2. 创建变量 `Motor01Ref`。
3. 在 Details 中将类型设为 `BP_Motor` Object Reference。
4. 勾选 `Instance Editable`（眼睛图标/可编辑图标，具体位置因布局不同）。
5. 同样创建 `Motor02Ref`，类型也为 `BP_Motor Object Reference`，并勾选 `Instance Editable`。
6. 创建变量 `MotorMap`：
   - Variable Type：`String`
   - 将容器类型切换为 `Map`（不要选 Array 或 Set）
   - Map Value 类型设为 `BP_Motor Object Reference`
7. 编译并保存。

**检查点：** `MotorMap` 应显示为 Map 容器；Key 是 String，Value 是 BP_Motor Object Reference。若类型下拉里暂时看不到 `BP_Motor`，先编译 `BP_Motor`，再回到 Manager 重新选择类型。

## 1.3 把关卡中的两个电机引用赋给 Manager

1. 回到 `FactoryLevel`。
2. 从 Content Drawer 将 `BP_MotorManager` 拖入关卡一次。
3. 在 World Outliner 选择这个 `BP_MotorManager` 实例。
4. 在 Details 中找到 `Motor01Ref`，使用对象选择器/下拉列表选择关卡中的 `Motor01`。
5. 找到 `Motor02Ref`，选择关卡中的 `Motor02`。
6. 保存关卡。

**检查点：** Details 面板里两个变量都应显示为已指定对象，而不是 `None`。

如果对象选择器没有列出关卡 Actor：
- 确认勾选了 `Instance Editable` 并且 Blueprint 已 Compile；
- 重新选择关卡中的 Manager 实例；
- 如仍不可选，先不要卡住，跳到“备选方案：BeginPlay 自动注册”。

## 1.4 BeginPlay 时建立 MotorMap

1. 打开 `BP_MotorManager` → Event Graph。
2. 找到 `Event BeginPlay`。
3. 从 BeginPlay 的白色执行引脚拉线，搜索并放置 `Clear`（针对 Map 的 Clear；如果有多个，选择目标为 `MotorMap` 的版本）。
4. 从 `MotorMap` 变量拖一个 `Get` 到图表。
5. 从 `MotorMap` Get 引脚拖出，搜索 `Add`，选择 Map 的 Add 节点。
6. 第一次 Add：
   - Target Map = `MotorMap`
   - Key = 字符串 `Motor01`
   - Value = `Motor01Ref`
   - 执行线：BeginPlay → Clear → Add
7. 再放一个 Map Add：
   - Target Map = `MotorMap`
   - Key = `Motor02`
   - Value = `Motor02Ref`
   - 执行线：第一个 Add → 第二个 Add
8. Compile、Save。

**备选方案：BeginPlay 自动注册（当实例引用不好配置时）**
- 在 BeginPlay 后用 `Get All Actors Of Class`，Class 选 `BP_Motor`。
- 用 `ForEachLoop` 遍历数组；对每个 Array Element 取其 Actor Name（`Get Object Name` 或适用的名称节点）。
- 将名称作为 Key、Array Element 转为/使用 `BP_Motor` 引用作为 Value，调用 Map Add。
- 该方式依赖关卡 Actor 名称与设备 ID 一致（`Motor01`、`Motor02`）。生产项目更建议使用显式设备 ID 属性，而不是把显示名称当作稳定 ID。

## 1.5 创建 FindMotorByID 函数

1. 在 My Blueprint 的 Functions 区点击 `+`，命名 `FindMotorByID`。
2. 选中函数，在 Details → Inputs 添加：
   - `DeviceID`，类型 `String`
3. 在 Outputs 添加：
   - `FoundMotor`，类型 `BP_Motor Object Reference`
   - `Found`，类型 `Boolean`
4. 在函数图表放置 `MotorMap` Get。
5. 从 Map 引脚拖出，搜索 `Find`，选择 Map Find 节点。
6. 将 `DeviceID` 输入接到 Find 的 Key。
7. 将 Find 的 Value 输出接到函数输出 `FoundMotor`。
8. 将 Find 的 Found 输出接到函数输出 `Found`。
9. 如果当前编辑器不允许直接连接输出变量：
   - 在函数 Outputs 中确认输出名与类型；
   - 使用 `Return Node`，将 Value 与 Found 分别接到对应输出引脚。
10. Compile、Save。

**预期逻辑：**
- 输入 `Motor01` → Found = true，FoundMotor 指向 Motor01。
- 输入 `Motor02` → Found = true，FoundMotor 指向 Motor02。
- 输入 `Motor999` → Found = false，不应调用目标电机函数。

## 1.6 测试：只更新 Motor02

为避免把测试逻辑永久塞进生产逻辑，先临时在 Manager 的 Event Graph 做测试，成功后可以删除测试节点。

1. 在 `BP_MotorManager` Event Graph 添加键盘事件 `2`（Keyboard 2）。
2. 从 Pressed 拉线调用 `FindMotorByID`，`DeviceID` 填 `Motor02`。
3. 放置 `Branch`，Condition 接 `Found`。
4. Branch True：
   - 从 `FoundMotor` 输出拉线调用 `ApplyMotorData`。
   - `NewTemperature` = `75`
   - `NewRPM` = `1500`
   - `NewRunning` = `true`
   - `NewFault` = `false`
5. Branch False：接 `Print String`，文本 `Motor ID not found`。
6. Compile、Save。
7. 回到关卡，选择 `BP_MotorManager` 实例，确认 `Motor01Ref` 与 `Motor02Ref` 已设置。
8. 点击 Play。先记住两个电机初始表现，再按键盘 `2`。
9. 在 Print String 或临时调试打印中确认查找到目标。若需要看变量值，可在 `ApplyMotorData` 后 Print String 输出 `Updated Motor02`。
10. 停止 Play。

**验收标准：** 只有 Motor02 的状态被设置为 75 / 1500 / Running true；Motor01 不变。

## 1.7 测试未知 ID 与空引用保护

1. 把键盘测试调用的 DeviceID 临时改成 `Motor999`。
2. Compile、Play、按 `2`。
3. 预期：显示 `Motor ID not found`，没有访问空对象的报错。
4. 再恢复为 `Motor02`。
5. 在使用 `FoundMotor` 前，除 `Found` 外最好也检查引用是否有效（Blueprint 中可用 `Is Valid` 节点）。逻辑是 `Found == true` 且引用有效才调用。
6. 保存。

**本实验结论：** 字符串 ID 与 UE Actor 引用是不同东西；Manager 负责注册、查找、校验和分发。

---

# 实验二：Tick 与事件驱动对比（约 15–20 分钟）

## 2.1 创建一个可观察的 Tick 计数

1. 打开 `BP_Motor`。
2. 新建 Integer 变量 `TickCount`，默认 0。
3. Event Graph 找到 `Event Tick`。
4. 从 Tick 的执行引脚接 `Increment Int`（目标是 TickCount），或者 `Get TickCount → + 1 → Set TickCount`。
5. 不要每帧 Print String（会刷屏并影响性能）。改为每隔一段时间打印，或者用键盘手动查看：
   - 简单做法：暂时不打印，只观察 TickCount 在运行中持续增长。
   - 更清晰做法：新建键盘事件 `T`，按下时 Print String 输出 TickCount。
6. Compile、Save、Play，等待约 3 秒，按 `T`，记下数值；再等 3 秒按 `T`，数值应明显增加。
7. Stop。

## 2.2 对比事件驱动

1. 在 `BP_Motor` 新建 Integer 变量 `ChangeCount`，默认 0。
2. 找到 `ApplyMotorData` 函数。每次函数调用时，将 `ChangeCount + 1` 后 Set 回 `ChangeCount`。
3. Compile、Save。
4. Play，不调用 `ApplyMotorData`，等待约 3 秒后按 `T`，记录 TickCount 与 ChangeCount。
5. 调用 Manager 的键盘 `2` 更新 Motor02，再按 `T`。
6. 预期：TickCount 持续增长；ChangeCount 只在 `ApplyMotorData` 被调用时增加。
7. Stop。

**解释：** Tick 适合持续变化、每帧都需要更新的逻辑；外部设备状态通常更适合数据到达或状态变化时更新。不要把所有设备的所有逻辑都放到 Tick 中。

---

# 实验三：Event Dispatcher 故障事件（约 20–30 分钟）

## 3.1 在 BP_Motor 中声明 Dispatcher

1. 打开 `BP_Motor`。
2. 在 My Blueprint 面板的 Event Dispatchers 区点击 `+`。
3. 命名 `OnMotorFault`。
4. 选中 Dispatcher，若 Details 支持参数，添加：
   - `DeviceID` String（可选）
   - `Temperature` Float（可选）
5. 为简化第一次实验，参数也可以不加，先只测试事件触发。

## 3.2 仅在故障状态发生变化时广播

1. 打开 `ApplyMotorData` 函数。
2. 在修改 `Fault` 之前，先读取旧 `Fault` 保存到局部变量 `OldFault`（或临时用变量保存）。
3. 设置新的 Fault 后，用 `!=` 比较 `OldFault` 与 `NewFault`。
4. 将比较结果接到 Branch。
5. True 分支再判断 `NewFault` 是否为 true：
   - True：调用 `Call OnMotorFault`（节点名称可能显示为 Call OnMotorFault）。
   - False：本次为故障恢复，可选择不广播，或后续扩展 `OnMotorRecovered`。
6. 注意：若先 Set Fault 再读取 Fault，旧值就丢失了；一定要先保存旧值。
7. Compile、Save。

**简化替代做法：** 若函数图太复杂，可先创建单独的测试 Custom Event `TestFault`，手动把 Fault 从 false 改为 true，并 Call Dispatcher 验证绑定。完成后再把触发逻辑整合回 `ApplyMotorData`。

## 3.3 在 Manager 里绑定并监听

1. 打开 `BP_MotorManager`。
2. 在 BeginPlay 建图后，分别对 `Motor01Ref`、`Motor02Ref` 做 `Is Valid` 检查。
3. 对有效引用拖线，搜索 `Bind Event to OnMotorFault`（也可能显示 `Bind Event` + Dispatcher 名）。
4. 从 Bind 的 Event 引脚创建对应 Custom Event，例如 `HandleMotorFault`。
5. 在 `HandleMotorFault` 中放 `Print String`，显示 `Motor fault event received`。
6. Compile、Save。
7. Play，调用 `ApplyMotorData` 让某台电机 `Fault` 从 false 变 true。
8. 预期：Manager 打印一次事件提示；重复传入 Fault=true 不应再次广播（前提是已按“状态发生变化”实现）。
9. Stop。

**常见问题：**
- 没收到事件：确认绑定在 Call 之前完成；确认绑定的是正确电机引用；确认调用了 `Call OnMotorFault`。
- 每次都触发：检查是否比较了旧状态和新状态，而不是单纯判断 NewFault 是否为 true。

---

# 实验四：基础材质与 MID（动态材质实例）（约 25–35 分钟）

## 4.1 创建基础材质 M_Motor_Base

1. Content Drawer → `Content/Materials`。
2. 右键 → Material，命名 `M_Motor_Base`。
3. 双击打开材质编辑器。
4. 在空白处右键，搜索 `Vector Parameter`，放置节点，命名 `MotorColor`。
5. 将 `MotorColor` 的 RGB 输出接到 `Base Color`。
6. 将参数默认值设为蓝色或绿色。
7. 保存材质。

## 4.2 给 BP_Motor 的网格指定材质

1. 打开 `BP_Motor`。
2. 选中 `MotorMesh`（Static Mesh Component）。
3. Details → Materials，将 Element 0 指定为 `M_Motor_Base`。
4. Compile、Save。

## 4.3 创建并使用 MID

1. 在 `BP_Motor` Event Graph 找到 `Event BeginPlay`。
2. 新建变量 `MotorMID`，类型选择 `Material Instance Dynamic Object Reference`（可通过节点返回值提升为变量）。
3. 从 `MotorMesh` 引脚拉线，搜索 `Create Dynamic Material Instance`。
4. Element Index = 0；Parent = `M_Motor_Base`（如果节点默认使用组件 Element 0，也可按节点版本设置）。
5. 将 Return Value 提升为变量 `MotorMID`。
6. 在 Create Dynamic Material Instance 执行之后，调用 `Set Vector Parameter Value`：
   - Target = MotorMID
   - Parameter Name = `MotorColor`
   - Value = 蓝色/绿色（运行状态）
7. Compile、Save。

## 4.4 根据状态改变单台电机颜色

1. 在 `BP_Motor` 中创建 Function `UpdateMotorVisual`。
2. 读取 `Fault`，接 Branch。
3. Fault=True：若 MotorMID 有效，调用 `Set Vector Parameter Value`，`MotorColor` 设为红色。
4. Fault=False 且 Running=True：设为绿色。
5. Fault=False 且 Running=False：设为灰色。
6. 在 `ApplyMotorData` 所有状态 Set 完成后调用 `UpdateMotorVisual`。
7. 在 BeginPlay 创建 MID 后也调用一次 `UpdateMotorVisual`，确保启动时外观与初始状态一致。
8. Compile、Save。
9. Play，用 Manager 的按键测试更新 Motor02；观察 Motor02 颜色变化，Motor01 不应变化。

**重要：** 每个电机 Actor 应有自己的 MID。不要把一个 MID 对象引用共享给两个不同电机，否则会失去独立控制。

---

# 实验五：MPC（Material Parameter Collection）共享参数（约 15–25 分钟）

## 5.1 创建 MPC

1. Content Drawer → `Content/Materials`。
2. 右键 → Materials → Material Parameter Collection。
3. 命名 `MPC_Motor_Global`。
4. 打开资产，添加 Scalar Parameter `GlobalAlarm`，默认 0。
5. 添加 Vector Parameter `GlobalMotorColor`，默认蓝色。
6. 保存。

## 5.2 在材质里读取 MPC

1. 打开 `M_Motor_Base`。
2. 空白处右键，搜索 `Collection Parameter`。
3. 选择 Collection 为 `MPC_Motor_Global`。
4. 选择参数 `GlobalMotorColor`。
5. 临时把它接到 Base Color（如果还想保留 MID 的独立颜色逻辑，可以先复制材质做 `M_Motor_MPC_Test`，避免覆盖前面的 MID 实验）。
6. 保存。

## 5.3 从蓝图修改 MPC 参数

1. 在 `BP_MotorManager` Event Graph 添加键盘事件 `G`。
2. 从 Pressed 拉线，搜索 `Set Vector Parameter Value`，选择 Material Parameter Collection 版本。
3. Collection 选择 `MPC_Motor_Global`，Parameter Name 选择 `GlobalMotorColor`。
4. Value 设为红色。
5. 再添加键盘事件 `H`，设置同一参数为蓝色。
6. 为测试 MPC 的共享作用，将 `M_Motor_MPC_Test` 指定给 Motor01 和 Motor02 的网格。
7. Compile、Save、Play。
8. 按 `G`，两台电机材质应同时变红；按 `H`，两台同时变蓝。

**MID 与 MPC 的区别：**
- MID：控制某一个材质实例/某个对象的参数，适合单台设备独立状态。
- MPC：同一集合参数被多个材质读取，适合全局告警、全场统一效果。
- MPC 不是设备 ID 映射，也不是用来替代 MID 的。

---

# 实验六：Hard Reference 与 Soft Reference（约 20–30 分钟）

## 6.1 理解目标

- Hard Reference：直接持有对象/资产引用，通常会形成硬依赖，可能导致相关资产随依赖链加载。
- Soft Reference：保存资产路径式引用，可按需异步加载；它不会因为“软引用”本身就自动完成加载。
- 对已经存在于关卡中的 Actor，不能简单把 Soft Object Reference 当成 Actor 运行时注册的替代品；本实验主要用材质资产演示资源引用。

## 6.2 建立测试变量

1. 打开 `BP_Motor`。
2. 新建变量 `HardMotorMaterial`，类型为 `Material Interface Object Reference`。
3. 默认值指定 `M_Motor_Base`。
4. 新建变量 `SoftMotorMaterial`，类型选择 `Soft Object Reference`，目标类为 Material Interface（在变量类型选择器中找 Soft Object Reference / Soft Object Path 对应的材质类型）。
5. 尝试把默认资产指定为 `M_Motor_Base`，Compile、Save。
6. 如果变量类型选择器无法创建该 Soft Reference 类型，不要卡住；使用下一节“资产引用节点演示”。

## 6.3 资产引用节点演示（备选）

1. 在 `BP_Motor` Event Graph 空白处右键，搜索 `Async Load Asset`。
2. 放置节点，观察它需要的 Soft Object Reference 输入以及完成回调执行引脚。
3. 从内容浏览器将 `M_Motor_Base` 拖入图表，观察直接引用节点（Hard Reference）的表现。
4. 如果编辑器允许将资产转换/提升为 Soft Reference，则连接到 Async Load Asset 的输入。
5. 在完成回调后检查返回资产是否有效；按节点支持的类型转换为 Material Interface，再用于材质设置。
6. 这一步主要是识别引用与加载的关系，不要求立即搭建复杂的异步资源系统。

## 6.4 记录观察结果

在学习日志中写下：
- Hard Reference 指向什么资产？
- Soft Reference 保存的是什么信息？
- Async Load Asset 在什么时候继续执行？
- 为什么不应在每帧 Tick 中反复加载资产？
- 哪些资源适合按需加载（例如大型设备模型、材质、关卡资源）？

---

# 实验七：最终回归测试与清理（约 15 分钟）

1. Compile 所有 Blueprint，解决红色错误提示。
2. Save All。
3. Play：
   - 键盘 `2`：只更新 Motor02；
   - 键盘 `G` / `H`：MPC 测试材质全局切换；
   - 故障状态从 false 变 true：Manager 收到一次 `OnMotorFault`；
   - 按 `T`：观察 TickCount 与 ChangeCount 的差别。
4. 对 `Motor999` 做一次负面测试，确认不会对 None 引用调用函数。
5. 删除或禁用临时测试节点时，先确保正式功能仍能通过测试；保留有价值的调试打印。
6. Save All。
7. 在 Git 中归档学习记录与项目源码。UE 项目提交前检查 `.gitignore`，通常不提交 `Binaries/`、`DerivedDataCache/`、`Intermediate/`、`Saved/` 等可再生成目录；保留 `.uproject`、`Config/`、`Content/`、`Source/`（若有）等必要文件。不要直接把整个项目目录无差别加入 Git。

---

# 明日执行顺序与时间安排

| 顺序 | 内容 | 预计时间 | 优先级 |
|---|---|---:|---|
| 1 | 开始前检查 + BP_MotorManager | 10 分钟 | 必做 |
| 2 | MotorMap、FindMotorByID、未知 ID 保护 | 35–50 分钟 | 必做 |
| 3 | Tick 与事件驱动对比 | 15–20 分钟 | 必做 |
| 4 | OnMotorFault Dispatcher | 20–30 分钟 | 必做 |
| 5 | 基础材质 + MID 单体颜色 | 25–35 分钟 | 必做 |
| 6 | MPC 全局参数 | 15–25 分钟 | 必做 |
| 7 | Hard/Soft Reference | 20–30 分钟 | 必做 |
| 8 | 最终回归测试与记录 | 15 分钟 | 必做 |

**总计约 2.5–3.5 小时。** 如果遇到 UE 5.6 的节点差异或蓝图编译问题，优先完成 1–5 和 7，再把 MPC/引用实验剩余部分记为待续；不要为了赶进度跳过编译、保存和验证。

## GitHub 归档

把本文件保存为：

`E:\DT\DigitalTwin-Lab\docs\learning-log\Day010_UE_Experiments.md`

然后在 PowerShell 或 VS Code 终端执行：

```powershell
cd E:\DT\DigitalTwin-Lab
git add docs/learning-log/Day010_UE_Experiments.md
git commit -m "Day010: UE device mapping events and material experiments"
git push origin main
```

只有终端确认 `git push` 成功，才算上传完成。
