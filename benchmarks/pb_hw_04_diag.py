from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import tempfile


def main() -> int:
    root=Path(__file__).resolve().parents[1]
    tb=root/'rtl'/'pb_hw_04_tb.v'
    rtl=root/'rtl'/'pb_hw_04.v'
    text=tb.read_text()
    replacements={
      'if(ca_s!==exp) failures=failures+1;':'if(ca_s!==exp) begin failures=failures+1; $display("DIAG COMPOSE single exp=%0d got=%b addrs=%0d,%0d,%0d,%0d ds=%h did=%0d",exp,ca_s,a0,a1,a2,a3,ds,did); end',
      'if(ca_b!==exp) failures=failures+1;':'if(ca_b!==exp) begin failures=failures+1; $display("DIAG COMPOSE banked exp=%0d got=%b addrs=%0d,%0d,%0d,%0d ds=%h did=%0d",exp,ca_b,a0,a1,a2,a3,ds,did); end',
      'if(ca_c!==exp) failures=failures+1;':'if(ca_c!==exp) begin failures=failures+1; $display("DIAG COMPOSE conventional_cache exp=%0d got=%b addrs=%0d,%0d,%0d,%0d ds=%h did=%0d",exp,ca_c,a0,a1,a2,a3,ds,did); end',
      'if(ca_p!==exp) failures=failures+1;':'if(ca_p!==exp) begin failures=failures+1; $display("DIAG COMPOSE proofbit_cache exp=%0d got=%b addrs=%0d,%0d,%0d,%0d ds=%h did=%0d",exp,ca_p,a0,a1,a2,a3,ds,did); end',
      'if(!(tv_s && ts_s===exp)) failures=failures+1;':'if(!(tv_s && ts_s===exp)) begin failures=failures+1; $display("DIAG OUTCOME single exp=%0d tv=%b ts=%b did=%0d stmt=%h state=%b",exp,tv_s,ts_s,did,stmt,st); end',
      'if(!(tv_b && ts_b===exp)) failures=failures+1;':'if(!(tv_b && ts_b===exp)) begin failures=failures+1; $display("DIAG OUTCOME banked exp=%0d tv=%b ts=%b did=%0d stmt=%h state=%b",exp,tv_b,ts_b,did,stmt,st); end',
      'if(!(tv_c && ts_c===exp)) failures=failures+1;':'if(!(tv_c && ts_c===exp)) begin failures=failures+1; $display("DIAG OUTCOME conventional_cache exp=%0d tv=%b ts=%b did=%0d stmt=%h state=%b",exp,tv_c,ts_c,did,stmt,st); end',
      'if(!(tv_p && ts_p===exp)) failures=failures+1;':'if(!(tv_p && ts_p===exp)) begin failures=failures+1; $display("DIAG OUTCOME proofbit_cache exp=%0d tv=%b ts=%b did=%0d stmt=%h state=%b",exp,tv_p,ts_p,did,stmt,st); end',
    }
    for old,new in replacements.items():
        if old not in text: raise RuntimeError(f'missing diagnostic anchor: {old}')
        text=text.replace(old,new)
    iverilog=shutil.which('iverilog');vvp=shutil.which('vvp')
    if not iverilog or not vvp: raise RuntimeError('iverilog/vvp required')
    with tempfile.TemporaryDirectory(prefix='pb-hw04-diag-') as td:
        dtb=Path(td)/'diag_tb.v';out=Path(td)/'sim.out';dtb.write_text(text)
        subprocess.run([iverilog,'-g2012','-s','pb_hw04_tb','-o',str(out),str(rtl),str(dtb)],check=True)
        p=subprocess.run([vvp,str(out)],text=True,capture_output=True)
        print(p.stdout,end='')
        print(p.stderr,end='')
        return p.returncode

if __name__=='__main__': raise SystemExit(main())
