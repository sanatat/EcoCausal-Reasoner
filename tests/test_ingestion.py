import json
from pathlib import Path
import pytest
from ecocausal.ingestion import sha256,pdf_ingest,csv_ingest

def test_pdf_pages_and_signature(tmp_path):
    import fitz
    doc=fitz.open();page=doc.new_page();page.insert_text((80,60),'Hypothetical phosphorus and chlorophyll-a report')
    p=tmp_path/'fixture.pdf';doc.save(p);doc.close()
    evidence,images=pdf_ingest(p,tmp_path/'out')
    assert evidence
    assert evidence[0].file_sha256==sha256(p.read_bytes())
    assert evidence[0].page==1
    assert images==[]
    assert json.loads((tmp_path/'out/ingestion_manifest.json').read_text())['text_blocks']>0

def test_fake_pdf_rejected(tmp_path):
    p=tmp_path/'fake.pdf';p.write_text('bad')
    with pytest.raises(ValueError):pdf_ingest(p,tmp_path/'out')

def test_csv_ingestion_and_missing_cols(tmp_path):
    p=tmp_path/'observations.csv';p.write_text('lake,phosphorus\nA,0.1\nB,0.2\n')
    evidence=csv_ingest(p,columns=['lake','phosphorus'])
    assert len(evidence)==2
    assert evidence[0].evidence_kind=='csv_data'
    with pytest.raises(ValueError):csv_ingest(p,columns=['unknown'])


def test_pdf_extracts_embedded_figure_with_same_provenance(tmp_path):
    import fitz
    from PIL import Image
    from io import BytesIO
    buf=BytesIO()
    Image.new('RGB',(32,24),'white').save(buf,format='PNG')
    doc=fitz.open();page=doc.new_page()
    page.insert_text((80,60),'Fictional chlorophyll and phosphorus chart')
    page.insert_image(fitz.Rect(80,90,240,210),stream=buf.getvalue())
    p=tmp_path/'figure.pdf';doc.save(p);doc.close()
    evidence,figures=pdf_ingest(p,tmp_path/'out')
    assert len(figures)==1
    assert figures[0].page==1
    assert figures[0].source_id.startswith('figure:')
    assert Path(figures[0].path).is_file()
    assert any(e.source_id.startswith('figure:') for e in evidence)


def test_different_documents_with_same_basename_have_distinct_evidence_ids(tmp_path):
    import fitz
    ids=[]
    for i in (1,2):
        folder=tmp_path/str(i);folder.mkdir()
        doc=fitz.open();page=doc.new_page()
        page.insert_text((80,60),f'Synthetic sample number {i}')
        p=folder/'paper.pdf';doc.save(p);doc.close()
        evidence,_=pdf_ingest(p,tmp_path/f'out{i}')
        ids.append(evidence[0].source_id)
    assert ids[0]!=ids[1]
