#!/usr/bin/env python3
"""Generate README SVG charts directly from offline JSON outputs.

No learned/empirical ecology results are implied: bundled inputs are synthetic.
This is dependency-free so figures can be regenerated after every CI run.
"""
from __future__ import annotations
import argparse
import json
from html import escape
from pathlib import Path

BG = '#0e1930'
PANEL = '#1a2a46'
EDGE = '#38506f'
TEXT = '#f2f7ff'
MUTED = '#b6c5db'
CYAN = '#69c5ef'
GREEN = '#70dfb7'
GOLD = '#ffce7a'


def el(name, **attrs):
    return '<' + name + ''.join(' ' + k.replace('_', '-') + '="' + escape(str(v), quote=True) + '"' for k, v in attrs.items()) + '/>'


def txt(x, y, value, size=17, color=TEXT, **attrs):
    return '<text x="%s" y="%s" font-size="%s" fill="%s" %s>%s</text>' % (
        x, y, size, color, ' '.join(k.replace('_', '-') + '="' + escape(str(v), quote=True) + '"' for k,v in attrs.items()), escape(str(value)))


def panel(w, h, title, subtitle):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">',
            el('rect', x=0, y=0, width=w, height=h, rx=18, fill=BG),
            txt(35, 53, title, 27, TEXT, font_weight='bold'), txt(35, 82, subtitle, 15, MUTED)]


