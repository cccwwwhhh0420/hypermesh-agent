# hm_bridge.tcl - HyperMesh TCP bridge server (run INSIDE HyperMesh)
# Protocol (line based, one reply per request):
#   client -> "ping"             server -> "pong"
#   client -> "quit"             server -> "bye" then closes
#   client -> "hmready"          server -> "yes"/"no"
#   client -> "cmd <base64>"     server -> "ok <base64>" | "err <base64>"
#   client -> "raw <tcl line>"   server -> "ok <base64>" | "err <base64>"  (debug)
# base64 payload = UTF-8 encoded Tcl script / result.
# Start: hw.exe /clientconfig hwfepre.dat -tcl "path/to/hm_bridge.tcl"
#   or inside HyperMesh: File > Run > Run Tcl/Tk Script...

namespace eval ::hmb {
  variable port [expr {[info exists env(HM_BRIDGE_PORT)] ? $env(HM_BRIDGE_PORT) : 23456}]
  variable sock ""
  variable logtext ""
  variable ready 0
}

proc ::hmb::log {msg} {
  puts "HM-BRIDGE: $msg"
  if {$::hmb::logtext ne "" && [winfo exists $::hmb::logtext]} {
    catch {
      $::hmb::logtext insert end "$msg\n"
      $::hmb::logtext see end
      update idletasks
    }
  }
}

proc ::hmb::b64enc {str} {
  # pure-Tcl base64 encoder (Tcl 8.5 compatible), UTF-8 in
  set chars "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  binary scan [encoding convertto utf-8 $str] cu* bytes
  set out ""
  set n [llength $bytes]
  for {set i 0} {$i < $n} {incr i 3} {
    set a [lindex $bytes $i]
    set b [expr {$i+1 < $n ? [lindex $bytes [expr {$i+1}]] : 0}]
    set c [expr {$i+2 < $n ? [lindex $bytes [expr {$i+2}]] : 0}]
    set v [expr {($a << 16) | ($b << 8) | $c}]
    append out [string index $chars [expr {($v >> 18) & 63}]]
    append out [string index $chars [expr {($v >> 12) & 63}]]
    if {$i+1 < $n} { append out [string index $chars [expr {($v >> 6) & 63}]] } else { append out "=" }
    if {$i+2 < $n} { append out [string index $chars [expr {$v & 63}]] } else { append out "=" }
  }
  return $out
}

proc ::hmb::b64dec {str} {
  # pure-Tcl base64 decoder -> UTF-8 bytes converted back to string
  set chars "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  regsub -all {\s} $str "" str
  set vals {}
  for {set i 0} {$i < [string length $str]} {incr i} {
    set ch [string index $str $i]
    if {$ch eq "="} { continue }
    set idx [string first $ch $chars]
    if {$idx < 0} { error "invalid base64 char: $ch" }
    lappend vals $idx
  }
  set out ""
  set n [llength $vals]
  for {set i 0} {$i < $n} {incr i 4} {
    set a [lindex $vals $i]
    set b [expr {$i+1 < $n ? [lindex $vals [expr {$i+1}]] : 0}]
    set c [expr {$i+2 < $n ? [lindex $vals [expr {$i+2}]] : 0}]
    set d [expr {$i+3 < $n ? [lindex $vals [expr {$i+3}]] : 0}]
    set v [expr {($a << 18) | ($b << 12) | ($c << 6) | $d}]
    append out [format %c [expr {($v >> 16) & 255}]]
    if {$i+2 < $n} { append out [format %c [expr {($v >> 8) & 255}]] }
    if {$i+3 < $n} { append out [format %c [expr {$v & 255}]] }
  }
  if {[catch {set s [encoding convertfrom utf-8 $out]}]} { return $out }
  return $s
}

proc ::hmb::Accept {chan addr port} {
  ::hmb::log "client connected: $addr:$port"
  catch { fconfigure $chan -blocking 0 -buffering line -translation lf -encoding utf-8 }
  fileevent $chan readable [list ::hmb::Read $chan $addr]
}

