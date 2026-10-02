# HyperMesh AI Bridge Bootstrap Script
set script_dir [file dirname [file normalize [info script]]]

if {[file exists [file join $script_dir "bridge_server" "hm_bridge.tcl"]]} {
    source [file join $script_dir "bridge_server" "hm_bridge.tcl"]
} elseif {[file exists [file join $script_dir "hm_agent" "bridge_server" "hm_bridge.tcl"]]} {
    source [file join $script_dir "hm_agent" "bridge_server" "hm_bridge.tcl"]
} else {
    puts "ERROR: Cannot locate bridge_server/hm_bridge.tcl"
}
