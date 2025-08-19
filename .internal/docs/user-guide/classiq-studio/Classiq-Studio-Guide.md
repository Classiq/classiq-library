---
search:
    boost: 3.095
---

# **Getting started with Classiq Studio**

This page contains a detailed guide on how to use the Classiq Studio.

## **Setup and get started**

To get started with the Classiq Studio, follow these steps:

1. Sign up to the Classiq platform: At https://platform.classiq.io/, click Sign Up. Approve the terms of use and register with your Google/Microsoft account or any other email (if needed fill in the registration form and you will be redirected to the home page).
2. Access the Classiq Studio from the Classiq Platform home page or site pane.
   ![platform home page](resources/StudioClickHere.png).

3. Your environment is loaded in a new browser tab (initial setup could take a couple of minutes). ![loading-page](resources/loading-page.png)

4. Please trust the Classiq workspace author to open the Classiq extension and load your workspace. ![trusted-host](resources/trusted-host.png)

Now your Studio is ready for use.
Access you workspace via the "EXPLORER" icon on the top left.
Your workspace consist of two sections:

-   Workspace: persistent storage, any edit to these files will be saved.
-   Classiq library: This is your place to wonder around in the world of quantum algorithms. You can click on any notebook, modify it and run it. But remember that this is a non-persistent storage, any edit to these files will be reverted when the Studio is shut down (after 1 hour of being idle). If you have made changes you want to save - just copy-paste the file to the personal workspace section.
    ![workspace](resources/workspace.png)
-   You can also upload any file into your persistent storage by right click on "user workspace" and select "upload". ![upload-file](resources/upload-file.png)

5.  When running a notebook for the first time, you will be asked to install the kernel. Click on the "Select Kernel" button and choose the recommended Python kernel (Python 3.12.8) ![install-kernel](resources/install-kernel.png)
6.  You will see a dropdown window - select "Python Environments" by clicking it (or hit "Enter" in the keyboard)
7.  Select "classiq-venv".
    -   More advanced users that feel comfortable managing their own environment are welcome to set their own virtual environment and use it.
8.  Start coding, experiment, and create quantum algorithms.
9.  when calling the method `show()` you might see a pop-up that asks you to trust external domain - click on "trust all domain from classiq.io" to see this popup only once. the circuit will open up in a separate tab.

## **Best practices**

In Classiq Studio each user has its own dedicated persistence storage (2 GB).
What does this even means? It means that every time you reload you can keep working right where you left off, same as working locally on your computer :)

There are several considerations and best practices it's better to keep in mind:

### **data persistence location**

The explorer (file browser) is divided into two sections: Workspace and Classiq library. The Classiq library is non-persistent and any edit to these files will be reverted when the Studio is shut down (after 1 hour of being idle). Thus, we recommend to copy the desired notebook to the Workspace section.

#### **Data retention Period**

Please note that this feature is still under development and we are working on improving it. Thus we will do our best to keep your data and work safe, but we cannot guarantee that your data will be kept forever. We recommend to backup your work locally (by downloading the files) or in a remote repository.

### **use git**

We highly recommend using git and GitHub (or similar) to keep track of your work. You can use git in the terminal or in the Studio. Check out [this section](git-getting-started.md) to get started with git.
After committing locally it's best to push your work into a remote repository for back up and collaborative work.

### **Use the virtual environment wisely**

You have a virtual environment installed in your studio. You can install any pip package you need for your work (e.g. Qiskit, TensorFlow etc.), but keep in mind that you have limited space. Also, environments are often hard to maintain, and you can get into dependencies rabbit hole. If you desire to experiment with new packages - install a new venv with any package you want, and delete it when you are done using.
We guarantee that the "classiq-venv" is set and working.

### **Resetting the Virtual Environment**

If you encounter issues or simply want a clean slate, you can reset your virtual environment by running the following command in the terminal:

```bash
reset-user-env
```

Running this command will remove any additional packages or modifications
you've made in your virtual environment, restoring it to its default state.
This is especially useful if you experience dependency issues or if the environment becomes cluttered from experimentation.

> **_Pro Tip:_** To manually reset your virtual environment, you can run:
> `rm -rf /classiq-venv/*`
