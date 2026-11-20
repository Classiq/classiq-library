import webbrowser
from classiq import *

# ==========================================
# Circuit 1: Bell State (|00> + |11>)
# ==========================================
print("[1/3] Synthesizing & Sampling Circuit 1: Bell State...")
@qfunc
def main(res: Output[QArray[QBit, 2]]):
    allocate(res)
    H(res[0])
    CX(res[0], res[1])

qprog1 = synthesize(main)
res1 = sample(qprog1)
url1 = getattr(qprog1, "circuit_url", None)
print(f"  --> Circuit 1 URL: {url1}")
try:
    show(qprog1)
except Exception:
    if url1:
        webbrowser.open(url1)

# ==========================================
# Circuit 2: GHZ State (|000> + |111>)
# ==========================================
print("[2/3] Synthesizing & Sampling Circuit 2: 3-Qubit GHZ State...")
@qfunc
def main(res: Output[QArray[QBit, 3]]):
    allocate(res)
    H(res[0])
    CX(res[0], res[1])
    CX(res[1], res[2])

qprog2 = synthesize(main)
res2 = sample(qprog2)
url2 = getattr(qprog2, "circuit_url", None)
print(f"  --> Circuit 2 URL: {url2}")
try:
    show(qprog2)
except Exception:
    if url2:
        webbrowser.open(url2)

# ==========================================
# Circuit 3: Arbitrary State Preparation
# ==========================================
print("[3/3] Synthesizing & Sampling Circuit 3: State Preparation (8 states)...")
dist = [0.3, 0.2, 0.05, 0.13, 0.15, 0.05, 0.1, 0.02]

@qfunc
def main(a: Output[QArray[QBit, 3]]):
    prepare_state(probabilities=dist, bound=0.01, out=a)

qprog3 = synthesize(main)
res3 = sample(qprog3, num_shots=10000)
url3 = getattr(qprog3, "circuit_url", None)
print(f"  --> Circuit 3 URL: {url3}")
try:
    show(qprog3)
except Exception:
    if url3:
        webbrowser.open(url3)

print("\n[OK] All 3 circuits and sampling tasks opened in browser!")
