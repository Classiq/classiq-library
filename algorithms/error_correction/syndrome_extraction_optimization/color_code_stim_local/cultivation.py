import math
from typing import Dict, FrozenSet, List, Literal, Optional, Sequence, Tuple, Union

import stim

from pathlib import Path


def _load_cultivation_circuit(d: int, p: float) -> stim.Circuit:
    """
    Loads a cultivation circuit from a file.
    """
    current_folder = Path(__file__).parent
    cultivation_circuit = stim.Circuit.from_file(
        f"{current_folder}/assets/cultivation_circuits/d{d}_p{p}.stim"
    )
    return cultivation_circuit


def _reformat_cultivation_circuit(
    circuit: stim.Circuit,
    d: int,
    qubit_coords: Dict[int, Tuple[int, int]],
    x_offset: int = 0,
    y_offset: int = 0,
) -> Tuple[stim.Circuit, Dict[Tuple[Literal["X", "Z"], FrozenSet[int]], List[int]]]:
    """
    Reformat a cultivation circuit to fit the format of our color code circuit.
    Detectors are annotated by appending -2 to their coordinates. (e.g. (0, 0, 0, -2))

    Parameters
    ----------
    circuit : stim.Circuit
        The input cultivation circuit.
    d : int
        The code distance of the color code.
    qubit_coords : Dict[int, Tuple[int, int]]
        A dictionary mapping qubit indices to their coordinates in the color code circuit.
    x_offset : int
        The x offset to apply to the coordinates (default 0).
    y_offset : int
        The y offset to apply to the coordinates (default 0).

    Returns
    -------
    trimmed_circuit : stim.Circuit
        The circuit containing only the instructions before measuring final stabilizers.
    final_detectors_info : Dict[Tuple[Literal['X', 'Z'], FrozenSet[int]], List[int]]
        Each item indicates the information of a detector after the final TICK.
        Its key corresponds to the target of the detector after the final TICK (which is unique),
        represented as (Pauli type character, frozenset of qubit indices).
        Its value is a list of measurement target indices (`rec[-k]`) that correspond to other measurements in the detector before the final TICK.
    """
    # 1. Adjust the coordinates of the qubits and detectors
    adjusted_circuit = _adjust_cultivation_circuit_coords(
        circuit, d, x_offset=x_offset, y_offset=y_offset
    )

    # 2. Reorder the qubits
    # Convert qubit_coords list to qubit_order dictionary
    qubit_order: Dict[Tuple[int, int], int] = {}
    for idx, coords in qubit_coords.items():
        coords = tuple([round(coord) for coord in coords])
        qubit_order[coords] = idx
    reordered_circuit = _reorder_qubits_in_circuit(adjusted_circuit, qubit_order)

    # 3. Isolate the final block
    circuit, final_detectors_info = _isolate_final_mpps(reordered_circuit)

    # 4. Remove observable
    circuit_new = stim.Circuit()
    for inst in circuit:
        if inst.name == "OBSERVABLE_INCLUDE":
            continue
        circuit_new.append(inst)

    return circuit_new, final_detectors_info


def _is_data_qubit(ox: int, oy: int) -> bool:
    """
        Determines if a qubit at original coordinates (ox, oy) is a data qubit
        based on the provided rules.

        Parameters
    ----------
        ox: Original X coordinate.
        oy: Original Y coordinate.

        Returns
        -------
        True if it's a data qubit, False otherwise (meaning it's an ancillary qubit).
    """
    if oy % 2 == 0:  # y is even
        # x=0, 3, 4, 7, 8, 11, 12, ...
        # Pattern: x % 4 is 0 or 3
        return ox % 4 == 0 or ox % 4 == 3
    else:  # y is odd
        # x=1, 2, 5, 6, 9, 10, 13, 14, ...
        # Pattern: x % 4 is 1 or 2
        return ox % 4 == 1 or ox % 4 == 2


def _get_ancilla_type(ox: int, oy: int) -> str:
    """
    Determines the type (X or Z) of an ancillary qubit.
    Assumes the input coordinates belong to an ancillary qubit.

    Parameters
    ----------
    ox: Original X coordinate.
    oy: Original Y coordinate.

    Returns
    -------
    'X' or 'Z'.
    """
    if (ox + oy) % 2 != 0:  # Odd sum
        return "X"
    else:  # Even sum
        return "Z"


