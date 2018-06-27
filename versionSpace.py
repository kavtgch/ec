from utilities import *
from program import *

class ExpressionTable():
    def __init__(self):
        self.expressions = []
        self.expression2index = {}
        self.freeVariables = []

        self.childrenTable = []
        self.substitutionTable = {}
        self.inversionTable = []
        self.recursiveInversionTable = []

    def incorporate(self,p):
        if p.isIndex or p.isPrimitive or p.isInvented:
            pass
        elif p.isAbstraction:
            p = Abstraction(self.incorporate(p.body))
        elif p.isApplication:
            p = Application(self.incorporate(p.f),
                            self.incorporate(p.x))
        else: assert False

        return self._incorporate(p)

    def _incorporate(self,p):
        if p in self.expression2index: return self.expression2index[p]

        if p.isIndex: free = [p.i]           
        elif p.isPrimitive or p.isInvented: free = []
        elif p.isAbstraction: free = [f - 1
                                      for f in self.freeVariables[p.body]
                                      if f > 0]
        elif p.isApplication: free = list(set(self.freeVariables[p.f] + self.freeVariables[p.x]))
        else: assert False


        j = len(self.expressions)
        
        self.expressions.append(p)
        self.expression2index[p] = j
        self.freeVariables.append(free)
        self.childrenTable.append(None)
        self.inversionTable.append(None)
        self.recursiveInversionTable.append(None)

        return j

    def extract(self,j):
        l = self.expressions[j]
        if l.isAbstraction:
            return Abstraction(self.extract(l.body))
        elif l.isApplication:
            return Application(self.extract(l.f),
                               self.extract(l.x))
        return l

    def shift(self,j, d, c=0):
        if n == 0 or all( f < c for f in self.freeVariables[j] ): return j

        l = self.expressions[j]
        if l.isIndex:
            assert l.i >= c
            assert l.i + d >= 0
            return self._incorporate(Index(l.i + d))
        elif l.isAbstraction:
            return self._incorporate(Abstraction(self.shift(l.body, d, c + 1)))
        elif l.isApplication:
            return self._incorporate(Application(self.shift(l.f, d, c),
                                                 self.shift(l.x, d, c)))
        else:
            assert False
            

    # def closedChildren(self,n,j):
    #     if (n,j) in self.childrenTable: return self.childrenTable[(n,j)]

    #     cc = set()
    #     if all( f - n >= 0
    #             for f in self.freeVariables[j] ):
    #         cc.add(self.shift(j,-n))
            
    #     l = self.expressions[j]
    #     if l.isAbstraction:
    #         cc.update(self.closedChildren(n + 1, l.body))
    #     elif l.isApplication:
    #         cc.update(self.closedChildren(n, l.f))
    #         cc.update(self.closedChildren(n, l.x))

    #     self.childrenTable[(n,j)] = cc
    #     return cc

    def CC(self,j):
        if self.childrenTable[j] is not None: return self.childrenTable[j]
        cc = {j: {0: j}}

        l = self.expressions[j]
        if l.isApplication:
            for v, shifts in self.CC(l.f).items():
                if v in cc:
                    cc[v].update(shifts)
                else:
                    cc[v] = shifts
            for v, shifts in self.CC(l.x).items():
                if v in cc:
                    cc[v].update(shifts)
                else:
                    cc[v] = shifts
        elif l.isAbstraction:
            for v,shifts in self.CC(l.body).items():
                if any( fv == 0 for fv in self.freeVariables[v] ): continue
                vp = self.shift(v,-1)
                if vp not in cc: cc[vp] = {}
                cc[vp].update({n + 1: vn for n,vn in shifts.items() })

        self.childrenTable[j] = cc
        
        return cc                    

    def substitutions(self,n,v,mapping,e):
        if (n,v,e) in self.substitutionTable: return self.substitutionTable[(n,v,e)]

        s = []

        if n in mapping and e == mapping[n]:
            s.append(self._incorporate(Index(n)))

        l = self.expressions[e]
        if l.isPrimitive or l.isInvented:
            s.append(e)
        elif l.isAbstraction:
            for b in self.substitutions(n + 1, v, mapping, l.body):
                s.append(self._incorporate(Abstraction(b)))
        elif l.isApplication:
            for f in self.substitutions(n, v, mapping, l.f):
                for x in self.substitutions(n, v, mapping, l.x):
                    s.append(self._incorporate(Application(f,x)))
        elif l.isIndex:
            if l.i < n:
                s.append(e)
            else:
                s.append(self._incorporate(Index(l.i + 1)))
        else: assert False

        self.substitutionTable[(n,v,e)] = s
        return s

    def invert(self,j):
        if self.inversionTable[j] is not None: return self.inversionTable[j]

        s = []
        for v,mapping in self.CC(j).items():
            for b in self.substitutions(0,v,mapping,j):
                f = self._incorporate(Abstraction(b))
                a = self._incorporate(Application(f,v))
                s.append(a)
        self.inversionTable[j] = s
        return s

    def recursiveInvert(self,j):
        if self.recursiveInversionTable[j] is not None: return self.recursiveInversionTable[j]

        s = list(self.invert(j))

        l = self.expressions[j]
        if l.isApplication:
            for f in self.recursiveInvert(l.f):
                s.append(self._incorporate(Application(f,l.x)))
            for x in self.recursiveInvert(l.x):
                s.append(self._incorporate(Application(l.f,x)))                    
        elif l.isAbstraction:
            for b in self.recursiveInvert(l.body):
                s.append(self._incorporate(Abstraction(b)))
        
        self.recursiveInversionTable[j] = s
        return s

    def expand(self,j,n=1):
        es = {j}
        previous = {j}
        for _ in range(n):
            previous = {rw
                        for p in previous
                        for rw in self.recursiveInvert(p) }
            es.update(previous)
        return es


        
if __name__ == "__main__":
    from arithmeticPrimitives import *
    from listPrimitives import *
    from grammar import *
    bootstrapTarget_extra()
    p1 = Program.parse("(lambda (fold empty $0 (lambda (lambda (cons (- $0 5) $1)))))")
    p2 = Program.parse("(lambda (fold empty $0 (lambda (lambda (cons (+ $0 $0) $1)))))")
    #p1 = Program.parse("(lambda (fold $1 (lambda ($0 fold $2))))")

    v = ExpressionTable()
    with timing("Computed expansions"):
        b1 = v.expand(v.incorporate(p1),n=2)
        b2 = v.expand(v.incorporate(p2),n=2)
    
