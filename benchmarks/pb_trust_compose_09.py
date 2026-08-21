from __future__ import annotations
import argparse, hashlib, json, statistics, struct, subprocess, sys, tempfile, time
from pathlib import Path

BENCHMARK_ID="PB-TRUST-COMPOSE-09"
VERSION="0.1"
PROTOCOL="PB-TC09/v0.1 enforcement-bypass-tcb"
MAGIC=0x50424639
VERSION_ID=5
MASK=0x1F
STATEMENT_A=0xA0A0A0A0A0A0A001
STATEMENT_B=0xB0B0B0B0B0B0B002
AUTHORITY=0xA17E0007
BASE_EPOCH=7
TOKEN=struct.Struct(">IHHIQQIIQQB3x")
SYSTEMS=("application_validator","software_reference_monitor","proofbit_execution_boundary")
ATTACK_CASES=("VALID_API","DIRECT_CALL_INVALID_AUTHORITY","ALTERNATE_ENTRYPOINT_STALE","CACHED_APPROVAL_AFTER_EPOCH_CHANGE","MUTATE_AFTER_VALIDATE_REBIND","REPLAY_AFTER_VALIDATE","DESERIALIZATION_BYPASS","FALSE_SUCCESS_SELF_REPORT")

def digest()->int:
    return int.from_bytes(hashlib.sha256(b"PB-TC09|v5|mask=31").digest()[:8],"big")

def pack_token(*, statement=STATEMENT_A, authority=AUTHORITY, epoch=BASE_EPOCH, replay=1, provenance=22)->bytes:
    return TOKEN.pack(MAGIC,VERSION_ID,0,MASK,digest(),statement,authority,epoch,replay,provenance,0)

def parse_token(raw:bytes):
    if len(raw)!=TOKEN.size:
        return None
    try:
        magic,version,flags,mask,dig,statement,authority,epoch,replay,provenance,outcome=TOKEN.unpack(raw)
    except struct.error:
        return None
    if any(raw[53:56]):
        return None
    return dict(magic=magic,version=version,flags=flags,mask=mask,digest=dig,statement=statement,
                authority=authority,epoch=epoch,replay=replay,provenance=provenance,outcome=outcome)

def app_validate(raw:bytes, requested_statement:int, current_epoch:int)->bool:
    x=parse_token(raw)
    return bool(x and x["magic"]==MAGIC and x["version"]==VERSION_ID and x["flags"]==0
                and x["mask"]==MASK and x["digest"]==digest()
                and x["statement"]==requested_statement and x["authority"]==AUTHORITY
                and x["epoch"]==current_epoch and x["replay"]!=0 and x["provenance"]!=0)

def send(proc, message):
    proc.stdin.write(json.dumps(message,separators=(",",":"))+"\n")
    proc.stdin.flush()
    line=proc.stdout.readline()
    if not line:
        err=proc.stderr.read()
        raise RuntimeError(f"worker exited: {err}")
    return json.loads(line)

def execute(proc, *, raw:bytes, requested:int, request_id:str, entrypoint:str="normal",
            force_fail:bool=False, caller_claim_success:bool=False):
    return send(proc,{"op":"execute","token_hex":raw.hex(),"requested_statement":hex(requested),
                      "request_id":request_id,"entrypoint":entrypoint,
                      "force_fail":force_fail,"caller_claim_success":caller_claim_success})

def set_epoch(proc, epoch:int):
    return send(proc,{"op":"set_epoch","epoch":epoch})