def _map_qubit_coords(ox: int, oy: int, d: int) -> tuple[float, int]:
    """
    Maps original qubit coordinates (ox, oy) to new coordinates (nx, ny).

    Parameters
    ----------
    ox: Original X coordinate.
    oy: Original Y coordinate.
    d: The code distance.

    Returns
    -------
    A tuple (nx, ny) representing the new coordinates.
    nx can be a float for ancillary qubits. ny is always an integer.
    """
    # Rule 1: New Y coordinate is the same as the original
    ny = oy

    k = d - 1

    # Rule 2: Determine qubit type and calculate New X accordingly
    if _is_data_qubit(ox, oy):
        nx = int(2 * math.ceil(k * 3 - 1.5 * ox))
    else:
        anc_type = _get_ancilla_type(ox, oy)

        group_index = (ox - 1) // 2
        nx_base = 6 * k - 4 - 6 * group_index

        # Apply offset based on ancilla type
        if anc_type == "X":
            nx = nx_base + 1
        else:  # anc_type == 'Z'
            nx = nx_base - 1

    return (nx, ny)


def _transform_coords(
    coords: Sequence[int | float],
    d: int,
    x_offset: int = 0,
    y_offset: int = 0,
    t_offset: int = 0,
) -> Tuple[int | float]:
    """
    Transforms the first coordinate (x) using _map_qubit_coords logic,
    keeping other coordinates (y, z, ...) the same.

    Parameters
    ----------
    coords: The list of original coordinates [x, y, z, ...].
    d: The code distance parameter for _map_qubit_coords.
    x_offset: The x offset to apply to the coordinates (default 0).
    y_offset: The y offset to apply to the coordinates (default 0).
    t_offset: The t offset to apply to the coordinates of detectors (default 0).
    Returns
    -------
    A list of transformed coordinates [x', y, z, ...].
    """
    if not coords:
        return []

    x = coords[0]
    rest = coords[1:]

    # Determine the effective 'oy' to use for mapping.
    oy_for_map = round(coords[1])

    if abs(x - round(x)) < 1e-9:
        new_x = _map_qubit_coords(round(x), oy_for_map, d)[0]
    else:
        # --- Float Case ---
        x1 = math.floor(x)
        x2 = math.ceil(x)

        # Handle edge case where floor and ceil are the same (should be rare with tolerance check)
        if x1 == x2:
            new_x = _map_qubit_coords(int(x1), oy_for_map, d)[0]
        else:
            # Map the integer coordinates bounding the float coordinate
            nx1 = _map_qubit_coords(int(x1), oy_for_map, d)[0]
            nx2 = _map_qubit_coords(int(x2), oy_for_map, d)[0]

            # Linearly interpolate between the transformed coordinates
            # based on the original float's position between the integers.
            ratio = (x - x1) / (x2 - x1)
            new_x = nx1 + ratio * (nx2 - nx1)

    # Combine the new x with the original rest of the coordinates & apply y_offset
    new_coords = [new_x] + rest
    new_coords[0] += x_offset
    new_coords[1] += y_offset
    try:
        new_coords[2] += t_offset
    except IndexError:
        pass

    return tuple(new_coords)


def _adjust_cultivation_circuit_coords(
    circuit: stim.Circuit, d: int, x_offset: int = 0, y_offset: int = 0
) -> stim.Circuit:
    """
    Adjusts the coordinates of qubits and detectors in a cultivation circuit.

    Iterates through the circuit, modifying QUBIT_COORDS and DETECTOR instructions
    that specify coordinates. It applies a transformation to the first coordinate (x)
    based on the `_map_qubit_coords` logic, leaving other coordinate dimensions
    unchanged.

    Note: This function implicitly flattens REPEAT blocks and SHIFT_COORDS
    by processing instruction by instruction and creating a new circuit.
    If precise handling of nested structures without flattening is needed,
    a more complex recursive approach would be required. For coordinate
    adjustment, operating on a flattened representation is often simpler.

    Parameters
    ----------
    circuit: The input stim.Circuit, potentially containing coordinate data.
    d: The code distance, used by the coordinate transformation logic.
    x_offset: The x offset to apply to the coordinates (default 0).
    y_offset: The y offset to apply to the coordinates (default 0).

    Returns:
        A new stim.Circuit with adjusted coordinates in QUBIT_COORDS and
        DETECTOR instructions. Other instructions are preserved.
    """
    # It's often easier to work with a flattened circuit when modifying
    # elements affected by loops or coordinate shifts.
    flattened_circuit = circuit.flattened()
    new_circuit = stim.Circuit()

    detectors_ts = [coords[2] for coords in circuit.get_detector_coordinates().values()]
    t_offset = -max(detectors_ts) + 1

    for instruction in flattened_circuit:
        # Since we flattened, we only expect stim.CircuitInstruction here
        if not isinstance(instruction, stim.CircuitInstruction):
            # This case should not happen after flattening, but handle defensively
            print(
                f"Warning: Encountered non-instruction in flattened circuit: {type(instruction)}"
            )
            # If it were a repeat block, we might recursively process its body
            # but flattening avoids this. We'll just skip non-instructions here.
            continue

        name = instruction.name
        targets = instruction.targets_copy()
        args = (
            instruction.gate_args_copy()
        )  # Parens arguments (like probabilities or coordinates)

        # Instructions that define coordinates that need transformation
        if name == "QUBIT_COORDS":
            if args:
                new_args = _transform_coords(
                    args, d, x_offset=x_offset, y_offset=y_offset, t_offset=t_offset
                )
                # Append the instruction with modified coordinates (args)
                new_circuit.append(name, targets, new_args)
            else:
                # QUBIT_COORDS should always have args, but handle defensively
                new_circuit.append(instruction)
        elif name == "DETECTOR":
            if args:  # Check if the detector instruction *has* coordinates specified
                new_args = _transform_coords(
                    args, d, x_offset=x_offset, y_offset=y_offset, t_offset=t_offset
                )
                # (x, y, t, pauli, color, flag)
                new_args = new_args[:3] + (-1, -1, -2)
                # Append the instruction with modified coordinates (args)
                new_circuit.append(name, targets, new_args)
            else:
                # Detector instruction without coordinates, append as is
                new_circuit.append(instruction)
        else:
            # For all other instructions, append them unmodified
            new_circuit.append(instruction)

    return new_circuit


