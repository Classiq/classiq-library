"""Point 3: parse results via `.result_value()`, not `.result()[0].value`.

Raw substring replace (the chars are not JSON-escaped inside .ipynb), so the
notebook diff is exactly the changed line(s) — nothing else is reserialized.
`.result()[0].value`        -> `.result_value()`
`.result()[0].value.counts` -> `.result_value().counts`   (suffix preserved)
"""

OLD = ".result()[0].value"
NEW = ".result_value()"

MAIN = [
    "algorithms/quantum_primitives/hadamard_test/hadamard_test.ipynb",
    "applications/image_processing/quantum_hadamard_edge_detection/quantum_image_edge_detection.ipynb",
    "applications/optimization/qaoa_in_qaoa/qaoa_in_qaoa.ipynb",
    "tutorials/basic_tutorials/quantum_primitives/hadamard_test_tutorial/hadamard_test_tutorial.ipynb",
]
COMMUNITY = [
    "community/paper_implementation_project/Block_encoding-ND_Laplacian/ND_Laplacian_BE.ipynb",
    "community/paper_implementation_project/block_encoding/select_structures_BE.ipynb",
    "community/paper_implementation_project/explicit_quantum_circuits_for_block_encoding/quantum_walks_via_efficient_blockencoding.ipynb",
    "community/paper_implementation_project/quantum_compression_algorithm_for_symmetric_states/quantum_compression_algorithm_for_symmetric_states.ipynb",
]


def fix(path: str) -> int:
    text = open(path).read()
    count = text.count(OLD)
    if count:
        open(path, "w").write(text.replace(OLD, NEW))
    return count


for label, files in (("MAIN", MAIN), ("COMMUNITY", COMMUNITY)):
    print(label)
    for path in files:
        print(f"  {fix(path):2d}  {path}")
