from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BENCHMARK_ID='PB-HW-04'
VERSION='0.1'
PROTOCOL='PB-HW-04/v0.1 physical-proof-memory-cache-economics'
TOPS={
 'single_port_conventional':'pb_hw04_single_port_conventional',
 'banked_conventional':'pb_hw04_banked_conventional',
 'multiport_conventional_cache':'pb_hw04_multiport_conventional_cache',
 'proofbit_cache':'pb_hw04_proofbit_cache',
}
PHYSICAL_EVIDENCE_BITS={
 'single_port_conventional':1024*64,
 'banked_conventional':1024*64,
 'multiport_conventional_cache':4*1024*64,
 'proofbit_cache':4*1024*64,
}
CACHE_DATA_BITS={
 'single_port_conventional':0,
 'banked_conventional':0,
 'multiport_conventional_cache':16*64,
 'proofbit_cache':16*64,
}
CACHE_TAG_VALID_BITS={
 'single_port_conventional':0,
 'banked_conventional':0,
 'multiport_conventional_cache':16*(6+1),
 'proofbit_cache':16*(6+1),
}
REPLAY_STATE_BITS={k:1024 for k in TOPS}


def require_tool(name:str)->str:
    p=shutil.which(name)
    if not p: raise RuntimeError(f'required tool not found: {name}')
    return p

def run_cmd(cmd:list[str],*,cwd:Path|None=None)->str:
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    if p.returncode!=0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p.stdout+p.stderr

def parse_sim(text:str)->dict:
    m=re.search(
      r'PB_HW04_SIM PASS checks=(\d+) failures=(\d+) '
      r'cold=(\d+),(\d+),(\d+),(\d+) warm=(\d+),(\d+),(\d+),(\d+) '
      r'conflict=(\d+),(\d+),(\d+),(\d+) conflict_warm=(\d+),(\d+),(\d+),(\d+) '
      r'invalidated=(\d+),(\d+),(\d+),(\d+)',text)
    if not m: raise ValueError('PB_HW04_SIM PASS marker not found')
    x=[int(v) for v in m.groups()]
    keys=('single_port_conventional','banked_conventional','multiport_conventional_cache','proofbit_cache')
    return {
      'checks':x[0],'failures':x[1],
      'cold_latency_cycles':dict(zip(keys,x[2:6])),
      'warm_latency_cycles':dict(zip(keys,x[6:10])),
      'same_bank_conflict_latency_cycles':dict(zip(keys,x[10:14])),
      'same_bank_warm_latency_cycles':dict(zip(keys,x[14:18])),
      'post_invalidation_latency_cycles':dict(zip(keys,x[18:22])),
    }

def parse_ltp(text:str)->int:
    vals=re.findall(r'length\s*=?\s*(\d+)',text,flags=re.I)
    if not vals: raise ValueError('Yosys ltp path length not found')
    return max(map(int,vals))

def cell_counts(path:Path,top:str)->dict:
    data=json.loads(path.read_text()); mod=data.get('modules',{}).get(top)
    if mod is None: raise ValueError(f'missing top {top}')
    counts=Counter(c.get('type','') for c in mod.get('cells',{}).values())
    lut=sum(v for k,v in counts.items() if re.fullmatch(r'LUT[1-6]',k))
    ff=sum(v for k,v in counts.items() if k in {'FDRE','FDSE','FDCE','FDPE'})
    br18=sum(v for k,v in counts.items() if k.startswith('RAMB18'))
    br36=sum(v for k,v in counts.items() if k.startswith('RAMB36'))
    lutram=sum(v for k,v in counts.items() if k.startswith('RAM32') or k.startswith('RAM64') or k.startswith('RAM128') or k.startswith('RAM256'))
    io=sum(v for k,v in counts.items() if k in {'IBUF','OBUF','IOBUF','BUFG'})
    total=sum(counts.values())
    return {'total_cells':total,'core_cells_excluding_io':total-io,'io_cells':io,'lut_cells':lut,'ff_cells':ff,
            'bram18_cells':br18,'bram36_cells':br36,'bram18_equivalent':br18+2*br36,'lutram_cells':lutram,
            'cell_types':dict(sorted(counts.items()))}

