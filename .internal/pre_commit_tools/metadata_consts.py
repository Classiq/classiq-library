#
# Configuration
#
class Config:
    # if `DISABLED` is True, then nothing runs, and all the other flags are ignored.
    IS_DISABLED: bool = False

    # if `AUTO_FIX` is True, then the script
    #   will automatically generate missing metadata files,
    #   and will automatically delete un-needed metadata files
    SHOULD_AUTO_FIX: bool = True

    # if `VALIDATE_CONTENT` is False, then the only check will be "does a file exist"
    #   and no content validation will happen
    SHOULD_VALIDATE_METADATA_CONTENT: bool = True

    # if `SKIP_MISSING` is True, then only existing fields will be validated
    SHOULD_SKIP_MISSING_FIELDS: bool = True

    # if `ALLOW_EXTRA_FIELDS` is False, then extra fields will be treated as errors
    SHOULD_ALLOW_EXTRA_FIELDS: bool = False

    # if `VALIDATE_SAME_NAME` is True, then, in the case where a folder has
    #   a single `ipynb` file and a single `.qmod` file
    #   then this pre-commit will enforce that they will have the same file name
    SHOULD_VALIDATE_SAME_NAME: bool = True

    # if `CLEAN_LEFTOVER` is True, then we will automatically delete un-needed metadata files
    #   (and, if after deleting them, they will have an empty directory, it will also be deleted)
    #   note that if `AUTO_FIX` is False, then we will not delete, we will only raise an error
    SHOULD_CLEAN_LEFTOVER_METADATA: bool = True


FILES_TO_NOT_GENERATE_METADATA = [
    "pennylane_cat_qsvt_example.ipynb",
    "qiskit_qsvt.ipynb",
    "tket_qsvt_example.ipynb",
    "pennylane_catalyst_discrete_quantum_walk.ipynb",
    "qiskit_discrete_quantum_walk.ipynb",
    "tket_discrete_quantum_walk.ipynb",
    "resiliency_planning_AMD.ipynb",
]
FILES_TO_IGNORE_SAME_NAME = [
    "qaoa.ipynb",
]