def _get_qubit_coordinate_map(circuit: stim.Circuit) -> Dict[int, Tuple[int, int]]:
    """
    Extracts qubit coordinates from QUBIT_COORDS instructions.

    Assumes coordinates are 2D integers for mapping purposes. Rounds floats.

    Parameters
    ----------
    circuit: The stim circuit to extract coordinates from.

    Returns
    -------
    A dictionary mapping qubit index (int) to its coordinates (Tuple[int, int]).
    Raises ValueError if coordinates are missing, not 2D, or non-numeric.
    """
    coord_map: Dict[int, Tuple[int, int]] = {}
    # Use get_final_qubit_coordinates which handles multiple declarations
    final_coords = circuit.get_final_qubit_coordinates()

    for qubit_index, coords_float in final_coords.items():
        if len(coords_float) < 2:
            raise ValueError(
                f"Qubit {qubit_index} has coordinates {coords_float}, "
                f"but at least 2D integer coordinates are required for reordering."
            )
        try:
            # Round floats to integers for the key lookup
            ox = round(coords_float[0])
            oy = round(coords_float[1])
            coord_map[qubit_index] = (ox, oy)
        except (TypeError, ValueError):
            raise ValueError(
                f"Qubit {qubit_index} has non-numeric or unsuitable coordinates "
                f"{coords_float}. Expected numbers convertible to integers."
            )
    return coord_map


def _build_reordering_map(
    circuit: stim.Circuit, qubit_order: Dict[Tuple[int, int], int]
) -> Dict[int, int]:
    """
    Builds a map from old qubit index to new qubit index.

    Parameters
    ----------
    circuit: The circuit to get original qubit coordinates from.
    qubit_order: The desired mapping from coordinates to new indices.

    Returns
    -------
    A dictionary mapping old qubit index (int) to new qubit index (int).
    Raises ValueError if a qubit with coordinates is not found in qubit_order.
    """
    original_coord_map = _get_qubit_coordinate_map(circuit)
    reorder_map: Dict[int, int] = {}
    present_indices = set(range(circuit.num_qubits))  # All indices potentially used

    old_indices_not_given = []
    for old_index, coords in original_coord_map.items():
        if coords not in qubit_order:
            old_indices_not_given.append(old_index)
            continue
            # raise ValueError(
            #     f"Qubit {old_index} with coordinates {coords} is missing "
            #     f"from the provided qubit_order mapping."
            # )
        new_index = qubit_order[coords]
        reorder_map[old_index] = new_index
        present_indices.discard(old_index)  # Remove mapped indices

    # Check if all qubits present in the circuit (even without coords) are handled
    # Option 1: Raise error for unmapped qubits that appear in the circuit
    # This requires checking *all* instructions, which is done during the main reordering.
    # For now, we only raise errors for qubits *with* coordinates that aren't mapped.

    # Option 2: Assign remaining indices sequentially (can lead to conflicts if not careful)
    next_new_idx = max(qubit_order.values() or [-1]) + 1
    for old_idx in old_indices_not_given:  # Process consistently
        reorder_map[old_idx] = next_new_idx
        next_new_idx += 1

    return reorder_map