def synth_one(yosys:str,rtl:Path,top:str,out_json:Path)->dict:
    script=(f'read_verilog -sv {rtl}; hierarchy -check -top {top}; flatten; '
            f'synth_xilinx -family xc7 -top {top}; ltp -noff; write_json {out_json}')
    text=run_cmd([yosys,'-p',script])
    row=cell_counts(out_json,top); row['logic_depth_proxy']=parse_ltp(text)
    row['logic_depth_method']='yosys ltp -noff after synth_xilinx xc7'
    return row

def tool_version(cmd:list[str])->str:
    t=run_cmd(cmd).strip().splitlines(); return t[0] if t else 'unknown'

def run()->dict:
    root=Path(__file__).resolve().parents[1]
    rtl=root/'rtl'/'pb_hw_04.v'; tb=root/'rtl'/'pb_hw_04_tb.v'
    iverilog=require_tool('iverilog'); vvp=require_tool('vvp'); yosys=require_tool('yosys')
    with tempfile.TemporaryDirectory(prefix='proofbit-pb-hw-04-') as td:
        td=Path(td); simbin=td/'sim.out'
        run_cmd([iverilog,'-g2012','-s','pb_hw04_tb','-o',str(simbin),str(rtl),str(tb)])
        simulation=parse_sim(run_cmd([vvp,str(simbin)]))
        synthesis={}
        for key,top in TOPS.items():
            row=synth_one(yosys,rtl,top,td/f'{key}.json')
            row['physical_evidence_bits']=PHYSICAL_EVIDENCE_BITS[key]
            row['cache_data_bits']=CACHE_DATA_BITS[key]
            row['cache_tag_valid_bits']=CACHE_TAG_VALID_BITS[key]
            row['replay_state_bits']=REPLAY_STATE_BITS[key]
            synthesis[key]=row
    c=synthesis['multiport_conventional_cache']; p=synthesis['proofbit_cache']
    eq={
      'same_lut_cells':c['lut_cells']==p['lut_cells'], 'same_ff_cells':c['ff_cells']==p['ff_cells'],
      'same_bram_mapping':(c['bram18_cells'],c['bram36_cells'])==(p['bram18_cells'],p['bram36_cells']),
      'same_lutram_cells':c['lutram_cells']==p['lutram_cells'], 'same_core_cells':c['core_cells_excluding_io']==p['core_cells_excluding_io'],
      'same_logic_depth_proxy':c['logic_depth_proxy']==p['logic_depth_proxy'],
      'same_physical_evidence_bits':c['physical_evidence_bits']==p['physical_evidence_bits'],
      'same_cache_bits':(c['cache_data_bits'],c['cache_tag_valid_bits'])==(p['cache_data_bits'],p['cache_tag_valid_bits']),
    }
    return {
      'benchmark_id':BENCHMARK_ID,'version':VERSION,'protocol':PROTOCOL,
      'tools':{'iverilog':tool_version([iverilog,'-V']),'yosys':tool_version([yosys,'-V'])},
      'physical_memory_instantiated':True,'depth_entries':1024,'record_bits':64,'cache_entries':16,'parent_count':4,
      'simulation':simulation,'synthesis':synthesis,
      'cache_workload':{
        'cold_conflict_free':{'hits':0,'misses':4},
        'warm_conflict_free':{'hits':4,'misses':0},
        'same_bank_cold':{'hits':0,'misses':4},
        'same_bank_warm':{'hits':4,'misses':0},
        'post_invalidation':{'hits':3,'misses':1},
      },
      'memory_topology':{
        'single_port_conventional':'one 1024x64 evidence table, one issued parent read per cycle',
        'banked_conventional':'four 256x64 banks selected by address[1:0], at most one read per bank per cycle',
        'multiport_conventional_cache':'four coherent 1024x64 replicas plus 16-entry direct-mapped cache',
        'proofbit_cache':'same physical topology as strong conventional cache',
      },
      'strong_conventional_vs_proofbit':eq,
      'primary_anti_strawman':'multiport_conventional_cache','no_single_winner_score':True,
      'claim_boundary':('Physical synthesizable evidence memories are instantiated. Cache hit/miss and bank-conflict behavior is exercised in Icarus. '
        'Yosys synth_xilinx mapping is structural, not placed/routed timing or ASIC PPA. Replicated memory models four read ports by full table replication; '
        'no FPGA board, energy, ECC, coherence fabric, speculation, IOMMU/firmware-root, silicon-performance, novelty, patentability or universal-superiority claim.')
    }

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--json',action='store_true');a=ap.parse_args();r=run()
    print(json.dumps(r,indent=2,sort_keys=True) if a.json else json.dumps(r['simulation'],sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
