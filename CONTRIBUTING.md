# Contributing to Classiq  

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:  

- Creating a new algorithm, application, or function 🚀  
- Submitting your research done with Classiq 👩🏻‍💻  
- Reporting a bug 🐞  
- Discussing the current state of the code  

We are **always available to help**—feel free to reach out via [GitHub Discussions](https://github.com/Classiq/classiq-library/discussions) or within the [Classiq Slack Community](https://short.classiq.io/join-slack).

Please note that we accept high-quality implementations to our repository and will be glad to accept a contribution that meets our standards.

## We Develop with GitHub  

We use GitHub to host code, track issues and feature requests, and accept pull requests.  

## Contribution Workflow  

We follow [GitHub Flow](https://guides.github.com/introduction/flow/index.html), and **all code changes must go through pull requests**.  

### **Important Guidelines for Code Submissions**  

1. **Discuss Before You Code**  
   - Create an issue to discuss your proposed contribution before submitting a PR.  
   - We will provide feedback to ensure your work aligns with the project's direction.  

2. **Fork and Branch**  
   - Fork the repository and create your feature branch from `main`.  

3. **Rebase Only, No Merge**  
   - We **strictly use [rebase](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) only** to maintain a clean and linear commit history.  
   - If your branch contains merge commits, you will need to either:  
     - Open a new PR from an updated branch  
     - Fix your branch and **rebase before merging** into `main`.  

4. **Ensure Compatibility**  
   - Make sure your code runs with the latest Classiq version.  

5. **Submit Your Pull Request**  
   - Open a PR and wait for feedback from maintainers.  

## Continuous Integration (CI) Requirements  

As part of the CI process, you **must** add a timeout value for your notebook in the file: `tests/resources/timeouts.yaml`  

- The timeout value should be **sufficient but not exaggerated**.  
- If your CI tests fail, check the error messages carefully.  
- **Common CI failures** are usually due to:  
  - Missing or insufficient timeout values - You will have to add or increase the timeout value of the specific notebook in `tests/resources/timeouts.yaml`.
  - Non-trivial dependencies in the new notebook — If this issue occurs, please contact us to discuss it further.

## Reporting Bugs  

We use GitHub issues to track public bugs. You can report a bug by [opening a new issue](https://github.com/Classiq/classiq-library/issues/new).  

### **How to Write a Good Bug Report**  

- Include **detailed** information about the issue
    - Provide a minimal **code example** that causes the error
    - Include the error message you get when running the code
- Provide **background context** if possible
    - Include the Classiq version you are using (you can obtain it by running `import classiq; print(classiq.__version__)`)
    - If you think it's necessary, add information about the OS you are using

## Need Help?  

We are always available to assist you!  
- Reach out through **[GitHub Discussions](https://github.com/Classiq/classiq-library/discussions)**.  
- Connect with us within the **[Classiq Slack Community](https://short.classiq.io/join-slack)**. 

## License  

By contributing, you agree that your submissions will be licensed under the [MIT License](http://opensource.org/licenses/MIT), the same as the project.  

## References  

Here are a few references you might find helpful:  

- [How to Contribute to an Open Source Project on GitHub](https://opensource.guide/how-to-contribute/)  
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)  
- [GitHub Flow](https://guides.github.com/introduction/flow/)  
