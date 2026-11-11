"""PDF/CSV provenance-first ingestion. PDFs are user-supplied, never assumed public domain."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from .schema import Evidence, Figure


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_ingest(path: str | Path, output_dir: str | Path, *, max_images=24) -> tuple[list[Evidence], list[Figure]]:
    import fitz
    p = Path(path)
    if not p.is_file() or p.suffix.lower() != '.pdf' or p.open('rb').read(5) != b'%PDF-':
        raise ValueError('Expected a readable PDF with PDF signature')
    digest = sha256(p.read_bytes())
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(p)
    table_errors = []
    chunks: list[Evidence] = []
    figures: list[Figure] = []
    for i, page in enumerate(doc):
        page_no=i+1
        blocks = page.get_text('blocks')
        for j, b in enumerate(blocks):
            if len(b)<5 or not isinstance(b[4],str) or not b[4].strip():
                continue
            text=b[4].strip()
            chunks.append(Evidence(source_id=f'{p.stem}:{digest[:12]}:p{page_no}:b{j}', page=page_no, text=text,
                          file_sha256=digest, evidence_kind='pdf_text'))
        # Extract embedded raster figures, not arbitrary page renderings.
        for k,img in enumerate(page.get_images(full=True)):
            if len(figures)>=max_images:break
            blob=doc.extract_image(img[0]); content=blob['image']; sh=sha256(content)
            ext=blob.get('ext','png')
            dest=out/f'{p.stem}_p{page_no}_{sh[:12]}.{ext}'
            if not dest.exists():dest.write_bytes(content)
            figures.append(Figure(image_sha256=sh,document_sha256=digest,source_id=f'{p.stem}:{digest[:12]}',page=page_no,path=str(dest)))
        # PyMuPDF table detector may fail on some layouts; failure is logged by caller, not fabricated.
        try:
            for k,table in enumerate(page.find_tables().tables):
                rows=table.extract()
                if rows:
                    txt='\n'.join(' | '.join('' if v is None else str(v) for v in row) for row in rows)
                    chunks.append(Evidence(source_id=f'{p.stem}:{digest[:12]}:p{page_no}:table{k}',page=page_no,
                                text=txt, evidence_kind='pdf_table',file_sha256=digest))
        except (ValueError, RuntimeError, AttributeError) as exc:
            table_errors.append({'page':page_no,'error_type':type(exc).__name__})
    doc.close()
    manifest={'pdf':p.name,'sha256':digest,'text_blocks':sum(e.evidence_kind=='pdf_text' for e in chunks),
              'tables':sum(e.evidence_kind=='pdf_table' for e in chunks),'figures':len(figures),
              'table_extraction_errors':table_errors,
              'caution':'Extracted PDF tables and generated image captions require human verification'}
    (out/'ingestion_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    return chunks,figures


def csv_ingest(path: str | Path, *, columns: list[str], source_name: str | None=None) -> list[Evidence]:
    p=Path(path); digest=sha256(p.read_bytes()); out=[]
    with p.open(newline='',encoding='utf-8-sig') as f:
        rdr=csv.DictReader(f)
        missing=set(columns)-set(rdr.fieldnames or ())
        if missing:raise ValueError(f'Absent CSV columns: {sorted(missing)}')
        for n,row in enumerate(rdr,2):
            text=' | '.join(f'{k}={row.get(k,"")}' for k in columns)
            out.append(Evidence(source_id=f'{source_name or p.stem}:{digest[:12]}:row{n}',page=n,
                       text=text,evidence_kind='csv_data',file_sha256=digest))
    return out
