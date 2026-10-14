"""Isolated H1/Go2 physical practice; no training or official-source modification.

Selectors can be deterministic, single Gemini, or independent Gemini for both teams.
All arena dimensions, collection/fall/respawn/car thresholds are assumptions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
import os
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
os.environ.setdefault('OMNI_KIT_ACCEPT_EULA', 'YES')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--map-seed', type=int, default=42)
    parser.add_argument('--duration', type=float, default=180)
    parser.add_argument('--strategy', choices=['nearest', 'flat_safe', 'score_rate'], default='score_rate')
    parser.add_argument('--speed', type=float, default=0.6)
    parser.add_argument('--record', action='store_true')
    parser.add_argument('--llm', action='store_true', help='Use real lecture Gemini; failures remain explicit, no surrogate fallback')
    parser.add_argument('--dual-llm', action='store_true', help='Same prompt, independent Gemini and public tactical observations for both teams')
    parser.add_argument('--prompt-file', type=Path)
    parser.add_argument('--h1-root', default='C:/workspace/training/humanoid')
    parser.add_argument('--robot', choices=['h1','go2'], default='h1')
    parser.add_argument('--robot-root', type=Path)
    parser.add_argument('--policy-path', type=Path)
    parser.add_argument('--checkpoint-path', type=Path)
    parser.add_argument('--expected-checkpoint-sha')
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.dual_llm:
        args.llm = True
    if not 0 < args.duration <= 180 or not 0 < args.speed <= 1:
        parser.error('duration must be (0,180], speed (0,1]')
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    if args.record:
        args.enable_cameras = True
    launcher = AppLauncher(args)
    app = launcher.app
    try:
        run(args, out, app)
    except BaseException:
        import traceback
        error = traceback.format_exc()
        (out / 'ERROR.txt').write_text(error, encoding='utf-8')
        print(error, flush=True)
        raise
    finally:
        app.close()


def run(args, out, app):
    import torch
    import numpy as np
    import trimesh
    from pxr import Usd, UsdGeom, UsdPhysics, Gf
    import isaaclab.sim as sim_utils
    from isaaclab.assets import AssetBaseCfg
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.terrains import TerrainImporterCfg
    from finals_practice_core import generate_map, choose_target, ScoreTracker
    sys.path.insert(0, str(args.robot_root or args.h1_root))
    if args.robot == 'h1':
        from h1_task.env_cfg import HumanoidRoughEnvCfg as RobotEnvCfg
    else:
        from go2_task.env_cfg import QuadrupedRoughEnvCfg as RobotEnvCfg

    arena = generate_map(args.map_seed)
    (out / 'map.json').write_text(json.dumps(arena, ensure_ascii=False, indent=2), encoding='utf-8')
    # One combined mesh makes collision geometry and the policy's ray scans agree.
    parts = [trimesh.creation.box(extents=[30, 26, .2], transform=trimesh.transformations.translation_matrix([0, 0, -.1]))]
    for b in arena['obstacles']:
        if b['kind'] == 'car_track':
            continue
        if b['kind'] == 'ramp':
            x0,x1 = b['cx']-b['sx']/2,b['cx']+b['sx']/2
            y0,y1 = b['cy']-b['sy']/2,b['cy']+b['sy']/2
            h = b['sz']
            vertices = [[x0,y0,0],[x1,y0,0],[x0,y1,0],[x1,y1,0],[x0,y1,h],[x1,y1,h]]
            faces = [[0,2,3],[0,3,1],[0,1,5],[0,5,4],[2,4,5],[2,5,3],[0,4,2],[1,3,5]]
            parts.append(trimesh.Trimesh(vertices=vertices, faces=faces))
            continue
        mesh = trimesh.creation.box(extents=[b['sx'], b['sy'], b['sz']])
        mesh.apply_translation([b['cx'], b['cy'], b['cz']])
        parts.append(mesh)
    terrain = trimesh.util.concatenate(parts)
    usd = Usd.Stage.CreateNew(str(out / 'arena.usda'))
    UsdGeom.SetStageUpAxis(usd, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(usd, 1)
    prim = UsdGeom.Xform.Define(usd, '/Arena')
    usd.SetDefaultPrim(prim.GetPrim())
    mesh = UsdGeom.Mesh.Define(usd, '/Arena/Mesh')
    mesh.CreatePointsAttr(terrain.vertices.tolist())
    mesh.CreateFaceVertexCountsAttr([3] * len(terrain.faces))
    mesh.CreateFaceVertexIndicesAttr(terrain.faces.flatten().tolist())
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateDisplayColorAttr([(0.48, 0.52, 0.55)])
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    usd.GetRootLayer().Save()

    cfg = RobotEnvCfg()
    cfg.seed = args.map_seed
    cfg.scene.num_envs = 2
    cfg.scene.env_spacing = 0
    cfg.scene.filter_collisions = False
    cfg.scene.terrain = TerrainImporterCfg(prim_path='/World/ground', terrain_type='usd', usd_path=str(out / 'arena.usda'), env_spacing=0, collision_group=-1)
    cfg.scene.sky_light = AssetBaseCfg(prim_path='/World/Light', spawn=sim_utils.DomeLightCfg(intensity=1800))
    # Preserve the exact training asset URI; the lecture Isaac/Robots asset differs.
    asset = cfg.scene.robot.spawn.usd_path
    asset_stage = Usd.Stage.Open(str(asset))
    root_prim = asset_stage.GetDefaultPrim()
    variants = {}
    for name in root_prim.GetVariantSets().GetNames():
        variant = root_prim.GetVariantSet(name)
        print('H1_ASSET_VARIANT',name,variant.GetVariantNames(),variant.GetVariantSelection(),flush=True)
        variants[name] = variant.GetVariantSelection()
    cfg.scene.robot.spawn.variants = variants
    cfg.scene.height_scanner.mesh_prim_paths = ['/World/ground']
    cfg.scene.height_scanner.debug_vis = False
    cfg.observations.policy.enable_corruption = False
    cfg.curriculum.terrain_levels = None
    cfg.events.push_robot = None
    cfg.events.reset_base.params['pose_range'] = {}
    cfg.events.reset_base.params['velocity_range'] = {}
    cfg.commands.base_velocity.debug_vis = False
    cfg.commands.base_velocity.heading_command = False
    cfg.commands.base_velocity.rel_standing_envs = 0
    cfg.commands.base_velocity.resampling_time_range = (10000, 10000)
    cfg.episode_length_s = 181
    cfg.sim.device = args.device
    cfg.sim.render_interval = cfg.decimation
    cfg.viewer.eye = (18, -24, 24)
    cfg.viewer.lookat = (0, 0, 0)
    cfg.viewer.origin_type = 'world'
    cfg.viewer.resolution = (960, 720)
    env = ManagerBasedRLEnv(cfg=cfg, render_mode='rgb_array' if args.record else None)
    # Match the initial reset performed by the standard RSL-RL wrapper.
    env.reset()
    robot = env.scene['robot']
    starts = arena['starts']
    teams = ['blue', 'red']
    spawn = robot.data.default_root_state.clone()
    for i, team in enumerate(teams):
        spawn[i, :2] = torch.tensor(starts[team][:2], device=env.device)
        yaw = 0 if i == 0 else math.pi
        spawn[i, 3:7] = torch.tensor([math.cos(yaw/2), 0, 0, math.sin(yaw/2)], device=env.device)
    robot.write_root_state_to_sim(spawn)
    env.scene.update(cfg.sim.dt)
    (out/'robot_identity.json').write_text(json.dumps({'joint_names':robot.joint_names,'body_names':robot.body_names,
        'default_joint_pos':robot.data.default_joint_pos[0].tolist(),'default_root_state':spawn.tolist(),
        'dt':cfg.sim.dt,'decimation':cfg.decimation,'asset_variants':variants},indent=2),encoding='utf-8')
    policy_path = args.policy_path or ROOT / 'workspace/submission_candidates/h1_run06_model9900/policy.pt'
    checkpoint = args.checkpoint_path or ROOT / 'workspace/submission_candidates/h1_run06_model9900/model_best_iter9900.pt'
    checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    if args.expected_checkpoint_sha and checkpoint_sha != args.expected_checkpoint_sha:
        raise ValueError('checkpoint identity mismatch')
    policy = torch.jit.load(str(policy_path), map_location=env.device).eval()
    actor_state = torch.load(checkpoint,map_location='cpu',weights_only=False)['actor_state_dict']
    exported_state = policy.state_dict()
    if not exported_state or any(k not in actor_state or not torch.equal(v.cpu(),actor_state[k]) for k,v in exported_state.items()):
        raise ValueError('exported policy does not match checkpoint actor tensors')
    print('POLICY_TENSOR_MATCH',len(exported_state),flush=True)
    meta = {'official_result': False, 'llm_execution': 'DETERMINISTIC_SURROGATE_NOT_GEMINI', 'strategy': args.strategy,
            'duration_requested': args.duration, 'map_seed': args.map_seed, 'speed': args.speed,
            'policy_sha256': hashlib.sha256(policy_path.read_bytes()).hexdigest(),
            'checkpoint_sha256': checkpoint_sha,
            'robot_type':args.robot,'policy_path':str(policy_path),'checkpoint_path':str(checkpoint),
            'actor_tensor_match_count':len(exported_state),
            'h1_asset_uri': str(asset),
            'assumptions_extra': ['collection radius .6m with vertical surface tolerance .35m', 'fall uses original body-contact termination, not posture-confirmed fall',
                                  'fall resets to team start; 3s stationary recovery', 'car event uses footprint overlap; knockback velocity 1.5m/s',
                                  'red is same robot policy with nearest selector; blue uses chosen selector', 'both robots share one physical map',
                                  'raised cubes excluded: climbing capability not verified',
                                  'termination rows are post-auto-reset positions, not impact positions'],
            'source': 'https://robotics.connect.or.kr/rules/finals_regulations.html'}
    meta['source_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (Path(__file__), ROOT/'tools/finals_practice_core.py', ROOT/'tools/finals_practice_gemini.py')}
    if args.robot_root:
        meta['robot_source_sha256'] = {str(p.relative_to(args.robot_root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in args.robot_root.rglob('*.py')}
    training_env = checkpoint.parent/'env.yaml'
    if training_env.exists():
        meta['training_env_sha256'] = hashlib.sha256(training_env.read_bytes()).hexdigest()
    (out / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    tracker = ScoreTracker(arena)
    llm = None
    selectors = [None, None]
    llm_records = []
    if args.llm:
        from finals_practice_gemini import GeminiSelector
        if args.prompt_file is None:
            raise ValueError('--llm requires --prompt-file')
        prompt = args.prompt_file.read_text(encoding='utf-8').strip()
        llm = GeminiSelector(prompt)
        selectors[0] = llm
        if args.dual_llm:
            selectors[1] = GeminiSelector(prompt)
        meta['llm_execution'] = 'REAL_GEMINI_LECTURE_API_NOT_OFFICIAL_MATCH_RUNTIME'
        meta['strategy_text'] = prompt
        meta['strategy_length'] = len(prompt)
        llm.robot_description = '4족보행 Go2' if args.robot == 'go2' else '2족보행 H1'
        if selectors[1]:
            selectors[1].robot_description = llm.robot_description
        meta['llm_latency_model'] = 'fixed 2.5 simulated seconds before each selection; network wait pauses physics'
        meta['dual_llm'] = args.dual_llm
        meta['team_strategies'] = {team: prompt if selectors[i] else 'nearest' for i,team in enumerate(teams)}
        if args.dual_llm:
            meta['llm_latency_model'] = 'initial/consumed-target delay 2.5 simulated seconds; tactical refresh every 10 simulated seconds; network pauses physics for both teams'
            meta['assumptions_extra'][4] = 'both teams use independent Gemini selectors with identical strategy and observation rules'
            meta['tactical_observations'] = 'full-map public positions sampled every .5s, latest 3s; no opponent private target; A* constant-speed ETA excludes turns; refresh every 10s'
        (out/'strategy.txt').write_text(prompt,encoding='utf-8')
        (out / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2),encoding='utf-8')
    targets = [None, None]
    paths = [[], []]
    wait_until = [0., 0.]
    next_plan = [2.5, 2.5]
    last_car = [False, False]
    histories = [deque(maxlen=7), deque(maxlen=7)]
    call_counts = [0, 0]
    cubes = {c['id']: c for c in arena['cubes']}
    # Cubes are visible non-colliding markers; collection is scored from measured position.
    stage = env.sim.stage
    team_markers = []
    if args.dual_llm:
        for team,color in zip(teams,[(.05,.2,1.),(.9,.1,.1)]):
            marker_cfg = sim_utils.CuboidCfg(size=(.2,.2,.2),visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color))
            marker_path = '/World/TeamMarker_'+team
            marker_cfg.func(marker_path,marker_cfg,translation=(0,0,2))
            team_markers.append(UsdGeom.Xformable(stage.GetPrimAtPath(marker_path)).GetOrderedXformOps()[0])
    cube_prims = {}
    for c in arena['cubes']:
        p = '/World/Cubes/' + str(c['id']).replace('-', '_')
        sim_utils.CuboidCfg(size=(.25,.25,.25), visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1,.7,.1))).func(p, sim_utils.CuboidCfg(size=(.25,.25,.25), visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1,.7,.1))), translation=tuple([c['x'],c['y'],c['z']]))
        cube_prims[c['id']] = UsdGeom.Imageable(stage.GetPrimAtPath(p))
    car_cfg = sim_utils.CuboidCfg(size=(1.4,.8,.6), visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.8,.1,.1)))
    car_cfg.func('/World/Car', car_cfg, translation=(0,0,.3))
    car_xform = UsdGeom.Xformable(stage.GetPrimAtPath('/World/Car'))
    car_op = car_xform.GetOrderedXformOps()[0]
    video = None
    if args.record:
        import imageio.v2 as imageio
        video = imageio.get_writer(str(out / 'practice.mp4'), fps=10)
    start_wall = time.time()
    steps = math.floor(args.duration / env.step_dt + 1e-8)
    csv_file = (out / 'steps.csv').open('w', newline='', encoding='utf-8')
    writer = csv.writer(csv_file)
    writer.writerow(['step','time_s','team','x','y','z','vx','wz','target','terminated','score'])
    command = env.command_manager.get_term('base_velocity').vel_command_b
    route = arena['car']['route']
    route = route if route[0] == route[-1] else route + [route[0]]
    lengths = [math.dist(a[:2], b[:2]) for a,b in zip(route,route[1:])]
    completed = False
    try:
        with torch.inference_mode():
            for step in range(steps):
                if not app.is_running():
                    break
                t = step * env.step_dt
                pos = robot.data.root_pos_w.detach().cpu().tolist()
                yaw = robot.data.heading_w.detach().cpu().tolist()
                if step % 25 == 0:
                    for i in range(2):
                        histories[i].append({'time_s':t,'x':pos[i][0],'y':pos[i][1]})
                command.zero_()
                for i, team in enumerate(teams):
                    if t < wait_until[i]:
                        continue
                    claimed = set(tracker.cube_owner)
                    if targets[i] in claimed:
                        targets[i] = None
                        paths[i] = []
                        next_plan[i] = t + 2.5
                    choice = None
                    if (targets[i] is None or args.dual_llm) and t >= next_plan[i] and selectors[i] is not None:
                        if choose_target(arena,pos[i][:2],claimed) is None:
                            llm_records.append({'time_s':t,'team':team,'no_reachable_targets':True})
                            targets[i], paths[i] = None, []
                            next_plan[i] = t + 10000
                            continue
                        if call_counts[i] >= 40:
                            raise RuntimeError('explicit per-team Gemini budget exhausted')
                        if call_counts[i] < 40:
                            try:
                                kwargs = {}
                                if args.dual_llm:
                                    from finals_practice_gemini import build_tactical_context
                                    kwargs['tactical_context'] = build_tactical_context(arena,pos[i][:2],list(histories[1-i]),claimed,speed=args.speed,current_target=targets[i])
                                call_counts[i] += 1
                                choice = selectors[i].select(arena,pos[i][:2],claimed,elapsed_s=t,**kwargs)
                                llm_records.append({'time_s':t,'team':team,'choice':choice})
                                print('LLM_SELECTION',t,team,choice['target']['id'] if choice else None,flush=True)
                                (out/'llm_decisions.json').write_text(json.dumps(llm_records,ensure_ascii=False,indent=2),encoding='utf-8')
                                if choice and choice['target']['id'] in tracker.cube_owner:
                                    choice = None
                            except Exception as error:
                                llm_records.append({'time_s':t,'team':team,'error':str(error)})
                                print('LLM_SELECTION_FAILED',str(error),flush=True)
                                if args.dual_llm:
                                    raise
                            next_plan[i] = t + (10 if args.dual_llm else 2.5)
                    elif targets[i] is None and t >= next_plan[i]:
                        choice = choose_target(arena, pos[i][:2], claimed, strategy=args.strategy if i == 0 else 'nearest')
                        next_plan[i] = t + 2.5
                    if choice:
                        target, path = choice['target'], choice['path']
                        if target['id'] != targets[i] or not paths[i]:
                            paths[i] = path
                        targets[i] = target['id']
                    if paths[i]:
                        while len(paths[i]) > 1 and math.dist(pos[i][:2], paths[i][0][:2]) < .25:
                            paths[i].pop(0)
                        goal = paths[i][0]
                        dx, dy = goal[0]-pos[i][0], goal[1]-pos[i][1]
                        error = (math.atan2(dy,dx)-yaw[i]+math.pi)%(2*math.pi)-math.pi
                        command[i,0] = min(args.speed,max(.08,math.hypot(dx,dy))) if abs(error)<.45 else 0
                        command[i,2] = max(-.6, min(.6, 1.2*error))
                # Recompute observations after writing the velocity command.
                obs = env.observation_manager.compute()['policy']
                if step == 0:
                    meta['observed_policy_input_shape'] = list(obs.shape)
                    meta['observed_policy_output_shape'] = list(policy(obs).shape)
                    (out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
                if step in (0,50,100):
                    print('OBS_DIAGNOSTIC',step,obs[0,:69].tolist(),'HEIGHT_RANGE',obs[0,69:].min().item(),obs[0,69:].max().item(),flush=True)
                result = env.step(policy(obs))
                new_pos = robot.data.root_pos_w.detach().cpu().tolist()
                for i,marker in enumerate(team_markers):
                    marker.Set(Gf.Vec3d(new_pos[i][0],new_pos[i][1],new_pos[i][2]+(.9 if args.robot=='h1' else .35)))
                terminated = result[2].detach().cpu().tolist()
                distance = (t * arena['car']['assumed_speed_mps']) % sum(lengths)
                car_xy = route[0][:2]
                for a,b,length in zip(route,route[1:],lengths):
                    if distance <= length:
                        car_xy = [a[j]+(b[j]-a[j])*distance/length for j in range(2)]
                        break
                    distance -= length
                car_op.Set(Gf.Vec3d(car_xy[0], car_xy[1], .3))
                for i,team in enumerate(teams):
                    event_t = (step+1)*env.step_dt
                    if terminated[i]:
                        histories[i].clear()
                        tracker.fall(team, event_t)
                        ids = torch.tensor([i], device=env.device)
                        robot.write_root_state_to_sim(spawn[i:i+1], env_ids=ids)
                        wait_until[i] = event_t + 3
                        targets[i], paths[i] = None, []
                    overlap = abs(new_pos[i][0]-car_xy[0]) < 1.0 and abs(new_pos[i][1]-car_xy[1]) < .7
                    if overlap and not last_car[i]:
                        tracker.collision(team, event_t)
                        vel = robot.data.root_vel_w[i:i+1].clone()
                        angle = math.atan2(new_pos[i][1]-car_xy[1],new_pos[i][0]-car_xy[0])
                        vel[0,0],vel[0,1] = 1.5*math.cos(angle),1.5*math.sin(angle)
                        robot.write_root_velocity_to_sim(vel, env_ids=torch.tensor([i],device=env.device))
                    last_car[i] = overlap
                    writer.writerow([step+1,event_t,team,*new_pos[i],command[i,0].item(),command[i,2].item(),targets[i],terminated[i],tracker.record(team)['score']])
                # Same-tick ownership goes to nearest eligible robot; exact ties alternate by map seed.
                for cid,c in cubes.items():
                    eligible = []
                    for i,team in enumerate(teams):
                        d = math.dist(new_pos[i][:2],[c['x'],c['y']])
                        if not terminated[i] and event_t >= wait_until[i] and d < .6 and abs(new_pos[i][2]-spawn[i,2].item()-(c['z']-.15)) < .35:
                            eligible.append((d,(i+args.map_seed)%2,team))
                    if cid not in tracker.cube_owner and eligible:
                        tracker.collect(min(eligible)[2],cid,event_t)
                        cube_prims[cid].MakeInvisible()
                if video and step % 5 == 0:
                    video.append_data(env.render())
                if step % 500 == 0:
                    csv_file.flush()
                    print('PRACTICE_PROGRESS', step, t, tracker.result(), flush=True)
            else:
                completed = True
    finally:
        csv_file.close()
        (out / 'llm_decisions.json').write_text(json.dumps(llm_records,ensure_ascii=False,indent=2),encoding='utf-8')
        if video:
            video.close()
        summary = {'completed': completed, 'simulated_seconds': (step+1)*env.step_dt, 'wall_seconds': time.time()-start_wall,
                   'teams': tracker.result(), 'events': tracker.events, 'official_result': False,
                   'llm_tested': any('choice' in entry and entry['choice'] for entry in llm_records),
                   'llm_errors': sum('error' in entry for entry in llm_records)}
        summary['llm_calls_by_team'] = dict(zip(teams, call_counts))
        (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        env.close()
    if not completed:
        raise RuntimeError('practice interrupted; score is partial')
    print('PRACTICE_COMPLETE', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