def _remap_pauli_string(
    pauli_string: stim.PauliString, reorder_map: Dict[int, int], new_num_qubits: int
) -> stim.PauliString:
    """Remaps the qubits within a stim.PauliString."""
    new_pauli_string = stim.PauliString(new_num_qubits)  # Initialize as identity
    new_pauli_string.sign = pauli_string.sign

    for old_index in range(len(pauli_string)):
        pauli = pauli_string[old_index]
        if pauli != 0:  # If not identity
            if old_index not in reorder_map:
                # This Pauli acts on a qubit that wasn't in the reorder map
                # (likely missing coordinates or wasn't in qubit_order)
                raise ValueError(
                    f"PauliString '{pauli_string}' acts on qubit {old_index}, "
                    f"which could not be remapped. Ensure all relevant qubits "
                    f"have coordinates defined in the circuit and are included "
                    f"in the qubit_order map."
                )
            new_index = reorder_map[old_index]
            if new_index >= new_num_qubits:
                raise ValueError(
                    f"Remapping of qubit {old_index} to {new_index} failed: "
                    f"new index exceeds calculated new number of qubits ({new_num_qubits})."
                )
            # Check if assigning conflicting Pauli (shouldn't happen with good map)
            if (
                new_pauli_string[new_index] != 0
                and new_pauli_string[new_index] != pauli
            ):
                raise ValueError(
                    f"Conflict while remapping PauliString '{pauli_string}'. "
                    f"Multiple old indices map to new index {new_index} with different Paulis."
                )
            new_pauli_string[new_index] = pauli
    return new_pauli_string


