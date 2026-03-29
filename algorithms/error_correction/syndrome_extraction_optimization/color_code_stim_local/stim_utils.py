import io
import math
import re
from typing import List, Tuple

import numpy as np
import stim
from cairosvg import svg2png
from scipy.sparse import csc_matrix


def dem_to_str(dem: stim.DetectorErrorModel) -> str:
    """
    Convert a detector error model to its string representation.

    Parameters
    ----------
    dem : stim.DetectorErrorModel
        The detector error model to convert.

    Returns
    -------
    str
        String representation of the detector error model.
    """
    buffer = io.StringIO()
    dem.to_file(buffer)
    s = buffer.getvalue()
    return s


def str_to_dem(s: str) -> stim.DetectorErrorModel:
    """
    Convert a string representation back to a detector error model.

    Parameters
    ----------
    s : str
        String representation of a detector error model.

    Returns
    -------
    stim.DetectorErrorModel
        The reconstructed detector error model.
    """
    buffer = io.StringIO(s)
    return stim.DetectorErrorModel.from_file(buffer)


def remove_obs_from_dem(dem: stim.DetectorErrorModel) -> stim.DetectorErrorModel:
    """
    Remove detectors acting as observables from a detector error model.

    Parameters
    ----------
    dem : stim.DetectorErrorModel
        The detector error model to process.

    Returns
    -------
    stim.DetectorErrorModel
        A new detector error model with all detectors acting as observables removed.
    """
    num_dets = dem.num_detectors
    num_obss = dem.num_observables
    s = dem_to_str(dem)

    # Remove last lines corresponding to observables
    s = "\n".join(s.splitlines()[:-num_obss]) + "\n"

    # Build a regex pattern to match the exact text "D{num_dets - 1}"
    patterns = [r"\bD" + str(num_dets - num_obss + i) + r"\b" for i in range(num_obss)]
    # Remove all occurrences of that pattern
    for pattern in patterns:
        s = re.sub(pattern, "", s)

    # Clean up extra spaces in each line (e.g. converting "D0  D1  L0" to "D0 D1 L0")
    s = "\n".join(" ".join(line.split()) for line in s.splitlines())

    return str_to_dem(s)


def dem_to_parity_check(
    dem: stim.DetectorErrorModel,
) -> Tuple[csc_matrix, csc_matrix, np.ndarray]:
    """
    Convert a detector error model (DEM) into a parity check matrix, observable matrix,
    and probability vector.

    Parameters
    ----------
    dem : stim.DetectorErrorModel
        The detector error model to convert.

    Returns
    -------
    H : csc_matrix
        A boolean matrix of shape (number of detectors, number of errors)
        where H[i, j] = True if detector i is involved in error j.
    obs_matrix : csc_matrix
        A boolean matrix of shape (number of observables, number of errors)
        where obs_matrix[i, j] = True if observable i is involved in error j.
    p : np.ndarray
        A 1D numpy array of probabilities corresponding to each error.
    """
    dem = dem.flattened()

    probabilities = []
    det_ids_in_ems = []
    obs_ids_in_ems = []

    for _, instruction in enumerate(dem):
        if instruction.type == "error":
            det_ids = []
            obs_ids = []
            det_ids_in_ems.append(det_ids)
            obs_ids_in_ems.append(obs_ids)

            # Extract probability
            prob = float(instruction.args_copy()[0])
            probabilities.append(prob)

            for target in instruction.targets_copy():
                if target.is_relative_detector_id():
                    det_ids.append(int(str(target)[1:]))
                elif target.is_logical_observable_id():
                    obs_ids.append(int(str(target)[1:]))
                else:
                    raise ValueError(f"Unknown target type: {target}")

    p = np.array(probabilities)

    # Create the parity check matrix H
    if det_ids_in_ems:
        num_detectors = dem.num_detectors
        num_errors = len(det_ids_in_ems)

        # Prepare data for CSC matrix construction
        row_indices = []
        col_indices = []
        data = []

        for error_idx, det_ids in enumerate(det_ids_in_ems):
            for det_id in det_ids:
                row_indices.append(det_id)
                col_indices.append(error_idx)
                data.append(True)

        H = csc_matrix(
            (data, (row_indices, col_indices)),
            shape=(num_detectors, num_errors),
            dtype=bool,
        )
    else:
        H = csc_matrix((0, 0), dtype=bool)

    # Create the observable matrix
    if obs_ids_in_ems:
        # Find the maximum observable ID
        num_observables = dem.num_observables
        num_errors = len(obs_ids_in_ems)

        # Prepare data for CSC matrix construction
        row_indices = []
        col_indices = []
        data = []

        for error_idx, obs_ids in enumerate(obs_ids_in_ems):
            for obs_id in obs_ids:
                row_indices.append(obs_id)
                col_indices.append(error_idx)
                data.append(True)

        obs_matrix = csc_matrix(
            (data, (row_indices, col_indices)),
            shape=(num_observables, num_errors),
            dtype=bool,
        )
    else:
        obs_matrix = csc_matrix((0, 0), dtype=bool)

    return H, obs_matrix, p


