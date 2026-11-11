"""RDF graph with PROV-O evidence links. Co-mention edges do not assert causation."""
from __future__ import annotations
from pathlib import Path
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from .schema import Claim

EC=Namespace('https://example.org/ecocausal/ontology/')
DOC=Namespace('https://example.org/ecocausal/record/')
PROV=Namespace('http://www.w3.org/ns/prov#')


def make_graph(claims:list[Claim])->Graph:
    g=Graph()
    g.bind('ec',EC);g.bind('prov',PROV);g.bind('doc',DOC)
    if claims:
        g.add((EC.Claim,RDFS.label,Literal('Unverified text-derived candidate relation')))
    for c in claims:
        cid=DOC['claim/'+c.claim_id.replace(':','_')]
        src=DOC['source/'+_safe(c.evidence.source_id)]
        g.add((cid,RDF.type,EC.Claim));g.add((cid,EC.subject,Literal(c.subject)))
        g.add((cid,EC.predicate,Literal(c.predicate)));g.add((cid,EC.object,Literal(c.object)))
        g.add((cid,EC.epistemicStatus,Literal(c.epistemic_status)))
        g.add((cid,EC.polarity,Literal(c.polarity)))
        if c.quote:g.add((cid,EC.supportingQuote,Literal(c.quote[:1000])))
        g.add((cid,PROV.wasDerivedFrom,src))
        g.add((src,EC.page,Literal(c.evidence.page,datatype=XSD.integer)))
        g.add((src,EC.evidenceKind,Literal(c.evidence.evidence_kind)))
        g.add((src,EC.excerpt,Literal(c.evidence.text[:1000])))
        if c.evidence.source_url:g.add((src,EC.sourceUrl,URIRef(c.evidence.source_url)))
        if c.evidence.file_sha256:g.add((src,EC.sha256,Literal(c.evidence.file_sha256)))
    return g


def _safe(s):
    from urllib.parse import quote
    return quote(s,safe='')


def query_claims(g:Graph,subject:str|None=None)->list[dict]:
    # Use SPARQL rather than a Python-only graph walk.
    q='''PREFIX ec: <https://example.org/ecocausal/ontology/>
          PREFIX prov: <http://www.w3.org/ns/prov#>
          SELECT ?c ?s ?p ?o ?source WHERE {
             ?c a ec:Claim ; ec:subject ?s ; ec:predicate ?p ; ec:object ?o ; prov:wasDerivedFrom ?source .
          } ORDER BY ?c'''
    records=[{'claim':str(row.c),'subject':str(row.s),'predicate':str(row.p),
              'object':str(row.o),'source':str(row.source)} for row in g.query(q)]
    return [r for r in records if subject is None or r['subject']==subject]


def export_graph(g:Graph,path:str|Path):
    g.serialize(destination=str(path),format='turtle')
