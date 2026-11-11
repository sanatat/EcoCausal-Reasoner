"""Fully specified synthetic structural causal model, with observed confounders.

This is a methods benchmark. No empirical freshwater causal effect is established.
"""
from __future__ import annotations
import networkx as nx
import numpy as np
from dataclasses import dataclass


@dataclass(frozen=True)
class SCMParameters:
    beta_phosphorus: float=80.0
    beta_landuse: float=1.5
    beta_temperature: float=0.5
    base_chla: float=8.0


def causal_dag()->nx.DiGraph:
    g=nx.DiGraph()
    g.add_edges_from([('land_use','phosphorus'),('land_use','temperature'),
        ('land_use','chlorophyll_a'),('temperature','chlorophyll_a'),
        ('phosphorus','chlorophyll_a')])
    assert nx.is_directed_acyclic_graph(g)
    return g


def check_adjustment(adjustment:set[str])->bool:
    # Pearl's backdoor criterion for the *explicit* synthetic DAG.
    # Remove edges emanating from treatment, then test d-separation.
    g=causal_dag()
    treatment='phosphorus';outcome='chlorophyll_a'
    if treatment in adjustment or outcome in adjustment or any(v not in g for v in adjustment):
        return False
    descendants=nx.descendants(g,treatment)
    if descendants.intersection(adjustment):return False
    g.remove_edges_from(list(g.out_edges(treatment)))
    return nx.is_d_separator(g,{treatment},{outcome},adjustment)


def sample_scm(n=1000,seed=42,p:SCMParameters=SCMParameters(),do_phosphorus:float|None=None):
    if n<20:raise ValueError('Need at least 20 samples')
    rng=np.random.default_rng(seed)
    land_use=rng.normal(size=n)
    temperature=17+3*land_use+rng.normal(scale=1.5,size=n)
    eps_p=rng.normal(scale=.018,size=n)
    natural_p=.1+.035*land_use+eps_p
    phosphorus=np.full(n,do_phosphorus) if do_phosphorus is not None else natural_p
    eps_y=rng.normal(scale=2,size=n)
    chl=p.base_chla+p.beta_phosphorus*phosphorus+p.beta_landuse*land_use+p.beta_temperature*(temperature-17)+eps_y
    return {'land_use':land_use,'temperature':temperature,'phosphorus':phosphorus,
            'chlorophyll_a':chl,'natural_phosphorus':natural_p}


def estimate_ate(rows:dict, *, p0=.08,p1=.12,bootstrap=150,seed=7):
    if not check_adjustment({'land_use','temperature'}):raise ValueError('Invalid backdoor set')
    from sklearn.linear_model import LinearRegression
    x=np.column_stack([rows['phosphorus'],rows['land_use'],rows['temperature']])
    y=np.asarray(rows['chlorophyll_a'])
    fit=LinearRegression().fit(x,y)
    estimated=float(fit.coef_[0]*(p1-p0))
    rng=np.random.default_rng(seed)
    samples=[]
    for _ in range(bootstrap):
        indices=rng.integers(0,len(y),len(y))
        b=LinearRegression().fit(x[indices],y[indices])
        samples.append(float(b.coef_[0]*(p1-p0)))
    lo,hi=np.quantile(samples,[.025,.975]) if bootstrap>=10 else (float('nan'),float('nan'))
    return {'estimated_ate':estimated,'bootstrap_95_interval':[float(lo),float(hi)],
            'p0':p0,'p1':p1,'adjustment_set':['land_use','temperature'],
            'interpretation':'synthetic SCM only; not an empirical lake effect'}


def true_intervention_effect(p0=.08,p1=.12,p:SCMParameters=SCMParameters()):
    return p.beta_phosphorus*(p1-p0)


def intervention_experiment(n=2500,seed=42,bootstrap=150):
    data=sample_scm(n=n,seed=seed)
    result=estimate_ate(data,bootstrap=bootstrap)
    result['scm_true_ate']=true_intervention_effect()
    result['absolute_error']=abs(result['estimated_ate']-result['scm_true_ate'])
    result['observational_correlations_are_not_causal_evidence']=True
    result['dag_edges']=[list(x) for x in causal_dag().edges]
    return result


def dowhy_optional(rows:dict):
    """Optional DoWhy identification/refutation using a *declared* synthetic DAG."""
    try:
        import dowhy
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError('Install pip install -e .[causal]') from exc
    df=pd.DataFrame({key:rows[key] for key in ('land_use','temperature','phosphorus','chlorophyll_a')})
    graph='digraph {land_use -> phosphorus; land_use -> temperature; land_use -> chlorophyll_a; temperature -> chlorophyll_a; phosphorus -> chlorophyll_a;}'
    model=dowhy.CausalModel(data=df,treatment='phosphorus',outcome='chlorophyll_a',graph=graph)
    identified=model.identify_effect(proceed_when_unidentifiable=False)
    estimate=model.estimate_effect(identified,method_name='backdoor.linear_regression',
                                   control_value=.08,treatment_value=.12)
    return {'estimand':str(identified),'effect':float(estimate.value), 'scope':'synthetic benchmark'}
