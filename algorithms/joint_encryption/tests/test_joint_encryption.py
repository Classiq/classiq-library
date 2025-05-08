import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def test_joint_encryption_notebook_runs():
    # Load the notebook
    with open("../joint_encryption.ipynb") as f:  
        nb = nbformat.read(f, as_version=4)
    
    # Execute the notebook
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': './'}})