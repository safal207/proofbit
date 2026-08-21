from __future__ import annotations
import argparse, hashlib, struct
from pathlib import Path
MAGIC=0x50424638; KNOWN_MASK=0x3F; STATEMENT=0xFEDCBA9876543210; AUTHORITY=0xA17E0007; EPOCH=7
TOKEN=struct.Struct('>IHHIQQIIQQB3x'); POLICY=struct.Struct('>HHIQ')
def policy_mask(v:int)->int:
    return {3:0x0F,4:0x1F,5:0x3F,6:0x7F}[v]
def policy_digest(v:int,m:int)->int:
    return int.from_bytes(hashlib.sha256(f'PB-TC08|v{v}|mask={m}'.encode()).digest()[:8],'big')
def parse_policy(h:str):
    raw=bytes.fromhex(h)
    if len(raw)!=POLICY.size: raise ValueError('length')
    v,res,m,d=POLICY.unpack(raw)
    if res!=0: raise ValueError('reserved')
    return v,m,d
def validate(raw:bytes,mode:str,artifact_version:int,policy_hex:str|None)->bool:
    if len(raw)!=TOKEN.size:return False
    try: magic,version,flags,mask,digest,statement,authority,epoch,replay,provenance,outcome=TOKEN.unpack(raw)
    except struct.error:return False
    if magic!=MAGIC or flags!=0 or any(raw[53:56]):return False
    if mode=='manual':
        if version<3 or version>artifact_version or version>5:return False
        expected_mask=policy_mask(version);expected_digest=policy_digest(version,expected_mask)
    else:
        if not policy_hex:return False
        try:pv,pm,pd=parse_policy(policy_hex)
        except ValueError:return False
        if pv>5 or pm & ~KNOWN_MASK or pd!=policy_digest(pv,pm):return False
        if version!=pv:return False
        expected_mask,expected_digest=pm,pd
    if mask!=expected_mask or digest!=expected_digest or mask & ~KNOWN_MASK:return False
    if statement!=STATEMENT or authority!=AUTHORITY or epoch!=EPOCH:return False
    if mask&0x08 and replay==0:return False
    if mask&0x10 and provenance==0:return False
    if mask&0x20 and outcome!=1:return False
    return True
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('manual','canonical','proofbit'),required=True);ap.add_argument('--artifact-version',type=int,required=True);ap.add_argument('--policy-hex');ap.add_argument('input');a=ap.parse_args();out=[]
    for line in Path(a.input).read_text().splitlines():
        if not line:continue
        name,expected,raw_hex=line.split('\t');ok=validate(bytes.fromhex(raw_hex),a.mode,a.artifact_version,a.policy_hex);out.append(f'{name}\t{int(ok)}')
    print('\n'.join(out));return 0
if __name__=='__main__':raise SystemExit(main())