def _reorder_qubits_in_circuit(
    circuit: stim.Circuit, qubit_order: Dict[Tuple[int, int], int]
) -> stim.Circuit:
    """
    Reorders the qubit indices in a Stim circuit based on a coordinate map.

    Parameters
    ----------
    circuit: The input stim.Circuit.
    qubit_order: A dictionary mapping original qubit coordinates (Tuple[int, int])
                 to the desired new qubit index (int).

    Returns
    -------
    A new stim.Circuit with qubit indices reordered according to qubit_order.
    Instructions like QUBIT_COORDS, gates (CX, H), errors (DEPOLARIZE1),
    and measurements (M, MPP) will have their target qubit indices updated.

    Raises
    ------
    ValueError: If a qubit referenced in the circuit has coordinates defined
                but those coordinates are not present in the qubit_order map,
                or if remapping leads to inconsistencies.
    ValueError: If coordinates needed for mapping are missing or invalid.
    """
    reorder_map = _build_reordering_map(circuit, qubit_order)

    if not reorder_map and circuit.num_qubits > 0:
        print(
            "Warning: No qubits were remapped. Either the circuit has no qubits "
            "with coordinates or the qubit_order map didn't match any coordinates."
        )
        # Decide if we should return original circuit or proceed (might error later)
        # Let's proceed, it might error informatively later if needed.

    # Determine the size needed for the new circuit representation
    new_num_qubits = 0
    if reorder_map:
        new_num_qubits = max(reorder_map.values()) + 1

    # --- Use Flattened Circuit for Simpler Processing ---
    # Flattening expands loops and applies coordinate shifts, simplifying
    # the remapping process as we don't need to track loop context.
    try:
        flattened_circuit = circuit.flattened()
    except Exception as e:
        print(f"Error during circuit flattening: {e}")
        print(
            "Consider simplifying the circuit (e.g., removing complex REPEAT blocks) if issues persist."
        )
        raise e

    new_circuit = stim.Circuit()

    # Keep track of all old indices actually encountered to check for unmapped ones
    encountered_old_indices = set()

    for instruction in flattened_circuit:
        # After flattening, we expect only stim.CircuitInstruction
        if not isinstance(instruction, stim.CircuitInstruction):
            print(
                f"Warning: Skipping non-instruction item found after flattening: {type(instruction)}"
            )
            continue  # Skip repeat blocks or other unexpected types

        name = instruction.name
        targets = instruction.targets_copy()
        gate_args = instruction.gate_args_copy()

        new_targets: List[stim.GateTarget | stim.PauliString] = []
        targets_modified = False  # Flag to check if any target actually changed

        for target in targets:
            new_target = target  # Default to keeping the target the same
            target_is_pauli_string = isinstance(target, stim.PauliString)

            if target_is_pauli_string:
                # Remap PauliString contents
                old_ps = target
                try:
                    new_target = _remap_pauli_string(
                        old_ps, reorder_map, new_num_qubits
                    )
                    if str(new_target) != str(old_ps):  # Check if changed
                        targets_modified = True
                except ValueError as e:
                    raise ValueError(
                        f"Error remapping PauliString target in instruction "
                        f"'{name} {targets}': {e}"
                    ) from e

            elif isinstance(target, stim.GateTarget):
                is_qubit = target.is_qubit_target
                is_pauli = (
                    target.is_x_target or target.is_y_target or target.is_z_target
                )

                if is_qubit or is_pauli:
                    old_index = target.value
                    encountered_old_indices.add(old_index)  # Track usage

                    if old_index not in reorder_map:
                        # Check if this qubit *had* coordinates defined originally
                        # This requires looking back at the original coord map, which
                        # _build_reordering_map already used. If it had coords,
                        # _build_reordering_map would have raised an error.
                        # If it *didn't* have coords, we hit an unmapped qubit.
                        raise ValueError(
                            f"Instruction '{name}' targets qubit {old_index}, which "
                            f"could not be remapped. It might be missing coordinates "
                            f"in the original circuit, or its coordinates were not "
                            f"in the qubit_order map."
                        )

                    new_index = reorder_map[old_index]

                    # Reconstruct the target with the new index, preserving type/flags
                    if (
                        target.is_inverted_result_target
                    ):  # Should not happen for qubit/pauli
                        pass  # Keep original target type if somehow inverted qubit
                    elif target.is_measurement_record_target:  # Should not happen
                        pass
                    elif target.is_sweep_bit_target:  # Should not happen
                        pass
                    elif target.is_combiner:  # Should not happen for simple qubit/pauli
                        pass
                    elif is_pauli:
                        pauli_type = target.pauli_type
                        if pauli_type == "X":
                            new_target = stim.target_x(new_index)
                        elif pauli_type == "Y":
                            new_target = stim.target_y(new_index)
                        elif pauli_type == "Z":
                            new_target = stim.target_z(new_index)
                        else:  # Should not happen
                            raise TypeError(f"Unexpected Pauli type {pauli_type}")
                    else:  # Simple qubit target
                        new_target = stim.GateTarget(new_index)

                    if new_target != target:
                        targets_modified = True

                # else: keep target as is (rec, sweep, etc.)

            # Append the (potentially modified) target
            new_targets.append(new_target)

        # Special handling for QUBIT_COORDS instruction arguments
        new_gate_args = gate_args
        if (
            name == "QUBIT_COORDS"
            and tuple(int(arg) for arg in gate_args) in qubit_order.keys()
        ):
            continue

        # Append the modified instruction to the new circuit
        # Use the generic append method that handles different target types
        new_circuit.append(name, new_targets, new_gate_args)

    # Final check: Did we encounter any old indices that weren't in the map?
    # This check is somewhat redundant if _build_reordering_map is robust,
    # but adds an extra layer of safety.
    unmapped_encountered = encountered_old_indices - set(reorder_map.keys())
    if unmapped_encountered:
        raise ValueError(
            f"The following qubit indices were used in the circuit but could not be "
            f"remapped (likely missing coordinates or missing from qubit_order): "
            f"{sorted(list(unmapped_encountered))}"
        )

    return new_circuit


