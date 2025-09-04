from lys.Qt import QtCore
from lys.decorators import avoidCircularReference


class PreCorrector:
    def __init__(self, controllers):
        super().__init__()
        self._enabled = True
        self._controllers = {}
        for c in controllers:
            c.busyStateChanged.connect(self._busy, QtCore.Qt.DirectConnection)
            c.valueChanged.connect(self._correct, QtCore.Qt.DirectConnection)
            self._controllers.update({name: c for name in c.nameList})

        self._correctParams = dict()

    @property
    def controllers(self):
        return self._controllers
    
    @property
    def corrections(self):
        return self._correctParams

    @avoidCircularReference
    def _correct(self, values={}):
        if not self._enabled:
            return
        
        for name, func in self.corrections.items():
            if not func.enabled:
                continue
            elif any([arg in values for arg in func.argNames(excludeFixed=False)]):
                params = {arg: self._controllers[arg].get()[arg] for arg in func.argNames()}
                self._controllers[name].set(**{name: func(**params)})

    def _busy(self, busy):
        def busyFunc(p1, p2):
            c1, c2 = self.controllers[p1], self.controllers[p2]
            result = c1._isBusy_orig()
            if c2._isBusy()[p2]:
                result[p1] = True
            return result

        if not self._enabled:
            return
                       
        for name, func in self.corrections.items(): # y = f(t,x)
            if not func.enabled:
                continue
            for name2, b in busy.items():
                if name2 in func.argNames(excludeFixed=True):
                    if b:
                        self.controllers[name2]._isBusy_orig = self.controllers[name2]._isBusy
                        self.controllers[name2]._isBusy = lambda p1=name2, p2=name: busyFunc(p1, p2)
                    else:
                        self.controllers[name2]._isBusy = self.controllers[name2]._isBusy_orig


class _FunctionCombination:
    def __init__(self):
        super().__init__()
        self._funcs = dict()
        self._formula = None
        self.enabled = True

    def __call__(self, **scanParams):
        if self._formula is None:
            firstFunc = next(iter(self._funcs.values()))
            correctValue = firstFunc(**scanParams)
        else:
            localVariables = {funcName: func(**scanParams) for funcName, func in self._funcs.items()}
            correctValue = eval(self._formula, {"__builtins__": None}, localVariables)
        return correctValue

    @property
    def functions(self):
        return self._funcs
    
    @property
    def expression(self):
        return self._formula
    
    @expression.setter
    def expression(self, value):
        self._formula = value

    def argNames(self, excludeFixed=True):
        res = []
        for func in self._funcs.values():
            for arg in func.argNames(excludeFixed=excludeFixed):
                if arg not in res:
                    res.append(arg)
        return res


class _InterpolatedFunction:
    """
    This class represents a function f(x,y) with the information of arguments name such as 'x'.

    Evaluation of the function can be done by __call__ like f(x=1, y=2).
    """

    def __init__(self, interpolator, argNames):
        super().__init__()
        self._argNames = argNames
        self._interpolator = interpolator
        self._fixedValues = {}

    def __call__(self, **kwargs):
        val = self._interpolator([[self._fixedValues.get(arg, kwargs.get(arg, None)) for arg in self.argNames()]])[0]
        if hasattr(val, "__iter__"):
            val = val[0]
        return val
    
    @property
    def fixedValues(self):
        """ a dictionary that specifies the fixed value."""
        return self._fixedValues

    def argNames(self, excludeFixed=False):
        """Returns all arguments names of this function."""
        if excludeFixed:
            return [arg for arg in self._argNames if arg not in self._fixedValues]
        else:
            return self._argNames

