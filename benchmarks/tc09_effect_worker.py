from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from proofbit.model import Evidence, ProofProcessor

MAGIC=0x50424639
VERSION_ID=5
MASK=0x1F
AUTHORITY=0xA17E0007
BASE_EPOCH=7
TOKEN=struct.Struct(">IHHIQQIIQQB3x")

def digest()->int:
    return int.from_bytes(hashlib.sha256(b"PB-TC09|v5|mask=31").digest()[:8],"big")

def parse_token(raw:bytes):
    if len(raw)!=TOKEN.size:
        return None
    try:
        magic,version,flags,mask,dig,statement,authority,epoch,replay,provenance,outcome=TOKEN.unpack(raw)
    except struct.error:
        return None
    if any(raw[53:56]):
        return None
    if magic!=MAGIC or version!=VERSION_ID or flags!=0 or mask!=MASK or dig!=digest():
        return None
    if replay==0 or provenance==0:
        return None
    return dict(statement=statement,authority=authority,epoch=epoch,replay=replay,provenance=provenance)

class Worker:
    def __init__(self,mode:str,effects:Path):
        self.mode=mode
        self.effects=effects
        self.epoch=BASE_EPOCH
        self.seen=set()
        self.effect_count=0
        self.proof=ProofProcessor(authority=AUTHORITY,epoch=BASE_EPOCH)

    def monitor_authorize(self,raw:bytes,requested:int)->bool:
        x=parse_token(raw)
        if not x or x["statement"]!=requested or x["authority"]!=AUTHORITY or x["epoch"]!=self.epoch:
            return False
        if x["replay"] in self.seen:
            return False
        self.seen.add(x["replay"])
        return True

    def proof_authorize(self,raw:bytes,requested:int)->bool:
        x=parse_token(raw)
        if not x:
            return False
        self.proof.epoch=self.epoch
        evidence=Evidence(statement=f"statement:{x['statement']:016x}",value=True,
                          proof_id=x["replay"],authority=x["authority"],epoch=x["epoch"],
                          provenance=x["provenance"])
        address=1
        self.proof.store_evidence(address,evidence)
        return self.proof.guarded_execute(address,single_use=True,
            expected_statement=f"statement:{requested:016x}")

    def authorize(self,raw:bytes,requested:int)->bool:
        if self.mode=="application_validator":
            return True
        if self.mode=="software_reference_monitor":
            return self.monitor_authorize(raw,requested)
        if self.mode=="proofbit_execution_boundary":
            return self.proof_authorize(raw,requested)
        raise ValueError(self.mode)

    def execute(self,msg):
        try:
            raw=bytes.fromhex(msg.get("token_hex",""))
            requested=int(msg["requested_statement"],16)
        except Exception:
            raw=b"";requested=0
        authorized=self.authorize(raw,requested)
        effect=False
        if authorized and not bool(msg.get("force_fail",False)):
            with self.effects.open("a",encoding="utf-8") as f:
                f.write(f"{msg.get('request_id','?')}\t{requested:016x}\n")
                f.flush()
            self.effect_count+=1
            effect=True
        return {"authorized":authorized,"effect":effect,"outcome_proven":effect,
            "caller_claim_success":bool(msg.get("caller_claim_success",False)),
            "entrypoint":msg.get("entrypoint","normal")}

    def handle(self,msg):
        op=msg.get("op")
        if op=="execute":
            return self.execute(msg)
        if op=="set_epoch":
            self.epoch=int(msg["epoch"]);self.proof.epoch=self.epoch
            return {"ok":True,"epoch":self.epoch}
        if op=="stats":
            return {"effect_count":self.effect_count,"epoch":self.epoch,
                    "seen_replays":len(self.seen),"proof_consumed":len(self.proof.consumed_proofs)}
        if op=="shutdown":
            return {"ok":True,"shutdown":True}
        return {"ok":False,"error":"unknown op"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("application_validator","software_reference_monitor","proofbit_execution_boundary"),required=True)
    ap.add_argument("--effects",required=True)
    a=ap.parse_args()
    w=Worker(a.mode,Path(a.effects))
    for line in sys.stdin:
        if not line.strip():
            continue
        msg=json.loads(line)
        out=w.handle(msg)
        print(json.dumps(out,separators=(",",":")),flush=True)
        if out.get("shutdown"):
            break
    return 0
if __name__=="__main__":raise SystemExit(main())