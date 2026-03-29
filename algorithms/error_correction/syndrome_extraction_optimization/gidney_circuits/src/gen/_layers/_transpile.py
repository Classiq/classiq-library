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

import stim

from gen._layers._layer_circuit import LayerCircuit


def transpile_to_z_basis_interaction_circuit(
    circuit: stim.Circuit, *, is_entire_circuit: bool = True
) -> stim.Circuit:
    """Converts to a circuit using CZ, ISWAP, and MZZ as appropriate.

    This method mostly focuses on inserting single qubit rotations to convert
    interactions into their Z basis variant. It also does some optimizations
    that remove redundant rotations which would tend to be introduced by this
    process.
    """
    c = LayerCircuit.from_stim_circuit(circuit)
    c = c.with_qubit_coords_at_start()
    c = c.with_locally_optimized_layers()
    c = c.to_z_basis()
    c = c.with_rotations_rolled_from_end_of_loop_to_start_of_loop()
    c = c.with_locally_optimized_layers()
    c = c.with_clearable_rotation_layers_cleared()
    c = c.with_rotations_merged_earlier()
    c = c.with_rotations_before_resets_removed()
    if is_entire_circuit:
        c = c.with_irrelevant_tail_layers_removed()
    return c.to_stim_circuit()
