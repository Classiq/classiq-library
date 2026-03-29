import itertools
from collections import defaultdict
from typing import Dict, FrozenSet, List, Literal, Optional, Self, Sequence, Set, Tuple

import numpy as np
import stim
from scipy.sparse import csr_matrix


class _ErrorMechanismSymbolic:
    """Represents a single error mechanism with symbolic probability."""

    prob_vars: np.ndarray
    prob_muls: np.ndarray
    dets: Set[stim.DemTarget]
    obss: Set[stim.DemTarget]

    def __init__(
        self,
        prob_vars: Optional[Sequence[int]] = None,
        dets: Optional[Sequence[stim.DemTarget]] = None,
        obss: Optional[Sequence[stim.DemTarget]] = None,
        prob_muls: Sequence[float] | int | float = 1,
    ):
        if prob_vars is None:
            prob_vars = np.array([], dtype="int32")
            prob_muls = np.array([], dtype="int32")
        else:
            prob_vars = np.asarray(prob_vars, dtype="int32")
            prob_muls = np.asarray(prob_muls)

        if prob_muls.ndim == 0:
            prob_muls = np.full_like(prob_vars, prob_muls)

        self.prob_vars = prob_vars
        self.prob_muls = prob_muls

        if dets is None:
            dets = []
        if obss is None:
            obss = []

        self.dets = set(dets)
        self.obss = set(obss)

    def __repr__(self) -> str:
        """Return a concise string representation of this error mechanism."""

        return (
            "_ErrorMechanismSymbolic("
            f"dets={{{ {', '.join(str(det) for det in self.dets)} }}}, "
            f"obss={{{ {', '.join(str(obs) for obs in self.obss)} }}}, "
            f"prob_vars={self.prob_vars}, prob_muls={self.prob_muls})"
        )


