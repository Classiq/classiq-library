---
search:
    boost: 2.906
---

# **Getting started with git**

This page contains a practical guide on how to get started with git and GitHub, so you can get the most out of working with Classiq Studio and writing code in general

## **what is git?**

Git is a version control system that tracks changes in your code. It lets you:

Keep a history of modifications.
Work on different versions of your code.
Collaborate with others without overwriting changes.
Restore previous versions if something breaks.
It runs locally on your machine, but when combined with platforms like GitHub or GitLab, it enables seamless collaboration.

### **What is a Repository?**

A repository (repo) is a storage space where your project’s files, code, and version history are managed by Git.
A local repository exists inside your project folder and tracks changes.
A remote repository is stored on a hosting service like GitHub, GitLab, or Bitbucket, allowing multiple people to work on the same project.
We highly recommend to push your code to a remote repository. It will promise you that your work is backed up, and you can access it from anywhere.

## **Common commands and quick setup**

Classiq Studio comes with Git pre-installed, so you can start using it right away.

### **Initialize a Git Repository**

Inside your project folder, run:

```bash
git init
```

This creates a local repository, allowing you to track changes in your project.

### **Clone an Existing Repository**

You can always copy (clone) an existing project from a remote repository (e.g., GitHub) to your workspace:

```bash
git clone <repository_url>
```

### **Useful commands:**

#### **Check the status of your project:**

```bash
git status
```

#### **Add changes to the next commit:**

```bash
git add .
```

#### **Save your changes:**

```bash
git commit -m "Description of changes"
```

#### **Push and Pull**

Push – Send your changes to a remote repository (called origin):

```bash
git push origin main
```

Pull – Get the latest updates from the remote repository:

```bash
git pull origin main
```

When you start feeling comfortable with git, you can start using branches, pull requests, and more advanced features. You can read more about it in attached linked.

## **How does it work with GitHub?**

GitHub (or alternatives like GitLab and Bitbucket) acts as a remote repository, meaning it stores your code in the cloud and enables collaboration.

### **What is a Remote Repository?**

A remote repository is a version of your project that is hosted online. It allows you to:

-   Store your code securely.
-   Access your work from any device.
-   Collaborate with team members in real-time.

### **Connect your local repository to a remote repository, use:**

clone the repo:

```bash
git clone <repository_url>
```

add it to your local workspace

```bash
git remote add origin <repository_url>
```

Then, push your local changes to the remote repo:

```bash
git push -u origin main
```

Best Practices for Using Git with GitHub
Use branches – Work on a separate branch before merging changes to the main project:

```bash
git checkout -b feature-branch
```

### **Best practice to combine git and GitHub (or gitlab etc. - it's up to you :)**

-   Write clear commit messages – describe what changed and why.
-   Pull before pushing – always get the latest updates before sending your changes.
-   Use `.gitignore` – avoid committing unnecessary files.
-   Create pull requests – review changes before merging into main.

## **How to use git in the Classiq Studio**

-   Open the terminal in the Classiq Studio.
-   We have already installed git inside the studio, so you can start using it right away.

## **Read more**

There are infinite number of guides available on using git, integration with GitHub or others. We have collected some of our favorites:

-   [Git official documentation](https://git-scm.com/doc)
-   [GitHub official documentation](https://docs.github.com/en/get-started/)
-   [Git cheat sheet](https://www.atlassian.com/git/tutorials/atlassian-git-cheatsheet)
