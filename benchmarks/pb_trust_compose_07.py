from __future__ import annotations
import argparse, hashlib, json, statistics, struct, subprocess, sys, tempfile, time
from pathlib import Path
BENCHMARK_ID='PB-TRUST-COMPOSE-07'; VERSION='0.1'; PROTOCOL='PB-TC07/v0.1 cross-language-conformance'
MAGIC=0x50424637; CURRENT_VERSION=5; CURRENT_MASK=0x3F; CURRENT_DIGEST=0xC43CD04DF228379F; STATEMENT=0xFEDCBA9876543210; AUTHORITY=0xA17E0007; EPOCH=7
TOKEN=struct.Struct('>IHHIQQIIQQB3x'); TOKEN_LE=struct.Struct('<IHHIQQIIQQB3x'); POLICY=struct.Struct('>HHIQ')
SYSTEMS=('software_per_language','software_canonical_contract','proofbit_contract'); MODES={'software_per_language':'manual','software_canonical_contract':'canonical','proofbit_contract':'proofbit'}
def policy_digest(version:int,mask:int)->int:return int.from_bytes(hashlib.sha256(f'PB-TC07|v{version}|mask={mask}'.encode()).digest()[:8],'big')
def policy_hex()->str:return POLICY.pack(CURRENT_VERSION,0,CURRENT_MASK,CURRENT_DIGEST).hex()
def pack_token(**u)->bytes:
 v={'magic':MAGIC,'version':CURRENT_VERSION,'flags':0,'mask':CURRENT_MASK,'digest':CURRENT_DIGEST,'statement':STATEMENT,'authority':AUTHORITY,'epoch':EPOCH,'replay':11,'provenance':22,'outcome':1};v.update(u);return TOKEN.pack(v['magic'],v['version'],v['flags'],v['mask'],v['digest'],v['statement'],v['authority'],v['epoch'],v['replay'],v['provenance'],v['outcome'])
def conformance_vectors():
 old_mask=0x1F;old_digest=policy_digest(4,old_mask);little=TOKEN_LE.pack(MAGIC,CURRENT_VERSION,0,CURRENT_MASK,CURRENT_DIGEST,STATEMENT,AUTHORITY,EPOCH,11,22,1)
 return [('VALID_HIGH64',True,pack_token()),('UNKNOWN_VERSION',False,pack_token(version=6)),('UNKNOWN_REQUIRED_BIT',False,pack_token(mask=CURRENT_MASK|0x40)),('DIGEST_MISMATCH',False,pack_token(digest=CURRENT_DIGEST^1)),('LITTLE_ENDIAN_REENCODE',False,little),('OLD_CONSUMER_V4',False,pack_token(version=4,mask=old_mask,digest=old_digest,outcome=0)),('REPLAY_ZERO',False,pack_token(replay=0)),('PROVENANCE_ZERO',False,pack_token(provenance=0)),('OUTCOME_MISSING',False,pack_token(outcome=0)),('AUTHORITY_MISMATCH',False,pack_token(authority=AUTHORITY+1)),('EPOCH_MISMATCH',False,pack_token(epoch=EPOCH+1)),('RESERVED_FLAGS_NONZERO',False,pack_token(flags=1)),('TRAILING_BYTES',False,pack_token()+b'\0'),('TRUNCATED',False,pack_token()[:-1])]
def write_dataset(path,repeats):
 expected=[];lines=[]
 for _ in range(repeats):
  for name,ok,raw in conformance_vectors():expected.append(ok);lines.append(f'{name}\t{int(ok)}\t{raw.hex()}')
 path.write_text('\n'.join(lines)+'\n');return expected
def compile_rust(root,out):subprocess.run(['rustc',str(root/'benchmarks/tc07_rust_validator.rs'),'-O','-o',str(out)],check=True)
def command_for(lang,root,rust_bin,mode,policy,dataset):
 cmd={'python':[sys.executable,str(root/'benchmarks/tc07_python_validator.py')],'node':['node',str(root/'benchmarks/tc07_node_validator.js')],'rust':[str(rust_bin)]}[lang]+['--mode',mode]
 if mode!='manual':cmd+=['--policy-hex',policy]
 return cmd+[str(dataset)]
def parse_output(text,count):
 rows=[x for x in text.splitlines() if x]
 if len(rows)!=count:raise RuntimeError(f'verdict count {len(rows)} != {count}')
 return [x.rsplit('\t',1)[1]=='1' for x in rows]
