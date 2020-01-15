"""
Provides optional bindings to an Rpy2 environment.
"""


try:
    # Note: to install rpy2
    # env ARCHFLAGS="-arch i386 -arch x86_64" pip install rpy2
    import rpy2
    from rpy2.robjects.packages import importr
    from rpy2.robjects import r, FloatVector
    
    HAS_RPY2 = True
except ImportError:
    HAS_RPY2 = False


class R(object):
    def __init__(self):
        if not HAS_RPY2:
            raise RuntimeError("Rpy2 is not available")

        self.base = importr("base")

        self._r_importr = importr
        self._r = r

    def _import_qvalue(self):
        self._r_qvalue = self._r_importr("qvalue")

    def qvalue(self, p_values):
        self._import_qvalue()
        q = self._r.qvalue(FloatVector(p_values))
        return list(q.rx2("qvalues"))