def attack_suite(system:str, proc):
    rows=[]
    rid=100
    raw=pack_token(replay=rid); rid+=1
    assert app_validate(raw,STATEMENT_A,BASE_EPOCH)
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="valid",entrypoint="normal")
    rows.append(("VALID_API",True,True,r))
    raw=pack_token(authority=AUTHORITY+1,replay=rid);rid+=1
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="direct",entrypoint="direct")
    rows.append(("DIRECT_CALL_INVALID_AUTHORITY",False,False,r))
    raw=pack_token(epoch=BASE_EPOCH-1,replay=rid);rid+=1
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="alternate",entrypoint="alternate")
    rows.append(("ALTERNATE_ENTRYPOINT_STALE",False,False,r))
    raw=pack_token(epoch=BASE_EPOCH,replay=rid);rid+=1
    assert app_validate(raw,STATEMENT_A,BASE_EPOCH)
    set_epoch(proc,BASE_EPOCH+1)
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="cached",entrypoint="cached")
    rows.append(("CACHED_APPROVAL_AFTER_EPOCH_CHANGE",False,False,r))
    set_epoch(proc,BASE_EPOCH)
    raw=pack_token(statement=STATEMENT_A,replay=rid);rid+=1
    assert app_validate(raw,STATEMENT_A,BASE_EPOCH)
    r=execute(proc,raw=raw,requested=STATEMENT_B,request_id="rebind",entrypoint="mutated")
    rows.append(("MUTATE_AFTER_VALIDATE_REBIND",False,False,r))
    raw=pack_token(replay=rid);rid+=1
    assert app_validate(raw,STATEMENT_A,BASE_EPOCH)
    first=execute(proc,raw=raw,requested=STATEMENT_A,request_id="replay-first",entrypoint="normal")
    if not first["effect"]:
        raise AssertionError(f"{system}: replay prelude did not execute")
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="replay-second",entrypoint="replay")
    rows.append(("REPLAY_AFTER_VALIDATE",False,False,r))
    raw=pack_token(replay=rid)[:-7];rid+=1
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="malformed",entrypoint="deser-bypass")
    rows.append(("DESERIALIZATION_BYPASS",False,False,r))
    raw=pack_token(replay=rid);rid+=1
    assert app_validate(raw,STATEMENT_A,BASE_EPOCH)
    r=execute(proc,raw=raw,requested=STATEMENT_A,request_id="false-success",
              entrypoint="normal",force_fail=True,caller_claim_success=True)
    rows.append(("FALSE_SUCCESS_SELF_REPORT",False,False,r))
    return rows

def summarize_attacks(system, rows):
    unsafe=false_success=wrong=0
    cases=[]
    for name,expected_effect,expected_success,r in rows:
        effect=bool(r["effect"])
        terminal = bool(r["caller_claim_success"]) if (system=="application_validator" and r["caller_claim_success"]) else bool(r["outcome_proven"])
        unsafe += int(effect and not expected_effect)
        false_success += int(terminal and not effect)
        wrong += int(effect!=expected_effect or terminal!=expected_success)
        cases.append({"name":name,"expected_effect":expected_effect,"actual_effect":effect,
                      "expected_terminal_success":expected_success,"terminal_success":terminal,
                      "authorized":bool(r["authorized"]),"outcome_proven":bool(r["outcome_proven"])})
    return {"oracle_accuracy":1-(wrong/len(rows)),"unsafe_side_effects":unsafe,
            "false_successes":false_success,"bypass_failures":wrong,"cases":cases}

def valid_path(system, proc, count:int):
    start=time.perf_counter_ns()
    for i in range(count):
        raw=pack_token(replay=100000+i)
        if system=="application_validator" and not app_validate(raw,STATEMENT_A,BASE_EPOCH):
            raise AssertionError("app valid path rejected")
        r=execute(proc,raw=raw,requested=STATEMENT_A,request_id=f"perf-{i}",entrypoint="normal")
        if not (r["effect"] and r["outcome_proven"]):
            raise AssertionError(f"{system}: valid request rejected")
    elapsed=time.perf_counter_ns()-start
    return {"elapsed_ns":elapsed,"valid_effects_per_sec":count/(elapsed/1e9)}

