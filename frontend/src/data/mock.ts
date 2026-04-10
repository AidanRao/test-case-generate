export interface Requirement {
  title: string
  type: string
  ID?: string
  code?: string
  content: string
}

export interface ProjectModule {
  module: string
  requirements: Requirement[]
}

export const projectData: ProjectModule[] = [
  {
    module: "风显示有效性判断",
    requirements: [
      {
        title: "风向有效性判断",
        type: "功能需求",
        ID: "SwRD_001",
        content: "当真实风向和真实航向均有效时，风向有效；当真实风向或真实航向之一为无效时，风向无效。"
      },
      {
        title: "PFD 菜单状态判断",
        type: "功能需求",
        code: "SwRD_002",
        content: "当 PFD 菜单标识为 1 时，PFD 菜单开启；当 PFD 菜单标识为 0 时，PFD 菜单关闭。"
      }
    ]
  },
  {
    module: "风速可显示性判断",
    requirements: [
      {
        title: "停止显示阈值判断",
        type: "功能需求",
        ID: "SwRD_010",
        content: "当风速小于 5knots 时，停止显示风速信息。"
      }
    ]
  }
]
