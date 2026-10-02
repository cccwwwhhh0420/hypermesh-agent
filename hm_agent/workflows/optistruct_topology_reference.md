# OptiStruct 拓扑优化命令速查 (HyperMesh 2022, 全部实测验证)

## 响应类型代码 (*optiresponsecreate)
| 类型 | 含义 | fem 卡片 |
| --- | --- | --- |
| 2 | VOLUME 体积 | VOLUME |
| 3 | VOLFRAC 体积分数 | VOLFRAC |
| 7 | DISP 位移 | DISP |
| 9 | STRESS 应力 | STRESS |
| 13 | CFAILUREPCOMP 复合材料失效 | CFAILUREPCOMP |
| 29 | MASS 质量 | MASS |
| 30 | MASSFRAC 质量分数 | MASSFRAC |
| 31 | COMP 柔度 (拓扑标准目标) | COMP |
| 34 | WCOMP 加权柔度 | WCOMP |
| 35 | COMP(方程) 带方程柔度 | COMP |

## 拓扑设计变量
*createmark properties 1 "属性名"
*topologydesvarcreate 1 "名字" 0 0 1   ;# 1=壳 2=实体 (导出为 DTPL)

## 响应创建 (必须先建数组!)
*createarray 6 0 0 0 0 0 0
*createdoublearray 6 0 0 0 0 0 0
*optiresponsecreate "名字" <类型> 0 0 0 0 0 6 0 0 0 1 6 1 6
*optiresponsesetequationdata1 "名字" 0 0 0 0 1 0
*optiresponsesetequationdata2 "名字" 0 0 1 0
*optiresponsesetequationdata3 "名字" 0 0 1 0
*optiresponsesetequationdata4 "名字" 0 0 0 0 1 0 1 0

## 目标 (最小化柔度)
*optiobjectivecreate <响应ID> 0 0
*setvalue objectives id=1 STATUS=2 loadstepid={loadsteps <载荷步ID>}
# 导出为 subcase 里的 DESOBJ(MIN)=响应ID

## 约束
*opticonstraintcreate "名字" <响应ID> 1 -1e+20 <上限> 1 0
# 例: volfrac<=0.3  ->  *opticonstraintcreate "con_vf" 2 1 -1e+20 0.3 1 0

## 导出 + 求解
*feoutputwithdata "D:/Hyperwork2022/hwdesktop/templates/feoutput/optistruct/optistruct" "out.fem" 1 0 1 1 1
# 求解环境: ALTAIR_HOME=D:/Hyperwork2022/hwdesktop, NOLICENSECHECK=true, PATH 加 hwsolvers/common/bin/win64

## 结果文件
- *.sh 拓扑密度文件
- *_des.h3d 设计结果 (可 HyperView 打开)
- *.stat 迭代历史
- *.out 求解报告 (含目标/约束表)
