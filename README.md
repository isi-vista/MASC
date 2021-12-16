# Machine-Assisted Script Curation (MASC)

The MASC schema curation tool is currently being developed for the LESTAT project.

## Requirements

Python must be installed. It currently runs on Python 3.7, but newer versions might work as well.

NodeJS v14 and npm v6 must be installed. Tools like [nodenv](https://github.com/nodenv/nodenv) or [nvm](https://github.com/nvm-sh/nvm) can be used for installation. For alternative methods, refer to the NodeSource blog posts [Installing Node.js Tutorial: Using nvm](https://nodesource.com/blog/installing-node-js-tutorial-using-nvm-on-mac-os-x-and-ubuntu/) (macOS and Ubuntu) or [Installing Node.js Tutorial: Windows](https://nodesource.com/blog/installing-nodejs-tutorial-windows/) (Windows) for instructions.

## Installation

Use the provided Makefile to install MASC:

```bash
make install
```

To configure deployment-specific settings, create `pycurator/.env` and add settings specified in `pycurator/common/config.py`.

## Usage

The application has two main components, and they must be run simultaneously to use the application:

- To run the back end, navigate to `pycurator/flask_backend` and run `bash start_gunicorn.sh`. The server will be available at `http://localhost:5000/`. Usage of the Flask server is possible, but due to a bug in `sentence-transformers`, the application might crash when run with Flask instead of Gunicorn.
- To run the front end, navigate to `angular-frontend` and run `npx ng serve`. The application will be hosted at `http://localhost:4200/`, which is viewable in a modern web browser. The application will automatically reload if any source files are changed.

While these instructions are sufficient for a local deployment, they should not be used on an actual server. It is up to the user to determine the proper server configuration for themselves.

### GPT-2 component

The GPT-2 component currently must be run manually.

It is recommended to use the `batch_run.py` script to do so. It automatically finds all schemas without a JSON file and runs a Slurm job for each. It doesn't use anything but the standard library, so the virtual environment is not necessary.

`batch_run.py` must be run from `pycurator/gpt2_component` to allow paths to work properly. Use the command `PYTHONPATH=../../ python -m pycurator.gpt2_component.batch_run`.

Do not start a new run until all previous jobs are finished. `batch_run.py` only checks whether there is output when deciding which schemas to run, so it can't tell if there is a currently running job for a schema.

## Publications

For more information about the project, see the related paper:

> Ciosici, Manuel, et al. "Machine-Assisted Script Curation." _Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies: Demonstrations_, Association for Computational Linguistics, 2021, pp. 8–17. _ACLWeb_, <https://www.aclweb.org/anthology/2021.naacl-demos.2>.

## License

[MIT](https://choosealicense.com/licenses/mit/)