def remove_redundant_qubit_coords_from_dict(
    circuit: stim.Circuit, reference_coords: Dict[int, Tuple[int, int]]
) -> stim.Circuit:
    """
    Removes QUBIT_COORDS instructions from 'circuit' if the same qubit index
    already has the exact same coordinates defined in the 'reference_coords' dictionary.

    Iterates through the input 'circuit' and builds a new circuit.
    A QUBIT_COORDS instruction from 'circuit' is omitted from the new circuit
    if and only if *all* qubits targeted by that specific instruction have
    identical coordinate definitions present in 'reference_coords'.

    Parameters
    ----------
    circuit : stim.Circuit
        The circuit from which redundant QUBIT_COORDS instructions might be removed.
    reference_coords : Dict[int, Tuple[float, ...]]
        A dictionary mapping qubit indices (int) to their coordinates (tuple of floats).
        These are considered the existing definitions.

    Returns
    -------
    stim.Circuit
        A new circuit, potentially with some QUBIT_COORDS instructions removed.
    """
    new_circuit = stim.Circuit()

    # The input dictionary already serves as the reference map.
    # Ensure coordinates in the reference dict are tuples for comparison.
    # (The type hint already suggests this, but we could add validation if needed)
    ref_coords_map = reference_coords

    # Iterate through the original circuit's instructions and blocks
    for item in circuit:
        is_qubit_coords_instruction = (
            isinstance(item, stim.CircuitInstruction) and item.name == "QUBIT_COORDS"
        )

        if is_qubit_coords_instruction:
            # This is guaranteed to be a CircuitInstruction now
            instr: stim.CircuitInstruction = item
            # Convert coords defined in the instruction to tuple for comparison
            coords_defined_here = tuple(instr.gate_args_copy())
            target_qubits: List[int] = []
            keep_instruction = False  # Default to removing unless proven otherwise

            for target in instr.targets_copy():
                if target.is_qubit_target:
                    target_qubit_idx = target.value
                    target_qubits.append(target_qubit_idx)
                    # Check if this qubit exists in the reference map
                    ref_coords_tuple = ref_coords_map.get(target_qubit_idx)
                    # Keep the instruction if:
                    # 1. The qubit isn't defined in the reference dictionary OR
                    # 2. The coordinates in the reference are DIFFERENT
                    if (
                        ref_coords_tuple is None
                        or ref_coords_tuple != coords_defined_here
                    ):
                        keep_instruction = True
                        # No need to check other targets of this instruction,
                        # since at least one part is not redundant.
                        break
                else:
                    # QUBIT_COORDS should only target qubits. If not, keep it safe.
                    print(
                        f"Warning: Found non-qubit target {target} in QUBIT_COORDS instruction: {instr}. Keeping instruction."
                    )
                    keep_instruction = True
                    break

            # If after checking all targets, none forced us to keep it, it means
            # all targets were redundant (or the target list was empty).
            if keep_instruction:
                new_circuit.append(instr)
            # else: instruction is fully redundant, so we don't append it.

        else:
            # If it's not a QUBIT_COORDS instruction, keep it as is.
            new_circuit.append(item)

    return new_circuit


def _parse_mpp_gate_targets(
    mpp_targets: List[stim.GateTarget], num_measurements: int
) -> List[Tuple[Literal["X", "Y", "Z"], FrozenSet[int]]]:
    """
    Parses the flat list of GateTargets from an MPP instruction into
    a list of measurement bases.

    Parameters
    ----------
    mpp_targets : List[stim.GateTarget]
        The list of targets from MPP.targets_copy().
    num_measurements : int
        The number of measurements produced by this MPP instruction.

    Returns
    -------
    List[Tuple[Literal['X', 'Y', 'Z'], FrozenSet[int]]]
        A list where each tuple represents one measurement basis:
        (Pauli type character, frozenset of qubit indices).
        The list order corresponds to the measurement result order.

    Raises
    ------
    ValueError
        If the target list structure is inconsistent with num_measurements
        or contains mixed Pauli types within a single basis.
    """
    parsed_bases: List[Tuple[Literal["X", "Y", "Z"], FrozenSet[int]]] = []
    if not mpp_targets and num_measurements > 0:
        raise ValueError("MPP instruction expected targets but list is empty.")
    if num_measurements == 0:
        return []

    current_qubit_set: set[int] = set()
    # Store the integer type (1, 2, or 3) while building the basis
    current_basis_pauli_char: Optional[str] = None

    for idx_target, target in enumerate(mpp_targets):
        if target.is_combiner:
            if not current_qubit_set:
                raise ValueError(
                    "MPP combiner '*' found before any Pauli target in a basis."
                )
            continue  # Combiner confirms continuation, move to next target

        # We expect a Pauli target now
        is_pauli = target.is_x_target or target.is_y_target or target.is_z_target
        if not is_pauli:
            raise ValueError(
                f"Expected Pauli target or combiner in MPP, but got {target}"
            )

        pauli_char = target.pauli_type
        qubit_index = target.value

        if current_basis_pauli_char is None:
            # --- Start the very first basis ---
            current_basis_pauli_char = pauli_char
            current_qubit_set = {qubit_index}
        elif pauli_char == current_basis_pauli_char:
            # --- Continue the current basis ---
            # Check if the previous target was NOT a combiner - this implies a new measurement basis
            # even if the Pauli type is the same (e.g., MPP X1 X2).
            # Find the previous non-combiner target if it exists.
            previous_non_combiner_idx = -1
            for k in range(idx_target - 1, -1, -1):
                if not mpp_targets[k].is_combiner:
                    previous_non_combiner_idx = k
                    break

            if (
                previous_non_combiner_idx == -1
            ):  # Should not happen if current_basis_pauli_type_val is not None
                pass  # Continue current basis

            # If the immediate previous target wasn't a combiner, it's a new basis
            elif idx_target > 0 and not mpp_targets[idx_target - 1].is_combiner:
                # --- Finalize previous basis (same-type new measurement) ---
                parsed_bases.append(
                    (current_basis_pauli_char, frozenset(current_qubit_set))
                )

                # --- Start the new basis (same type as previous, but distinct measurement) ---
                current_basis_pauli_char = pauli_char
                current_qubit_set = {qubit_index}
            else:
                # --- Truly continue the current basis (combiner was likely involved) ---
                current_qubit_set.add(qubit_index)

        else:  # pauli_val != current_basis_pauli_type_val
            # --- New Pauli type means finalize previous and start new basis ---
            parsed_bases.append(
                (current_basis_pauli_char, frozenset(current_qubit_set))
            )

            # --- Start the new basis ---
            current_basis_pauli_char = pauli_char
            current_qubit_set = {qubit_index}

    # Add the very last collected basis after the loop finishes
    if current_basis_pauli_char is not None:
        parsed_bases.append((current_basis_pauli_char, frozenset(current_qubit_set)))

    # Validate the number of bases found
    if len(parsed_bases) != num_measurements:
        raise ValueError(
            f"Parsing MPP targets yielded {len(parsed_bases)} measurement bases, "
            f"but the instruction reported producing {num_measurements} measurements. "
            f"Parsed: {parsed_bases}"
        )

    return parsed_bases