# def get_observable_matrix_from_dem(
#     dem: stim.DetectorErrorModel,
# ) -> csc_matrix:
#     """
#     Extracts the observable matrix from a Detector Error Model.

#     The resulting matrix indicates which error mechanisms (columns) affect
#     which logical observables (rows).

#     Parameters
#     ----------
#     dem : stim.DetectorErrorModel
#         The input Detector Error Model.

#     Returns
#     -------
#     obs_matrix : scipy.sparse.csc_matrix
#         A boolean sparse matrix in CSC format. obs_matrix[i, j] is True
#         if and only if the j-th error mechanism (in the flattened DEM order)
#         affects the i-th logical observable (L{i}).
#         The number of rows equals dem.num_observables.
#         The number of columns equals the total count of 'error' instructions
#         in the flattened DEM.
#     """
#     # Flatten the DEM to handle loops and get a linear sequence of errors
#     try:
#         flattened_dem = dem.flattened()
#     except Exception as e:
#         print(f"Error during DEM flattening: {e}")
#         # Re-raise or handle as appropriate
#         raise e

#     num_observables = dem.num_observables
#     if num_observables == 0:
#         # If there are no observables, the matrix has 0 rows.
#         # We still need to count errors to determine the number of columns.
#         num_errors = 0
#         for instruction in flattened_dem:
#             if (
#                 isinstance(instruction, stim.DemInstruction)
#                 and instruction.type == "error"
#             ):
#                 num_errors += 1
#         return csc_matrix((0, num_errors), dtype=bool)

#     # Data for constructing the CSC matrix directly
#     row_indices: List[int] = (
#         []
#     )  # Stores the observable index (row) for each non-zero entry
#     col_pointers: List[int] = [0]  # indptr array for CSC format
#     data: List[bool] = []  # Stores the non-zero values (always True for us)

#     error_index_counter = 0  # Tracks the current error mechanism (column index)

#     for instruction in flattened_dem:
#         # We only care about 'error' instructions for the columns
#         if isinstance(instruction, stim.DemInstruction) and instruction.type == "error":
#             instruction_targets = instruction.targets_copy()

#             # Check which observables this error affects
#             for target in instruction_targets:
#                 if target.is_logical_observable_id():
#                     observable_id = int(str(target)[1:])
#                     if observable_id >= num_observables:
#                         # This shouldn't happen if num_observables is correct
#                         raise ValueError(
#                             f"Error instruction {error_index_counter} targets "
#                             f"observable L{observable_id}, but DEM only reports "
#                             f"{num_observables} observables."
#                         )
#                     row_indices.append(observable_id)
#                     data.append(True)

#             # Update the column pointer: points to the start of the *next* column's data
#             col_pointers.append(len(row_indices))
#             error_index_counter += 1

#         # Ignore other instruction types like 'detector', 'logical_observable'

#     num_columns = error_index_counter

#     # Create the CSC matrix
#     obs_matrix = csc_matrix(
#         (data, row_indices, col_pointers),
#         shape=(num_observables, num_columns),
#         dtype=bool,
#     )

#     return obs_matrix


def save_circuit_diagram(
    circuit: stim.Circuit, path: str, type: str = "timeline-svg"
) -> None:
    """
    Save a textual diagram of ``circuit`` to ``path``.

    Parameters
    ----------
    circuit : stim.Circuit
        Circuit whose diagram will be saved.
    path : str
        File path for the output diagram.
    type : str, default 'timeline-svg'
        Format used by ``stim.Circuit.diagram``.

    Returns
    -------
    None
        This function writes to disk and does not return a value.
    """

    print(circuit.diagram(type=type), file=open(path, "w"))


