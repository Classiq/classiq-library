# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from gen._circuit_util import (
    gates_used_by_circuit,
    gate_counts_for_circuit,
    count_measurement_layers,
)
from gen._core import (
    AtLayer,
    Builder,
    complex_key,
    MeasurementTracker,
    min_max_complex,
    NoiseModel,
    NoiseRule,
    occurs_in_classical_control_system,
    Patch,
    PauliString,
    sorted_complex,
    StabilizerCode,
    Tile,
)
from gen._flows import (
    Chunk,
    ChunkLoop,
    Flow,
    compile_chunks_into_circuit,
    magic_measure_for_flows,
    FlowStabilizerVerifier,
)
from gen._layers import (
    transpile_to_z_basis_interaction_circuit,
)
from gen._surf import (
    ClosedCurve,
    CssObservableBoundaryPair,
    StepSequenceOutline,
    int_points_on_line,
    int_points_inside_polygon,
    checkerboard_basis,
    Order_Z,
    Order_ᴎ,
    Order_N,
    Order_S,
    PatchOutline,
    layer_begin,
    layer_loop,
    layer_transition,
    layer_end,
    layer_single_shot,
    surface_code_patch,
    PathOutline,
    build_patch_to_patch_surface_code_transition_rounds,
    PatchTransitionOutline,
    StepOutline,
)
from gen._util import (
    stim_circuit_with_transformed_coords,
    estimate_qubit_count_during_postselection,
    write_file,
)
from gen._viz_circuit_html import (
    stim_circuit_html_viewer,
)
from gen._viz_patch_svg import (
    patch_svg_viewer,
    is_colinear,
    svg_path_directions_for_tile,
)
