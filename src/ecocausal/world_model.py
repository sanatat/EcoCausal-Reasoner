"""A learned reduced-order controlled dynamical WORLD MODEL on synthetic trajectories only.

Actions are exogenous phosphorus-input controls; they are not causal estimates on real lakes.
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error


def simulate_controlled(steps=48,seed=42,actions=None):
    rng=np.random.default_rng(seed)
    p=np.empty(steps);chl=np.empty(steps);temp=np.empty(steps)
    p[0]=.10;chl[0]=16;temp[0]=17
    if actions is None:
        actions=np.clip(rng.normal(.10,.025,size=steps-1),.005,.2)
    actions=np.asarray(actions,dtype=float)
    if len(actions)!=steps-1:raise ValueError('actions must have length steps-1')
    if not np.isfinite(actions).all():raise ValueError('actions must be finite')
    for t in range(steps-1):
        temp[t+1]=.85*temp[t]+.15*(17+3*np.sin(t/6))+rng.normal(0,.2)
        p[t+1]=max(.001,.72*p[t]+.28*actions[t]+rng.normal(0,.004))
        chl[t+1]=max(.1,.65*chl[t]+.35*(8+75*p[t]+.35*(temp[t]-17))+rng.normal(0,.5))
    return np.column_stack([p,chl,temp]),actions


def simulate_trajectory(steps=48,seed=42,intervention=None):
    return simulate_controlled(steps=steps,seed=seed,actions=intervention)[0]


def fit_world_model(train_seeds=range(20),test_seeds=range(50,55),steps=65):
    train=[simulate_controlled(steps,seed=s) for s in train_seeds]
    X=np.vstack([np.column_stack([states[:-1],actions]) for states,actions in train])
    Y=np.vstack([states[1:] for states,_ in train])
    reg=Ridge(alpha=.002).fit(X,Y)
    holdouts=[simulate_controlled(steps,seed=s) for s in test_seeds]
    one_step=np.vstack([np.column_stack([states[:-1],actions]) for states,actions in holdouts])
    ground=np.vstack([states[1:] for states,_ in holdouts]);predicted=reg.predict(one_step)
    one_step_rmse=float(np.sqrt(mean_squared_error(ground,predicted)))
    persistence_rmse=float(np.sqrt(mean_squared_error(ground,one_step[:,:3])))
    rollouts=[]
    for trajectory,actions in holdouts:
        state=trajectory[0].copy();preds=[state]
        for a in actions:
            state=reg.predict(np.append(state,a)[None,:])[0]
            preds.append(state)
        rollouts.append(float(np.sqrt(np.mean((np.asarray(preds)-trajectory)**2))))
    # Action-conditioned counterfactual simulation under the *learned* surrogate.
    initial=np.array([.1,16.0,17.0])
    def forecast(action,steps=15):
        state=initial.copy();states=[state]
        for _ in range(steps):
            state=reg.predict(np.append(state,action)[None,:])[0]
            states.append(state)
        return np.asarray(states)
    baseline=forecast(.10);reduction=forecast(.07)
    return {'one_step_rmse':one_step_rmse,'persistence_rmse':persistence_rmse,
            'mean_open_loop_rollout_rmse':float(np.mean(rollouts)),
            'predicted_15_step_chlorophyll_difference_under_30pct_action_reduction':
                float(reduction[-1,1]-baseline[-1,1]),
            'coefficients':reg.coef_.tolist(),'intercept':reg.intercept_.tolist(),
            'action':'synthetic exogenous phosphorus input',
            'data_provenance':'synthetic action-conditioned trajectories only',
            'does_not_establish_real_ecosystem_prediction':True}
