import itertools
from pathlib import Path
import pickle
import time
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import igraph as ig
import matplotlib.pyplot as plt
import numpy as np
import pymatching
import stim
from scipy.sparse import csc_matrix, csr_matrix
from statsmodels.stats.proportion import proportion_confint

from .cultivation import _load_cultivation_circuit, _reformat_cultivation_circuit
from .dem_decomp import DemDecomp
from .stim_utils import (
    dem_to_parity_check,
    remove_obs_from_dem,
    separate_depolarizing_errors,
)
from .utils import _get_final_predictions, get_pfail, get_project_folder, timeit
from .visualization import draw_lattice, draw_tanner_graph

PAULI_LABEL = Literal["X", "Y", "Z"]
COLOR_LABEL = Literal["r", "g", "b"]


class ColorCode:
    tanner_graph: ig.Graph
    circuit: stim.Circuit
    d: int
    d2: Optional[int]
    rounds: int
    circuit_type: str
    temp_bdry_type: Literal["X", "Y", "Z", "r", "g", "b"]
    cnot_schedule: List[int]
    num_obs: int
    qubit_groups: Dict[str, ig.VertexSeq]
    obs_paulis: List[PAULI_LABEL]
    dem_xz: stim.DetectorErrorModel
    H: csc_matrix
    probs_xz: np.ndarray
    obs_matrix: csc_matrix
    detector_ids_by_color: Dict[COLOR_LABEL, List[int]]
    detectors_checks_map: List[Tuple[ig.Vertex, int]]
    cult_detector_ids: List[int]
    interface_detector_ids: List[int]
    dems_decomposed: Dict[COLOR_LABEL, DemDecomp]
    perfect_init_final: bool
    physical_probs: Dict[
        Literal["bitflip", "reset", "meas", "cnot", "idle", "cult"], float
    ]
    comparative_decoding: bool
    exclude_non_essential_pauli_detectors: bool
    cultivation_circuit: Optional[stim.Circuit]
    remove_non_edge_like_errors: bool
    _benchmarking: bool
    _bp_inputs: Dict[str, Any]
    _per_stabilizer_cnot: bool

    def __init__(
        self,
        *,
        d: int,
        rounds: int,
        circuit_type: str = "tri",
        d2: int = None,
        cnot_schedule: Union[str, List[int], List[List[int]], dict],
        temp_bdry_type: Optional[Literal["X", "Y", "Z", "x", "y", "z"]] = None,
        p_bitflip: float = 0.0,
        p_reset: float = 0.0,
        p_meas: float = 0.0,
        p_cnot: float = 0.0,
        p_idle: float = 0.0,
        p_circuit: Optional[float] = None,
        p_cult: Optional[float] = None,
        perfect_init_final: bool = False,
        comparative_decoding: bool = False,
        exclude_non_essential_pauli_detectors: bool = False,
        cultivation_circuit: Optional[stim.Circuit] = None,
        remove_non_edge_like_errors: bool = True,
        shape: str = None,
        _generate_dem: bool = True,
        _decompose_dem: bool = True,
        _benchmarking: bool = False,
    ):
        """
        Class for constructing a color code circuit and simulating the
        concatenated MWPM decoder.

        Parameters
        ----------
        d : int >= 3
            Code distance.

        rounds : int >= 1
            Number of syndrome extraction rounds.

        circuit_type : {'triangle', 'tri', 'rectangle', 'rec', 'rec_stability', 'growing',
                'cult+growing'}, default 'tri'
            Circuit type.
            - 'triangle'/'tri': memory experiment of a triangular patch with distance
              `d`.
            - 'rectangle'/'rec': memory experiment of a rectangular patch with distance
              `d` and `d2`.
            - 'rec_stability': stability experiment of a rectangle-like patch with
              single-type boundaries. `d` and `d2` indicate the size of the patch,
              rather than code distances.
            - 'growing': growing operation from a triangular patch with distance `d` to
              a larger triangular patch with distance `d2`. Must be `d2 > d`.
            - 'cult+growing': cultivation on a triangular patch with distance `d`,
              followed by a growing operation to distance `d2`. Must be `d2 > d`.

        d2 : int >= 3, optional
            Second code distance required for several circuit types.
            If not provided, `d2 = d`.

        cnot_schedule : str, list of 12 ints, or dict with keys 'X' and 'Z', default 'tri_optimal'
            CNOT schedule.
            - If a string, must be one of {'tri_optimal', 'tri_optimal_reversed', 'LLB'} and uses a preset uniform schedule for all stabilizers.
            - If a list of 12 ints, applies the same CNOT order to all stabilizers (uniform schedule).
            - If a dict with keys 'X' and 'Z', each value should be a list of lists of ints, specifying the CNOT order for each X or Z stabilizer, respectively (per-stabilizer schedule for both X and Z stabilizers).
            This allows for custom, non-uniform CNOT ordering across stabilizers.

        temp_bdry_type : {'X', 'Y', 'Z', 'x', 'y', 'z'}, optional
            Type of the temporal boundaries, i.e., the reset/measurement basis of
            data qubits at the beginning and end of the circuit.
            Not supported for `rec_stability` and `cult+growing` circuits: the types of
            the temporal boundaries are fixed to red for `rec_stability` and `Y` for
            `cult+growing`. For the other circuit types, it is `Z` by default.

        p_bitflip : float, default 0
            Bit-flip probability at the start of each round.
        p_reset : float, default 0
            Probability of a wrong qubit reset (i.e., producing an
            orthogonal state).
        p_meas : float, default 0
            Probability of a flipped measurement outcome.
        p_cnot : float, default 0
            Strength of a two-qubit depolarizing noise channel following
            each CNOT gate.
        p_idle : float, default 0
            Strength of a single-qubit depolarizing noise channel following
            each idle gate.
        p_circuit : float, optional
            If given, p_reset = p_meas = p_cnot = p_idle = p_circuit.
        p_cult : float, optional
            Physical error probability during cultivation (only used for 'cult+growing'
            circuits). If not given, `p_cult = p_circuit`.
        perfect_init_final : bool, default False
            Whether to use perfect initialization and final measurement.
        comparative_decoding : bool, default False
            Whether to use the comparative decoding technique. If True, observables are
            included as additional detectors and decoding can be done by running the
            decoder for each logical class and choosing the lowest-weight one. This also
            provides the logical gap information, which quantifies the reliability of
            decoding.
        exclude_non_essential_pauli_detectors : bool, default False
            If True and `temp_bdry_type` is not "Y", detectors with the Pauli type
            different from the temporal boundary type (e.g., X-type detectors for
            `temp_bdry_type="Z"`) are excluded from the circuit. This does not affect the
            decoding results since X and Z errors are independently decoded in our method
            and physical errors with the same pauli type as the temporal boundaries do
            not affect the logical values. If `temp_bdry_type="Y"` or
            `circuit_type="cult+growing"`, both types of detectors are required for decoding,
            so this option is ignored.
        cultivation_circuit: stim.Circuit, optional
            If given, it is used as the cultivation circuit for cultivation + growing
            circuit (`circuit_type == 'cult+growing'`). WARNING: Its validity is not
            checked internally.
        remove_non_edge_like_errors: bool, default True
            Whether to remove error mechanisms that are not edge-like when decomposing
            the detector error model.
        shape: str, optional
            Legacy parameter same as `circuit_type` for backward compatability. If this
            is given, it is prioritized over `circuit_type`.
        """
        if isinstance(cnot_schedule, str):
            if cnot_schedule in ["tri_optimal", "LLB"]:
                cnot_schedule = [2, 3, 6, 5, 4, 1, 3, 4, 7, 6, 5, 2]
            elif cnot_schedule == "tri_optimal_reversed":
                cnot_schedule = [3, 4, 7, 6, 5, 2, 2, 3, 6, 5, 4, 1]
            else:
                raise ValueError(f"Invalid cnot schedule: {cnot_schedule}")
            self._per_stabilizer_cnot = False
        elif isinstance(cnot_schedule, dict):
            # Dict with keys 'X' and 'Z', each a list of lists
            if set(cnot_schedule.keys()) == {"X", "Z"} and all(
                isinstance(v, list)
                and all(
                    isinstance(l, list) and all(isinstance(i, int) for i in l)
                    for l in v
                )
                for v in cnot_schedule.values()
            ):
                self._per_stabilizer_cnot = "dict"
            else:
                raise ValueError(
                    "If cnot_schedule is a dict, it must have keys 'X' and 'Z', each mapping to a list of lists of ints."
                )
        elif isinstance(cnot_schedule, list):
            if all(isinstance(x, int) for x in cnot_schedule):
                assert len(cnot_schedule) == 12
                self._per_stabilizer_cnot = False
            else:
                raise ValueError(
                    "cnot_schedule must be a string, a list of 12 ints, or a dict with keys 'X' and 'Z'."
                )
        else:
            raise ValueError(
                "cnot_schedule must be a string, a list of 12 ints, or a dict with keys 'X' and 'Z'."
            )
        self.cnot_schedule = cnot_schedule

        assert d > 1 and rounds >= 1

        if p_circuit is not None:
            p_reset = p_meas = p_cnot = p_idle = p_circuit

        self.d = d
        d2 = self.d2 = d if d2 is None else d2
        self.rounds = rounds

        if shape is not None:
            circuit_type = shape

        if circuit_type in {"triangle", "tri"}:
            assert d % 2 == 1
            self.circuit_type = "tri"
            self.num_obs = 1

        elif circuit_type in {"rectangle", "rec"}:
            assert d2 is not None
            assert d % 2 == 0 and d2 % 2 == 0
            self.circuit_type = "rec"
            self.num_obs = 2

        elif circuit_type == "rec_stability":
            assert d2 is not None
            assert d % 2 == 0 and d2 % 2 == 0
            self.circuit_type = "rec_stability"
            self.num_obs = 2

        elif circuit_type == "growing":
            assert d2 is not None
            assert d % 2 == 1 and d2 % 2 == 1 and d2 > d
            self.circuit_type = "growing"
            self.num_obs = 1

        elif circuit_type in {"cultivation+growing", "cult+growing"}:
            assert p_circuit is not None and p_bitflip == 0
            assert d2 is not None
            assert d % 2 == 1 and d2 % 2 == 1 and d2 > d
            self.circuit_type = "cult+growing"
            self.num_obs = 1

        else:
            raise ValueError(f"Invalid circuit type: {circuit_type}")

        if temp_bdry_type is None:
            if circuit_type == "rec_stability":
                temp_bdry_type = "r"
            elif circuit_type == "cult+growing":
                temp_bdry_type = "Y"
            else:
                temp_bdry_type = "Z"
        else:
            assert temp_bdry_type in {"X", "Y", "Z", "x", "y", "z"}
            assert circuit_type not in {"rec_stability", "cult+growing"}
            temp_bdry_type = temp_bdry_type.upper()

        self.temp_bdry_type = temp_bdry_type

        if circuit_type == "rec_stability":
            self.obs_paulis = ["Z", "X"]
        else:
            self.obs_paulis = [temp_bdry_type] * self.num_obs

        self.perfect_init_final = perfect_init_final
        self.physical_probs = {
            "bitflip": p_bitflip,
            "reset": p_reset,
            "meas": p_meas,
            "cnot": p_cnot,
            "idle": p_idle,
        }
        if self.circuit_type == "cult+growing":
            self.physical_probs["cult"] = p_cult if p_cult is not None else p_circuit
        self.comparative_decoding = comparative_decoding

        self.exclude_non_essential_pauli_detectors = (
            exclude_non_essential_pauli_detectors
        )

        self.remove_non_edge_like_errors = remove_non_edge_like_errors

        if self.comparative_decoding and self.circuit_type == "rec_stability":
            raise NotImplementedError

        if self.circuit_type == "cult+growing":
            if cultivation_circuit is None:
                cultivation_circuit = _load_cultivation_circuit(
                    d=d, p=self.physical_probs["cult"]
                )

        else:
            cultivation_circuit = None
        self.cultivation_circuit = cultivation_circuit

        self.tanner_graph = ig.Graph()

        self._benchmarking = _benchmarking

        # Various qubit groups predefined for efficiency
        self.qubit_groups = {}

        tanner_graph = self.tanner_graph

        self._create_tanner_graph()

        self.circuit = self._generate_circuit()

        (
            detector_ids_by_color,
            cult_detector_ids,
            interface_detector_ids,
            detectors_checks_map,
        ) = self._generate_det_id_info()

        # Detector coordinates: (x, y, t, pauli, color) OR (x, y, t, pauli, color, flag)
        # pauli = 0, 1, 2 -> X, Y, Z
        # color = 0, 1, 2 -> r, g, b
        # flag does not exist for ordinary detectors.
        # flag >= 0: detector corresponding to an observable (id=flag)
        # (only when comparatitive_decoding is True)
        # flag = -2, -1: cultivation / interface between cultivation and growing
        # (only for `cult+growing` circuits)
        self.detector_ids_by_color = detector_ids_by_color
        self.cult_detector_ids = cult_detector_ids
        self.interface_detector_ids = interface_detector_ids

        # Mapping between detector ids and ancillary qubits
        # self.detectors_checks_map[detector_id] = (anc_qubit, time_coord)
        self.detectors_checks_map = detectors_checks_map

        if _generate_dem:
            self.dem_xz, self.H, self.obs_matrix, self.probs_xz = self._generate_dem()
        else:
            self.dem_xz = None
            self.H = None
            self.obs_matrix = None
            self.probs_xz = None

        self._bp_inputs = {}

        # Decompose detector error models
        self.dems_decomposed = {}
        if _generate_dem and _decompose_dem:
            for c in ["r", "g", "b"]:
                dem_decomp = DemDecomp(
                    org_dem=self.dem_xz,
                    color=c,
                    remove_non_edge_like_errors=self.remove_non_edge_like_errors,
                )
                self.dems_decomposed[c] = dem_decomp

    def get_detector_type(self, detector_id: int) -> Tuple[PAULI_LABEL, COLOR_LABEL]:
        coords = self.circuit.get_detector_coordinates(only=[detector_id])[detector_id]
        pauli = coords[3]
        if pauli == 0:
            pauli = "X"
        elif pauli == 1:
            pauli = "Y"
        elif pauli == 2:
            pauli = "Z"
        else:
            raise ValueError(f"Invalid pauli: {pauli}")
        color = self.color_val_to_color(coords[4])

        return pauli, color

    def get_observable_pauli(self, observable_id: int) -> PAULI_LABEL:
        return self.obs_paulis[observable_id]

    @timeit
    def _create_tanner_graph(self) -> None:
        """Construct the Tanner graph for the chosen circuit type."""

        circuit_type = self.circuit_type
        tanner_graph = self.tanner_graph

        if circuit_type in {"tri", "growing", "cult+growing"}:
            if circuit_type == "tri":
                d = self.d
            else:
                d = self.d2

            assert d % 2 == 1

            detid = 0
            L = round(3 * (d - 1) / 2)
            for y in range(L + 1):
                if y % 3 == 0:
                    anc_qubit_color = "g"
                    anc_qubit_pos = 2
                elif y % 3 == 1:
                    anc_qubit_color = "b"
                    anc_qubit_pos = 0
                else:
                    anc_qubit_color = "r"
                    anc_qubit_pos = 1

                for x in range(2 * y, 4 * L - 2 * y + 1, 4):
                    boundary = []
                    if y == 0:
                        boundary.append("r")
                    if x == 2 * y:
                        boundary.append("g")
                    if x == 4 * L - 2 * y:
                        boundary.append("b")
                    boundary = "".join(boundary)
                    if not boundary:
                        boundary = None

                    if circuit_type in {"tri"}:
                        obs = boundary in ["r", "rg", "rb"]
                    elif circuit_type in {"growing", "cult+growing"}:
                        obs = boundary in ["g", "gb", "rg"]
                    else:
                        obs = False

                    if round((x / 2 - y) / 2) % 3 != anc_qubit_pos:
                        tanner_graph.add_vertex(
                            name=f"{x}-{y}",
                            x=x,
                            y=y,
                            qid=tanner_graph.vcount(),
                            pauli=None,
                            color=None,
                            obs=obs,
                            boundary=boundary,
                        )
                    else:
                        for pauli in ["Z", "X"]:
                            tanner_graph.add_vertex(
                                name=f"{x}-{y}-{pauli}",
                                x=x,
                                y=y,
                                qid=tanner_graph.vcount(),
                                pauli=pauli,
                                color=anc_qubit_color,
                                obs=False,
                                boundary=boundary,
                            )
                            detid += 1

        elif circuit_type == "rec":
            d, d2 = self.d, self.d2
            assert d % 2 == 0
            assert d2 % 2 == 0

            detid = 0
            L1 = round(3 * d / 2 - 2)
            L2 = round(3 * d2 / 2 - 2)
            for y in range(L2 + 1):
                if y % 3 == 0:
                    anc_qubit_color = "g"
                    anc_qubit_pos = 2
                elif y % 3 == 1:
                    anc_qubit_color = "b"
                    anc_qubit_pos = 0
                else:
                    anc_qubit_color = "r"
                    anc_qubit_pos = 1

                for x in range(2 * y, 2 * y + 4 * L1 + 1, 4):
                    boundary = []
                    if y == 0 or y == L2:
                        boundary.append("r")
                    if 2 * y == x or 2 * y == x - 4 * L1:
                        boundary.append("g")
                    boundary = "".join(boundary)
                    if not boundary:
                        boundary = None

                    if round((x / 2 - y) / 2) % 3 != anc_qubit_pos:
                        obs_g = y == 0
                        obs_r = x == 2 * y + 4 * L1

                        tanner_graph.add_vertex(
                            name=f"{x}-{y}",
                            x=x,
                            y=y,
                            qid=tanner_graph.vcount(),
                            pauli=None,
                            color=None,
                            obs_r=obs_r,
                            obs_g=obs_g,
                            boundary=boundary,
                        )
                    else:
                        for pauli in ["Z", "X"]:
                            tanner_graph.add_vertex(
                                name=f"{x}-{y}-{pauli}",
                                x=x,
                                y=y,
                                qid=tanner_graph.vcount(),
                                pauli=pauli,
                                color=anc_qubit_color,
                                obs_r=False,
                                obs_g=False,
                                boundary=boundary,
                            )
                            detid += 1

            # Additional corner vertex
            x = 2 * L2 + 2
            y = L2 + 1
            # x, y = L2 - 2, L2
            tanner_graph.add_vertex(
                name=f"{x}-{y}",
                x=x,
                y=y,
                qid=tanner_graph.vcount(),
                pauli=None,
                color=None,
                obs_r=False,
                obs_g=False,
                boundary="rg",
            )

        elif circuit_type == "rec_stability":
            d = self.d
            d2 = self.d2
            assert d % 2 == 0
            assert d2 % 2 == 0

            detid = 0
            L1 = round(3 * d / 2 - 2)
            L2 = round(3 * d2 / 2 - 2)
            for y in range(L2 + 1):
                if y % 3 == 0:
                    anc_qubit_color = "r"
                    anc_qubit_pos = 0
                elif y % 3 == 1:
                    anc_qubit_color = "b"
                    anc_qubit_pos = 1
                else:
                    anc_qubit_color = "g"
                    anc_qubit_pos = 2

                if y == 0:
                    x_init_adj = 8
                elif y == 1:
                    x_init_adj = 4
                else:
                    x_init_adj = 0

                if y == L2:
                    x_fin_adj = 8
                elif y == L2 - 1:
                    x_fin_adj = 4
                else:
                    x_fin_adj = 0

                for x in range(2 * y + x_init_adj, 2 * y + 4 * L1 + 1 - x_fin_adj, 4):
                    if (
                        y == 0
                        or y == L2
                        or x == y * 2
                        or x == 2 * y + 4 * L1
                        or (x, y) == (6, 1)
                        or (x, y) == (2 * L2 + 4 * L1 - 6, L2 - 1)
                    ):
                        boundary = "g"
                    else:
                        boundary = None

                    if round((x / 2 - y) / 2) % 3 != anc_qubit_pos:
                        tanner_graph.add_vertex(
                            name=f"{x}-{y}",
                            x=x,
                            y=y,
                            qid=tanner_graph.vcount(),
                            pauli=None,
                            color=None,
                            boundary=boundary,
                        )
                    else:
                        for pauli in ["Z", "X"]:
                            tanner_graph.add_vertex(
                                name=f"{x}-{y}-{pauli}",
                                x=x,
                                y=y,
                                qid=tanner_graph.vcount(),
                                pauli=pauli,
                                color=anc_qubit_color,
                                boundary=boundary,
                            )
                            detid += 1

        else:
            raise ValueError(f"Invalid circuit type: {circuit_type}")

        # Update qubit_groups
        data_qubits = tanner_graph.vs.select(pauli=None)
        anc_qubits = tanner_graph.vs.select(pauli_ne=None)
        anc_Z_qubits = anc_qubits.select(pauli="Z")
        anc_X_qubits = anc_qubits.select(pauli="X")
        anc_red_qubits = anc_qubits.select(color="r")
        anc_green_qubits = anc_qubits.select(color="g")
        anc_blue_qubits = anc_qubits.select(color="b")

        self.qubit_groups.update(
            {
                "data": data_qubits,
                "anc": anc_qubits,
                "anc_Z": anc_Z_qubits,
                "anc_X": anc_X_qubits,
                "anc_red": anc_red_qubits,
                "anc_green": anc_green_qubits,
                "anc_blue": anc_blue_qubits,
            }
        )

        # Add edges
        links = []
        offsets = [(-2, 1), (2, 1), (4, 0), (2, -1), (-2, -1), (-4, 0)]
        for anc_qubit in self.qubit_groups["anc"]:
            data_qubits = []
            for offset in offsets:
                data_qubit_x = anc_qubit["x"] + offset[0]
                data_qubit_y = anc_qubit["y"] + offset[1]
                data_qubit_name = f"{data_qubit_x}-{data_qubit_y}"
                try:
                    data_qubit = tanner_graph.vs.find(name=data_qubit_name)
                except ValueError:
                    continue
                data_qubits.append(data_qubit)
                tanner_graph.add_edge(anc_qubit, data_qubit, kind="tanner", color=None)

            if anc_qubit["pauli"] == "Z":
                weight = len(data_qubits)
                for i in range(weight):
                    qubit = data_qubits[i]
                    next_qubit = data_qubits[(i + 1) % weight]
                    if not tanner_graph.are_connected(qubit, next_qubit):
                        link = tanner_graph.add_edge(
                            qubit, next_qubit, kind="lattice", color=None
                        )
                        links.append(link)

        # Assign colors to links
        link: ig.Edge
        for link in links:
            v1: ig.Vertex
            v2: ig.Vertex
            v1, v2 = link.target_vertex, link.source_vertex
            ngh_ancs_1 = {anc.index for anc in v1.neighbors() if anc["pauli"] == "Z"}
            ngh_ancs_2 = {anc.index for anc in v2.neighbors() if anc["pauli"] == "Z"}
            color = tanner_graph.vs[(ngh_ancs_1 ^ ngh_ancs_2).pop()]["color"]
            link["color"] = color

    @staticmethod
    def get_qubit_coords(qubit: ig.Vertex) -> Tuple[int, int]:
        coords = [qubit["x"], qubit["y"]]
        # if qubit["pauli"] == "Z":
        #     coords[0] -= 1
        # elif qubit["pauli"] == "X":
        #     coords[0] += 1

        return tuple(coords)

    @staticmethod
    def color_to_color_val(color: Literal["r", "g", "b"]) -> int:
        return {"r": 0, "g": 1, "b": 2}[color]

    @staticmethod
    def color_val_to_color(color_val: Literal[0, 1, 2]) -> Literal["r", "g", "b"]:
        return {0: "r", 1: "g", 2: "b"}[color_val]

    def get_decomposed_dems(
        self, color: COLOR_LABEL
    ) -> Tuple[stim.DetectorErrorModel, stim.DetectorErrorModel]:
        dem1 = self.dems_decomposed[color][0].copy()
        dem2 = self.dems_decomposed[color][1].copy()
        return dem1, dem2

    @timeit
    def _generate_circuit(self) -> stim.Circuit:
        qubit_groups = self.qubit_groups
        cnot_schedule = self.cnot_schedule
        tanner_graph = self.tanner_graph
        rounds = self.rounds
        circuit_type = self.circuit_type
        d = self.d
        d2 = self.d2
        temp_bdry_type = self.temp_bdry_type
        probs = self.physical_probs
        p_bitflip = probs["bitflip"]
        p_reset = probs["reset"]
        p_meas = probs["meas"]
        p_cnot = probs["cnot"]
        p_idle = probs["idle"]

        perfect_init_final = self.perfect_init_final
        use_last_detectors = True

        data_qubits = qubit_groups["data"]
        anc_qubits = qubit_groups["anc"]
        anc_Z_qubits = qubit_groups["anc_Z"]
        anc_X_qubits = qubit_groups["anc_X"]

        data_qids = data_qubits["qid"]
        anc_qids = anc_qubits["qid"]
        anc_Z_qids = anc_Z_qubits["qid"]
        anc_X_qids = anc_X_qubits["qid"]

        num_data_qubits = len(data_qids)
        num_anc_Z_qubits = len(anc_Z_qubits)
        num_anc_X_qubits = len(anc_X_qubits)
        num_anc_qubits = num_anc_X_qubits + num_anc_Z_qubits

        num_qubits = tanner_graph.vcount()
        all_qids = list(range(num_qubits))
        all_qids_set = set(all_qids)

        exclude_non_essential_pauli_detectors = (
            self.exclude_non_essential_pauli_detectors
        )

        # Main circuit
        circuit = stim.Circuit()
        for qubit in tanner_graph.vs:
            coords = self.get_qubit_coords(qubit)
            circuit.append("QUBIT_COORDS", qubit.index, coords)

        # Syndrome extraction circuit without SPAM
        synd_extr_circuit_without_spam = stim.Circuit()
        if getattr(self, "_per_stabilizer_cnot", False) == True:
            # Per-stabilizer CNOT schedule: cnot_schedule is a list of lists, for Z stabilizers only
            for stab_idx, anc_Z_qubit in enumerate(anc_Z_qubits):
                CX_targets = []
                schedule = cnot_schedule[stab_idx]
                for offset_idx in schedule:
                    offsets = [(-2, 1), (2, 1), (4, 0), (2, -1), (-2, -1), (-4, 0)]
                    offset = offsets[offset_idx % 6]
                    data_qubit_x = anc_Z_qubit["x"] + offset[0]
                    data_qubit_y = anc_Z_qubit["y"] + offset[1]
                    data_qubit_name = f"{data_qubit_x}-{data_qubit_y}"
                    try:
                        data_qubit = tanner_graph.vs.find(name=data_qubit_name)
                    except ValueError:
                        continue
                    anc_qid = anc_Z_qubit.index
                    data_qid = data_qubit.index
                    CX_targets.extend([data_qid, anc_qid])
                if CX_targets:
                    synd_extr_circuit_without_spam.append("CX", CX_targets)
                    if p_cnot > 0:
                        synd_extr_circuit_without_spam.append(
                            "DEPOLARIZE2", CX_targets, p_cnot
                        )
                synd_extr_circuit_without_spam.append("TICK")
        elif getattr(self, "_per_stabilizer_cnot", False) == "dict":
            # Per-stabilizer CNOT schedule for both X and Z stabilizers
            z_schedules = cnot_schedule["Z"]
            x_schedules = cnot_schedule["X"]
            # Z stabilizers
            for stab_idx, anc_Z_qubit in enumerate(anc_Z_qubits):
                schedule = z_schedules[stab_idx]
                for offset_idx in schedule:
                    offsets = [(-2, 1), (2, 1), (4, 0), (2, -1), (-2, -1), (-4, 0)]
                    offset = offsets[offset_idx % 6]
                    data_qubit_x = anc_Z_qubit["x"] + offset[0]
                    data_qubit_y = anc_Z_qubit["y"] + offset[1]
                    data_qubit_name = f"{data_qubit_x}-{data_qubit_y}"
                    try:
                        data_qubit = tanner_graph.vs.find(name=data_qubit_name)
                    except ValueError:
                        continue
                    anc_qid = anc_Z_qubit.index
                    data_qid = data_qubit.index
                    synd_extr_circuit_without_spam.append("CX", [data_qid, anc_qid])
                    if p_cnot > 0:
                        synd_extr_circuit_without_spam.append(
                            "DEPOLARIZE2", [data_qid, anc_qid], p_cnot
                        )
                    synd_extr_circuit_without_spam.append("TICK")
            # X stabilizers
            for stab_idx, anc_X_qubit in enumerate(anc_X_qubits):
                schedule = x_schedules[stab_idx]
                for offset_idx in schedule:
                    offsets = [(-2, 1), (2, 1), (4, 0), (2, -1), (-2, -1), (-4, 0)]
                    offset = offsets[offset_idx % 6]
                    data_qubit_x = anc_X_qubit["x"] + offset[0]
                    data_qubit_y = anc_X_qubit["y"] + offset[1]
                    data_qubit_name = f"{data_qubit_x}-{data_qubit_y}"
                    try:
                        data_qubit = tanner_graph.vs.find(name=data_qubit_name)
                    except ValueError:
                        continue
                    anc_qid = anc_X_qubit.index
                    data_qid = data_qubit.index
                    synd_extr_circuit_without_spam.append("CX", [anc_qid, data_qid])
                    if p_cnot > 0:
                        synd_extr_circuit_without_spam.append(
                            "DEPOLARIZE2", [anc_qid, data_qid], p_cnot
                        )
                    synd_extr_circuit_without_spam.append("TICK")
        else:
            # Old behavior: uniform schedule for all stabilizers
            for timeslice in range(1, max(cnot_schedule) + 1):
                targets = [i for i, val in enumerate(cnot_schedule) if val == timeslice]
                operated_qids = set()

                CX_targets = []
                for target in targets:
                    if target in {0, 6}:
                        offset = (-2, 1)
                    elif target in {1, 7}:
                        offset = (2, 1)
                    elif target in {2, 8}:
                        offset = (4, 0)
                    elif target in {3, 9}:
                        offset = (2, -1)
                    elif target in {4, 10}:
                        offset = (-2, -1)
                    else:
                        offset = (-4, 0)

                    target_anc_qubits = anc_Z_qubits if target < 6 else anc_X_qubits
                    for anc_Z_qubit in target_anc_qubits:
                        data_qubit_x = anc_Z_qubit["x"] + offset[0]
                        data_qubit_y = anc_Z_qubit["y"] + offset[1]
                        data_qubit_name = f"{data_qubit_x}-{data_qubit_y}"
                        try:
                            data_qubit = tanner_graph.vs.find(name=data_qubit_name)
                        except ValueError:
                            continue
                        anc_qid = anc_Z_qubit.index
                        data_qid = data_qubit.index
                        operated_qids.update({anc_qid, data_qid})

                        CX_target = (
                            [data_qid, anc_qid] if target < 6 else [anc_qid, data_qid]
                        )
                        CX_targets.extend(CX_target)

                synd_extr_circuit_without_spam.append("CX", CX_targets)
                if p_cnot > 0:
                    synd_extr_circuit_without_spam.append(
                        "DEPOLARIZE2", CX_targets, p_cnot
                    )

                if p_idle > 0:
                    idling_qids = list(all_qids_set - operated_qids)
                    synd_extr_circuit_without_spam.append(
                        "DEPOLARIZE1", idling_qids, p_idle
                    )

                synd_extr_circuit_without_spam.append("TICK")

        # Syndrome extraction circuit with measurement & detector
        synd_extr_circuits = []
        obs_included_lookbacks = set()
        for first in [True, False]:
            synd_extr_circuit = synd_extr_circuit_without_spam.copy()

            if p_bitflip > 0:
                synd_extr_circuit.insert(
                    0, stim.CircuitInstruction("X_ERROR", data_qids, [p_bitflip])
                )

            synd_extr_circuit.append("MRZ", anc_Z_qids, p_meas)
            synd_extr_circuit.append("MRX", anc_X_qids, p_meas)

            ## If first is True:
            # tri/rec: detectors have the same type as the temporal boundary
            # rec_stability: X- and Z-type detectors exist except for red faces
            # growing: same as tri/rec if anc_qubit['y'] >= y_offset_init_patch,
            #          same as rec_stability otherwise.
            # cult+growing: X- and Z-type detectors exist if anc_qubit['y'] >= y_offset_init_patch,
            #               same as rec_stability otherwise.

            ## Z- and X-type detectors
            for pauli in ["Z", "X"]:
                if exclude_non_essential_pauli_detectors:
                    if temp_bdry_type in {"X", "Z"} and pauli != temp_bdry_type:
                        continue

                anc_qubits_now = anc_Z_qubits if pauli == "Z" else anc_X_qubits
                init_lookback = -num_anc_qubits if pauli == "Z" else -num_anc_X_qubits

                for j, anc_qubit in enumerate(anc_qubits_now):
                    anc_qubit: ig.Vertex
                    pauli_val = 0 if pauli == "X" else 2
                    color = anc_qubit["color"]
                    color_val = self.color_to_color_val(color)
                    coords = self.get_qubit_coords(anc_qubit)
                    det_coords = coords + (0, pauli_val, color_val)

                    if not first:
                        lookback = init_lookback + j
                        targets = [
                            stim.target_rec(lookback),
                            stim.target_rec(lookback - num_anc_qubits),
                        ]
                        synd_extr_circuit.append("DETECTOR", targets, det_coords)

                    else:
                        if circuit_type in {"tri", "rec"}:
                            detector_exists = temp_bdry_type == pauli
                        elif circuit_type == "rec_stability":
                            detector_exists = color != "r"
                        elif circuit_type == "growing":
                            if coords[1] >= y_offset_init_patch:
                                detector_exists = temp_bdry_type == pauli
                            else:
                                detector_exists = color != "r"
                        elif circuit_type == "cult+growing":
                            detector_exists = (
                                coords[1] >= y_offset_init_patch or color != "r"
                            )
                        else:
                            raise NotImplementedError

                        if detector_exists:
                            targets = [stim.target_rec(init_lookback + j)]

                            # For cult+growing, need to add targets during cultivation
                            # if anc_qubit is inside the initial patch.
                            if (
                                circuit_type == "cult+growing"
                                and coords[1] >= y_offset_init_patch
                            ):
                                # Add detector targets during cultivation
                                det_coords += (-1,)
                                adj_data_qubits = frozenset(
                                    qubit.index
                                    for qubit in anc_qubit.neighbors()
                                    if qubit["y"] >= y_offset_init_patch - 1e-6
                                )
                                paulis = [pauli]
                                if pauli == "X":
                                    paulis.append("Z")
                                    det_coords = list(det_coords)
                                    det_coords[3] = 1
                                    det_coords = tuple(det_coords)

                                    anc_Z_name = f"{coords[0]}-{coords[1]}-Z"
                                    anc_Z_qid = tanner_graph.vs.find(
                                        name=anc_Z_name
                                    ).index
                                    j_Z = anc_Z_qids.index(anc_Z_qid)
                                    targets.append(
                                        stim.target_rec(-num_anc_qubits + j_Z)
                                    )

                                targets_cult_all = []
                                lookbacks = []
                                for pauli_now in paulis:
                                    key = (pauli_now, adj_data_qubits)
                                    targets_cult = interface_detectors_info[key]
                                    lookbacks.extend(targets_cult)
                                    targets_cult = [
                                        stim.target_rec(-num_anc_qubits + cult_lookback)
                                        for cult_lookback in targets_cult
                                    ]
                                    targets_cult_all.extend(targets_cult)
                                targets.extend(targets_cult_all)

                                if pauli == "X" and color == "g":
                                    obs_included_lookbacks ^= set(lookbacks)

                            # Add detector
                            synd_extr_circuit.append("DETECTOR", targets, det_coords)

            ## Y-type detectors
            if first and temp_bdry_type == "Y" and circuit_type != "cult+growing":
                for j_Z, anc_qubit_Z in enumerate(anc_Z_qubits):
                    anc_qubit_Z: ig.Vertex
                    color = anc_qubit_Z["color"]
                    coords = self.get_qubit_coords(anc_qubit_Z)

                    if circuit_type in {"tri", "rec"}:
                        detector_exists = True
                    elif circuit_type == "rec_stability":
                        detector_exists = color != "r"
                    elif circuit_type == "growing":
                        detector_exists = coords[1] >= y_offset_init_patch
                    else:
                        raise NotImplementedError

                    if detector_exists:
                        j_X = anc_X_qubits["name"].index(
                            f"{anc_qubit_Z['x']}-{anc_qubit_Z['y']}-X"
                        )
                        det_coords = coords + (0, 1, self.color_to_color_val(color))
                        targets = [
                            stim.target_rec(-num_anc_qubits + j_Z),
                            stim.target_rec(-num_anc_X_qubits + j_X),
                        ]
                        synd_extr_circuit.append("DETECTOR", targets, det_coords)

            if p_reset > 0:
                synd_extr_circuit.append("X_ERROR", anc_Z_qids, p_reset)
                synd_extr_circuit.append("Z_ERROR", anc_X_qids, p_reset)
            if p_idle > 0:
                synd_extr_circuit.append("DEPOLARIZE1", data_qids, p_idle)

            # if custom_noise_channel is not None:
            #     synd_extr_circuit.append(custom_noise_channel[0],
            #                              data_qids,
            #                              custom_noise_channel[1])

            synd_extr_circuit.append("TICK")
            synd_extr_circuit.append("SHIFT_COORDS", (), (0, 0, 1))

            synd_extr_circuits.append(synd_extr_circuit)

        # Initialize qubits
        if temp_bdry_type in {"X", "Y", "Z"} and circuit_type not in {
            "growing",
            "cult+growing",
        }:
            circuit.append(f"R{temp_bdry_type}", data_qids)
            if p_reset > 0 and not perfect_init_final:
                error_type = "Z_ERROR" if temp_bdry_type == "X" else "X_ERROR"
                circuit.append(error_type, data_qids, p_reset)

        elif temp_bdry_type == "r":
            circuit.append("RX", data_q1s)
            circuit.append("RZ", data_q2s)
            if p_reset > 0 and not perfect_init_final:
                circuit.append("Z_ERROR", data_q1s, p_reset)
                circuit.append("X_ERROR", data_q2s, p_reset)

            circuit.append("TICK")

            circuit.append("CX", red_links.ravel())
            if p_cnot > 0:
                circuit.append("DEPOLARIZE2", red_links.ravel(), p_cnot)

        elif circuit_type == "growing":
            # Data qubits inside the initial patch
            data_qids_init_patch = data_qubits.select(y_ge=y_offset_init_patch)["qid"]
            circuit.append(f"R{temp_bdry_type}", data_qids_init_patch)
            if p_reset > 0 and not perfect_init_final:
                error_type = "Z_ERROR" if temp_bdry_type == "X" else "X_ERROR"
                circuit.append(error_type, data_qids_init_patch, p_reset)

            # Data qubits outside the initial patch
            circuit.append("RX", data_q1s)
            circuit.append("RZ", data_q2s)
            if p_reset > 0:
                circuit.append("Z_ERROR", data_q1s, p_reset)
                circuit.append("X_ERROR", data_q2s, p_reset)

            circuit.append("TICK")

            circuit.append("CX", red_links.ravel())
            if p_cnot > 0:
                circuit.append("DEPOLARIZE2", red_links.ravel(), p_cnot)

        elif circuit_type == "cult+growing":
            # Find last tick position
            for i in range(len(circuit) - 1, -1, -1):
                instruction = circuit[i]
                if (
                    isinstance(instruction, stim.CircuitInstruction)
                    and instruction.name == "TICK"
                ):
                    last_tick_pos = i
                    break

            # Data qubits outside the initial patch (inserted before the last tick)
            circuit.insert(last_tick_pos, stim.CircuitInstruction("RX", data_q1s))
            circuit.insert(last_tick_pos + 1, stim.CircuitInstruction("RZ", data_q2s))
            if p_reset > 0:
                circuit.insert(
                    last_tick_pos + 2,
                    stim.CircuitInstruction("Z_ERROR", data_q1s, [p_reset]),
                )
                circuit.insert(
                    last_tick_pos + 3,
                    stim.CircuitInstruction("X_ERROR", data_q2s, [p_reset]),
                )

            # CX gate (inserted after the last tick)
            circuit.append("CX", red_links.ravel())
            if p_cnot > 0:
                circuit.append("DEPOLARIZE2", red_links.ravel(), p_cnot)

        else:
            raise NotImplementedError

        circuit.append("RZ", anc_Z_qids)
        circuit.append("RX", anc_X_qids)

        if p_reset > 0:
            circuit.append("X_ERROR", anc_Z_qids, p_reset)
            circuit.append("Z_ERROR", anc_X_qids, p_reset)

        # if p_bitflip > 0:
        #     circuit.append("X_ERROR", data_qids, p_bitflip)

        # if custom_noise_channel is not None:
        #     circuit.append(custom_noise_channel[0],
        #                    data_qids,
        #                    custom_noise_channel[1])

        circuit.append("TICK")

        circuit += synd_extr_circuits[0]
        circuit += synd_extr_circuits[1] * (rounds - 1)

        # Final data qubit measurements (& observables for red boundaries)
        p_meas_final = 0 if perfect_init_final else p_meas
        if temp_bdry_type in {"X", "Y", "Z"}:
            circuit.append(f"M{temp_bdry_type}", data_qids, p_meas_final)
            if use_last_detectors:
                if temp_bdry_type == "X":
                    anc_qubits_now = anc_X_qubits
                    init_lookback = -num_data_qubits - num_anc_X_qubits
                    pauli_val = 0
                else:
                    anc_qubits_now = anc_Z_qubits
                    init_lookback = -num_data_qubits - num_anc_qubits
                    pauli_val = 2 if temp_bdry_type == "Z" else 1

                for j_anc, anc_qubit in enumerate(anc_qubits_now):
                    anc_qubit: ig.Vertex
                    ngh_data_qubits = anc_qubit.neighbors()
                    lookback_inds = [
                        -num_data_qubits + data_qids.index(q.index)
                        for q in ngh_data_qubits
                    ]
                    lookback_inds.append(init_lookback + j_anc)
                    if temp_bdry_type == "Y":
                        anc_X_qubit = tanner_graph.vs.find(
                            name=f"{anc_qubit['x']}-{anc_qubit['y']}-X"
                        )
                        j_anc_X = anc_X_qids.index(anc_X_qubit.index)
                        lookback_inds.append(
                            -num_data_qubits - num_anc_X_qubits + j_anc_X
                        )
                    target = [stim.target_rec(ind) for ind in lookback_inds]
                    color_val = self.color_to_color_val(anc_qubit["color"])
                    coords = self.get_qubit_coords(anc_qubit) + (
                        0,
                        pauli_val,
                        color_val,
                    )
                    circuit.append("DETECTOR", target, coords)

        elif temp_bdry_type == "r":
            if not use_last_detectors:
                raise NotImplementedError

            circuit.append("CX", red_links.ravel())
            if p_cnot > 0 and not perfect_init_final:
                circuit.append("DEPOLARIZE2", red_links.ravel(), p_cnot)

            circuit.append("TICK")

            circuit.append("MZ", data_q2s, p_meas_final)  # ZZ measurement outcomes

            num_data_q2s = data_q2s.size
            lookback_inds_anc = {}
            for j, data_q2 in enumerate(data_q2s):
                for anc_Z_qubit in tanner_graph.vs[data_q2].neighbors():
                    if anc_Z_qubit["pauli"] == "Z" and anc_Z_qubit["color"] != "r":
                        anc_Z_qid = anc_Z_qubit.index
                        lookback_ind = j - num_data_q2s
                        try:
                            lookback_inds_anc[anc_Z_qid].append(lookback_ind)
                        except KeyError:
                            lookback_inds_anc[anc_Z_qid] = [lookback_ind]

            obs_Z_lookback_inds = []
            for j_anc_Z, anc_Z_qubit in enumerate(anc_Z_qubits):
                check_meas_lookback_ind = j_anc_Z - num_data_q2s - num_anc_qubits
                if anc_Z_qubit["color"] != "g":
                    obs_Z_lookback_inds.append(check_meas_lookback_ind)
                try:
                    lookback_inds = lookback_inds_anc[anc_Z_qubit.index]
                except KeyError:
                    continue
                lookback_inds.append(check_meas_lookback_ind)
                target = [stim.target_rec(ind) for ind in lookback_inds]
                color_val = self.color_to_color_val(anc_Z_qubit["color"])
                coords = self.get_qubit_coords(anc_Z_qubit) + (0, 2, color_val)
                circuit.append("DETECTOR", target, coords)

            target = [stim.target_rec(ind) for ind in obs_Z_lookback_inds]
            circuit.append("OBSERVABLE_INCLUDE", [target], 0)
            if self.comparative_decoding:
                raise NotImplementedError

            circuit.append("MX", data_q1s, p_meas_final)  # XX measurement outcomes

            num_data_q1s = data_q1s.size
            lookback_inds_anc = {}
            for j, data_q1 in enumerate(data_q1s):
                for anc_X_qubit in tanner_graph.vs[data_q1].neighbors():
                    if anc_X_qubit["pauli"] == "X" and anc_X_qubit["color"] != "r":
                        anc_X_qid = anc_X_qubit.index
                        lookback_ind = j - num_data_q1s
                        try:
                            lookback_inds_anc[anc_X_qid].append(lookback_ind)
                        except KeyError:
                            lookback_inds_anc[anc_X_qid] = [lookback_ind]

            obs_X_lookback_inds = []
            for j_anc_X, anc_X_qubit in enumerate(anc_X_qubits):
                check_meas_lookback_ind = (
                    j_anc_X - num_data_q1s - num_data_q2s - num_anc_X_qubits
                )
                color = anc_X_qubit["color"]
                if color != "g":
                    obs_X_lookback_inds.append(check_meas_lookback_ind)

                try:
                    lookback_inds = lookback_inds_anc[anc_X_qubit.index]
                except KeyError:
                    continue

                lookback_inds.append(check_meas_lookback_ind)
                target = [stim.target_rec(ind) for ind in lookback_inds]
                color_val = self.color_to_color_val(color)
                coords = self.get_qubit_coords(anc_X_qubit) + (0, 0, color_val)
                circuit.append("DETECTOR", target, coords)

            target = [stim.target_rec(ind) for ind in obs_X_lookback_inds]
            circuit.append("OBSERVABLE_INCLUDE", target, 1)
            if self.comparative_decoding:
                raise NotImplementedError

        else:
            raise NotImplementedError

        # Logical observables
        if temp_bdry_type in {"X", "Y", "Z"}:
            if circuit_type in {"tri", "growing", "cult+growing"}:
                qubits_logs = [tanner_graph.vs.select(obs=True)]
                if circuit_type == "tri":
                    bdry_colors = [0]
                elif circuit_type == "growing":
                    bdry_colors = [1]
                elif circuit_type == "cult+growing":
                    bdry_colors = [1]

            # elif shape == "cult+growing":
            #     qubits_logs = [tanner_graph.vs.select(pauli=None)]
            #     bdry_colors = [1]

            elif circuit_type == "rec":
                qubits_log_r = tanner_graph.vs.select(obs_r=True)
                qubits_log_g = tanner_graph.vs.select(obs_g=True)
                qubits_logs = [qubits_log_r, qubits_log_g]
                bdry_colors = [1, 0]

            for obs_id, qubits_log in enumerate(qubits_logs):
                lookback_inds = [
                    -num_data_qubits + data_qids.index(q.index) for q in qubits_log
                ]
                if obs_included_lookbacks:
                    num_meas_after_cult = num_anc_qubits * self.rounds + num_data_qubits
                    lookback_inds.extend(
                        lb - num_meas_after_cult for lb in obs_included_lookbacks
                    )

                target = [stim.target_rec(ind) for ind in lookback_inds]
                circuit.append("OBSERVABLE_INCLUDE", target, obs_id)
                if self.comparative_decoding:
                    color_val = bdry_colors[obs_id]
                    if temp_bdry_type == "X":
                        pauli_val = 0
                    elif temp_bdry_type == "Y":
                        pauli_val = 1
                    elif temp_bdry_type == "Z":
                        pauli_val = 2
                    else:
                        raise ValueError(f"Invalid temp_bdry_type: {temp_bdry_type}")
                    coords = (-1, -1, -1, pauli_val, color_val, obs_id)
                    circuit.append("DETECTOR", target, coords)

        return circuit

    def _generate_det_id_info(
        self,
    ) -> Tuple[
        Dict[COLOR_LABEL, List[int]], List[int], List[int], List[Tuple[ig.Vertex, int]]
    ]:
        tanner_graph = self.tanner_graph

        detector_coords_dict = self.circuit.get_detector_coordinates()
        detector_ids_by_color = {
            "r": [],
            "g": [],
            "b": [],
        }
        cult_detector_ids = []
        interface_detector_ids = []
        detectors_checks_map = []

        for detector_id in range(self.circuit.num_detectors):
            coords = detector_coords_dict[detector_id]
            if self.circuit_type == "cult+growing" and len(coords) == 6:
                # The detector is in the cultivation circuit or the interface region
                flag = coords[-1]
                if flag == -1:
                    interface_detector_ids.append(detector_id)
                elif flag == -2:
                    cult_detector_ids.append(detector_id)
                    continue

            x = round(coords[0])
            y = round(coords[1])
            t = round(coords[2])
            pauli = round(coords[3])
            color = self.color_val_to_color(round(coords[4]))
            is_obs = len(coords) == 6 and round(coords[-1]) >= 0

            if not is_obs:
                # Ordinary X/Z detectors
                if pauli == 0:
                    name = f"{x}-{y}-X"
                    qubit = tanner_graph.vs.find(name=name)
                    color = qubit["color"]
                elif pauli == 2:
                    name = f"{x}-{y}-Z"
                    qubit = tanner_graph.vs.find(name=name)
                    color = qubit["color"]
                elif pauli == 1:
                    name_X = f"{x}-{y}-X"
                    name_Z = f"{x}-{y}-Z"
                    qubit_X = tanner_graph.vs.find(name=name_X)
                    qubit_Z = tanner_graph.vs.find(name=name_Z)
                    qubit = (qubit_X, qubit_Z)
                    color = qubit_X["color"]
                else:
                    print(coords)
                    raise ValueError(f"Invalid pauli: {pauli}")

                detectors_checks_map.append((qubit, t))

            detector_ids_by_color[color].append(detector_id)

        return (
            detector_ids_by_color,
            cult_detector_ids,
            interface_detector_ids,
            detectors_checks_map,
        )

    def _generate_dem(
        self,
    ) -> Tuple[stim.DetectorErrorModel, csc_matrix, csc_matrix, np.ndarray]:
        circuit_xz = separate_depolarizing_errors(self.circuit)
        dem_xz = circuit_xz.detector_error_model(flatten_loops=True)
        if self.circuit_type == "cult+growing":
            # Remove error mechanisms that involve detectors that will be post-selected
            dem_xz_new = stim.DetectorErrorModel()
            all_detids_in_dem_xz = set()
            for inst in dem_xz:
                keep = True
                if inst.type == "error":
                    detids = []
                    for target in inst.targets_copy():
                        if target.is_relative_detector_id():
                            detid = int(str(target)[1:])
                            detids.append(detid)
                            if (
                                detid
                                in self.cult_detector_ids
                                # + self.interface_detector_ids
                            ):
                                keep = False
                                continue
                    if keep:
                        all_detids_in_dem_xz.update(detids)
                if keep:
                    dem_xz_new.append(inst)
            dem_xz = dem_xz_new
            probs_dem_xz = [
                em.args_copy()[0] for em in dem_xz.flattened() if em.type == "error"
            ]

            # After removing, some detectors during growth may not be involved
            # in any error mechanisms. Although such detectors have very low probability
            # to be flipped, we add them in the DEM with an arbitrary very small
            # probability to prevent PyMatching errors.
            detids_to_add = set(range(self.circuit.num_detectors))
            detids_to_add -= all_detids_in_dem_xz
            detids_to_add -= set(self.cult_detector_ids)
            detids_to_add = list(detids_to_add)
            p_very_small = max(probs_dem_xz) ** 2
            for detid in detids_to_add:
                dem_xz.append(
                    "error",
                    p_very_small,
                    [stim.DemTarget.relative_detector_id(detid)],
                )

        H, obs_matrix, probs_xz = dem_to_parity_check(dem_xz)

        return dem_xz, H, obs_matrix, probs_xz

    def draw_lattice(
        self,
        ax: Optional[plt.Axes] = None,
        show_axes: bool = False,
        highlight_qubits: Optional[
            List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
        ] = None,
        highlight_qubits2: Optional[
            List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
        ] = None,
        highlight_faces: Optional[
            List[int] | List[Tuple[float, float]] | List[str] | np.ndarray
        ] = None,
        **kwargs,
    ) -> plt.Axes:
        """
        Draws the color code lattice.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            The axis on which to draw the graph. If None, a new figure and
            axis will be created.
        show_axes : bool, default False
            Whether to show the x- and y-axis.
        highlight_qubits : list[int] | list[tuple] | list[str] | np.ndarray, optional
            Data qubits to highlight with orange triangles (by default).
            Can be a list of data qubit indices (ordered by code.vs.select(pauli=None)),
            a list of coordinate tuples [(x, y), ...], or a list of qubit names ['x-y', ...].
        highlight_qubits2 : list[int] | list[tuple] | list[str] | np.ndarray, optional
            Data qubits to highlight with purple rectangles (by default).
            Format is the same as highlight_qubits.
        highlight_faces : list[int] | list[tuple] | list[str] | np.ndarray, optional
            Z ancillary qubits whose corresponding faces should be highlighted.
            Can be a list of Z ancillary qubit indices (ordered by code.vs.select(pauli="Z")),
            a list of coordinate tuples [(x, y), ...], or a list of qubit names ['x-y', ...].
            Note that for names, the actual stored name includes a '-Z' suffix.
        edge_color : str, default 'black'
            Colors for edges.
        edge_linewidth : float, default 1.0
            Linewidth for edges.
        face_lightness : float, default 0.3
            Controls the lightness of face colors. Lower values make colors lighter.
        show_data_qubits : bool, default True
            Whether to draw circles representing data qubits.
        data_qubit_color : str, default 'black'
            Color for the data qubit circles (if shown).
        data_qubit_size : float, default 5.0
            Size for the data qubit circles (if shown).
        highlight_qubit_color : str, default 'orange'
            The color used to highlight qubits in `highlight_qubits`.
        highlight_qubit_color2 : str, default 'purple'
            The color used to highlight qubits in `highlight_qubits2`.
        highlight_qubit_marker : str, default '^' (triangle)
            The marker used to highlight qubits in `highlight_qubits`.
        highlight_qubit_marker2 : str, default 's' (square)
            The marker used to highlight qubits in `highlight_qubits2`.
        highlight_face_lightness : float, default 1.0
            Controls the lightness of the highlighted faces.

        Returns
        -------
        matplotlib.axes.Axes
            The axis containing the drawn lattice visualization.
        """
        return draw_lattice(
            self,
            ax=ax,
            show_axes=show_axes,
            highlight_qubits=highlight_qubits,
            highlight_qubits2=highlight_qubits2,
            highlight_faces=highlight_faces,
            **kwargs,
        )

    def draw_tanner_graph(
        self,
        ax: Optional[plt.Axes] = None,
        show_axes: bool = False,
        show_lattice: bool = False,
        **kwargs,
    ) -> plt.Axes:
        """
        Draw the tanner graph of the code.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            The axis on which to draw the graph. If None, a new figure and axis will be created.
        show_axes : bool, default False
            Whether to show the x- and y-axis.
        show_lattice : bool, default False
            Whether to show the lattice edges in addition to the tanner graph edges.
        **kwargs : dict
            Additional keyword arguments to pass to igraph.plot.

        Returns
        -------
        matplotlib.axes.Axes
            The axis containing the drawn graph.
        """
        return draw_tanner_graph(
            self,
            ax=ax,
            show_axes=show_axes,
            show_lattice=show_lattice,
            **kwargs,
        )

    def get_detector(self, detector_id: int) -> Tuple[ig.Vertex, int]:
        """
        Get the ancillary qubit and round corresponding to a detector from a
        given detector ID.

        Parameters
        ----------
        detector_id : int
            Detector ID.

        Returns
        -------
        anc : ig.Vertex
            Ancillary qubit involved in the detector.
        round : int
            Round that the detector belongs to.
        """
        try:
            return self.detectors_checks_map[detector_id]
        except IndexError:
            raise ValueError(f"Detector ID {detector_id} not found.")

    def decode_bp(
        self,
        detector_outcomes: np.ndarray,
        max_iter: int = 10,
        **kwargs,
    ):
        """
        Decode detector outcomes using belief propagation.

        This method uses the LDPC belief propagation decoder to decode the detector outcomes.
        It converts the detector error model to a parity check matrix and probability vector,
        then uses these to initialize a BpDecoder.

        Parameters
        ----------
        detector_outcomes : np.ndarray
            1D or 2D array of detector measurement outcomes to decode.
        max_iter : int
            Maximum number of belief propagation iterations to perform.
        **kwargs
            Additional keyword arguments to pass to the BpDecoder constructor.

        Returns
        -------
        pred : np.ndarray
            Predicted error pattern.
        llrs : np.ndarray
            Log probability ratios for each bit in the predicted error pattern.
        converge : bool
            Whether the belief propagation algorithm converged within max_iter iterations.
        """
        try:
            from ldpc import BpDecoder
        except ImportError:
            raise ImportError(
                "The 'ldpc' package is required for belief propagation decoding. "
                "Please install it using: pip install ldpc"
            )

        bp_inputs = self._bp_inputs
        if bp_inputs:
            H = bp_inputs["H"]
            p = bp_inputs["p"]
        else:
            if self.comparative_decoding:
                dem = remove_obs_from_dem(self.dem_xz)
            else:
                dem = self.dem_xz
            H, p = dem_to_parity_check(dem)
            bp_inputs["H"] = H
            bp_inputs["p"] = p

        if detector_outcomes.ndim == 1:
            bpd = BpDecoder(H, error_channel=p, max_iter=max_iter, **kwargs)
            pred = bpd.decode(detector_outcomes)
            llrs = bpd.log_prob_ratios
            converge = bpd.converge
        elif detector_outcomes.ndim == 2:
            pred = []
            llrs = []
            converge = []
            for det_sng in detector_outcomes:
                bpd = BpDecoder(H, error_channel=p, max_iter=max_iter, **kwargs)
                pred.append(bpd.decode(det_sng))
                llrs.append(bpd.log_prob_ratios)
                converge.append(bpd.converge)
            pred = np.stack(pred, axis=0)
            llrs = np.stack(llrs, axis=0)
            converge = np.stack(converge, axis=0)
        else:
            raise ValueError

        return pred, llrs, converge

    def decode(
        self,
        detector_outcomes: np.ndarray,
        colors: str | List[str] = "all",
        logical_value: bool | Sequence[bool] | None = None,
        bp_predecoding: bool = False,
        bp_prms: dict | None = None,
        erasure_matcher_predecoding: bool = False,
        partial_correction_by_predecoding: bool = False,
        full_output: bool = False,
        check_validity: bool = False,
        verbose: bool = False,
    ) -> np.ndarray | Tuple[np.ndarray, dict]:
        """
        Decode given detector outcomes using given decomposed DEMs.

        Parameters
        ----------
        detector_outcomes : 1D or 2D array-like of bool
            Array of input detector outcomes for one or multiple samples.
            If 1D, it is interpreted as a single sample.
            If 2D, each row corresponds to a sample and each column corresponds to a
            detector. detector_outcomes[i, j] is True if and only if the detector with
            id j in the ith sample has the outcome −1.
        colors : str or list of str, default 'all'
            Colors to use for decoding. Can be 'all', one of {'r', 'g', 'b'},
            or a list containing any combination of {'r', 'g', 'b'}.
        logical_value : bool or 1D array-like of bool, optional
            Logical value(s) to use for decoding. If None, all possible logical value
            combinations (i.e., logical classes) will be tried and the one with minimum
            weight will be selected.
        bp_predecoding : bool, default False
            Whether to use belief propagation as a pre-decoding step.
        bp_prms : dict, default None
            Parameters for the belief propagation decoder.
        erasure_matcher_predecoding : bool, default False
            Whether to use erasure matcher as a pre-decoding step.
        partial_correction_by_predecoding : bool, default False
            Whether to use the prediction from the erasure matcher predecoding as a
            partial correction for the second round of decoding, in the case that the predecoding fails to find a valid prediction.
        full_output : bool, default False
            Whether to return extra information about the decoding process.
        check_validity : bool, default False
            Whether to check the validity of the predicted error patterns.
        verbose : bool, default False
            Whether to print additional information during decoding.

        Returns
        -------
        obs_preds : 1D or 2D numpy array of bool
            Predicted observables. It is 1D if there is only one observable and
            2D if otherwise. obs_preds[i] or obs_preds[i,j] is True if and only
            if the j-th observable (j=0 when 1D) of the i-th sample is
            predicted to be -1.
        extra_outputs : dict, only when full_output is True
            Dictionary containing additional decoding outputs.
        """

        if erasure_matcher_predecoding:
            assert self.comparative_decoding

        detector_outcomes = np.asarray(detector_outcomes, dtype=bool)
        if detector_outcomes.ndim == 1:
            detector_outcomes = detector_outcomes.reshape(1, -1)

        if colors == "all":
            colors = ["r", "g", "b"]
        elif colors in ["r", "g", "b"]:
            colors = [colors]

        num_obs = self.num_obs

        all_logical_values = np.array(
            list(itertools.product([False, True], repeat=num_obs))
        )

        if logical_value is not None:
            logical_value = np.asarray(logical_value, dtype=bool).ravel()
            assert len(logical_value) == num_obs

        if bp_predecoding:
            if bp_prms is None:
                bp_prms = {}
            _, llrs, _ = self.decode_bp(detector_outcomes, **bp_prms)
            bp_probs = 1 / (1 + np.exp(llrs))
            eps = 1e-14
            bp_probs = bp_probs.clip(eps, 1 - eps)

            error_preds = []
            extra_outputs = {}
            for det_outcomes_sng in detector_outcomes:
                dems = {}
                for c in colors:
                    dem1_sym, dem2_sym = self.dems_decomposed[c].dems_symbolic
                    dem1 = dem1_sym.to_dem(self._bp_inputs["p"])
                    dem2 = dem2_sym.to_dem(self._bp_inputs["p"], sort=True)
                    dems[c] = (dem1, dem2)

                results = self.decode(
                    det_outcomes_sng.reshape(1, -1),
                    dems,
                    logical_value=logical_value,
                    full_output=full_output,
                )
                if full_output:
                    obs_preds_sng, extra_outputs_sng = results
                    for k, v in extra_outputs_sng.items():
                        try:
                            extra_outputs[k].append(v)
                        except KeyError:
                            extra_outputs[k] = [v]
                else:
                    obs_preds_sng = results
                error_preds.append(obs_preds_sng)

            error_preds = np.concatenate(error_preds, axis=0)
            for k, v in extra_outputs.items():
                extra_outputs[k] = np.concatenate(v, axis=0)

            if full_output:
                return error_preds, extra_outputs
            else:
                return error_preds

        if self.circuit_type == "cult+growing":
            # Post-select based on the detector outcomes within cultivation
            cult_interface_det_ids = (
                self.cult_detector_ids + self.interface_detector_ids
            )
            cult_success = ~np.any(detector_outcomes[:, cult_interface_det_ids], axis=1)

            detector_outcomes = detector_outcomes[cult_success, :]

        # First round
        num_logical_classes = (
            len(all_logical_values)
            if self.comparative_decoding and logical_value is None
            else 1
        )
        error_preds_stage1_all = []
        if verbose:
            print("First-round decoding:")
        for i in range(num_logical_classes):
            error_preds_stage1_all.append({})
            for c in colors:
                if verbose:
                    print(f"    > logical class {i}, color {c}...")
                if self.comparative_decoding:
                    detector_outcomes_copy = detector_outcomes.copy()
                    if logical_value is not None:
                        detector_outcomes_copy[:, -num_obs:] = logical_value
                    else:
                        detector_outcomes_copy[:, -num_obs:] = all_logical_values[i]
                    error_preds_stage1_all[i][c] = self._decode_stage1(
                        detector_outcomes_copy, c
                    )
                else:
                    error_preds_stage1_all[i][c] = self._decode_stage1(
                        detector_outcomes, c
                    )

        # Erasure matcher predecoding
        if erasure_matcher_predecoding:
            assert len(error_preds_stage1_all) > 1

            if verbose:
                print("Erasure matcher predecoding:")
            (
                predecoding_obs_preds,
                predecoding_error_preds,  # in self.dem_xz
                predecoding_weights,
                predecoding_success,
            ) = self._erasure_matcher_predecoding(
                error_preds_stage1_all, detector_outcomes
            )

            predecoding_failure = ~predecoding_success
            detector_outcomes_left = detector_outcomes[predecoding_failure, :]
            error_preds_stage1_left = [
                {
                    c: arr[predecoding_failure, :]
                    for c, arr in error_preds_stage1_all[i].items()
                }
                for i in range(len(error_preds_stage1_all))
            ]

            if verbose:
                print(
                    "    > # of samples with successful predecoding:",
                    predecoding_success.sum(),
                )

        else:
            detector_outcomes_left = detector_outcomes
            error_preds_stage1_left = error_preds_stage1_all

        # Second round
        if verbose:
            print("Second-round decoding:")

        num_left_samples = detector_outcomes_left.shape[0]
        if num_left_samples > 0 and not (
            erasure_matcher_predecoding and partial_correction_by_predecoding
        ):
            num_errors = self.H.shape[1]

            error_preds = np.empty(
                (num_logical_classes, len(colors), num_left_samples, num_errors),
                dtype=bool,
            )
            weights = np.empty(
                (num_logical_classes, len(colors), num_left_samples), dtype=float
            )
            for i in range(len(error_preds_stage1_left)):
                for i_c, c in enumerate(colors):
                    if verbose:
                        print(f"    > logical class {i}, color {c}...")
                    if self.comparative_decoding:
                        detector_outcomes_copy = detector_outcomes_left.copy()
                        if logical_value is not None:
                            detector_outcomes_copy[:, -num_obs:] = logical_value
                        else:
                            detector_outcomes_copy[:, -num_obs:] = all_logical_values[i]
                        error_preds_new, weights_new = self._decode_stage2(
                            detector_outcomes_copy, error_preds_stage1_left[i][c], c
                        )
                    else:
                        error_preds_new, weights_new = self._decode_stage2(
                            detector_outcomes_left, error_preds_stage1_left[i][c], c
                        )

                    # Adjust to fit the original error order in self.dem_xz
                    error_preds_new = self.dems_decomposed[c].map_errors_to_org_dem(
                        error_preds_new, stage=2
                    )

                    error_preds[i, i_c, :, :] = error_preds_new
                    weights[i, i_c, :] = weights_new

            # Obtain best prediction for each logical class
            # 1D arrays of int / int / float / float
            best_logical_classes, best_color_inds, weights_final, logical_gaps = (
                _get_final_predictions(weights)
            )

            error_preds_final = error_preds[
                best_logical_classes, best_color_inds, np.arange(num_left_samples), :
            ]

            if self.comparative_decoding:
                if logical_value is None:
                    # Retrieve observable predictions from best_logical_classes
                    obs_preds_final = all_logical_values[best_logical_classes]
                    assert obs_preds_final.shape == (num_left_samples, num_obs)

                else:
                    # We already know the logical value
                    obs_preds_final = np.tile(logical_value, (num_left_samples, 1))

            else:
                # Need to calculate observable predictions from error predictions
                obs_preds_final = np.empty((num_left_samples, num_obs), dtype=bool)
                for i_c, c in enumerate(colors):
                    obs_matrix = self.obs_matrix
                    # obs_matrix = self.dems_decomposed[c].obs_matrix_stage2
                    mask = best_color_inds == i_c
                    obs_preds_final[mask, :] = (
                        (error_preds_final[mask, :].astype("uint8") @ obs_matrix.T) % 2
                    ).astype(bool)

            # Adjust best_colors in case colors != ["r", "g", "b"]
            if colors == ["r", "g", "b"]:
                best_colors = best_color_inds
            else:
                best_colors = np.array([self.color_to_color_val(c) for c in colors])[
                    best_color_inds
                ]

        elif (
            num_left_samples > 0
            and erasure_matcher_predecoding
            and partial_correction_by_predecoding
        ):
            # Apply partial correction based on the predecoding results and then run
            # the decoder again.

            predecoding_error_preds_failed = predecoding_error_preds[
                predecoding_failure, :
            ].astype("uint8")

            def get_partial_corr(matrix):
                corr = (predecoding_error_preds_failed @ matrix.T) % 2
                return corr.astype(bool)

            obs_partial_corr = get_partial_corr(self.obs_matrix)
            det_partial_corr = get_partial_corr(self.H)
            detector_outcomes_left ^= det_partial_corr

            obs_preds_final = self.decode(
                detector_outcomes_left,
                colors=colors,
                full_output=full_output,
            )
            if full_output:
                obs_preds_final, extra_outputs = obs_preds_final
            else:
                extra_outputs = {}

            if obs_preds_final.ndim == 1:
                obs_preds_final = obs_preds_final[:, np.newaxis]

            if full_output:
                error_preds_final = extra_outputs["error_preds"]
                best_colors = extra_outputs["best_colors"]
                weights_final = extra_outputs["weights"]
                logical_gaps = extra_outputs["logical_gaps"]

        else:
            error_preds_final = np.array([[]], dtype=bool)
            obs_preds_final = np.array([[]], dtype=bool)
            best_colors = np.array([], dtype=np.uint8)
            weights_final = np.array([], dtype=float)
            logical_gaps = np.array([], dtype=float)

        # Merge predecoding & second-round decoding outcomes
        if erasure_matcher_predecoding and np.any(predecoding_success):
            if verbose:
                print("Merging predecoding & second-round decoding outcomes")
            # For samples with successful predecoding, use the predecoding results
            full_obs_preds_final = predecoding_obs_preds.copy()
            if full_output:
                full_best_colors = np.full(detector_outcomes.shape[0], "P")
                full_weights_final = predecoding_weights.copy()
                full_logical_gaps = np.full(detector_outcomes.shape[0], -1)
                full_error_preds_final = predecoding_error_preds.copy()

            # For samples with failed predecoding, use the second-round decoding results
            if detector_outcomes_left.shape[0] > 0:
                if partial_correction_by_predecoding:
                    # Apply partial correction
                    obs_preds_final ^= obs_partial_corr
                    if full_output:
                        error_preds_final ^= predecoding_error_preds_failed.astype(bool)

                full_obs_preds_final[predecoding_failure, :] = obs_preds_final

                if full_output:
                    full_best_colors[predecoding_failure] = best_colors
                    full_weights_final[predecoding_failure] = weights_final
                    full_logical_gaps[predecoding_failure] = logical_gaps
                    full_error_preds_final[predecoding_failure, :] = error_preds_final

            obs_preds_final = full_obs_preds_final
            if full_output:
                best_colors = full_best_colors
                weights_final = full_weights_final
                logical_gaps = full_logical_gaps
                error_preds_final = full_error_preds_final

        if check_validity:
            det_preds = (error_preds_final.astype("uint8") @ self.H.T % 2).astype(bool)
            validity = np.all(det_preds == detector_outcomes, axis=1)
            if verbose:
                if np.all(validity):
                    print("All predictions are valid")
                else:
                    print(f"{np.sum(~validity)} invalid predictions found!")

        if obs_preds_final.shape[1] == 1:
            obs_preds_final = obs_preds_final.ravel()

        if full_output:
            extra_outputs = {
                "best_colors": best_colors,
                "weights": weights_final,
                "error_preds": error_preds_final,
            }

            if len(error_preds_stage1_all) > 1:
                extra_outputs["logical_gaps"] = logical_gaps
                extra_outputs["logical_values"] = all_logical_values
                if erasure_matcher_predecoding:
                    extra_outputs["erasure_matcher_success"] = predecoding_success
                    extra_outputs["predecoding_error_preds"] = predecoding_error_preds
                    extra_outputs["predecoding_obs_preds"] = predecoding_obs_preds
            if self.circuit_type == "cult+growing":
                extra_outputs["cult_success"] = cult_success

            if check_validity:
                extra_outputs["validity"] = validity

        if full_output:
            return obs_preds_final, extra_outputs
        else:
            return obs_preds_final

    def _decode_stage1(self, detector_outcomes: np.ndarray, color: str) -> np.ndarray:
        det_outcomes_dem1 = detector_outcomes.copy()
        H, p = self.dems_decomposed[color].Hs[0], self.dems_decomposed[color].probs[0]
        checks_to_keep = H.tocsr().getnnz(axis=1) > 0
        det_outcomes_dem1 = det_outcomes_dem1[:, checks_to_keep]
        H = H[checks_to_keep, :]
        weights = np.log((1 - p) / p)
        matching = pymatching.Matching.from_check_matrix(H, weights=weights)
        preds_dem1 = matching.decode_batch(det_outcomes_dem1)
        del det_outcomes_dem1, matching

        return preds_dem1

    def _decode_stage2(
        self,
        detector_outcomes: np.ndarray,
        preds_dem1: np.ndarray,
        color: COLOR_LABEL,
    ) -> Tuple[np.ndarray, np.ndarray]:
        det_outcome_dem2 = detector_outcomes.copy()
        mask = np.full_like(det_outcome_dem2, True)
        mask[:, self.detector_ids_by_color[color]] = False
        det_outcome_dem2[mask] = False
        del mask
        det_outcome_dem2 = np.concatenate([det_outcome_dem2, preds_dem1], axis=1)

        H, p = self.dems_decomposed[color].Hs[1], self.dems_decomposed[color].probs[1]
        weights = np.log((1 - p) / p)
        matching = pymatching.Matching.from_check_matrix(H, weights=weights)
        preds, weights_new = matching.decode_batch(
            det_outcome_dem2, return_weights=True
        )
        return preds, weights_new

    def _find_error_set_intersection(
        self,
        preds_dem1: Dict[COLOR_LABEL, np.ndarray],
    ) -> np.ndarray:
        """
        Find the intersection of the error sets of the different colors.
        """
        possible_errors = []
        for c in ["r", "g", "b"]:
            preds_dem1_c = preds_dem1[c]
            error_map_matrix = self.dems_sym_decomposed[c][0].error_map_matrix
            possible_errors_c = (preds_dem1_c.astype("uint8") @ error_map_matrix) > 0
            possible_errors.append(possible_errors_c)
        possible_errors = np.stack(possible_errors, axis=-1)

        # 2D array of bool with shape (num_samples, num_errors)
        error_set_intersection = np.all(possible_errors, axis=-1).astype(bool)

        return error_set_intersection

    def _erasure_matcher_predecoding(
        self,
        preds_dem1_all: List[Dict[COLOR_LABEL, np.ndarray]],
        detector_outcomes: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Predecoding using the erasure matcher method.

        Parameters
        ----------
        preds_dem1_all : List[Dict[COLOR_LABEL, numpy array of bool/int]]
            Predictions from the first round of decoding.
            `preds_dem1_all[i][c]`: 2D array with shape (number of samples, number of errors in DEM1 for color `c`) that contains the predictions for the i-th logical class and the color `c`.
        detector_outcomes : 2D numpy array of bool/int
            Detector outcomes with shape (number of samples, number of detectors)

        Returns
        -------
        obs_preds : 2D numpy array of bool
            Observable predictions with shape (number of samples, number of observables).
        error_preds : 2D numpy array of bool
            Error predictions with shape (number of samples, number of errors).
        weights : 1D numpy array of float
            Prediction weights with shape (number of samples,).
        validity : 1D numpy array of bool
            Validity of the predictions with shape (number of samples,).
            For samples with no valid predictions, `obs_preds`, `error_preds`,
            and `weights` correspond to the smallest-weight invalid predictions.
        """

        detector_outcomes = np.asarray(detector_outcomes, dtype=bool)

        # All combinations of logical values (logical classes)
        all_logical_values = list(itertools.product([False, True], repeat=self.num_obs))
        all_logical_values = np.array(all_logical_values)

        ## Calculate the error set intersection and weights for each logical class
        error_preds_all = []
        weights_all = []
        for preds_dem1 in preds_dem1_all:
            error_preds = self._find_error_set_intersection(preds_dem1)
            llrs_all = np.log((1 - self.probs_xz) / self.probs_xz)
            llrs = np.zeros_like(error_preds, dtype=float)
            llrs[error_preds] = llrs_all[np.where(error_preds)[1]]
            weights = llrs.sum(axis=1)
            error_preds_all.append(error_preds)
            weights_all.append(weights)

        # (num_samples, num_logical_classes, num_errors), bool
        error_preds_all = np.stack(error_preds_all, axis=1)
        # (num_samples, num_logical_classes), float
        weights_all = np.stack(weights_all, axis=1)

        num_samples = error_preds_all.shape[0]

        ## Indices of logical classes sorted by prediction weight
        # (num_samples, num_logical_classes), int
        inds_logical_class_sorted = np.argsort(weights_all, axis=1)

        ## Error predictions for each sample, sorted by prediction weight
        # (num_samples, num_logical_classes, num_errors), uint8
        error_preds_all_sorted = error_preds_all[
            np.arange(num_samples)[:, np.newaxis], inds_logical_class_sorted
        ].astype("uint8")

        ## Weight for each sample, sorted by prediction weight
        # (num_samples, num_logical_classes), float
        weights_all_sorted = np.take_along_axis(
            weights_all, inds_logical_class_sorted, axis=1
        )

        ## Check if the predictions are valid (match with detectors & observables)
        # (num_samples, num_logical_classes), bool
        match_with_dets = np.all(
            ((error_preds_all_sorted @ self.H.T.toarray()) % 2).astype(bool)
            == detector_outcomes[:, np.newaxis, :],
            axis=-1,
        )
        # (num_samples, num_logical_classes, num_obs), bool
        logical_classes_sorted = all_logical_values[inds_logical_class_sorted]
        # (num_samples, num_logical_classes), bool
        match_with_obss = np.all(
            ((error_preds_all_sorted @ self.obs_matrix.T.toarray()) % 2).astype(bool)
            == logical_classes_sorted,
            axis=-1,
        )
        # (num_samples, num_logical_classes), bool
        validity_full = match_with_dets & match_with_obss

        ## Determine observable predictions among valid predictions for each sample
        # (num_samples,), int
        inds_first_valid_logical_classes = np.argmax(validity_full, axis=1)
        # (num_samples, num_obs), bool
        obs_preds = logical_classes_sorted[
            np.arange(num_samples), inds_first_valid_logical_classes, :
        ]
        # (num_samples,), bool
        validity = np.any(validity_full, axis=1)

        # Prediction weights
        # (num_samples,), float
        weights = weights_all_sorted[
            np.arange(num_samples), inds_first_valid_logical_classes
        ]
        weights[~validity] = np.inf

        # Prediction errors
        # (num_samples, num_errors), bool
        error_preds = error_preds_all_sorted[
            np.arange(num_samples), inds_first_valid_logical_classes, :
        ]

        return obs_preds, error_preds, weights, validity

    def sample(
        self, shots: int, seed: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sample detector outcomes and observables from the quantum circuit.

        Parameters
        ----------
        shots : int
            Number of samples to generate
        seed : int, optional
            Seed value to initialize the random number generator

        Returns
        -------
        det : 2D numpy array of bool
            Detector outcomes. det[i,j] is True if and only if the detector
            with id j in the i-th sample has an outcome of −1.
        obs : 1D or 2D numpy array of bool
            Observable outcomes. If there is only one observable, returns a 1D array;
            otherwise returns a 2D array. obs[i] or obs[i,j] is True if and only if
            the j-th observable (j=0 when 1D) of the i-th sample has an outcome of -1.
        """
        sampler = self.circuit.compile_detector_sampler(seed=seed)
        det, obs = sampler.sample(shots, separate_observables=True)
        if obs.shape[1] == 1:
            obs = obs.ravel()
        return det, obs

    def sample_with_errors(
        self,
        shots: int,
        seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Sample detector outcomes, observables, and errors from the quantum circuit.

        Parameters
        ----------
        shots : int
            Number of samples to generate
        seed : int, optional
            Seed value to initialize the random number generator

        Returns
        -------
        det : 2D numpy array of bool
            Detector outcomes. det[i,j] is True if and only if the detector
            with id j in the i-th sample has an outcome of −1.
        obs : 1D or 2D numpy array of bool
            Observable outcomes. If there is only one observable, returns a 1D array;
            otherwise returns a 2D array. obs[i] or obs[i,j] is True if and only if
            the j-th observable (j=0 when 1D) of the i-th sample has an outcome of -1.
        errors : 2D numpy array of bool
            Errors sampled from the quantum circuit. errors[i,j] is True if and only if
            the j-th error (in the DEM) of the i-th sample has an outcome of -1.
        """
        dem = self.circuit.detector_error_model()
        sampler = dem.compile_sampler(seed=seed)
        det, obs, err = sampler.sample(shots, return_errors=True)
        if obs.shape[1] == 1:
            obs = obs.ravel()

        return det, obs, err

    def errors_to_qubits(
        self,
        errors: np.ndarray,
    ) -> np.ndarray:
        """
        Convert errors (generated by `self.sample_with_errors`) or error predictions
        (generated by `self.decode` or `self.simulate`) into the corresponding data
        qubit indices.

        Available only for `tri` and `rec` circuit types with `rounds=1` under
        bit-flip noise (i.e., probabilities besides `p_bitflip` are 0).

        Note: Errors and error predictions from `self.sample_with_errors`,
        `self.decode`, or `self.simulate` follow the ordering of error mechanisms
        in the circuit's detector error model (`self.circuit.detector_error_model()`).
        This function is necessary because this ordering differs from the data qubit
        ordering in the tanner graph (`self.tanner_graph.vs.select(pauli=None)`).
        This conversion is especially helpful when visualizing errors or error
        predictions on the lattice with `self.draw_lattice()`.

        Parameters
        ----------
        errors : 2D numpy array of bool
            Errors following the ordering of error mechanisms in the DEM of the circuit
            `self.circuit.detector_error_model()`.

        Returns
        -------
        errors_qubits : 2D numpy array of bool
            Errors following the ordering of data qubits in the tanner graph
            `self.tanner_graph.vs.select(pauli=None)`.
        """

        if self.circuit_type not in {"tri", "rec"}:
            raise NotImplementedError(
                f'errors_to_qubits is not available for "{self.circuit_type}" circuit type.'
            )

        if self.rounds != 1:
            raise NotImplementedError(
                "errors_to_qubits is only available when rounds = 1."
            )

        if any(
            prob > 0 for key, prob in self.physical_probs.items() if key != "bitflip"
        ):
            raise NotImplementedError(
                "errors_to_qubits is only available under bit-flip noise "
                "(only p_bitflip is nonzero)."
            )

        # set of ancillary qubits - data qubit mapping
        anc_qids_to_data_qubit_idx = {}
        data_qubits = self.tanner_graph.vs.select(pauli=None)
        for i_dq, data_qubit in enumerate(data_qubits):
            data_qubit: ig.Vertex
            connected_anc_qubits = data_qubit.neighbors()
            connected_anc_qubits = [
                q for q in connected_anc_qubits if q["pauli"] == "Z"
            ]
            key = frozenset(q.index for q in connected_anc_qubits)
            assert key not in anc_qids_to_data_qubit_idx
            anc_qids_to_data_qubit_idx[key] = i_dq

        # data qubit mapping - error mechanism in DEM
        dem = self.circuit.detector_error_model()
        data_qubit_idx_to_em = np.full(len(data_qubits), -1, dtype="int32")
        for i_em, em in enumerate(dem):
            if em.type == "error":
                det_ids = [
                    int(str(target)[1:])
                    for target in em.targets_copy()
                    if target.is_relative_detector_id()
                ]
                anc_qids = [
                    self.get_detector(det_id)[0].index
                    for det_id in det_ids
                    if det_id < len(self.detectors_checks_map)
                ]
                anc_qids = frozenset(anc_qids)
                data_qubit_idx = anc_qids_to_data_qubit_idx[anc_qids]
                if data_qubit_idx_to_em[data_qubit_idx] != -1:
                    raise ValueError(
                        f"Data qubit {data_qubit_idx} is mapped to multiple error mechanisms: {data_qubit_idx_to_em[data_qubit_idx]} and {i_em}"
                    )
                data_qubit_idx_to_em[data_qubit_idx] = i_em
        assert np.all(data_qubit_idx_to_em != -1)

        return errors[..., data_qubit_idx_to_em]

    def simulate(
        self,
        shots: int,
        *,
        bp_predecoding: bool = False,
        bp_prms: dict | None = None,
        erasure_matcher_predecoding: bool = False,
        partial_correction_by_predecoding: bool = False,
        colors: Union[List[str], str] = "all",
        alpha: float = 0.01,
        confint_method: str = "wilson",
        full_output: bool = False,
        seed: Optional[int] = None,
        verbose: bool = False,
        **kwargs,
    ) -> Tuple[np.ndarray, dict]:
        """
        Monte-Carlo simulation of the concatenated MWPM decoder.

        Parameters
        ----------
        shots : int
            Number of shots to simulate.
        bp_predecoding : bool, default False
            If True, use belief propagation for predecoding.
        bp_prms : dict | None, default None
            Parameters for belief propagation predecoding.
        erasure_matcher_predecoding : bool, default False
            If True, use erasure matcher predecoding to identify errors common to all colors.
        partial_correction_by_predecoding : bool, default False
            If True, apply partial correction using predecoding results when erasure matcher predecoding fails.
        colors : Union[List[str], str], default 'all'
            Colors of the sub-decoding procedures to consider. Can be 'all', one of {'r', 'g', 'b'},
            or a list containing any combination of {'r', 'g', 'b'}.
        alpha : float, default 0.01
            Significance level for the confidence interval calculation.
        confint_method : str, default 'wilson'
            Method to calculate the confidence interval.
            See statsmodels.stats.proportion.proportion_confint for available options.
        full_output: bool = False,
            If True, return additional information.
        seed : Optional[int], default None
            Seed to initialize the random number generator.
        verbose : bool, default False
            If True, print progress information during simulation.
        **kwargs :
            Additional keyword arguments for the decoder (see `ColorCode.decode()`).

        Returns
        -------
        num_fails : numpy.ndarray
            Number of failures for each observable.
        extra_outputs : dict, optional
            Dictionary containing additional information:
            - 'stats': Tuple of (pfail, delta_pfail) where pfail is the estimated failure rate
              and delta_pfail is the half-width of the confidence interval
            - 'fails': Boolean array indicating which samples failed
            - 'logical_gaps': Array of logical gaps (only when self.logical_gap is True)
            - etc.
        """
        if self.circuit_type == "cult+growing":
            raise NotImplementedError(
                "Cult+growing circuit type is not supported for this method."
            )

        if colors == "all":
            colors = ["r", "g", "b"]

        if verbose:
            print("Sampling...")

        shots = round(shots)
        det, obs = self.sample(shots, seed=seed)

        if verbose:
            print("Decoding...")

        preds = self.decode(
            det,
            verbose=verbose,
            bp_predecoding=bp_predecoding,
            bp_prms=bp_prms,
            full_output=full_output,
            erasure_matcher_predecoding=erasure_matcher_predecoding,
            partial_correction_by_predecoding=partial_correction_by_predecoding,
            **kwargs,
        )

        if full_output:
            preds, extra_outputs = preds

        if verbose:
            print("Postprocessing...")

        fails = np.logical_xor(obs, preds)
        num_fails = np.sum(fails, axis=0)

        if full_output:
            pfail, delta_pfail = get_pfail(
                shots, num_fails, alpha=alpha, confint_method=confint_method
            )
            extra_outputs["stats"] = (pfail, delta_pfail)
            extra_outputs["fails"] = fails

            return num_fails, extra_outputs

        else:
            return num_fails

    def simulate_target_confint_gen(
        self,
        tol: Optional[float] = None,
        tol_zx: Optional[float] = None,
        rel_tol: Optional[float] = None,
        init_shots: int = 10_000,
        max_shots: Optional[int] = 160_000,
        max_time_per_round: Optional[int] = 600,
        max_time_total: Optional[int] = None,
        shots_mul_factor: int = 2,
        alpha: float = 0.01,
        confint_method: str = "wilson",
        color: Union[List[str], str] = "all",
        pregiven_shots: int = 0,
        pregiven_fails: int = 0,
        pfail_lower_bound: Optional[float] = None,
        verbose: bool = False,
    ):
        assert tol is not None or rel_tol is not None or tol_zx is not None

        shots_now = init_shots
        shots_total = pregiven_shots
        fails_total = pregiven_fails

        if shots_total > 0:
            pfail_low, pfail_high = proportion_confint(
                fails_total, shots_total, alpha=alpha, method=confint_method
            )
            pfail = (pfail_low + pfail_high) / 2
            delta_pfail = pfail_high - pfail

            if (
                (rel_tol is None or np.all(delta_pfail / pfail < rel_tol))
                and (tol is None or np.all(delta_pfail < tol))
                and (
                    tol_zx is None
                    or np.all(delta_pfail * np.sqrt(2 * (1 - pfail)) <= tol_zx)
                )
            ):
                res = pfail, delta_pfail, shots_total, fails_total
                yield res

        t0_total = time.time()
        trial = 0
        while True:
            if verbose:
                print(f"Sampling {shots_now} samples...", end="")
            t0 = time.time()
            fails_now = self.simulate(shots_now, colors=color)
            shots_total += shots_now
            fails_total += fails_now

            pfail, delta_pfail = get_pfail(
                shots_total, fails_total, alpha=alpha, confint_method=confint_method
            )

            res = pfail, delta_pfail, shots_total, fails_total
            yield res

            time_taken = time.time() - t0

            if verbose:
                if np.ndim(pfail) == 0:
                    print(
                        f" Result: {pfail:.2%} +- {delta_pfail:.2%} "
                        f"({time_taken}s taken)"
                    )
                else:
                    print(" Result: ", end="")
                    for pfail_indv, delta_pfail_indv in zip(pfail, delta_pfail):
                        print(f"{pfail_indv:.2%} +- {delta_pfail_indv:.2%}, ", end="")
                    print(f"({time_taken}s taken)")

            if (
                (rel_tol is None or np.all(delta_pfail / pfail < rel_tol))
                and (tol is None or np.all(delta_pfail < tol))
                and (
                    tol_zx is None
                    or np.all(delta_pfail * np.sqrt(2 * (1 - pfail)) <= tol_zx)
                )
            ):
                break

            if (
                trial > 0
                and max_time_total is not None
                and time.time() - t0_total >= max_time_total
            ):
                break

            if pfail_lower_bound is not None and np.all(pfail_high < pfail_lower_bound):
                break

            not_reach_max_shots = (
                max_shots is None or shots_now * shots_mul_factor <= max_shots
            )
            not_reach_max_time = (
                max_time_per_round is None
                or time_taken * shots_mul_factor <= max_time_per_round
            )

            if not_reach_max_time and not_reach_max_shots:
                shots_now *= shots_mul_factor

            trial += 1

    def simulate_target_confint(self, *args, **kwargs):
        for res in self.simulate_target_confint_gen(*args, **kwargs):
            pass
        return res

    # ----- Save/Load Methods -----

    def save(self, path: str):
        """
        Save the ColorCode object to a file using pickle.

        Excludes non-picklable attributes: `detectors_checks_map`, `qubit_groups`,
        `dems_decomposed`, and `_bp_inputs`. These will be reconstructed upon loading.

        Parameters
        ----------
        path : str
            The file path where the object should be saved.
        """
        data = self.__dict__.copy()
        # Attributes to exclude from pickling
        excluded_keys = [
            "detectors_checks_map",
            "qubit_groups",
            "dems_decomposed",
            "_bp_inputs",
        ]
        for key in excluded_keys:
            if key in data:
                del data[key]

        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "ColorCode":
        """
        Load a ColorCode object from a file saved by the `save` method.

        Reconstructs non-picklable attributes excluded during saving.

        Parameters
        ----------
        path : str
            The file path from which to load the object.

        Returns
        -------
        ColorCode
            The loaded ColorCode object.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        # Create a new instance without calling __init__
        instance = cls.__new__(cls)
        instance.__dict__.update(data)

        # Reconstruct non-picklable attributes
        try:
            instance._reconstruct_qubit_groups()
            instance._reconstruct_detectors_checks_map()
            instance._reconstruct_dems_decomposed()
            instance._bp_inputs = {}  # Initialize empty cache
        except Exception as e:
            print(f"Error during reconstruction: {e}")
            # Depending on desired behavior, you might re-raise or handle differently
            raise

        return instance

    def _reconstruct_qubit_groups(self):
        """Helper method to reconstruct the qubit_groups attribute after loading."""
        tanner_graph = self.tanner_graph
        data_qubits = tanner_graph.vs.select(pauli=None)
        anc_qubits = tanner_graph.vs.select(pauli_ne=None)
        anc_Z_qubits = anc_qubits.select(pauli="Z")
        anc_X_qubits = anc_qubits.select(pauli="X")
        anc_red_qubits = anc_qubits.select(color="r")
        anc_green_qubits = anc_qubits.select(color="g")
        anc_blue_qubits = anc_qubits.select(color="b")

        self.qubit_groups = {
            "data": data_qubits,
            "anc": anc_qubits,
            "anc_Z": anc_Z_qubits,
            "anc_X": anc_X_qubits,
            "anc_red": anc_red_qubits,
            "anc_green": anc_green_qubits,
            "anc_blue": anc_blue_qubits,
        }

    def _reconstruct_detectors_checks_map(self):
        """Helper method to reconstruct the detectors_checks_map attribute after loading."""
        (
            detector_ids_by_color,
            cult_detector_ids,
            interface_detector_ids,
            detectors_checks_map,
        ) = self._generate_det_id_info()
        # These attributes might have been loaded, update them if necessary
        # or ensure consistency if they were *not* saved.
        self.detector_ids_by_color = detector_ids_by_color
        self.cult_detector_ids = cult_detector_ids
        self.interface_detector_ids = interface_detector_ids
        self.detectors_checks_map = detectors_checks_map

    def _reconstruct_dems_decomposed(self):
        """Helper method to reconstruct the dems_decomposed attribute after loading."""
        self.dems_decomposed = {}
        for c in ["r", "g", "b"]:
            try:
                # Assuming DemDecomp class is available in the scope
                dem_decomp = DemDecomp(
                    org_dem=self.dem_xz,
                    color=c,
                    remove_non_edge_like_errors=self.remove_non_edge_like_errors,
                )
                self.dems_decomposed[c] = dem_decomp
            except Exception as e:
                print(f"Error reconstructing DemDecomp for color {c}: {e}")
                # Handle error as appropriate, maybe skip this color
                pass
