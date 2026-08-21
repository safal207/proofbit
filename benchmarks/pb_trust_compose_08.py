from __future__ import annotations
import argparse, hashlib, json, statistics, struct, subprocess, sys, tempfile, time
from pathlib import Path
BENCHMARK_ID='PB-TRUST-COMPOSE-08';VERSION='0.1';PROTOCOL='PB-TC08/v0.1 independent-release-skew'
MAGIC=0x50424638;KNOWN_MASK=0x3F;STATEMENT=0xFEDCBA9876543210;AUTHORITY=0xA17E0007;EPOCH=7
TOKEN=struct.Struct('>IHHIQQIIQQB3x');POLICY=struct.Struct('>HHIQ')
SYSTEMS=('software_per_language_artifacts','software_canonical_runtime','proofbit_contract');MODES={'software_per_language_artifacts':'manual','software_canonical_runtime':'canonical','proofbit_contract':'proofbit'}
LANGS=('python','rust','node')
SCENARIOS=(
 ('ALIGNED_V3',{'python':3,'rust':3,'node':3},3),
 ('SKEW_LATEST_V5',{'python':5,'rust':4,'node':3},5),
 ('NEGOTIATED_DOWNGRADE_V3',{'python':5,'rust':4,'node':3},3),
 ('ALIGNED_V5',{'python':5,'rust':5,'node':5},5),
 ('NEW_PRIMITIVE_V6',{'python':5,'rust':5,'node':5},6),
)
def policy_mask(v:int)->int:return {3:0x0F,4:0x1F,5:0x3F,6:0x7F}[v]
def policy_digest(v:int,m:int)->int:return int.from_bytes(hashlib.sha256(f'PB-TC08|v{v}|mask={m}'.encode()).digest()[:8],'big')
def policy_hex(v:int)->str:
 m=policy_mask(v);return POLICY.pack(v,0,m,policy_digest(v,m)).hex()
def pack_token(v:int,**u)->bytes:
 m=policy_mask(v);d=policy_digest(v,m);x={'magic':MAGIC,'version':v,'flags':0,'mask':m,'digest':d,'statement':STATEMENT,'authority':AUTHORITY,'epoch':EPOCH,'replay':11,'provenance':22,'outcome':1};x.update(u);return TOKEN.pack(x['magic'],x['version'],x['flags'],x['mask'],x['digest'],x['statement'],x['authority'],x['epoch'],x['replay'],x['provenance'],x['outcome'])
def cases(v:int):
 m=policy_mask(v);d=policy_digest(v,m)
 return [
  ('VALID',True,pack_token(v)),
  ('DIGEST_MISMATCH',False,pack_token(v,digest=d^1)),
  ('REPLAY_ZERO',False if m&0x08 else True,pack_token(v,replay=0)),
  ('PROVENANCE_ZERO',False if m&0x10 else True,pack_token(v,provenance=0)),
  ('OUTCOME_ZERO',False if m&0x20 else True,pack_token(v,outcome=0)),
  ('TRUNCATED',False,pack_token(v)[:-1]),
 ]
def write_dataset(path:Path,v:int,repeats:int):
 rows=[];expected=[]
 for _ in range(repeats):
  for name,ok,raw in cases(v):rows.append(f'{name}\t{int(ok)}\t{raw.hex()}');expected.append((name,ok))
 path.write_text('\n'.join(rows)+'\n');return expected
def compile_rust(root:Path,out:Path):subprocess.run(['rustc',str(root/'benchmarks/tc08_rust_validator.rs'),'-O','-o',str(out)],check=True)
def command(lang,root,rust_bin,mode,av,ph,dataset):
 base={'python':[sys.executable,str(root/'benchmarks/tc08_python_validator.py')],'rust':[str(rust_bin)],'node':['node',str(root/'benchmarks/tc08_node_validator.js')]}[lang]
 cmd=base+['--mode',mode,'--artifact-version',str(av)]
 if mode!='manual':cmd+=['--policy-hex',ph]
 return cmd+[str(dataset)]
def parse(text,count):
 rows=[x for x in text.splitlines() if x]
 if len(rows)!=count:raise RuntimeError(f'rows {len(rows)} != {count}')
 return [(x.rsplit('\t',1)[0],x.rsplit('\t',1)[1]=='1') for x in rows]
def run_scenario(system,scenario,root,rust_bin,dataset,expected):
 name,artifacts,pv=scenario;mode=MODES[system];lang_results={};start=time.perf_counter_ns()
 for lang in LANGS:
  p=subprocess.run(command(lang,root,rust_bin,mode,artifacts[lang],policy_hex(pv),dataset),check=True,text=True,capture_output=True)
  lang_results[lang]=parse(p.stdout,len(expected))
 elapsed=time.perf_counter_ns()-start;unsafe=0;fault_total=0;fault_correct=0;disagreements=0;valid_accepts=0
 for i,(case_name,oracle) in enumerate(expected):
  vals=[lang_results[l][i][1] for l in LANGS]
  disagreements+=int(len(set(vals))>1)
  if case_name=='VALID':valid_accepts+=sum(vals)
  if not oracle:
   fault_total+=len(vals);fault_correct+=sum(not x for x in vals);unsafe+=sum(vals)
 return {'scenario':name,'unsafe_accepts':unsafe,'fault_rejection_accuracy':fault_correct/fault_total if fault_total else 1.0,'cross_language_disagreements':disagreements,'valid_accepts':valid_accepts,'valid_opportunities':expected.count(('VALID',True))*len(LANGS),'elapsed_ns':elapsed,'language_validations_per_sec':len(expected)*len(LANGS)/(elapsed/1e9)}