class _DemSymbolic:
    """Symbolic representation of a Detector Error Model."""

    _ems: List[_ErrorMechanismSymbolic]
    dets_org: stim.DetectorErrorModel
    error_map_matrix: csr_matrix
    num_org_errors: int

    def __init__(
        self,
        prob_vars: Sequence[Sequence[int]],
        dets: Sequence[Sequence[stim.DemTarget]],
        obss: Sequence[Sequence[stim.DemTarget]],
        dets_org: stim.DetectorErrorModel,
        num_org_errors: int,
    ):
        self._ems = [
            _ErrorMechanismSymbolic(*prms) for prms in zip(prob_vars, dets, obss)
        ]
        self.dets_org = dets_org
        self.num_org_errors = num_org_errors

        self.update_error_map_matrix()

    def __iter__(self) -> "Iterator[_ErrorMechanismSymbolic]":
        """Return an iterator over the error mechanisms."""

        return iter(self._ems)

    def __len__(self) -> int:
        """Return the number of error mechanisms."""

        return len(self._ems)

    def __getitem__(
        self, key: int | slice
    ) -> _ErrorMechanismSymbolic | List[_ErrorMechanismSymbolic]:
        """Access error mechanisms by index or slice."""

        return self._ems[key]

    @classmethod
    def FromEms(
        cls,
        ems: List[_ErrorMechanismSymbolic],
        dets_org: stim.DetectorErrorModel,
        num_org_errors: Optional[int] = None,
    ):
        new_dem = cls.__new__(cls)
        new_dem._ems = ems
        new_dem.dets_org = dets_org
        new_dem.error_map_matrix = csr_matrix((0, 0), dtype=bool)  # Placeholder
        if num_org_errors is None:
            num_org_errors = max(em.prob_vars.max() for em in ems) + 1
        new_dem.num_org_errors = num_org_errors

        new_dem.update_error_map_matrix()
        return new_dem

    def update_error_map_matrix(self) -> None:
        """
        Recalculate ``error_map_matrix`` from the current error mechanisms.

        The matrix maps indices of decomposed errors to indices of the original
        error mechanisms.
        """
        num_errors = len(self._ems)
        if num_errors == 0:
            self.error_map_matrix = csr_matrix((0, 0), dtype=bool)
            return

        map_data: List[bool] = []
        map_row_indices: List[int] = []  # Error index (row)
        map_col_indices: List[int] = []  # Variable index (column)

        for error_idx, em in enumerate(self._ems):
            if em.prob_vars.size > 0:
                # Add entries to CSR data lists
                for var_idx in em.prob_vars:
                    map_data.append(True)
                    map_row_indices.append(error_idx)
                    map_col_indices.append(var_idx)

        # Create the new CSR matrix
        new_error_map_matrix = csr_matrix(
            (map_data, (map_row_indices, map_col_indices)),
            shape=(num_errors, self.num_org_errors),
            dtype=bool,
        )

        # Update the instance attribute
        self.error_map_matrix = new_error_map_matrix

    def inds_probs_sorted(self, prob_vals: Sequence[float]) -> np.ndarray:
        probs = [
            (1 - np.prod(1 - 2 * em.prob_muls * prob_vals[em.prob_vars])) / 2
            for em in self._ems
        ]
        return np.argsort(probs, kind="stable")[::-1]

    def to_dem(
        self, prob_vals: Sequence[float], sort: bool = False
    ) -> Tuple[stim.DetectorErrorModel, np.ndarray]:
        prob_vals = np.asarray(prob_vals, dtype="float64")

        probs = [
            (1 - np.prod(1 - 2 * em.prob_muls * prob_vals[em.prob_vars])) / 2
            for em in self._ems
        ]

        if sort:
            inds = np.argsort(probs, kind="stable")[::-1]
        else:
            inds = np.arange(len(probs))

        dem = stim.DetectorErrorModel()
        for i in inds:
            em = self._ems[i]
            targets = em.dets | em.obss
            try:
                dem.append("error", probs[i], list(targets))
            except ValueError:
                print(probs[i], list(targets))
                raise ValueError(f"Error appending error mechanism {em} to DEM.")

        dem += self.dets_org

        return dem, inds

    def non_edge_like_errors_exist(self) -> bool:
        for e in self._ems:
            if len(e.dets) > 2:
                return True
        return False

    def decompose_complex_error_mechanisms(self):
        """
        For each error mechanism `e` in `dem` that involves more than two detectors,
        searches for candidate pairs (e1, e2) among the other error mechanisms (with e1, e2 disjoint)
        such that:
        - e1.dets ∪ e2.dets equals e.dets, and e1.dets ∩ e2.dets is empty.
        - e1.obss ∪ e2.obss equals e.obss, and e1.obss ∩ e2.obss is empty.

        For each valid candidate pair, updates both e1 and e2 by concatenating e's
        probability variable and multiplier arrays. If there are multiple candidate pairs,
        the probability multipliers from e are split equally among the pairs.

        Finally, removes the complex error mechanism `e` from `dem.ems`.

        Raises:
            ValueError: If a complex error mechanism cannot be decomposed.
        """
        # Iterate over a copy of the error mechanisms list
        em_inds_to_remove = []
        for i_e, e in enumerate(self._ems):
            # Process only error mechanisms that involve more than 2 detectors.
            if len(e.dets) > 2:
                candidate_pairs = []
                # Search for candidate pairs among the other error mechanisms.
                for i, e1 in enumerate(self._ems):
                    if i == i_e or i in em_inds_to_remove:
                        continue
                    for j in range(i + 1, len(self._ems)):
                        if j == i_e or j in em_inds_to_remove:
                            continue
                        e2 = self._ems[j]
                        # Check that e1 and e2 have disjoint detectors and observables.
                        if e1.dets & e2.dets:
                            continue
                        if e1.obss & e2.obss:
                            continue
                        # Check that the union of their detectors and observables equals e's.
                        if (e1.dets | e2.dets == e.dets) and (
                            e1.obss | e2.obss == e.obss
                        ):
                            candidate_pairs.append((e1, e2))
                if not candidate_pairs:
                    raise ValueError(
                        f"No valid decomposition found for error mechanism with dets {e.dets} and obss {e.obss}."
                    )
                # If there are multiple decompositions, split the probability equally.
                fraction = 1 / len(candidate_pairs)
                for e1, e2 in candidate_pairs:
                    # Append the probability variable arrays.
                    e1.prob_vars = np.concatenate([e1.prob_vars, e.prob_vars])
                    e2.prob_vars = np.concatenate([e2.prob_vars, e.prob_vars])
                    # Append the probability multiplier arrays, scaling by the fraction.
                    e1.prob_muls = np.concatenate(
                        [e1.prob_muls, e.prob_muls * fraction]
                    )
                    e2.prob_muls = np.concatenate(
                        [e2.prob_muls, e.prob_muls * fraction]
                    )
                # Remove the complex error mechanism from the model.
                em_inds_to_remove.append(i_e)

            for i_e in em_inds_to_remove[::-1]:
                self._ems.pop(i_e)

    def decompose_paulis(
        self,
        det_paulis: List[Literal["X", "Y", "Z"]],
        obs_paulis: List[Literal["X", "Y", "Z"]],
    ) -> Self:
        """
        Decomposes error mechanisms containing both X and Z type detectors.

        Splits EMs with mixed X/Z detectors into two EMs (one X, one Z),
        distributing detectors and observables appropriately. Handles Y-type
        observables by ensuring the resulting decomposed EMs match existing
        EM structures in the original DEM (ignoring probability).

        Parameters
        ----------
        det_paulis : List[Literal['X', 'Y', 'Z']]
            List mapping detector ID to its Pauli type ('X', 'Y', or 'Z').
        obs_paulis : List[Literal['X', 'Y', 'Z']]
            List mapping observable ID to its Pauli type ('X', 'Y', or 'Z').

        Returns
        -------
        decomposed_dem : _DemSymbolic
            A new _DemSymbolic object with mixed X/Z EMs decomposed.

        Raises
        ------
        ValueError
            If an EM contains X, Y, and Z detectors simultaneously.
            If an EM contains X and Z detectors and also Y observables.
            If a suitable decomposition for Y observables cannot be found
            matching existing EM structures.
            If detector or observable IDs are out of bounds for the pauli lists.
        """
        new_ems: List[_ErrorMechanismSymbolic] = []
        original_ems_set_repr = {  # For efficient lookup based on dets/obss sets
            (frozenset(str(d) for d in em.dets), frozenset(str(o) for o in em.obss))
            for em in self._ems
        }

        # Identify all globally available Y-type observables
        global_y_observables: Set[stim.DemTarget] = set()
        for obs_id, pauli_type in enumerate(obs_paulis):
            if pauli_type == "Y":
                global_y_observables.add(stim.target_logical_observable_id(obs_id))

        has_global_y_observables = bool(global_y_observables)

        def _get_target_id(target: stim.DemTarget) -> int:
            """Helper to extract ID, assuming D<id> or L<id> format."""
            try:
                # Extract numeric part after the first character (D or L)
                return int(str(target)[1:])
            except (IndexError, ValueError):
                raise ValueError(f"Could not parse ID from DemTarget: {target}")

        def _em_repr_exists(
            dets_repr: FrozenSet[str], obss_repr: FrozenSet[str]
        ) -> bool:
            """Checks if an EM with these det/obs string representations exists."""
            return (dets_repr, obss_repr) in original_ems_set_repr

        for em_idx, em in enumerate(self._ems):  # Use index for error messages
            detector_types: Set[Literal["X", "Y", "Z"]] = set()
            em_y_observables: Set[stim.DemTarget] = set()  # Y obs specific to this EM

            # --- Classify detectors and check EM's Y observables ---
            for det_target in em.dets:
                det_id = _get_target_id(det_target)
                if det_id >= len(det_paulis):
                    raise ValueError(
                        f"Detector ID {det_id} from EM {em_idx} is out of bounds for det_paulis (length {len(det_paulis)})."
                    )
                print(det_id, det_paulis[det_id])
                detector_types.add(det_paulis[det_id])

            for obs_target in em.obss:
                obs_id = _get_target_id(obs_target)
                if obs_id >= len(obs_paulis):
                    raise ValueError(
                        f"Observable ID {obs_id} from EM {em_idx} is out of bounds for obs_paulis (length {len(obs_paulis)})."
                    )
                pauli_type = obs_paulis[obs_id]
                if pauli_type == "Y":
                    em_y_observables.add(obs_target)  # Track Y obs in *this* EM

            # --- Check assumptions ---
            if len(detector_types) == 3:
                raise ValueError(
                    f"EM {em_idx} contains X, Y, and Z detectors simultaneously: {em}"
                )
            needs_decomposition = "X" in detector_types and "Z" in detector_types

            # This check is based on the guarantee provided in the prompt
            if needs_decomposition and em_y_observables:
                raise ValueError(
                    f"EM {em_idx} needs decomposition (has X/Z dets) but also contains Y observables {em_y_observables}, violating guarantee."
                )

            # --- Perform decomposition or keep original ---
            if needs_decomposition:
                em_x = _ErrorMechanismSymbolic()
                em_z = _ErrorMechanismSymbolic()

                # Copy probability info
                em_x.prob_vars = em.prob_vars
                em_x.prob_muls = em.prob_muls
                em_z.prob_vars = em.prob_vars
                em_z.prob_muls = em.prob_muls

                # Distribute detectors
                for det_target in em.dets:
                    det_id = _get_target_id(det_target)
                    pauli_type = det_paulis[det_id]
                    if pauli_type == "X":
                        em_x.dets.add(det_target)
                    elif pauli_type == "Z":
                        em_z.dets.add(det_target)
                    elif pauli_type == "Y":  # Y detectors go to both
                        em_x.dets.add(det_target)
                        em_z.dets.add(det_target)

                # Distribute X/Z observables (Y observables in em.obss are guaranteed empty here)
                for obs_target in em.obss:
                    obs_id = _get_target_id(obs_target)
                    pauli_type = obs_paulis[obs_id]
                    if pauli_type == "X":
                        em_x.obss.add(obs_target)
                    elif pauli_type == "Z":
                        em_z.obss.add(obs_target)
                    # No 'Y' case needed due to guarantee

                # --- Handle Global Y Observables ---
                # If there are global Y observables, we need to find a subset
                # to add to *both* em_x and em_z such that the resulting
                # (dets, obss) structures exist in the original DEM.
                if has_global_y_observables:
                    found_combination = False
                    y_obs_list = sorted(
                        list(global_y_observables), key=str
                    )  # Consistent order

                    # Check the case with NO added Y observables first
                    temp_em_x_dets_repr = frozenset(str(d) for d in em_x.dets)
                    temp_em_x_obss_repr = frozenset(
                        str(o) for o in em_x.obss
                    )  # No Y added yet
                    temp_em_z_dets_repr = frozenset(str(d) for d in em_z.dets)
                    temp_em_z_obss_repr = frozenset(
                        str(o) for o in em_z.obss
                    )  # No Y added yet

                    if _em_repr_exists(
                        temp_em_x_dets_repr, temp_em_x_obss_repr
                    ) and _em_repr_exists(temp_em_z_dets_repr, temp_em_z_obss_repr):
                        found_combination = True
                        # No Y observables need to be added

                    # If not found, iterate through non-empty subsets of global Y observables
                    if not found_combination:
                        for k in range(1, len(y_obs_list) + 1):
                            for y_subset_targets in itertools.combinations(
                                y_obs_list, k
                            ):
                                y_subset = set(y_subset_targets)
                                # Check if adding this subset makes both em_x and em_z match existing structures
                                current_em_x_obss_repr = frozenset(
                                    str(o) for o in em_x.obss.union(y_subset)
                                )
                                current_em_z_obss_repr = frozenset(
                                    str(o) for o in em_z.obss.union(y_subset)
                                )

                                if _em_repr_exists(
                                    temp_em_x_dets_repr, current_em_x_obss_repr
                                ) and _em_repr_exists(
                                    temp_em_z_dets_repr, current_em_z_obss_repr
                                ):
                                    # Found a valid combination, update the actual em_x, em_z
                                    em_x.obss.update(y_subset)
                                    em_z.obss.update(y_subset)
                                    found_combination = True
                                    break  # Stop checking subsets for this k
                            if found_combination:
                                break  # Stop checking larger subsets

                    if not found_combination:
                        raise ValueError(
                            f"Could not find a valid decomposition for EM {em_idx} involving global Y observables "
                            f"that matches existing EM structures in the original DEM. "
                            f"Base X-part: (dets={em_x.dets}, obss={em_x.obss}), "
                            f"Base Z-part: (dets={em_z.dets}, obss={em_z.obss}). "
                            f"Global Y obs: {global_y_observables}"
                        )

                # Append the (potentially Y-augmented) decomposed EMs
                new_ems.append(em_x)
                new_ems.append(em_z)
            else:
                # No decomposition needed, keep the original EM
                new_ems.append(em)

        # --- Create the new _DemSymbolic object ---
        new_dem = _DemSymbolic.__new__(_DemSymbolic)
        new_dem._ems = new_ems
        new_dem.dets_org = self.dets_org.copy()
        new_dem.error_map_matrix = csr_matrix((0, 0), dtype=bool)  # Placeholder
        new_dem.num_org_errors = self.num_org_errors

        new_dem.update_error_map_matrix()
        return new_dem

    @classmethod
    def FromDem(cls, dem: stim.DetectorErrorModel) -> Self:
        """
        Converts a standard stim.DetectorErrorModel into a _DemSymbolic object.

        Each 'error' instruction in the input DEM corresponds to a unique
        probability variable p_k in the symbolic representation, where k is the
        0-based index of the error instruction in the flattened DEM.
        The resulting error_mapping_arr is an identity matrix.

        Parameters
        ----------
        dem : stim.DetectorErrorModel
            The input detector error model.

        Returns
        -------
        _DemSymbolic
            The symbolic representation of the input DEM.
        """
        try:
            flattened_dem = dem.flattened()
        except Exception as e:
            print(f"Error during DEM flattening: {e}")
            raise e

        symbolic_ems: List[_ErrorMechanismSymbolic] = []
        metadata_instructions: List[str] = []  # Store non-error instructions as strings

        # Data for the identity mapping matrix (CSR format)
        map_data: List[bool] = []
        map_row_indices: List[int] = []
        map_col_indices: List[int] = []

        error_counter = 0  # 0-based index for error mechanisms and plist variables

        for instruction in flattened_dem:
            # Process only DemInstruction objects after flattening
            if not isinstance(instruction, stim.DemInstruction):
                print(
                    f"Warning: Skipping non-DemInstruction item found after flattening: {type(instruction)}"
                )
                # If it's somehow a repeat block, we might want its string representation
                try:
                    metadata_instructions.append(str(instruction))
                except:
                    print(f"Could not convert {instruction} to string.")
                continue

            if instruction.type == "error":
                # Create the symbolic error mechanism
                sym_em = _ErrorMechanismSymbolic()

                # Probability: Corresponds to the k-th variable (pk) with multiplier 1
                sym_em.prob_vars = np.array([error_counter], dtype=np.int32)
                sym_em.prob_muls = np.array([1], dtype=np.int32)

                # Extract detector and observable targets
                for target in instruction.targets_copy():
                    if target.is_relative_detector_id():
                        sym_em.dets.add(target)
                    elif target.is_logical_observable_id():
                        sym_em.obss.add(target)
                    # Ignore separator targets if present

                symbolic_ems.append(sym_em)

                # Add entry for the identity mapping matrix
                map_data.append(True)
                map_row_indices.append(error_counter)  # Row = error index
                map_col_indices.append(error_counter)  # Col = variable index

                error_counter += 1
            else:
                # Keep non-error instructions (detector, logical_observable, etc.)
                # for the dets_org part. Store as string.
                metadata_instructions.append(str(instruction))

        # --- Construct the final objects ---

        # Create dets_org from metadata instructions
        dets_org_stim = stim.DetectorErrorModel("\n".join(metadata_instructions))

        # Create the identity error_mapping_arr
        num_errors = dem.num_errors
        assert num_errors == error_counter
        # Shape is (# errors, # variables). In this case, # variables = # errors.
        error_map_matrix = csr_matrix(
            (map_data, (map_row_indices, map_col_indices)),
            shape=(num_errors, num_errors),
            dtype=bool,
        )

        # Instantiate and return the _DemSymbolic object
        dem_symbolic = cls.__new__(cls)
        dem_symbolic._ems = symbolic_ems
        dem_symbolic.dets_org = dets_org_stim
        dem_symbolic.error_map_matrix = error_map_matrix
        dem_symbolic.num_org_errors = num_errors

        return dem_symbolic

    def compress(self) -> None:
        """
        Compresses the error mechanisms (EMs) by merging those with identical
        detector and observable sets.

        Identifies groups of EMs sharing the same `dets` and `obss` sets.
        Merges each group into a single EM, combining their symbolic probability
        representations. Specifically, it concatenates the `prob_vars` and
        `prob_muls` arrays and then consolidates terms for the same variable
        index by summing their multipliers.

        Modifies `self.ems` and updates `self.error_map_matrix` in place.
        """
        if not self._ems:
            return  # Nothing to compress

        # Group EMs by their (dets, obss) sets
        # Use frozensets of string representations as dictionary keys
        grouped_ems: Dict[
            Tuple[FrozenSet[str], FrozenSet[str]], List[_ErrorMechanismSymbolic]
        ] = defaultdict(list)

        for em in self._ems:
            dets_key = frozenset(str(d) for d in em.dets)
            obss_key = frozenset(str(o) for o in em.obss)
            group_key = (dets_key, obss_key)
            grouped_ems[group_key].append(em)

        compressed_ems: List[_ErrorMechanismSymbolic] = []

        for group_key, em_group in grouped_ems.items():
            if len(em_group) == 1:
                # No merging needed for single-EM groups
                compressed_ems.append(em_group[0])
            else:
                # Merge multiple EMs in the group
                merged_em = _ErrorMechanismSymbolic()
                # Set dets and obss from the first EM (they are all the same)
                merged_em.dets = em_group[0].dets
                merged_em.obss = em_group[0].obss

                # Concatenate all probability variables and multipliers
                all_vars_list = [
                    em.prob_vars for em in em_group if em.prob_vars.size > 0
                ]
                all_muls_list = [
                    em.prob_muls for em in em_group if em.prob_muls.size > 0
                ]  # Ensure prob_vars/muls match

                if (
                    not all_vars_list
                ):  # Handle case where all EMs in group had empty probs
                    merged_em.prob_vars = np.array([], dtype=np.int32)
                    merged_em.prob_muls = np.array([], dtype=float)
                else:
                    all_vars = np.concatenate(all_vars_list)
                    all_muls = np.concatenate(all_muls_list)

                    # Consolidate terms: sum multipliers for the same variable index
                    consolidated_muls: Dict[int, float] = defaultdict(float)
                    for var_idx, mul_val in zip(all_vars, all_muls):
                        consolidated_muls[var_idx] += mul_val

                    # Create final arrays from consolidated data
                    # Sort by variable index for consistent representation
                    sorted_vars = sorted(consolidated_muls.keys())
                    merged_em.prob_vars = np.array(sorted_vars, dtype=np.int32)
                    merged_em.prob_muls = np.array(
                        [consolidated_muls[v] for v in sorted_vars], dtype=float
                    )

                compressed_ems.append(merged_em)

        # Update the list of error mechanisms
        self._ems = compressed_ems

        # Update the mapping matrix to reflect the new EMs
        self.update_error_map_matrix()
