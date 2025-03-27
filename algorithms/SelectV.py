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
    for i in range (len(next)-1, -1, -1):
        if not next[i]:
            next[i] = True
            break
        else:
            next[i] = False
    return next

#Translate integer n into a length-m bitstring.
def to_node(n: int, m: int) -> list[bool]:
    return  [((n >> (m-i-1)) % 2 == 1) for i in range(m)]

def to_num(node: list[bool]):
    return sum(node[i] << len(node)-i-1 for i in range(len(node)))

#reverse the bits in n, flipping its endian-ness.
def reverse_endian(n: int, m: int):
    return to_num(to_node(n,m)[::-1])

#print(increment(to_node(127, 8)))
#[True, False, False...]
#print(reverse_endian(1, 8))
#128

#step to the next node in the tree, where xs are inputs and qs are ancillas.
#Precondition 1 < |bs| = |xs| = |qs| + 1.
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
                #q0 = qs[-1]
                #q1 = qs[-2]
                CX(qs[qs.len-2],qs[qs.len-1])
                return
            #2 -> diamond step
            case 2:
                #q0 = qs[-1]
                #q1 = qs[-2]
                #q2 = qs[-3]
                #x0 = xs[-1]
                control(ctrl=qs[qs.len-2], stmt_block=lambda: X(qs[qs.len-1]))
                tof_CT(True, False, qs[qs.len-3], xs[xs.len-1], qs[qs.len-1])
                control(ctrl=qs[qs.len-3], stmt_block=lambda: X(qs[qs.len-2]))
                return
            #else recurse
            case _:
                #note: "init" means [:-1]
                #x0 = xs[-1]
                x0 = QBit()
                #xss = xs[:-1]
                xss = QArray("xss", QBit, xs.size-1)
                bind(xs,[xss,x0])
                #q0 = qs[-1]
                q0 = QBit()
                #q1 = qs[-2]
                q1 = QBit()
                #qss = qs[:-1]
                qsss = QArray("qsss", QBit, qs.size-2)
                bind(qs,[qsss,q1,q0])
                m = n[:n.len-1]
            
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
                bind([qsss,q1],qss)
                stepRight_aux(m,xss,qss)
                bind(qss,[qsss,q1])

                T(q1)
                CX(x0,q1)
                T(q1)
                CX(q0,q1)
                TDG(q1)
                CX(x0,q1)
                TDG(q1)
                H(q0)

                bind([qsss,q1,q0], qs)
                bind([xss,x0],xs)
        return

    x0 = QBit()
    xss = QArray("xss", QBit, xs.size-1)
    qs_aux = QArray("qs_aux", QBit, qs.size+1)
    within_apply(
        lambda : [
            bind(xs, [x0, xss]),
            bind([x0, qs], qs_aux)
        ],
        #tail xs, (head xs : qs)
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
            tof_CT(bs[0], True, xs[0], qs[0], qs[1])
        else:
            tof_CT(bs[0], True, xs[0], qs[0], qs[1])
            walkDown_aux(bs[1:], xs[1:xs.len], qs[1:qs.len])
        return

    tof_CT(bs[0], bs[1], xs[0], xs[1], qs[0])
    walkDown_aux(bs[2:], xs[2:xs.len], qs)



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
    start = [True] + to_node(0,n)
    end = [True] + to_node((m-1),n)

    #Operand lists don't support slicing?!
    @qfunc(generative=True)
    def applyAndStep(ops: QCallableList[QBit, QArray[QBit]], opsindex: CInt, start: CArray[CBool], end: CArray[CBool], xs: QArray, qs: QArray, target: QArray)  -> None:
        if (start == end):
            ops[opsindex](qs[qs.len-1], target)
            return
        else:
            ops[opsindex](qs[qs.len-1], target)
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
        lambda: bind([q,xs], xsp),
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

