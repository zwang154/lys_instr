from lys.Qt import QtCore
from lys.decorators import avoidCircularReference


class PreCorrector(QtCore.QObject):
    def __init__(self, controllers):
        super().__init__()
        self._enabled = True
        self._controllers = {}
        for c in controllers:
            c.busyStateChanged.connect(self._busy, QtCore.Qt.DirectConnection)
            self._controllers.update({name: c for name in c.nameList})
            c._isBusy_orig = c._isBusy

        self._correctParams = dict()

    @property
    def controllers(self):
        return self._controllers

    @property
    def corrections(self):
        return self._correctParams

    def _busy(self, busy):
        if not self._enabled:
            return

        for y, f in self.corrections.items():  # y = f(t,x)
            if not f.enabled:
                continue

            # Replace busy method of arg
            flg =False
            for arg, b in busy.items():
                if arg in f.argNames(excludeFixed=True):  # e.g. arg is t
                    self._replaceBusyMethod(arg, y, not b)
                    flg = True

            # set y if any arg is busy
            if flg:
                params = {arg: self._controllers[arg].get()[arg] for arg in f.argNames() if arg not in busy}
                params.update({arg: self._controllers[arg].target[arg] for arg in f.argNames() if arg in busy})
                self._controllers[y].set(**{y: f(**params)}, lock=False)

    def _replaceBusyMethod(self, targ, dep, reset=False):
        """
        Replace busy method of targ.
        New _isBusy method of targ returns True if _isBusy of dep is True. 
        """
        busy_targ = self.controllers[targ]._isBusy
        busy_dep = self.controllers[dep]._isBusy

        def busyFunc():
            result = busy_targ()  # {..., f: False, ...}
            dep_busy = busy_dep()[dep]
            result[targ] = result[targ] or dep_busy
            return result

        if reset is True:
            self.controllers[targ]._isBusy = self.controllers[targ]._isBusy_orig
        else:
            self.controllers[targ]._isBusy = busyFunc


class _FunctionCombination:
    def __init__(self):
        super().__init__()
        self._funcs = dict()
        self._formula = None
        self.enabled = True

    def __call__(self, **scanParams):
        if self._formula is None or self._formula == "":
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
