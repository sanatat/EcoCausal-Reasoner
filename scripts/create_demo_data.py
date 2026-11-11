"""Deterministic *invented* fixture data. Never cite as scientific literature."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
records=[
('demo:phosphorus-a','A hypothetical lake management study reports phosphorus declining after a planned intervention, followed by lower chlorophyll-a under stable weather.'),
('demo:phosphorus-b','In an illustrative observational record, phosphorus and chlorophyll-a are positively associated. No causal experiment was performed.'),
('demo:phosphorus-c','A synthetic example shows phosphorus decreasing but chlorophyll-a staying high during a period of elevated temperature.'),
('demo:temperature-a','A hypothetical warm year increases algal biomass and chlorophyll-a independently of nutrient loading.'),
('demo:zebra-a','A fictional lake monitoring record describes zebra mussel filtration associated with increased water clarity.'),
('demo:zebra-b','Synthetic illustration: zebra mussel abundance and chlorophyll-a may change in opposite directions, but measurement bias is possible.'),
('demo:clarity-a','In an invented ecology lesson, water clarity increases when suspended sediment decreases.'),
('demo:landuse-a','A fabricated watershed example describes land use intensity increasing runoff and phosphorus inputs.'),
('demo:confounder-a','An illustrative causal diagram considers land use and temperature as confounders of the phosphorus and chlorophyll-a association.'),
('demo:sediment-a','A made-up sediment monitoring exercise uses turbidity but does not measure biological responses.'),
('demo:design-a','In a synthetic randomized intervention, a phosphorus reduction changes chlorophyll-a, but the result does not estimate any real lake effect.'),
('demo:unrelated-a','Synthetic quality-control note: sample labels and laboratory blanks should be reviewed before making environmental claims.'),
]
path=ROOT/'data/demo_evidence.jsonl'
path.write_text(''.join(json.dumps({'source_id':id,'page':1,'text':txt,'evidence_kind':'synthetic_demo'})+'\n' for id,txt in records),encoding='utf8')
qrels=[
 {'query':'phosphorus and chlorophyll-a in lakes','relevant_ids':['demo:phosphorus-a','demo:phosphorus-b','demo:phosphorus-c','demo:confounder-a','demo:design-a']},
 {'query':'zebra mussel effects on water clarity','relevant_ids':['demo:zebra-a','demo:clarity-a']},
 {'query':'temperature and algal biomass','relevant_ids':['demo:temperature-a','demo:phosphorus-c']},
]
(ROOT/'data/demo_qrels.json').write_text(json.dumps(qrels,indent=2),encoding='utf8')
# Illustrative annotations ONLY, no external expert ratings.
rows=[
 {'text':'Phosphorus and chlorophyll-a vary together in this hypothetical record.','label':'association','group_id':'synthetic_A'},
 {'text':'Zebra mussels and clarity were correlated in the illustrative sample.','label':'association','group_id':'synthetic_B'},
 {'text':'A randomized phosphorus intervention reduced chlorophyll-a in this fictional experiment.','label':'intervention','group_id':'synthetic_C'},
 {'text':'A simulated controlled trial manipulated temperature and measured algal response.','label':'intervention','group_id':'synthetic_D'},
 {'text':'The bibliography contains publication dates and journal issues.','label':'unrelated','group_id':'synthetic_E'},
 {'text':'Sampling instructions require the instrument to be cleaned.','label':'unrelated','group_id':'synthetic_F'},
]
(ROOT/'data/demo_nlp_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf8')
items=[{'question':f'Summarize hypothetical evidence example {i}.','answer':'The example is synthetic and cannot establish an empirical causal claim.','group_id':f'fixture_{i}'} for i in range(1,9)]
(ROOT/'data/demo_lora_train.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in items),encoding='utf8')
print('Synthetic fixtures generated:',len(records),'evidence records')
