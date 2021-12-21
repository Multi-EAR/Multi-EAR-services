# relative imports
from . import create_app

app = create_app()


def main(app_kwargs: dict = None, run_kwargs: dict = None):
    """
    A wrapper to simplify uWSGI. Creates and runs the ctrl Flask app.

    Parameters
    ----------

    app_kwargs : `dict`, optional
        Keyword arguments passed to `ctrl.create_app()`.

    run_kwargs : `dict`, optional
        Keyword arguments passed to `app.run()`.
    """
    app_kwargs = app_kwargs or dict()
    run_kwargs = run_kwargs or dict(debug=False)

    app = create_app(**app_kwargs)
    app.run(**run_kwargs)


if __name__ == '__main__':
    app.run()
