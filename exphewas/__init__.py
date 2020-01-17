"""Browser and tools for the gene-based PheWAS analysis."""

try:
    from .version import exphewas_version as __version__
except ImportError:
    __version__ = None


__author__ = "Marc-Andre Legault"
__copyright__ = "Copyright 2020, Beaulieu-Saucier Pharmacogenomics Centre"
__credits__ = ["Louis-Philippe Lemieux Perreault", "Marc-Andre Legault"]
__license__ = "MIT"
__maintainer__ = "Louis-Philippe Lemieux Perreault"
__email__ = "louis-philippe.lemieux.perreault@statgen.org"
__status__ = "Development"