def release_work():
 return {
  'software_per_language_artifacts':{'managed_trust_sources':3,'trust_source_releases_v3_to_v5':6,'descriptor_updates_v3_to_v5':0,'v6_new_primitive_validator_updates_required':3},
  'software_canonical_runtime':{'managed_trust_sources':1,'trust_source_releases_v3_to_v5':0,'descriptor_updates_v3_to_v5':2,'v6_new_primitive_validator_updates_required':3},
  'proofbit_contract':{'managed_trust_sources':1,'trust_source_releases_v3_to_v5':0,'descriptor_updates_v3_to_v5':2,'v6_new_primitive_validator_updates_required':3},
 }
def run(repeats:int,rounds:int):
 root=Path(__file__).resolve().parents[1];orders=[];raw={s:[] for s in SYSTEMS};scenario_static={}
 with tempfile.TemporaryDirectory(prefix='proofbit-tc08-') as td:
  td=Path(td);rust_bin=td/'tc08-rust';compile_rust(root,rust_bin);datasets={}
  for sc in SCENARIOS:
   path=td/f'{sc[0]}.tsv';expected=write_dataset(path,sc[2],repeats);datasets[sc[0]]=(path,expected)
  perms=(SYSTEMS,(SYSTEMS[1],SYSTEMS[2],SYSTEMS[0]),(SYSTEMS[2],SYSTEMS[0],SYSTEMS[1]))
  for r in range(rounds):
   order=perms[r%3];orders.append(list(order))
   for s in order:
    row=[]
    for sc in SCENARIOS:
     path,expected=datasets[sc[0]];row.append(run_scenario(s,sc,root,rust_bin,path,expected))
    raw[s].append(row)
  for s in SYSTEMS:
   sample=raw[s][0]
   scenario_static[s]={x['scenario']:{'valid_availability':x['valid_accepts']/x['valid_opportunities'],'fault_rejection_accuracy':x['fault_rejection_accuracy'],'unsafe_accepts_per_round':x['unsafe_accepts'],'cross_language_disagreements_per_round':x['cross_language_disagreements']} for x in sample}
 runtime={}
 for s,round_rows in raw.items():
  rates=[]
  for rr in round_rows:
   elapsed=sum(x['elapsed_ns'] for x in rr);validations=sum((len(cases(sc[2]))*repeats*len(LANGS)) for sc in SCENARIOS);rates.append(validations/(elapsed/1e9))
  runtime[s]={'median_language_validations_per_sec':statistics.median(rates),'raw_language_validations_per_sec':rates,'unsafe_accepts_total':sum(x['unsafe_accepts'] for rr in round_rows for x in rr)}
 v3_mask=policy_mask(3);v5_mask=policy_mask(5)
 return {'benchmark_id':BENCHMARK_ID,'version':VERSION,'protocol':PROTOCOL,'languages':list(LANGS),'rounds':rounds,'repeats_per_case':repeats,'token_bytes':TOKEN.size,'policy_descriptor_bytes':POLICY.size,'scenarios':[{'name':n,'artifact_versions':a,'active_policy_version':v} for n,a,v in SCENARIOS],'scenario_results':scenario_static,'runtime':runtime,'release_work':release_work(),'downgrade_tradeoff':{'from_policy_version':5,'to_policy_version':3,'required_primitives_v5':v5_mask.bit_count(),'required_primitives_v3':v3_mask.bit_count(),'relative_guarantee_coverage':v3_mask.bit_count()/v5_mask.bit_count(),'lost_guarantees':['provenance','outcome']},'primary_anti_strawman':'software_canonical_runtime','new_primitive_rule':'v6 adds bit 0x40 outside the frozen validator primitive set; all current systems must fail closed and all three language validators require semantic/runtime updates in this software fixture.','measurement_orders':orders,'no_single_winner_score':True,'claim_boundary':'Real Python/Rust/Node subprocess parsing with frozen artifact-version configurations on one Linux checkout. Release counts are a model of trust-policy ownership, not package-registry telemetry or measured engineering hours. No network, cryptography, hardware, novelty or universal superiority claim.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repeats-per-case',type=int,default=250);ap.add_argument('--rounds',type=int,default=11);ap.add_argument('--json',action='store_true');a=ap.parse_args();r=run(a.repeats_per_case,a.rounds);print(json.dumps(r,indent=2,sort_keys=True) if a.json else '\n'.join(f"{s}: {x['median_language_validations_per_sec']:.1f}/s" for s,x in r['runtime'].items()));return 0
if __name__=='__main__':raise SystemExit(main())