def separate_depolarizing_errors(circuit: stim.Circuit) -> stim.Circuit:
    """
    Separates depolarizing errors in a Stim circuit into X and Z error components
    using modified probability calculations.

    DEPOLARIZE1(p) is replaced by X_ERROR(pxz) Z_ERROR(pxz).
    pxz = 2*q1*(1 - q1), where q1 = (1 - sqrt(1 - 4p/3))/2.

    DEPOLARIZE2(p) on qubits A and B is replaced by a sequence of:
    X_ERROR(p_comp) on A
    Z_ERROR(p_comp) on A
    X_ERROR(p_comp) on B
    Z_ERROR(p_comp) on B
    CORRELATED_ERROR(p_comp) XA*XB
    CORRELATED_ERROR(p_comp) ZA*ZB
    p_comp = 4*q2*(1 - q2)*(1 - 2*q2 + 2*q2**2), where q2 = (1 - (1 - 16p/15)**(1/8))/2.

    Parameters
    ----------
    circuit : stim.Circuit
        The input circuit containing depolarizing errors to be separated.

    Returns
    -------
    stim.Circuit
        A new circuit with DEPOLARIZE1 and DEPOLARIZE2 instructions replaced
        by sequences of X and Z type errors according to the specified formulas.

    Raises
    ------
    ValueError
        - If DEPOLARIZE1 probability `p` is not in the range `[0, 0.75]`.
        - If DEPOLARIZE2 probability `p` is not in the range `[0, 15/16]`.
        - If DEPOLARIZE1 or DEPOLARIZE2 targets non-qubit values.
        - If DEPOLARIZE2 has an odd number of targets.
    """
    new_circuit = stim.Circuit()

    for instruction in circuit:
        if isinstance(instruction, stim.CircuitInstruction):
            name = instruction.name
            targets = instruction.targets_copy()
            args = instruction.gate_args_copy()

            if name == "DEPOLARIZE1":
                if len(args) != 1:
                    raise ValueError(
                        f"Instruction {instruction} DEPOLARIZE1 must have exactly one argument (probability)."
                    )
                p = args[0]
                if not (0 <= p <= 0.75):
                    raise ValueError(
                        f"DEPOLARIZE1 probability p={p} must be in [0, 0.75] for this decomposition. Found in instruction: {instruction}"
                    )

                # Handle p=0 case explicitly
                if p == 0:
                    q1 = 0.0
                    pxz = 0.0
                else:
                    term_under_sqrt = 1.0 - 4.0 * p / 3.0
                    # Clamp negative due to potential floating point error
                    if term_under_sqrt < 0:
                        term_under_sqrt = 0
                    q1 = (1.0 - math.sqrt(term_under_sqrt)) / 2.0
                    pxz = 2.0 * q1 * (1.0 - q1)

                if pxz > 1e-15:  # Add errors only if probability is non-negligible
                    for target in targets:
                        if not target.is_qubit_target:
                            raise ValueError(
                                f"DEPOLARIZE1 target must be a qubit target. Found {target} in instruction: {instruction}"
                            )
                        q = target.value
                        new_circuit.append("X_ERROR", [q], pxz)
                        new_circuit.append("Z_ERROR", [q], pxz)

            elif name == "DEPOLARIZE2":
                if len(args) != 1:
                    raise ValueError(
                        f"Instruction {instruction} DEPOLARIZE2 must have exactly one argument (probability)."
                    )
                p = args[0]
                if not (0 <= p <= 15.0 / 16.0):
                    raise ValueError(
                        f"DEPOLARIZE2 probability p={p} must be in [0, 15/16] for this decomposition. Found in instruction: {instruction}"
                    )

                # Handle p=0 case explicitly
                if p == 0:
                    q2 = 0.0
                    p_component = 0.0
                else:
                    term_in_power = 1.0 - 16.0 * p / 15.0
                    # Clamp negative due to potential floating point error
                    if term_in_power < 0:
                        term_in_power = 0
                    q2 = (1.0 - term_in_power ** (1.0 / 8.0)) / 2.0
                    # Probability of odd number of successes in 4 trials with prob q2
                    # P(k=1) + P(k=3) = C(4,1)q^1(1-q)^3 + C(4,3)q^3(1-q)^1
                    p_component = 4.0 * q2 * (1.0 - q2) ** 3 + 4.0 * q2**3 * (1.0 - q2)
                    # Simplified form: 4*q2*(1-q2)*( (1-q2)^2 + q2^2 ) = 4*q2*(1-q2)*(1 - 2*q2 + 2*q2**2)

                if (
                    p_component > 1e-15
                ):  # Add errors only if probability is non-negligible
                    if len(targets) % 2 != 0:
                        raise ValueError(
                            f"DEPOLARIZE2 requires an even number of targets. Found {len(targets)} in instruction: {instruction}"
                        )

                    for i in range(0, len(targets), 2):
                        t_a = targets[i]
                        t_b = targets[i + 1]
                        if not t_a.is_qubit_target or not t_b.is_qubit_target:
                            raise ValueError(
                                f"DEPOLARIZE2 targets must be qubit targets. Found {t_a}, {t_b} in instruction: {instruction}"
                            )
                        qA = t_a.value
                        qB = t_b.value

                        # Single qubit X/Z errors
                        new_circuit.append("X_ERROR", [qA], p_component)
                        new_circuit.append("Z_ERROR", [qA], p_component)
                        new_circuit.append("X_ERROR", [qB], p_component)
                        new_circuit.append("Z_ERROR", [qB], p_component)

                        # Two qubit X/Z errors
                        new_circuit.append(
                            "CORRELATED_ERROR",
                            [stim.target_x(qA), stim.target_x(qB)],
                            p_component,
                        )
                        new_circuit.append(
                            "CORRELATED_ERROR",
                            [stim.target_z(qA), stim.target_z(qB)],
                            p_component,
                        )
            else:
                # Copy other instructions directly
                new_circuit.append(instruction)

        elif isinstance(instruction, stim.CircuitRepeatBlock):
            # Recursively process the body of the repeat block
            new_body = separate_depolarizing_errors(instruction.body_copy())
            # Create a new repeat block with the processed body
            new_block = stim.CircuitRepeatBlock(instruction.repeat_count, new_body)
            new_circuit.append(new_block)
        else:
            # Should not happen with current stim versions but good practice
            raise TypeError(f"Unknown object in circuit: {instruction}")

    return new_circuit
