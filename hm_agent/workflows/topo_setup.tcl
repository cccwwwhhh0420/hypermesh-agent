# ============================================================
# OptiStruct 拓扑优化工作流 (HyperMesh 2022, 已验证)
# 用法: python _run.py topology/topo_setup.tcl
# 前置: 模型已加载, 设计空间属性存在, 载荷/约束已定义
# ============================================================

set out ""
hm_blockmessages 1
hm_blockerrormessages 1

# ---------- 1. 设计空间: 在属性上创建拓扑设计变量 ----------
# 标记设计空间属性 (可改属性名/ID)
*createmark properties 1 "auto1"
if {[catch {*topologydesvarcreate 1 "topo_dv" 0 0 1} e]} {
  append out "desvar ERR: $e\n"
} else {
  append out "拓扑设计变量 topo_dv 创建成功\n"
}

# ---------- 2. 响应 (必须先建数组!) ----------
# VOLFRAC 体积分数响应 (type 3)
*createarray 6 0 0 0 0 0 0
*createdoublearray 6 0 0 0 0 0 0
if {[catch {*optiresponsecreate "volfrac_resp" 3 0 0 0 0 0 6 0 0 0 1 6 1 6} e]} { append out "volfrac ERR: $e\n" } else { append out "VOLFRAC 响应创建成功\n" }
*optiresponsesetequationdata1 "volfrac_resp" 0 0 0 0 1 0
*optiresponsesetequationdata2 "volfrac_resp" 0 0 1 0
*optiresponsesetequationdata3 "volfrac_resp" 0 0 1 0
*optiresponsesetequationdata4 "volfrac_resp" 0 0 0 0 1 0 1 0

# COMPL 柔度响应 (type 31 = 拓扑优化标准目标)
*createarray 6 0 0 0 0 0 0
*createdoublearray 6 0 0 0 0 0 0
if {[catch {*optiresponsecreate "compl_resp" 31 0 0 0 0 0 6 0 0 0 1 6 1 6} e]} { append out "compl ERR: $e\n" } else { append out "COMPL 响应创建成功\n" }
*optiresponsesetequationdata1 "compl_resp" 0 0 0 0 1 0
*optiresponsesetequationdata2 "compl_resp" 0 0 1 0
*optiresponsesetequationdata3 "compl_resp" 0 0 1 0
*optiresponsesetequationdata4 "compl_resp" 0 0 0 0 1 0 1 0

# 获取响应 ID
set rids [hm_entitylist optiresponses id all]
set rid_list {}
foreach r $rids {
  set nm [hm_getvalue optiresponses id=$r dataname=name]
  if {$nm eq "volfrac_resp"} { set vid $r }
  if {$nm eq "compl_resp"} { set cid $r }
}
append out "响应ID: volfrac=$vid compl=$cid\n"

# ---------- 3. 目标: 最小化柔度 ----------
if {[catch {*optiobjectivecreate $cid 0 0} e]} { append out "objective ERR: $e\n" } else { append out "目标(最小化柔度)创建成功\n" }
# 关联载荷步 (载荷步ID按实际修改)
catch {*setvalue objectives id=1 STATUS=2 loadstepid={loadsteps 1}}

# ---------- 4. 约束: volfrac <= 0.3 ----------
if {[catch {*opticonstraintcreate "con_volfrac" $vid 1 -1e+20 0.3 1 0} e]} { append out "constraint ERR: $e\n" } else { append out "约束(volfrac<=0.3)创建成功\n" }

hm_blockmessages 0
hm_blockerrormessages 0

# ---------- 5. 导出 FEM ----------
hm_answer yes
set fem_out [file join [pwd] "topo_run.fem"]
if {[catch {*feoutputwithdata "#optistruct\\optistruct" $fem_out 1 0 1 1 1} e]} { append out "export ERR: $e\n" } else { append out "FEM 导出成功: $fem_out\n" }

append out "== 工作流完成 =="
set out

