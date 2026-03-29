"""
ILP-based exact circuit distance computation using Google OR-Tools.

Based on: https://github.com/shohamjac/ILP-circuit-distance
Adapted to use OR-Tools for better cross-platform support (including Apple Silicon).
"""

from ortools.linear_solver import pywraplp
import stim


def mip_circuit_distance(
    dem: stim.DetectorErrorModel,
    time_limit: int | None = None,
    *,
    verbose: bool = False,
    solver_name: str = None,
):
    """
    Solve for the minimum number of DEM error mechanisms whose combined effect:
    - flips NO detectors (all detectors even parity)
    - flips AT LEAST ONE logical observable (some logical has odd parity)

    Formulation:
        x_j ∈ {0,1}  for each error mechanism j
        y_i ∈ ℤ≥0    detector parity slack vars
        s_r ∈ ℤ≥0    logical parity slack vars
        w_r ∈ {0,1}  logical parity bits (mod 2)

        For each detector i:
            sum_j D[i,j] * x_j = 2 * y_i

        For each logical r:
            sum_j L[r,j] * x_j = 2 * s_r + w_r

        At least one logical flipped:
            sum_r w_r ≥ 1

        Objective:
            minimize sum_j x_j

    Returns:
        {
            "status": solver status string,
            "distance": int | None,         # minimal number of DEM errors, or None if infeasible
            "error_indices": list[int] | None,  # indices j of chosen DEM errors
        }
    """
    err_detectors, err_observables, num_detectors, num_observables = parse_dem_errors(
        dem
    )

    num_errors = len(err_detectors)
    if num_errors == 0:
        return {"status": None, "distance": None, "error_indices": None}

    # Build inverted maps: for each detector/logical, which errors touch it
    det_to_errors = [[] for _ in range(num_detectors)]
    for j, dets in enumerate(err_detectors):
        for d in dets:
            det_to_errors[d].append(j)

    obs_to_errors = [[] for _ in range(num_observables)]
    for j, obs in enumerate(err_observables):
        for r in obs:
            obs_to_errors[r].append(j)

    # Create the MIP solver with SCIP backend (or CBC if available)
    if solver_name is None:
        solver_name = "SCIP"
    solver = pywraplp.Solver.CreateSolver(solver_name)
    if not solver:
        # Fallback to CBC
        solver = pywraplp.Solver.CreateSolver("CBC")
    if not solver:
        return {"status": "NO_SOLVER", "distance": None, "error_indices": None}

    # Upper bounds for slack vars (parity counts)
    max_pairs = num_errors // 2

    # Decision variables: x_j ∈ {0,1}, select error mechanisms
    x = [solver.BoolVar(f"x_{j}") for j in range(num_errors)]

    # Detector slack vars: y_i ∈ ℤ≥0, enforce even parity (no detector flips)
    y = [solver.IntVar(0, max_pairs, f"y_det_{i}") for i in range(num_detectors)]

    # Logical slack vars and parity bits
    s = [solver.IntVar(0, max_pairs, f"s_log_{r}") for r in range(num_observables)]
    w = [solver.BoolVar(f"w_log_{r}") for r in range(num_observables)]

    # Detector parity constraints: sum_j D[i,j] x_j = 2 y_i
    for i in range(num_detectors):
        if det_to_errors[i]:
            solver.Add(sum(x[j] for j in det_to_errors[i]) == 2 * y[i])

    # Logical parity constraints: sum_j L[r,j] x_j = 2 s_r + w_r
    for r in range(num_observables):
        if obs_to_errors[r]:
            solver.Add(sum(x[j] for j in obs_to_errors[r]) == 2 * s[r] + w[r])
        else:
            # This logical is never affected; enforce w_r = 0
            solver.Add(w[r] == 0)

    # At least one logical has odd parity
    if num_observables > 0:
        solver.Add(sum(w) >= 1)
    else:
        # No logicals defined => no undetected logical error makes sense
        return {"status": None, "distance": None, "error_indices": None}

    # Objective: minimize number of errors
    solver.Minimize(sum(x))

    # Set time limit
    if time_limit is not None:
        solver.SetTimeLimit(time_limit * 1000)  # milliseconds

    # Solve
    status = solver.Solve()

    status_names = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }
    status_str = status_names.get(status, f"UNKNOWN_{status}")

    if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        return {"status": status_str, "distance": None, "error_indices": None}

    # Extract solution
    chosen = [j for j in range(num_errors) if x[j].solution_value() >= 0.5]
    distance = len(chosen)

    return {
        "status": status_str,
        "distance": distance,
        "error_indices": chosen,
        "lower_bound": (
            solver.Objective().BestBound()
            if hasattr(solver.Objective(), "BestBound")
            else distance
        ),
    }


def parse_dem_errors(dem: stim.DetectorErrorModel):
    """
    Extract, for each error mechanism in the DEM:
        - which detectors it flips
        - which logical observables it flips

    Returns:
        err_detectors: list[list[int]]
        err_observables: list[list[int]]
        num_detectors: int
        num_observables: int
    """
    # Flatten the DEM to resolve all shift_detectors and repeat blocks
    dem = dem.flattened()

    err_detectors = []
    err_observables = []

    for inst in dem:
        if inst.type == "error":
            dets = []
            obs = []
            for t in inst.targets_copy():
                if t.is_relative_detector_id():
                    # In flattened DEM, relative IDs are absolute
                    dets.append(t.val)
                elif t.is_logical_observable_id():
                    # observable (logical) index
                    obs.append(t.val)

            # Deduplicate and sort for consistency
            dets = sorted(set(dets))
            obs = sorted(set(obs))

            err_detectors.append(dets)
            err_observables.append(obs)

        # other DEM instructions are irrelevant here

    num_detectors = dem.num_detectors
    num_observables = dem.num_observables

    return err_detectors, err_observables, num_detectors, num_observables
