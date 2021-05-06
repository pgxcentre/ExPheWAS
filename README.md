This repository contains the code behind [ExPheWas](https://exphewas.statgen.org/). A thorough description of the project can be found either in the project's [documentation](https://exphewas.statgen.org/v0/docs) or in the [manuscript](https://www.medrxiv.org/content/10.1101/2021.03.17.21253824v2).

### Overview of the repository

Briefly, the ``exphewas`` directory contains the python package that powers the web application's backend (API, web application and database). The ``exphewas`` python package can be installed (_e.g._ using ``pip install .``. Once this is done, a command-line utility will be available that offers various housekeeping utilities like data loading or database initialization.

The code for the frontend is in the ``frontend`` directory. The command ``npm run build`` can be used from that directory to build the javascript from the frontend. The code for all D3.js graphs can be found there.

### Configuration

Configuration only requires a database string for SQLAlchemy and the path where the frontend gets built.

    export EXPHEWAS_DATABASE_URL=postgresql+psycopg2://user:password@host/dbname
    export EXPHEWAS_STATIC_FOLDER=.../exphewas/frontend/dist

### Issue tracker

The [issue tracker](https://github.com/pgxcentre/ExPheWAS/issues) is a good way to send us suggestions or to report problems with any aspect of ExPheWas.


### Citation

Legault, Marc-André, Louis-Philippe Lemieux Perreault, and Marie-Pierre Dubé. "ExPheWas: a browser for gene-based pheWAS associations." medRxiv (2021).
