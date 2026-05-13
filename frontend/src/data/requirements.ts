export interface RawRequirement {
  title: string
  type: string
  ID?: string
  code?: string
  content: string
}

export interface ModuleGroup {
  module: string
  requirements: RawRequirement[]
}

export interface Requirement extends RawRequirement {
  module: string
}

const rawRequirements = [
  {
    "module": "飞行控制系统",
    "requirements": [
      {
        "title": "软件运行环境计算资源预留余量",
        "type": "余量需求",
        "code": "SwRD_001",
        "content": "为保证后续扩展，飞行控制软件在标准任务剖面下的 CPU 平均占用率应不超过 60%，静态内存（RAM）占用率应不超过 50%，以确保系统在极端负载下仍有处理余量。"
      },
      {
        "title": "多余度控制通道无缝切换机制",
        "type": "可靠性需求",
        "code": "SwRD_002",
        "content": "余度管理模块应实现三余度机箱同步。当主控制通道发生硬件失效或连续 3 个周期 未更新心跳信号 Heartbeat_Main 时，系统应在 10ms 内切换至备用通道，并保持控制输出的平滑连续。"
      },
      {
        "title": "自主飞行模式紧急终止与平飞保护",
        "type": "安全性需求",
        "code": "SwRD_003",
        "content": "软件应设置独立的\"自主飞行紧急终止\"功能。当触发指令 Emergency_Stop = 1 或链路中断时长超过 30s 时，软件必须立即禁止自主飞行（Inhibit），并自动切入平飞保护模式。"
      },
      {
        "title": "非易失性存储器飞行日志存储容量",
        "type": "容量需求",
        "code": "SwRD_004",
        "content": "飞行日志存储模块应支持在板载 NVRAM 中保存至少最近 48 小时 的飞行数据。当存储空间占用率达到 90% 时，软件应输出 LogStorageFullWarning 告警，并执行覆盖逻辑。"
      },
      {
        "title": "故障快照瞬时大数据量处理能力",
        "type": "强度需求",
        "code": "SwRD_005",
        "content": "系统监控模块应具备高频数据处理能力。在触发全系统状态快照（Snapshot）时，软件应能在单周期内支持至少 500 个 关键参数的同步记录，且不应引起主控制循环的执行超时。"
      },
      {
        "title": "俯仰轴控制律任务实时性要求",
        "type": "性能需求",
        "code": "SwRD_006",
        "content": "在手动飞行模式下，飞行控制软件应确保俯仰角（Pitch）控制指令的闭环响应延迟不超过 50ms。从飞行员操纵杆位移信号 $L_{stick}$ 输入到舵机指令 $D_{cmd}$ 输出的总处理时间应满足该实时性要求，以保证飞行控制的动态稳定性。"
      },
      {
        "title": "ARINC 429 总线大气高度数据接收协议",
        "type": "接口需求",
        "code": "SwRD_007",
        "content": "飞行控制软件应通过 ARINC 429 总线接收来自大气数据计算系统（ADCU）的高度信号 Alt_MSL。该信号应采用 32-bit BNR 编码格式，标签号（Label）为 203，且软件应在每个 20ms 周期起始处完成读取。"
      },
      {
        "title": "三余度加速度计信号中值选优算法",
        "type": "数据处理需求",
        "code": "SwRD_008",
        "content": "软件应输出三轴加速度融合值 Fused_Accel。该值由三个独立加速度计通道 $A_1, A_2, A_3$ 经中值选择算法（Middle Value Selection）计算得出。当三个通道偏差均在 5% 以内时，取中值；当仅有两个通道有效时，取其算术平均值；当有效通道数少于两个时，应将 Fused_Accel_Valid 置为 0。"
      },
      {
        "title": "飞行姿态保护逻辑极限阈值限制",
        "type": "边界需求",
        "code": "SwRD_009",
        "content": "自动飞行系统应实时监测飞机姿态。当机体俯仰角 $\\theta$ 达到 +25°（抬头）或 -15°（低头）时，系统应触发姿态保护逻辑。此时，自动控制律应强制限制升降舵输出指令，防止姿态进一步扩大，并将状态标识 AttitudeLimitReached 置为 1。"
      }
    ]
  },
  {
    "module": "风速显示系统",
    "requirements": [
      {
        "title": "风速系统显示软件输出风显示标识",
        "type": "功能需求",
        "code": "SwRD_101",
        "content": "风速系统显示软件应输出风显示标识 WindVisible，其取值为 0 或 1，用于表征风信息在飞行显示上的可见状态。在满足显示配置条件且风速有效标识 WindSpeedFMSSideIsValid = 1 的前提下，系统应结合真实风向与真实航向的有效性对 WindVisible 进行判定。\n当真实风向有效标识 WindDirectionTrueFMSSideIsValid = 1 且真实航向有效标识 TrueRefHeadingIsValid = 1 时，系统应将风显示标识 WindVisible 置为 1；当 WindDirectionTrueFMSSideIsValid = 0 或 TrueRefHeadingIsValid = 0 时，系统应将 WindVisible 置为 0。上述判定逻辑在 PFD 模式（DuConfig = 1） 和 MFD 模式（DuConfig = 0） 下均应一致生效，并正确反映在对应的飞行显示界面中。"
      }
    ]
  }
]

const modules = rawRequirements as ModuleGroup[]

const requirements = modules.flatMap((group) =>
  group.requirements.map((item) => ({
    ...item,
    module: group.module
  }))
)

const projectName = '项目需求'

export { modules, requirements, projectName }