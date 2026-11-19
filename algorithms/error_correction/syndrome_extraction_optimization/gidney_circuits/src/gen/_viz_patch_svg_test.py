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

import gen


def test_patch_svg_exact():
    patch = gen.Patch(
        tiles=[
            gen.Tile(
                ordered_data_qubits=(None, 1j, None, 2j),
                measurement_qubit=(-0.5 + 1.5j),
                bases="Z",
            ),
            gen.Tile(
                ordered_data_qubits=(None, 0j, None, (1 + 0j)),
                measurement_qubit=(0.5 - 0.5j),
                bases="X",
            ),
            gen.Tile(
                ordered_data_qubits=(0j, (1 + 0j), 1j, (1 + 1j)),
                measurement_qubit=(0.5 + 0.5j),
                bases="Z",
            ),
            gen.Tile(
                ordered_data_qubits=(1j, 2j, (1 + 1j), (1 + 2j)),
                measurement_qubit=(0.5 + 1.5j),
                bases="X",
            ),
            gen.Tile(
                ordered_data_qubits=((1 + 0j), (1 + 1j), (2 + 0j), (2 + 1j)),
                measurement_qubit=(1.5 + 0.5j),
                bases="X",
            ),
            gen.Tile(
                ordered_data_qubits=((1 + 1j), (2 + 1j), (1 + 2j), (2 + 2j)),
                measurement_qubit=(1.5 + 1.5j),
                bases="Z",
            ),
            gen.Tile(
                ordered_data_qubits=((1 + 2j), None, (2 + 2j), None),
                measurement_qubit=(1.5 + 2.5j),
                bases="X",
            ),
            gen.Tile(
                ordered_data_qubits=((2 + 0j), None, (2 + 1j), None),
                measurement_qubit=(2.5 + 0.5j),
                bases="Z",
            ),
        ]
    )
    svg_content = gen.patch_svg_viewer([patch])
    assert (
        svg_content.strip()
        == """
<svg viewBox="0 0 1400 500" xmlns="http://www.w3.org/2000/svg">
<rect fill="#FF8080" x="1" y="1" width="20" height="20" />
<text x="11" y="11" fill="white" font-size="20" text-anchor="middle" alignment-baseline="central">X</text>
<rect fill="#8080FF" x="1" y="21" width="20" height="20" />
<text x="11" y="31" fill="white" font-size="20" text-anchor="middle" alignment-baseline="central">Z</text>
<path d="M229.16666666666666,187.5 L 229.16666666666666,104.16666666666666 L 312.5,104.16666666666666 L 312.5,187.5 L 229.16666666666666,187.5" fill="#8080FF" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M229.16666666666666,270.8333333333333 L 229.16666666666666,187.5 L 312.5,187.5 L 312.5,270.8333333333333 L 229.16666666666666,270.8333333333333" fill="#FF8080" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M312.5,187.5 L 312.5,104.16666666666666 L 395.8333333333333,104.16666666666666 L 395.8333333333333,187.5 L 312.5,187.5" fill="#FF8080" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M312.5,270.8333333333333 L 312.5,187.5 L 395.8333333333333,187.5 L 395.8333333333333,270.8333333333333 L 312.5,270.8333333333333" fill="#8080FF" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M229.16666666666666,187.5 L 229.16666666666666,104.16666666666666 L 312.5,104.16666666666666 L 312.5,187.5 L 229.16666666666666,187.5" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M229.16666666666666,270.8333333333333 L 229.16666666666666,187.5 L 312.5,187.5 L 312.5,270.8333333333333 L 229.16666666666666,270.8333333333333" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M312.5,187.5 L 312.5,104.16666666666666 L 395.8333333333333,104.16666666666666 L 395.8333333333333,187.5 L 312.5,187.5" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M312.5,270.8333333333333 L 312.5,187.5 L 395.8333333333333,187.5 L 395.8333333333333,270.8333333333333 L 312.5,270.8333333333333" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M 229.16666666666666,187.5 a 1,1 0 0,0 0.0,83.33333333333334 L 229.16666666666666,187.5" fill="#8080FF" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M 312.5,104.16666666666666 a 1,1 0 0,0 -83.33333333333334,0.0 L 312.5,104.16666666666666" fill="#FF8080" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M 312.5,270.8333333333333 a 1,1 0 0,0 83.33333333333334,0.0 L 312.5,270.8333333333333" fill="#FF8080" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M 395.8333333333333,187.5 a 1,1 0 0,0 0.0,-83.33333333333333 L 395.8333333333333,187.5" fill="#8080FF" opacity="1" stroke="none" stroke-width="1.6666666666666572"    />
<path d="M 229.16666666666666,187.5 a 1,1 0 0,0 0.0,83.33333333333334 L 229.16666666666666,187.5" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M 312.5,104.16666666666666 a 1,1 0 0,0 -83.33333333333334,0.0 L 312.5,104.16666666666666" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M 312.5,270.8333333333333 a 1,1 0 0,0 83.33333333333334,0.0 L 312.5,270.8333333333333" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<path d="M 395.8333333333333,187.5 a 1,1 0 0,0 0.0,-83.33333333333333 L 395.8333333333333,187.5" fill="none" stroke="black" stroke-width="1.6666666666666572"    />
<circle cx="270.8333333333333" cy="145.83333333333331" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="270.8333333333333" cy="229.16666666666666" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="354.16666666666663" cy="145.83333333333331" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="354.16666666666663" cy="229.16666666666666" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="187.5" cy="229.16666666666666" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="270.8333333333333" cy="62.5" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="354.16666666666663" cy="312.5" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="437.5" cy="145.83333333333331" r="8.333333333333343" fill="black" stroke-width="1.6666666666666572"   stroke="black" />
<circle cx="212.49999999999997" cy="204.16666666666666" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<circle cx="212.49999999999997" cy="229.16666666666663" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<path d="M212.49999999999997,204.16666666666666 212.49999999999997,254.16666666666663" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M212.49999999999997,260.83333333333326 205.83333333333334,254.16666666666663 219.1666666666666,254.16666666666663 212.49999999999997,260.83333333333326" stroke="none" fill="black" />
<circle cx="245.83333333333334" cy="87.5" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<circle cx="270.8333333333333" cy="87.5" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<path d="M245.83333333333334,87.5 295.8333333333333,87.5" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M302.49999999999994,87.5 295.8333333333333,94.16666666666663 295.8333333333333,80.83333333333337 302.49999999999994,87.5" stroke="none" fill="black" />
<path d="M245.83333333333334,120.83333333333333 295.8333333333333,120.83333333333333 245.83333333333334,170.83333333333331 295.8333333333333,170.83333333333331" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M302.49999999999994,170.83333333333331 295.8333333333333,177.49999999999994 295.8333333333333,164.16666666666669 302.49999999999994,170.83333333333331" stroke="none" fill="black" />
<path d="M245.83333333333334,204.16666666666666 245.83333333333334,254.16666666666663 295.8333333333333,204.16666666666666 295.8333333333333,254.16666666666663" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M295.8333333333333,260.83333333333326 289.1666666666667,254.16666666666663 302.49999999999994,254.16666666666663 295.8333333333333,260.83333333333326" stroke="none" fill="black" />
<path d="M329.1666666666667,120.83333333333333 329.1666666666667,170.83333333333331 379.16666666666663,120.83333333333333 379.16666666666663,170.83333333333331" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M379.16666666666663,177.49999999999994 372.5,170.83333333333331 385.83333333333326,170.83333333333331 379.16666666666663,177.49999999999994" stroke="none" fill="black" />
<path d="M329.1666666666667,204.16666666666666 379.16666666666663,204.16666666666666 329.1666666666667,254.16666666666663 379.16666666666663,254.16666666666663" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M385.83333333333326,254.16666666666663 379.16666666666663,260.83333333333326 379.16666666666663,247.5 385.83333333333326,254.16666666666663" stroke="none" fill="black" />
<circle cx="354.16666666666663" cy="287.5" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<path d="M329.1666666666667,287.5 379.16666666666663,287.5" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M385.83333333333326,287.5 379.16666666666663,294.16666666666663 379.16666666666663,280.83333333333337 385.83333333333326,287.5" stroke="none" fill="black" />
<circle cx="412.5" cy="145.83333333333331" r="3.333333333333333" stroke-width="1.6666666666666572" stroke="yellow" fill="none" />
<path d="M412.5,120.83333333333333 412.5,170.83333333333331" fill="none" stroke-width="1.6666666666666572" stroke="black" />
<path d="M412.5,177.49999999999994 405.83333333333337,170.83333333333331 419.16666666666663,170.83333333333331 412.5,177.49999999999994" stroke="none" fill="black" />
<rect fill="none" stroke="#999" x="112.5" y="-12.499999999999991" width="400.0" height="400.0" />
</svg>
    """.strip()
    )