def run_once(system, root:Path, valid_count:int, td:Path):
    effects=td/f"{system}.effects"
    proc=subprocess.Popen([sys.executable,str(root/"benchmarks/tc09_effect_worker.py"),
                           "--mode",system,"--effects",str(effects)],
                          stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    try:
        attacks=summarize_attacks(system,attack_suite(system,proc))
        perf=valid_path(system,proc,valid_count)
        stats=send(proc,{"op":"stats"})
    finally:
        if proc.poll() is None:
            try: send(proc,{"op":"shutdown"})
            except Exception: pass
        proc.wait(timeout=5)
    return {"attacks":attacks,"valid_path":perf,"worker_stats":stats,
            "effects_file_bytes":effects.stat().st_size if effects.exists() else 0}

def tcb_surface():
    return {
      "application_validator":{"mandatory_effect_boundary_checks":0,"application_validation_sites":1,
        "protected_resource_writer_processes":1,"outcome_authority":"application_report"},
      "software_reference_monitor":{"mandatory_effect_boundary_checks":1,"application_validation_sites":0,
        "protected_resource_writer_processes":1,"outcome_authority":"worker_receipt"},
      "proofbit_execution_boundary":{"mandatory_effect_boundary_checks":1,"application_validation_sites":0,
        "protected_resource_writer_processes":1,"outcome_authority":"worker_receipt"},
    }

def run(rounds:int,valid_count:int):
    root=Path(__file__).resolve().parents[1]
    permutations=(SYSTEMS,(SYSTEMS[1],SYSTEMS[2],SYSTEMS[0]),(SYSTEMS[2],SYSTEMS[0],SYSTEMS[1]))
    raw={s:[] for s in SYSTEMS};orders=[]
    with tempfile.TemporaryDirectory(prefix="proofbit-tc09-") as base:
        base=Path(base)
        for r in range(rounds):
            order=permutations[r%3];orders.append(list(order))
            for s in order:
                td=base/f"r{r}-{s}";td.mkdir()
                raw[s].append(run_once(s,root,valid_count,td))
    runtime={};attack_summary={}
    for s,rows in raw.items():
        attack_summary[s]=rows[0]["attacks"]
        rates=[x["valid_path"]["valid_effects_per_sec"] for x in rows]
        runtime[s]={"median_valid_effects_per_sec":statistics.median(rates),"raw_valid_effects_per_sec":rates}
    return {"benchmark_id":BENCHMARK_ID,"version":VERSION,"protocol":PROTOCOL,
      "rounds":rounds,"valid_requests_per_round":valid_count,
      "attack_cases":[x["name"] for x in attack_summary["application_validator"]["cases"]],
      "attack_results":attack_summary,"runtime":runtime,"tcb_surface":tcb_surface(),
      "measurement_orders":orders,"primary_anti_strawman":"software_reference_monitor",
      "resource_isolation_assumption":"The protected effect file is writable only by the worker process in this fixture.",
      "host_escape_status":"NOT_MODELED: an attacker with direct write access to the protected resource can bypass both software reference-monitor and software ProofBit boundaries; OS/hardware isolation is a later boundary.",
      "no_single_winner_score":True,
      "claim_boundary":"Real Python subprocess worker and real file side effects over stdio IPC on one Linux runner. Logical entrypoint labels are not separate network transports. The resource-isolation assumption is explicit. No hardware, privilege-boundary, cryptographic, energy, novelty, patentability or universal-superiority claim."}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--rounds",type=int,default=11)
    ap.add_argument("--valid-requests",type=int,default=500);ap.add_argument("--json",action="store_true")
    a=ap.parse_args();r=run(a.rounds,a.valid_requests)
    print(json.dumps(r,indent=2,sort_keys=True) if a.json else
          "\n".join(f"{s}: {x['median_valid_effects_per_sec']:.1f}/s" for s,x in r["runtime"].items()))
    return 0
if __name__=="__main__":raise SystemExit(main())