def _isolate_final_mpps(
    circuit: stim.Circuit,
) -> Tuple[stim.Circuit, Dict[Tuple[Literal["X", "Z"], FrozenSet[int]], List[int]]]:
    """
    Isolates the final block (TICK, MPP, OBSERVABLE_INCLUDE, DETECTORs)
    from a circuit and analyzes the detector measurement dependencies.
    Handles MPP targets specified as GateTargets with combiners.

    Parameters
    ----------
    circuit : stim.Circuit
        The input circuit, guaranteed to end with the structure:
        TICK
        MPP {targets...}
        OBSERVABLE_INCLUDE(0) {targets...}
        DETECTOR {targets...}
        ... (more DETECTORs)

    Returns
    -------
    trimmed_circuit : stim.Circuit
        The circuit containing only the instructions *before* the final TICK.
    final_detectors_info : Dict[Tuple[Literal['X', 'Z'], FrozenSet[int]], List[int]]
        Each item indicates the information of a detector after the final TICK.
        Its key corresponds to the target of the detector after the final TICK (which is unique),
        represented as (Pauli type character, frozenset of qubit indices).
        Its value is a list of measurement target indices (`rec[-k]`) that correspond to other measurements in the detector before the final TICK.
    """
    if len(circuit) == 0:
        return stim.Circuit(), {}

    # --- Identify the block boundaries by working backwards ---
    tick_index: Optional[int] = None
    mpp_instruction: Optional[stim.CircuitInstruction] = None
    observable_instruction: Optional[stim.CircuitInstruction] = None
    detector_instructions: List[stim.CircuitInstruction] = []
    num_instructions = len(circuit)

    # Expected instruction sequence from the end (reverse order)
    expected_sequence = ["DETECTOR", "OBSERVABLE_INCLUDE", "MPP", "TICK"]
    expected_idx = 0
    current_block_instructions: List[stim.CircuitInstruction] = []  # For debugging

    # Similar reverse iteration logic as before...
    for i in range(num_instructions - 1, -1, -1):
        instr = circuit[i]
        if not isinstance(instr, stim.CircuitInstruction):
            raise TypeError(
                f"Expected stim.CircuitInstruction at index {i}, but got {type(instr)}"
            )

        current_block_instructions.append(instr)
        instr_name = instr.name

        if expected_idx < len(expected_sequence):
            expected_name = expected_sequence[expected_idx]
            if expected_name == "DETECTOR":
                if instr_name == "DETECTOR":
                    detector_instructions.append(instr)
                    continue
                else:
                    expected_idx += 1
                    # Fall through

            if expected_idx < len(expected_sequence):  # Re-check bounds
                expected_name = expected_sequence[expected_idx]
                if instr_name == expected_name:
                    if instr_name == "OBSERVABLE_INCLUDE":
                        args = instr.gate_args_copy()
                        if not args or args[0] != 0:
                            raise ValueError(
                                f"Expected OBSERVABLE_INCLUDE(0) at index {i}, but found {instr}"
                            )
                        observable_instruction = instr
                    elif instr_name == "MPP":
                        mpp_instruction = instr
                    elif instr_name == "TICK":
                        tick_index = i
                        break  # Found start of block
                    expected_idx += 1
                else:
                    raise ValueError(
                        f"Unexpected instruction sequence. Expected '{expected_name}', found '{instr_name}' at index {i}."
                    )
        else:
            raise ValueError(
                "Circuit structure guarantee violated. Reached beginning without finding TICK."
            )

    detector_instructions.reverse()
    current_block_instructions.reverse()

    # --- Validate findings ---
    if tick_index is None:
        raise ValueError("Could not find the final TICK instruction.")
    if mpp_instruction is None:
        raise ValueError("Could not find the final MPP instruction.")
    if observable_instruction is None:
        raise ValueError("Could not find the final OBSERVABLE_INCLUDE(0) instruction.")

    # --- Create the trimmed circuit ---
    trimmed_circuit = circuit[0:tick_index]

    # --- Calculate measurement indices ---
    num_measurements_before_tick = trimmed_circuit.num_measurements
    num_total_measurements_original = circuit.num_measurements

    # Get number of measurements directly from the MPP instruction property
    num_mpp_measurements = mpp_instruction.num_measurements

    # Validate measurement count consistency (optional but good check)
    expected_min_total = num_measurements_before_tick + num_mpp_measurements
    if num_total_measurements_original < expected_min_total:
        print(
            f"Warning: Original circuit has {num_total_measurements_original} measurements, "
            f"but expected at least {expected_min_total} based on MPP instruction. "
            f"Proceeding, but check circuit structure if errors occur."
        )
        # Adjust total based on expectation if inconsistent? Safer to use original total.

    # --- Parse MPP targets ---
    mpp_targets_list = mpp_instruction.targets_copy()
    try:
        # Parse the flat list into structured measurement bases
        parsed_mpp_measurement_bases = _parse_mpp_gate_targets(
            mpp_targets_list, num_mpp_measurements
        )
    except ValueError as e:
        raise ValueError(
            f"Error parsing MPP instruction targets: {mpp_instruction}. Details: {e}"
        ) from e

    # --- Process detectors ---
    final_detectors_info: List[List[Union[int, Tuple[str, FrozenSet[int]]]]] = []

    for det_instr in detector_instructions:
        current_detector_info: List[Union[int, Tuple[str, FrozenSet[int]]]] = []
        det_targets = det_instr.targets_copy()

        for target in det_targets:
            if not target.is_measurement_record_target:
                raise ValueError(f"Unexpected target type in DETECTOR: {target}")

            lookback_k = target.value  # is negative

            # Calculate absolute index from the *start* of the original circuit
            abs_measurement_index = num_total_measurements_original + lookback_k

            if abs_measurement_index < 0:
                raise ValueError(
                    f"Lookback {lookback_k} is too large for the circuit's "
                    f"{num_total_measurements_original} measurements."
                )

            # Check if the measurement occurred before the final TICK
            if abs_measurement_index < num_measurements_before_tick:
                target_info = lookback_k + num_mpp_measurements
            # Check if the measurement occurred within the MPP block
            elif (
                abs_measurement_index
                < num_measurements_before_tick + num_mpp_measurements
            ):
                # Index relative to the start of the MPP measurements (0-based)
                mpp_measurement_rel_index = (
                    abs_measurement_index - num_measurements_before_tick
                )

                if mpp_measurement_rel_index >= len(parsed_mpp_measurement_bases):
                    raise IndexError(
                        f"Calculated MPP relative index {mpp_measurement_rel_index} "
                        f"out of bounds for {len(parsed_mpp_measurement_bases)} parsed MPP bases."
                    )

                # Get the corresponding parsed basis info tuple
                target_info = parsed_mpp_measurement_bases[mpp_measurement_rel_index]
            else:
                raise ValueError(
                    f"Measurement lookback {lookback_k} points to index "
                    f"{abs_measurement_index}, which is after the final MPP block "
                    f"(ending at index {num_measurements_before_tick + num_mpp_measurements - 1}). "
                    f"Circuit structure guarantee violated."
                )

            current_detector_info.append(target_info)

        final_detectors_info.append(current_detector_info)

    # Reformat final_detectors_info to dictionary
    final_detectors_info_dict = {}
    for det_info in final_detectors_info:
        values = []
        key = None
        for target_info in det_info:
            if isinstance(target_info, tuple):
                key = target_info
            else:
                values.append(target_info)
        assert key is not None and key not in final_detectors_info_dict
        final_detectors_info_dict[key] = values

    final_detectors_info = final_detectors_info_dict

    return trimmed_circuit, final_detectors_info
