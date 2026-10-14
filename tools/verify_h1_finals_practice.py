"""Verify completed practice evidence and draw a standalone map/trajectory SVG."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import subprocess
from pathlib import Path


def verify(folder: Path, decode_video=True, expected_checkpoint_sha=None):
    summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
    arena = json.loads((folder / 'map.json').read_text(encoding='utf-8'))
    rows = list(csv.DictReader((folder / 'steps.csv').open(encoding='utf-8',newline='')))
    errors = []
    requested = meta['duration_requested']
    if not summary['completed'] or abs(summary['simulated_seconds']-requested) > .021:
        errors.append('incomplete_duration')
    teams = summary['teams']
    events = summary['events']
    owners = set()
    cube_values = {c['id']:c['value'] for c in arena['cubes']}
    cubes = {c['id']:c for c in arena['cubes']}
    positions = {(r['team'],int(r['step'])):r for r in rows}
    for event in events:
        if not 0 <= event['time_s'] <= min(180,requested):
            errors.append('event_outside_match')
        if event['event'] == 'cube':
            if event['cube_id'] in owners or event['value'] != cube_values.get(event['cube_id']):
                errors.append('invalid_cube_award')
            owners.add(event['cube_id'])
            sample = positions.get((event['team'],round(event['time_s']/.02)))
            cube = cubes.get(event['cube_id'])
            if sample is None or cube is None or math.dist((float(sample['x']),float(sample['y'])),(cube['x'],cube['y'])) >= .6:
                errors.append('cube_not_reached_in_telemetry')
        elif event['event'] == 'fall':
            sample = positions.get((event['team'],round(event['time_s']/.02)))
            if sample is None or sample['terminated'] != 'True':
                errors.append('fall_without_termination')
    for team in ('blue','red'):
        selected = [r for r in rows if r['team'] == team]
        if len(selected) != round(requested/.02):
            errors.append(team+'_row_count')
        if any(int(r['step']) != i+1 or abs(float(r['time_s'])-(i+1)*.02)>1e-7 for i,r in enumerate(selected)):
            errors.append(team+'_time_sequence')
        if any(not math.isfinite(float(r[k])) for r in selected for k in ('x','y','z','vx','wz')):
            errors.append(team+'_nonfinite')
        team_events = [e for e in events if e['team']==team]
        score = sum(e['value'] for e in team_events)
        falls = sum(e['event']=='fall' for e in team_events)
        collisions = sum(e['event']=='car_collision' for e in team_events)
        count = sum(e['event']=='cube' for e in team_events)
        if (score,falls,collisions,count) != tuple(teams[team][k] for k in ('score','falls','collisions','cube_count')):
            errors.append(team+'_score_mismatch')
    expected_checkpoint_sha = expected_checkpoint_sha or '8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636'
    if meta['checkpoint_sha256'] != expected_checkpoint_sha:
        errors.append('wrong_checkpoint')
    dual_report = None
    if meta.get('dual_llm'):
        decisions = json.loads((folder/'llm_decisions.json').read_text(encoding='utf-8'))
        strategies = meta.get('team_strategies',{})
        if not strategies.get('blue') or strategies.get('blue') != strategies.get('red'):
            errors.append('dual_strategy_mismatch')
        counts = {team:sum(d.get('team')==team and bool(d.get('choice')) for d in decisions) for team in ('blue','red')}
        for team,count in counts.items():
            if not count or count != summary.get('llm_calls_by_team',{}).get(team):
                errors.append(team+'_llm_calls_missing')
        for decision in decisions:
            if 'error' in decision:
                errors.append('dual_llm_request_error')
            choice = decision.get('choice')
            if choice and (strategies['blue'] not in choice['request']['prompt'] or 'tactical_context' not in choice['request']['prompt']):
                errors.append('dual_prompt_or_context_missing')
            if choice:
                try:
                    context = json.loads(choice['request']['prompt'].split('tactical_context:',1)[1])
                    opponent = 'red' if decision['team']=='blue' else 'blue'
                    if 'current_target' in context['opponent'] or 'target_id' in context['opponent']:
                        errors.append('private_opponent_target_leak')
                    for sample in context['opponent']['observed_history']:
                        sample_time = sample['time_s']
                        if sample_time > decision['time_s']:
                            errors.append('future_observation_leak')
                        if sample_time > 0:
                            actual = positions.get((opponent,round(sample_time/.02)))
                            if actual is None or math.dist((sample['x'],sample['y']),(float(actual['x']),float(actual['y'])))>1e-5:
                                errors.append('opponent_observation_mismatch')
                    if choice['target']['id'] not in choice['request']['reachable_ids']:
                        errors.append('invalid_llm_target')
                except (KeyError,ValueError,IndexError,TypeError):
                    errors.append('invalid_tactical_context')
        dual_report = {'same_strategy': strategies.get('blue')==strategies.get('red'), 'successful_calls':counts}
    video = folder/'practice.mp4'
    car_metrics = vehicle_metrics(arena, rows)
    video_result = {'required': requested > 2, 'decoded': False}
    if decode_video and video.exists():
        import imageio_ffmpeg
        result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
        video_result.update(decoded=result.returncode==0, error=result.stderr[:1000])
        if result.returncode:
            errors.append('video_decode')
    elif video_result['required']:
        errors.append('video_not_verified')
    svg_map(folder,arena,rows)
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file() and p.name not in ('verification.json','SHA256SUMS.json')}
    (folder/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    report = {'artifact_status':'ARTIFACT_VERIFIED' if not errors else 'ARTIFACT_VERIFICATION_FAILED',
              'errors':errors,'row_count':len(rows),'event_count':len(events),'video':video_result,
              'vehicle_metrics':car_metrics,
              'dual_llm':dual_report,
              'video_behavior':'VIDEO_UNKNOWN','official_result':False,'llm_tested':summary['llm_tested']}
    (folder/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def vehicle_metrics(arena, rows):
    route=arena['car']['route']
    route=route if route[0]==route[-1] else route+[route[0]]
    lengths=[math.dist(a,b) for a,b in zip(route,route[1:])]
    result={}
    for team in ('blue','red'):
        distance_min=math.inf
        clearance_min=math.inf
        track_steps=overlap_steps=0
        previous_overlap=False
        overlap_entries=0
        for row in rows:
            if row['team']!=team or row['terminated']=='True':
                continue
            # Runner positions the car from pre-step time and checks post-step robot pose.
            elapsed=max(0,float(row['time_s'])-.02)
            d=elapsed*arena['car']['assumed_speed_mps']%sum(lengths)
            for a,b,length in zip(route,route[1:],lengths):
                if d<=length:
                    car=[a[j]+(b[j]-a[j])*d/length for j in range(2)]
                    break
                d-=length
            x,y=float(row['x']),float(row['y'])
            dx,dy=abs(x-car[0]),abs(y-car[1])
            distance_min=min(distance_min,math.hypot(dx,dy))
            # Same expanded axis-aligned footprint as the runner, not physical contact telemetry.
            clearance_min=min(clearance_min,max(dx-1,dy-.7))
            overlap=dx<1 and dy<.7
            overlap_steps+=overlap
            overlap_entries+=overlap and not previous_overlap
            previous_overlap=overlap
            track_steps+=any(o['kind']=='car_track' and abs(x-o['cx'])<=o['sx']/2 and abs(y-o['cy'])<=o['sy']/2 for o in arena['obstacles'])
        result[team]={'minimum_center_distance_m':None if math.isinf(distance_min) else round(distance_min,4),
                      'minimum_expanded_box_clearance_m':None if math.isinf(clearance_min) else round(clearance_min,4),
                      'track_exposure_seconds':round(track_steps*.02,3),
                      'overlap_seconds':round(overlap_steps*.02,3),'overlap_entries':overlap_entries,
                      'method':'assumed axis-aligned footprint, excluding post-reset termination samples'}
    return result


def svg_map(folder, arena, rows):
    meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    robot_name=html.escape(meta.get('robot_type','h1').upper())
    def xy(x,y):
        return 50+(float(x)+12)*30,50+(10-float(y))*30
    elements=['<svg xmlns="http://www.w3.org/2000/svg" width="820" height="740" viewBox="0 0 820 740">',
              '<rect width="820" height="740" fill="#faf9f5"/>',
              f'<text x="50" y="26" font-family="sans-serif" font-size="17">{robot_name} practice: assumed map / measured trajectories</text>']
    palette={'wall':'#555','maze_wall':'#555','box_hill':'#b99472','stairs':'#87a8c5','stairs_platform':'#87a8c5','ramp':'#82b997','ramp_platform':'#82b997','car_track':'#f6d2cc'}
    for o in arena['obstacles']:
        x,y=xy(o['cx']-o['sx']/2,o['cy']+o['sy']/2)
        elements.append(f'<rect x="{x}" y="{y}" width="{o["sx"]*30}" height="{o["sy"]*30}" fill="{palette[o["kind"]]}" opacity=".8"/>')
    for team,color in [('blue','#236ce0'),('red','#d33040')]:
        points=[]
        selected=[r for r in rows if r['team']==team]
        previous=None
        segments=[]
        for r in selected[::10]:
            if r['terminated'] == 'True':
                if points: segments.append(points)
                points=[]
                previous=None
                continue
            p=(float(r['x']),float(r['y']))
            if previous and math.dist(previous,p)>2:
                if points: segments.append(points)
                points=[]
            points.append(xy(*p)); previous=p
        if points:segments.append(points)
        for segment in segments:
            points_text=' '.join(f'{x:.1f},{y:.1f}' for x,y in segment)
            elements.append(f'<polyline points="{points_text}" fill="none" stroke="{color}" stroke-width="2" opacity=".75"/>')
        x,y=xy(*arena['starts'][team][:2])
        elements.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>')
    for c in arena['cubes']:
        x,y=xy(c['x'],c['y'])
        elements.append(f'<rect x="{x-4}" y="{y-4}" width="8" height="8" fill="#e4ac00" stroke="#5c4800"/><text x="{x+7}" y="{y-5}" font-size="12" font-family="sans-serif">{html.escape(c["id"])}:{c["value"]}</text>')
    meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    legend='Blue / Red: independent Gemini, same strategy.' if meta.get('dual_llm') else 'Blue: selected strategy. Red: nearest.'
    elements.append(f'<text x="50" y="690" font-family="sans-serif" font-size="13">{legend} Raised targets excluded.</text>')
    elements.append('<text x="50" y="713" font-family="sans-serif" font-size="13">Dimensions, collection, recovery and car physics are unofficial assumptions.</text></svg>')
    (folder/'map_trajectories.svg').write_text('\n'.join(elements),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('folder',type=Path)
    parser.add_argument('--skip-video',action='store_true')
    parser.add_argument('--expected-checkpoint-sha')
    args=parser.parse_args()
    result=verify(args.folder,not args.skip_video,args.expected_checkpoint_sha)
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(bool(result['errors']))
