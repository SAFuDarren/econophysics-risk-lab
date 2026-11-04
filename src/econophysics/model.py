"""Explicit unit-order execution for the project's independently resampled ER model."""

from dataclasses import dataclass
import hashlib
import math
import random


@dataclass(frozen=True)
class Parameters:
    n: int = 128
    rho: float = 1.0
    a: float = 0.1
    lambda_impact: float = 0.02
    unit_order: float = 1.0
    initial_price: float = 100.0

    def __post_init__(self):
        if isinstance(self.n, bool) or not isinstance(self.n, int) or self.n < 2:
            raise ValueError('n must be an integer >= 2')
        values = [self.rho, self.a, self.lambda_impact, self.unit_order, self.initial_price]
        if not all(math.isfinite(x) for x in values):
            raise ValueError('parameters must be finite')
        if not 0 <= self.rho <= self.n - 1:
            raise ValueError('rho must lie in [0, n-1]')
        if not 0 < self.a < 0.5:
            raise ValueError('a must lie strictly between 0 and 1/2')
        if min(self.lambda_impact, self.unit_order, self.initial_price) <= 0:
            raise ValueError('impact, unit order and initial price must be positive')

    @property
    def edge_probability(self):
        return self.rho / (self.n - 1)


def derived_seed(seed, stream):
    return int.from_bytes(hashlib.sha256(f'{seed}:{stream}'.encode()).digest()[:16], 'big')


def er_edges(n, p, rng):
    """Exact independent Bernoulli edges via geometric skips of absent edges."""
    if n < 2 or not 0 <= p <= 1:
        raise ValueError('invalid graph size or probability')
    if p == 0:
        return []
    if p == 1:
        return [(v, w) for v in range(1, n) for w in range(v)]
    edges, v, w = [], 1, -1
    log_absence = math.log1p(-p)
    while v < n:
        w += 1 + math.floor(math.log1p(-rng.random()) / log_absence)
        while v < n and w >= v:
            w -= v
            v += 1
        if v < n:
            edges.append((v, w))
    return edges


def components(n, edges):
    parent, size = list(range(n)), [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for v, w in edges:
        if not 0 <= v < n or not 0 <= w < n or v == w:
            raise ValueError('edge must connect two distinct existing nodes')
        rv, rw = find(v), find(w)
        if rv != rw:
            if size[rv] < size[rw]:
                rv, rw = rw, rv
            parent[rw] = rv
            size[rv] += size[rw]
    groups = {}
    for node in range(n):
        groups.setdefault(find(node), []).append(node)
    return sorted(groups.values(), key=lambda group: group[0])


def draw_actions(count, a, rng):
    if not 0 < a < 0.5:
        raise ValueError('invalid activity probability')
    actions = []
    for _ in range(count):
        z = rng.random()
        actions.append(-1 if z < a else (1 if z >= 1 - a else 0))
    return actions


def aggregate_orders(sizes, actions, params):
    if len(sizes) != len(actions) or sum(sizes) != params.n:
        raise ValueError('sizes/actions must describe all n traders')
    if any(s <= 0 or not isinstance(s, int) for s in sizes) or any(x not in (-1, 0, 1) for x in actions):
        raise ValueError('invalid cluster size or action')
    signed = sum(s * x for s, x in zip(sizes, actions))
    active = sum(s * abs(x) for s, x in zip(sizes, actions))
    return params.lambda_impact * signed / params.n, params.unit_order * active


def execute_bar(groups, actions, params, open_price, rng):
    """All trader orders fill against an external counterparty, counted once."""
    members = [node for group in groups for node in group]
    if sorted(members) != list(range(params.n)):
        raise ValueError('groups must partition all traders without duplication')
    sizes = [len(group) for group in groups]
    ret, volume = aggregate_orders(sizes, actions, params)
    if not math.isfinite(open_price) or open_price <= 0:
        raise ValueError('open price must be positive and finite')
    signs = [action for size, action in zip(sizes, actions) for _ in range(size) if action]
    rng.shuffle(signs)
    log_price = math.log(open_price)
    prices = [open_price]
    amounts, trader_cash = [], []
    for sign in signs:
        log_price += params.lambda_impact * sign / params.n
        price = math.exp(log_price)
        if not math.isfinite(price) or price <= 0:
            raise ValueError('execution produced an invalid price')
        prices.append(price)
        amounts.append(params.unit_order * price)
        trader_cash.append(-sign * params.unit_order * price)
    signed_quantity = params.unit_order * sum(signs)
    cash_change = math.fsum(trader_cash)
    observation = {'r': ret, 'V': volume, 'D': math.fsum(amounts), 'O': prices[0],
                   'H': max(prices), 'L': min(prices), 'C': prices[-1]}
    bookkeeping = {'trader_inventory_change': signed_quantity,
                   'counterparty_inventory_change': -signed_quantity,
                   'trader_cash_change': cash_change, 'counterparty_cash_change': -cash_change,
                   'unit_trades': len(signs)}
    return observation, bookkeeping


def conditional_moments(sizes, params):
    if sum(sizes) != params.n:
        raise ValueError('cluster sizes do not sum to n')
    q, s2 = 2 * params.a, sum(s * s for s in sizes)
    return {'mean_r': 0.0, 'mean_V': q * params.unit_order * params.n,
            'var_r': q * (params.lambda_impact / params.n) ** 2 * s2,
            'var_V': q * (1 - q) * params.unit_order ** 2 * s2,
            'cov_r_V': 0.0, 's2': s2}


def simulate_window(params, length, seed):
    if not isinstance(length, int) or length < 1:
        raise ValueError('length must be a positive integer')
    graphs = random.Random(derived_seed(seed, 'graphs'))
    actions = random.Random(derived_seed(seed, 'actions'))
    execution = random.Random(derived_seed(seed, 'execution'))
    observations, latent, records = [], [], []
    price = params.initial_price
    first_graph = None
    for t in range(length):
        edges = er_edges(params.n, params.edge_probability, graphs)
        groups = components(params.n, edges)
        directions = draw_actions(len(groups), params.a, actions)
        obs, book = execute_bar(groups, directions, params, price, execution)
        obs = {'t': t, **obs}
        sizes = sorted((len(g) for g in groups), reverse=True)
        finite = sizes[1:]
        latent.append({'t': t, 'edge_count': len(edges), 'cluster_count': len(groups),
                       'largest_fraction': sizes[0] / params.n,
                       's2': sum(s * s for s in sizes),
                       'finite_susceptibility': sum(s * s for s in finite) / sum(finite) if finite else None})
        observations.append(obs)
        records.append(book)
        price = obs['C']
        if first_graph is None:
            first_graph = {'edges': edges, 'groups': groups, 'actions': directions}
    return observations, latent, records, first_graph


def simulate_aggregates(params, length, seed):
    """Exact r,V marginal using the same graph/action streams, without OHLC work."""
    if not isinstance(length, int) or length < 1:
        raise ValueError('length must be a positive integer')
    graphs = random.Random(derived_seed(seed, 'graphs'))
    actions = random.Random(derived_seed(seed, 'actions'))
    observations = []
    for _ in range(length):
        groups = components(params.n, er_edges(params.n, params.edge_probability, graphs))
        directions = draw_actions(len(groups), params.a, actions)
        ret, volume = aggregate_orders([len(group) for group in groups], directions, params)
        observations.append({'r': ret, 'V': volume})
    return observations