def run_system(system,root,rust_bin,dataset,expected):
 mode=MODES[system];results={};start=time.perf_counter_ns()
 for lang in ('python','rust','node'):
  p=subprocess.run(command_for(lang,root,rust_bin,mode,policy_hex(),dataset),check=True,text=True,capture_output=True);results[lang]=parse_output(p.stdout,len(expected))
 elapsed=time.perf_counter_ns()-start;unsafe=missed=correct=disagree=0
 for i,oracle in enumerate(expected):
  vals=[results[x][i] for x in ('python','rust','node')];disagree+=int(len(set(vals))>1)
  for v in vals:correct+=int(v==oracle);unsafe+=int(v and not oracle);missed+=int((not v) and oracle)
 verdicts=len(expected)*3
 return {'oracle_accuracy':correct/verdicts,'unsafe_accepts':unsafe,'missed_valid':missed,'cross_language_disagreements':disagree,'elapsed_ns':elapsed,'language_validations_per_sec':verdicts/(elapsed/1e9)}
def evolution_work():
 t=CURRENT_VERSION-1;l=3
 return {'software_per_language':{'managed_policy_sources':l,'validator_source_updates':t*l,'descriptor_updates':0,'language_conformance_invocations':t*l,'wire_token_bytes':TOKEN.size},'software_canonical_contract':{'managed_policy_sources':1,'validator_source_updates':0,'descriptor_updates':t,'language_conformance_invocations':t*l,'policy_descriptor_bytes':POLICY.size,'wire_token_bytes':TOKEN.size},'proofbit_contract':{'managed_policy_sources':1,'validator_source_updates':0,'descriptor_updates':t,'language_conformance_invocations':t*l,'policy_descriptor_bytes':POLICY.size,'wire_token_bytes':TOKEN.size}}
def run(repeats,rounds):
 root=Path(__file__).resolve().parents[1];raws={s:[] for s in SYSTEMS};orders=[]
 with tempfile.TemporaryDirectory(prefix='proofbit-tc07-') as td:
  td=Path(td);dataset=td/'vectors.tsv';rust_bin=td/'tc07-rust';expected=write_dataset(dataset,repeats);compile_rust(root,rust_bin);perms=(SYSTEMS,(SYSTEMS[1],SYSTEMS[2],SYSTEMS[0]),(SYSTEMS[2],SYSTEMS[0],SYSTEMS[1]))
  for r in range(rounds):
   order=perms[r%3];orders.append(list(order))
   for s in order:raws[s].append(run_system(s,root,rust_bin,dataset,expected))
 runtime={}
 for s,rows in raws.items():runtime[s]={'oracle_accuracy':min(x['oracle_accuracy'] for x in rows),'unsafe_accepts':sum(x['unsafe_accepts'] for x in rows),'missed_valid':sum(x['missed_valid'] for x in rows),'cross_language_disagreements':sum(x['cross_language_disagreements'] for x in rows),'median_language_validations_per_sec':statistics.median(x['language_validations_per_sec'] for x in rows),'median_elapsed_ns':statistics.median(x['elapsed_ns'] for x in rows),'raw_language_validations_per_sec':[x['language_validations_per_sec'] for x in rows]}
 return {'benchmark_id':BENCHMARK_ID,'version':VERSION,'protocol':PROTOCOL,'languages':['python','rust','node'],'rounds':rounds,'repeats_per_case':repeats,'cases':[{'name':n,'expected_accept':e} for n,e,_ in conformance_vectors()],'token_bytes':TOKEN.size,'policy_descriptor_bytes':POLICY.size,'high64_statement_hex':hex(STATEMENT),'measurement_orders':orders,'runtime':runtime,'evolution_work':evolution_work(),'primary_anti_strawman':'software_canonical_contract','no_single_winner_score':True,'interpretation_rule':'Any benefit reproduced by software_canonical_contract is a canonical-contract architecture benefit, not uniquely ProofBit. Per-language code is not deliberately buggy and all systems must match the same oracle.','claim_boundary':'Real Python/Rust/Node binary parsing on one Linux runner. Update-surface counts are a frozen ownership model, not measured engineering hours. No real separate organizations, network, cryptography, silicon, novelty or universal superiority claim.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repeats-per-case',type=int,default=1000);ap.add_argument('--rounds',type=int,default=11);ap.add_argument('--json',action='store_true');a=ap.parse_args();report=run(a.repeats_per_case,a.rounds);print(json.dumps(report,indent=2,sort_keys=True) if a.json else '\n'.join(f"{s}: {r['median_language_validations_per_sec']:.1f}/s" for s,r in report['runtime'].items()));return 0
if __name__=='__main__':raise SystemExit(main())
