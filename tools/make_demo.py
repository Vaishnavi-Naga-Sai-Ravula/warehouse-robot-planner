"""Build an offline teaching animation. This utility is not the submitted adapter."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'bench-warehouse'))
import _paths  # noqa: F401
import data
import validator
from adapters.myteam import Planner


def public_example():
    item = data.public_instances(['w01-aisles-small'])[0]
    report_path = ROOT / 'benchmarks' / 'public_report.json'
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding='utf-8'))
        plan = report.get('plans', {}).get(item.name)
        if plan is not None:
            cost, reason = validator.evaluate(item, plan)
            if reason is not None:
                raise RuntimeError(f'Saved public plan is invalid: {reason}')
            measured = validator.describe(item, plan)
            (ROOT / 'benchmarks' / 'demo_plan.json').write_text(json.dumps({
                'instance': item.name, 'plan': plan, 'measured': measured,
                'source': 'public_report.json', 'cost_units': cost,
                'note': 'Saved plan from the included unmodified public harness run.'},
                indent=2), encoding='utf-8')
            return {'title': 'Actual public case: 50 robots', 'width': item.width,
                    'height': item.height, 'blocked': list(item.blocked),
                    'starts': list(item.starts), 'goals': list(item.goals),
                    'paths': plan, 'corridors': list(item.corridor_cells),
                    'description': 'This validated plan is saved in public_report.json. '
                                   'Read BENCHMARKS.md for measured costs and limitations.',
                    'expected_valid': True, 'measured': measured}
    started = time.perf_counter()
    best, best_cost, history = None, None, []
    budget = data.budget_for(item)

    def submit(plan):
        nonlocal best, best_cost
        cost, reason = validator.evaluate(item, plan)
        elapsed = time.perf_counter() - started
        accepted = cost is not None and elapsed <= budget
        if accepted and (best_cost is None or cost < best_cost):
            best, best_cost = [list(path) for path in plan], cost
            history.append([round(elapsed, 6), cost])
        return {'accepted': accepted, 'reason': reason, 'cost': cost, 'best': best_cost,
                'elapsed_s': elapsed, 'remaining_s': budget - elapsed}

    submit(Planner().solve(item, submit))
    if best is None:
        raise RuntimeError('No valid plan found for the visual demonstration.')
    measured = validator.describe(item, best)
    result = {'title': 'Actual public case: 50 robots', 'width': item.width,
              'height': item.height, 'blocked': list(item.blocked),
              'starts': list(item.starts), 'goals': list(item.goals),
              'paths': best, 'corridors': list(item.corridor_cells),
              'description': 'A direct visual-demo run of the submitted planner. '
                             'Use the included full public report for benchmark claims.',
              'expected_valid': True, 'measured': measured}
    (ROOT / 'benchmarks' / 'demo_plan.json').write_text(json.dumps({
        'instance': item.name, 'plan': best, 'measured': measured, 'history': history,
        'note': 'Direct demonstration run; not an official private result.'}, indent=2), encoding='utf-8')
    return result


def main():
    examples = [
        {'title': 'Learn: why a direct swap is invalid', 'width': 3, 'height': 2,
         'blocked': [], 'starts': [0, 1], 'goals': [1, 0],
         'paths': [[0, 1], [1, 0]], 'corridors': [], 'expected_valid': False,
         'description': 'At t=1 the robots exchange cells across the same edge. '
                        'They do not share an endpoint, but the edge-swap rule rejects this plan.'},
        {'title': 'Learn: a valid detour', 'width': 3, 'height': 2,
         'blocked': [], 'starts': [0, 1], 'goals': [1, 0],
         'paths': [[0, 1], [1, 4, 3, 0]], 'corridors': [], 'expected_valid': True,
         'description': 'Robot 0 reaches cell 1 at t=1 and stays there. Robot 1 detours '
                        'through cells 4 and 3, reaching cell 0 at t=3. Makespan=3; sum of costs=4.'},
        public_example(),
    ]
    payload = json.dumps(examples).replace('</', '<\\/')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Warehouse Robot Planner — Teaching Demo</title>
<style>body{font-family:system-ui,sans-serif;margin:30px auto;padding:0 20px;max-width:1080px;color:#172554;background:#f8fafc}h1{margin-bottom:8px;font-size:30px}p{line-height:1.6}.panel{background:white;border:1px solid #dbeafe;border-radius:14px;padding:18px;margin:18px 0}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px}button,select{padding:9px 12px;border:1px solid #94a3b8;border-radius:7px;background:white;color:#172554}button{cursor:pointer}button.primary{background:#1d4ed8;color:white;border-color:#1d4ed8}canvas{display:block;margin:16px auto;max-width:100%;height:auto;background:white;border:1px solid #cbd5e1}.badge{padding:6px 10px;border-radius:6px;background:#dcfce7;color:#166534}.bad{background:#fee2e2;color:#991b1b}code{background:#e2e8f0;padding:2px 5px;border-radius:4px}input[type=range]{min-width:220px;flex:1}.legend{font-size:14px;color:#475569}</style>
</head><body>
<h1>Warehouse Robot Planner</h1><p>See why robots need to plan in both <strong>space and time</strong>. Start with the two-robot example, then view the actual 50-robot public instance.</p>
<div class="panel"><div class="controls"><label for="example">Example</label><select id="example"></select><span id="validity" class="badge"></span></div><p id="description"></p></div>
<div class="panel"><div class="controls"><button id="play" class="primary">Play</button><button id="step">Step +1</button><button id="reset">Reset</button><label for="speed">Speed</label><select id="speed"><option value="650">Slow</option><option value="250" selected>Normal</option><option value="70">Fast</option></select><label><input type="checkbox" id="showPaths">Show paths</label></div>
<div class="controls" style="margin-top:16px"><label for="time">Time</label><input id="time" type="range" min="0" value="0"><strong id="timeText"></strong></div>
<canvas id="grid" aria-label="Warehouse grid with robot positions"></canvas><p id="collision"></p><p class="legend">Filled circles: robots; dashed circles: assigned goals; dark squares: walls; pale blue squares: corridor cells. Robots remain on their goals after finishing. Numbers identify robots.</p></div>
<div class="panel"><strong>What the planner does</strong><ol><li>Measure wall-aware shortest distances with BFS.</li><li>Construct paths one robot at a time using safe intervals and A*.</li><li>Reserve occupied cells, edges and permanently parked goals.</li><li>Repair groups using full cell-and-time search, keeping only complete plans with lower exact cost.</li></ol><p>The supplied benchmark validates the plans independently. Our method is a heuristic: it does not prove the globally optimal plan and does not guarantee every unseen instance.</p></div>
<script id="data" type="application/json">PAYLOAD</script>
<script>
const examples=JSON.parse(document.getElementById('data').textContent);
const selector=document.getElementById('example'),canvas=document.getElementById('grid'),ctx=canvas.getContext('2d');
const slider=document.getElementById('time'),play=document.getElementById('play');
let ex,t=0,maxT=0,unit=32,timer=null;
examples.forEach((item,i)=>{const opt=document.createElement('option');opt.value=i;opt.textContent=item.title;selector.appendChild(opt)});
function color(r){return `hsl(${(r*137.508)%360} 70% 42%)`}
function position(path,time){return path[Math.min(time,path.length-1)]}
function center(cell){return [(cell%ex.width+.5)*unit,(Math.floor(cell/ex.width)+.5)*unit]}
function stop(){if(timer)clearInterval(timer);timer=null;play.textContent='Play'}
function choose(){stop();ex=examples[Number(selector.value)];t=0;maxT=Math.max(...ex.paths.map(p=>p.length-1));unit=Math.min(70,Math.floor(760/Math.max(ex.width,ex.height)));canvas.width=ex.width*unit;canvas.height=ex.height*unit;slider.max=maxT;document.getElementById('description').textContent=ex.description;const badge=document.getElementById('validity');badge.textContent=ex.expected_valid?'Collision-free example':'Intentionally invalid example';badge.className=ex.expected_valid?'badge':'badge bad';draw()}
function draw(){slider.value=t;document.getElementById('timeText').textContent=`${t} / ${maxT}`;ctx.clearRect(0,0,canvas.width,canvas.height);const walls=new Set(ex.blocked),corridors=new Set(ex.corridors);for(let c=0;c<ex.width*ex.height;c++){const x=c%ex.width*unit,y=Math.floor(c/ex.width)*unit;ctx.fillStyle=walls.has(c)?'#334155':corridors.has(c)?'#eff6ff':'#ffffff';ctx.fillRect(x,y,unit,unit);ctx.strokeStyle='#e2e8f0';ctx.strokeRect(x,y,unit,unit);if(ex.width<=5){ctx.fillStyle='#94a3b8';ctx.font='11px system-ui';ctx.fillText(c,x+4,y+12)}}
if(document.getElementById('showPaths').checked){ex.paths.forEach((path,r)=>{ctx.beginPath();path.forEach((cell,i)=>{const [x,y]=center(cell);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle=color(r);ctx.globalAlpha=.25;ctx.lineWidth=2;ctx.stroke();ctx.globalAlpha=1})}
ex.goals.forEach((cell,r)=>{const [x,y]=center(cell);ctx.beginPath();ctx.arc(x,y,unit*.36,0,Math.PI*2);ctx.strokeStyle=color(r);ctx.lineWidth=2;ctx.setLineDash([4,3]);ctx.stroke();ctx.setLineDash([])});
const cells=ex.paths.map(p=>position(p,t));let conflicts=[];cells.forEach((cell,r)=>{for(let q=0;q<r;q++){if(cell===cells[q])conflicts.push(`robots ${q} and ${r} share cell ${cell}`);if(t>0&&position(ex.paths[r],t-1)===cells[q]&&position(ex.paths[q],t-1)===cell&&cell!==position(ex.paths[r],t-1))conflicts.push(`robots ${q} and ${r} swap across an edge`)}});
cells.forEach((cell,r)=>{const [x,y]=center(cell);ctx.beginPath();ctx.arc(x,y,unit*.29,0,Math.PI*2);ctx.fillStyle=color(r);ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=1;ctx.stroke();ctx.fillStyle='white';ctx.font=`bold ${Math.max(9,Math.floor(unit*.28))}px system-ui`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(r,x,y)});
const message=document.getElementById('collision');message.textContent=conflicts.length?`Conflict at time ${t}: ${conflicts.join('; ')}.`:`No vertex or edge-swap conflict at time ${t}.`;message.style.color=conflicts.length?'#b91c1c':'#166534';}
function advance(){if(t>=maxT){stop();return}t++;draw()}
play.onclick=()=>{if(timer){stop();return}if(t>=maxT)t=0;draw();play.textContent='Pause';timer=setInterval(advance,Number(document.getElementById('speed').value))};document.getElementById('step').onclick=()=>{stop();advance()};document.getElementById('reset').onclick=()=>{stop();t=0;draw()};slider.oninput=()=>{stop();t=Number(slider.value);draw()};selector.onchange=choose;document.getElementById('showPaths').onchange=draw;document.getElementById('speed').onchange=()=>{if(timer){stop();play.click()}};selector.value='1';choose();
</script></body></html>'''.replace('PAYLOAD', payload)
    (ROOT / 'demo.html').write_text(page, encoding='utf-8')
    print(f'Teaching demo saved: {ROOT / "demo.html"}')


if __name__ == '__main__':
    main()
