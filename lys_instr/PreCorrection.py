from lys.Qt import QtCore
from lys.decorators import avoidCircularReference


class PreCorrector(QtCore.QObject):
    """
    Corrector that manages inter-axis dependencies and applies value corrections.

    This class automatically applies configured correction callables whenever controller axis targets change. 
    Correction parameters are stored in ``_correctParams``, which maps a target axis name to a callable that computes the corrected value from current master-axis parameters.
    The corrector expects controllers passed to the constructor to provide a ``busyStateChanged`` Qt signal and a ``nameList`` iterable of axis names (typically motors).
    """

    def __init__(self, controllers):
        """
        Initialize the corrector with the given controllers.

        Args:
            controllers (Iterable): Iterable of controller objects. Each controller must provide a ``busyStateChanged`` Qt signal and a ``nameList`` iterable of its axis names.
        """
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
        """
        Controller instances.

        Returns:
            dict: Mapping of axis name (str) to controller instance.
        """
        return self._controllers

    @property
    def corrections(self):
        """
        Configured correction callables.

        Returns:
            dict: Mapping of target name to correction callable (typically ``_FunctionCombination``) that computes the corrected value.
        """
        return self._correctParams

    def _busy(self, busy):
        """
        Handle controller busy-state updates.

        Args:
            busy (dict): Mapping of axis name (str) to bool indicating busy state.
        """
        if not self._enabled:
            return

        for y, f in self.corrections.items():  # y = f(t,x)
            if not f.enabled:
                continue

            # Replace busy method of arg
            flg = False
            for arg, b in busy.items():
                if arg in f.argNames(excludeFixed=True):  # e.g. arg is t
                    self._replaceBusyMethod(arg, y, not b)
                    if b:
                        flg = True

            # set y if any arg is busy
            if flg:
                params = {arg: self._controllers[arg].get()[arg] for arg in f.argNames() if arg not in busy}
                params.update({arg: self._controllers[arg].target[arg] for arg in f.argNames() if arg in busy})
                self._controllers[y].set(**{y: f(**params)}, lock=False)

    def _replaceBusyMethod(self, targ, dep, reset=False):
        """
        Override or restore a controller's ``_isBusy`` method.

        Replace the ``_isBusy`` attribute of the controller named ``targ`` with a wrapper that marks the target axis busy if it was already busy or if controller ``dep`` is busy. 
        When ``reset`` is True, restore the original ``_isBusy`` method.

        Args:
            targ (str): Name of the target controller whose busy method will be modified.
            dep (str): Name of the dependent controller whose busy state will be included.
            reset (bool, optional): If True, restore the original busy method. Defaults to False.
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
    """
    Combination of named correction callables into a single correction callable.
    """

    def __init__(self):
        """
        Initialize the combination of correction callables.
        """
        super().__init__()
        self._funcs = dict()
        self._formula = None
        self.enabled = True

    def __call__(self, **scanParams):
        """
        Evaluate the combined correction for the given scan parameters.

        Invoke each registered correction callable with the provided keyword scan parameters (typically named motor-axis positions, e.g. ``x=..., y=...``).
        Correction callables must accept those keyword arguments and return a numeric value.
        If ``expression`` is set, invoke each registered correction callable and supply its return value as a local variable to the expression. 
        If ``expression`` is ``None`` or an empty string, use the return value of the first registered correction callable (in insertion order).

        Args:
            **scanParams: Keyword scan parameters forwarded to each correction callable.

        Returns:
            float | int: Computed correction (typically the corrected target value for an axis).

        Caution:
            The expression is evaluated with ``eval`` using ``{"__builtins__": None}``. Only trusted expressions should be used.
        """
        if self._formula is None or self._formula == "":
            firstFunc = next(iter(self._funcs.values()))
            correctValue = firstFunc(**scanParams)
        else:
            localVariables = {funcName: func(**scanParams) for funcName, func in self._funcs.items()}
            correctValue = eval(self._formula, {"__builtins__": None}, localVariables)
        return correctValue

    @property
    def functions(self):
        """
        Correction callables registered in this combination.

        Returns:
            dict[str, Callable]: Mapping of function names to correction callables.

        Note:
            Each correction callable must implement ``__call__(**kwargs)`` and ``argNames(excludeFixed: bool) -> list[str]``.
        """
        return self._funcs

    @property
    def expression(self):
        """
        Expression string used to combine registered correction callables.

        Returns:
            str | None: Expression string that combines registered correction callables' return values, or ``None`` if no expression is set.
        """
        return self._formula

    @expression.setter
    def expression(self, value):
        """
        Set the expression string used to combine registered correction callables.
        """
        self._formula = value

    def argNames(self, excludeFixed=True):
        """
        Return the ordered list of unique argument names required by the registered correction callables.

        Args:
            excludeFixed (bool): If True, exclude arguments that the correction callable reports as fixed.

        Returns:
            list[str]: Ordered, unique argument names.
        """
        res = []
        for func in self._funcs.values():
            for arg in func.argNames(excludeFixed=excludeFixed):
                if arg not in res:
                    res.append(arg)
        return res


class _InterpolatedFunction:
    """
    Adapter wrapping an interpolator into a correction callable.
    """

    def __init__(self, interpolator, argNames):
        """
        Create the interpolator wrapper.

        Args:
            interpolator (callable): An interpolation callable that accepts a 2D sequence of input points and returns an iterable of values.
            argNames (Sequence[str]): Ordered list of argument names the interpolator expects.
        """
        super().__init__()
        self._argNames = argNames
        self._interpolator = interpolator
        self._fixedValues = {}

    def __call__(self, **kwargs):
        """
        Evaluate the interpolated function for the provided named args.

        Any arguments present in ``fixedValues`` override values supplied in ``kwargs``. 
        Missing arguments are passed as ``None`` to the interpolator.

        Args:
            **kwargs: Named argument values to pass to the interpolator.

        Returns:
            float | int: The interpolator result for the requested point.
        """
        val = self._interpolator([[self._fixedValues.get(arg, kwargs.get(arg, None)) for arg in self.argNames()]])[0]
        if hasattr(val, "__iter__"):
            val = val[0]
        return val

    @property
    def fixedValues(self):
        """
        Fixed values of arguments.

        Use this mapping to specify arguments that should always use a particular value when evaluating the interpolator.

        Returns:
            dict[str, Any]: Mutable mapping of argument names to fixed values.
        """
        return self._fixedValues

    def argNames(self, excludeFixed=False):
        """
        Return the ordered list of unique argument names required by the registered correction callables.

        Args:
            excludeFixed (bool): If True, exclude arguments that the correction callable reports as fixed.

        Returns:
            list[str]: Ordered, unique argument names.
        """
        if excludeFixed:
            return [arg for arg in self._argNames if arg not in self._fixedValues]
        else:
            return self._argNames