proc ::hmb::Reply {chan str} {
  catch { puts $chan $str; flush $chan }
}

proc ::hmb::Read {chan addr} {
  if {[eof $chan]} {
    catch { close $chan }
    ::hmb::log "client closed: $addr"
    return
  }
  if {[catch {gets $chan line} n]} {
    catch { close $chan }
    return
  }
  if {$n < 0} { return }
  set line [string trim $line]
  if {$line eq ""} { return }
  switch -exact -- $line {
    "ping"    { ::hmb::Reply $chan "pong" }
    "quit"    { ::hmb::Reply $chan "bye"; catch { close $chan }; ::hmb::log "client quit: $addr" }
    "hmready" { ::hmb::Reply $chan [expr {$::hmb::ready ? "yes" : "no"}] }
    default {
      set payload ""
      if {[string match "cmd *" $line]} {
        set b64 [string range $line 4 end]
        if {[catch {set payload [::hmb::b64dec $b64]} derr]} {
          ::hmb::Reply $chan "err [::hmb::b64enc "BAD_BASE64: $derr"]"
          return
        }
      } elseif {[string match "raw *" $line]} {
        set payload [string range $line 4 end]
      } else {
        ::hmb::Reply $chan "err [::hmb::b64enc "BAD_REQUEST: $line"]"
        return
      }
      ::hmb::log ">> [string range $payload 0 200]"
      if {[catch {uplevel #0 $payload} result]} {
        ::hmb::log "<< ERR: [string range $result 0 300]"
        ::hmb::Reply $chan "err [::hmb::b64enc $result]"
      } else {
        ::hmb::log "<< OK"
        ::hmb::Reply $chan "ok [::hmb::b64enc $result]"
      }
    }
  }
}

proc ::hmb::MakeLogWindow {} {
  if {[catch {winfo exists .}]} { return }
  set w .hmbridge_log
  if {[winfo exists $w]} { return }
  catch {
    toplevel $w -width 620 -height 320
    wm title $w "AI Bridge (HyperMesh) - Command Log"
    wm geometry $w 620x320+40+40
    text $w.txt -wrap word -font {Consolas 9} -bg #1e1e1e -fg #dcdcdc
    scrollbar $w.sb -command "$w.txt yview"
    $w.txt configure -yscrollcommand "$w.sb set"
    pack $w.sb -side right -fill y
    pack $w.txt -side left -fill both -expand true
    set ::hmb::logtext $w.txt
    ::hmb::log "AI Bridge started - listening on 127.0.0.1:$::hmb::port"
  }
}

proc ::hmb::Start {} {
  if {![info exists env(HM_BRIDGE_SKIP_WAIT)]} {
    set waited 0
    while {$waited < 300 && [info commands hm_info] eq ""} {
      after 100
      incr waited 10
    }
  }
  if {[info commands hm_info] ne ""} { set ::hmb::ready 1 }
  catch { ::hmb::MakeLogWindow }
  if {[catch {set ::hmb::sock [socket -server ::hmb::Accept -myaddr 127.0.0.1 $::hmb::port]}]} {
    set ::hmb::sock [socket -server ::hmb::Accept $::hmb::port]
  }
  ::hmb::log "listening on 127.0.0.1:$::hmb::port (hm_ready=$::hmb::ready)"
  # 可选：启动后自动打开指定项目文件（HM_STARTUP_FILE 环境变量）
  if {[info exists env(HM_STARTUP_FILE)] && $env(HM_STARTUP_FILE) ne ""} {
    set ::hmb::startupFile $env(HM_STARTUP_FILE)
    after 3000 {
      hm_answer yes
      if {[catch {*readfile $::hmb::startupFile} e]} {
        ::hmb::log "startup open FAILED: $e"
      } else {
        ::hmb::log "startup opened: $::hmb::startupFile"
      }
    }
  }
}

::hmb::Start

