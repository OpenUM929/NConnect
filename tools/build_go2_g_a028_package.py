"""Build P1 from the frozen A027 release; never train or rewrite old releases."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / 'workspace/training/quadruped'
SOURCE = GO2 / 'upload/G-A027/current/go2_a017_full_suite.zip'
SOURCE_SHA = 'e7749d0f6adc4abb2b32fca9393523b8059b8954cec068ba2c7c2930af0a7d15'
PREFIX = 'GO2_G_A028_P1'
NAME = PREFIX + '.zip'
OUT = GO2 / 'upload/G-A028/current'


def sha(data): return hashlib.sha256(data).hexdigest()


def payload():
    assert sha(SOURCE.read_bytes()) == SOURCE_SHA, 'Frozen A027 release mismatch'
    with zipfile.ZipFile(SOURCE) as z:
        base = 'go2_a017_full_suite/'
        data = {n[len(base):]: z.read(n) for n in z.namelist()
                if n.startswith((base+'a017/', base+'pilot/')) and not n.endswith('/')}
        for n in ['package_go2_result.py', 'posture_contract_check.py', 'go2_self_eval_registry.json']:
            data[n] = z.read(base+n)
        old = z.read(base+'server_run_go2_a017_full_suite.sh').decode().replace('\r\n','\n')
        data['a027_case_definitions.sh'] = ('#!/usr/bin/env bash\n'+old[old.index('PLANE=('):old.index('posture_ok()')]).encode()
    data['server_run_GO2_G_A028.sh'] = (GO2/'server_run_GO2_G_A028.sh').read_bytes().replace(b'\r\n', b'\n')
    spec = {'work_id':'G-A028', 'phase':'P1_DIAGNOSIS', 'training':False,
            'source_release_sha256':SOURCE_SHA, 'num_envs':4, 'steps':1000,
            'cases':[{'policy':p,'case':c,'seed':s} for p in ['a017','pilot']
                     for s in [101,202,303] for c in ['stairs_10_down','stairs_15_down','slope_plus_20']],
            'required':['video','telemetry','summary','logs','model','env','SHA256SUMS'],
            'report_status':{'a017':'MISSING','pilot':'READ_UNMATCHED','new_training':'NOT_APPLICABLE'},
            'limitations':['Not a 70-point evaluation','4-env rollout is not A027 32-env rollout',
                          'No wx/wy or foot-contact channels; rotation cause remains unconfirmed',
                          'Video/telemetry frame alignment requires post-run verification'],
            'next_training':'HOLD; diagnosis and report identity required'}
    data['P1_SPEC.json'] = (json.dumps(spec,indent=2)+'\n').encode()
    data['PACKAGE_SHA256SUMS.txt'] = ''.join(f'{sha(v)}  {n}\n' for n,v in sorted(data.items())).encode()
    return data


def build(out=OUT):
    data=payload()
    out.mkdir(parents=True,exist_ok=True)
    target=out/NAME
    # Repeatable creation; published conflicting bytes are never overwritten.
    import io
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for name,content in sorted(data.items()):
            info=zipfile.ZipInfo(PREFIX+'/'+name,(2026,9,13,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o755 if name.endswith('.sh') else 0o644)<<16
            z.writestr(info,content)
    content=buf.getvalue()
    if target.exists() and target.read_bytes()!=content: raise RuntimeError('Existing release differs; preserve it')
    target.write_bytes(content)
    digest=sha(content)
    (out/(NAME+'.sha256')).write_text(f'{digest}  {NAME}\n',encoding='ascii')
    guide=f'''GO2 G-A028 P1 — 낙상 진단 실행 (새 학습 없음)
업로드 파일: {target}
서버 위치: /workspace/{NAME}
한 줄 실행:
cd /workspace && echo '{digest}  {NAME}' | sha256sum -c - && test ! -e /workspace/{PREFIX} && unzip -q {NAME} && bash /workspace/{PREFIX}/server_run_GO2_G_A028.sh
관찰: tmux attach -t go2_G_A028
완료 표식: [DONE] GO2_G_A028_P1_RESULT_READY
결과 회수: /workspace/_keep/GO2_G_A028_RESULT.zip 및 같은 이름의 .sha256
예상: 18회 재생, 약 15~30분 계획 추정(이 패키지 서버 실측 아님). 첫 case 소요를 보고 재산정.
중단: tmux에서 Ctrl-C. PARTIAL ZIP 생성 여부 확인 후 회수. 기존 결과가 있으면 재실행을 거부하며 삭제하지 않음.
필수: 18영상·동일 실행 telemetry·각 로그·model/env·SHA. 로컬 검증 전 서버 종료 가능 판정 없음.
report: 평가 전용이므로 새 학습 HTML은 생성하지 않음. 기존 A017 HTML 누락은 계속 명시.
G4/G5 진단만 수행; 기존 A027 69case는 재사용. /70 점수·reward 효과 판정 없음.
새 학습의 report.html 회수 개선은 별도 공용 학습 runner에 구현되어 있으며 이 재생은 학습하지 않음.
'''
    (out/'GO2_G_A028_RUN_GUIDE.txt').write_text(guide,encoding='utf-8',newline='\n')
    (out/'GO2_G_A028_RUN_GUIDE.txt.sha256').write_text(f"{sha((out/'GO2_G_A028_RUN_GUIDE.txt').read_bytes())}  GO2_G_A028_RUN_GUIDE.txt\n",encoding='ascii')
    (out/'CURRENT_UPLOAD.txt').write_text(f'G-A028 P1_DIAGNOSIS — upload only {NAME}\nNot a training release. Read GO2_G_A028_RUN_GUIDE.txt\n',encoding='utf-8')
    (out/'UPLOAD_MANIFEST.json').write_text(json.dumps({'experiment_id':'G-A028','release_id':'20260913_p1','status':'LOCAL_VALIDATION_PENDING','training':False,'upload_files':[{'name':NAME,'sha256':digest,'server_path':'/workspace/'+NAME}]},indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for n,v in data.items(): assert z.read(PREFIX+'/'+n)==v
    return target


if __name__=='__main__': print(build())
