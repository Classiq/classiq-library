# Contributing to Classiq

We appreciate your input! Contributing to this project should be easy, clear, and collaborative—whether you're:

- Creating a new algorithm, application, or function
- Submitting your research using Classiq
- Reporting a bug
- Discussing or improving existing code

We are always available to help — feel free to reach out via [GitHub Discussions](https://github.com/Classiq/classiq-library/discussions) or the [Classiq Slack Community](https://short.classiq.io/join-slack).

We welcome high-quality contributions that follow our standards and can serve the quantum ecosystem.

---

## Table of Contents

- [How to Contribute & Workflow](#how-to-contribute--workflow)
- [Contribution Standards](#contribution-standards)
- [CI Requirements](#ci-requirements)
- [Before-You-Submit Checklist](#before-you-submit-checklist)
- [Reporting Bugs](#reporting-bugs)
- [Need Help?](#need-help)
- [License](#license)
- [References](#references)

---

## How to Contribute & Workflow

We follow a standard GitHub-based workflow with issues, branches, and pull requests.

We use [GitHub Flow](https://guides.github.com/introduction/flow/index.html), and all code changes must go through pull requests.

### Submission Guidelines:

1. **Start with an Issue:**
   Open an issue to discuss your proposed change. This helps align efforts, avoid duplication, and ensure your contribution fits the project's goals.

2. **Fork and Branch:**
   Fork the repository and create a new branch from `main`.

3. **Rebase Only (No Merge Commits):**
   We maintain a clean, linear commit history via rebase-only.

   - If your branch includes merge commits, please rebase it or create a fresh branch.
   - See: [Git Rebase Guide](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)

4. **Use the Latest Classiq Version:**
   Ensure your code is compatible with the current SDK version.

5. **Open a Pull Request:**
   Submit your PR and tag the maintainers for feedback.
   - Make sure the PR is **linked to its related issue**. See: [Linking a PR to an Issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)

---

## Contribution Standards

To keep the library organized and functional, please follow these standards:

- **Place Files Correctly:**
  Add new content to the appropriate folder: `algorithms/`, `applications/`, or `tutorials/`.

- **Use `.ipynb` Format:**
  All contributions should be in Jupyter Notebook format unless agreed otherwise with a maintainer.

- **If your contribution is based on a paper:**

  - The folder and notebook name should match the paper title (use lowercase and underscores if needed).
  - Include a link to the paper’s [arXiv](https://arxiv.org/) or publication URL **at the top of the notebook**.

- **Include Images Within the Notebook:**
  Use Jupyter's built-in drag-and-drop feature to embed images directly into the notebook. Do not add images as separate files.

- **Include Required Support Files:**
  Each notebook must be accompanied by:

  - `file_name.qmod`
  - `file_name.synthesis_options.json`
  - `file_name.metadata.json`

- **Use `pre-commit`**
  New content must follow the standars which are enforced by `pre-commit`.
  Such standards, for example, automatically format the code, or add templates for testing notebooks.
  In order to install `pre-commit`, you may run
  ```bash
  pip install pre-commit
  pre-commit install
  ```
  Alternatively, you may visit [the `pre-commit` documentation](https://pre-commit.com/) for more details.

### How to Generate These Files:

- Use the [`write_qmod`](https://docs.classiq.io/latest/sdk-reference/modeling/?h=write_qmod#classiq.write_qmod.write_qmod) function:

  ```python
  write_qmod(qmod, out_file="your_filename")
  ```

- Or use `out_file` when creating the model:

  ```python
  qmod = create_model(main, out_file="your_filename")
  ```

- The `.metadata.json` file is **not auto-generated**.
  Copy one from a similar folder, rename it, and adapt the content.
  Example: [bernstein_vazirani_example.metadata.json](https://github.com/Classiq/classiq-library/blob/main/algorithms/bernstein_vazirani/bernstein_vazirani_example.metadata.json)

---

## CI Requirements

To pass CI, you must add a timeout for your notebook in:
`tests/resources/timeouts.yaml`

- The timeout should be just enough for the notebook to complete — avoid setting unnecessarily high values.
- If the CI fails:
  - Review the error logs.
  - Common causes include:
    - Missing or insufficient timeout.
    - Non-trivial dependencies. If this occurs, contact us via GitHub or Slack.

---

## Before-You-Submit Checklist

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

---

## Reporting Bugs

We use GitHub Issues to track bugs. [Open a new issue](https://github.com/Classiq/classiq-library/issues/new) and include the following:

### How to Write a Helpful Bug Report:

- **What were you trying to do?**
  Briefly explain your goal or expected behavior.

- **What went wrong?**
  Describe the issue and include the full error message or stack trace.

- **Code to reproduce:**
  Include a minimal snippet or notebook, if possible.

- **Version info:**

  ```python
  import classiq
  print(classiq.__version__)
  ```

  Optionally include Python version and OS.

- **Additional context (if relevant):**
  Does the issue happen consistently? After an update?

---

## Need Help?

We're here to support you:

- Ask questions in [GitHub Discussions](https://github.com/Classiq/classiq-library/discussions)
- Join the [Classiq Slack Community](https://short.classiq.io/join-slack)

---

## License

By contributing, you agree that your work will be licensed under the [MIT License](http://opensource.org/licenses/MIT), in line with the rest of the project.

---

## References

- [How to Contribute to an Open Source Project on GitHub](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Linking Pull Requests to Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)
