#SelectV

from classiq import *
from classiq.qmod.symbolic import floor
import numpy as np

#nth_to_last(0, list) == list[-1]
#def nth_to_last(n:int, list): 
#    return list[-1-n]

@qfunc
def tof_CT(b0:CBool, b1:CBool, ctl0:QBit, ctl1:QBit, target:QBit):
    
    #apply NOT to target if ctl0==b0, etc
    #keeping semantics as close to original as possible
    #within (change of basis) do CCNOT
    #Note: this was not originally its own function, but this is very difficult to write inside a lambda.
    @qfunc(generative=True)
    def basischange(b0:CBool, b1:CBool, ctl0:QBit, ctl1:QBit):
        if (not b0):
            X(ctl0)
        if (not b1):
            X(ctl1)
        return

    ctls = QArray()
    bind([ctl0,ctl1],ctls)
    within_apply(
        lambda: basischange(b0,b1,ctls[0],ctls[1]),
        lambda: control(ctrl=ctls, stmt_block=lambda: X(target))
    )
    bind(ctls,[ctl0,ctl1])
    return

#type Node = CArray[CBool]

#Compute Hamming distance; rewritten slightly from Haskell for Pythonic legibility.
#Technically possible with sum(...for ...), but this is clearer.
def distance(p1: CArray[CBool], p2:CArray[CBool]):
    return len([1 for (a,b) in zip(p1,p2) if a != b])

#Increment node to next boolstring.
#Python lists aren't linked lists, and they are mutable...
#Doing this out of place, for now.
def increment(l: CArray[CBool]) -> CArray[CBool]:
    next = l.copy()
    #flip True (1) to False (0) until we hit a False(0); then flip and break.
    for i in range (len(next)):
        if not next[i]:
            next[i] = True
            break
        else:
            next[i] = False
    return next

#Translate integer n into a length-m little-endian bitstring.
def to_node(n: int, m: int) -> list[bool]:
    return  [((n >> i) % 2 == 1) for i in range(m)]

def to_num(node: list[bool]):
    return sum(node[i] << i for i in range(len(node)))

#reverse the bits in n, flipping its endian-ness.
def reverse_endian(n: int, m: int):
    return to_num(to_node(n,m)[::-1])

#print(increment(to_node(127, 8)))
#[True, False, False...]
#print(reverse_endian(1, 8))
#128

#step to the next node in the tree, where xs are inputs and qs are ancillas.
#Precondition 1 < |bs| = |xs| = |qs| + 1.
#Childs' version is big-endian: we want little-endian...
@qfunc(generative=True)
def stepRight(n:CArray[CBool], xs:QArray, qs:QArray) -> None:
    assert xs.len == qs.len + 1
    @qfunc(generative=True)
    def stepRight_aux(n:CArray[CBool], xs:QArray, qs:QArray) -> None:
        match distance(n, increment(n)):
            case 0:
                return
            #1 -> triangle step
            case 1:
                CX(qs[1], qs[0])
                return
            #2 -> diamond step
            case 2:
                CX(qs[1], qs[0])
                tof_CT(True, False, qs[2], xs[0], qs[0])
                CX(qs[2], qs[1])
                return
            #else recurse
            case _:
                #note: "init" means [:-1]; but we're reversing, so...
                x0 = QBit()
                xss = QArray("xss", QBit, xs.size-1)
                bind(xs,[x0,xss])
                q0 = QBit()
                q1 = QBit()
                qsss = QArray("qsss", QBit, qs.size-2)
                bind(qs,[q0,q1,qsss])
                m = n[1:]
            
                H(q0)
                TDG(q1)
                CX(x0,q1)
                T(q1)
                CX(q0,q1)
                TDG(q1)
                CX(x0,q1)
                T(q1)

                SDG(q0)
                qss = QArray("qss", QBit, qs.size-1)
                bind([q1,qsss],qss)
                stepRight_aux(m,xss,qss)
                bind(qss,[q1,qsss])

                T(q1)
                CX(x0,q1)
                T(q1)
                CX(q0,q1)
                TDG(q1)
                CX(x0,q1)
                TDG(q1)
                H(q0)

                bind([q0,q1,qsss], qs)
                bind([x0,xss],xs)
        return

    x0 = QBit()
    xss = QArray("xss", QBit, xs.size-1)
    qs_aux = QArray("qs_aux", QBit, qs.size+1)
    within_apply(
        lambda : [
            bind(xs, [xss, x0]),
            bind([qs, x0], qs_aux)
        ],
        #tail xs, (head xs : qs) but reversed
        lambda : stepRight_aux(n, xss, qs_aux)
    )
    return


@qfunc(generative=True)
def walkDown(bs: CArray[CBool], xs: QArray, qs: QArray) -> None:
    @qfunc(generative=True)
    def walkDown_aux(bs: CArray[CBool], xs: QArray, qs: QArray) -> None:
        #Quantum Arrays can't be empty! We have to catch the "end" earlier.
        if(len(bs)==0):
            return
        elif(len(bs)==1):
            tof_CT(bs[bs.len-1], True, xs[xs.len-1], qs[qs.len-1], qs[qs.len-2])
            #walkDown_aux(bs[0:bs.len-1], xs[0:xs.len-1], qs[0:qs.len-1])
        else:
            tof_CT(bs[bs.len-1], True, xs[xs.len-1], qs[qs.len-1], qs[qs.len-2])
            walkDown_aux(bs[0:bs.len-1], xs[0:xs.len-1], qs[0:qs.len-1])
        return

    tof_CT(bs[bs.len-1], bs[bs.len-2], xs[xs.len-1], xs[xs.len-2], qs[qs.len-1])
    walkDown_aux(bs[0:bs.len-2], xs[0:xs.len-2], qs)



@qfunc(generative=True)
def walkUp(bs: CArray[CBool], xs: QArray, qs: QArray) -> None:
    invert(lambda: walkDown(bs, xs, qs))

#Operators = list of controlled circuits, i.e. [u(control, targets)]
#This type alias fails???
#type Operators = QCallableList[QBit, QArray]

#controlled uniformly-controlled gate: if q, then apply ops[xs](target).
@qfunc(generative=True)
def controlled_selectV(ops: QCallableList[QBit, QArray[QBit]], q: QBit, xs: QArray, target: QArray) -> None:
    m = ops.len
    n = xs.size
    start = to_node(0,n) + [True]
    end =  to_node((m-1),n) + [True]

    #Operand lists don't support slicing?!
    @qfunc(generative=True)
    def applyAndStep(ops: QCallableList[QBit, QArray[QBit]], opsindex: CInt, start: CArray[CBool], end: CArray[CBool], xs: QArray, qs: QArray, target: QArray)  -> None:
        if (start == end):
            ops[opsindex](qs[0], target)
            return
        else:
            ops[opsindex](qs[0], target)
            stepRight(start, xs, qs)
            #applyAndStep(ops[1:ops.len], increment(start), end, xs, qs, target)
            applyAndStep(ops, opsindex+1, increment(start), end, xs, qs, target)
            return
        return

    #xs' isn't a valid Python name!
    #xs' = q:xs
    xsp = QArray("xs'", QBit, n + 1)
    qs = QArray("qs", QBit, n)
    within_apply(
        lambda: bind([xs,q], xsp),
        #with_ancilla_list n $ \qs-> do...
        #creates n ancillas in 0 and uses as qs in the function following.
        lambda: within_apply(
            lambda: allocate(n, qs),
            lambda: [
                walkDown(start, xsp, qs),
                applyAndStep(ops, 0, start, end, xsp, qs, target),
                walkUp(end, xsp, qs)
            ]
        )
    )
    return

