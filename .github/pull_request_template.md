### PR Description

<!-- Describe the PR's general purpose -->

### Some notes

- [ ] Please make sure that the notebook runs successfully with the latest Classiq version.

- [ ] Please make sure that you placed the files in an appropriate folder

  - [ ] And that the file names are clear, descriptive, and match the notebook content.
    - [ ] Note that we require the file names of `.ipynb` and `.qmod` to be unique across this repository.
  - [ ] Plus, please make sure that all required files are included: `.qmod`, `.synthesis_options.json`, `.metadata.json`
  - [ ] And that images are embedded inside the notebook, not added as external files

- [ ] If applicable, please include link to the paper on which the notebook is based, in the notebook itself.

- [ ] Please use `rebase` on your branch (no merge commits)
- [ ] Please link this PR to the relevant issue

- [ ] Please make sure to run `pre-commit` when commiting changes
  - [ ] If you're using `git` in the terminal, make sure to install `pre-commit` via running `pip install pre-commit` followed by `pre-commit install`
    - [ ] More info at [the `pre-commit` documentation](https://pre-commit.com/)
  - [ ] Note that Classiq runs automatic code linting. Meaning that one of the tests verifies the output of `pre-commit`.
  - [ ] Also note that `pre-commit` may minorly alter some files. Make sure to `git add` the changes done by `pre-commit`