def save(parts, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text('\n'.join(parts + ['</svg>']) + '\n', encoding='utf-8')


def retrieval_chart(data, out):
    rows = data['questions']
    negatives = data['hard_negative_queries']
    h = max(440, 155 + 75 * len(rows))
    s = panel(1100, h, 'Retrieval on synthetic fixtures',
              'Calculated from results/retrieval.json  |  not evaluated on real scientific papers')
    s.append(txt(35, 126, 'Authored query', 16, MUTED))
    s.append(txt(570, 126, 'Recall@5', 16, MUTED))
    s.append(txt(805, 126, 'nDCG@5', 16, MUTED))
    for i, r in enumerate(rows):
        y = 170 + i * 75
        s.append(txt(35, y, r['question'][:49], 17))
        for x, key, color in ((575, 'recall@5', GREEN), (810, 'ndcg@5', CYAN)):
            value = max(0., min(1., float(r[key])))
            s.append(el('rect', x=x, y=y-19, width=146, height=20, rx=5, fill=PANEL))
            s.append(el('rect', x=x, y=y-19, width=round(146*value,2), height=20, rx=5, fill=color))
            s.append(txt(x+155, y-2, f'{value:.2f}', 15, TEXT))
    py = 196 + len(rows)*75
    rejected = sum(not r['returned_ids'] for r in negatives)
    s.extend([el('rect', x=35, y=py-31, width=1030, height=66, rx=11, fill=PANEL),
              txt(58, py+1, f'Hard-negative abstentions: {rejected} / {len(negatives)}', 19, GOLD, font_weight='bold'),
              txt(670, py+1, f'False positive rate: {data["hard_negative_false_positive_rate"]:.2f}', 16)])
    s.append(txt(35, h-22, 'Synthetic labels written by project authors; high scores are not independent scientific validation.', 14, MUTED))
    save(s, out)


def causal_chart(data, out):
    d = data['synthetic_scm']
    est, truth = float(d['estimated_ate']), float(d['scm_true_ate'])
    low, high = map(float, d['bootstrap_95_interval'])
    margin = max((high-low)*0.35, abs(est-truth)*2, 0.05)
    xmin, xmax = min(truth, low, est)-margin, max(truth, high, est)+margin
    pos = lambda v: 100 + (v-xmin)/(xmax-xmin)*880
    s = panel(1100, 390, 'Estimated vs known synthetic intervention effect',
              'Synthetic SCM / adjusted estimate and bootstrap interval (not lake field evidence)')
    s.append(txt(40, 139, f'Intervention P: {d["p0"]:.2f} to {d["p1"]:.2f}', 17, MUTED))
    s.append(el('line', x1=100, y1=240, x2=980, y2=240, stroke=EDGE, stroke_width=3))
    for i in range(5):
        value=xmin+(xmax-xmin)*i/4
        xx=round(pos(value),2)
        s.append(el('line',x1=xx,y1=234,x2=xx,y2=246,stroke=MUTED,stroke_width=1))
        s.append(txt(xx,272,f'{value:.2f}',14,MUTED,text_anchor='middle'))
    s.append(el('line', x1=round(pos(truth),2), y1=169, x2=round(pos(truth),2), y2=231,
                stroke=GOLD, stroke_width=3, stroke_dasharray='7 5'))
    s.append(el('line', x1=round(pos(low),2), y1=205, x2=round(pos(high),2), y2=205,
                stroke=GREEN, stroke_width=8, stroke_linecap='round'))
    for v in (low,high):
        s.append(el('line',x1=round(pos(v),2),y1=193,x2=round(pos(v),2),y2=217,stroke=GREEN,stroke_width=3))
    s.append(el('circle',cx=round(pos(est),2),cy=205,r=10,fill=TEXT,stroke=GREEN,stroke_width=4))
    s.append(txt(50,321,f'True ATE (SCM): {truth:.3f}',18,GOLD))
    s.append(txt(360,321,f'Estimated ATE: {est:.3f}',18,GREEN))
    s.append(txt(700,321,f'95% CI: [{low:.3f}, {high:.3f}]',17,TEXT))
    s.append(txt(50,363,f'Absolute error: {abs(est-truth):.3f}  |  Assumed adjustment: {", ".join(d["adjustment_set"])}',14,MUTED))
    save(s,out)


def world_chart(data, out):
    d = data['synthetic_world_model']
    vals=[('Learned one-step',float(d['one_step_rmse']),GREEN),
          ('Persistence one-step',float(d['persistence_rmse']),GOLD)]
    maximum=max(x[1] for x in vals)*1.22
    s=panel(1100,370,'World-model error on synthetic trajectories',
            'One-step RMSE versus persistence baseline; identical synthetic evaluation horizon')
    for i,(name,val,color) in enumerate(vals):
        y=163+i*84
        s.append(txt(40,y,name,20))
        s.append(el('rect',x=310,y=y-23,width=660,height=29,rx=7,fill=PANEL))
        s.append(el('rect',x=310,y=y-23,width=round(660*val/maximum,2),height=29,rx=7,fill=color))
        s.append(txt(987,y,f'{val:.3f}',18,TEXT))
    s.append(txt(40,321,f'Mean open-loop rollout RMSE (separate multi-step task): {d["mean_open_loop_rollout_rmse"]:.3f}',16,MUTED))
    s.append(txt(40,348,'Source: results/simulation.json  |  No empirical forecasting claim',14,MUTED))
    save(s,out)


def provenance_chart(data, out):
    report=data['report']
    claims=report.get('candidate_claims',[])
    ids=[c['evidence']['source_id'] for c in claims]
    sources=list(dict.fromkeys(ids))
    height=max(380,170+max(len(sources),len(claims))*57)
    s=panel(1100,height,'Claim-to-source provenance (offline demo)',
            'Actual candidate_claims from results/demo/report.json  |  Co-mentions are NOT causal evidence')
    s.append(txt(70,128,'Evidence source IDs',16,CYAN))
    s.append(txt(715,128,'Extracted candidate claims',16,GREEN))
    source_y={name:166+58*i for i,name in enumerate(sources)}
    for i,source in enumerate(sources):
        yy=source_y[source]
        s.append(el('rect',x=45,y=yy-24,width=380,height=41,rx=8,fill=PANEL,stroke=EDGE))
        s.append(txt(61,yy+2,source,16))
    for i,c in enumerate(claims):
        yy=166+58*i
        y0=source_y[c['evidence']['source_id']]
        s.append(el('line',x1=425,y1=y0-4,x2=688,y2=yy-4,stroke=GOLD,stroke_width=2,stroke_opacity='.85'))
        s.append(el('rect',x=690,y=yy-24,width=367,height=41,rx=8,fill=PANEL,stroke=EDGE))
        label=f'{c["claim_id"]}: {c["subject"]} / {c["object"]}'
        s.append(txt(706,yy+2,label[:41],15))
    s.append(txt(46,height-25,f'{len(claims)} candidate claims linked to {len(sources)} sources; source pointers do not prove entailment.',14,MUTED))
    save(s,out)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir',type=Path,default=Path('results'))
    parser.add_argument('--out-dir',type=Path,default=Path('docs/figures'))
    args=parser.parse_args(argv)
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    retrieval=load(args.results_dir/'retrieval.json')
    simulation=load(args.results_dir/'simulation.json')
    report=load(args.results_dir/'demo'/'report.json')
    paths={
       'retrieval_benchmark.svg':lambda p:retrieval_chart(retrieval,p),
       'synthetic_causal_effect.svg':lambda p:causal_chart(simulation,p),
       'synthetic_world_model_rmse.svg':lambda p:world_chart(simulation,p),
       'evidence_provenance.svg':lambda p:provenance_chart(report,p),
    }
    for name, render in paths.items():
        output=args.out_dir/name
        render(output)
        print(f'Generated {output}')


if __name__=='__main__':
    main()
